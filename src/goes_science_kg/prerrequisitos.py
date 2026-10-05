"""Prerrequisitos entre conceptos: un DAG por asignatura (skill grafo-prerrequisitos).

Evidencia que se le entrega al subagente (calculada aquí, de forma determinista):
- primer grado en que El Salvador trabaja el concepto (temas → TRABAJA → concepto);
- primer grado en que lo trabaja cada país de referencia: DIRECTO si los objetivos de país están etiquetados
  con conceptos (objetivo de país → TRABAJA → concepto); si no, VÍA EL PIVOTE
  (objetivo de país → ALINEA_CON → objetivo de marco → TRABAJA → concepto), que es más grueso;
- nivel del marco que lo pide (TIMSS 4.° = 4, TIMSS 8.° = 8, PISA = 9, ACARA Senior / TIMSS Advanced = 11).

El subagente propone aristas A → B («A es prerrequisito de B») con tipo de evidencia
(declarada | orden_observado | logica), confianza y justificación. `unir()` valida, rompe ciclos quitando
la arista de menor confianza y elimina redundancias transitivas que no tengan evidencia declarada.
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict

import networkx as nx

from goes_science_kg.config import cargar, ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo

DIR = "data/interim/prerrequisitos"
VERSION = "prerrequisitos-v1"
def paises_alto_desempeno(tope: int = 10) -> set[str]:
    """Países entre los `tope` primeros de TIMSS 2023 Ciencias en 4.° u 8.° (evidencia en config/referentes.yaml)."""
    out = set()
    for cod, p in cargar("referentes")["paises"].items():
        t = p.get("timss2023_ciencias") or {}
        if any((t.get(g) or {}).get("puesto", 99) <= tope for g in ("g4", "g8")):
            out.add(cod)
    return out


NIVEL_MARCO = {"T4_27": 4, "T8_27": 8, "PISA25": 9, "TA15": 11, "AUSS": 11}
PESO = {"alta": 3, "media": 2, "baja": 1}
TIPOS = {"declarada", "orden_observado", "logica"}


def evidencia_orden(nodos: list[Nodo], aristas: list[Arista]) -> dict[str, dict]:
    """Por concepto: primer grado SV, primer grado por país (vía pivote) y nivel mínimo de marco."""
    por_id = {n.id: n for n in nodos}
    obj_a_con, tema_a_con, op_a_con = defaultdict(set), defaultdict(set), defaultdict(set)
    for a in aristas:
        if a.tipo == TipoArista.TRABAJA and a.destino.startswith("CON:"):
            destino = {"OBJ": obj_a_con, "TEMA": tema_a_con, "OP": op_a_con}[a.origen.split(":")[0]]
            destino[a.origen].add(a.destino)
    ev: dict[str, dict] = {n.id: {"sv": None, "paises": {}, "marco": None}
                           for n in nodos if n.tipo == TipoNodo.CONCEPTO}

    def _min(actual, nuevo):
        return nuevo if actual is None else min(actual, nuevo)

    # Primer grado SV: temas donde el concepto es PRINCIPAL, o secundario con confianza alta o media (una mención
    # secundaria de confianza baja no es «enseñarlo»); si no hay ninguna, el primer grado como secundario.
    for a in aristas:
        if a.tipo == TipoArista.TRABAJA and a.origen.startswith("TEMA:") and a.destino in ev:
            g = por_id[a.origen].grado
            fuerte = a.rol == "principal" or (a.confianza is not None and a.confianza.value in ("alta", "media"))
            clave = "sv" if fuerte else "sv_secundario"
            ev[a.destino][clave] = _min(ev[a.destino].get(clave), g)
    for e in ev.values():
        if e["sv"] is None and e.get("sv_secundario") is not None:
            e["sv"], e["sv_solo_secundario"] = e["sv_secundario"], True
    for oid, cons in obj_a_con.items():
        nivel = NIVEL_MARCO.get(por_id[oid].props.get("marco"))
        for c in cons:
            if nivel:
                ev[c]["marco"] = _min(ev[c]["marco"], nivel)
    def _pais(op_id: str, cons) -> None:
        op = por_id[op_id]
        # Objetivos por banda (KS3 de Inglaterra, Estándares de Colombia): el punto medio de la banda, no el mínimo,
        # para no atribuir al primer año de la banda todo lo que se enseña a lo largo de ella.
        gmin = op.props.get("grado_min") or 2
        gmax = op.props.get("grado_max") or gmin
        pais, g = op.props.get("pais"), max(2, (gmin + gmax) / 2)
        for c in cons:
            ev[c]["paises"][pais] = _min(ev[c]["paises"].get(pais), g)

    if op_a_con:
        for op_id, cons in op_a_con.items():
            _pais(op_id, cons)
    else:
        for a in aristas:
            if a.tipo == TipoArista.ALINEA_CON and a.destino in obj_a_con:
                _pais(a.origen, obj_a_con[a.destino])
    # Conceptos equivalentes entre asignaturas comparten el primer grado (SV y países).
    eq = nx.Graph([(a.origen, a.destino) for a in aristas
                   if a.tipo == TipoArista.EQUIVALE_A and a.origen in ev and a.destino in ev])
    for grupo in nx.connected_components(eq):
        svs = [ev[c]["sv"] for c in grupo if ev[c]["sv"] is not None]
        paises: dict[str, int] = {}
        for c in grupo:
            for p, g in ev[c]["paises"].items():
                paises[p] = min(g, paises.get(p, g))
        for c in grupo:
            ev[c]["sv"] = min(svs) if svs else None
            ev[c]["paises"] = dict(paises)
            ev[c]["equivalentes"] = sorted(grupo - {c})
    alto = paises_alto_desempeno()
    for e in ev.values():
        alto_g = [g for p, g in e["paises"].items() if p in alto]
        e["mediana_alto_desempeno"] = statistics.median(alto_g) if alto_g else None
        e["via_paises"] = "directo" if op_a_con else "pivote"
        e["paises_mediana"] = statistics.median(e["paises"].values()) if e["paises"] else None
    return ev


def preparar(nodos: list[Nodo], aristas: list[Arista]) -> list[str]:
    ev = evidencia_orden(nodos, aristas)
    conceptos = [n for n in nodos if n.tipo == TipoNodo.CONCEPTO]
    d = ruta(f"{DIR}/lotes")
    d.mkdir(parents=True, exist_ok=True)
    escritos = []
    for asig in cargar("asignaturas")["asignaturas"]:
        lote = {
            "lote": asig, "version": VERSION, "instrucciones": "prompts/prerrequisitos.md",
            "conceptos": [{"id": c.id, "nombre": c.etiqueta, "definicion": c.props.get("definicion"),
                           "nivel": c.props.get("nivel"), **ev[c.id]}
                          for c in sorted(conceptos, key=lambda x: x.id) if c.asignatura == asig],
            "otras_asignaturas": [{"id": c.id, "nombre": c.etiqueta} for c in conceptos if c.asignatura != asig],
        }
        p = d / f"lote_{asig}.json"
        p.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
        escritos.append(str(p.relative_to(ruta("."))))
    return escritos


def unir(nodos: list[Nodo]) -> dict:
    ids = {n.id for n in nodos if n.tipo == TipoNodo.CONCEPTO}
    candidatas, errores = [], []
    for p in sorted(ruta(f"{DIR}/lotes").glob("salida_*.json")):
        for e in json.loads(p.read_text(encoding="utf-8")):
            if e["origen"] not in ids or e["destino"] not in ids or e["origen"] == e["destino"]:
                errores.append(f"{p.name}: arista inválida {e['origen']} → {e['destino']}")
            elif e.get("tipo_evidencia") not in TIPOS or e.get("confianza") not in PESO:
                errores.append(f"{p.name}: tipo/confianza inválidos en {e['origen']} → {e['destino']}")
            else:
                candidatas.append(e)
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))

    g = nx.DiGraph()
    for e in candidatas:
        if not g.has_edge(e["origen"], e["destino"]) or PESO[e["confianza"]] > g[e["origen"]][e["destino"]]["peso"]:
            g.add_edge(e["origen"], e["destino"], peso=PESO[e["confianza"]], dato=e)
    rotas = []
    while True:
        try:
            ciclo = nx.find_cycle(g)
        except nx.NetworkXNoCycle:
            break
        u, v = min(ciclo, key=lambda uv: (g[uv[0]][uv[1]]["peso"], uv))[:2]
        rotas.append(g[u][v]["dato"])
        g.remove_edge(u, v)
    reducido = nx.transitive_reduction(g)
    redundantes = [g[u][v]["dato"] for u, v in g.edges if not reducido.has_edge(u, v)
                   and g[u][v]["dato"]["tipo_evidencia"] != "declarada"]
    for e in redundantes:
        g.remove_edge(e["origen"], e["destino"])
    final = sorted((g[u][v]["dato"] | {"version": VERSION} for u, v in g.edges),
                   key=lambda e: (e["origen"], e["destino"]))
    for nombre, datos in (("prerrequisitos.json", final), ("descartadas_ciclo.json", rotas),
                          ("descartadas_transitivas.json", redundantes)):
        (ruta(DIR) / nombre).write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"aristas": len(final), "rotas_por_ciclo": len(rotas), "transitivas_quitadas": len(redundantes),
            "cadena_mas_larga": len(nx.dag_longest_path(g))}


def cargar_prerrequisitos() -> list[dict]:
    """Prerrequisitos consolidados menos los que rechazó la revisión humana."""
    p = ruta(f"{DIR}/prerrequisitos.json")
    if not p.exists():
        return []
    r = ruta(f"{DIR}/rechazados.json")
    rechazados = ({(x["origen"], x["destino"]) for x in json.loads(r.read_text(encoding="utf-8"))}
                  if r.exists() else set())
    from goes_science_kg.conceptos import VERSION_TRIAJE, conceptos_del_triaje, vocabulario

    aristas = json.loads(p.read_text(encoding="utf-8"))
    # Conceptos nuevos del triaje: sus prerrequisitos sugeridos entran como evidencia lógica de confianza media.
    # Solo llegan aristas hacia el concepto nuevo, así que no pueden crear ciclos.
    # Hoy los conceptos del triaje no tienen aristas salientes, pero un próximo `unir` podría dárselas: se descarta
    # toda arista del triaje que repita un par o cierre un ciclo.
    import networkx as nx

    voc = vocabulario()
    g = nx.DiGraph((e["origen"], e["destino"]) for e in aristas if (e["origen"], e["destino"]) not in rechazados)
    for c in conceptos_del_triaje():
        for o in c["prerrequisitos_sugeridos"]:
            d = c["id"]
            if o not in voc or g.has_edge(o, d) or (d in g and o in g and nx.has_path(g, d, o)):
                continue
            g.add_edge(o, d)
            aristas.append({"origen": o, "destino": d, "tipo_evidencia": "logica", "evidencias": ["triaje"],
                            "confianza": "media", "version": VERSION_TRIAJE,
                            "justificacion": "Prerrequisito sugerido al incorporar el concepto (triaje)."})
    return [e for e in aristas if (e["origen"], e["destino"]) not in rechazados]
