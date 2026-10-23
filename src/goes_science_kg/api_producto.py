"""Expose the pinned V4 curriculum and its source evidence through HTTP."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field

from goes_science_kg.motor.contratos import Asignatura, Contrato
from goes_science_kg.producto.lectura import LecturaProducto
from goes_science_kg.producto.unidades import ContextoAula, preparar_unidad


class PreparacionUnidadAPI(Contrato):
    """Validate a unit preparation request and its declared classroom context."""

    grado: int = Field(ge=2, le=11)
    asignatura_malla: str = Field(min_length=1, max_length=100)
    unidad: str = Field(min_length=1, max_length=300)
    contexto: ContextoAula = Field(default_factory=ContextoAula)


def crear_router(base: Path, *, destino: Path | None = None, lector: LecturaProducto | None = None) -> APIRouter:
    """Bind publication roots in the host application rather than accepting request paths."""
    base = base.resolve()
    lectura = lector or LecturaProducto(base, destino)
    router = APIRouter(prefix="/api/v4", tags=["Producto Ciencias V4"])

    def identidad(runtime):
        """Return the curriculum and snapshot identities shared by this response."""
        return {"version_curriculo": "V4", "snapshot_id": runtime.producto.manifest.snapshot_id}

    def fila(runtime, fila_id):
        """Find an exact row within the pinned publication or report a missing identity."""
        encontrada = next((f for f in runtime.producto.curriculo.filas if f.id == fila_id), None)
        if encontrada is None:
            raise HTTPException(404, "La fila no pertenece a esta publicación V4")
        return encontrada

    @router.get("/salud")
    def salud():
        """Report the verified V4 publication and its complete row count."""
        r = lectura.leer()
        return identidad(r) | {
            "estado": "ok",
            "alcance": "snapshot_publicado",
            "filas": len(r.producto.curriculo.filas),
            "conocimiento": r.producto.diagnostico["conocimiento"],
        }

    @router.get("/diagnostico")
    def diagnostico():
        """Return the diagnostic recorded in the selected immutable generation."""
        r = lectura.leer()
        return identidad(r) | {"diagnostico": r.producto.diagnostico}

    @router.get("/filas")
    def filas(
        grado: int | None = Query(None, ge=2, le=11),
        disciplina: Asignatura | None = None,
        offset: int = Query(0, ge=0, le=100000),
        limite: int = Query(50, ge=1, le=200),
    ):
        """List original curriculum rows with exact subject and grade filters."""
        r = lectura.leer()
        decisiones = {d.fila_id: d for d in r.producto.catalogo.filas}
        seleccion = [
            f
            for f in r.producto.curriculo.filas
            if (grado is None or f.grado == grado)
            and (disciplina is None or disciplina in decisiones[f.id].disciplinas)
        ]
        return identidad(r) | {
            "total": len(seleccion),
            "offset": offset,
            "limite": limite,
            "filas": [
                {
                    "id": f.id,
                    "grado": f.grado,
                    "asignatura_malla": f.asignatura_malla,
                    "unidad": f.unidad,
                    "objetivo": f.procedimental,
                    "clasificacion": decisiones[f.id].model_dump(mode="json"),
                }
                for f in seleccion[offset : offset + limite]
            ],
        }

    @router.get("/filas/{fila_id}")
    def detalle_fila(fila_id: str):
        """Rehydrate one original row and expose its evidence and recorded knowledge reviews."""
        from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila

        r = lectura.leer()
        f = fila(r, fila_id)
        pruebas = r.fuentes.hidratar_celdas(documento_de_fila(f))
        if not pruebas:
            raise HTTPException(503, "No se pudo verificar la fuente original de la fila")
        decision = next(d for d in r.producto.catalogo.filas if d.fila_id == f.id)
        juicios = r.producto.conocimiento.coleccion.resultados if r.producto.conocimiento else ()
        return identidad(r) | {
            "fila": f.model_dump(mode="json"),
            "clasificacion": decision.model_dump(mode="json"),
            "evidencias": [e.model_dump(mode="json") for e in pruebas],
            "alerta_cientifica": r.fuentes.bloqueos_efectivos.get(f.id),
            "juicios_conocimiento": [
                j.model_dump(mode="json")
                for j in juicios
                if r.producto.conocimiento.expediente(j.solicitud.candidato_id).fila_id == f.id
            ],
        }

    @router.get("/contexto")
    def contexto(
        fila_id: Annotated[str, Query(min_length=1, max_length=200)],
        grado: Annotated[int, Query(ge=2, le=11)],
        disciplina: Annotated[Asignatura, Query()],
    ):
        """Retrieve verified evidence for an exact row under matching grade and subject filters."""
        from goes_science_kg.motor.contexto import construir_contexto

        r = lectura.leer()
        fila(r, fila_id)
        try:
            resultados = r.buscador.buscar_fila(fila_id, version="V4", grado=grado, asignatura=disciplina)
            evidencias = construir_contexto(resultados, version="V4", fuentes=r.fuentes)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        if not evidencias:
            raise HTTPException(503, "No se pudo verificar evidencia para la fila solicitada")
        return identidad(r) | {"fila_id": fila_id, "evidencias": [e.model_dump(mode="json") for e in evidencias]}

    @router.get("/juicios/{candidato_id}")
    def juicio(candidato_id: str):
        """Audit one published knowledge review against its original physical sources."""
        from goes_science_kg.producto.consulta_conocimiento import fuentes_del_archivo, rehidratar_evidencias

        r = lectura.leer()
        archivo = r.producto.conocimiento
        if archivo is None or candidato_id not in archivo.expedientes:
            raise HTTPException(404, "El candidato no tiene un juicio en esta publicación")
        expediente = archivo.expediente(candidato_id)
        fuentes = fuentes_del_archivo(
            archivo,
            r.producto.curriculo,
            raiz_v4=base / "insumos/v4",
            raiz_historica=base / "data/fuentes",
            raiz_referencias=base / "data/referencias_2026",
            raiz_paises=base / "data/referencias_paises_2026",
            raiz_cientificas=base / "data/referencias_cientificas_2026",
        )
        try:
            rehidratar_evidencias(archivo, fuentes, [e.id for e in expediente.evidencias])
        except (ValueError, KeyError, OSError) as error:
            raise HTTPException(503, "No se pudieron verificar las fuentes originales del juicio") from error
        resultado = next(j for j in archivo.coleccion.resultados if j.solicitud.candidato_id == candidato_id)
        return identidad(r) | {
            "resultado": resultado.model_dump(mode="json"),
            "expediente": expediente.model_dump(mode="json"),
        }

    @router.get("/alineaciones")
    def alineaciones(fila_id: str | None = Query(None, max_length=200)):
        """List the complete documentary alignment cohort, including negative outcomes."""
        from goes_science_kg.motor.contratos import huella

        r = lectura.leer()
        if fila_id is not None:
            fila(r, fila_id)
        archivo = r.producto.alineaciones
        casos = [c for c in archivo.casos if fila_id is None or c.solicitud.fila_id == fila_id] if archivo else []
        return identidad(r) | {
            "archivo_id": archivo.id if archivo else None,
            "casos": [
                {
                    "id": huella(c.solicitud),
                    "fila_id": c.solicitud.fila_id,
                    "referente_id": c.solicitud.referente_id,
                    "estado": c.resultado.estado,
                    "alerta_cientifica_actual": r.fuentes.bloqueos_efectivos.get(c.solicitud.fila_id),
                    "habilitada_para_generacion": c.solicitud.fila_id not in r.fuentes.bloqueos_efectivos,
                }
                for c in casos
            ],
            "limite": archivo.limite if archivo else "No hay alineaciones documentales publicadas",
        }

    @router.get("/alineaciones/{caso_id}")
    def auditar_alineacion(caso_id: str):
        """Rehydrate one documentary alignment case without repeating its votes."""
        from goes_science_kg.motor.contratos import huella
        from goes_science_kg.recuperacion import Documento

        r = lectura.leer()
        archivo = r.producto.alineaciones
        caso = next((c for c in archivo.casos if huella(c.solicitud) == caso_id), None) if archivo else None
        if caso is None:
            raise HTTPException(404, "No hay un caso documental con esa identidad")
        for e in caso.preparacion.evidencias:
            if (
                r.fuentes.hidratar(Documento(id=e.id, texto="Releer fuente física", fuente=e.fuente, version=e.version))
                != e
            ):
                raise HTTPException(503, "No se pudo verificar la fuente primaria de la alineación")
        return identidad(r) | {
            "archivo_id": archivo.id,
            "caso": caso.model_dump(mode="json"),
            "limite": archivo.limite,
            "alerta_cientifica_actual": r.fuentes.bloqueos_efectivos.get(caso.solicitud.fila_id),
            "habilitada_para_generacion": caso.solicitud.fila_id not in r.fuentes.bloqueos_efectivos,
        }

    @router.post("/unidades/preparar")
    def preparar(solicitud: PreparacionUnidadAPI):
        """Prepare a complete teaching unit locally without invoking models."""
        r = lectura.leer()
        try:
            paquete = preparar_unidad(
                r.producto.curriculo,
                r.producto.catalogo,
                grado=solicitud.grado,
                asignatura_malla=solicitud.asignatura_malla,
                unidad=solicitud.unidad,
                contexto=solicitud.contexto,
                fuentes=r.fuentes,
            )
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        return identidad(r) | {"paquete": paquete.model_dump(mode="json"), "llamadas_modelos": 0}

    from goes_science_kg.api_mejoras import crear_router_mejoras

    router.include_router(crear_router_mejoras(lectura.leer))
    from goes_science_kg.api_interfaz import crear_router_interfaz

    router.include_router(crear_router_interfaz(lectura.leer, base))
    return router
