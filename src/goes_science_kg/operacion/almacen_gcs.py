"""Objetos inmutables en el bucket institucional; nunca cambia IAM ni sobrescribe generaciones."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from pydantic import Field

from goes_science_kg.motor.contratos import Contrato

LOGGER = logging.getLogger(__name__)


class ConfiguracionAlmacen(Contrato):
    proyecto: str = Field(pattern=r"^[a-z][a-z0-9-]{4,62}$")
    bucket: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{1,220}[a-z0-9]$")
    prefijo: str = Field(pattern=r"^[a-z0-9][a-z0-9/_-]{1,150}$")
    cuenta: str = Field(pattern=r"^[a-zA-Z0-9._+-]+@goes\.gob\.sv$")
    python_gcloud: str | None = None

    def ruta(self, nombre: str) -> str:
        if ".." in self.prefijo or any(c in nombre for c in ("..", "#", "?", "\\")):
            raise ValueError("El nombre de objeto sale del prefijo autorizado")
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9/_.-]{0,300}", nombre):
            raise ValueError("Nombre de objeto incompatible")
        return f"gs://{self.bucket}/{self.prefijo.rstrip('/')}/{nombre}"


class GCloud:
    """CLI instalada, sin shell ni tokens en argumentos/salidas de aplicación."""

    def __init__(self, configuracion: ConfiguracionAlmacen):
        self.configuracion = configuracion

    def ejecutar(self, argumentos: list[str]) -> str:
        entorno = dict(os.environ)
        python = self.configuracion.python_gcloud or shutil.which("python3.12")
        if python:
            entorno["CLOUDSDK_PYTHON"] = python
        resultado = subprocess.run(
            ["gcloud", *argumentos, f"--project={self.configuracion.proyecto}", "--quiet"],
            env=entorno,
            capture_output=True,
            text=True,
            timeout=900 if argumentos[:2] == ["storage", "cp"] else 180,
            check=False,
        )
        if resultado.returncode:
            # No propagar trazas o posibles detalles del proveedor al producto/API.
            raise RuntimeError(f"gcloud no completó {argumentos[0]} (código {resultado.returncode})")
        return resultado.stdout


class AlmacenGCS:
    def __init__(self, configuracion: ConfiguracionAlmacen, *, cli=None, max_bytes_objeto: int = 1024**3):
        if type(max_bytes_objeto) is not int or not 1 <= max_bytes_objeto <= 8 * 1024**3:
            raise ValueError("El límite de objeto debe ser un entero positivo de hasta 8 GiB")
        self.configuracion = configuracion
        self.cli = cli or GCloud(configuracion)
        self.max_bytes_objeto = max_bytes_objeto

    def _validar_tamano(self, tamano: int) -> None:
        if type(tamano) is not int or not 1 <= tamano <= self.max_bytes_objeto:
            raise ValueError("El tamaño debe ser positivo y no exceder el límite de objeto configurado")

    def comprobar_proteccion(self) -> dict:
        cfg = self.configuracion
        cuenta = self.cli.ejecutar(["config", "get-value", "account"]).strip()
        if cuenta != cfg.cuenta:
            raise ValueError("El respaldo requiere la identidad institucional GOES configurada")
        bucket = json.loads(
            self.cli.ejecutar(
                [
                    "storage",
                    "buckets",
                    "describe",
                    f"gs://{cfg.bucket}",
                    "--raw",
                    "--format=json",
                ]
            )
        )
        proyecto = json.loads(self.cli.ejecutar(["projects", "describe", cfg.proyecto, "--format=json"]))
        iam = bucket.get("iamConfiguration", {})
        if (
            bucket.get("name") != cfg.bucket
            or iam.get("uniformBucketLevelAccess", {}).get("enabled") is not True
            or not str(proyecto.get("projectNumber", "")).isdigit()
            or str(bucket.get("projectNumber")) != str(proyecto.get("projectNumber"))
            or proyecto.get("projectId") != cfg.proyecto
        ):
            raise ValueError("El bucket no conserva identidad o acceso uniforme")
        politica = None
        pap = iam.get("publicAccessPrevention")
        if pap == "inherited":
            politica = json.loads(
                self.cli.ejecutar(
                    [
                        "resource-manager",
                        "org-policies",
                        "describe",
                        "constraints/storage.publicAccessPrevention",
                        "--effective",
                        "--format=json",
                    ]
                )
            )
            if politica.get("constraint") != "constraints/storage.publicAccessPrevention" or (
                politica.get("booleanPolicy", {}).get("enforced") is not True
            ):
                raise ValueError("La protección heredada requiere una política efectiva enforced")
        elif pap != "enforced":
            raise ValueError("El bucket no demuestra prevención de acceso público")
        LOGGER.info("VERDE respaldo privado: %s; PAP %s; UBLA activo", cfg.bucket, pap)
        return {"cuenta": cuenta, "bucket": bucket, "politica_efectiva": politica}

    def crear(self, archivo: Path, nombre: str) -> dict:
        if not archivo.is_file() or archivo.is_symlink():
            raise ValueError("Suba únicamente un archivo local regular")
        digest, tamano = _medir(archivo)
        self._validar_tamano(tamano)  # Fallar antes de crear un objeto que no podría releerse.
        destino = self.configuracion.ruta(nombre)
        proteccion = self.comprobar_proteccion()  # Relectura por cada escritura, no recibo histórico.
        self.cli.ejecutar(
            [
                "storage",
                "cp",
                str(archivo),
                destino,
                "--if-generation-match=0",
                f"--custom-metadata=sha256={digest}",
            ]
        )
        metadata = json.loads(self.cli.ejecutar(["storage", "objects", "describe", destino, "--raw", "--format=json"]))
        generacion = str(metadata.get("generation", ""))
        if (
            not generacion.isdigit()
            or metadata.get("metadata", {}).get("sha256") != digest
            or str(metadata.get("size")) != str(tamano)
        ):
            raise ValueError("La generación subida no conserva la identidad del objeto")
        self.verificar(destino, generacion, digest, tamano)
        if _medir(archivo) != (digest, tamano):
            raise ValueError("El archivo local cambió durante el respaldo")
        LOGGER.info("VERDE objeto creado y releído: %s#%s", destino, generacion)
        return {
            "uri": destino,
            "generacion": generacion,
            "sha256": digest,
            "bytes": tamano,
            "proteccion": proteccion,
        }

    def verificar(self, uri: str, generacion: str, digest: str, tamano: int, *, destino: Path | None = None) -> None:
        prefijo = f"gs://{self.configuracion.bucket}/{self.configuracion.prefijo.rstrip('/')}/"
        if not uri.startswith(prefijo) or uri != self.configuracion.ruta(uri.removeprefix(prefijo)):
            raise ValueError("El recibo apunta fuera del prefijo autorizado")
        self._validar_tamano(tamano)
        if not re.fullmatch(r"[0-9]+", generacion) or not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise ValueError("La generación y el SHA deben estar fijados")
        if destino is not None and (destino.exists() or destino.is_symlink()):
            raise ValueError("La descarga requiere un archivo nuevo")
        with tempfile.TemporaryDirectory(prefix="goes-ciencias-gcs-") as temporal:
            archivo = Path(temporal) / "objeto"
            self.cli.ejecutar(["storage", "cp", f"{uri}#{generacion}", str(archivo)])
            if _medir(archivo) != (digest, tamano):
                raise ValueError("Los bytes releídos de GCS no coinciden con la generación subida")
            if destino is not None:
                destino.parent.mkdir(parents=True, exist_ok=True)
                with archivo.open("rb") as origen, destino.open("xb") as salida:
                    shutil.copyfileobj(origen, salida, length=1024 * 1024)
                if _medir(destino) != (digest, tamano):
                    raise ValueError("La copia local no conserva el SHA de la generación verificada")

    def descargar(self, recibo: dict, destino: Path) -> None:
        self.verificar(recibo["uri"], recibo["generacion"], recibo["sha256"], recibo["bytes"], destino=destino)


def _medir(archivo: Path) -> tuple[str, int]:
    """SHA incremental: evita cargar paquetes de cientos de MiB completos en RAM."""
    with archivo.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
        tamano = stream.tell()
    return digest, tamano
