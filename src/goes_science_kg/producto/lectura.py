"""Thread-safe repository for immutable, verified V4 publications."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from threading import Lock

from fastapi import HTTPException

from goes_science_kg.producto.almacen import archivos_producto
from goes_science_kg.producto.runtime import RuntimeProducto, cargar_runtime

LOGGER = logging.getLogger(__name__)


def _observar(destino: Path) -> dict:
    """Compare file signatures while validating byte fingerprints during initial loading."""
    puntero = destino / "actual.json"
    if puntero.stat().st_size > 4096:
        raise ValueError("Puntero de publicación incompatible")
    seleccion = json.loads(puntero.read_bytes())
    if not isinstance(seleccion, dict):
        raise ValueError("El puntero de publicación debe ser un objeto")
    identidad = seleccion.get("snapshot_id", "")
    if not isinstance(identidad, str) or not re.fullmatch(r"[a-f0-9]{64}", identidad):
        raise ValueError("Identidad de snapshot incompatible")
    generacion = destino / "snapshots" / identidad
    archivos = [
        puntero,
        generacion / "manifest.json",
        *(generacion / n for n in sorted(archivos_producto(seleccion.get("version")))),
    ]
    firmas = {}
    for archivo in archivos:
        actual = archivo
        while actual != destino.parent:
            if actual.is_symlink():
                raise ValueError("La publicación no admite enlaces")
            actual = actual.parent
        s = archivo.stat()
        firmas[str(archivo)] = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    return firmas


class LecturaProducto:
    """Pin one verified generation and reject any subsequent publication change."""

    def __init__(self, base: Path, destino: Path | None = None) -> None:
        self.base = base.resolve()
        self.destino = destino or self.base / "data/producto/V4"
        self._runtime: RuntimeProducto | None = None
        self._firmas = None
        self._error = False
        self._lock = Lock()

    def leer(self) -> RuntimeProducto:
        """Load once, compare file signatures on every read, and fail closed."""
        with self._lock:
            try:
                if self._error:
                    raise ValueError("La instancia quedó invalidada")
                firmas = _observar(self.destino)
                if self._runtime is None:
                    runtime = cargar_runtime(
                        self.destino,
                        raiz_v4=self.base / "insumos/v4",
                        raiz_historica=self.base / "data/fuentes",
                        raiz_referencias=self.base / "data/referencias_2026",
                        raiz_paises=self.base / "data/referencias_paises_2026",
                        raiz_cientificas=self.base / "data/referencias_cientificas_2026",
                        archivo_alertas=self.base / "docs/investigacion/alertas_v4.json",
                        archivo_alertas_derivadas=self.base / "config/alertas_derivadas_v4.yaml",
                        raiz_progresiones=self.base / "data/referencias_progresiones_2026",
                    )
                    if firmas != _observar(self.destino):
                        raise ValueError("La publicación cambió durante la carga")
                    self._runtime, self._firmas = runtime, firmas
                elif firmas != self._firmas:
                    raise ValueError("La publicación cambió después de cargarse")
                return self._runtime
            except (ValueError, KeyError, OSError) as error:
                self._error = True
                LOGGER.error("ROJO API V4 sin publicación verificable: %s", type(error).__name__)
                raise HTTPException(
                    503,
                    {
                        "codigo": "producto_v4_no_disponible",
                        "estado": "sin_datos",
                        "motivo": "No hay datos disponibles: falta una publicación V4 íntegra o cambió; "
                        "verifícala y reinicia el servicio",
                    },
                ) from error
