"""Contratos de aplicación; un dictamen automático nunca equivale a aprobación del MINED."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Asignatura = Literal["biologia", "fisica", "quimica", "ciencias_tierra_espacio"]
Rol = Literal["cientifico", "psicopedagogo", "adversarial"]


class Contrato(BaseModel):
    """Rechaza campos inesperados, especialmente en las respuestas del modelo."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class Solicitud(Contrato):
    consulta: str = Field(min_length=5, max_length=2000)
    version_curriculo: str = Field(min_length=2, max_length=30)
    grado: int = Field(ge=2, le=11)
    asignatura: Asignatura
    minutos: int = Field(default=40, ge=5, le=120)
    recursos: tuple[str, ...] = ("papel", "lapiz")
    fila_id: str | None = Field(default=None, min_length=1, max_length=200)


class Evidencia(Contrato):
    id: str
    texto: str
    fuente: dict[str, Any]
    version: str
    huella: str

    @classmethod
    def crear(cls, id: str, texto: str, fuente: dict, version: str) -> Evidencia:
        return cls(
            id=id, texto=texto, fuente=fuente, version=version, huella=hashlib.sha256(texto.encode()).hexdigest()
        )


class Cita(Contrato):
    evidencia_id: str
    literal: str = Field(min_length=12, max_length=280)

    @field_validator("literal")
    @classmethod
    def _cita_breve(cls, texto: str) -> str:
        if len(texto.split()) > 20:
            raise ValueError("La cita debe contener como máximo veinte palabras")
        return texto


class Afirmacion(Contrato):
    texto: str = Field(min_length=10, max_length=1500)
    citas: list[Cita] = Field(min_length=1, max_length=5)


class Actividad(Contrato):
    objetivo: str = Field(min_length=10)
    pasos: list[str] = Field(min_length=1, max_length=8)
    comprobacion: str = Field(min_length=10)
    minutos: int = Field(ge=1, le=120)
    recursos: list[str]
    adaptacion_salvador: str = Field(min_length=10)


class Propuesta(Contrato):
    """Las afirmaciones son el texto factual publicable; la actividad es una propuesta."""

    afirmaciones: list[Afirmacion] = Field(min_length=1, max_length=8)
    anclaje_curricular: list[Cita] = Field(min_length=1, max_length=5)
    actividad: Actividad
    limites: list[str] = Field(min_length=1)


class Revision(Contrato):
    """Salida del juez. Su rol y la huella evaluada se añaden fuera del modelo."""

    aprobado: bool
    errores: list[str]
    criterios: dict[str, bool]
    evidencia_ids: list[str]


class CriteriosCientificos(Contrato):
    correccion_cientifica: bool
    respaldo_de_afirmaciones: bool
    alineacion_curricular: bool


class CriteriosPsicopedagogicos(Contrato):
    adecuacion_al_grado: bool
    carga_cognitiva: bool
    evaluacion_del_objetivo: bool
    accesibilidad: bool


class CriteriosAdversariales(Contrato):
    sin_contradicciones: bool
    citas_implican_afirmaciones: bool
    seguridad_y_factibilidad: bool


class RevisionCientifica(Contrato):
    aprobado: bool
    errores: list[str]
    criterios: CriteriosCientificos
    evidencia_ids: list[str]


class RevisionPsicopedagogica(Contrato):
    aprobado: bool
    errores: list[str]
    criterios: CriteriosPsicopedagogicos
    evidencia_ids: list[str]


class RevisionAdversarial(Contrato):
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
    rol: Rol
    modelo: str
    huella_propuesta: str
    revision: Revision


class ResultadoMotor(Contrato):
    estado: Literal["respaldado_automaticamente", "abstencion"]
    ejecucion_id: str
    version_curriculo: str
    propuesta: Propuesta | None
    dictamenes: list[Dictamen]
    motivos: list[str]
    evidencias: list[Evidencia]
    iteraciones: int


def huella(valor: BaseModel | dict | list) -> str:
    """Identidad de contenido para invalidar dictámenes, cachés y checkpoints."""
    datos = valor.model_dump(mode="json") if isinstance(valor, BaseModel) else valor
    return hashlib.sha256(json.dumps(datos, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
