"""Lectura y descargas de la biblioteca docente fijada; ninguna petición genera contenido."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response

from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import markdown, serializar, sha

LOGGER = logging.getLogger(__name__)
Version = Literal["V4", "V3", "historico"]
Tipo = Literal[
    "paquete_objetivo",
    "paquete_unidad",
    "paquete_indicador",
    "fila_fuera_alcance",
    "paquete_historico",
    "actividad",
    "experimento",
    "microtema",
    "dificultad",
    "recorrido",
    "unidad_experimental",
    "guion_clase",
    "guion_unidad",
]


def crear_router_materiales(
    base: Path,
    *,
    directorio: str = "data/materiales",
    prefijo: str = "/api/v4/materiales",
    etiqueta: str = "Materiales docentes",
):
    router = APIRouter(prefix=prefijo, tags=[etiqueta])
    biblioteca, lock = None, Lock()

    def leer():
        nonlocal biblioteca
        try:
            with lock:
                if biblioteca is None:
                    candidato = Biblioteca(base / directorio)
                    candidato.validar()
                    biblioteca = candidato
                biblioteca.comprobar()
                return biblioteca
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error) as error:
            LOGGER.error("ROJO biblioteca docente no verificable: %s", type(error).__name__)
            raise HTTPException(
                503, "Biblioteca no disponible; restaure los materiales verificados y reinicie"
            ) from error

    def consultar(operacion):
        try:
            return operacion(leer())
        except KeyError as error:
            raise HTTPException(404, "Material o archivo no encontrado en esta biblioteca") from error
        except (OSError, ValueError, TypeError, sqlite3.Error) as error:
            LOGGER.error("ROJO consulta docente invalidada: %s", type(error).__name__)
            raise HTTPException(503, "La biblioteca cambió o no puede verificarse") from error

    def obtener(id_):
        if len(id_) > 300:
            raise HTTPException(422, "Identificador demasiado largo")
        try:
            return consultar(lambda b: b.detalle(id_))
        except KeyError as error:
            raise HTTPException(404, "Material no encontrado en esta biblioteca") from error

    def descarga(contenido, tipo, nombre):
        return Response(
            contenido,
            media_type=tipo,
            headers={
                "Content-Disposition": f'attachment; filename="{nombre}"',
                "ETag": '"' + sha(contenido) + '"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "private, no-cache",
            },
        )

    @router.get("/salud")
    def salud():
        m = leer().manifest
        return {
            "estado": "verificado",
            "biblioteca_id": m["id"],
            "materiales": m["materiales"],
            "por_tipo": m["por_tipo"],
            "por_version": m["por_version"],
            "llamadas_modelos_por_peticion": 0,
            "snapshot_id": m["procedencia"]["snapshot_id"],
            "edicion": m["procedencia"].get("edicion"),
            "estado_revision_contenido": m["procedencia"].get("estado_revision"),
        }

    @router.get("/manifest")
    def manifest():
        return leer().manifest

    @router.get("")
    def listar(
        version: Version = "V4",
        tipo: Tipo | None = None,
        grado: Annotated[int | None, Query(ge=2, le=11)] = None,
        asignatura: Annotated[str | None, Query(max_length=100)] = None,
        fila_id: Annotated[str | None, Query(max_length=200)] = None,
        q: Annotated[str, Query(max_length=200)] = "",
        limite: Annotated[int, Query(ge=1, le=200)] = 40,
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
    ):
        return consultar(
            lambda b: b.listar(
                version=version,
                tipo=tipo,
                grado=grado,
                asignatura=asignatura,
                fila_id=fila_id,
                q=q,
                limite=limite,
                offset=offset,
            )
        )

    @router.get("/archivos/{digest}")
    def archivo(digest: str):
        if not re.fullmatch(r"[a-f0-9]{64}", digest):
            raise HTTPException(422, "Se requiere un SHA-256 válido")
        try:
            contenido, rutas = consultar(lambda b: b.archivo(digest))
        except KeyError as error:
            raise HTTPException(404, "Archivo no encontrado") from error
        extension = Path(rutas[0]).suffix
        tipo = {
            ".json": "application/json",
            ".md": "text/markdown",
            ".xml": "application/xml",
            ".cnxml": "application/xml",
            ".zip": "application/zip",
            ".txt": "text/plain",
            ".csv": "text/csv",
        }.get(extension, "application/octet-stream")
        return descarga(contenido, tipo, digest + extension)

    @router.get("/descarga/{id_:path}")
    def descargar(
        id_: str,
        formato: Literal["json", "md", "zip"] = "json",
        audiencia: Literal["docente", "estudiante"] = "docente",
    ):
        d = obtener(id_)
        if formato == "zip":
            if d["tipo"] != "paquete_indicador" or audiencia != "docente":
                raise HTTPException(422, "El ZIP individual requiere un paquete por indicador y audiencia docente")
            b = leer()
            ruta = "indicadores/" + sha(id_.encode()) + ".zip"
            ref = b.manifest["originales"].get(ruta)
            if ref is None:
                raise HTTPException(503, "El paquete por indicador no tiene un ZIP verificable")
            contenido, _ = consultar(lambda b: b.archivo(ref["sha256"]))
            return descarga(contenido, "application/zip", ref["sha256"] + ".zip")
        if audiencia == "estudiante":
            if formato != "md" or d["tipo"] != "guion_clase":
                raise HTTPException(422, "La hoja de estudiante requiere un guion_clase y formato md")
            from goes_science_kg.clases.lectura import markdown_clase

            contenido = markdown_clase(d, estudiante=True).encode()
        else:
            contenido = serializar(d) if formato == "json" else markdown(d).encode()
        return descarga(
            contenido, "application/json" if formato == "json" else "text/markdown", sha(contenido) + "." + formato
        )

    @router.get("/detalle/{id_:path}")
    def detalle(id_: str):
        return {"biblioteca_id": leer().manifest["id"], "material": obtener(id_)}

    return router
