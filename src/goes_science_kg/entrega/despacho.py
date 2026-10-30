"""Release only validated final teaching packages and preserve a portable dispatch receipt."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree

from goes_science_kg.archivos import destino_generado
from goes_science_kg.entrega.compilacion import digest, validar
from goes_science_kg.materiales.compilacion import serializar, sha

VERSION = "despacho-didactico-1"


def _propio(archivo: Path, *, directorio: bool = False) -> Path:
    if any(p.is_symlink() for p in (archivo, *archivo.parents)):
        raise ValueError("El despacho requiere rutas propias sin enlaces simbólicos")
    if not (archivo.is_dir() if directorio else archivo.is_file()):
        raise ValueError("Falta un archivo o directorio regular de la entrega")
    return archivo


def _inventario(carpeta: Path) -> dict:
    resultado = {}
    for archivo in sorted(carpeta.rglob("*")):
        if archivo.is_symlink() or not (archivo.is_dir() or archivo.is_file()):
            raise ValueError("La entrega contiene un enlace o archivo no regular")
        if archivo.is_file():
            resultado[archivo.relative_to(carpeta).as_posix()] = {
                "bytes": archivo.stat().st_size,
                "sha256": digest(archivo),
            }
    return resultado


def _verificar_zip(edicion: Path, archivo: Path, manifest: dict) -> None:
    esperados = dict(manifest["archivos"])
    esperados["manifest.json"] = {
        "bytes": (edicion / "manifest.json").stat().st_size,
        "sha256": digest(edicion / "manifest.json"),
    }
    try:
        with zipfile.ZipFile(archivo) as z:
            infos = z.infolist()
            nombres = [i.filename for i in infos]
            if len(nombres) != len(set(nombres)) or set(nombres) != set(esperados):
                raise ValueError("El ZIP no conserva el inventario exacto de la edición")
            for info in infos:
                nombre = PurePosixPath(info.filename)
                if (
                    nombre.is_absolute()
                    or nombre.as_posix() != info.filename
                    or any(p in {"", ".", ".."} for p in info.filename.split("/"))
                    or "\\" in info.filename
                    or ":" in info.filename
                    or info.is_dir()
                    or info.flag_bits & 1
                    or stat.S_ISLNK(info.external_attr >> 16)
                ):
                    raise ValueError("El ZIP contiene un nombre o una entrada no segura")
                meta = esperados[info.filename]
                if info.file_size != meta["bytes"]:
                    raise ValueError("El tamaño del ZIP difiere de la edición")
                with z.open(info) as stream:
                    actual = hashlib.file_digest(stream, "sha256").hexdigest()
                if actual != meta["sha256"]:
                    raise ValueError("El SHA del ZIP difiere de la edición")
            if z.testzip() is not None:
                raise ValueError("El ZIP tiene un CRC inválido")
    except (zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        raise ValueError("El ZIP no supera la comprobación de integridad") from error


def _huella_codigo(raiz: Path) -> str:
    archivo = _propio(raiz / "scripts/generar_badges.py")
    spec = importlib.util.spec_from_file_location("gskg_despacho_medicion", archivo)
    if spec is None or spec.loader is None:
        raise ValueError("No se puede comprobar la huella de código de la medición")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.huella_codigo(raiz)


def _contar_pruebas(raiz: Path) -> int:
    entorno = dict(os.environ)
    entorno.pop("PYTEST_ADDOPTS", None)
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q", "-o", "addopts="],
            cwd=raiz,
            env=entorno,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("No se pudo comprobar la colección completa de pruebas") from error
    cuenta = re.search(r"(?m)^(\d+) tests? collected", resultado.stdout)
    if resultado.returncode != 0 or cuenta is None:
        raise ValueError("No se pudo comprobar la colección completa de pruebas")
    return int(cuenta[1])


def _verificar_medicion(raiz: Path, medicion: Path) -> dict:
    informe = json.loads(medicion.read_bytes())
    pruebas = informe.get("pruebas", {})
    claves = ("tests", "ejecutadas", "aprobadas", "failures", "errors", "skipped")
    if (
        any(type(pruebas.get(k)) is not int for k in claves)
        or pruebas["tests"] <= 0
        or pruebas["tests"] != pruebas["ejecutadas"]
        or pruebas["tests"] != pruebas["aprobadas"]
        or any(pruebas[k] != 0 for k in ("failures", "errors", "skipped"))
    ):
        raise ValueError("La medición no acredita una suite completa sin fallos ni omisiones")
    if informe.get("huella_codigo_sha256") != _huella_codigo(raiz):
        raise ValueError("La medición corresponde a otra versión de código o de la política de calidad")
    xml = ElementTree.parse(_propio(raiz / "junit.xml")).getroot()
    suites = [xml] if xml.tag == "testsuite" else list(xml.findall("testsuite"))
    totales = {k: sum(int(s.get(k, "0")) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    if not suites or any(totales[k] != pruebas[k] for k in totales):
        raise ValueError("JUnit no acredita los resultados declarados por la medición")
    cobertura = ElementTree.parse(_propio(raiz / "coverage.xml")).getroot()
    cubiertas, lineas = int(cobertura.get("lines-covered", "-1")), int(cobertura.get("lines-valid", "0"))
    declarado = informe.get("cobertura", {})
    if (
        not 0 <= cubiertas <= lineas
        or lineas <= 0
        or declarado.get("lineas_cubiertas") != cubiertas
        or declarado.get("lineas_totales") != lineas
        or not math.isclose(declarado.get("porcentaje", -1), 100 * cubiertas / lineas, rel_tol=1e-9)
    ):
        raise ValueError("La cobertura declarada no corresponde al informe XML")
    if _contar_pruebas(raiz) != pruebas["tests"]:
        raise ValueError("La medición no cubre toda la colección actual de pruebas")
    return informe


def _verificar_auditoria(auditoria: dict, manifest: dict, archivo_zip: Path) -> None:
    revisadas = manifest.get("revision_documental", [])
    if not revisadas or not isinstance(revisadas, list) or len(revisadas) != len(set(revisadas)):
        raise ValueError("Faltan dictámenes documentales exactos para los materiales nuevos")
    controles = auditoria.get("comprobaciones", {})
    ids = auditoria.get("json_revisados", [])
    if (
        auditoria.get("estado") != "aprobado"
        or auditoria.get("errores") != []
        or auditoria.get("manifest_id") != manifest["id"]
        or auditoria.get("zip_sha256") != digest(archivo_zip)
        or auditoria.get("zip_bytes") != archivo_zip.stat().st_size
        or auditoria.get("denominadores") != manifest["resumen"]
        or auditoria.get("archivos_zip_y_carpeta") != len(manifest["archivos"]) + 1
        or not isinstance(ids, list)
        or len(ids) != len(set(ids))
        or set(ids) != set(revisadas)
        or controles.get("json_revisados_sha_verificados") != len(revisadas)
        or controles.get("entradas_zip_sha_verificadas") != len(manifest["archivos"]) + 1
        or controles.get("archivos_carpeta_sha_verificados") != len(manifest["archivos"])
    ):
        raise ValueError("La auditoría independiente no acredita esta versión exacta de la entrega")


def verificar_despacho(destino: Path) -> dict:
    """Verify the complete copied delivery and its receipt without relying on original paths."""
    _propio(destino, directorio=True)
    recibo = json.loads(_propio(destino / "recibo_despacho.json").read_bytes())
    if recibo.get("version") != VERSION or recibo.get("id") != sha(
        serializar({k: v for k, v in recibo.items() if k != "id"})
    ):
        raise ValueError("El recibo de despacho cambió")
    actuales = _inventario(destino)
    actuales.pop("recibo_despacho.json")
    if actuales != recibo["archivos"]:
        raise ValueError("La copia entregada está incompleta o fue alterada")
    manifest = json.loads((destino / "entrega/manifest.json").read_bytes())
    if manifest["id"] != recibo["edicion_id"] or manifest["id"] != sha(
        serializar({k: v for k, v in manifest.items() if k != "id"})
    ):
        raise ValueError("La copia pertenece a otra edición")
    nombre_zip = recibo["zip"]["archivo"]
    if (
        not isinstance(nombre_zip, str)
        or PurePosixPath(nombre_zip).name != nombre_zip
        or "\\" in nombre_zip
        or ":" in nombre_zip
    ):
        raise ValueError("El recibo requiere un nombre ZIP portable dentro de la entrega")
    archivo_zip = _propio(destino / nombre_zip)
    if digest(archivo_zip) != recibo["zip"]["sha256"] or archivo_zip.stat().st_size != recibo["zip"]["bytes"]:
        raise ValueError("El resumen ZIP del recibo no corresponde a los bytes entregados")
    _verificar_zip(destino / "entrega", archivo_zip, manifest)
    _verificar_auditoria(
        json.loads((destino / "calidad/auditoria_independiente.json").read_bytes()), manifest, archivo_zip
    )
    return recibo


def despachar(
    raiz: Path,
    edicion: Path,
    archivo_zip: Path,
    auditoria: Path,
    medicion: Path,
    destino: Path,
    *,
    evidencias_extra: Sequence[Path] = (),
) -> dict:
    """Release only a complete reviewed edition with current quality evidence, without overwriting."""
    raiz = raiz.resolve()
    for archivo in (archivo_zip, auditoria, medicion, *evidencias_extra):
        _propio(archivo)
    _propio(edicion, directorio=True)
    if destino.exists() or destino.is_symlink() or any(p.is_symlink() for p in destino.parents):
        raise ValueError("El despacho requiere una carpeta nueva y propia; no se sobrescribe")
    if not destino.parent.is_dir():
        raise ValueError("La carpeta padre del despacho debe existir")
    destino = destino.resolve()
    destino_generado(destino / "recibo_despacho.json", raiz=raiz)
    fuentes = (edicion, archivo_zip, auditoria, medicion, raiz / "junit.xml", raiz / "coverage.xml", *evidencias_extra)
    if any(p.resolve().is_relative_to(destino) or destino.is_relative_to(p.resolve()) for p in fuentes):
        raise ValueError("El despacho no puede solaparse con sus originales o evidencias")
    if archivo_zip.suffix.lower() != ".zip" or "\\" in archivo_zip.name or ":" in archivo_zip.name:
        raise ValueError("El paquete requiere un nombre ZIP portable")
    inventario_original = _inventario(edicion)
    entradas = {
        "auditoria_independiente.json": auditoria,
        "medicion.json": medicion,
        "junit.xml": raiz / "junit.xml",
        "coverage.xml": raiz / "coverage.xml",
    }
    for archivo in evidencias_extra:
        if archivo.name in entradas or archivo.name in {"ENTREGA_DIDACTICA_V2.md", "PEDAGOGIA_CIENCIAS_V4.md"}:
            raise ValueError("Las evidencias de calidad requieren nombres distintos")
        entradas[archivo.name] = archivo
    for nombre in ("ENTREGA_DIDACTICA_V2.md", "PEDAGOGIA_CIENCIAS_V4.md"):
        origen = raiz / "docs" / nombre
        if origen.is_file():
            entradas[nombre] = _propio(origen)
    for archivo in entradas.values():
        _propio(archivo)
    hashes_entradas = {n: digest(p) for n, p in entradas.items()}
    hash_zip = digest(archivo_zip)
    manifest = validar(edicion)
    if not manifest.get("revision_documental") or not list((edicion / "auditoria/revisiones").glob("*.json")):
        raise ValueError("Faltan dictámenes documentales exactos para los materiales nuevos")
    _verificar_zip(edicion, archivo_zip, manifest)
    informe = json.loads(auditoria.read_bytes())
    _verificar_auditoria(informe, manifest, archivo_zip)
    medida = _verificar_medicion(raiz, medicion)
    with tempfile.TemporaryDirectory(prefix=f".{destino.name}-", dir=destino.parent) as temporal:
        preparado = Path(temporal).resolve() / "preparado"
        preparado.mkdir()
        shutil.copytree(edicion, preparado / "entrega")
        shutil.copy2(archivo_zip, preparado / archivo_zip.name)
        (preparado / "calidad").mkdir()
        for nombre, origen in entradas.items():
            shutil.copy2(origen, preparado / "calidad" / nombre)
        if _inventario(preparado / "entrega") != inventario_original:
            raise ValueError("La copia de los materiales no conserva su SHA")
        if any(digest(preparado / "calidad" / n) != h for n, h in hashes_entradas.items()):
            raise ValueError("La copia de las evidencias no conserva su SHA")
        validar(preparado / "entrega")
        _verificar_zip(preparado / "entrega", preparado / archivo_zip.name, manifest)
        catalogo = json.loads((preparado / "entrega/catalogo.json").read_bytes())
        enlaces = []
        for recorrido in catalogo["recorridos"]:
            archivo = PurePosixPath(recorrido["archivo"]).parent
            contenido = json.loads((preparado / "entrega" / recorrido["archivo"]).read_bytes())
            enlaces.append(f"- [{contenido['id']} · {contenido['titulo']}](entrega/{archivo}/docente.md).")
        for clase in catalogo["clases"]:
            if clase["estado"] == "sucesor_local_con_correccion":
                enlaces.append(f"- [{clase['titulo']}](entrega/{clase['archivo']}.docente.md).")
        for modulo in catalogo.get("modulos_adicionales", []):
            archivo = PurePosixPath(modulo["archivo"]).parent
            enlaces.append(f"- [{modulo['titulo']}](entrega/{archivo}/docente.md).")
        resumen = manifest["resumen"]
        antecedentes = resumen["clases"] - resumen["correcciones_cientificas"]
        leeme = (
            "# Paquetes finales de Ciencias\n\n"
            "Empiece por el [índice de materiales](entrega/INDICE.md). "
            f"La [copia ZIP]({archivo_zip.name}) contiene la misma edición.\n\n"
            "## Paquetes nuevos revisados\n\n" + "\n".join(enlaces) + "\n\n"
            "Los diagnósticos, refuerzos y comprobaciones se entregan en hojas separadas; "
            "las soluciones y rúbricas pertenecen a la guía docente.\n\n"
            f"Los otros {antecedentes} guiones son antecedentes con apoyos de diseño, no nuevas revisiones "
            f"científicas integrales. Los {resumen['objetivos_sin_guion']} objetivos sin guion y "
            f"las {resumen['retenidos']} piezas retenidas conservan sus motivos y no se presentan como aprobados. "
            "La completitud de archivos y las pruebas de software no acreditan aprendizaje, "
            "eficacia ni carga cognitiva medida.\n\n"
            "La carpeta `calidad/` conserva auditoría independiente, medición de pruebas, JUnit y cobertura. "
            "`recibo_despacho.json` fija los SHA de todos los archivos entregados.\n"
        )
        (preparado / "LEEME.md").write_text(leeme, encoding="utf-8")
        recibo = {
            "version": VERSION,
            "fecha_utc": datetime.now(UTC).isoformat(),
            "edicion_id": manifest["id"],
            "zip": {
                "archivo": archivo_zip.name,
                "bytes": (preparado / archivo_zip.name).stat().st_size,
                "sha256": hash_zip,
            },
            "revision_documental": manifest["revision_documental"],
            "resumen": manifest["resumen"],
            "archivos": _inventario(preparado),
            "limite": "Despacho técnico y documental; no acredita eficacia ni carga cognitiva medida.",
        }
        recibo["id"] = sha(serializar(recibo))
        (preparado / "recibo_despacho.json").write_bytes(serializar(recibo))
        verificar_despacho(preparado)
        if (
            _inventario(edicion) != inventario_original
            or digest(archivo_zip) != hash_zip
            or any(digest(entradas[n]) != h for n, h in hashes_entradas.items())
        ):
            raise ValueError("Los originales o sus evidencias cambiaron durante el despacho")
        if _huella_codigo(raiz) != medida["huella_codigo_sha256"]:
            raise ValueError("El código o la política de calidad cambiaron durante el despacho")
        destino.mkdir()  # Reserve exclusively after every check; do not replace a racing destination.
        try:
            for entrada in sorted(preparado.iterdir(), key=lambda p: p.name == "recibo_despacho.json"):
                entrada.rename(destino / entrada.name)
            verificar_despacho(destino)
        except BaseException:
            shutil.rmtree(destino)
            raise
    return recibo
