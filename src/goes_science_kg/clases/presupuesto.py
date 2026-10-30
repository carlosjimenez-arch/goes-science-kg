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
        todas = [
            dict(r)
            for r in db.execute(
                "SELECT * FROM llamadas WHERE ejecucion=? ORDER BY creada,id",
                (cfg["ejecucion"],),
            )
        ]
        total, reserva = db.execute(
            "SELECT COUNT(*),COALESCE(SUM(reserva_usd),0) FROM llamadas WHERE ejecucion=?",
            (cfg["ejecucion"],),
        ).fetchone()
    filas = todas[: cfg["baseline"]["llamadas"]]
    if (
        len(filas) != cfg["baseline"]["llamadas"]
        or hashlib.sha256(serializar(filas)).hexdigest() != cfg["baseline"]["filas_sha256"]
    ):
        raise ValueError("El ledger no conserva íntegro el consumo anterior autorizado")
    if punto := cfg.get("punto_continuidad"):
        base = ruta(".").resolve()
        archivo_punto = base / punto["ruta"]
        if (
            archivo_punto.is_symlink()
            or any(p.is_symlink() for p in archivo_punto.parents)
            or not archivo_punto.resolve().is_relative_to(base)
            or not archivo_punto.is_file()
        ):
            raise ValueError("Falta el punto de continuidad del ledger; no use un respaldo anterior")
        raw = archivo_punto.read_bytes()
        if hashlib.sha256(raw).hexdigest() != punto["sha256"]:
            raise ValueError("El punto de continuidad del presupuesto cambió")
        guardado = json.loads(raw)
        actuales = {r["id"]: r for r in todas}
        if (
            guardado["version"] != "continuidad-presupuesto-clases-1"
            or guardado["ejecucion"] != cfg["ejecucion"]
            or len(guardado["filas_sha256"]) != guardado["llamadas"]
            or guardado["llamadas"] != punto["llamadas"]
            or total < guardado["llamadas"]
            or reserva + 1e-9 < guardado["reserva_usd"]
            or any(
                id_ not in actuales or hashlib.sha256(serializar(actuales[id_])).hexdigest() != esperado
                for id_, esperado in guardado["filas_sha256"].items()
            )
        ):
            raise ValueError("El ledger retrocede o altera consumo posterior al presupuesto inicial")
    _verificar_ampliaciones(cfg)
    return {"llamadas": total, "reserva_usd": reserva, "baseline_verificado": True}


def _verificar_ampliaciones(cfg):
    """Tie the effective cap to the last authorized extension and its private literal receipt."""
    ampliaciones = cfg.get("ampliaciones") or []
    if not ampliaciones:
        return
    vigente = ampliaciones[-1]
    if (cfg["max_llamadas_acumuladas"], cfg["max_reserva_usd_acumulada"]) != (
        vigente["max_llamadas_acumuladas"],
        vigente["max_reserva_usd_acumulada"],
    ):
        raise ValueError("El tope vigente no coincide con la última ampliación autorizada")
    base = ruta(".").resolve()
    for ampliacion in ampliaciones:
        recibo = base / ampliacion["recibo_literal_privado"]
        if (
            recibo.is_symlink()
            or not recibo.resolve().is_relative_to(base)
            or not recibo.is_file()
            or hashlib.sha256(recibo.read_bytes()).hexdigest() != ampliacion["recibo_sha256"]
        ):
            raise ValueError("El recibo de una ampliación de presupuesto falta o cambió")


def fijar_punto(archivo: Path, salida: Path, *, cfg=None):
    """Fija llamadas ya terminadas; no modifica el contador ni adopta la configuración pública."""
    cfg = cfg or configuracion()
    comprobar_continuidad(archivo, cfg)
    with closing(sqlite3.connect(archivo.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        filas = [
            dict(r)
            for r in db.execute("SELECT * FROM llamadas WHERE ejecucion=? ORDER BY creada,id", (cfg["ejecucion"],))
        ]
    if any(r["estado"] == "reservada" for r in filas):
        raise ValueError("Hay llamadas pendientes; no se fija un punto de continuidad")
    documento = {
        "version": "continuidad-presupuesto-clases-1",
        "ejecucion": cfg["ejecucion"],
        "llamadas": len(filas),
        "reserva_usd": sum(r["reserva_usd"] for r in filas),
        "filas_sha256": {r["id"]: hashlib.sha256(serializar(r)).hexdigest() for r in filas},
        "limite": "Punto mínimo de consumo histórico. No reinicia, devuelve ni amplía invocaciones o reserva.",
    }
    raw = serializar(documento)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("xb") as f:
        f.write(raw)
    return {"sha256": hashlib.sha256(raw).hexdigest(), "llamadas": len(filas), "reserva_usd": documento["reserva_usd"]}
