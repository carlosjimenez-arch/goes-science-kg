"""Genera asignaturas/<asignatura>/ficha.md: el estado de cada asignatura según el grafo.

La ficha es un ARCHIVO GENERADO (no editar a mano); el README.md de cada carpeta es el
documento escrito por el equipo.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo


def _tabla(encabezado: list[str], filas: list[list]) -> str:
    out = ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado)]
    out += ["| " + " | ".join(str(c) for c in f) + " |" for f in filas]
    return "\n".join(out)


def ficha(asig: str, nodos: list[Nodo], aristas: list[Arista], version: str) -> str:
    a_cfg = cargar("asignaturas")["asignaturas"][asig]
    por_id = {n.id: n for n in nodos}
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura == asig]
    objetivos = [n for n in nodos if n.tipo == TipoNodo.OBJETIVO_MARCO and n.asignatura == asig
                 and n.props.get("marco") != "T23"]
    ids_temas = {t.id for t in temas}

    cubre = defaultdict(list)          # objetivo → temas SV
    for e in aristas:
        if e.tipo == TipoArista.CUBRE and e.destino in por_id:
            cubre[e.destino].append(e.origen)
    alinea = defaultdict(set)          # objetivo → países
    for e in aristas:
        if e.tipo == TipoArista.ALINEA_CON:
            alinea[e.destino].add(por_id[e.origen].props.get("pais"))

    lineas = [f"# Ficha · {a_cfg['nombre']}",
              "",
              f"> Generada por `gskg fichas` desde el grafo {version}. No editar a mano.",
              "",
              "## Temas de la malla de El Salvador por grado", ""]
    por_grado = Counter(t.grado for t in temas)
    vias = Counter(t.props.get("metodo_asignatura") for t in temas)
    filas = []
    for g in sorted(por_grado):
        unidades = Counter(t.props.get("unidad") for t in temas if t.grado == g)
        filas.append([f"{g}.°", por_grado[g], "; ".join(u for u, _ in unidades.most_common(4))])
    lineas += [_tabla(["Grado", "Temas", "Unidades principales"], filas), "",
               f"Total: **{len(temas)} temas**. Asignados por: "
               + ", ".join(f"{k} {v}" for k, v in sorted(vias.items())) + ".", ""]

    lineas += ["## Cobertura de los marcos internacionales", ""]
    filas, faltan = [], []
    # AUSS se separa: sus objetivos de indagación y naturaleza de la ciencia se repiten en cada unidad
    # y no deben esconder los faltantes de contenido disciplinar.
    grupos = [("T4_27", None), ("T8_27", None), ("TA15", None), ("AUSS", "contenido"),
              ("AUSS", "practicas"), ("PISA25", None)]
    for marco, eje in grupos:
        objs = [o for o in objetivos if o.props.get("marco") == marco
                and (eje is None or (o.props.get("eje") == "contenido") == (eje == "contenido"))]
        if not objs:
            continue
        cub = [o for o in objs if any(t in ids_temas for t in cubre[o.id])]
        nombre = marco if eje is None else f"{marco} · {'contenido' if eje == 'contenido' else 'indagación y NdC'}"
        filas.append([nombre, len(objs), len(cub), f"{len(cub) / len(objs):.0%}"])
        if eje != "practicas":
            faltan += [(marco, o) for o in objs if o not in cub]
    lineas += [_tabla(["Marco", "Objetivos", "Cubiertos (en cualquier grado)", "%"], filas), ""]
    if faltan:
        lineas += ["### Objetivos sin ningún tema de esta asignatura", ""]
        lineas += [_tabla(["Marco", "Código", "Objetivo", "Países que lo trabajan"],
                          [[m, o.id.removeprefix("OBJ:"), o.etiqueta, ", ".join(sorted(alinea[o.id])) or "—"]
                           for m, o in faltan]), ""]

    pais_obj = Counter(n.props.get("pais") for n in nodos
                       if n.tipo == TipoNodo.OBJETIVO_PAIS and n.asignatura == asig)
    lineas += ["## Referentes de otros países en el grafo", "",
               _tabla(["País", "Objetivos alineados a esta asignatura"], sorted(pais_obj.items())) if pais_obj
               else "Aún no hay objetivos de países.", ""]
    return "\n".join(lineas)


def escribir_fichas(nodos: list[Nodo], aristas: list[Arista], version: str) -> list[str]:
    escritas = []
    for asig, a in cargar("asignaturas")["asignaturas"].items():
        p = ruta(a["carpeta"]) / "ficha.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(ficha(asig, nodos, aristas, version), encoding="utf-8")
        escritas.append(relativa(p))
    return escritas
