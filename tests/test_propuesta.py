import json

import pytest

from goes_science_kg.config import ruta

PROPUESTAS = sorted(ruta("asignaturas").glob("*/propuesta/propuesta_G*.json"))


@pytest.mark.parametrize("p", PROPUESTAS, ids=lambda p: f"{p.parent.parent.name}-{p.stem}")
def test_propuesta_respeta_presupuesto_y_reglas(p):
    prop = json.loads(p.read_text(encoding="utf-8"))
    cand = json.loads((p.parent / p.name.replace("propuesta_", "candidatos_")).read_text(encoding="utf-8"))
    antes = {int(g): k for g, k in cand["temas_por_grado"].items()}
    despues = {int(g): k for g, k in prop["temas_por_grado_propuesto"].items()}
    assert sum(antes.values()) == sum(despues.values()), "el total del ciclo debe conservarse"
    ids = {t["id"] for t in cand["temas_del_ciclo"]}
    for a in prop["acciones"]:
        assert a["accion"] in {"mover", "nuevo", "fusionar", "dividir", "revisar", "mantener"}
        assert a["accion"] != "quitar", "quitar temas requiere preguntar al usuario (CLAUDE.md)"
        assert set(a.get("temas_afectados", [])) <= ids
        assert a.get("evidencia"), f"acción {a.get('n')} sin evidencia"
    assert prop["estado"] == "borrador"


def test_candidatos_usan_el_marco_del_ciclo():
    """Regresión: los candidatos de 2.°–4.° se evaluaban contra TIMSS 8.° (T8_27) por un valor por defecto."""
    import json

    from goes_science_kg.config import ruta

    esperado = {"G02-G04": "T4_27", "G05-G08": "T8_27"}
    for p in ruta("asignaturas").glob("*/propuesta/candidatos_G*.json"):
        ciclo = p.stem.removeprefix("candidatos_")
        if ciclo in esperado:
            assert json.loads(p.read_text(encoding="utf-8"))["marco"] == esperado[ciclo], p


def test_simulacion_aplica_quitas_de_otras_asignaturas():
    """Biología 10.°–11.° retira etiquetas de Química; la simulación de Química debe verlas."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import simular

    r = simular("quimica", 10, 11, *cargar())
    assert any(q["asignatura"] == "biologia" for q in r["quitas_de_otras_asignaturas"])


def test_conciliacion_con_la_v2_completa_y_valida():
    """Cada acción «nuevo» tiene su conciliación con la V2, y los temas citados son de los 47 que agregó la V2."""
    from goes_science_kg.ingesta.mallas import extraer
    from goes_science_kg.propuesta import ESTADOS_ADOPCION, adopcion_v2

    adopcion = adopcion_v2()
    nuevos_v2 = {t.id for t in extraer()} - {t.id for t in extraer("mallas_v1")}
    for p in sorted(ruta("asignaturas").glob("*/propuesta/propuesta_G*.json")):
        asig, ciclo = p.parent.parent.name, p.stem.removeprefix("propuesta_")
        for a in json.loads(p.read_text(encoding="utf-8"))["acciones"]:
            if a["accion"] == "nuevo":
                f = adopcion[(asig, ciclo, a["n"])]
                assert f["estado"] in ESTADOS_ADOPCION and set(f["temas_v2"]) <= nuevos_v2
