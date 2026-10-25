"""Distribución privada de la entrega completa, siempre por generación y SHA fijados."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from goes_science_kg.clases.paquete import VERSION, extraer, sin_guion_declarados, validar, validar_cobertura_publicable
from goes_science_kg.materiales.compilacion import serializar, sha


def publicar(archivo: Path, almacen, recibo: Path):
    m = validar(archivo)
    pendientes = sin_guion_declarados(m.get("procedencia"))
    validar_cobertura_publicable(m["por_tipo"], len(pendientes))
    identidad = {"version": VERSION, "entrega_id": m["id"], "materiales": m["materiales"], "por_tipo": m["por_tipo"]}
    if pendientes:
        identidad["objetivos_sin_guion_liberado"] = pendientes
    nombre = f"clases/{m['id']}/guiones.zip"
    digest = sha(archivo.read_bytes())
    if recibo.is_symlink():
        raise ValueError("El recibo requiere un archivo propio")
    if recibo.exists():
        anterior = json.loads(recibo.read_bytes())
        if any(anterior[k] != v for k, v in identidad.items()):
            raise ValueError("El recibo corresponde a otra entrega")
        ref = anterior["objeto"]
        if (ref["uri"], ref["sha256"], ref["bytes"]) != (
            almacen.configuracion.ruta(nombre),
            digest,
            archivo.stat().st_size,
        ):
            raise ValueError("El objeto no corresponde a la entrega")
        almacen.verificar(ref["uri"], ref["generacion"], digest, ref["bytes"])
        return anterior
    ref = almacen.crear(archivo, nombre)
    if sha(archivo.read_bytes()) != digest:
        raise ValueError("La entrega cambió durante la publicación")
    resultado = identidad | {"objeto": ref}
    recibo.parent.mkdir(parents=True, exist_ok=True)
    with recibo.open("xb") as f:
        f.write(serializar(resultado))
    return resultado


def descargar(recibo: dict, destino: Path, almacen):
    if recibo["version"] != VERSION:
        raise ValueError("Recibo incompatible")
    validar_cobertura_publicable(recibo["por_tipo"], len(sin_guion_declarados(recibo)))
    ref = recibo["objeto"]
    if ref["uri"] != almacen.configuracion.ruta(f"clases/{recibo['entrega_id']}/guiones.zip"):
        raise ValueError("El objeto no corresponde a la entrega solicitada")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La descarga requiere un directorio nuevo")
    with tempfile.TemporaryDirectory(prefix="clases-descarga-") as temporal:
        archivo = Path(temporal) / "guiones.zip"
        almacen.descargar(ref, archivo)
        m = validar(archivo)
        if any(m[k] != recibo[k] for k in ("materiales", "por_tipo")) or m["id"] != recibo["entrega_id"]:
            raise ValueError("La entrega descargada no conserva su identidad")
        return extraer(archivo, destino)
