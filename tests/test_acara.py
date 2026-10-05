import json
from collections import Counter

from goes_science_kg.config import ruta
from goes_science_kg.ingesta import acara


def test_parser_lee_las_cuatro_unidades():
    for asig, total, ultimo in (("biologia", 125, "ACSBL125"), ("quimica", 138, "ACSCH138")):
        objs = acara.parsear(asig)
        assert len(objs) == total
        assert objs[-1]["codigo"] == ultimo
        assert set(Counter(o["unidad"] for o in objs)) == {1, 2, 3, 4}
        # Numeración oficial continua: no falta ninguna descripción de contenido.
        nums = sorted(int(o["codigo"][5:]) for o in objs)
        assert nums == list(range(1, total + 1))
        assert all(o["eje"] in {"contenido", "indagacion", "naturaleza_ciencia"} for o in objs)


def test_catalogo_completo_y_en_espanol():
    cat = json.loads(ruta(acara.SALIDA).read_text(encoding="utf-8"))
    assert len(cat) == 125 + 138
    assert len({o["codigo"] for o in cat}) == len(cat)
    for o in cat:
        assert o["objetivo"] and len(o["objetivo"].split()) <= 25
        assert o["localizador"] == o["codigo"]


def test_fuentes_registradas_con_sha256():
    import hashlib

    from goes_science_kg.ingesta.legado import manifiesto_fuentes

    docs = {d["id"]: d for d in manifiesto_fuentes()}
    for i in ("au_ss_bio_u13", "au_ss_bio_u4", "au_ss_chem_u13", "au_ss_chem_u4"):
        d = docs[i]
        contenido = (ruta("data/fuentes/externos") / d["archivo_local"]).read_bytes()
        assert hashlib.sha256(contenido).hexdigest() == d["sha256"]
