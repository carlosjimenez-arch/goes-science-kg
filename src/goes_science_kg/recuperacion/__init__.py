"""Provide traceable local retrieval without implicit cloud-provider calls."""

from goes_science_kg.recuperacion.baseline import BuscadorBaseline, cargar_buscador_baseline
from goes_science_kg.recuperacion.buscador import Buscador
from goes_science_kg.recuperacion.embeddings import IndiceEmbeddings
from goes_science_kg.recuperacion.grafo import (
    aristas_del_grafo,
    cargar_buscador_grafo,
    cargar_documentos_grafo,
    documentos_del_grafo,
)
from goes_science_kg.recuperacion.modelos import Documento, Enlace, Resultado, huella_corpus

__all__ = [
    "Buscador",
    "BuscadorBaseline",
    "Documento",
    "Enlace",
    "IndiceEmbeddings",
    "Resultado",
    "aristas_del_grafo",
    "cargar_buscador_grafo",
    "cargar_buscador_baseline",
    "cargar_documentos_grafo",
    "documentos_del_grafo",
    "huella_corpus",
]
