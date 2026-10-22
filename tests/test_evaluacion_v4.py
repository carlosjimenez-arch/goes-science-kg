"""Transcripción íntegra de selectores sintéticos; no abre el reservado del producto."""

import json

import pytest

from goes_science_kg.curriculo.contratos import Curriculo, FuenteCurricular
from goes_science_kg.recuperacion.evaluacion_v4 import escribir_conjunto_v4, preparar_conjunto_v4


@pytest.fixture
def conjunto():
    fuente = FuenteCurricular(id="fuente-id-opaco", version="V4", archivo="malla.xlsx",
                              archivo_local="insumos/v4/malla.xlsx", sha256="a" * 64, bytes=100,
                              procedencia={"version": "V4"})
    curriculo = Curriculo(version="V4", huella="b" * 64, fuentes=(fuente,), filas=(), hojas=(), agrupaciones=())
    datos = {"conjunto_id": "fixture-sintetico", "nivel": "sintetico_plata", "casos": [{
        "id": "fixture-1", "consulta": "Una consulta que no revela su localizador", "grado": 4,
        "asignatura": "biologia", "fuente": {"archivo": "insumos/v4/malla.xlsx", "sha256": "a" * 64,
                                              "hoja": "Unidad 1", "filas": [2], "celdas": ["E2", "L2"]},
        "referencias_adicionales": [{"archivo": "insumos/v4/malla.xlsx", "sha256": "a" * 64,
                                     "hoja": "Unidad 1", "filas": [1], "celdas": ["E1"]}],
        "reservado_evaluador": {"secreto": "No debe llegar al modelo ni a consultas públicas"},
    }]}
    return datos, curriculo


def test_separa_consultas_y_gold_sin_eliminar_encabezados_ni_selectores_ausentes(conjunto, tmp_path):
    datos, curriculo = conjunto
    preparado = preparar_conjunto_v4(datos, curriculo)
    consultas = preparado["consultas"]["casos"]
    assert set(consultas[0]) == {"id", "consulta", "version", "grado", "asignatura"}
    assert "malla.xlsx" not in json.dumps(consultas) and "secreto" not in json.dumps(preparado)
    gold = preparado["gold_offline"]["objetivos"]["fixture-1"]
    assert len(gold) == 2 and sum(len(g["celdas"]) for g in gold) == 3
    assert all(g["documento"] == "fuente-id-opaco" for g in gold)
    assert preparado["gold_offline"]["avisos"]
    hashes = escribir_conjunto_v4(preparado, tmp_path / "evaluacion")
    assert set(hashes) == {"consultas", "gold_offline"} and all(len(v) == 64 for v in hashes.values())
    assert json.loads((tmp_path / "evaluacion/consultas_publicas.json").read_text())["casos"] == consultas


@pytest.mark.parametrize("campo,valor", [("archivo", "../malla.xlsx"), ("archivo", "/tmp/malla.xlsx"),
                                        ("sha256", "0" * 64), ("celdas", ["E3"]),
                                        ("celdas", ["E2", "E2"])])
def test_localizador_no_cambia_fuente_sha_fila_ni_ruta(conjunto, campo, valor):
    datos, curriculo = conjunto
    datos["casos"][0]["fuente"][campo] = valor
    with pytest.raises(ValueError):
        preparar_conjunto_v4(datos, curriculo)
