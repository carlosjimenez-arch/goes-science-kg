"""Contratos de publicación del producto; sus estados no equivalen a aprobación oficial."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import ContratoCurricular, Curriculo
from goes_science_kg.modelos import Arista, Nodo
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento


class ReferenciasProducto(ContratoCurricular):
    """Referencias proporcionadas explícitamente; nunca contienen temas nuevos por herencia."""

    nodos: tuple[Nodo, ...] = ()
    aristas: tuple[Arista, ...] = ()
    procedencia: dict[str, Any] = Field(default_factory=dict)


class AlertaSolicitada(ContratoCurricular):
    """Observación pendiente: los localizadores y valores se verifican al materializar."""

    fila_id: str
    campo: str
    codigo: str = Field(min_length=1)
    descripcion: str = Field(min_length=5)


class ManifestProducto(ContratoCurricular):
    """El formato de publicación y la versión curricular son dimensiones separadas."""

    version: Literal["producto-2", "producto-3"] = "producto-2"
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
    """Una sola generación verificada, en memoria y con ruta estable del grafo."""

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
