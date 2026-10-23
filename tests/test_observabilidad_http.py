"""Verify local request correlation without collecting identifiers or secret query values."""

from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from goes_science_kg.api import crear_app
from goes_science_kg.observabilidad_http import ObservabilidadHTTP

LOGGER = "goes_science_kg.observabilidad_http"


def test_identidades_independientes_de_headers_cliente_y_tiempos_reales(tmp_path, caplog):
    with caplog.at_level("INFO", logger=LOGGER), TestClient(crear_app(tmp_path)) as cliente:
        respuestas = [
            cliente.get("/health/live?token=valor-no-registrar", headers={"X-Request-ID": "valor-no-registrar"})
            for _ in range(2)
        ]
    identidades = {respuesta.headers["x-request-id"] for respuesta in respuestas}
    assert len(identidades) == 2 and all(UUID(valor).version == 4 for valor in identidades)
    for respuesta in respuestas:
        assert respuesta.status_code == 200
        assert respuesta.headers["server-timing"].startswith("app;dur=")
        assert float(respuesta.headers["server-timing"].split("=", 1)[1]) >= 0
    eventos = [evento for evento in caplog.records if evento.name == LOGGER]
    assert {evento.request_id for evento in eventos} == identidades
    assert all(evento.http_route == "/health/live" and evento.http_status == 200 for evento in eventos)
    assert all(evento.http_method == "GET" and evento.duration_ms >= 0 for evento in eventos)
    assert "valor-no-registrar" not in caplog.text


def test_ausencia_de_datos_conserva_identidad_y_estado_503(tmp_path, caplog):
    with caplog.at_level("INFO", logger=LOGGER), TestClient(crear_app(tmp_path)) as cliente:
        respuesta = cliente.get("/health/ready")
    assert respuesta.status_code == 503 and respuesta.json()["detail"]["estado"] == "sin_datos"
    evento = next(evento for evento in caplog.records if evento.name == LOGGER)
    assert evento.request_id == respuesta.headers["x-request-id"]
    assert evento.http_status == 503 and evento.http_route == "/health/ready"


def test_logs_conservan_plantilla_sin_ruta_identificadora_ni_cuerpo(caplog):
    app = FastAPI()
    app.add_middleware(ObservabilidadHTTP)

    @app.post("/pruebas/{identidad}")
    def responder(identidad: str):
        return {"id": identidad}

    with caplog.at_level("INFO", logger=LOGGER), TestClient(app) as cliente:
        respuesta = cliente.post(
            "/pruebas/dato-no-registrar?clave=consulta-no-registrar", json={"dato": "cuerpo-privado"}
        )
    evento = next(evento for evento in caplog.records if evento.name == LOGGER)
    assert respuesta.status_code == 200 and evento.http_route == "/pruebas/{identidad}"
    assert all(valor not in caplog.text for valor in ("dato-no-registrar", "consulta-no-registrar", "cuerpo-privado"))
