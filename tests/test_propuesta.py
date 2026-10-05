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
