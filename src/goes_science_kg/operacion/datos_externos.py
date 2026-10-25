"""Migrate and restore the complete corpus with verified retirement conditions."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path

from goes_science_kg.operacion.respaldo import crear_paquete, nombre_seguro, restaurar_paquete

VERSION = "datos-ciencias-1"
TRANSITORIOS = {".DS_Store", ".gitkeep"}
LEDGER = "data/operaciones/registro.sqlite"
MAX_BYTES_PREDETERMINADO = 2 * 1024**3
MAX_BYTES_PERMITIDO = 8 * 1024**3


def limite_bytes(valor=None):
    """Validate the corpus size limit, defaulting to the documented minimum."""
    limite = MAX_BYTES_PREDETERMINADO if valor is None else valor
    if type(limite) is not int or not MAX_BYTES_PREDETERMINADO <= limite <= MAX_BYTES_PERMITIDO:
        raise ValueError("El límite del corpus debe ser un entero entre 2 y 8 GiB")
    return limite


def digest(archivo: Path) -> str:
    """Compute a file's SHA-256 fingerprint incrementally."""

    with archivo.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def identidad_ledger(archivo: Path) -> dict | None:
    """Record a ledger's physical identity without opening or modifying its data."""

    if not archivo.exists():
        return None
    estado = archivo.stat()
    return {"ruta": str(archivo.resolve()), "dispositivo": estado.st_dev, "inodo": estado.st_ino}


def _transitorio(archivo: Path) -> bool:
    return (
        archivo.name in TRANSITORIOS
        or archivo.name.endswith(("-wal", "-shm", ".lock", ".pyc"))
        or "__pycache__" in archivo.parts
        or ".pytest_cache" in archivo.parts
    )


def montajes(raiz: Path, configuracion: dict) -> list[str]:
    """Resolve configured corpus roots while rejecting overlapping mounts."""

    rutas = set(configuracion["rutas"])
    for patron in configuracion.get("patrones", []):
        rutas.update(p.relative_to(raiz).as_posix() for p in raiz.glob(patron))
    seleccion = sorted(nombre_seguro(p) for p in rutas if (raiz / p).exists())
    if any(Path(b).is_relative_to(a) for i, a in enumerate(seleccion) for b in seleccion[i + 1 :]):
        raise ValueError("Las raíces de datos no pueden solaparse")
    return seleccion


def inventariar(raiz: Path, rutas: list[str]) -> tuple[dict, dict, dict]:
    """Inventory corpus bytes, symlinks, and transient SQLite companions."""

    archivos, enlaces, wal = {}, {}, {}
    for rel in rutas:
        nombre_seguro(rel)
        origen = raiz / rel
        if origen.is_symlink():
            raise ValueError("La raíz de datos no puede ser un enlace")
        candidatos = sorted(origen.rglob("*")) if origen.is_dir() else [origen]
        for archivo in candidatos:
            nombre = nombre_seguro(archivo.relative_to(raiz).as_posix())
            if archivo.is_symlink():
                target = archivo.readlink()
                resuelto = (archivo.parent / target).resolve()
                if target.is_absolute() or not resuelto.is_relative_to(raiz.resolve()):
                    raise ValueError("Un enlace de datos sale de la raíz")
                relativo = resuelto.relative_to(raiz.resolve())
                if not any(relativo.is_relative_to(p) for p in rutas):
                    raise ValueError("Un enlace requiere datos no incluidos")
                enlaces[nombre] = str(target)
            elif archivo.is_file():
                if archivo.name.endswith("-wal") and archivo.stat().st_size:
                    wal[nombre] = digest(archivo)
                elif not _transitorio(archivo):
                    archivos[nombre] = {"sha256": digest(archivo), "bytes": archivo.stat().st_size}
    return archivos, enlaces, wal


def preparar(raiz: Path, configuracion: dict, destino: Path) -> dict:
    """Prepare a complete corpus package and deterministic retirement plan."""

    raiz = raiz.resolve()
    rutas = montajes(raiz, configuracion)
    if not rutas or any(destino.resolve().is_relative_to(raiz / p) for p in rutas):
        raise ValueError("El paquete requiere datos y un destino fuera de sus raíces")
    # Materializar WAL confirmado antes de fijar las huellas de los originales.
    # SQLite puede hacer este checkpoint al cerrar su último lector durante backup().
    for rel in rutas:
        for archivo in (raiz / rel).rglob("*.sqlite"):
            if archivo.is_symlink() or not archivo.with_name(archivo.name + "-wal").exists():
                continue
            with closing(sqlite3.connect(archivo.resolve().as_uri() + "?mode=rw", uri=True, timeout=1)) as db, db:
                if db.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0]:
                    raise ValueError("Hay un escritor SQLite activo; cierre la ejecución antes de preparar")
    originales, enlaces, wal = inventariar(raiz, rutas)
    max_bytes = limite_bytes(configuracion.get("max_bytes_sin_comprimir"))
    paquete = crear_paquete(raiz, list(originales), destino, max_bytes=max_bytes)
    if inventariar(raiz, rutas) != (originales, enlaces, wal):
        raise ValueError("Los datos cambiaron durante el respaldo; espere al escritor y prepare otro paquete")
    return {
        "version": VERSION,
        "paquete_local": paquete,
        "montajes": rutas,
        "enlaces": enlaces,
        "originales": originales,
        "wal": wal,
        "identidad_ledger": identidad_ledger(raiz / LEDGER),
        "max_bytes_sin_comprimir": max_bytes,
    }


def restaurar(archivo: Path, destino: Path, recibo: dict) -> dict:
    """Restore the exact remote corpus generation and verify all original paths."""

    if recibo.get("version") != VERSION:
        raise ValueError("Recibo de datos incompatible")
    max_bytes = limite_bytes(recibo.get("max_bytes_sin_comprimir"))
    rutas = [nombre_seguro(p) for p in recibo["montajes"]]
    # Validar enlaces y cobertura antes de escribir un solo archivo.
    with zipfile.ZipFile(archivo) as zip_:
        manifest = json.loads(zip_.read("MANIFEST_RESPALDO.json"))
    if manifest["huella_inventario"] != recibo["huella_inventario"]:
        raise ValueError("El inventario no corresponde al recibo")
    for nombre in [*manifest["archivos"], *recibo["enlaces"]]:
        nombre_seguro(nombre)
        if not any(Path(nombre).is_relative_to(p) for p in rutas):
            raise ValueError("Un artefacto sale de las raíces declaradas")
    for nombre, target in recibo["enlaces"].items():
        relativo = Path(nombre)
        resuelto = (destino / relativo.parent / target).resolve()
        if Path(target).is_absolute() or not resuelto.is_relative_to(destino.resolve()):
            raise ValueError("Un enlace restaurado sale del destino")
        if not any(resuelto.is_relative_to(destino.resolve() / p) for p in rutas):
            raise ValueError("Un enlace restaurado sale de los datos declarados")
        if any(Path(p).is_relative_to(relativo) for p in manifest["archivos"]):
            raise ValueError("Un enlace colisiona con un archivo")
    resultado = restaurar_paquete(archivo, destino, sha256=recibo["paquete"]["sha256"], max_bytes=max_bytes)
    for nombre, target in recibo["enlaces"].items():
        enlace = destino / nombre
        enlace.parent.mkdir(parents=True, exist_ok=True)
        enlace.symlink_to(target)
    resultado["sqlite_verificados"] = {n: v["sha256"] for n, v in manifest["archivos"].items() if n.endswith(".sqlite")}
    return resultado


def incorporar(restaurado: Path, raiz: Path, rutas: list[str]) -> None:
    """Restore original paths without overwriting files or following checkout symlinks."""
    raiz = raiz.resolve()
    for rel in rutas:
        nombre_seguro(rel)
        destino = raiz / rel
        if destino.exists() or destino.is_symlink():
            raise ValueError(f"Ya existe {rel}; restaure en otro directorio para no sobreescribir")
        for padre in destino.parents:
            if padre == raiz:
                break
            if padre.is_symlink():
                raise ValueError("Un padre del destino es un enlace")
    movidos = []
    try:
        for rel in rutas:
            origen, destino = restaurado / rel, raiz / rel
            if not origen.exists() and not origen.is_symlink():
                continue
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origen), destino)
            movidos.append(rel)
    except Exception:
        for rel in reversed(movidos):
            (restaurado / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(raiz / rel), restaurado / rel)
        raise


def retirar(raiz: Path, plan: dict, recibo: dict, configuracion: dict) -> dict:
    """Retire unchanged originals only after verified remote restoration."""
    if plan.get("version") != VERSION or recibo.get("version") != VERSION:
        raise ValueError("Plan o recibo incompatible")
    paquete = plan["paquete_local"]
    if (
        paquete["sha256"] != recibo["paquete"]["sha256"]
        or paquete["huella_inventario"] != recibo["huella_inventario"]
        or plan["montajes"] != recibo["montajes"]
        or plan["enlaces"] != recibo["enlaces"]
    ):
        raise ValueError("El recibo no corresponde al plan local")
    rutas = montajes(raiz, configuracion)
    if rutas != plan["montajes"] or inventariar(raiz, rutas) != (plan["originales"], plan["enlaces"], plan["wal"]):
        raise ValueError("Los datos cambiaron desde la subida; no se retira ningún archivo")
    # Renombres en el mismo filesystem; un fallo revierte todos los movimientos.
    movidos = []
    staging = Path(tempfile.mkdtemp(prefix=".gskg-retiro-", dir=raiz))
    try:
        for rel in rutas:
            destino = staging / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            os.replace(raiz / rel, destino)
            movidos.append(rel)
    except Exception:
        # Si también falla la reversión, preservar staging: nunca borrar la única copia local.
        for rel in reversed(movidos):
            os.replace(staging / rel, raiz / rel)
        shutil.rmtree(staging)
        raise
    shutil.rmtree(staging)
    return {"archivos_retirados": len(plan["originales"]), "rutas_retiradas": len(rutas)}
