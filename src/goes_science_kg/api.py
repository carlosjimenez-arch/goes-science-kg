"""API de lectura (FastAPI) sobre el grafo: grados, conceptos, propuestas y GraphRAG.

Solo lectura. Sirve lo que ya está en data/grafo/ y asignaturas/; no escribe nada. Arranque:
    uv sync --extra api && uv run gskg servir --puerto 8010
Documentación interactiva en /docs.
"""

from __future__ import annotations

import json
from functools import cache

from fastapi import FastAPI, HTTPException, Query

from goes_science_kg.config import cargar, ruta
from goes_science_kg.grafo.almacen import cargar as cargar_grafo
from goes_science_kg.modelos import TipoArista, TipoNodo
from goes_science_kg.rag import GraphRAG, busqueda_global

app = FastAPI(title="goes-science-kg", description="Grafo de conocimiento de Ciencias · El Salvador (solo lectura)",
              version="1.0")


@cache
def _grafo():
    nodos, aristas = cargar_grafo()
    return {n.id: n for n in nodos}, aristas, GraphRAG(nodos, aristas)


def _json(rel: str):
    p = ruta(rel)
    if not p.exists():
        raise HTTPException(404, f"No existe {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/api/salud")
def salud() -> dict:
    return {"estado": "ok", "manifest": _json("data/grafo/manifest.json")}


@app.get("/api/grados")
def grados() -> list[dict]:
    """Resumen de los grafos por grado."""
    salida = []
    for g in range(2, 12):
        d = _json(f"data/grafo/grados/G{g:02d}/diagnostico.json")
        salida.append({k: d[k] for k in ("grado", "temas", "temas_por_asignatura", "conceptos", "conceptos_nuevos",
                                         "conceptos_retomados", "referentes_paises")}
                      | {"prerrequisitos_tarde": sum(a["estado"] in ("ausente", "posterior") for a in d["anclajes"]),
                         "faltantes_por_edad": len(d["faltantes_por_edad"])})
    return salida


@app.get("/api/grados/{grado}")
def grado(grado: int) -> dict:
    """Diagnóstico completo y bloques temáticos de un grado."""
    if not 2 <= grado <= 11:
        raise HTTPException(404, "Grado fuera de 2–11")
    return {"diagnostico": _json(f"data/grafo/grados/G{grado:02d}/diagnostico.json"),
            "bloques": _json(f"data/grafo/grados/G{grado:02d}/comunidades.json")}


@app.get("/api/conceptos/{asignatura}/{slug}")
def concepto(asignatura: str, slug: str) -> dict:
    """Un concepto con sus prerrequisitos, los conceptos que habilita y los temas que lo trabajan."""
    por_id, aristas, _ = _grafo()
    cid = f"CON:{asignatura}/{slug}"
    if cid not in por_id:
        raise HTTPException(404, f"No existe {cid}")
    n = por_id[cid]

    def etiqueta(i: str) -> dict:
        x = por_id[i]
        return {"id": i, "etiqueta": x.etiqueta, "grado": x.grado, "asignatura": x.asignatura}

    return {"id": cid, "nombre": n.etiqueta, "definicion": n.props.get("definicion"),
            "prerrequisitos": [etiqueta(a.origen) for a in aristas
                               if a.tipo == TipoArista.PRERREQUISITO_DE and a.destino == cid],
            "habilita": [etiqueta(a.destino) for a in aristas
                         if a.tipo == TipoArista.PRERREQUISITO_DE and a.origen == cid],
            "temas_sv": sorted((etiqueta(a.origen) for a in aristas if a.tipo == TipoArista.TRABAJA
                                and a.destino == cid and por_id[a.origen].tipo == TipoNodo.TEMA),
                               key=lambda t: (t["grado"] or 0, t["id"])),
            "objetivos_paises": [etiqueta(a.origen) for a in aristas if a.tipo == TipoArista.TRABAJA
                                 and a.destino == cid and por_id[a.origen].tipo == TipoNodo.OBJETIVO_PAIS]}


@app.get("/api/propuestas")
def propuestas() -> list[dict]:
    """Simulación (antes/después) de cada propuesta curricular en borrador."""
    salida = []
    for p in sorted(ruta("asignaturas").glob("*/propuesta/simulacion_G*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        salida.append({"asignatura": p.parent.parent.name, "ciclo": p.stem.removeprefix("simulacion_"),
                       "antes": s["antes"], "despues": s["despues"]})
    return salida


@app.get("/api/rag")
def rag(q: str = Query(..., min_length=3), grado: int | None = None, asignatura: str | None = None,
        k: int = Query(20, ge=1, le=60)) -> dict:
    """GraphRAG local: evidencia citable del grafo para una pregunta (sin generación)."""
    if asignatura and asignatura not in cargar("asignaturas")["asignaturas"]:
        raise HTTPException(422, "Asignatura desconocida")
    ctx = _grafo()[2].recuperar(q, grado=grado, asignatura=asignatura, k_final=k)
    return {"consulta": q, "grado": grado, "asignatura": asignatura,
            "nodos": [{"id": n.id, "tipo": n.tipo.value, "etiqueta": n.etiqueta, "grado": n.grado,
                       "asignatura": n.asignatura, "puntaje": round(s, 4),
                       "fuente": n.fuente.model_dump(exclude_none=True) if n.fuente else None}
                      for n, s in ctx.nodos],
            "relaciones": [{"origen": a.origen, "tipo": a.tipo.value, "rol": a.rol, "destino": a.destino}
                           for a in ctx.relaciones]}


@app.get("/api/rag/global")
def rag_global(q: str = Query(..., min_length=3), grado: int = Query(..., ge=2, le=11)) -> list[dict]:
    """Búsqueda global: bloques temáticos del grado más pertinentes."""
    return busqueda_global(q, grado)
