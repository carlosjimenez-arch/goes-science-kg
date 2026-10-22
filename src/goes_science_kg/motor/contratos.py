"""Define application contracts that distinguish automatic review from official approval."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Asignatura = Literal["biologia", "fisica", "quimica", "ciencias_tierra_espacio"]
Rol = Literal["cientifico", "psicopedagogo", "adversarial"]


class Contrato(BaseModel):
    """Reject unexpected fields, especially in structured model responses."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Solicitud(Contrato):
    """Declare the curriculum query, grade, subject, duration, resources, and optional exact row."""

    consulta: str = Field(min_length=5, max_length=2000)
    version_curriculo: str = Field(min_length=2, max_length=30)
    grado: int = Field(ge=2, le=11)
    asignatura: Asignatura
    minutos: int = Field(default=40, ge=5, le=120)
    recursos: tuple[str, ...] = ("papel", "lapiz")
    fila_id: str | None = Field(default=None, min_length=1, max_length=200)


class Evidencia(Contrato):
    """Bind evidence text to its source, curriculum version, and content fingerprint."""

    id: str
    texto: str
    fuente: dict[str, Any]
    version: str
    huella: str

    @classmethod
    def crear(cls, id: str, texto: str, fuente: dict, version: str) -> Evidencia:
        """Create evidence with a deterministic content and provenance fingerprint."""

        return cls(
            id=id, texto=texto, fuente=fuente, version=version, huella=hashlib.sha256(texto.encode()).hexdigest()
        )


class Cita(Contrato):
    """Quote an exact literal from a registered evidence item."""

    evidencia_id: str
    literal: str = Field(min_length=12, max_length=280)

    @field_validator("literal")
    @classmethod
    def _cita_breve(cls, texto: str) -> str:
        if len(texto.split()) > 20:
            raise ValueError("La cita debe contener como máximo veinte palabras")
        return texto


class Afirmacion(Contrato):
    """Bind one factual statement to the evidence quotations supporting it."""

    texto: str = Field(min_length=10, max_length=1500)
    citas: list[Cita] = Field(min_length=1, max_length=5)


class Actividad(Contrato):
    """Describe a proposed learning activity and its observable assessment."""

    objetivo: str = Field(min_length=10)
    pasos: list[str] = Field(min_length=1, max_length=8)
    comprobacion: str = Field(min_length=10)
    minutos: int = Field(ge=1, le=120)
    recursos: list[str]
    adaptacion_salvador: str = Field(min_length=10)


class Propuesta(Contrato):
    """Separate publishable factual statements from proposed learning activities."""

    afirmaciones: list[Afirmacion] = Field(min_length=1, max_length=8)
    anclaje_curricular: list[Cita] = Field(min_length=1, max_length=5)
    actividad: Actividad
    limites: list[str] = Field(min_length=1)


class Revision(Contrato):
    """Represent a review whose role and evaluated fingerprint are assigned outside the model."""

    aprobado: bool
    errores: list[str]
    criterios: dict[str, bool]
    evidencia_ids: list[str]


class CriteriosCientificos(Contrato):
    """Require scientific accuracy, claim support, and curriculum alignment."""

    correccion_cientifica: bool
    respaldo_de_afirmaciones: bool
    alineacion_curricular: bool


class CriteriosPsicopedagogicos(Contrato):
    """Require grade suitability, bounded cognitive load, assessment, and accessibility."""

    adecuacion_al_grado: bool
    carga_cognitiva: bool
    evaluacion_del_objetivo: bool
    accesibilidad: bool


class CriteriosAdversariales(Contrato):
    """Require consistency, evidential implication, safety, and feasibility."""

    sin_contradicciones: bool
    citas_implican_afirmaciones: bool
    seguridad_y_factibilidad: bool


class RevisionCientifica(Contrato):
    """Represent the scientific review with mandatory criteria and cited evidence."""

    aprobado: bool
    errores: list[str]
    criterios: CriteriosCientificos
    evidencia_ids: list[str]


class RevisionPsicopedagogica(Contrato):
    """Represent the pedagogical review with mandatory criteria and cited evidence."""

    aprobado: bool
    errores: list[str]
    criterios: CriteriosPsicopedagogicos
    evidencia_ids: list[str]


class RevisionAdversarial(Contrato):
    """Represent the adversarial review with mandatory criteria and cited evidence."""

    aprobado: bool
    errores: list[str]
    criterios: CriteriosAdversariales
    evidencia_ids: list[str]


ESQUEMAS_REVISION = {
    "cientifico": RevisionCientifica,
    "psicopedagogo": RevisionPsicopedagogica,
    "adversarial": RevisionAdversarial,
}


class Dictamen(Contrato):
    """Bind a reviewer's output to its model and exact proposal fingerprint."""

    rol: Rol
    modelo: str
    huella_propuesta: str
    revision: Revision


class ResultadoMotor(Contrato):
    """Preserve the engine outcome, evidence, reviews, iterations, and abstention reasons."""

    estado: Literal["respaldado_automaticamente", "abstencion"]
    ejecucion_id: str
    version_curriculo: str
    propuesta: Propuesta | None
    dictamenes: list[Dictamen]
    motivos: list[str]
    evidencias: list[Evidencia]
    iteraciones: int


def huella(valor: BaseModel | dict | list) -> str:
    """Fingerprint content to invalidate stale reviews, caches, and checkpoints."""
    datos = valor.model_dump(mode="json") if isinstance(valor, BaseModel) else valor
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
