"""Test the V4 API against a temporary real publication and verified original sources."""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402
from test_producto_v4 import catalogo as catalogo  # noqa: E402
from test_producto_v4 import curriculo as curriculo  # noqa: E402

from goes_science_kg.api import crear_app  # noqa: E402
from goes_science_kg.config import ruta  # noqa: E402
from goes_science_kg.producto import construir_producto  # noqa: E402


@pytest.fixture(scope="module")
def publicado(tmp_path_factory, curriculo, catalogo):
    base = tmp_path_factory.mktemp("api-v4")
    shutil.copytree(ruta("insumos/v4"), base / "insumos/v4")
    alertas = base / "docs/investigacion/alertas_v4.json"
    alertas.parent.mkdir(parents=True)
    shutil.copyfile(ruta("docs/investigacion/alertas_v4.json"), alertas)
    informe = construir_producto(
        curriculo,
        catalogo,
        destino=base / "data/producto/V4",
        raiz_v4=base / "insumos/v4",
    )
    filas = [f for f in curriculo.filas if f.grado == 10 and f.asignatura_malla == "Física"]
    fuente = next(f for f in curriculo.fuentes if f.id == filas[0].fuente_id)
    return SimpleNamespace(base=base, informe=informe, filas=filas, fuente_fisica=fuente)


@pytest.fixture
def cliente(publicado, monkeypatch):
    def prohibido(*args, **kwargs):
        raise AssertionError("La API de lectura no crea proveedores Vertex")

    monkeypatch.setattr("goes_science_kg.motor.vertex.Vertex.__init__", prohibido)
    return TestClient(crear_app(publicado.base))


def test_v4_se_consulta_sin_grafo_historico_ni_proveedor(publicado, cliente):
    r = cliente.get("/api/v4/salud")
    assert r.status_code == 200
    assert r.json()["snapshot_id"] == publicado.informe["snapshot_id"]
    assert r.json()["filas"] == 1020 and r.json()["version_curriculo"] == "V4"
    assert cliente.get("/api/salud").status_code == 503
    assert cliente.get("/api/v4/diagnostico").json()["diagnostico"]["temas"] == 1020
    assert cliente.get("/api/v4/juicios/CANDIDATO:inexistente").status_code == 404


def test_filtros_y_paginacion_conservan_total_y_filas_exactas(cliente, publicado):
    r = cliente.get("/api/v4/filas", params={"grado": 10, "disciplina": "fisica", "limite": 3})
    assert r.status_code == 200
    assert r.json()["total"] == len(publicado.filas) and len(r.json()["filas"]) == 3
    assert all(f["grado"] == 10 and f["asignatura_malla"] == "Física" for f in r.json()["filas"])
    siguiente = cliente.get("/api/v4/filas", params={"grado": 10, "disciplina": "fisica", "offset": 3, "limite": 3})
    assert {f["id"] for f in r.json()["filas"]}.isdisjoint(f["id"] for f in siguiente.json()["filas"])
    assert cliente.get("/api/v4/filas", params={"limite": 1000}).status_code == 422


def test_fila_recupera_celdas_exactas_y_contexto_rechaza_otro_grado(publicado, cliente):
    f = publicado.filas[0]
    r = cliente.get(f"/api/v4/filas/{f.id}")
    assert r.status_code == 200
    assert r.json()["fila"]["procedimental"] == f.procedimental
    assert all(e["id"].startswith(f.id + "#CELDA:") for e in r.json()["evidencias"])
    params = {"fila_id": f.id, "grado": 10, "disciplina": "fisica"}
    contexto = cliente.get("/api/v4/contexto", params=params)
    assert contexto.status_code == 200 and contexto.json()["evidencias"]
    assert cliente.get("/api/v4/contexto", params=params | {"grado": 9}).status_code == 422
    assert cliente.get("/api/v4/filas/TEMA:V3:ajena").status_code == 404


def test_preparar_unidad_conserva_ocho_objetivos_sin_generar(cliente):
    r = cliente.post(
        "/api/v4/unidades/preparar",
        json={
            "grado": 10,
            "asignatura_malla": "Física",
            "unidad": "1. La física como ciencia",
            "contexto": {"minutos_por_sesion": 40, "recursos": ["papel", "lapiz"], "conectividad": "sin_confirmar"},
        },
    )
    assert r.status_code == 200
    assert len(r.json()["paquete"]["filas"]) == len(r.json()["paquete"]["sesiones"]) == 8
    assert r.json()["llamadas_modelos"] == 0
    assert (
        cliente.post(
            "/api/v4/unidades/preparar",
            json={
                "grado": 10,
                "asignatura_malla": "Física",
                "unidad": "inexistente",
            },
        ).status_code
        == 422
    )


@pytest.mark.parametrize("archivo", ["manifest.json", "catalogo.json", "nodos.jsonl", "conocimiento.json"])
def test_snapshot_alterado_invalida_instancia_aun_despues_de_restaurar(publicado, cliente, archivo):
    assert cliente.get("/api/v4/salud").status_code == 200
    p = Path(publicado.informe["ruta_grafo"]) / archivo
    original = p.read_bytes()
    try:
        p.write_bytes(original + b" ")
        assert cliente.get("/api/v4/filas").status_code == 503
    finally:
        p.write_bytes(original)
    assert cliente.get("/api/v4/salud").status_code == 503
    assert TestClient(crear_app(publicado.base)).get("/api/v4/salud").status_code == 200


def test_original_modificado_no_se_sustituye_con_metadata(publicado, cliente):
    f = publicado.filas[0]
    assert cliente.get(f"/api/v4/filas/{f.id}").status_code == 200
    p = publicado.base / publicado.fuente_fisica.archivo_local
    original = p.read_bytes()
    try:
        p.write_bytes(b"fuente alterada")
        assert cliente.get(f"/api/v4/filas/{f.id}").status_code == 503
    finally:
        p.write_bytes(original)


def test_sin_publicacion_no_hay_fallback_a_v3(tmp_path):
    c = TestClient(crear_app(tmp_path))
    assert c.get("/api/v4/salud").status_code == 503
    assert c.get("/api/v4/filas").status_code == 503
