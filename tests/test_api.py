import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from goes_science_kg.api import app  # noqa: E402

cliente = TestClient(app)


def test_salud_del_grafo_no_afirma_procedencia_de_derivados():
    r = cliente.get("/api/salud")
    assert r.status_code == 200 and r.json()["alcance"] == "grafo"
    assert r.json()["derivados"] == "requieren_publicacion_por_articulo"
    assert set(r.json()["manifest"]["sha256"]) == {"nodos.jsonl", "aristas.jsonl"}


def test_grado_y_concepto():
    # El contrato 200 de grados se verifica con su generador en test_api_publicacion.
    assert cliente.get("/api/grados/13").status_code == 404
    c = cliente.get("/api/conceptos/biologia/fotosintesis")
    assert c.status_code == 200 and c.json()["temas_sv"]


def test_rag():
    r = cliente.get("/api/rag", params={"q": "fotosíntesis y respiración", "grado": 6, "k": 10})
    assert r.status_code == 200 and len(r.json()["nodos"]) == 10
    assert cliente.get("/api/rag", params={"q": "x"}).status_code == 422


def test_equivalentes_en_los_dos_sentidos():
    """EQUIVALE_A se guarda en un sentido (a → b), pero la API la muestra desde los dos conceptos."""
    a = cliente.get("/api/conceptos/fisica/modelo-particulas").json()
    b = cliente.get("/api/conceptos/quimica/modelo-de-particulas").json()
    assert "CON:quimica/modelo-de-particulas" in {x["id"] for x in a["equivalentes"]}
    assert "CON:fisica/modelo-particulas" in {x["id"] for x in b["equivalentes"]}
