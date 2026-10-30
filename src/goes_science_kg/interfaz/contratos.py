"""Public response schemas for the GOEs curriculum application."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IdentidadSnapshot(BaseModel):
    """Identify the immutable curriculum generation used by a response."""

    model_config = ConfigDict(extra="forbid")
    version_curriculo: Literal["V4"]
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")


class FichaFila(BaseModel):
    """Expose original row metadata and its published proposal state."""

    model_config = ConfigDict(extra="forbid")
    id: str
    grado: int = Field(ge=2, le=11)
    asignatura: str
    unidad: str
    objetivo_original: str
    objetivo_propuesto: str | None
    accion: str | None
    disciplinas: tuple[str, ...]
    estado_clasificacion: str
    estado_revision: str
    preparacion_id: str
    fuera_alcance: bool
    alerta_original: str | None
    hoja: str
    fila: int


class PaginaFilas(IdentidadSnapshot):
    """Return a stable page while retaining the full filtered denominator."""

    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limite: int = Field(ge=1, le=200)
    filas: list[FichaFila]


class DocumentoFuente(BaseModel):
    """Describe a registered source without inventing links or licenses."""

    model_config = ConfigDict(extra="forbid")
    id: str
    titulo: str
    sha256: str | None
    url: str | None
    tipo: Literal["curriculo", "referencia"]
    version_documental: str | None
    licencia: str | None
    usos: int = Field(ge=0)


class ListaDocumentos(IdentidadSnapshot):
    """Return the sources registered or cited in this publication."""

    total: int = Field(ge=0)
    documentos: list[DocumentoFuente]


class NodoVisual(BaseModel):
    """Represent a real graph node independently of its visual coordinates."""

    id: str
    tipo: str
    etiqueta: str
    grado: int | None
    asignatura: str | None
    conexiones: int = Field(ge=0)


class AristaVisual(BaseModel):
    """Preserve the published type and endpoints of a graph edge."""

    origen: str
    destino: str
    tipo: str


class RespuestaGrafo(IdentidadSnapshot):
    """Describe a bounded subgraph and disclose any truncation."""

    total_nodos_filtrados: int = Field(ge=0)
    limite: int = Field(ge=10, le=800)
    recortado: bool
    nodos: list[NodoVisual]
    aristas: list[AristaVisual]
    limite_semantico: str


class BriefDocumental(IdentidadSnapshot):
    """Deliver a compiled brief with its row and snapshot provenance."""

    fila_id: str
    formato: Literal["evaluacion", "cinco_fases"]
    titulo: str
    markdown: str
    llamadas_modelos: Literal[0]


class RespuestaBriefs(IdentidadSnapshot):
    """Return existing curricular content without a model invocation."""

    briefs: list[BriefDocumental]
    llamadas_modelos: Literal[0]
