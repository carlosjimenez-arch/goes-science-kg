"""Prevent empty or partially failing test runs from producing misleading badges."""

import json
import runpy
from pathlib import Path

import pytest


@pytest.fixture
def generador():
    return runpy.run_path(str(Path(__file__).parents[1] / "scripts/generar_badges.py"))["generar"]


def test_badges_conservan_fallos_omitidas_y_denominador(generador, tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite tests="10" failures="1" errors="1" skipped="2"/></testsuites>')
    cobertura = tmp_path / "coverage.xml"
    cobertura.write_text('<coverage lines-covered="15" lines-valid="20"/>')
    raiz = Path(__file__).parents[1]
    informe = generador(junit, cobertura, tmp_path / "badges", raiz)
    assert informe["pruebas"]["aprobadas"] == 6
    assert informe["pruebas"]["ejecutadas"] == 8
    assert informe["pruebas"]["porcentaje_aprobado"] == 75
    assert informe["cobertura"]["porcentaje"] == 75
    assert "75.00%" in (tmp_path / "badges/pass-rate.svg").read_text()
    assert json.loads((tmp_path / "badges/medicion.json").read_text())["pruebas"]["errors"] == 1


def test_suite_vacia_no_publica_un_cien_por_ciento(generador, tmp_path):
    junit = tmp_path / "junit.xml"
    junit.write_text('<testsuites><testsuite tests="0"/></testsuites>')
    with pytest.raises(ValueError, match="denominador"):
        generador(junit, tmp_path / "no-existe.xml", tmp_path / "badges", Path(__file__).parents[1])
    assert not (tmp_path / "badges").exists()
