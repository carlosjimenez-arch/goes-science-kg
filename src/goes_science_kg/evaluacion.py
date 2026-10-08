"""Evaluación de la recuperación de GraphRAG (spec 10, «Evaluación»).

Conjunto: data/evaluacion/rag_preguntas.json. Cada pregunta trae grado/asignatura opcionales y la lista de
nodos `relevantes` (ids del grafo) que una buena recuperación debería traer. Es un conjunto «plata»: lo redactó
un especialista (subagente) mirando el grafo; debe revisarlo el equipo de Ciencias para volverlo «oro».

Métricas por pregunta y promedio: recall@k (fracción de relevantes en los k primeros), acierto@k (al menos uno)
y MRR (rango recíproco del primer relevante).
"""

from __future__ import annotations

import json
from statistics import mean

from goes_science_kg.config import ruta
from goes_science_kg.rag import GraphRAG

CONJUNTO = "data/evaluacion/rag_preguntas.json"


def evaluar(rag: GraphRAG, ks: tuple[int, ...] = (5, 10, 25), conjunto: str = CONJUNTO) -> dict:
    """Mide la recuperación de `rag` sobre `conjunto`: promedios de recall@k, acierto@k y MRR, desglose por tipo
    de pregunta (recall@10 y MRR) y las cinco peores preguntas.
    """
    preguntas = json.loads(ruta(conjunto).read_text(encoding="utf-8"))
    filas = []
    for p in preguntas:
        ctx = rag.recuperar(p["pregunta"], grado=p.get("grado"), asignatura=p.get("asignatura"), k_final=max(ks))
        orden = [n.id for n, _ in ctx.nodos]
        rel = set(p["relevantes"])
        primero = next((i for i, n in enumerate(orden, 1) if n in rel), None)
        fila = {"id": p["id"], "tipo": p.get("tipo"), "mrr": 1 / primero if primero else 0.0}
        for k in ks:
            hits = len(rel & set(orden[:k]))
            fila[f"recall@{k}"] = hits / len(rel)
            fila[f"acierto@{k}"] = float(hits > 0)
        filas.append(fila)
    metricas = {m: round(mean(f[m] for f in filas), 3) for m in filas[0] if m not in ("id", "tipo")}
    por_tipo = {}
    for t in sorted({f["tipo"] for f in filas if f["tipo"]}):
        sub = [f for f in filas if f["tipo"] == t]
        por_tipo[t] = {"n": len(sub), "recall@10": round(mean(f["recall@10"] for f in sub), 3),
                       "mrr": round(mean(f["mrr"] for f in sub), 3)}
    return {"preguntas": len(filas), **metricas, "por_tipo": por_tipo,
            "peores": sorted(filas, key=lambda f: (f["recall@10"], f["mrr"]))[:5]}
