"""Lectura de propuestas fijadas: filtros, identidad y ausencia explícita, sin modelos."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_mejoras_curriculares import caso as caso
from test_mejoras_entrega import entrega as entrega

from goes_science_kg.api_mejoras import crear_router_mejoras


def cliente(entrega):
    curriculo, archivo = entrega
    runtime = SimpleNamespace(
        producto=SimpleNamespace(mejoras=archivo, curriculo=curriculo, manifest=SimpleNamespace(snapshot_id="d" * 64))
    )
    app = FastAPI()
    app.include_router(crear_router_mejoras(lambda: runtime), prefix="/api/v4")
    return TestClient(app), runtime


def test_listado_filtra_y_detalle_conserva_votos(entrega):
    api, runtime = cliente(entrega)
    r = api.get("/api/v4/propuestas?grado=3")
    assert r.status_code == 200 and len(r.json()["unidades"]) == 1
    assert r.json()["snapshot_id"] == "d" * 64
    assert api.get("/api/v4/propuestas?grado=4").json()["unidades"] == []
    id_ = runtime.producto.mejoras.unidades[0].preparacion.id
    detalle = api.get("/api/v4/propuestas/" + id_).json()
    assert len(detalle["resultado"]["rondas"][0]["dictamenes"]) == 4
    assert api.get("/api/v4/propuestas/ajena").status_code == 404


def test_version_sin_propuestas_no_simula_cobertura_vacia(entrega):
    api, runtime = cliente(entrega)
    runtime.producto.mejoras = None
    assert api.get("/api/v4/propuestas").status_code == 409
    assert api.get("/api/v4/progresiones").status_code == 409


def test_descarga_csv_es_de_la_misma_publicacion(entrega):
    api, _ = cliente(entrega)
    r = api.get("/api/v4/exportaciones/mejoras.csv")
    assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
    assert "objetivo_original" in r.text and "objetivo_propuesto" in r.text
    assert "attachment" in r.headers["content-disposition"]
