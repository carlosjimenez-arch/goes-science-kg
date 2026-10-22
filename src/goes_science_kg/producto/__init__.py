"""Materialize V4 publications independently of the historical graph configuration."""

from goes_science_kg.producto.almacen import cargar_producto
from goes_science_kg.producto.construccion import construir_producto
from goes_science_kg.producto.contratos import (
    AlertaSolicitada,
    ManifestProducto,
    ProductoMaterializado,
    ReferenciasProducto,
)

__all__ = [
    "AlertaSolicitada",
    "ManifestProducto",
    "ProductoMaterializado",
    "ReferenciasProducto",
    "cargar_producto",
    "construir_producto",
]
