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
        validar_cobertura_publicable({"guion_clase": 1013 - MAX_SIN_GUION - 1, "guion_unidad": 108}, MAX_SIN_GUION + 1)


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


def test_bloqueo_por_revision_directa_es_un_estado_declarable():
    pendiente = _pendiente(3, "bloqueado_revision_directa")
    assert (
        sin_guion_declarados({"objetivos_sin_guion_liberado": [pendiente]})[0]["estado"] == "bloqueado_revision_directa"
    )


def test_revisiones_directas_aplican_a_una_version_exacta_del_guion(tmp_path):
    import json

    from goes_science_kg.clases.compilacion import cargar_revisiones_directas

    def revision(sha, veredicto):
        return {"fila_id": "F1", "guion_sha256": sha, "veredicto": veredicto, "hallazgos": [], "verificaciones": []}

    (tmp_path / "a.json").write_text(json.dumps({"revisiones": [revision("1" * 64, "bloquear")]}))
    (tmp_path / "b.json").write_text(json.dumps({"revisiones": [revision("2" * 64, "liberable")]}))
    revisiones = cargar_revisiones_directas(tmp_path, ["a.json", "b.json"])
    # La versión bloqueada y su corrección aprobada conviven sin que una oculte a la otra.
    assert revisiones[("F1", "1" * 64)]["veredicto"] == "bloquear"
    assert revisiones[("F1", "2" * 64)]["expediente"] == "b.json"
    with pytest.raises(ValueError, match="duplicada"):
        cargar_revisiones_directas(tmp_path, ["a.json", "a.json"])
