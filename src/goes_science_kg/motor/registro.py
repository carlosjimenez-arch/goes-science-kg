"""Presupuesto durable y caché por contenido; las reservas sobreviven a reinicios."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


class PresupuestoAgotado(RuntimeError):
    """No se inicia una llamada que sobrepase los límites de ejecución."""


class Registro:
    def __init__(self, archivo: Path):
        archivo.parent.mkdir(parents=True, exist_ok=True)
        self.archivo = archivo
        with self.conexion() as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS llamadas (
                    id TEXT PRIMARY KEY, ejecucion TEXT NOT NULL, clave TEXT NOT NULL,
                    modelo TEXT NOT NULL, rol TEXT NOT NULL, reserva_usd REAL NOT NULL,
                    estado TEXT NOT NULL, entrada_tokens INTEGER, salida_tokens INTEGER,
                    latencia_ms REAL, creada TEXT DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS llamadas_ejecucion ON llamadas(ejecucion);
                CREATE TABLE IF NOT EXISTS cache (
                    clave TEXT PRIMARY KEY, respuesta TEXT NOT NULL
                );
            """)

    @contextmanager
    def conexion(self):
        db = sqlite3.connect(self.archivo, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def reservar(
        self,
        *,
        ejecucion: str,
        clave: str,
        modelo: str,
        rol: str,
        reserva_usd: float,
        max_llamadas: int,
        max_usd: float,
    ) -> str:
        if reserva_usd <= 0 or max_llamadas <= 0 or max_usd <= 0:
            raise ValueError("Presupuesto y reserva deben ser positivos")
        with self.conexion() as db:
            db.execute("BEGIN IMMEDIATE")
            total, reservado = db.execute(
                "SELECT COUNT(*), COALESCE(SUM(reserva_usd),0) FROM llamadas WHERE ejecucion=?",
                (ejecucion,),
            ).fetchone()
            if total >= max_llamadas or reservado + reserva_usd > max_usd:
                raise PresupuestoAgotado(f"Límite: {total}/{max_llamadas} llamadas, reserva USD {reservado:.4f}")
            id_llamada = uuid4().hex
            db.execute(
                "INSERT INTO llamadas(id,ejecucion,clave,modelo,rol,reserva_usd,estado) VALUES(?,?,?,?,?,?,?)",
                (id_llamada, ejecucion, clave, modelo, rol, reserva_usd, "reservada"),
            )
            return id_llamada

    def terminar(
        self,
        id_llamada: str,
        *,
        estado: str,
        latencia_ms: float,
        entrada_tokens: int | None = None,
        salida_tokens: int | None = None,
    ) -> None:
        with self.conexion() as db:
            db.execute(
                "UPDATE llamadas SET estado=?,latencia_ms=?,entrada_tokens=?,salida_tokens=? WHERE id=?",
                (estado, latencia_ms, entrada_tokens, salida_tokens, id_llamada),
            )

    def cache(self, clave: str) -> dict | None:
        with self.conexion() as db:
            fila = db.execute("SELECT respuesta FROM cache WHERE clave=?", (clave,)).fetchone()
        return json.loads(fila[0]) if fila else None

    def guardar_cache(self, clave: str, respuesta: dict) -> None:
        with self.conexion() as db:
            db.execute("INSERT OR REPLACE INTO cache VALUES(?,?)", (clave, json.dumps(respuesta, ensure_ascii=False)))

    def resumen(self, ejecucion: str) -> dict:
        with self.conexion() as db:
            filas = db.execute(
                "SELECT modelo,rol,estado,reserva_usd,entrada_tokens,salida_tokens,latencia_ms "
                "FROM llamadas WHERE ejecucion=? ORDER BY creada,id",
                (ejecucion,),
            ).fetchall()
        return {
            "llamadas": len(filas),
            "reserva_usd": sum(f["reserva_usd"] for f in filas),
            "detalle": [dict(f) for f in filas],
        }
