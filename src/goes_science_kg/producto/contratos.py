"""Define publication contracts independently of official curriculum approval."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import ContratoCurricular, Curriculo
from goes_science_kg.modelos import Arista, Nodo
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento
from goes_science_kg.producto.mejoras_publicadas import ArchivoMejoras


class ReferenciasProducto(ContratoCurricular):
    """Declare explicit references without inheriting previous curriculum topics."""

    nodos: tuple[Nodo, ...] = ()
    aristas: tuple[Arista, ...] = ()
    procedencia: dict[str, Any] = Field(default_factory=dict)


class AlertaSolicitada(ContratoCurricular):
    """Record a pending observation whose locator and value require materialization checks."""

    fila_id: str
    campo: str
    codigo: str = Field(min_length=1)
    descripcion: str = Field(min_length=5)


class ManifestProducto(ContratoCurricular):
    """Keep publication format and curriculum version as separate identities."""

    version: Literal["producto-2", "producto-3", "producto-4"] = "producto-2"
    version_curriculo: Literal["V4"] = "V4"
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_curriculo: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_catalogo: str = Field(pattern=r"^[a-f0-9]{64}$")
    nodos: dict[str, int]
    aristas: dict[str, int]
    sha256: dict[str, str]
    bytes: dict[str, int]
    limites: tuple[str, ...]


class ProductoMaterializado(ContratoCurricular):
    """Hold one verified generation and its stable in-memory graph."""

    ruta_grafo: Path
    manifest: ManifestProducto
    curriculo: Curriculo
    catalogo: CatalogoDisciplinas
    nodos: tuple[Nodo, ...]
    aristas: tuple[Arista, ...]
    diagnostico: dict[str, Any]
    alertas: dict[str, Any]
    publicacion: dict[str, Any]
    conocimiento: ArchivoConocimiento | None
    alineaciones: ArchivoAlineaciones | None = None
    mejoras: ArchivoMejoras | None = None
