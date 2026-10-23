"""Coordinate a bounded LangGraph workflow with review, repair, and abstention."""

from __future__ import annotations

import logging
from typing import TypedDict

from goes_science_kg.motor.calidad import validar_dictamenes, validar_propuesta
from goes_science_kg.motor.contexto import construir_contexto, grupos_obligatorios
from goes_science_kg.motor.contratos import (
    ESQUEMAS_REVISION,
    Dictamen,
    Evidencia,
    Propuesta,
    ResultadoMotor,
    Revision,
    Solicitud,
    huella,
)
from goes_science_kg.motor.fragmentos import (
    Borrador,
    Fragmento,
    datos_fragmentos,
    preparar_fragmentos,
    resolver_borrador,
)
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.motor.prompts import REDACTOR, juez, serializar
from goes_science_kg.motor.puertos import ModeloEstructurado, Recuperador
from goes_science_kg.recuperacion import Documento

LOGGER = logging.getLogger(__name__)


class Estado(TypedDict, total=False):
    """Persist curriculum-engine context, proposals, reviews, repairs, and final outcome."""

    solicitud: dict
    ejecucion_id: str
    evidencias: list[dict]
    propuesta: dict | None
    cientifico: dict | None
    psicopedagogo: dict | None
    adversarial: dict | None
    errores: list[str]
    reparaciones: int
    resultado: dict
    huella_entorno: str
    fragmentos: list[dict]


class Motor:
    """Coordinate bounded generation and independent review over verified curriculum evidence."""

    def __init__(
        self,
        buscador: Recuperador,
        modelo: ModeloEstructurado,
        *,
        max_caracteres: int = 18000,
        max_reparaciones: int = 1,
        fuentes: FuentesVerificadas | None = None,
    ):
        if not 0 <= max_reparaciones <= 2:
            raise ValueError("Se admiten de cero a dos reparaciones")
        self.buscador = buscador
        self.modelo = modelo
        self.max_caracteres = max_caracteres
        self.max_reparaciones = max_reparaciones
        self.fuentes = fuentes

    def _contexto(self, estado: Estado) -> dict:
        s = Solicitud.model_validate(estado["solicitud"])
        if self.fuentes is None:
            return {
                "evidencias": [],
                "fragmentos": [],
                "reparaciones": 0,
                "errores": ["Falta el repositorio de fuentes verificadas"],
            }
        try:
            if s.fila_id is not None:
                if not hasattr(self.buscador, "buscar_fila"):
                    raise ValueError("El recuperador no admite evidencia por fila explícita")
                resultados = self.buscador.buscar_fila(
                    s.fila_id,
                    version=s.version_curriculo,
                    grado=s.grado,
                    asignatura=s.asignatura,
                    k=16,
                )
            else:
                resultados = self.buscador.buscar(
                    s.consulta,
                    version=s.version_curriculo,
                    grado=s.grado,
                    asignatura=s.asignatura,
                    k=16,
                    saltos_grafo=2,
                )
        except ValueError as error:
            LOGGER.warning("AMARILLO contexto no disponible: %s", error)
            return {"evidencias": [], "reparaciones": 0, "errores": [str(error)]}
        evidencias = construir_contexto(
            resultados, version=s.version_curriculo, max_caracteres=self.max_caracteres, fuentes=self.fuentes
        )
        if bloqueos := self.fuentes.motivos_bloqueo(evidencias):
            return {"evidencias": [], "fragmentos": [], "reparaciones": 0, "errores": bloqueos}
        LOGGER.info("Contexto %s: %d fragmentos de evidencia", s.version_curriculo, len(evidencias))
        # Una referencia internacional sola no sustituye el currículo local vigente.
        vigente = any(e.version == s.version_curriculo for e in evidencias)
        fragmentos = []
        if vigente:
            try:
                fragmentos = preparar_fragmentos(
                    evidencias,
                    s.consulta,
                    max_caracteres=self.max_caracteres,
                    lectura_completa=True,
                    grupos_obligatorios=grupos_obligatorios(resultados, evidencias),
                )
            except ValueError as error:
                return {
                    "evidencias": [e.model_dump() for e in evidencias],
                    "fragmentos": [],
                    "reparaciones": 0,
                    "errores": [str(error)],
                }
        return {
            "evidencias": [e.model_dump() for e in evidencias],
            "fragmentos": [f.model_dump() for f in fragmentos],
            "reparaciones": 0,
            "errores": [] if vigente else [f"No hay evidencia curricular {s.version_curriculo} para la solicitud"],
        }

    def _datos(self, estado: Estado) -> dict:
        datos = datos_fragmentos(
            [Fragmento.model_validate(f) for f in estado.get("fragmentos", [])],
            [Evidencia.model_validate(e) for e in estado.get("evidencias", [])],
            lectura_completa=True,
        )
        return {"solicitud": estado["solicitud"], **datos}

    def _redactar(self, estado: Estado) -> dict:
        datos = self._datos(estado)
        if estado.get("propuesta"):
            datos.update({"propuesta_anterior": estado["propuesta"], "errores_a_corregir": estado["errores"]})
        elif estado.get("errores"):
            datos["errores_a_corregir"] = estado["errores"]
        try:
            borrador = self.modelo.generar(
                rol="redactor", sistema=REDACTOR, mensaje=serializar(datos), esquema=Borrador
            )
            propuesta = resolver_borrador(borrador, [Fragmento.model_validate(f) for f in estado["fragmentos"]])
            return {"propuesta": propuesta.model_dump(), "errores": []}
        except Exception as error:
            # Cualquier fallo de proveedor o contrato produce abstención, nunca aprobación parcial.
            LOGGER.error("ROJO redacción fallida: %s", type(error).__name__)
            return {"propuesta": None, "errores": [f"Redacción no disponible: {type(error).__name__}"]}

    def _revisar(self, estado: Estado, rol: str) -> dict:
        if not estado.get("propuesta"):
            return {rol: None}
        propuesta = Propuesta.model_validate(estado["propuesta"])
        datos = self._datos(estado) | {"propuesta": propuesta.model_dump()}
        try:
            revision = self.modelo.generar(
                rol=rol, sistema=juez(rol), mensaje=serializar(datos), esquema=ESQUEMAS_REVISION[rol]
            )
            d = Dictamen(
                rol=rol,
                modelo=self.modelo.nombre_modelo(rol),
                huella_propuesta=huella(propuesta),
                revision=Revision.model_validate(revision.model_dump()),
            )
            return {rol: d.model_dump()}
        except Exception as error:
            LOGGER.error("ROJO revisión %s fallida: %s", rol, type(error).__name__)
            return {rol: None}

    def _evaluar(self, estado: Estado) -> dict:
        if not estado.get("propuesta"):
            return {"errores": estado.get("errores") or ["No se generó una propuesta"]}
        propuesta = Propuesta.model_validate(estado["propuesta"])
        evidencias = [Evidencia.model_validate(e) for e in estado["evidencias"]]
        dictamenes = [
            Dictamen.model_validate(estado[r]) for r in ("cientifico", "psicopedagogo", "adversarial") if estado.get(r)
        ]
        errores = validar_propuesta(propuesta, Solicitud.model_validate(estado["solicitud"]), evidencias)
        errores += validar_dictamenes(propuesta, dictamenes, evidencias)
        if errores:
            LOGGER.warning("AMARILLO %d observaciones; reparación %d", len(errores), estado["reparaciones"])
        else:
            LOGGER.info("VERDE propuesta respaldada automáticamente")
        return {"errores": errores}

    def _anclar(self, estado: Estado) -> dict:
        """Reject invalid citations or conditions before spending on three reviews."""
        if not estado.get("propuesta"):
            return {"errores": estado.get("errores") or ["No se generó una propuesta"]}
        errores = validar_propuesta(
            Propuesta.model_validate(estado["propuesta"]),
            Solicitud.model_validate(estado["solicitud"]),
            [Evidencia.model_validate(e) for e in estado["evidencias"]],
        )
        if errores:
            LOGGER.warning("AMARILLO se omiten jueces: %d fallos de anclaje", len(errores))
        return {"errores": errores}

    def _reparar(self, estado: Estado) -> dict:
        return self._redactar(estado) | {"reparaciones": estado["reparaciones"] + 1}

    def _validar_evidencias(self, estado: Estado, solicitud: Solicitud) -> list[Evidencia]:
        evidencias = [Evidencia.model_validate(e) for e in estado.get("evidencias", [])]
        if len({e.id for e in evidencias}) != len(evidencias):
            raise ValueError("El estado conserva identificadores de evidencia duplicados")
        if evidencias and self.fuentes is None:
            raise ValueError("Las evidencias persistidas requieren el repositorio de fuentes verificadas")
        for evidencia in evidencias:
            if evidencia.version not in {solicitud.version_curriculo, "referencia"}:
                raise ValueError("La evidencia persistida pertenece a otra versión curricular")
            actual = self.fuentes.hidratar(
                Documento(
                    id=evidencia.id,
                    texto="El texto se obtiene del localizador físico, nunca de este registro",
                    fuente=evidencia.fuente,
                    version=evidencia.version,
                )
            )
            if actual is None or huella(actual) != huella(evidencia):
                raise ValueError(f"La evidencia {evidencia.id} cambió al rehidratar las fuentes")
        if self.fuentes is not None and (bloqueos := self.fuentes.motivos_bloqueo(evidencias)):
            raise ValueError("Las fuentes tienen bloqueos actuales: " + " | ".join(bloqueos))
        por_id = {e.id: e for e in evidencias}
        fragmentos = [Fragmento.model_validate(f) for f in estado.get("fragmentos", [])]
        if len({f.id for f in fragmentos}) != len(fragmentos):
            raise ValueError("El registro persistido contiene fragmentos duplicados")
        for fragmento in fragmentos:
            evidencia = por_id.get(fragmento.evidencia_id)
            if evidencia is None or fragmento.literal not in " ".join(evidencia.texto.split()):
                raise ValueError("Un fragmento persistido no pertenece a sus fuentes verificadas")
        return evidencias

    def _dictamenes_estado(self, estado: Estado) -> list[Dictamen]:
        dictamenes = []
        for rol in ("cientifico", "psicopedagogo", "adversarial"):
            if not estado.get(rol):
                continue
            dictamen = Dictamen.model_validate(estado[rol])
            if dictamen.rol != rol or dictamen.modelo != self.modelo.nombre_modelo(rol):
                raise ValueError("El dictamen persistido pertenece a otro rol o modelo")
            dictamenes.append(dictamen)
        return dictamenes

    def _resultado_cierre(self, estado: Estado) -> ResultadoMotor:
        """Reconstruct closure errors without retrieving sources or generating content."""

        # Implementation notes:
        # Un anclaje inválido omite jueces. En esa abstención, o tras fallar la redacción reparada,
        # pueden quedar dictámenes de una ronda anterior: se conservan como en el workflow original.
        solicitud = Solicitud.model_validate(estado["solicitud"])
        evidencias = [Evidencia.model_validate(e) for e in estado.get("evidencias", [])]
        propuesta = Propuesta.model_validate(estado["propuesta"]) if estado.get("propuesta") else None
        dictamenes = self._dictamenes_estado(estado)
        errores = list(estado.get("errores", []))
        if propuesta is not None:
            errores = validar_propuesta(propuesta, solicitud, evidencias)
            if not errores:
                errores += validar_dictamenes(propuesta, dictamenes, evidencias)
        aprobada = propuesta is not None and not errores
        return ResultadoMotor(
            estado="respaldado_automaticamente" if aprobada else "abstencion",
            ejecucion_id=estado["ejecucion_id"],
            version_curriculo=solicitud.version_curriculo,
            propuesta=propuesta if aprobada else None,
            dictamenes=dictamenes,
            motivos=errores,
            evidencias=evidencias,
            iteraciones=estado.get("reparaciones", 0) + int(bool(propuesta)),
        )

    def validar_estado(self, estado: Estado) -> None:
        """Validate partial and terminal state locally without retrieval or model calls."""
        solicitud = Solicitud.model_validate(estado["solicitud"])
        self._validar_evidencias(estado, solicitud)
        # Tras reparar puede persistir una revisión de la propuesta anterior hasta el siguiente fanout.
        self._dictamenes_estado(estado)
        if "resultado" in estado:
            guardado = ResultadoMotor.model_validate(estado["resultado"])
            if huella(self._resultado_cierre(estado)) != huella(guardado):
                raise ValueError("El resultado terminal no corresponde al estado verificado")

    def _cerrar(self, estado: Estado) -> dict:
        self._validar_evidencias(estado, Solicitud.model_validate(estado["solicitud"]))
        return {"resultado": self._resultado_cierre(estado).model_dump()}

    def compilar(self, *, checkpointer=None):
        """Compile the workflow with an explicitly injected persistent checkpoint backend."""
        from langgraph.graph import END, START, StateGraph

        flujo = StateGraph(Estado)
        flujo.add_node("contexto", self._contexto)
        flujo.add_node("redactar", self._redactar)
        flujo.add_node("anclar", self._anclar)
        for rol in ("cientifico", "psicopedagogo", "adversarial"):
            flujo.add_node(rol, lambda estado, r=rol: self._revisar(estado, r))
        flujo.add_node("evaluar", self._evaluar)
        flujo.add_node("reparar", self._reparar)
        flujo.add_node("cerrar", self._cerrar)
        flujo.add_edge(START, "contexto")
        flujo.add_conditional_edges("contexto", lambda e: "cerrar" if e["errores"] else "redactar")
        flujo.add_edge("redactar", "anclar")
        flujo.add_edge("reparar", "anclar")
        flujo.add_conditional_edges(
            "anclar",
            lambda e: (
                ["cientifico", "psicopedagogo", "adversarial"]
                if not e["errores"]
                else ("reparar" if e["reparaciones"] < self.max_reparaciones else "cerrar")
            ),
        )
        flujo.add_edge(["cientifico", "psicopedagogo", "adversarial"], "evaluar")
        flujo.add_conditional_edges(
            "evaluar", lambda e: "reparar" if e["errores"] and e["reparaciones"] < self.max_reparaciones else "cerrar"
        )
        flujo.add_edge("cerrar", END)
        return flujo.compile(checkpointer=checkpointer)
