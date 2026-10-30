"""El historial no debe contaminar el borrador; los votos antiguos mantienen su clave."""

from __future__ import annotations

from copy import deepcopy

from goes_science_kg.clases.contexto import contexto
from goes_science_kg.clases.preparacion import contexto as contexto_historico


def test_contexto_separa_alertas_sin_perder_objetivo_criterios_datos_o_fuentes():
    propuesta = {
        "objetivo_propuesto": "Comparar células en división.",
        "criterio_evaluacion": "Distingue fases y límites de la inferencia.",
        "seguridad": "Actividad en papel.",
        "justificacion": "Una alerta antigua de ångström sin relación con mitosis.",
        "fragmentos_ids": ["historico"],
    }
    fila = {
        "fila_id": "f1",
        "grado": 9,
        "propuesta": propuesta,
        "alerta_original": "Corrección de otro proceso",
        "origen": {"fila": 3},
        "consulta_recuperacion": "irrelevante",
        "fuentes_cientificas_ids": ["e1"],
        "datos_contextuales": [{"tabla": [1, 2, 3]}],
        "enmienda_didactica_auditoria": "Los datos simulados no prueban una causa.",
    }
    fuente = {"id": "e1", "texto": "Pasaje completo " * 2000}
    p = {"escenario": {"recursos": ["papel"]}, "filas": [fila], "fuentes": [fuente]}
    antes = deepcopy(p)
    viejo = contexto_historico(p)
    nuevo = contexto(p)
    assert viejo["filas"][0] == antes["filas"][0]
    assert nuevo["filas"][0]["propuesta"] == {
        k: propuesta[k]
        for k in (
            "objetivo_propuesto",
            "criterio_evaluacion",
            "seguridad",
        )
    }
    assert nuevo["fuentes"] == [fuente]
    assert nuevo["filas"][0]["datos_contextuales"] == fila["datos_contextuales"]
    assert nuevo["filas"][0]["enmienda_didactica_auditoria"] == fila["enmienda_didactica_auditoria"]
    assert not {"alerta_original", "origen", "consulta_recuperacion"} & nuevo["filas"][0].keys()
    nuevo["filas"][0]["datos_contextuales"][0]["tabla"].clear()
    assert p == antes


def test_contexto_no_intercambia_fuentes_entre_filas():
    p = {
        "escenario": {},
        "filas": [
            {"fila_id": id_, "propuesta": {}, "fuentes_cientificas_ids": [e]} for id_, e in (("f1", "e1"), ("f2", "e2"))
        ],
        "fuentes": [{"id": "e1"}, {"id": "e2"}],
    }
    assert contexto(p, ids={"f2"}) == {"escenario": {}, "filas": [p["filas"][1]], "fuentes": [{"id": "e2"}]}
