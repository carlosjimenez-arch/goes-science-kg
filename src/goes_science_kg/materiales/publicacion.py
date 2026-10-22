"""Publicación y restauración verificables en el almacén institucional aprobado."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from goes_science_kg.archivos import destino_generado
from goes_science_kg.materiales.almacen import VERSION, Biblioteca
from goes_science_kg.materiales.compilacion import serializar, sha


def _guardar(p, valor):
    with p.open("xb") as salida:
        salida.write(serializar(valor))


def publicar(destino: Path, almacen, recibo: Path) -> dict:
    """Guarda un recibo de progreso tras cada objeto para reanudar sin sobrescribirlo."""
    biblioteca = Biblioteca(destino)
    manifest = biblioteca.validar()
    if recibo.is_symlink():
        raise ValueError("El recibo debe ser un archivo propio")
    progreso = (
        json.loads(recibo.read_bytes())
        if recibo.exists()
        else {
            "version": VERSION,
            "biblioteca_id": manifest["id"],
            "objetos": {},
        }
    )
    if progreso["version"] != VERSION or progreso["biblioteca_id"] != manifest["id"]:
        raise ValueError("El recibo pertenece a otra biblioteca")
    recibo.parent.mkdir(parents=True, exist_ok=True)
    for nombre in ("biblioteca.sqlite", "manifest.json"):
        archivo = destino / nombre
        digest = sha(archivo.read_bytes())
        objeto = f"materiales/{manifest['id']}/{nombre}"
        if nombre in progreso["objetos"]:
            ref = progreso["objetos"][nombre]
            if (ref["uri"], ref["sha256"], ref["bytes"]) != (
                almacen.configuracion.ruta(objeto),
                digest,
                archivo.stat().st_size,
            ):
                raise ValueError("El recibo no corresponde al artefacto local")
            almacen.verificar(ref["uri"], ref["generacion"], ref["sha256"], ref["bytes"])
        else:
            progreso["objetos"][nombre] = almacen.crear(archivo, objeto)
            temporal = recibo.with_name(recibo.name + ".temporal")
            _guardar(temporal, progreso)
            temporal.replace(recibo)
        biblioteca.comprobar()
    return progreso


def restaurar(recibo: dict, destino: Path, almacen) -> dict:
    """Sólo habilita los dos artefactos juntos, después de reconstruir sus comprobaciones."""
    destino_generado(destino / "biblioteca.sqlite")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La restauración requiere un directorio nuevo")
    if recibo["version"] != VERSION or set(recibo["objetos"]) != {"biblioteca.sqlite", "manifest.json"}:
        raise ValueError("Recibo incompleto o incompatible")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".materiales-", dir=destino.parent) as temporal:
        base = Path(temporal) / "verificado"
        base.mkdir()
        for nombre in ("biblioteca.sqlite", "manifest.json"):
            ref = recibo["objetos"][nombre]
            esperado = almacen.configuracion.ruta(f"materiales/{recibo['biblioteca_id']}/{nombre}")
            if ref["uri"] != esperado:
                raise ValueError("El objeto no pertenece a la biblioteca solicitada")
            almacen.descargar(ref, base / nombre)
        manifest = Biblioteca(base).validar()
        if manifest["id"] != recibo["biblioteca_id"]:
            raise ValueError("La biblioteca recuperada tiene otra identidad")
        base.rename(destino)
    return manifest
