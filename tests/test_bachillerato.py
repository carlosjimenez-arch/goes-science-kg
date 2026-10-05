from collections import Counter

from goes_science_kg.modelos import TipoArista, TipoNodo


def test_bachillerato_bio_quim_alineado_a_auss(grafo):
    nodos, aristas = grafo
    temas = {n.id for n in nodos if n.tipo == TipoNodo.TEMA and n.grado >= 10
             and n.asignatura in ("biologia", "quimica")}
    assert len(temas) == 371
    auss = {a.origen for a in aristas if a.tipo == TipoArista.CUBRE and a.destino.startswith("OBJ:ACS")}
    # Todo tema de Biología/Química de Bachillerato está alineado (o marcado FUERA en la clasificación).
    from goes_science_kg.ingesta.legado import clasificacion_auss

    fuera = {f"TEMA:{c['id']}" for c in clasificacion_auss().values() if c["obj1"] == "FUERA"}
    assert (auss | fuera) & temas == temas


def test_objetivos_auss_en_el_grafo(grafo):
    nodos, _ = grafo
    c = Counter(n.asignatura for n in nodos if n.tipo == TipoNodo.OBJETIVO_MARCO and n.props.get("marco") == "AUSS")
    assert c == {"biologia": 125, "quimica": 138}
