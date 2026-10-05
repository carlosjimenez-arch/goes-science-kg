from collections import Counter

from goes_science_kg import conceptos as cp
from goes_science_kg.modelos import TipoArista, TipoNodo


def test_vocabulario_por_asignatura():
    voc = cp.vocabulario()
    c = Counter(v["asignatura"] for v in voc.values())
    assert set(c) == {"biologia", "fisica", "quimica", "ciencias_tierra_espacio"}
    assert all(40 <= k <= 170 for k in c.values())  # Biología: 153 tras el triaje de conceptos propuestos
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


def test_lotes_de_paises_no_reutilizan_numeros():
    """Regresión: al sumar objetivos de un país ya etiquetado, preparar-paises reiniciaba en _1 y pisaba lotes."""
    import json

    from goes_science_kg.config import ruta

    d = ruta("data/interim/conceptos/lotes_paises")
    for p_sal in d.glob("salida_PAIS_*.json"):
        p_lote = p_sal.with_name(p_sal.name.replace("salida_", "lote_", 1))
        ids_lote = {i["id"] for i in json.loads(p_lote.read_text(encoding="utf-8"))["items"]}
        ids_sal = {r["id"] for r in json.loads(p_sal.read_text(encoding="utf-8"))}
        assert ids_sal <= ids_lote, p_sal.name


def test_triaje_suma_conceptos_nuevos_y_los_aplica_a_los_temas():
    nuevos = {c["id"] for c in cp.conceptos_del_triaje()}
    assert nuevos and nuevos <= set(cp.vocabulario())
    assert all(c["version"] == cp.VERSION_TRIAJE for c in cp.conceptos_del_triaje())
    con_triaje = [f for f in cp.etiquetado().values() if f.get("conceptos_triaje")]
    assert con_triaje and all(set(f["conceptos_triaje"]) <= set(f["conceptos"]) for f in con_triaje)
    # las decisiones de confianza baja no se aplican
    import json

    from goes_science_kg.config import ruta

    bajas = [t for t in json.loads(ruta("data/interim/conceptos/triaje_propuestos.json").read_text(encoding="utf-8"))
             if t.get("confianza") == "baja"]
    assert not {t["propuesto"] for t in bajas} & set(cp.mapa_triaje())
