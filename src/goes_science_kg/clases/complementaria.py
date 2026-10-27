"""Capa complementaria de implementación: anexos por clase y evaluación por unidad sin alterar el guion liberado.

Cada anexo se ancla al SHA-256 del guion publicado y sólo propone cómo aplicarlo: versión mínima, recursos,
progresión entre grados, inclusión, indagación abierta y contexto nacional con fuentes registradas. No sustituye
las cuatro lecturas ni la revisión directa del guion, y requiere su propia revisión independiente.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from goes_science_kg.clases.contratos import FASES, AfirmacionClase, ComprobacionCalculo, CriterioRubrica, GuionClase
from goes_science_kg.clases.validacion import calcular
from goes_science_kg.motor.contratos import Contrato

VERSION_ANEXO = "anexo-clase-1"
VERSION_EVALUACION = "evaluacion-unidad-1"
LIMITE = (
    "Propuesta complementaria redactada y revisada con asistencia de IA. No modifica el guion liberado, no es "
    "aprobación del MINED ni evidencia de eficacia en aula."
)
NECESIDADES_OBLIGATORIAS = ("discapacidad_visual", "discapacidad_auditiva", "dificultad_lectora", "discapacidad_motora")
Necesidad = Literal[
    "discapacidad_visual",
    "discapacidad_auditiva",
    "dificultad_lectora",
    "discapacidad_motora",
    "atencion_e_hiperactividad",
    "altas_capacidades",
]
NivelIndagacion = Literal["confirmacion", "estructurada", "guiada", "abierta"]


class Material(Contrato):
    material: str = Field(min_length=3, max_length=200)
    sustituto_casero: str | None = Field(default=None, min_length=3, max_length=300)
    imprescindible: bool


class Recursos(Contrato):
    nivel: Literal["sin_materiales", "materiales_caseros", "laboratorio"]
    materiales: tuple[Material, ...] = Field(max_length=15)
    requiere_electricidad: bool
    requiere_agua: bool
    requiere_exterior: bool
    requiere_conectividad: bool
    costo: Literal["nulo", "bajo", "medio"]

    @model_validator(mode="after")
    def _nivel(self):
        if self.nivel == "sin_materiales" and any(m.imprescindible for m in self.materiales):
            raise ValueError("Una clase sin materiales no declara materiales imprescindibles")
        return self


class AjusteBloque(Contrato):
    sesion: int = Field(ge=1, le=3)
    bloque: int = Field(ge=1, le=8)
    accion: Literal["conservar", "acortar", "omitir"]
    minutos: int = Field(ge=0, le=60)
    nota: str | None = Field(default=None, min_length=10, max_length=400)

    @model_validator(mode="after")
    def _coherencia(self):
        if (self.accion == "omitir") != (self.minutos == 0):
            raise ValueError("Sólo un bloque omitido tiene 0 minutos")
        if self.accion != "conservar" and not self.nota:
            raise ValueError("Acortar u omitir un bloque exige explicar qué se pierde y cómo se compensa")
        return self


class VersionMinima(Contrato):
    minutos_efectivos: int = Field(ge=30, le=50, description="Tiempo real de trabajo por sesión de 60 minutos.")
    ajustes: tuple[AjusteBloque, ...] = Field(min_length=2, max_length=24)
    tarea_prioritaria: int = Field(ge=1, le=3)
    evidencia_minima: str = Field(min_length=30, max_length=500)


class EnlaceProgresion(Contrato):
    concepto: str = Field(min_length=5, max_length=120)
    fila_id: str = Field(min_length=1, max_length=200)
    grado: int = Field(ge=2, le=11)
    como_usarlo: str = Field(min_length=30, max_length=500)


class Progresion(Contrato):
    ideas_previas: tuple[EnlaceProgresion, ...] = Field(max_length=4)
    continuidad: tuple[EnlaceProgresion, ...] = Field(max_length=4)
    sin_antecedente: str | None = Field(default=None, min_length=30, max_length=500)

    @model_validator(mode="after")
    def _algo(self):
        if not self.ideas_previas and not self.sin_antecedente:
            raise ValueError("Sin ideas previas registradas, explica cómo diagnosticar lo que el grupo ya sabe")
        return self


class Adecuacion(Contrato):
    necesidad: Necesidad
    ajuste: str = Field(min_length=30, max_length=500)


class Inclusion(Contrato):
    adecuaciones: tuple[Adecuacion, ...] = Field(min_length=4, max_length=6)
    multigrado: str = Field(min_length=40, max_length=600)
    contexto_rural: str = Field(min_length=40, max_length=600)
    hoja_lectura_facil: str = Field(min_length=150, max_length=1800)

    @model_validator(mode="after")
    def _cobertura(self):
        necesidades = [a.necesidad for a in self.adecuaciones]
        if len(set(necesidades)) != len(necesidades) or set(NECESIDADES_OBLIGATORIAS) - set(necesidades):
            raise ValueError("Cada necesidad aparece una vez y las cuatro discapacidades básicas son obligatorias")
        return self


class IndagacionAbierta(Contrato):
    nivel_actual: NivelIndagacion
    nivel_propuesto: Literal["estructurada", "guiada", "abierta"]
    pregunta_ejemplo: str = Field(min_length=15, max_length=300)
    como_formulan_preguntas: str = Field(min_length=40, max_length=600)
    variable_independiente: str = Field(min_length=3, max_length=200)
    variable_dependiente: str = Field(min_length=3, max_length=200)
    variables_controladas: tuple[str, ...] = Field(min_length=1, max_length=5)
    diseno_por_estudiantes: str = Field(min_length=40, max_length=700)
    error_y_repeticion: str = Field(min_length=40, max_length=500)
    seguridad: str = Field(min_length=20, max_length=400)

    @model_validator(mode="after")
    def _avance(self):
        orden = ("confirmacion", "estructurada", "guiada", "abierta")
        if orden.index(self.nivel_propuesto) < orden.index(self.nivel_actual):
            raise ValueError("La propuesta no puede reducir la autonomía de indagación del guion")
        return self


class ContextoNacional(Contrato):
    afirmaciones: tuple[AfirmacionClase, ...] = Field(max_length=3)
    fuente_a_consultar: str | None = Field(default=None, min_length=20, max_length=400)

    @model_validator(mode="after")
    def _algo(self):
        if not self.afirmaciones and not self.fuente_a_consultar:
            raise ValueError("Sin fuente nacional registrada, indica qué fuente oficial consultar")
        return self


class AnexoClase(Contrato):
    version: Literal["anexo-clase-1"]
    fila_id: str = Field(min_length=1, max_length=200)
    guion_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    recursos: Recursos
    version_minima: VersionMinima
    progresion: Progresion
    inclusion: Inclusion
    indagacion: IndagacionAbierta
    contexto_nacional: ContextoNacional


class Opcion(Contrato):
    letra: Literal["A", "B", "C", "D"]
    texto: str = Field(min_length=1, max_length=300)
    concepcion_que_detecta: str | None = Field(default=None, min_length=15, max_length=300)


class ItemEvaluacion(Contrato):
    id: str = Field(pattern=r"^I[0-9]{2}$")
    fila_id: str = Field(min_length=1, max_length=200)
    dominio: Literal["conocer", "aplicar", "razonar"]
    formato: Literal["opcion_multiple", "respuesta_construida"]
    enunciado: str = Field(min_length=30, max_length=1200)
    opciones: tuple[Opcion, ...] = Field(max_length=4)
    clave: str = Field(min_length=1, max_length=1200)
    justificacion: str = Field(min_length=30, max_length=800)
    rubrica: tuple[CriterioRubrica, ...] = Field(max_length=3)
    calculos: tuple[ComprobacionCalculo, ...] = Field(max_length=4)
    datos_simulados: bool

    @model_validator(mode="after")
    def _formato(self):
        if self.formato == "opcion_multiple":
            letras = [o.letra for o in self.opciones]
            distractores = [o for o in self.opciones if o.letra != self.clave]
            if letras != ["A", "B", "C", "D"] or self.clave not in letras or self.rubrica:
                raise ValueError("Opción múltiple: opciones A–D en orden, clave entre ellas y sin rúbrica")
            if any(not o.concepcion_que_detecta for o in distractores):
                raise ValueError("Cada distractor declara la concepción alternativa que detecta")
        elif self.opciones or not self.rubrica:
            raise ValueError("Respuesta construida: sin opciones y con rúbrica")
        return self


class EvaluacionUnidad(Contrato):
    version: Literal["evaluacion-unidad-1"]
    unidad_id: str = Field(min_length=1, max_length=200)
    minutos: int = Field(ge=30, le=90)
    items: tuple[ItemEvaluacion, ...] = Field(min_length=6, max_length=24)

    @model_validator(mode="after")
    def _balance(self):
        if len({i.id for i in self.items}) != len(self.items):
            raise ValueError("Los ítems no pueden repetir identificador")
        dominios = [i.dominio for i in self.items]
        if dominios.count("razonar") * 5 < len(dominios):
            raise ValueError("Al menos 20 % de los ítems evalúa razonamiento")
        if dominios.count("conocer") * 5 > 2 * len(dominios):
            raise ValueError("Como máximo 40 % de los ítems evalúa sólo conocimiento")
        if not any(i.formato == "respuesta_construida" for i in self.items):
            raise ValueError("La evaluación incluye al menos un ítem de respuesta construida")
        return self


def errores_calculos(calculos) -> list[str]:
    """Recompute declared arithmetic with the same safe evaluator used for the scripts."""
    errores = []
    for c in calculos:
        try:
            obtenido = calcular(c.expresion)
        except (ValueError, SyntaxError, ZeroDivisionError) as error:
            errores.append(f"Cálculo inválido {c.expresion!r}: {error}")
            continue
        if not math.isclose(
            obtenido,
            c.resultado,
            rel_tol=min(c.tolerancia_relativa, 1e-6),
            abs_tol=min(c.tolerancia, abs(c.resultado) * 1e-6),
        ):
            errores.append(f"{c.expresion!r} produce {obtenido!r}, no {c.resultado!r}")
    return errores


def validar_anexo(anexo: AnexoClase, guion: GuionClase, guion_sha256: str, candidatos: dict) -> list[str]:
    """Check that an annex refers to the exact released script and only to registered progression links.

    `candidatos` maps "previas" and "continuidad" to sets of (concepto, fila_id) pairs derived from the
    progression layer; `fuentes` is the set of registered source ids allowed for national context.
    """
    errores = []
    if anexo.fila_id != guion.fila_id or anexo.guion_sha256 != guion_sha256:
        errores.append("El anexo no está anclado al guion liberado exacto")
    bloques = {(s.numero, i): b for s in guion.sesiones for i, b in enumerate(s.bloques, 1)}
    ajustes = {(a.sesion, a.bloque): a for a in anexo.version_minima.ajustes}
    if len(ajustes) != len(anexo.version_minima.ajustes) or set(ajustes) != set(bloques):
        errores.append("La versión mínima debe decidir sobre cada bloque del guion exactamente una vez")
    else:
        for clave, ajuste in ajustes.items():
            if ajuste.minutos > bloques[clave].minutos:
                errores.append(f"El bloque {clave} no puede durar más que en el guion")
        for sesion in guion.sesiones:
            usados = sum(ajustes[(sesion.numero, i)].minutos for i in range(1, len(sesion.bloques) + 1))
            if usados != anexo.version_minima.minutos_efectivos:
                errores.append(
                    f"La sesión {sesion.numero} mínima suma {usados} minutos; debe sumar los "
                    f"{anexo.version_minima.minutos_efectivos} minutos efectivos declarados"
                )
        conservadas = {bloques[k].fase for k, a in ajustes.items() if a.accion != "omitir"}
        if "explicar" not in conservadas or not conservadas & {"explorar", "indagar"}:
            errores.append("La versión mínima conserva la explicación y al menos una fase de exploración o indagación")
        if set(FASES) - conservadas and not any(a.nota for a in ajustes.values() if a.accion == "omitir"):
            errores.append("Omitir una fase exige explicar cómo se compensa")
    if anexo.version_minima.tarea_prioritaria > len(guion.tareas):
        errores.append("La tarea prioritaria no existe en el guion")
    for campo in ("ideas_previas", "continuidad"):
        permitidos = candidatos.get("previas" if campo == "ideas_previas" else "continuidad", set())
        for enlace in getattr(anexo.progresion, campo):
            if (enlace.concepto, enlace.fila_id) not in permitidos:
                errores.append(f"Enlace de progresión no registrado: {enlace.concepto} → {enlace.fila_id}")
    fuentes = candidatos.get("fuentes", set())
    for afirmacion in anexo.contexto_nacional.afirmaciones:
        if set(afirmacion.fuentes_ids) - fuentes:
            errores.append("El contexto nacional cita una fuente que no está registrada para esta clase")
    return errores


def validar_evaluacion(evaluacion: EvaluacionUnidad, unidad_id: str, filas: set[str]) -> list[str]:
    """Require full coverage of the unit's released objectives and correct arithmetic."""
    errores = [] if evaluacion.unidad_id == unidad_id else ["La evaluación no corresponde a la unidad"]
    citadas = {i.fila_id for i in evaluacion.items}
    if citadas - filas:
        errores.append("Hay ítems sobre objetivos que no pertenecen a la unidad publicada")
    if filas - citadas:
        errores.append(f"Faltan ítems para {len(filas - citadas)} objetivos con guion publicado")
    for item in evaluacion.items:
        errores += [f"{item.id}: {e}" for e in errores_calculos(item.calculos)]
    return errores


def markdown_anexo(anexo: dict, titulo: str) -> str:
    """Render the teacher-facing annex as plain Markdown."""
    a = AnexoClase.model_validate(anexo)
    r, m, p, inc, ind, ctx = (
        a.recursos,
        a.version_minima,
        a.progresion,
        a.inclusion,
        a.indagacion,
        a.contexto_nacional,
    )
    lineas = [f"# Anexo de implementación · {titulo}", "", f"> {LIMITE}", "", "## Recursos", ""]
    lineas.append(f"Nivel: {r.nivel.replace('_', ' ')} · costo {r.costo}.")
    requisitos = [
        n
        for n, v in (
            ("electricidad", r.requiere_electricidad),
            ("agua", r.requiere_agua),
            ("espacio exterior", r.requiere_exterior),
            ("conectividad", r.requiere_conectividad),
        )
        if v
    ]
    lineas.append("Requiere: " + (", ".join(requisitos) if requisitos else "nada adicional") + ".")
    lineas += [
        f"- {x.material}" + (f" → sustituto: {x.sustituto_casero}" if x.sustituto_casero else "") for x in r.materiales
    ]
    lineas += ["", f"## Versión mínima ({m.minutos_efectivos} minutos efectivos por sesión)", ""]
    for x in m.ajustes:
        lineas.append(
            f"- Sesión {x.sesion}, bloque {x.bloque}: {x.accion} ({x.minutos} min)" + (f". {x.nota}" if x.nota else "")
        )
    lineas += [f"- Tarea prioritaria: {m.tarea_prioritaria}. Evidencia mínima: {m.evidencia_minima}", ""]
    lineas += ["## Progresión entre grados", ""]
    lineas += [f"- Viene de {e.grado}.º ({e.concepto}): {e.como_usarlo}" for e in p.ideas_previas]
    if p.sin_antecedente:
        lineas.append(f"- Sin antecedente registrado: {p.sin_antecedente}")
    lineas += [f"- Continúa en {e.grado}.º ({e.concepto}): {e.como_usarlo}" for e in p.continuidad]
    lineas += ["", "## Inclusión", ""]
    lineas += [f"- {x.necesidad.replace('_', ' ').capitalize()}: {x.ajuste}" for x in inc.adecuaciones]
    lineas += [f"- Multigrado: {inc.multigrado}", f"- Contexto rural: {inc.contexto_rural}", ""]
    lineas += ["### Hoja del estudiante en lectura fácil", "", inc.hoja_lectura_facil, ""]
    lineas += [f"## Indagación abierta ({ind.nivel_actual} → {ind.nivel_propuesto})", ""]
    lineas += [
        f"- Pregunta de ejemplo: {ind.pregunta_ejemplo}",
        f"- Cómo formulan sus preguntas: {ind.como_formulan_preguntas}",
        f"- Variables: cambia {ind.variable_independiente}; se mide {ind.variable_dependiente}; "
        f"se mantienen {', '.join(ind.variables_controladas)}.",
        f"- Diseño por estudiantes: {ind.diseno_por_estudiantes}",
        f"- Error y repetición: {ind.error_y_repeticion}",
        f"- Seguridad: {ind.seguridad}",
        "",
        "## Contexto salvadoreño",
        "",
    ]
    lineas += [f"- {x.texto} Fuentes: {', '.join(x.fuentes_ids)}" for x in ctx.afirmaciones]
    if ctx.fuente_a_consultar:
        lineas.append(f"- Fuente oficial a consultar: {ctx.fuente_a_consultar}")
    return "\n".join(lineas) + "\n"
