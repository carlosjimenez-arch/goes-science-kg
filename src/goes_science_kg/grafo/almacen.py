"""Almacenamiento del grafo en archivos (fuente de verdad versionable en git).

data/grafo/nodos.jsonl      un nodo por línea, ordenado por (tipo, id)
data/grafo/aristas.jsonl    una arista por línea, ordenada por (tipo, origen, destino, rol)
data/grafo/manifest.json    versión, conteos por tipo y SHA-256 de cada archivo

Neo4j u otro motor es una proyección opcional de estos archivos (specs/01_arquitectura.md).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import networkx as nx

from goes_science_kg.config import DIR_GRAFO, ruta
from goes_science_kg.modelos import Arista, Nodo


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def guardar(nodos: list[Nodo], aristas: list[Arista], version: str, directorio: str = DIR_GRAFO) -> dict:
    """Escribe nodos.jsonl y aristas.jsonl (en el orden recibido) y manifest.json en `directorio`. Devuelve el
    manifiesto."""
    d = ruta(directorio)
    d.mkdir(parents=True, exist_ok=True)
    for nombre, filas in (("nodos.jsonl", nodos), ("aristas.jsonl", aristas)):
        with open(d / nombre, "w", encoding="utf-8") as f:
            for x in filas:
                f.write(json.dumps(x.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
                                   ensure_ascii=False, sort_keys=True) + "\n")
    manifest = {
        "version": version,
        "nodos": dict(sorted(Counter(n.tipo.value for n in nodos).items())),
        "aristas": dict(sorted(Counter(a.tipo.value for a in aristas).items())),
        "sha256": {n: _sha(d / n) for n in ("nodos.jsonl", "aristas.jsonl")},
    }
    (d / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def cargar(directorio: str = DIR_GRAFO) -> tuple[list[Nodo], list[Arista]]:
    """Lee los nodos y las aristas guardados en `directorio`."""
    d = ruta(directorio)
    with open(d / "nodos.jsonl", encoding="utf-8") as f:
        nodos = [Nodo.model_validate_json(linea) for linea in f]
    with open(d / "aristas.jsonl", encoding="utf-8") as f:
        aristas = [Arista.model_validate_json(linea) for linea in f]
    return nodos, aristas


def a_networkx(nodos: list[Nodo], aristas: list[Arista]) -> nx.MultiDiGraph:
    """Proyección a un MultiDiGraph de networkx; la clave de cada arista es «tipo:rol»."""
    g = nx.MultiDiGraph()
    for n in nodos:
        g.add_node(n.id, **n.model_dump(mode="json", exclude={"id"}))
    for a in aristas:
        g.add_edge(a.origen, a.destino, key=f"{a.tipo}:{a.rol or ''}", **a.model_dump(mode="json"))
    return g
