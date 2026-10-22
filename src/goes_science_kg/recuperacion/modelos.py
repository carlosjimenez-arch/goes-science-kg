"""Contratos de recuperación independientes del grafo y del proveedor de embeddings."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Documento(BaseModel):
    """Unidad recuperable: el texto y su procedencia conservan su versión de origen."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    texto: str = Field(min_length=1)
    fuente: dict[str, Any]
    version: str = Field(min_length=1)
    grado: int | None = Field(default=None, ge=1, le=13)
    asignatura: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id", "texto", "version")
    @classmethod
    def _no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El valor no puede contener únicamente espacios")
        return valor

    @field_validator("fuente")
    @classmethod
    def _documento_fuente(cls, valor: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(valor.get("documento"), str) or not valor["documento"].strip():
            raise ValueError("La fuente debe identificar su documento")
        return valor


class Resultado(BaseModel):
    """Resultado ordenado; el puntaje de fusión no representa una probabilidad."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    documento: Documento
    puntaje: float = Field(ge=0, allow_inf_nan=False)
    canales: tuple[str, ...]


class Enlace(BaseModel):
    """Relación dirigida utilizable para expansión controlada de evidencia."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    origen: str = Field(min_length=1)
    destino: str = Field(min_length=1)
    tipo: str = Field(min_length=1)
    peso: float = Field(default=1.0, gt=0, le=1)


def ordenar_documentos(documentos: Iterable[Documento]) -> tuple[Documento, ...]:
    """Copia y ordena el corpus; un identificador ambiguo invalida el índice."""
    ordenados = tuple(sorted((d.model_copy(deep=True) for d in documentos), key=lambda d: d.id))
    ids = [d.id for d in ordenados]
    if len(ids) != len(set(ids)):
        raise ValueError("El corpus contiene identificadores duplicados")
    return ordenados


def huella_corpus(documentos: Iterable[Documento]) -> str:
    """Huella estable ante reordenamiento; cambia con texto, filtros o procedencia."""
    datos = [d.model_dump(mode="json") for d in ordenar_documentos(documentos)]
    contenido = json.dumps(datos, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(contenido.encode("utf-8")).hexdigest()
