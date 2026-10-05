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

import networkx as nx

from goes_science_kg.config import ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo

SEMILLA = 42
RESUMENES = "data/interim/comunidades/resumenes.json"


@cache
def resumenes() -> dict[str, dict]:
    """Títulos y resúmenes redactados por un especialista, ligados al conjunto exacto de conceptos del bloque."""
    p = ruta(RESUMENES)
    return {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def consolidar_resumenes() -> dict:
    """Une salida_*.json (subagentes) con los conceptos actuales de cada comunidad → resumenes.json."""
    actuales = {}
    for p in sorted(ruta("data/grafo/grados").glob("G*/comunidades.json")):
        for c in json.loads(p.read_text(encoding="utf-8")):
            actuales[c["id"]] = c
    filas = []
    for p in sorted(ruta("data/interim/comunidades").glob("salida_*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            if r["id"] in actuales:
                filas.append({"id": r["id"], "conceptos": sorted(actuales[r["id"]]["conceptos"]),
                              "titulo": r["titulo"], "resumen_ia": r["resumen"], "version": "comunidades-v1"})
    ruta(RESUMENES).write_text(json.dumps(sorted(filas, key=lambda f: f["id"]), ensure_ascii=False, indent=1) + "\n",
                               encoding="utf-8")
    resumenes.cache_clear()
    return {"resumenes": len(filas)}


def comunidades_grado(g: int, nodos: list[Nodo], aristas: list[Arista]) -> list[dict]:
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
        asignaturas = Counter(por_id[c].asignatura for c in miembros)
        objetivos = Counter(o for t in temas_c for o in cubre_de_tema[t])
        cid = f"COM:G{g:02d}-{i + 1:02d}"
        r = resumenes().get(cid)
        vigente = r is not None and r["conceptos"] == sorted(miembros)
        resultado.append({
            "id": cid,
            "titulo": r["titulo"] if vigente else None,
            "resumen_ia": r["resumen_ia"] if vigente else None,
            "grado": g,
            "nombre": " · ".join(por_id[c].etiqueta for c in centrales[:3]),
            "conceptos": centrales,
            "temas": temas_c,
            "asignaturas": dict(asignaturas.most_common()),
            "unidades": [u for u, _ in unidades.most_common(5)],
            "objetivos_marco": [o.removeprefix("OBJ:") for o, _ in objetivos.most_common(8)],
            "resumen": (f"{len(miembros)} conceptos y {len(temas_c)} temas; centro en "
                        + ", ".join(por_id[c].etiqueta for c in centrales[:5])
                        + ". Unidades: " + "; ".join(u for u, _ in unidades.most_common(3) if u) + "."),
        })
    return resultado
