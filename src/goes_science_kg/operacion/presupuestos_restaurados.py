"""Re-vincula copias verificadas del ledger sin modificar reservas ni checkpoints."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from uuid import uuid4

from goes_science_kg.operacion.datos_externos import LEDGER, digest, identidad_ledger
from goes_science_kg.operacion.respaldo import nombre_seguro


def migrar_presupuestos(raiz: Path, recibo: dict, sqlites: dict[str, str]) -> dict:
    """Sólo para copias recién restauradas: todos los bytes deben coincidir con el paquete GCS."""
    if not sqlites:
        return {"vinculos_actualizados": 0}
    for rel, sha in sqlites.items():
        nombre_seguro(rel)
        archivo = raiz / rel
        if archivo.is_symlink() or digest(archivo) != sha:
            raise ValueError("Un SQLite cambió después de restaurarse; no se migra ningún presupuesto")
    if LEDGER not in sqlites or not recibo.get("identidad_ledger"):
        raise ValueError("Falta la identidad original del ledger verificado")
    anterior = json.dumps(recibo["identidad_ledger"], sort_keys=True)
    nueva = json.dumps(identidad_ledger(raiz / LEDGER), sort_keys=True)
    cambios = []
    with sqlite3.connect(":memory:", uri=True) as db:
        db.execute("ATTACH DATABASE ? AS registro", ((raiz / LEDGER).resolve().as_uri() + "?mode=ro",))
        resumen = db.execute(
            "SELECT ejecucion,COUNT(*),SUM(reserva_usd) FROM registro.llamadas GROUP BY ejecucion ORDER BY ejecucion"
        ).fetchall()
        for i, rel in enumerate(sorted(sqlites)):
            if rel == LEDGER:
                continue
            alias = f"c{i}"
            db.execute(f"ATTACH DATABASE ? AS {alias}", ((raiz / rel).resolve().as_uri() + "?mode=rw",))
            if not db.execute(
                f"SELECT 1 FROM {alias}.sqlite_master WHERE name='checkpoint_presupuestos'"
            ).fetchone():
                continue
            filas = db.execute(
                f"SELECT ejecucion,ledger FROM {alias}.checkpoint_presupuestos ORDER BY ejecucion"
            ).fetchall()
            if any(identidad != anterior for _, identidad in filas):
                raise ValueError("Un checkpoint no pertenece al ledger original del paquete")
            cambios.append({"archivo": rel, "alias": alias, "ejecuciones": [p[0] for p in filas]})
        # Auditoría previa al UPDATE; sólo se actualiza la identidad física, nunca las tablas del ledger.
        auditoria = {
            "version": "migracion-presupuestos-restaurados-1",
            "estado": "preparado",
            "paquete_sha256": recibo["paquete"]["sha256"],
            "huella_inventario": recibo["huella_inventario"],
            "sqlite_verificados": sqlites,
            "identidad_anterior": json.loads(anterior),
            "identidad_nueva": json.loads(nueva),
            "reservas_por_ejecucion": [
                {"ejecucion": ejecucion, "llamadas": llamadas, "reserva_usd": reserva}
                for ejecucion, llamadas, reserva in resumen
            ],
            "vinculos": cambios,
        }
        salida = raiz / "data/operaciones/migraciones" / f"restauracion-{uuid4().hex}.json"
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        try:
            db.execute("BEGIN IMMEDIATE")
            for cambio in cambios:
                db.execute(
                    f"UPDATE {cambio['alias']}.checkpoint_presupuestos SET ledger=? WHERE ledger=?", (nueva, anterior)
                )
            if digest(raiz / LEDGER) != sqlites[LEDGER]:
                raise ValueError("El ledger cambió durante la migración")
            db.commit()
        except Exception:
            db.rollback()
            raise
        auditoria["estado"] = "completado"
        temporal = salida.with_suffix(".tmp")
        temporal.write_text(json.dumps(auditoria, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporal.replace(salida)
    return {"vinculos_actualizados": sum(len(c["ejecuciones"]) for c in cambios), "auditoria": str(salida)}
