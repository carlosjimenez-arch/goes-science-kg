"""Describe observed mental-effort self-reports without inventing cognitive-load scores."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EscalaEsfuerzo(BaseModel):
    """Keep every ordinal response category explicit and preserve its original numbering."""

    model_config = ConfigDict(extra="forbid", strict=True)

    minimo: int = 1
    categorias: list[str] = Field(min_length=2)

    @field_validator("categorias")
    @classmethod
    def categorias_distintas(cls, valores: list[str]) -> list[str]:
        """Reject missing or duplicate anchors instead of guessing their interpretation."""
        valores = [v.strip() for v in valores]
        if any(not v for v in valores) or len({v.casefold() for v in valores}) != len(valores):
            raise ValueError("Cada categoría ordinal requiere una etiqueta distinta y no vacía")
        return valores


class AutoinformeEsfuerzo(BaseModel):
    """Record one task-specific response and the conditions under which it was obtained."""

    model_config = ConfigDict(extra="forbid", strict=True)

    registro_id: str = Field(min_length=1)
    instrumento_id: str = Field(min_length=1)
    version: str = Field(min_length=1)
    referencia: str = Field(min_length=1)
    idioma: str = Field(min_length=1)
    pregunta: str = Field(min_length=1)
    escala: EscalaEsfuerzo
    grado: int = Field(ge=2, le=11)
    tarea: str = Field(min_length=1)
    momento: str = Field(min_length=1)
    contexto_aplicacion: str = Field(min_length=1)
    ayuda_conceptual: bool
    adaptaciones_acceso: list[str] = Field(default_factory=list)
    origen: Literal["estudiante", "simulacion"]
    respuesta: int | None = None

    @field_validator("*", mode="before")
    @classmethod
    def texto_no_vacio(cls, valor):
        """Reject whitespace-only metadata while leaving structured values unchanged."""
        if isinstance(valor, str):
            valor = valor.strip()
            if not valor:
                raise ValueError("El metadato no puede estar vacío")
        return valor

    @field_validator("adaptaciones_acceso")
    @classmethod
    def adaptaciones_declaradas(cls, valores: list[str]) -> list[str]:
        """Normalize access accommodations independently of conceptual help."""
        valores = [v.strip() for v in valores]
        if any(not v for v in valores):
            raise ValueError("Cada adaptación de acceso debe estar descrita")
        return sorted(set(valores))

    @model_validator(mode="after")
    def categoria_en_escala(self) -> AutoinformeEsfuerzo:
        """Require an actual category, or preserve a missing response as missing."""
        if self.respuesta is not None:
            maximo = self.escala.minimo + len(self.escala.categorias) - 1
            if not self.escala.minimo <= self.respuesta <= maximo:
                raise ValueError("La respuesta debe corresponder a una categoría de la escala declarada")
        return self


def resumen_esfuerzo(registros: Sequence[dict | AutoinformeEsfuerzo] | None = None) -> dict:
    """Summarize compatible real observations; simulations never count as learner measurements."""
    observaciones = [AutoinformeEsfuerzo.model_validate(r) for r in registros or []]
    if len({r.registro_id for r in observaciones}) != len(observaciones):
        raise ValueError("Un registro de autoinforme no se puede contar dos veces")
    reales = [r for r in observaciones if r.origen == "estudiante"]
    respuestas_reales = sum(r.respuesta is not None for r in reales)
    grupos = defaultdict(list)
    for registro in reales:
        condiciones = registro.model_dump(exclude={"registro_id", "origen", "respuesta"})
        clave = json.dumps(condiciones, ensure_ascii=False, sort_keys=True)
        grupos[clave].append(registro)
    resultados = []
    for clave, grupo in sorted(grupos.items()):
        condiciones = json.loads(clave)
        valores = sorted(r.respuesta for r in grupo if r.respuesta is not None)
        conteos = Counter(valores)
        escala = grupo[0].escala
        centrales = [valores[(len(valores) - 1) // 2], valores[len(valores) // 2]] if valores else None
        resultados.append(
            {
                **condiciones,
                "n_registros": len(grupo),
                "n_respuestas": len(valores),
                "n_faltantes": len(grupo) - len(valores),
                "distribucion": [
                    {"categoria": escala.minimo + i, "etiqueta": etiqueta, "n": conteos[escala.minimo + i]}
                    for i, etiqueta in enumerate(escala.categorias)
                ],
                "categorias_centrales": centrales,
            }
        )
    return {
        "estado": "observado_sin_inferencia_causal"
        if respuestas_reales
        else "solo_simulado"
        if observaciones and not reales
        else "no_medido",
        "constructo": "esfuerzo_mental_autoinformado",
        "n_reales": len(reales),
        "n_respuestas_reales": respuestas_reales,
        "n_faltantes_reales": len(reales) - respuestas_reales,
        "n_simulados": len(observaciones) - len(reales),
        "unidad_conteo": "registros por tarea; no estudiantes únicos",
        "grupos": resultados,
        "limite": "El autoinforme no mide por sí solo aprendizaje ni separa tipos de carga cognitiva. "
        "El instrumento y su adaptación requieren validación en la población y contexto de uso. "
        "No se comparan grupos, no se aplica un umbral de sobrecarga y no se calcula eficacia.",
    }
