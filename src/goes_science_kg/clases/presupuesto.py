"""Impide iniciar la ampliación desde un ledger vacío, truncado o con consumo anterior alterado."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.materiales.compilacion import serializar


def configuracion():
    return json.loads(ruta("config/presupuesto_clases_v4.json").read_bytes())


def comprobar_continuidad(archivo: Path, cfg=None):
    cfg = cfg or configuracion()
    if not archivo.is_file() or archivo.is_symlink():
        raise ValueError("Falta el ledger acumulado de Ciencias; no se crea otro contador")
    with closing(sqlite3.connect(archivo.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        filas = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM llamadas WHERE ejecucion=? ORDER BY creada,id LIMIT ?",
                (cfg["ejecucion"], cfg["baseline"]["llamadas"]),
            )
        ]
        total, reserva = db.execute(
            "SELECT COUNT(*),COALESCE(SUM(reserva_usd),0) FROM llamadas WHERE ejecucion=?",
            (cfg["ejecucion"],),
        ).fetchone()
    if (
        len(filas) != cfg["baseline"]["llamadas"]
        or hashlib.sha256(serializar(filas)).hexdigest() != cfg["baseline"]["filas_sha256"]
    ):
        raise ValueError("El ledger no conserva íntegro el consumo anterior autorizado")
    return {"llamadas": total, "reserva_usd": reserva, "baseline_verificado": True}
