"""Catálogo exacto por indicador y descargas, sin reclasificar ni generar al consultar."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response

from goes_science_kg.api_materiales import crear_router_materiales
from goes_science_kg.interfaz.consulta import normalizar
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import sha

LOGGER = logging.getLogger(__name__)
PREFIJO = "/api/v4/produccion/indicadores"
DIRECTORIO = "data/materiales_indicadores_v4"


def crear_router_indicadores(base: Path):
    router = APIRouter()
    catalogo = APIRouter(prefix=PREFIJO, tags=["Paquetes por indicador de logro"])
    biblioteca, indice, auditoria = None, None, None
    lock = Lock()

    def leer():
        nonlocal biblioteca, indice, auditoria
        try:
            with lock:
                if biblioteca is None:
                    b = Biblioteca(base / DIRECTORIO)
                    b.validar()

                    def documento(ruta):
                        ref = b.manifest["originales"][ruta]
                        return json.loads(b.archivo(ref["sha256"])[0])

                    i = documento("indicadores/indice.json")
                    a = documento("indicadores/auditoria.json")
                    if len(i["indicadores"]) != b.manifest["materiales"] or a["paquetes"] != b.manifest["materiales"]:
                        raise ValueError("El catálogo no cubre la biblioteca")
                    biblioteca, indice, auditoria = b, i, a
                biblioteca.comprobar()
                return biblioteca, indice, auditoria
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            LOGGER.error("ROJO catálogo de indicadores no disponible: %s", type(error).__name__)
            raise HTTPException(503, "Restaure la biblioteca de indicadores y reinicie el servicio") from error

    @catalogo.get("/indice")
    def listar(
        codigo: Annotated[str | None, Query(max_length=40)] = None,
        grado: Annotated[int | None, Query(ge=2, le=11)] = None,
        asignatura: Annotated[str | None, Query(max_length=100)] = None,
        unidad: Annotated[str | None, Query(max_length=200)] = None,
        fila_id: Annotated[str | None, Query(max_length=200)] = None,
        origen: Literal["malla_final", "completacion_derivada"] | None = None,
        estado_contextos: Literal["contextos_con_revision_completa", "contextos_con_pendientes"] | None = None,
        q: Annotated[str, Query(max_length=200)] = "",
        limite: Annotated[int, Query(ge=1, le=200)] = 40,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
    ):
        b, i, _ = leer()
        consulta = normalizar(q).strip()
        filas = [
            f
            for f in i["indicadores"]
            if (codigo is None or codigo == f["codigo"])
            and (grado is None or grado == f["grado"])
            and (asignatura is None or asignatura == f["asignatura"])
            and (unidad is None or unidad == f["unidad"])
            and (fila_id is None or fila_id in f["filas_ids"])
            and (origen is None or origen == f["origen"])
            and (estado_contextos is None or estado_contextos == f["estado_contextos"])
            and (not consulta or consulta in normalizar(" ".join([f["indicador"], *f["indicadores_docentes"]])))
        ]
        return {
            "biblioteca_id": b.manifest["id"],
            "total": len(filas),
            "offset": offset,
            "limite": limite,
            "indicadores": filas[offset : offset + limite],
            "estado_reagrupamiento": "sin_revision_especifica",
            "llamadas_modelos": 0,
            "alcance": i["limite"],
        }

    @catalogo.get("/auditoria")
    def auditar():
        b, _, a = leer()
        return {"biblioteca_id": b.manifest["id"], "auditoria": a}

    @catalogo.get("/catalogo.csv")
    def csv():
        b, _, _ = leer()
        ref = b.manifest["originales"]["indicadores/catalogo.csv"]
        raw, _ = b.archivo(ref["sha256"])
        return Response(
            raw,
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="indicadores-ciencias-v4.csv"',
                "ETag": '"' + sha(raw) + '"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, no-cache",
            },
        )

    router.include_router(catalogo)
    router.include_router(
        crear_router_materiales(
            base, directorio=DIRECTORIO, prefijo=PREFIJO, etiqueta="Paquetes por indicador de logro"
        )
    )
    return router
