"""Test V3 error persistence, reinforcement candidates, and writer-output validation."""

from __future__ import annotations

from goes_science_kg import refuerzo


def test_los_errores_se_buscan_literales_en_la_v3():
    """Match known V3 errors literally at their current physical curriculum locations."""
    e = {x["id"]: x for x in refuerzo.errores_en_vigente()}
    assert e["ERR-05"]["estado"] == "corregido_en_v3" and not e["ERR-05"]["temas_v3"]
    assert e["ERR-01"]["temas_v3"] == ["G05-CIE-U6-6.7"]
    assert e["PROG-02"]["temas_v3"] == ["G11-FIS-U3-3.1-v3"]
    assert sum(x["estado"] == "sigue" for x in e.values()) == 10


def test_ubicacion_vigente_sigue_lo_movido_y_lo_absorbido():
    assert refuerzo.ubicacion_vigente("G07-CIE-U2-2.15") == "G09-CIE-U9-9.3-v3"  # movido de grado
    assert refuerzo.ubicacion_vigente("TEMA:G09-CIE-U3-3.6") == "G09-CIE-U3-3.3"  # absorbido
    assert refuerzo._grados_en("Retomar en 5.°–6.° y repasar en 9.°") == [5, 6, 9]


def test_candidatos_con_evidencia_y_sin_fragiles():
    filas = refuerzo.candidatos()
    assert len({f["id"] for f in filas}) == len(filas)
    assert {f["origen"] for f in filas} >= {"error_malla", "panel_hallazgo", "panel_propuesta", "contraste"}
    for f in filas:
        assert f["evidencia"] and f["solidez"] not in ("fragil", "sin_consenso", "sin_bucle")
        assert f["temas_v3"] or f["grados"] or f["origen"] == "quitado_v3"


def _lote():
    return {
        "lote": "x",
        "version": "v",
        "candidatos": [
            {"id": "REF-1", "tipo": "corregir"},
            {"id": "REF-2", "tipo": "recuperar"},
            {"id": "REF-3", "tipo": "acotar"},
        ],
    }


def test_el_validador_del_redactor():
    fila = {
        "contenido": "c",
        "procedimental": "5.12a. Descripción de algo.",
        "indicador": "5.12a. Describe algo.",
        "evidencia_aprendizaje": "e",
    }
    bien = [
        {
            "id": "REF-1",
            "decision": "inyectar",
            "forma": "nota_en_tema",
            "tema_ancla": "G06-CIE-U5-5.12",
            "refuerzo": "Escribir la energía aparte de los productos.",
            "evidencia": [{"fuente": "x"}],
            "confianza": "alta",
        },
        {
            "id": "REF-2",
            "decision": "inyectar",
            "forma": "fila_nueva",
            "tema_ancla": "G05-CIE-U6-6.7",
            "refuerzo": "Recuperar el tema.",
            "fila": fila,
            "evidencia": [{"fuente": "x"}],
            "confianza": "media",
        },
        {"id": "REF-3", "decision": "descartar", "motivo": "La V3 ya lo acota en 10.°.", "confianza": "alta"},
    ]
    assert refuerzo.errores_lote(_lote(), bien) == []
    mal = [
        {**bien[0], "tema_ancla": "G99-CIE-U1-1.1"},
        {**bien[1], "id": "REF-3"},
        {"id": "REF-2", "decision": "descartar"},
    ]
    errores = " | ".join(refuerzo.errores_lote(_lote(), mal))
    for esperado in ("no está en la malla vigente", "una fila nueva solo para", "exige motivo"):
        assert esperado in errores
