from goes_science_kg.evaluacion import evaluar
from goes_science_kg.rag import GraphRAG


def test_recuperacion_no_retrocede(grafo):
    """Umbral de regresión: la v3 del recuperador da MRR 0,81 y recall@25 0,86 (data/evaluacion/resultados.md)."""
    r = evaluar(GraphRAG(*grafo))
    assert r["mrr"] >= 0.75
    assert r["recall@25"] >= 0.80
    assert r["acierto@10"] >= 0.95
