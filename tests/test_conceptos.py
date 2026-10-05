from collections import Counter

from goes_science_kg import conceptos as cp
from goes_science_kg.modelos import TipoArista, TipoNodo


def test_vocabulario_por_asignatura():
    voc = cp.vocabulario()
    c = Counter(v["asignatura"] for v in voc.values())
    assert set(c) == {"biologia", "fisica", "quimica", "ciencias_tierra_espacio"}
    assert all(40 <= k <= 140 for k in c.values())
    assert all(i.startswith(f"CON:{v['asignatura']}/") for i, v in voc.items())


def test_practicas():
    assert 18 <= len(cp.practicas()) <= 30


def test_todo_tema_en_alcance_esta_etiquetado(grafo):
    nodos, aristas = grafo
    temas = {n.id for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura}
    etiquetados = {a.origen for a in aristas if a.tipo == TipoArista.TRABAJA and a.origen.startswith("TEMA:")}
    assert temas <= etiquetados


def test_trabaja_es_trazable(grafo):
    _, aristas = grafo
    for a in (x for x in aristas if x.tipo == TipoArista.TRABAJA):
        assert a.confianza and a.justificacion and a.version
