"""Verify that Vertex batch prompts contain the source context required by each agent."""

from __future__ import annotations

from goes_science_kg import agentes_vertex


def test_temas_y_desenvolver():
    assert agentes_vertex._temas('{"a": "TEMA:G11-QUI-U2-2.1", "b": ["TEMA:G11-FIS-U3-3.1-v3"]}') == [
        "TEMA:G11-FIS-U3-3.1-v3",
        "TEMA:G11-QUI-U2-2.1",
    ]
    assert agentes_vertex._desenvolver({"salida": [1, 2]}) == [1, 2]
    assert agentes_vertex._desenvolver([3]) == [3]


def test_sistema_trae_el_agente_y_sus_prompts():
    s = agentes_vertex.sistema("redactor-actividades")
    assert "Reglas de la revisión del panel" in s and "No tienes herramientas" in s and not s.startswith("---")
