"""Consulta indexada de oportunidades de práctica, sin inferir dominio ni ejecutar modelos."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query

from goes_science_kg.materiales.almacen import Biblioteca

LOGGER = logging.getLogger(__name__)
Codigo = Literal["E1", "E2", "E3", "E4", "E5", "E6", "D1", "D2", "D3", "D4", "I1", "I2", "I3", "I4", "I5"]
Macro = Literal["explicacion_modelizacion", "indagacion_datos", "informacion_argumentacion_decisiones"]


def crear_router_didactica(base: Path):
    router = APIRouter(prefix="/api/v4/produccion/didactica", tags=["Diseño didáctico propuesto"])
    biblioteca, indice, auditoria = None, None, None
    lock = Lock()

    def leer():
        nonlocal biblioteca, indice, auditoria
        try:
            with lock:
                if biblioteca is None:
                    b = Biblioteca(base / "data/materiales_produccion_v4")
                    b.validar()

                    def documento(nombre):
                        ref = b.manifest["originales"]["didactica/" + nombre + ".json"]
                        return json.loads(b.archivo(ref["sha256"])[0])

                    i, a = documento("indice"), documento("auditoria")
                    if i["huella_curriculo"] != b.manifest["procedencia"]["snapshot_id"]:
                        raise ValueError("El índice no corresponde a la biblioteca")
                    if len(i["filas"]) != b.manifest["por_tipo"]["paquete_objetivo"]:
                        raise ValueError("El índice perdió objetivos")
                    biblioteca, indice, auditoria = b, i, a
                biblioteca.comprobar()
                return biblioteca.manifest["id"], indice, auditoria
        except (OSError, ValueError, KeyError, TypeError) as error:
            LOGGER.error("ROJO índice didáctico no disponible: %s", type(error).__name__)
            raise HTTPException(503, "Restaure la biblioteca con diseño didáctico y reinicie el servicio") from error

    @router.get("/habilidades")
    def habilidades(
        codigo: Codigo | None = None,
        macro: Macro | None = None,
        grado: Annotated[int | None, Query(ge=2, le=11)] = None,
        asignatura: Annotated[str | None, Query(max_length=100)] = None,
        limite: Annotated[int, Query(ge=1, le=200)] = 40,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
    ):
        id_, i, _ = leer()
        filas = [
            f
            for f in i["filas"]
            if (codigo is None or codigo in f["codigos"])
            and (macro is None or macro in f["macrohabilidades"])
            and (grado is None or grado == f["grado"])
            and (asignatura is None or asignatura == f["asignatura"])
        ]
        return {
            "biblioteca_id": id_,
            "total": len(filas),
            "offset": offset,
            "limite": limite,
            "filas": filas[offset : offset + limite],
            "alcance": i["limite"],
            "estado_revision": "propuesta_didactica_pendiente_revision",
            "dominio_observado": None,
            "llamadas_modelos": 0,
        }

    @router.get("/macrohabilidades")
    def macrohabilidades():
        id_, i, _ = leer()
        return {"biblioteca_id": id_, "macrohabilidades": i["macrohabilidades"], "alcance": i["limite"]}

    @router.get("/auditoria")
    def auditar():
        id_, _, a = leer()
        return {"biblioteca_id": id_, "auditoria": a}

    return router
