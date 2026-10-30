from goes_science_kg.evaluacion import evaluar
from goes_science_kg.rag import GraphRAG


def test_recuperacion_no_retrocede(grafo):
    """Keep retrieval above the documented historical regression thresholds."""
    r = evaluar(GraphRAG(*grafo))
    assert r["mrr"] >= 0.75
    assert r["recall@25"] >= 0.80
    assert r["acierto@10"] >= 0.95
