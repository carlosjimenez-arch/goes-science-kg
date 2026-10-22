"""API de la aplicación curricular: consultas reales y briefs documentales sin invocar modelos."""

from __future__ import annotations

import logging
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from threading import Lock
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from goes_science_kg.interfaz.consulta import ConsultaInterfaz, normalizar
from goes_science_kg.motor.contratos import Asignatura

LOGGER = logging.getLogger(__name__)
DIRECTORIO = Path(__file__).parent / "interfaz" / "estaticos"
Grado = Annotated[int | None, Query(ge=2, le=11)]
Texto = Annotated[str, Query(max_length=200)]


class SolicitudBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    filas_ids: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(min_length=1, max_length=20)
    formato: Literal["evaluacion", "cinco_fases"] = "evaluacion"


def registrar_interfaz(app):
    """Los assets no contienen corpus ni semillas. El navegador consulta la API de su mismo origen."""

    @app.get("/", include_in_schema=False)
    def inicio():
        return RedirectResponse("/app/", status_code=307)

    app.mount("/app", StaticFiles(directory=DIRECTORIO, html=True), name="interfaz")

    @app.middleware("http")
    async def cabeceras(peticion, siguiente):
        respuesta = await siguiente(peticion)
        if peticion.url.path.startswith(("/app", "/api/v4/interfaz")):
            respuesta.headers["X-Content-Type-Options"] = "nosniff"
            respuesta.headers["Referrer-Policy"] = "no-referrer"
            respuesta.headers["Cache-Control"] = "private, no-store"
            respuesta.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            )
        return respuesta


def crear_router_interfaz(leer, base: Path):
    router = APIRouter(prefix="/interfaz", tags=["Aplicación curricular"])
    cache, lock = {}, Lock()

    def consultar():
        runtime = leer()  # Revalida el snapshot también cuando la proyección ya está en caché.
        with lock:
            id_ = runtime.producto.manifest.snapshot_id
            if id_ not in cache:
                try:
                    cache[id_] = ConsultaInterfaz(runtime)
                except ValueError as error:
                    raise HTTPException(409, str(error)) from error
            return cache[id_]

    def verificar_fila(servicio, fila_id):
        from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila

        try:
            if not servicio.runtime.fuentes.hidratar_celdas(documento_de_fila(servicio.filas[fila_id])):
                raise ValueError("La fuente no contiene celdas verificables")
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(503, "No se pudo verificar la fuente original de la fila") from error

    @router.get("/resumen")
    def resumen():
        return consultar().resumen()

    @router.get("/filas")
    def filas(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limite: Annotated[int, Query(ge=1, le=200)] = 40,
        solo_alertas: bool = False,
    ):
        s = consultar()
        seleccion = s.seleccionar(grado, disciplina, q)
        if solo_alertas:
            seleccion = [f for f in seleccion if f.id in s.runtime.fuentes.bloqueos_efectivos]
        seleccion.sort(key=lambda f: (f.grado, f.asignatura_malla, f.hoja, f.fila))
        return s.identidad | {
            "total": len(seleccion),
            "offset": offset,
            "limite": limite,
            "filas": [s.ficha(f) for f in seleccion[offset : offset + limite]],
        }

    @router.get("/filas/{fila_id}")
    def fila(fila_id: str):
        s = consultar()
        if fila_id not in s.filas:
            raise HTTPException(404, "La fila no pertenece al snapshot")
        verificar_fila(s, fila_id)
        return s.detalle(fila_id)

    @router.get("/documentos")
    def documentos(q: Texto = "", tipo: Literal["curriculo", "referencia"] | None = None):
        s = consultar()
        seleccion = [
            d
            for d in s.documentos.values()
            if (not q or normalizar(q) in normalizar(d["titulo"] + " " + d["id"]))
            and (tipo is None or d["tipo"] == tipo)
        ]
        return s.identidad | {"total": len(seleccion), "documentos": sorted(seleccion, key=lambda d: d["titulo"])}

    @router.get("/grafo")
    def grafo(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        limite: Annotated[int, Query(ge=10, le=800)] = 260,
    ):
        return consultar().grafo(grado=grado, disciplina=disciplina, q=q, limite=limite)

    @router.get("/nodos/{nodo_id}")
    def nodo(nodo_id: str):
        s = consultar()
        if nodo_id not in s.nodos:
            raise HTTPException(404, "El nodo no pertenece al snapshot")
        if nodo_id in s.filas:
            verificar_fila(s, nodo_id)
        n = s.nodos[nodo_id]
        return s.identidad | {
            "nodo": n.model_dump(mode="json"),
            "relaciones": [a.model_dump(mode="json") for a in s.producto.aristas if nodo_id in (a.origen, a.destino)],
            "fila": s.detalle(nodo_id) if nodo_id in s.filas else None,
        }

    @router.get("/revision")
    def revision(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        estado: Literal["respaldado_automaticamente", "no_respaldado", "abstencion"] | None = None,
    ):
        return consultar().revision(grado, disciplina, q, estado)

    @router.post("/briefs")
    def briefs(solicitud: SolicitudBrief):
        s = consultar()
        if len(solicitud.filas_ids) != len(set(solicitud.filas_ids)):
            raise HTTPException(422, "No se admiten filas duplicadas")
        if any(id_ not in s.filas for id_ in solicitud.filas_ids):
            raise HTTPException(404, "Hay una fila ajena al snapshot")
        for id_ in solicitud.filas_ids:
            verificar_fila(s, id_)
        try:
            return s.identidad | {
                "briefs": [s.brief(id_, solicitud.formato) for id_ in solicitud.filas_ids],
                "llamadas_modelos": 0,
            }
        except ValueError as error:
            raise HTTPException(422, str(error)) from error

    @router.get("/exportaciones/matriz.xlsx")
    def excel():
        from goes_science_kg.producto.exportacion_mejoras import exportar_excel

        s = consultar()
        with tempfile.TemporaryDirectory(prefix="ciencias-matriz-api-") as temporal:
            archivo = Path(temporal) / "ciencias-v4.xlsx"
            exportar_excel(s.producto.curriculo, s.producto.mejoras, archivo)
            contenido = archivo.read_bytes()
        return Response(
            contenido,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": 'attachment; filename="ciencias-v4.xlsx"',
                "X-Snapshot-ID": s.producto.manifest.snapshot_id,
            },
        )

    @router.get("/administracion")
    def administracion():
        s = consultar()
        ledger = base / "data/operaciones/registro.sqlite"
        actividad = None
        if ledger.is_file() and not ledger.is_symlink():
            try:
                with closing(sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                    filas = db.execute(
                        "SELECT modelo,rol,estado,COUNT(*),SUM(reserva_usd) FROM llamadas "
                        "WHERE ejecucion=? GROUP BY modelo,rol,estado ORDER BY modelo,rol,estado",
                        ("ciencias_v4_curricularizacion_20261022",),
                    ).fetchall()
                actividad = {
                    "llamadas": sum(f[3] for f in filas),
                    "reserva_usd": sum(f[4] for f in filas),
                    "detalle": [{"modelo": f[0], "rol": f[1], "estado": f[2], "llamadas": f[3]} for f in filas],
                    "importe_facturado": None,
                }
            except sqlite3.Error:
                LOGGER.warning("AMARILLO: ledger no disponible para la vista operativa")
        return s.identidad | {
            "modo": "lectura_local",
            "usuarios": None,
            "proveedor_identidad": None,
            "actividad_vertex": actividad,
            "archivos_snapshot": s.producto.manifest.sha256,
            "permisos": {
                "lectura": True,
                "generacion_modelos": False,
                "aprobacion_institucional": False,
                "gestion_usuarios": False,
            },
            "roles_revision": ROLES_MEJORA_API,
            "limite": "La aplicación no autentica usuarios ni sustituye una aprobación institucional.",
        }

    return router


ROLES_MEJORA_API = ["Ciencia", "Currículo", "Psicopedagogía", "Adversarial"]
