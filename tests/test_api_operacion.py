"""Verify service availability contracts without a private corpus."""

import json

import pytest
from fastapi.testclient import TestClient

from goes_science_kg.api import crear_app


def test_proceso_disponible_sin_falsear_disponibilidad_de_datos(tmp_path):
    cliente = TestClient(crear_app(tmp_path))
    assert cliente.get("/health/live").json()["estado"] == "ok"
    assert cliente.get("/app/").status_code == 200
    respuesta = cliente.get("/health/ready")
    assert respuesta.status_code == 503
    assert respuesta.json()["detail"]["estado"] == "sin_datos"
    assert "No hay datos disponibles" in respuesta.json()["detail"]["motivo"]


@pytest.mark.parametrize("ruta", ["/api/grados", "/api/rag?q=ciencia", "/api/v4/interfaz/resumen"])
def test_datos_ausentes_no_exponen_rutas_del_servidor(tmp_path, ruta):
    respuesta = TestClient(crear_app(tmp_path)).get(ruta)
    assert respuesta.status_code == 503
    assert str(tmp_path) not in respuesta.text
    assert "Errno" not in respuesta.text
    assert respuesta.json()["detail"]["estado"] == "sin_datos"


@pytest.mark.parametrize("puntero", [[], 42, None, {"snapshot_id": 42}, {"snapshot_id": []}])
def test_puntero_con_tipo_invalido_se_declara_no_disponible(tmp_path, puntero):
    archivo = tmp_path / "data/producto/V4/actual.json"
    archivo.parent.mkdir(parents=True)
    archivo.write_text(json.dumps(puntero))
    cliente = TestClient(crear_app(tmp_path))
    assert cliente.get("/health/live").status_code == 200
    for ruta in ("/health/ready", "/api/v4/interfaz/resumen"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 503
        assert respuesta.json()["detail"]["estado"] == "sin_datos"
