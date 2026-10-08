"""Comunidades de conceptos por grado (capa «global» de GraphRAG; spec 10).

Para cada grado se arma un grafo concepto–concepto:
- peso += 1 por cada tema del grado que trabaja ambos conceptos (co-ocurrencia);
- peso += 1 si hay una arista PRERREQUISITO_DE entre ellos.
Se detectan comunidades con Louvain (semilla fija → resultado reproducible). Cada comunidad es un
«bloque temático» del grado; su resumen determinista (conceptos centrales, unidades, asignaturas, objetivos
de marco) sirve para la búsqueda global y para la ficha del grado. Un resumen redactado con Claude puede
agregarse después sin cambiar la estructura (campo `resumen_ia`).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from functools import cache
from itertools import combinations
from typing import TYPE_CHECKING

import networkx as nx

from goes_science_kg.config import ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo

if TYPE_CHECKING:
    from collections.abc import Iterable

SEMILLA = 42
UMBRAL_JACCARD = 0.75  # un resumen sigue vigente si el bloque conserva ≥75 % de sus conceptos


def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    a, b = set(a), set(b)
    return len(a & b) / max(1, len(a | b))
RESUMENES = "data/interim/comunidades/resumenes.json"


@cache
def resumenes() -> dict[str, dict]:
    """Títulos y resúmenes redactados por un especialista, ligados al conjunto exacto de conceptos del bloque."""
    p = ruta(RESUMENES)
    return {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def resumen_para(g: int, miembros: Iterable[str]) -> dict | None:
    """El resumen del grado cuyo bloque original más se parece a este (Jaccard ≥ umbral).

    Louvain puede renumerar los bloques al cambiar el grafo; por eso se empareja por conceptos y no por id.
    Con un umbral mayor que 0,5, dos bloques disjuntos nunca reclaman el mismo resumen.
    """
    pref = f"COM:G{g:02d}-"
    candidatos = [(_jaccard(r["conceptos"], miembros), i) for i, r in resumenes().items() if i.startswith(pref)]
    j, i = max(candidatos, key=lambda x: (x[0], x[1]), default=(0, None))
    return resumenes()[i] if j >= UMBRAL_JACCARD else None


def consolidar_resumenes() -> dict:
    """Une resúmenes vigentes y salidas nuevas de subagentes → resumenes.json.

    Un resumen solo se acepta si los conceptos del bloque para el que se escribió (lote_*.json, por nombre) son
    exactamente los del bloque actual con ese id; así un id reutilizado tras reconstruir no hereda un texto ajeno.
    """
    actuales = {}
    for p in sorted(ruta("data/grafo/grados").glob("G*/comunidades.json")):
        for c in json.loads(p.read_text(encoding="utf-8")):
            actuales[c["id"]] = c
    nombres = {}
    for p in ruta("data/grafo/grados").glob("G*/nodos.jsonl"):
        for linea in p.read_text(encoding="utf-8").splitlines():
            n = json.loads(linea)
            nombres[n["id"]] = n["etiqueta"]
    vigentes = {}
    for i, c in actuales.items():
        if r := resumen_para(c["grado"], c["conceptos"]):
            # Se conserva el conjunto para el que se escribió el resumen: si se reemplazara por el actual, el texto
            # podría derivar de reconstrucción en reconstrucción hasta describir otro bloque.
            vigentes[i] = {**r, "id": i}
    d = ruta("data/interim/comunidades")
    for p in sorted(d.glob("salida_*.json")):
        lote = {b["id"]: b for b in json.loads((d / p.name.replace("salida_", "lote_", 1)).read_text(encoding="utf-8"))}
        for r in json.loads(p.read_text(encoding="utf-8")):
            c = actuales.get(r["id"])
            actuales_nombres = [nombres.get(x, x) for x in c["conceptos"]] if c else []
            if c and _jaccard(lote[r["id"]]["conceptos"], actuales_nombres) >= UMBRAL_JACCARD:
                vigentes[r["id"]] = {"id": r["id"], "conceptos": sorted(c["conceptos"]), "titulo": r["titulo"],
                                     "resumen_ia": r["resumen"], "version": "comunidades-v1"}
    ruta(RESUMENES).write_text(json.dumps(sorted(vigentes.values(), key=lambda f: f["id"]), ensure_ascii=False,
                                          indent=1) + "\n", encoding="utf-8")
    resumenes.cache_clear()
    sin = [i for i, c in actuales.items() if len(c["conceptos"]) >= 2 and i not in vigentes]
    return {"resumenes_vigentes": len(vigentes), "bloques_sin_resumen": len(sin)}


def comunidades_grado(g: int, nodos: list[Nodo], aristas: list[Arista]) -> list[dict]:
    """Bloques temáticos del grado `g`: comunidades Louvain del grafo concepto–concepto, de mayor a menor, con su
    resumen determinista y, si sigue vigente, el título y el resumen del especialista."""
    por_id = {n.id: n for n in nodos}
    temas = {n.id for n in nodos if n.tipo == TipoNodo.TEMA and n.grado == g and n.asignatura}
    conceptos_de_tema, cubre_de_tema = defaultdict(list), defaultdict(set)
    for a in aristas:
        if a.origen in temas:
            if a.tipo == TipoArista.TRABAJA and a.destino.startswith("CON:"):
                conceptos_de_tema[a.origen].append(a.destino)
            elif a.tipo == TipoArista.CUBRE:
                cubre_de_tema[a.origen].add(a.destino)
    gr = nx.Graph()
    for cons in conceptos_de_tema.values():
        gr.add_nodes_from(cons)
        for u, v in combinations(sorted(set(cons)), 2):
            gr.add_edge(u, v, weight=gr.get_edge_data(u, v, {"weight": 0})["weight"] + 1)
    for a in aristas:
        if a.tipo == TipoArista.PRERREQUISITO_DE and a.origen in gr and a.destino in gr:
            gr.add_edge(a.origen, a.destino, weight=gr.get_edge_data(a.origen, a.destino, {"weight": 0})["weight"] + 1)
    if gr.number_of_nodes() == 0:
        return []
    grupos = nx.community.louvain_communities(gr, weight="weight", seed=SEMILLA)
    resultado = []
    for i, miembros in enumerate(sorted(grupos, key=lambda m: (-len(m), sorted(m)[0]))):
        sub = gr.subgraph(miembros)
        centrales = sorted(miembros, key=lambda c: (-sub.degree(c, weight="weight"), c))
        temas_c = sorted(t for t, cons in conceptos_de_tema.items() if set(cons) & miembros)
        unidades = Counter(por_id[t].props.get("unidad") for t in temas_c)
        asignaturas = Counter(por_id[c].asignatura for c in sorted(miembros))
        objetivos = Counter(o for t in temas_c for o in sorted(cubre_de_tema[t]))

        def top(cnt: Counter, n: int) -> list:  # empates resueltos por clave: salida independiente del hash
            return [k for k, _ in sorted(cnt.items(), key=lambda x: (-x[1], str(x[0])))[:n]]

        cid = f"COM:G{g:02d}-{i + 1:02d}"
        r = resumen_para(g, miembros)
        vigente = r is not None
        resultado.append({
            "id": cid,
            "titulo": r["titulo"] if vigente else None,
            "resumen_ia": r["resumen_ia"] if vigente else None,
            "grado": g,
            "nombre": " · ".join(por_id[c].etiqueta for c in centrales[:3]),
            "conceptos": centrales,
            "temas": temas_c,
            "asignaturas": {k: asignaturas[k] for k in top(asignaturas, 99)},
            "unidades": top(unidades, 5),
            "objetivos_marco": [o.removeprefix("OBJ:") for o in top(objetivos, 8)],
            "resumen": (f"{len(miembros)} conceptos y {len(temas_c)} temas; centro en "
                        + ", ".join(por_id[c].etiqueta for c in centrales[:5])
                        + ". Unidades: " + "; ".join(u for u in top(unidades, 3) if u) + "."),
        })
    return resultado
