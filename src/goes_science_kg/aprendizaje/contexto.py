"""Alineación curricular y contexto del tutor (spec 13, «Inyección»).

- `alinear()`: identifica el objetivo de la malla (tema) a partir de lo que trae el estudiante o el docente, con el
  GraphRAG del proyecto. Si la ambigüedad es alta, lo dice: el tutor debe preguntar, no adivinar.
- `paquete()`: lo que se inyecta al agente tutor en cada paso. Solo conocimiento compartido citado (objetivo,
  conceptos, bases, fuentes) más la evidencia de ESTE estudiante. La referencia internacional entra como comparación,
  nunca como prerrequisito ni como argumento para agregar contenido.
"""

from __future__ import annotations

import json
from functools import cache

from goes_science_kg.aprendizaje.estudiante import Perfil
from goes_science_kg.aprendizaje.pedagogia import Pedagogia, palabras_max, registro
from goes_science_kg.aprendizaje.relaciones import Navegador
from goes_science_kg.config import ruta
from goes_science_kg.modelos import TipoArista, TipoNodo


def alinear(texto: str, grado: int, nav: Navegador, asignatura: str | None = None, k: int = 3) -> dict:
    """Objetivos candidatos de la malla para un texto libre, en el grado del estudiante."""
    from goes_science_kg.rag import GraphRAG

    ctx = GraphRAG(nav.nodos, nav.aristas).recuperar(texto, grado=grado, asignatura=asignatura)
    temas = [(n, s) for n, s in ctx.nodos if n.tipo == TipoNodo.TEMA and n.grado == grado][:k]
    if not temas:
        return {"objetivo": None, "candidatos": [], "decision": "sin objetivo en el grado: preguntar al docente"}
    ambiguo = len(temas) > 1 and temas[1][1] >= 0.85 * temas[0][1]
    return {"objetivo": temas[0][0].id,
            "candidatos": [{"tema": n.id, "texto": n.etiqueta, "puntaje": round(s, 3)} for n, s in temas],
            "decision": "ambiguo: confirmar con el estudiante o el docente" if ambiguo else "alineado"}


@cache
def _consenso(tramo: str) -> dict[str, dict]:
    p = ruta(f"data/grafo/{'internacional' if tramo == '9_11' else 'internacional_2_8'}/consenso.json")
    return {c["concepto"]: c for c in json.loads(p.read_text(encoding="utf-8"))["conceptos"]} if p.exists() else {}


def referencia_internacional(concepto: str, grado: int) -> str | None:
    """Comparación con el núcleo de los países de alto desempeño (no define prerrequisitos ni agrega contenido)."""
    c = _consenso("9_11" if grado >= 9 else "2_8").get(concepto)
    if not c:
        return None
    paises = c.get("paises", {})
    nucleo = sorted(p for p, d in paises.items() if d.get("primer_grado_nucleo") is not None)
    esp = sorted(p for p, d in paises.items() if d.get("en_especializacion") and d.get("primer_grado_nucleo") is None)
    return (f"{len(nucleo)} países lo tienen en el núcleo ({', '.join(nucleo) or '—'}); {len(esp)} solo en "
            f"especialización ({', '.join(esp) or '—'}). Referencia comparativa: no indica que sea prerrequisito ni "
            "que deba agregarse.")


def fuentes_del_objetivo(nav: Navegador, objetivo: str) -> list[str]:
    """La fila de la malla y los objetivos de marco que el tema cubre, con su documento y página."""
    t = nav.por_id[objetivo]
    f = t.fuente
    citas = [f"malla: {f.documento} hoja «{f.hoja}» fila {f.fila}"] if f else []
    for a in nav.aristas:
        if a.origen == objetivo and a.tipo == TipoArista.CUBRE and a.destino in nav.por_id:
            o = nav.por_id[a.destino]
            fo = o.fuente
            citas.append(f"{o.props.get('marco')} {a.destino.removeprefix('OBJ:')} ({a.rol}): {o.etiqueta[:90]}"
                         + (f" · {fo.documento} p. {fo.pagina}" if fo and fo.pagina else ""))
    return citas


def paquete(perfil: Perfil, nav: Navegador, ped: Pedagogia, objetivo: str, concepto: str | None = None) -> dict:
    """El contexto del agente tutor para un paso: qué enseñar, con qué fuentes y qué sabe de este estudiante."""
    t = nav.por_id[objetivo]
    principal = nav.conceptos_de_tema(objetivo, ("principal",))[0]
    foco = concepto or principal
    mt = ped.es_reforzado_por(foco, perfil.grado)
    propias = [h for h in perfil.hipotesis if h.objetivo == objetivo]
    return {
        "objetivo": {"id": objetivo, "grado": t.grado, "procedimental": t.etiqueta,
                     "indicador": t.props.get("indicador"), "evidencia_de_logro": t.props.get("evidencia")},
        "foco": {"concepto": foco, "nombre": nav.por_id[foco].etiqueta,
                 "definicion": nav.por_id[foco].props.get("definicion"),
                 "microtema": mt["id"] if mt else None, "estado_microtema": mt["estado"] if mt else None},
        "bases": [{"concepto": b.concepto, "nombre": nav.por_id[b.concepto].etiqueta, "profundidad": b.profundidad,
                   "antes_en_la_malla": b.antes_del_objetivo, "confianza": b.confianza,
                   "estado_relacion": b.estado_relacion} for b in nav.bases(objetivo, profundidad=1)],
        "fuentes": fuentes_del_objetivo(nav, objetivo),
        "referencia_internacional": referencia_internacional(principal, t.grado or 0),
        "estudiante": {"grado": perfil.grado,
                       "dominio": {c: round(e.p, 2) for c, e in sorted(perfil.conceptos.items())},
                       "hipotesis": [{"concepto": h.concepto, "tipo": h.tipo, "estado": h.estado} for h in propias]},
        "restricciones": {"palabras_max": palabras_max(perfil.grado), "registro": registro(perfil.grado),
                          "no_revelar_respuesta": True, "citar_fuentes": True,
                          "volver_al_objetivo": "al cumplir el criterio o tocar un límite"},
    }
