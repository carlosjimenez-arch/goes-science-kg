from collections import Counter

from goes_science_kg.config import cargar
from goes_science_kg.ingesta import legado
from goes_science_kg.ingesta.mallas import _norma, correspondencia, extraer

TEXTO = ("hoja", "fila", "grado", "asignatura", "unidad", "contenido", "subcontenido", "procedimental", "indicador")


def test_temas_por_grado_y_asignatura():
    ts = extraer()
    assert len(ts) == 935
    c = Counter((t.grado, t.asignatura) for t in ts)
    assert c[(2, "ciencias")] == 70 and c[(9, "ciencias")] == 99
    assert c[(10, "fisica")] + c[(11, "fisica")] == 64
    assert c[(10, "quimica")] + c[(11, "quimica")] == 128
    assert c[(10, "biologia")] + c[(11, "biologia")] == 125


def test_ids_estables_y_unicos():
    a, b = extraer(), extraer()
    assert [t.id for t in a] == [t.id for t in b]
    assert len({t.id for t in a}) == len(a)


def test_lee_la_version_3():
    assert cargar("mallas")["directorio"].endswith("Mallas sugeridas v3")
    assert cargar("mallas_v2")["directorio"].endswith("Mallas sugeridas v2")
    rutas_v1 = {t.ruta for t in extraer("mallas_v1") if t.grado in (2, 3, 4)}
    assert all("(1)" in r for r in rutas_v1)  # la V1 conserva sus versiones fijadas de 2.°–4.°


def test_la_v2_contiene_la_v1_sin_cambios():
    """Retain V1 identities only while their original curriculum text remains unchanged in V2."""

    # Historical test notes:
    # V2 conserva cada tema con el mismo id, ubicación y texto.
    v2 = {t.id: t for t in extraer("mallas_v2")}
    v1 = extraer("mallas_v1")
    assert len(v2) == 1307 and len(v1) == 1260
    distintos = [t.id for t in v1 if t.id not in v2 or any(getattr(t, k) != getattr(v2[t.id], k) for k in TEXTO)]
    assert not distintos, distintos[:5]
    assert Counter(v2[i].grado for i in v2.keys() - {t.id for t in v1}) == {2: 1, 3: 6, 4: 6, 7: 1, 8: 15, 9: 18}


def test_la_v3_conserva_los_ids_de_la_v2():
    """Preserve matched V2 identities in V3 and create distinct identities for new topics."""

    # Historical test notes:
    # nunca toma un id que existió en la V2 para otro tema.
    v2 = {t.id: t for t in extraer("mallas_v2")}
    ts = extraer()
    assert Counter(t.origen for t in ts) == {"identico": 819, "parecido": 21, "ampliado": 75, "nuevo": 20}
    for t in ts:
        if t.origen == "nuevo":
            assert t.id not in v2 and t.llave[0].startswith("V3/")
        else:
            p = v2[t.id]
            assert (p.grado, p.asignatura) == (t.grado, t.asignatura) and t.llave == (p.archivo, p.hoja, p.fila)
            assert t.origen != "identico" or _norma(p.procedimental) == _norma(t.procedimental)


def test_la_correspondencia_guardada_esta_al_dia():
    """Keep persisted V2-to-V3 correspondence consistent with deterministic source comparison."""
    import json

    from goes_science_kg.config import ruta

    guardada = json.loads(ruta(cargar("mallas")["correspondencia"]).read_text(encoding="utf-8"))
    assert guardada == correspondencia()
    assert guardada["resumen"]["sin_par_en_la_anterior"] == len(guardada["sin_par"]) == 1307 - 819 - 21 - 75
    vigentes = {f["id"] for f in guardada["temas"]}
    assert all(x["absorbido_por"] in vigentes for x in guardada["sin_par"] if x["absorbido_por"])


def test_lo_movido_de_grado_no_es_quitado():
    """Distinguish moved curriculum topics from removed topics."""
    import json

    from goes_science_kg.config import ruta

    d = json.loads(ruta(cargar("mallas")["correspondencia"]).read_text(encoding="utf-8"))
    movidos = {x["id"]: x["movido_a"] for x in d["sin_par"] if x["movido_a"]}
    assert movidos["G07-CIE-U2-2.15"] == "G09-CIE-U9-9.3-v3"  # resistencia bacteriana
    assert d["resumen"]["movidos_de_grado"] == len(movidos) == 5


def test_vigente_de_traduce_lo_absorbido():
    """Resolve explicitly absorbed historical topics to their current curriculum identities."""

    # Historical test notes:
    # leen en 3.3. Un tema que sigue en la malla es él mismo; uno sin rastro, None.
    from goes_science_kg.ingesta.mallas import vigente_de

    assert vigente_de("TEMA:G09-CIE-U3-3.6") == "TEMA:G09-CIE-U3-3.3"
    assert vigente_de("G09-CIE-U3-3.1") == "G09-CIE-U3-3.1"
    assert vigente_de("G99-CIE-U1-1.1") is None


def test_clasificaciones_previas_llegan_a_la_v3():
    """Carry historical classifications through the documented source-location correspondence."""

    # Historical test notes:
    # heredan los temas de la V3 con par.
    ct, cp = legado.clasificacion_timss(), legado.clasificacion_pisa()
    v1 = {t.id for t in extraer("mallas_v1")}
    previos = [t for t in extraer() if t.id in v1 and t.origen == "identico"]
    assert previos
    assert all(t.llave in ct for t in previos if t.grado <= 9 or t.asignatura == "fisica")
    assert all(t.llave in cp for t in previos if 7 <= t.grado <= 9)
