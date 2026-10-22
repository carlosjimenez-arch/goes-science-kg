"""Adapt the historical GraphRAG baseline without changing its ranking."""

from __future__ import annotations

import hashlib
import inspect
import json
from collections.abc import Sequence
from pathlib import Path

from goes_science_kg.modelos import Arista, Nodo
from goes_science_kg.rag import GraphRAG
from goes_science_kg.recuperacion.grafo import _cargar_grafo_validado, _convertir
from goes_science_kg.recuperacion.modelos import Resultado


class BuscadorBaseline:
    """Adapt the baseline without merging rankings or changing filters and weights."""

    def __init__(self, nodos: list[Nodo], aristas: list[Arista], *, version: str):
        self._rag = GraphRAG(nodos, aristas)
        self.version = version
        self.documentos = {d.id: d for d in _convertir(nodos, version)}
        identidad = {
            "algoritmo": "graphrag-historico",
            "version_curriculo": version,
            "nodos": [n.model_dump(mode="json") for n in sorted(nodos, key=lambda n: n.id)],
            "aristas": [
                a.model_dump(mode="json")
                for a in sorted(
                    aristas,
                    key=lambda a: (a.origen, a.destino, a.tipo.value, a.rol or ""),
                )
            ],
            "implementacion_sha256": hashlib.sha256(Path(inspect.getfile(GraphRAG)).read_bytes()).hexdigest(),
        }
        self.huella = hashlib.sha256(json.dumps(identidad, sort_keys=True).encode("utf-8")).hexdigest()

    def buscar(
        self,
        consulta: str,
        *,
        version: str | None = None,
        grado: int | None = None,
        asignatura: str | None = None,
        k: int = 10,
        vector_consulta: Sequence[float] | None = None,
        modelo_embeddings: str | None = None,
        saltos_grafo: int = 2,
    ) -> list[Resultado]:
        """Apply the original retrieval algorithm and its configured expansion depth."""
        if version is not None and version != self.version:
            raise ValueError(f"El baseline contiene {self.version}; se solicitó {version}")
        if vector_consulta is not None or modelo_embeddings is not None:
            raise ValueError("El baseline histórico no utiliza embeddings")
        if not 1 <= k <= 100 or not 0 <= saltos_grafo <= 2:
            raise ValueError("Se requiere k entre 1 y 100 y entre cero y dos saltos")
        contexto = self._rag.recuperar(
            consulta,
            grado=grado,
            asignatura=asignatura,
            k_final=k,
            saltos=saltos_grafo,
        )
        return [
            Resultado(
                documento=self.documentos[nodo.id].model_copy(deep=True),
                puntaje=puntaje,
                canales=("baseline",),
            )
            for nodo, puntaje in contexto.nodos
        ]


def cargar_buscador_baseline(
    directorio: str | Path = "data/grafo",
    *,
    version: str | None = None,
) -> BuscadorBaseline:
    """Validate the curriculum version and load baseline nodes and relationships once."""
    nodos, aristas, verificada = _cargar_grafo_validado(directorio, version=version)
    return BuscadorBaseline(nodos, aristas, version=verificada)
