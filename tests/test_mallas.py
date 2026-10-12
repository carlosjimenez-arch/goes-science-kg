from collections import Counter

from goes_science_kg.config import cargar
from goes_science_kg.ingesta import legado
from goes_science_kg.ingesta.mallas import extraer

TEXTO = ("hoja", "fila", "grado", "asignatura", "unidad", "contenido", "subcontenido", "procedimental", "indicador")


def test_temas_por_grado_y_asignatura():
    ts = extraer()
    assert len(ts) == 1307
    c = Counter((t.grado, t.asignatura) for t in ts)
    assert c[(2, "ciencias")] == 71 and c[(9, "ciencias")] == 108
    assert c[(10, "fisica")] + c[(11, "fisica")] == 267
    assert c[(10, "quimica")] + c[(11, "quimica")] == 209
    assert c[(10, "biologia")] + c[(11, "biologia")] == 162


def test_ids_estables_y_unicos():
    a, b = extraer(), extraer()
    assert [t.id for t in a] == [t.id for t in b]
    assert len({t.id for t in a}) == len(a)


def test_lee_la_version_2():
    assert cargar("mallas")["directorio"].endswith("Mallas sugeridas v2")
    rutas_v1 = {t.ruta for t in extraer("mallas_v1") if t.grado in (2, 3, 4)}
    assert all("(1)" in r for r in rutas_v1)   # la V1 conserva sus versiones fijadas de 2.°–4.°


def test_la_v2_contiene_la_v1_sin_cambios():
    """Las etiquetas, revisiones, propuestas y preguntas de evaluación usan ids de la V1: siguen valiendo solo si la
    V2 conserva cada tema con el mismo id, ubicación y texto."""
    v2 = {t.id: t for t in extraer()}
    v1 = extraer("mallas_v1")
    assert len(v1) == 1260
    distintos = [t.id for t in v1 if t.id not in v2 or any(getattr(t, k) != getattr(v2[t.id], k) for k in TEXTO)]
    assert not distintos, distintos[:5]
    assert Counter(v2[i].grado for i in v2.keys() - {t.id for t in v1}) == {2: 1, 3: 6, 4: 6, 7: 1, 8: 15, 9: 18}


def test_clasificaciones_previas_llegan_a_la_v2():
    """Las clasificaciones previas usan el nombre del libro en la V1; `legado` lo traduce sin perder ningún tema."""
    ct, cp = legado.clasificacion_timss(), legado.clasificacion_pisa()
    v1 = {t.id for t in extraer("mallas_v1")}
    previos = [t for t in extraer() if t.id in v1]
    assert all((t.archivo, t.hoja, t.fila) in ct for t in previos if t.grado <= 9 or t.asignatura == "fisica")
    assert all((t.archivo, t.hoja, t.fila) in cp for t in previos if 7 <= t.grado <= 9)
