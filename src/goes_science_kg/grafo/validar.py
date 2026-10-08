"""Invariantes del grafo (specs/07_calidad_y_gobernanza.md).

ERRORES bloquean (la CLI sale con código 1); AVISOS se reportan para revisión humana.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

import networkx as nx

from goes_science_kg.modelos import ARISTAS_INFERIDAS, Arista, Confianza, Nodo, TipoArista, TipoNodo

MAX_PALABRAS_JUSTIFICACION = 15


@dataclass
class Reporte:
    errores: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    metricas: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errores


def validar(nodos: list[Nodo], aristas: list[Arista]) -> Reporte:
    r = Reporte()
    ids = Counter(n.id for n in nodos)
    r.errores += [f"id duplicado: {i}" for i, k in ids.items() if k > 1]
    por_id = {n.id: n for n in nodos}

    for a in aristas:
        for extremo in (a.origen, a.destino):
            if extremo not in por_id:
                r.errores.append(f"{a.tipo} {a.origen}→{a.destino}: no existe {extremo}")
        if a.tipo in ARISTAS_INFERIDAS and a.metodo == "ia" and not (a.confianza and a.justificacion and a.version):
            r.errores.append(f"{a.tipo} {a.origen}→{a.destino}: inferencia sin confianza/justificación/versión")

    for n in nodos:
        if n.tipo == TipoNodo.TEMA and not (n.fuente and n.fuente.hoja and n.fuente.fila):
            r.errores.append(f"{n.id}: tema sin hoja/fila de la malla")
        if n.tipo == TipoNodo.OBJETIVO_PAIS and not (n.fuente and (n.fuente.pagina or n.fuente.localizador)):
            r.errores.append(f"{n.id}: objetivo de país sin página ni localizador")
        if (n.tipo == TipoNodo.OBJETIVO_MARCO and n.props.get("marco") in ("T4_27", "T8_27", "PISA25")
                and not (n.fuente and n.fuente.pagina)):
            r.errores.append(f"{n.id}: objetivo de marco sin página")
        if (n.tipo == TipoNodo.OBJETIVO_MARCO and n.props.get("marco") == "AUSS"
                and not (n.fuente and n.fuente.localizador)):
            r.errores.append(f"{n.id}: objetivo AUSS sin código localizador")


    dag = nx.DiGraph([(a.origen, a.destino) for a in aristas if a.tipo == TipoArista.PRERREQUISITO_DE])
    if not nx.is_directed_acyclic_graph(dag):
        r.errores.append(f"PRERREQUISITO_DE tiene ciclos, p. ej. {nx.find_cycle(dag)[:4]}")

    # Avisos: lo que la revisión humana o las fases siguientes deben resolver.
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA]
    sin_asig = [n.id for n in temas if not n.asignatura and not n.props.get("fuera_de_alcance")]
    if sin_asig:
        r.avisos.append(f"{len(sin_asig)} temas sin asignatura (skill grafo-asignar-disciplina)")
    largas = [a for a in aristas if a.justificacion and len(a.justificacion.split()) > MAX_PALABRAS_JUSTIFICACION]
    if largas:
        r.avisos.append(f"{len(largas)} justificaciones con más de {MAX_PALABRAS_JUSTIFICACION} palabras")
    bajas = [a for a in aristas if a.confianza == Confianza.BAJA]
    r.avisos.append(f"{len(bajas)} aristas con confianza baja pendientes de revisión humana")

    cubiertos = {a.destino for a in aristas if a.tipo == TipoArista.CUBRE}
    r.metricas = {
        "temas": len(temas),
        "temas_sin_asignatura": len(sin_asig),
        "temas_con_cobertura": len({a.origen for a in aristas if a.tipo == TipoArista.CUBRE}),
        "objetivos_marco": sum(n.tipo == TipoNodo.OBJETIVO_MARCO for n in nodos),
        "objetivos_marco_cubiertos": len(cubiertos),
        "objetivos_pais": sum(n.tipo == TipoNodo.OBJETIVO_PAIS for n in nodos),
        "aristas_confianza_baja": len(bajas),
    }
    return r
