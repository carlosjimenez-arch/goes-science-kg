"""Rebind verified ledger copies without changing reservations or graph states."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from goes_science_kg.operacion.datos_externos import LEDGER, digest, identidad_ledger
from goes_science_kg.operacion.respaldo import nombre_seguro


def _verificar(raiz, sqlites):
    """Reject any packaged SQLite that changed, escaped the root, or has pending WAL bytes."""
    for rel, sha in sqlites.items():
        nombre_seguro(rel)
        archivo = raiz / rel
        wal = archivo.with_name(archivo.name + "-wal")
        if (
            archivo.is_symlink()
            or not archivo.resolve().is_relative_to(raiz.resolve())
            or digest(archivo) != sha
            or (wal.exists() and wal.stat().st_size)
        ):
            raise ValueError("Un SQLite cambió después de restaurarse; no se migra ningún presupuesto")


def migrar_presupuestos(raiz: Path, recibo: dict, sqlites: dict[str, str], *, sustituir=None) -> dict:
    """Rebind restored checkpoints to the new ledger identity, one database at a time.

    Handles dozens of databases without exceeding SQLITE_MAX_ATTACHED. It only runs on a complete
    restoration without writers: every database is verified, updated copies are staged, and the
    original bytes are kept to revert a failed installation. The ledger is opened read-only and is
    never replaced. Graph states are not executed.
    """
    if not sqlites:
        return {"vinculos_actualizados": 0}
    _verificar(raiz, sqlites)
    if LEDGER not in sqlites or not recibo.get("identidad_ledger"):
        raise ValueError("Falta la identidad original del ledger verificado")
    anterior = json.dumps(recibo["identidad_ledger"], sort_keys=True)
    nueva = json.dumps(identidad_ledger(raiz / LEDGER), sort_keys=True)
    with closing(sqlite3.connect((raiz / LEDGER).resolve().as_uri() + "?mode=ro", uri=True)) as db:
        resumen = db.execute(
            "SELECT ejecucion,COUNT(*),SUM(reserva_usd) FROM llamadas GROUP BY ejecucion ORDER BY ejecucion"
        ).fetchall()
    cambios = []
    for rel in sorted(sqlites):
        if rel == LEDGER:
            continue
        with closing(sqlite3.connect((raiz / rel).resolve().as_uri() + "?mode=ro", uri=True)) as db:
            if not db.execute("SELECT 1 FROM sqlite_master WHERE name='checkpoint_presupuestos'").fetchone():
                continue
            filas = db.execute("SELECT ejecucion,ledger FROM checkpoint_presupuestos ORDER BY ejecucion").fetchall()
        if any(identidad != anterior for _, identidad in filas):
            raise ValueError("Un checkpoint no pertenece al ledger original del paquete")
        if filas:
            cambios.append({"archivo": rel, "ejecuciones": [p[0] for p in filas]})
    auditoria = {
        "version": "migracion-presupuestos-restaurados-1",
        "estado": "preparado",
        "metodo": "copias_verificadas_con_reversion",
        "paquete_sha256": recibo["paquete"]["sha256"],
        "huella_inventario": recibo["huella_inventario"],
        "sqlite_verificados": sqlites,
        "identidad_anterior": json.loads(anterior),
        "identidad_nueva": json.loads(nueva),
        "reservas_por_ejecucion": [{"ejecucion": e, "llamadas": n, "reserva_usd": r} for e, n, r in resumen],
        "vinculos": cambios,
    }
    salida = raiz / "data/operaciones/migraciones" / f"restauracion-{uuid4().hex}.json"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    staging = Path(tempfile.mkdtemp(prefix=".presupuestos-", dir=salida.parent))
    reemplazar = sustituir or os.replace
    instalados, preservar = [], False
    try:
        for i, cambio in enumerate(cambios):
            carpeta = staging / str(i)
            carpeta.mkdir()
            original, actualizado = carpeta / "original.sqlite", carpeta / "actualizado.sqlite"
            shutil.copy2(raiz / cambio["archivo"], original)
            if digest(original) != sqlites[cambio["archivo"]]:
                raise ValueError("Un SQLite cambió mientras se copiaba")
            shutil.copy2(original, actualizado)
            with closing(sqlite3.connect(actualizado)) as db:
                with db:
                    db.execute("UPDATE checkpoint_presupuestos SET ledger=? WHERE ledger=?", (nueva, anterior))
                if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise ValueError("La copia migrada no supera la integridad SQLite")
            cambio["sha256_actualizado"] = digest(actualizado)
        _verificar(raiz, sqlites)
        for i, cambio in enumerate(cambios):
            reemplazar(staging / str(i) / "actualizado.sqlite", raiz / cambio["archivo"])
            instalados.append(i)
        wal_ledger = (raiz / LEDGER).with_name("registro.sqlite-wal")
        if digest(raiz / LEDGER) != sqlites[LEDGER] or (wal_ledger.exists() and wal_ledger.stat().st_size):
            raise ValueError("El ledger cambió durante la migración")
        auditoria["estado"] = "completado"
    except BaseException:
        errores = []
        for i in reversed(instalados):
            try:
                reemplazar(staging / str(i) / "original.sqlite", raiz / cambios[i]["archivo"])
            except BaseException:
                errores.append(cambios[i]["archivo"])
        preservar = bool(errores)
        auditoria["estado"] = "reversion_pendiente" if errores else "revertido"
        if errores:
            auditoria["copias_para_recuperar"] = str(staging)
            auditoria["reversion_pendiente"] = errores
        raise
    finally:
        temporal = salida.with_suffix(".tmp")
        temporal.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(salida)
        if not preservar:
            shutil.rmtree(staging)
    return {"vinculos_actualizados": sum(len(c["ejecuciones"]) for c in cambios), "auditoria": str(salida)}
