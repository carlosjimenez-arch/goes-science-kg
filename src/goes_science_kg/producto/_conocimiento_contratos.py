"""Contratos de descubrimiento: una hipótesis de enlace nunca es un dictamen."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from goes_science_kg.curriculo.contratos import ContratoCurricular
from goes_science_kg.motor.contratos import Evidencia


class EdicionEsperada(ContratoCurricular):
    """Edición fijada por el integrador; no afirma vigencia normativa por su fecha."""

    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    version_documental: str = Field(min_length=1)


class PoliticaConocimiento(ContratoCurricular):
    """Presupuestos explícitos para que la generación de propuestas sea reproducible."""

    version: Literal["descubrimiento-1"] = "descubrimiento-1"
    campos_locales: tuple[str, ...] = (
        "procedimental",
        "indicadores_logro",
        "evidencia_aprendizaje",
        "contenido",
        "subcontenido",
    )
    max_conceptos_por_fila: int = Field(default=8, ge=1, le=32)
    max_objetivos_pais_por_fila: int = Field(default=6, ge=1, le=24)
    max_prerrequisitos_por_fila: int = Field(default=8, ge=1, le=32)
    ediciones_por_documento: dict[str, EdicionEsperada] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _campos_conocidos(self) -> PoliticaConocimiento:
        permitidos = {
            "procedimental",
            "indicadores_logro",
            "indicador_avanzado",
            "evidencia_aprendizaje",
            "contenido",
            "subcontenido",
        }
        if (
            not self.campos_locales
            or len(set(self.campos_locales)) != len(self.campos_locales)
            or (set(self.campos_locales) - permitidos)
        ):
            raise ValueError("Campos locales vacíos, duplicados o fuera de los objetivos/evidencias curriculares")
        return self


class CandidatoConocimiento(ContratoCurricular):
    """Propuesta con anclas y bloqueos, excluida de toda arista curricular aceptada."""

    id: str
    tipo: Literal["fila_concepto", "fila_practica", "contraste_pais", "prerrequisito"]
    fila_id: str
    origen: str
    destino: str
    metodo: Literal["alias_literal", "ruta_historica_por_revalidar"]
    estado: Literal["candidato", "ambiguo", "bloqueado"]
    advertencias: tuple[str, ...] = ()
    bloqueos_aceptacion: tuple[str, ...] = ()
    evidencias_locales: tuple[str, ...]
    referencias_evidencia: tuple[str, ...] = ()
    alternativas: tuple[str, ...] = ()
    contexto: dict[str, Any]


class DAGNoValidado(ContratoCurricular):
    """Un DAG vacío no equivale a una progresión educativa verificada."""

    estado: Literal["sin_progresion_verificada"] = "sin_progresion_verificada"
    nodos: tuple[()] = ()
    aristas: tuple[()] = ()
    ciclos_candidatos: tuple[tuple[str, ...], ...] = ()


class InformeConocimiento(ContratoCurricular):
    """Paquete para juicio especializado posterior; no contiene la puerta de aceptación."""

    version: Literal["conocimiento-candidatos-1"] = "conocimiento-candidatos-1"
    version_curriculo: Literal["V4"] = "V4"
    huella_curriculo: str
    huella_referencia: str
    procedencia_referencia: dict[str, Any]
    huella_pipeline: str
    huella_candidatos: str
    politica: PoliticaConocimiento
    candidatos: tuple[CandidatoConocimiento, ...]
    evidencias: dict[str, Evidencia]
    referencias: dict[str, dict[str, Any]]
    por_fila: dict[str, dict[str, Any]]
    por_concepto: dict[str, dict[str, Any]]
    por_pais: dict[str, dict[str, Any]]
    aceptados: tuple[()] = ()
    dag_aceptado: DAGNoValidado
    resumen: dict[str, Any]
    metricas: dict[str, Any]
    limites: tuple[str, ...]
