"""Calidad y bidireccionalidad de los grafos versionados (auditoría del 2026-10-09).

- Estructura: cada arista une los tipos de nodo que permite el modelo, sin autolazos ni pares en los dos sentidos, y
  el DAG de prerrequisitos no tiene ciclos ni aristas transitivas.
- Grafo ↔ fuentes, en los dos sentidos: cada nodo apunta a una fuente que existe (fila del Excel, página del PDF,
  sha256) y cada elemento de las fuentes está en el grafo.
- Entre grafos: los subgrafos por grado y el grafo internacional son coherentes con el principal.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict

import networkx as nx
import pytest

from goes_science_kg import conceptos
from goes_science_kg.config import cargar, ruta
from goes_science_kg.grafo.almacen import cargar as cargar_grafo
from goes_science_kg.modelos import TipoArista as A
from goes_science_kg.modelos import TipoNodo as N

CONTRATO = {
    A.EN_GRADO: ({N.TEMA}, {N.GRADO}),
    A.DE_ASIGNATURA: ({N.TEMA, N.OBJETIVO_MARCO, N.OBJETIVO_PAIS, N.CONCEPTO}, {N.ASIGNATURA}),
    A.EN_MARCO: ({N.OBJETIVO_MARCO}, {N.MARCO}),
    A.DE_PAIS: ({N.OBJETIVO_PAIS}, {N.PAIS}),
    A.FUENTE: (set(N), {N.DOCUMENTO}),
    A.CUBRE: ({N.TEMA}, {N.OBJETIVO_MARCO}),
    A.ALINEA_CON: ({N.OBJETIVO_PAIS}, {N.OBJETIVO_MARCO}),
    A.EQUIVALE_A: ({N.OBJETIVO_MARCO, N.CONCEPTO}, {N.OBJETIVO_MARCO, N.CONCEPTO}),
    A.TRABAJA: ({N.TEMA, N.OBJETIVO_PAIS, N.OBJETIVO_MARCO}, {N.CONCEPTO, N.PRACTICA}),
    A.PRERREQUISITO_DE: ({N.CONCEPTO}, {N.CONCEPTO}),
}


@pytest.fixture(scope="module")
def principal():
    nodos, aristas = cargar_grafo()
    return nodos, aristas, {n.id: n for n in nodos}


@pytest.fixture(scope="module")
def internacional():
    d = ruta("data/grafo/internacional")
    nodos = {(n := json.loads(linea))["id"]: n for linea in open(d / "nodos.jsonl", encoding="utf-8")}
    aristas = [json.loads(linea) for linea in open(d / "aristas.jsonl", encoding="utf-8")]
    return nodos, aristas


def _archivo(doc):
    a = doc.props.get("archivo_local")
    if not a:
        return None
    for base in ("", "data/fuentes/externos/", "data/fuentes/"):
        if (p := ruta(base + a)).exists():
            return p
    return None


# -- Estructura -------------------------------------------------------------------------------------------------------
def test_contrato_de_tipos_por_arista(principal):
    _, aristas, por_id = principal
    malas = [(a.tipo, a.origen, a.destino) for a in aristas
             if por_id[a.origen].tipo not in CONTRATO[a.tipo][0] or por_id[a.destino].tipo not in CONTRATO[a.tipo][1]]
    assert not malas, malas[:5]


def test_sin_autolazos_ni_relaciones_en_los_dos_sentidos(principal):
    _, aristas, _ = principal
    assert not [a for a in aristas if a.origen == a.destino]
    trios = {(a.origen, a.destino, a.tipo) for a in aristas}
    assert not [t for t in trios if (t[1], t[0], t[2]) in trios]


def test_dag_de_prerrequisitos_sin_ciclos_ni_redundancias(principal):
    _, aristas, _ = principal
    dag = nx.DiGraph([(a.origen, a.destino) for a in aristas if a.tipo == A.PRERREQUISITO_DE])
    assert nx.is_directed_acyclic_graph(dag)
    assert dag.number_of_edges() == nx.transitive_reduction(dag).number_of_edges()


def test_sin_prerrequisitos_entre_equivalentes(principal):
    """Si dos conceptos son el mismo (EQUIVALE_A), uno no puede ser prerrequisito del otro. Las 3 contradicciones de la
    auditoría se resolvieron el 2026-10-09 (equivalencias_retiradas.json y prerrequisitos/rechazados.json)."""
    _, aristas, _ = principal
    eq = {frozenset((a.origen, a.destino)) for a in aristas
          if a.tipo == A.EQUIVALE_A and a.origen.startswith("CON:")}
    assert not [(a.origen, a.destino) for a in aristas
                if a.tipo == A.PRERREQUISITO_DE and frozenset((a.origen, a.destino)) in eq]


def test_sin_nodos_aislados(principal):
    nodos, aristas, _ = principal
    conectados = {a.origen for a in aristas} | {a.destino for a in aristas}
    assert not [n.id for n in nodos if n.id not in conectados]


def test_el_enlace_quimico_no_depende_de_la_mecanica_cuantica(principal):
    """Regresión pedagógica: la regla del octeto y el enlace se enseñan con el modelo de capas (división de
    «Configuración electrónica», conceptos/divisiones.json)."""
    _, aristas, _ = principal
    dag = nx.DiGraph([(a.origen, a.destino) for a in aristas if a.tipo == A.PRERREQUISITO_DE])
    for cuantico in ("CON:quimica/numeros-cuanticos", "CON:quimica/configuracion-electronica"):
        assert not nx.has_path(dag, cuantico, "CON:quimica/enlace-quimico")
    assert nx.has_path(dag, "CON:quimica/distribucion-electronica-por-niveles", "CON:quimica/enlace-quimico")


def test_divisiones_aplicadas_en_todos_los_conjuntos():
    from goes_science_kg.internacional import etiquetar

    cargadas = {"malla_v1": {i: e["conceptos"] for i, e in conceptos.etiquetado().items()},
                "objetivos_pais": {i: e["conceptos"] for i, e in conceptos.etiquetado_paises().items()},
                "internacional": {i: e["principales"] + e["secundarios"]
                                  for i, e in etiquetar.cargar_etiquetas("pais_").items()}}
    for d in conceptos.divisiones():
        assert d["nuevo"]["id"] in conceptos.vocabulario()
        for conjunto, asignaciones in d["asignaciones"].items():
            for item, esperados in asignaciones.items():
                if conjunto in cargadas:
                    assert set(esperados) <= set(cargadas[conjunto][item]), (conjunto, item)
                    if d["concepto"] not in esperados:
                        assert d["concepto"] not in cargadas[conjunto][item], (conjunto, item)


def test_relaciones_esperadas_en_cada_nodo(principal):
    """Navegación inversa: cada tema tiene grado, asignatura y conceptos; cada objetivo, su país o marco."""
    nodos, aristas, _ = principal
    sal = defaultdict(Counter)
    for a in aristas:
        sal[a.origen][a.tipo] += 1
    en_alcance = [n for n in nodos if n.tipo == N.TEMA and not n.props.get("fuera_de_alcance")]
    assert all(sal[n.id][A.EN_GRADO] and sal[n.id][A.DE_ASIGNATURA] and sal[n.id][A.TRABAJA] for n in en_alcance)
    assert all(sal[n.id][A.DE_PAIS] for n in nodos if n.tipo == N.OBJETIVO_PAIS)
    assert all(sal[n.id][A.EN_MARCO] for n in nodos if n.tipo == N.OBJETIVO_MARCO)


# -- Grafo ↔ fuentes ----------------------------------------------------------------------------
def test_cada_tema_esta_en_su_fila_del_excel(principal):
    import openpyxl

    nodos, _, por_id = principal
    libros, faltan = {}, []
    for t in (n for n in nodos if n.tipo == N.TEMA):
        p = _archivo(por_id[f"DOC:{t.fuente.documento}"])
        if p not in libros:
            libros[p] = openpyxl.load_workbook(p, data_only=True, read_only=True)
        fila = next(libros[p][t.fuente.hoja].iter_rows(min_row=t.fuente.fila, max_row=t.fuente.fila, values_only=True))
        texto = re.sub(r"\s+", " ", " ".join(str(v) for v in fila if v is not None))
        if re.sub(r"\s+", " ", t.etiqueta)[:40] not in texto:
            faltan.append(t.id)
    assert not faltan, faltan[:5]


def test_documentos_con_sha256_coinciden(principal):
    nodos, _, _ = principal
    docs = [n for n in nodos if n.tipo == N.DOCUMENTO and n.props.get("ok", True)]
    malos = [n.id for n in docs if (p := _archivo(n)) and p.is_file() and n.props.get("sha256")
             and hashlib.sha256(p.read_bytes()).hexdigest() != n.props["sha256"]]
    assert not malos
    mallas = [n for n in docs if n.id.startswith("DOC:MALLA:")]
    assert mallas and all(n.props.get("sha256") for n in mallas)


def test_paginas_citadas_existen():
    pypdf = pytest.importorskip("pypdf")
    from goes_science_kg.internacional.consenso import objetivos

    docs = {d["id"]: d for d in cargar("internacional")["documentos"]}
    paginas = {}
    fuera = []
    for o in objetivos():
        d = docs.get(o["documento"])
        if not d or not d["archivo"].endswith(".pdf"):
            continue
        if d["archivo"] not in paginas:
            paginas[d["archivo"]] = len(pypdf.PdfReader(ruta(d["archivo"])).pages)
        rangos = d.get("paginas") or [1, paginas[d["archivo"]]]
        rangos = [rangos] if isinstance(rangos[0], int) else rangos
        if not any(a <= o["pagina"] <= b for a, b in rangos):
            fuera.append(o["id"])
    assert not fuera, fuera[:5]


def test_de_las_fuentes_al_grafo_uno_a_uno(principal):
    from goes_science_kg.grafo.construir import Constructor
    from goes_science_kg.ingesta import legado
    from goes_science_kg.ingesta.mallas import extraer
    from goes_science_kg.prerrequisitos import cargar_prerrequisitos

    nodos, aristas, por_id = principal
    de_tipo = lambda t: {n.id for n in nodos if n.tipo == t}  # noqa: E731
    assert de_tipo(N.TEMA) == {f"TEMA:{t.id}" for t in extraer()}
    assert de_tipo(N.CONCEPTO) == set(conceptos.vocabulario())
    assert de_tipo(N.PRACTICA) == set(conceptos.practicas())
    assert de_tipo(N.OBJETIVO_PAIS) == {f"OP:{o['id']}" for o in [*legado.alineacion_paises(), *legado.paises_nuevos()]}
    assert {(a.origen, a.destino) for a in aristas if a.tipo == A.PRERREQUISITO_DE} == \
        {(e["origen"], e["destino"]) for e in cargar_prerrequisitos()}
    assert {(a.origen, a.destino) for a in aristas if a.tipo == A.EQUIVALE_A and a.origen.startswith("CON:")} == \
        {(e["a"], e["b"]) for e in conceptos.equivalencias()}
    esperadas = {(f"TEMA:{t}", c) for t, e in Constructor._etiquetas_revisadas().items()
                 for c in e["conceptos"] + e["practicas"] if f"TEMA:{t}" in por_id and c in por_id}
    assert {(a.origen, a.destino) for a in aristas if a.tipo == A.TRABAJA and a.origen.startswith("TEMA:")} == esperadas


# -- Entre grafos ----------------------------------------------------------------------------
def test_subgrafos_por_grado_contenidos_y_completos(principal):
    nodos, aristas, por_id = principal
    claves = {(a.origen, a.destino, a.tipo.value, a.rol) for a in aristas}
    for d in sorted(ruta("data/grafo/grados").glob("G*")):
        g = int(d.name[1:])
        sn = [json.loads(linea) for linea in open(d / "nodos.jsonl", encoding="utf-8")]
        sa = [json.loads(linea) for linea in open(d / "aristas.jsonl", encoding="utf-8")]
        ids = {n["id"] for n in sn}
        assert all(por_id[n["id"]].model_dump(mode="json", exclude_none=True, exclude_defaults=True) == n
                   for n in sn), d.name
        assert all((a["origen"], a["destino"], a["tipo"], a.get("rol")) in claves for a in sa), d.name
        assert all(a["origen"] in ids and a["destino"] in ids for a in sa), d.name
        temas = {n.id for n in nodos if n.tipo == N.TEMA and n.grado == g and not n.props.get("fuera_de_alcance")}
        assert temas <= ids, d.name


def test_internacional_coherente_con_el_principal_y_sus_fuentes(principal, internacional):
    from goes_science_kg.internacional.consenso import objetivos

    _, aristas, por_id = principal
    nodos, ina = internacional
    ent, sal = defaultdict(Counter), defaultdict(Counter)
    for a in ina:
        assert a["origen"] in nodos and a["destino"] in nodos
        sal[a["origen"]][a["tipo"]] += 1
        ent[a["destino"]][a["tipo"]] += 1
    obj = [n for n in nodos.values() if n["tipo"] == "ObjetivoPais"]
    assert {n["id"] for n in obj} == {o["id"] for o in objetivos()}
    # Jerarquía y fuente: un curso y un documento del registro por objetivo (los mismos ids que el principal).
    assert all(ent[n["id"]]["CONTIENE"] == 1 and sal[n["id"]]["FUENTE"] == 1 for n in obj)
    from goes_science_kg.ingesta import legado

    registro = {f"DOC:{r['id']}" for r in legado.manifiesto_fuentes()}
    docs = [n for n in nodos.values() if n["tipo"] == "Documento"]
    assert docs and all(n["id"] in registro for n in docs)   # mismos ids que el registro de fuentes
    # Conceptos y prerrequisitos idénticos a los del principal.
    for n in nodos.values():
        if n["tipo"] in ("Concepto", "Practica"):
            assert por_id[n["id"]].etiqueta == n["nombre"]
    pre = {(a.origen, a.destino) for a in aristas if a.tipo == A.PRERREQUISITO_DE}
    pre_int = {(a["origen"], a["destino"]) for a in ina if a["tipo"] == "PRERREQUISITO"}
    assert pre_int == {p for p in pre if p[0] in nodos and p[1] in nodos}
