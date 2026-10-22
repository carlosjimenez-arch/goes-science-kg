"""Ingest verifiable curricula independently of historical pipeline configuration."""

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.curriculo.ingesta import cargar_curriculo

__all__ = ["Curriculo", "cargar_curriculo"]
