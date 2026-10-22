"""API V4 sobre una publicación fijada, sin generación ni adopción implícita de otra versión."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from threading import Lock
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import Field

from goes_science_kg.motor.contratos import Asignatura, Contrato
from goes_science_kg.producto.almacen import archivos_producto
from goes_science_kg.producto.runtime import RuntimeProducto, cargar_runtime
from goes_science_kg.producto.unidades import ContextoAula, preparar_unidad

LOGGER = logging.getLogger(__name__)


class PreparacionUnidadAPI(Contrato):
    grado: int = Field(ge=2, le=11)
    asignatura_malla: str = Field(min_length=1, max_length=100)
    unidad: str = Field(min_length=1, max_length=300)
    contexto: ContextoAula = Field(default_factory=ContextoAula)


def _observar(destino: Path) -> dict:
    """Firma de archivos; las huellas de bytes se validan al cargar, fuera del camino frecuente."""
    puntero = destino / "actual.json"
    if puntero.stat().st_size > 4096:
        raise ValueError("Puntero de publicación incompatible")
    seleccion = json.loads(puntero.read_bytes())
    identidad = seleccion.get("snapshot_id", "")
    if not re.fullmatch(r"[a-f0-9]{64}", identidad):
        raise ValueError("Identidad de snapshot incompatible")
    generacion = destino / "snapshots" / identidad
    archivos = [
        puntero,
        generacion / "manifest.json",
        *(generacion / n for n in sorted(archivos_producto(seleccion.get("version")))),
    ]
    firmas = {}
    for archivo in archivos:
        actual = archivo
        while actual != destino.parent:
            if actual.is_symlink():
                raise ValueError("La publicación no admite enlaces")
            actual = actual.parent
        s = archivo.stat()
        firmas[str(archivo)] = (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
    return firmas


class _LecturaProducto:
    def __init__(self, base: Path, destino: Path):
        self.base, self.destino = base, destino
        self._runtime: RuntimeProducto | None = None
        self._firmas = None
        self._error = False
        self._lock = Lock()

    def leer(self) -> RuntimeProducto:
        with self._lock:
            try:
                if self._error:
                    raise ValueError("La instancia quedó invalidada")
                firmas = _observar(self.destino)
                if self._runtime is None:
                    runtime = cargar_runtime(
                        self.destino,
                        raiz_v4=self.base / "insumos/v4",
                        raiz_historica=self.base / "data/fuentes",
                        raiz_referencias=self.base / "data/referencias_2026",
                        raiz_paises=self.base / "data/referencias_paises_2026",
                        raiz_cientificas=self.base / "data/referencias_cientificas_2026",
                        archivo_alertas=self.base / "docs/investigacion/alertas_v4.json",
                        raiz_progresiones=self.base / "data/referencias_progresiones_2026",
                    )
                    if firmas != _observar(self.destino):
                        raise ValueError("La publicación cambió durante la carga")
                    self._runtime, self._firmas = runtime, firmas
                elif firmas != self._firmas:
                    raise ValueError("La publicación cambió después de cargarse")
                return self._runtime
            except (ValueError, KeyError, OSError) as error:
                self._error = True
                LOGGER.error("ROJO API V4 sin publicación verificable: %s", type(error).__name__)
                raise HTTPException(
                    503,
                    {
                        "codigo": "producto_v4_no_disponible",
                        "motivo": "Falta una publicación V4 íntegra o cambió; verifícala y reinicia el servicio",
                    },
                ) from error


def crear_router(base: Path, *, destino: Path | None = None) -> APIRouter:
    """El anfitrión fija las rutas; las peticiones no reciben archivos ni destinos de publicación."""
    base = base.resolve()
    lectura = _LecturaProducto(base, destino or base / "data/producto/V4")
    router = APIRouter(prefix="/api/v4", tags=["Producto Ciencias V4"])

    def identidad(runtime):
        return {"version_curriculo": "V4", "snapshot_id": runtime.producto.manifest.snapshot_id}

    def fila(runtime, fila_id):
        encontrada = next((f for f in runtime.producto.curriculo.filas if f.id == fila_id), None)
        if encontrada is None:
            raise HTTPException(404, "La fila no pertenece a esta publicación V4")
        return encontrada

    @router.get("/salud")
    def salud():
        r = lectura.leer()
        return identidad(r) | {
            "estado": "ok",
            "alcance": "snapshot_publicado",
            "filas": len(r.producto.curriculo.filas),
            "conocimiento": r.producto.diagnostico["conocimiento"],
        }

    @router.get("/diagnostico")
    def diagnostico():
        r = lectura.leer()
        return identidad(r) | {"diagnostico": r.producto.diagnostico}

    @router.get("/filas")
    def filas(
        grado: int | None = Query(None, ge=2, le=11),
        disciplina: Asignatura | None = None,
        offset: int = Query(0, ge=0, le=100000),
        limite: int = Query(50, ge=1, le=200),
    ):
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
            "alerta_cientifica": r.fuentes.bloqueos_curriculares.get(f.id),
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
                }
                for c in casos
            ],
            "limite": archivo.limite if archivo else "No hay alineaciones documentales publicadas",
        }

    @router.get("/alineaciones/{caso_id}")
    def auditar_alineacion(caso_id: str):
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
        return identidad(r) | {"archivo_id": archivo.id, "caso": caso.model_dump(mode="json"), "limite": archivo.limite}

    @router.post("/unidades/preparar")
    def preparar(solicitud: PreparacionUnidadAPI):
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
    return router
