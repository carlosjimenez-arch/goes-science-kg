from collections import Counter

from goes_science_kg.ingesta.mallas import extraer


def test_temas_por_grado_y_asignatura():
    ts = extraer()
    assert len(ts) == 1260
    c = Counter((t.grado, t.asignatura) for t in ts)
    assert c[(2, "ciencias")] == 70 and c[(9, "ciencias")] == 90
    assert c[(10, "fisica")] + c[(11, "fisica")] == 267
    assert c[(10, "quimica")] + c[(11, "quimica")] == 209
    assert c[(10, "biologia")] + c[(11, "biologia")] == 162


def test_ids_estables_y_unicos():
    a, b = extraer(), extraer()
    assert [t.id for t in a] == [t.id for t in b]
    assert len({t.id for t in a}) == len(a)


def test_usa_las_versiones_fijadas_de_2_a_4():
    rutas = {t.ruta for t in extraer() if t.grado in (2, 3, 4)}
    assert all("(1)" in r for r in rutas)
