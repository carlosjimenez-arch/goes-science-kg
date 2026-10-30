"""Expose repository-backed curriculum queries and documentary briefs without model calls."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from goes_science_kg.interfaz.consulta import normalizar
from goes_science_kg.interfaz.contratos import ListaDocumentos, PaginaFilas, RespuestaBriefs, RespuestaGrafo
from goes_science_kg.interfaz.progresion import VISTAS, ProgresionCurricular
from goes_science_kg.interfaz.servicio import FuenteNoDisponible, RegistroActividad, ServicioInterfaz
from goes_science_kg.motor.contratos import Asignatura
from goes_science_kg.producto.runtime import RuntimeProducto

DIRECTORIO = Path(__file__).parent / "interfaz" / "estaticos"
Grado = Annotated[int | None, Query(ge=2, le=11)]
Texto = Annotated[str, Query(max_length=200)]
Vista = Literal[VISTAS]


class SolicitudBrief(BaseModel):
    """Select verified curriculum rows and a supported brief layout."""

    model_config = ConfigDict(extra="forbid")
    filas_ids: list[Annotated[str, Field(min_length=1, max_length=200)]] = Field(min_length=1, max_length=20)
    formato: Literal["evaluacion", "cinco_fases"] = "evaluacion"


def registrar_interfaz(app: FastAPI) -> None:
    """Mount local application assets whose data comes exclusively from the API."""

    @app.get("/", include_in_schema=False)
    def inicio():
        """Redirect the entry page to the local curriculum application."""
        return RedirectResponse("/app/", status_code=307)

    app.mount("/app", StaticFiles(directory=DIRECTORIO, html=True), name="interfaz")

    @app.middleware("http")
    async def cabeceras(peticion: Request, siguiente: Callable) -> Response:
        """Apply local application security and no-store response headers."""
        respuesta = await siguiente(peticion)
        if peticion.url.path.startswith(("/app", "/api/v4/interfaz", "/api/v4/materiales")):
            respuesta.headers["X-Content-Type-Options"] = "nosniff"
            respuesta.headers["Referrer-Policy"] = "no-referrer"
            respuesta.headers["Cache-Control"] = "private, no-store"
            respuesta.headers["Content-Security-Policy"] = (
                "default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; font-src 'self'; connect-src 'self'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
            )
        return respuesta


def crear_router_interfaz(leer: Callable[[], RuntimeProducto], base: Path) -> APIRouter:
    """Bind HTTP routes to a shared, verified curriculum application service."""
    router = APIRouter(prefix="/interfaz", tags=["Aplicación curricular"])
    servicio = ServicioInterfaz(leer)
    registro = RegistroActividad(base / "data/operaciones/registro.sqlite")
    progresion_v4 = ProgresionCurricular(base / "data/producto/progresion_v4/progresion.json")

    def consultar():
        """Translate application compatibility errors into the public HTTP contract."""
        try:
            return servicio.consultar()
        except ValueError as error:
            raise HTTPException(409, str(error)) from error

    def verificar_fila(consulta, fila_id: str) -> None:
        """Require verifiable original cells before exposing row details or briefs."""
        try:
            servicio.verificar_fila(consulta, fila_id)
        except FuenteNoDisponible as error:
            raise HTTPException(503, str(error)) from error

    @router.get("/resumen")
    def resumen():
        """Return verified snapshot counts and explicit integration availability."""
        return consultar().resumen()

    @router.get("/filas", response_model=PaginaFilas)
    def filas(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        offset: Annotated[int, Query(ge=0, le=100000)] = 0,
        limite: Annotated[int, Query(ge=1, le=200)] = 40,
        solo_alertas: bool = False,
    ):
        """Return a bounded, filtered page while preserving its complete row denominator."""
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
        """Return one verified original row, its proposal, reviews, and cited evidence."""
        s = consultar()
        if fila_id not in s.filas:
            raise HTTPException(404, "La fila no pertenece al snapshot")
        verificar_fila(s, fila_id)
        return s.detalle(fila_id)

    @router.get("/documentos", response_model=ListaDocumentos)
    def documentos(q: Texto = "", tipo: Literal["curriculo", "referencia"] | None = None):
        """List registered and cited documents using validated source metadata."""
        s = consultar()
        seleccion = [
            d
            for d in s.documentos.values()
            if (not q or normalizar(q) in normalizar(d["titulo"] + " " + d["id"]))
            and (tipo is None or d["tipo"] == tipo)
        ]
        return s.identidad | {"total": len(seleccion), "documentos": sorted(seleccion, key=lambda d: d["titulo"])}

    @router.get("/grafo", response_model=RespuestaGrafo)
    def grafo(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        limite: Annotated[int, Query(ge=10, le=800)] = 260,
    ):
        """Return a bounded real subgraph with typed edges and explicit truncation."""
        return consultar().grafo(grado=grado, disciplina=disciplina, q=q, limite=limite)

    @router.get("/nodos/{nodo_id:path}")
    def nodo(nodo_id: str):
        """Look up an exact node identity and its indexed relationships, including IDs with slashes."""
        s = consultar()
        if nodo_id not in s.nodos:
            raise HTTPException(404, "El nodo no pertenece al snapshot")
        if nodo_id in s.filas:
            verificar_fila(s, nodo_id)
        n = s.nodos[nodo_id]
        return s.identidad | {
            "nodo": n.model_dump(mode="json"),
            "relaciones": [a.model_dump(mode="json") for a in s.aristas_por_nodo[nodo_id]],
            "fila": s.detalle(nodo_id) if nodo_id in s.filas else None,
        }

    @router.get("/revision")
    def revision(
        grado: Grado = None,
        disciplina: Asignatura | None = None,
        q: Texto = "",
        estado: Literal["respaldado_automaticamente", "no_respaldado", "abstencion"] | None = None,
    ):
        """List published unit reviews under the same curriculum filters."""
        return consultar().revision(grado, disciplina, q, estado)

    def progresion_disponible(llamada: Callable):
        """Translate a missing or foreign progression artifact into the explicit no-data contract."""
        try:
            return llamada()
        except FuenteNoDisponible as error:
            raise HTTPException(503, str(error)) from error

    @router.get("/progresion")
    def progresion(vista: Vista = "original"):
        """Return how concepts and practices are introduced and reinforced from grade 2 to 11."""
        s = consultar()
        return s.identidad | progresion_disponible(
            lambda: progresion_v4.resumen(s.producto.manifest.snapshot_id, vista)
        )

    @router.get("/progresion/conceptos")
    def progresion_conceptos(
        vista: Vista = "original",
        disciplina: Asignatura | None = None,
        patron: Literal["aislado", "concentrado", "espiral", "intermitente"] | None = None,
        q: Texto = "",
    ):
        """List concept trajectories with their grades, pattern, and largest gap."""
        s = consultar()
        conceptos = progresion_disponible(
            lambda: progresion_v4.conceptos(
                s.producto.manifest.snapshot_id, vista, disciplina=disciplina, patron=patron, q=q
            )
        )
        return s.identidad | {"vista": vista, "total": len(conceptos), "conceptos": conceptos}

    @router.get("/progresion/conceptos/{concepto_id:path}")
    def progresion_concepto(concepto_id: str, vista: Vista = "original"):
        """Return one concept trajectory with the curriculum rows behind each grade."""
        s = consultar()
        try:
            detalle = progresion_disponible(
                lambda: progresion_v4.concepto(
                    s.producto.manifest.snapshot_id,
                    vista,
                    concepto_id,
                    s.filas,
                    (lambda f: s.ficha(s.filas[f]).get("objetivo_propuesto")) if vista == "propuesta" else None,
                )
            )
        except KeyError as error:
            raise HTTPException(404, "El concepto no aparece en la progresión de esta publicación") from error
        return s.identidad | {"vista": vista, "concepto": detalle}

    @router.post("/briefs", response_model=RespuestaBriefs)
    def briefs(solicitud: SolicitudBrief):
        """Compile existing proposals into documentary briefs without invoking models."""
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
        """Export the full curricular comparison with its pinned snapshot identity."""
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
        """Report publication identity, local capabilities, and optional recorded campaign usage."""
        s = consultar()
        actividad = registro.consultar("ciencias_v4_curricularizacion_20261022")
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
