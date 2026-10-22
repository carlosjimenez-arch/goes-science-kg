"""Ingesta curricular verificable; no reemplaza la configuración histórica."""

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.curriculo.ingesta import cargar_curriculo

__all__ = ["Curriculo", "cargar_curriculo"]
