"""Read the pinned complementary implementation layer; no request generates content."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from goes_science_kg.clases.complementaria_publicacion import leer_publicada

LOGGER = logging.getLogger(__name__)
IDENTIDAD = re.compile(r"(CURRICULO:V4|CLASE-UNIDAD-V4):[0-9a-f]{64}")


def crear_router_complementos(base: Path):
    """Build the read-only router for annexes and unit assessments with their national sources."""
    router = APIRouter(prefix="/api/v4/complementos", tags=["Capa complementaria"])
    estado, lock = {"documento": None}, Lock()

    def leer():
        try:
            with lock:
                if estado["documento"] is None:
                    estado["documento"] = leer_publicada(base)
                return estado["documento"]
        except (OSError, ValueError, KeyError, TypeError) as error:
            LOGGER.error("ROJO capa complementaria no verificable: %s", type(error).__name__)
            raise HTTPException(503, "No hay datos disponibles: restaure la capa complementaria verificada") from error

    def identidad(valor: str) -> str:
        if not IDENTIDAD.fullmatch(valor):
            raise HTTPException(404, "Identificador inválido")
        return valor

    @router.get("")
    def resumen():
        d = leer()
        return {
            "id": d["id"],
            "limite": d["limite"],
            "clases": len(d["clases"]),
            "unidades": len(d["unidades"]),
            "fuentes_nacionales": len(d["fuentes_nacionales"]),
            "retenidos": len(d["retenidos"]),
            "llamadas_modelos_por_peticion": 0,
        }

    @router.get("/clases")
    def clases(grado: Annotated[int | None, Query(ge=2, le=11)] = None):
        d = leer()
        return [
            {"fila_id": f, "titulo": c["titulo"], "grado": c["grado"], "unidad_id": c["unidad_id"]}
            for f, c in sorted(d["clases"].items())
            if grado is None or c["grado"] == grado
        ]

    @router.get("/clases/{fila_id}")
    def clase(fila_id: str):
        c = leer()["clases"].get(identidad(fila_id))
        if c is None:
            raise HTTPException(404, "No hay anexo publicado para esa clase")
        return c

    @router.get("/unidades/{unidad_id}")
    def unidad(unidad_id: str):
        u = leer()["unidades"].get(identidad(unidad_id))
        if u is None:
            raise HTTPException(404, "No hay evaluación publicada para esa unidad")
        return u

    @router.get("/fuentes")
    def fuentes():
        return leer()["fuentes_nacionales"]

    return router
