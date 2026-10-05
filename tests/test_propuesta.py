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
