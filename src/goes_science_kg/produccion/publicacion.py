"""Distribución privada de exportaciones finales; objetos nuevos y generaciones verificadas."""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path

from goes_science_kg.archivos import destino_generado
from goes_science_kg.materiales.compilacion import serializar, sha

VERSION = "exportaciones-mallas-finales-1"


def _nombre(nombre):
    if not re.fullmatch(r"grado-[0-9]{2}-[a-z]+\.zip|indice\.json", nombre):
        raise ValueError("Nombre de exportación incompatible")
    return nombre


def _objeto(biblioteca_id, nombre):
    if not re.fullmatch(r"[a-f0-9]{64}", biblioteca_id):
        raise ValueError("Identidad de biblioteca incompatible")
    return f"produccion/mallas-finales/{biblioteca_id}/paquetes/{_nombre(nombre)}"


def publicar(directorio: Path, biblioteca, almacen, recibo: Path):
    """Admite reanudación exacta; una referencia previa se relee y nunca se sobrescribe."""
    manifest = biblioteca.validar()
    if manifest["procedencia"].get("edicion") != "produccion-final-20261026":
        raise ValueError("Se requiere la biblioteca de la edición final")
    if any(p.is_symlink() for p in (directorio, *directorio.parents, recibo, *recibo.parents)):
        raise ValueError("Las exportaciones y recibos deben tener rutas propias")
    indice = json.loads((directorio / "indice.json").read_bytes())
    esperados = {e["archivo"]: {k: e[k] for k in ("sha256", "bytes")} for e in indice["paquetes"]}
    if len(esperados) != len(indice["paquetes"]):
        raise ValueError("Exportaciones duplicadas")
    raw = (directorio / "indice.json").read_bytes()
    esperados["indice.json"] = {"sha256": sha(raw), "bytes": len(raw)}
    for nombre, esperado in esperados.items():
        _nombre(nombre)
        archivo = directorio / nombre
        if archivo.is_symlink():
            raise ValueError("Las exportaciones deben ser archivos propios")
        raw = archivo.read_bytes()
        if (
            esperado != {"sha256": sha(raw), "bytes": len(raw)}
            or manifest["originales"].get("paquetes/" + nombre) != esperado
        ):
            raise ValueError("La exportación no corresponde a la biblioteca verificada")
    progreso = (
        json.loads(recibo.read_bytes())
        if recibo.exists()
        else {
            "version": VERSION,
            "biblioteca_id": manifest["id"],
            "snapshot_id": manifest["procedencia"]["snapshot_id"],
            "estado_revision": "pendiente_revision_nueva_edicion",
            "objetos": {},
        }
    )
    if (
        progreso["version"] != VERSION
        or progreso["biblioteca_id"] != manifest["id"]
        or (set(progreso["objetos"]) - esperados.keys())
    ):
        raise ValueError("El recibo corresponde a otras exportaciones")
    recibo.parent.mkdir(parents=True, exist_ok=True)
    for nombre, esperado in sorted(esperados.items()):
        objeto = _objeto(manifest["id"], nombre)
        if nombre in progreso["objetos"]:
            ref = progreso["objetos"][nombre]
            if ref["uri"] != almacen.configuracion.ruta(objeto) or any(ref[k] != esperado[k] for k in esperado):
                raise ValueError("Una referencia previa difiere de la exportación")
            almacen.verificar(ref["uri"], ref["generacion"], ref["sha256"], ref["bytes"])
        else:
            progreso["objetos"][nombre] = almacen.crear(directorio / nombre, objeto)
            temporal = recibo.with_name(recibo.name + ".temporal")
            with temporal.open("xb") as f:
                f.write(serializar(progreso))
            temporal.replace(recibo)
        biblioteca.comprobar()
    return progreso


def descargar(recibo: dict, destino: Path, almacen):
    """Valida URI, generación, tamaño y SHA; sólo habilita el directorio completo verificado."""
    destino_generado(destino / "indice.json")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La descarga requiere un directorio nuevo")
    if recibo["version"] != VERSION or "indice.json" not in recibo["objetos"]:
        raise ValueError("Recibo de exportaciones incompleto")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".produccion-", dir=destino.parent) as temporal:
        carpeta = Path(temporal) / "verificado"
        carpeta.mkdir()
        for nombre, ref in recibo["objetos"].items():
            if ref["uri"] != almacen.configuracion.ruta(_objeto(recibo["biblioteca_id"], nombre)):
                raise ValueError("La referencia no pertenece a esta entrega final")
            almacen.descargar(ref, carpeta / nombre)
        indice = json.loads((carpeta / "indice.json").read_bytes())
        esperados = {e["archivo"]: e for e in indice["paquetes"]}
        if set(esperados) != set(recibo["objetos"]) - {"indice.json"} or len(esperados) != len(indice["paquetes"]):
            raise ValueError("El índice omite o duplica exportaciones")
        for nombre, e in esperados.items():
            ref = recibo["objetos"][nombre]
            if any(ref[k] != e[k] for k in ("sha256", "bytes")):
                raise ValueError("El índice no corresponde a las exportaciones")
        carpeta.rename(destino)
    return indice
