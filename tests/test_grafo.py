from collections import Counter

import pytest

from goes_science_kg.grafo.validar import validar
from goes_science_kg.modelos import Arista, TipoArista, TipoNodo


def test_grafo_sin_errores(grafo):
    rep = validar(*grafo)
    assert rep.ok, rep.errores[:10]


def test_conteos(grafo):
    nodos, aristas = grafo
    n = Counter(x.tipo for x in nodos)
    assert n[TipoNodo.TEMA] == 1260
    assert n[TipoNodo.ASIGNATURA] == 4
    # 506 objetivos heredados (UY, CO, SG) + los países nuevos de data/interim/paises/ (ENG 270, AU 152).
    assert n[TipoNodo.OBJETIVO_PAIS] >= 506
    paises = {x.props["pais"] for x in nodos if x.tipo == TipoNodo.OBJETIVO_PAIS}
    assert {"UY", "CO", "SG"} <= paises
    assert sum(1 for x in nodos if x.tipo == TipoNodo.OBJETIVO_MARCO and x.props["marco"] in ("T4_27", "T8_27")) == 80


def test_bachillerato_respeta_la_malla(grafo):
    nodos, _ = grafo
    for t in (x for x in nodos if x.tipo == TipoNodo.TEMA and x.grado >= 10):
        assert t.asignatura == t.props["asignatura_malla"]


def test_cubre_es_trazable(grafo):
    _, aristas = grafo
    for a in (x for x in aristas if x.tipo == TipoArista.CUBRE):
        assert a.confianza and a.justificacion and a.version


def test_arista_ia_sin_confianza_falla():
    with pytest.raises(ValueError):
        Arista(origen="TEMA:x", destino="OBJ:y", tipo=TipoArista.CUBRE, metodo="ia")


def test_grafo_determinista():
    from goes_science_kg.grafo.construir import construir

    a, b = construir(), construir()
    assert [n.id for n in a[0]] == [n.id for n in b[0]]
    assert [x.clave for x in a[1]] == [x.clave for x in b[1]]


def test_objetivos_de_paises_tienen_fuente_citable(grafo):
    nodos, _ = grafo
    for n in (x for x in nodos if x.tipo == TipoNodo.OBJETIVO_PAIS):
        assert n.fuente and (n.fuente.pagina or n.fuente.localizador), n.id
        assert n.props.get("grado_min"), n.id
