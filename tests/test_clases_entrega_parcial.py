"""Entrega de guiones con objetivos declarados sin guion liberado: nunca se omiten ni se presentan como listos."""

from __future__ import annotations

import pytest

from goes_science_kg.clases.paquete import MAX_SIN_GUION, sin_guion_declarados, validar_cobertura_publicable


def _pendiente(n, estado="no_respaldado"):
    return {"fila_id": f"F{n}", "estado": estado, "motivo": "Veto científico conservado en su expediente"}


def test_cobertura_completa_o_con_pendientes_declarados():
    validar_cobertura_publicable({"guion_clase": 1013, "guion_unidad": 108})
    validar_cobertura_publicable({"guion_clase": 1009, "guion_unidad": 108}, 4)
    with pytest.raises(ValueError, match="1013"):
        validar_cobertura_publicable({"guion_clase": 1009, "guion_unidad": 108})
    with pytest.raises(ValueError, match="1013"):
        validar_cobertura_publicable({"guion_clase": 1009, "guion_unidad": 107}, 4)
    with pytest.raises(ValueError, match="como máximo"):
        validar_cobertura_publicable({"guion_clase": 1013 - 21, "guion_unidad": 108}, MAX_SIN_GUION + 1)


def test_declaracion_de_pendientes_exige_estado_negativo_motivo_y_unicidad():
    assert (
        len(sin_guion_declarados({"objetivos_sin_guion_liberado": [_pendiente(1), _pendiente(2, "abstencion")]})) == 2
    )
    assert sin_guion_declarados({}) == []
    for malo in (
        [_pendiente(1), _pendiente(1)],
        [_pendiente(1, "respaldado_automaticamente")],
        [{"fila_id": "F1", "estado": "no_respaldado", "motivo": ""}],
    ):
        with pytest.raises(ValueError):
            sin_guion_declarados({"objetivos_sin_guion_liberado": malo})
