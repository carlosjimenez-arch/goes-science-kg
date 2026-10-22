"""Define semantic dossiers and outcomes separately from institutional approval."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from goes_science_kg.motor.contratos import Cita, Contrato, Evidencia
from goes_science_kg.motor.fragmentos import Fragmento

ROLES_CONOCIMIENTO = ("juez_ciencia", "juez_curriculo", "juez_psicopedagogia", "juez_refutador")
VERSION_JUICIOS = "juicio-conocimiento-1"
Valor = Literal["si", "no", "insuficiente"]
TipoRelacion = Literal["trabaja_concepto", "practica_declarada", "contraste_documental", "prerrequisito_necesario"]
LIMITE_JUICIOS = (
    "Respaldo semántico automático limitado a la fila y fuentes examinadas; no acredita aprendizaje, "
    "eficacia, equivalencia de grados, cobertura de un marco ni aprobación del MINED"
)


class SoporteSemantico(Contrato):
    """Locate semantic evidence through a trusted documentary catalog."""

    candidato_id: str
    grupo: Literal["destino", "origen", "dependencia"]
    documento: str = Field(min_length=1)
    pagina: int | None = Field(default=None, strict=True, ge=1)
    localizador: str | None = None
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    version_documental: str = Field(min_length=1)


class SolicitudConocimiento(Contrato):
    """Request review of one explicit knowledge-candidate identity."""

    candidato_id: str = Field(pattern=r"^CANDIDATO_V4:[a-f0-9]{64}$")


class ExpedienteConocimiento(Contrato):
    """Preserve a complete semantic-review dossier with verified source context."""

    version: Literal["juicio-conocimiento-1"] = VERSION_JUICIOS
    estado: Literal["preparado", "abstencion"]
    candidato_id: str
    huella_curriculo: str
    huella_referencia: str
    huella_candidato: str
    fila_id: str
    grado: int
    asignatura_malla: str
    tipo_relacion: TipoRelacion
    origen: str
    destino: str
    descriptores: dict
    grupos: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    evidencias: tuple[Evidencia, ...] = ()
    fragmentos: tuple[Fragmento, ...] = ()
    motivos: tuple[str, ...] = ()
    limite: str = LIMITE_JUICIOS


class CriteriosComunes(Contrato):
    """Require source implication, bounded interpretation, and explicit relationship conditions."""

    fuentes_implican_relacion: Valor
    sin_extrapolar_de_mencion_o_orden: Valor
    alcance_y_condiciones_explicitos: Valor


class CriteriosCiencia(CriteriosComunes):
    """Require scientific correctness and primary evidence for definitions or performances."""

    significado_cientifico_correcto: Valor
    definicion_o_desempeno_primario: Valor


class CriteriosCurriculo(CriteriosComunes):
    """Require explicit local performance, compatible cognitive demand, and preserved modality."""

    desempeno_local_explicito: Valor
    demanda_cognitiva_compatible: Valor
    modalidades_y_traduccion_respetadas: Valor


class CriteriosPsicopedagogia(CriteriosComunes):
    """Require grade suitability, justified cognitive supports, and demonstrated applicability."""

    alcance_adecuado_al_grado_sv: Valor
    carga_y_apoyos_justificados: Valor
    necesidad_cognitiva_o_aplicabilidad_demostrada: Valor


class CriteriosRefutacion(CriteriosComunes):
    """Require ambiguity resolution and explicit dismissal of counterexamples and alternatives."""

    ambiguedades_y_negaciones_resueltas: Valor
    contraejemplos_y_alternativas_descartados: Valor


class LecturaConocimiento(Contrato):
    """Record a semantic reading with required criteria, fragment selections, and limitations."""

    criterios: CriteriosComunes
    fragmentos_ids: tuple[str, ...] = Field(min_length=2, max_length=12)
    explicacion: str = Field(min_length=20, max_length=1200)
    limites: tuple[str, ...] = Field(min_length=1, max_length=8)

    @field_validator("fragmentos_ids", "limites")
    @classmethod
    def _unicos_no_vacios(cls, valores):
        if len(set(valores)) != len(valores) or any(not v.strip() for v in valores):
            raise ValueError("Se requieren valores únicos y no vacíos")
        return valores


class LecturaCiencia(LecturaConocimiento):
    """Represent the scientific specialist's semantic relationship reading."""

    criterios: CriteriosCiencia


class LecturaCurriculo(LecturaConocimiento):
    """Represent the curriculum specialist's semantic relationship reading."""

    criterios: CriteriosCurriculo


class LecturaPsicopedagogia(LecturaConocimiento):
    """Represent the pedagogical specialist's semantic relationship reading."""

    criterios: CriteriosPsicopedagogia


class LecturaRefutacion(LecturaConocimiento):
    """Represent the adversarial specialist's semantic relationship reading."""

    criterios: CriteriosRefutacion


ESQUEMAS_CONOCIMIENTO = dict(
    zip(ROLES_CONOCIMIENTO, (LecturaCiencia, LecturaCurriculo, LecturaPsicopedagogia, LecturaRefutacion), strict=True)
)


class DictamenConocimiento(Contrato):
    """Bind a semantic judgment to its exact task, reviewer model, criteria, and quotations."""

    rol: Literal["juez_ciencia", "juez_curriculo", "juez_psicopedagogia", "juez_refutador"]
    modelo: str = Field(min_length=1)
    huella_tarea: str
    criterios: dict[str, Valor]
    citas: tuple[Cita, ...] = Field(min_length=2, max_length=12)
    explicacion: str = Field(min_length=20, max_length=1200)
    limites: tuple[str, ...] = Field(min_length=1, max_length=8)


class RelacionRespaldada(Contrato):
    """Represent a row-conditioned relationship without promoting it to universal concept truth."""

    id: str = Field(pattern=r"^RELACION_V4:[a-f0-9]{64}$")
    tipo: TipoRelacion
    origen: str
    destino: str
    fila_id: str
    grado_sv: int
    huella_curriculo: str
    huella_tarea: str
    ambito: Literal["fila_curricular"] = "fila_curricular"


class ResultadoConocimiento(Contrato):
    """Preserve the semantic outcome, all judgments, conditional relationship, and limitations."""

    version: Literal["juicio-conocimiento-1"] = VERSION_JUICIOS
    estado: Literal["respaldado", "no_respaldado", "abstencion"]
    solicitud: SolicitudConocimiento
    ejecucion_id: str
    huella_tarea: str
    huella_motor: str
    dictamenes: tuple[DictamenConocimiento, ...]
    relacion: RelacionRespaldada | None = None
    motivos: tuple[str, ...]
    limite: str = LIMITE_JUICIOS


class ProyeccionDependencias(Contrato):
    """Describe accepted dependency projection, topological order, and any cyclic components."""

    estado: Literal["sin_prerrequisitos_respaldados", "aciclica", "bloqueada_por_ciclos"]
    nodos: tuple[str, ...]
    aristas: tuple[RelacionRespaldada, ...]
    componentes_ciclicas: tuple[tuple[str, ...], ...]
    orden_topologico: tuple[str, ...]
    alcance: Literal["proyeccion_conceptual_de_relaciones_condicionadas_a_filas"] = (
        "proyeccion_conceptual_de_relaciones_condicionadas_a_filas"
    )


class ColeccionConocimiento(Contrato):
    """Preserve the complete reviewed collection and its accepted and rejected relationships."""

    version: Literal["relaciones-v4-1"] = "relaciones-v4-1"
    huella_curriculo: str
    huella_motor: str
    huella_coleccion: str
    resultados: tuple[ResultadoConocimiento, ...]
    relaciones_respaldadas: tuple[RelacionRespaldada, ...]
    relaciones_admisibles: tuple[RelacionRespaldada, ...]
    proyeccion_dependencias: ProyeccionDependencias
    filas_examinadas: tuple[str, ...]
    limite: str = LIMITE_JUICIOS
