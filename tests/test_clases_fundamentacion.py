"""El respaldo declarado no permite inventar citas ni omitir tareas."""

import json
from copy import deepcopy

import pytest

from goes_science_kg.clases.fundamentacion import RevisionFundamentada, revisar, validar


@pytest.fixture
def datos():
    cita = "Atoms are conserved in a chemical reaction."
    guion = {
        "fila_id": "f1",
        "explicacion_docente": [{"texto": cita, "fuentes_ids": ["e1"]}] * 2,
        "tareas": [{}, {}],
    }
    preparacion = {
        "id": "p1",
        "escenario": {},
        "filas": [{"fila_id": "f1", "fuentes_cientificas_ids": ["e1", "e2"]}],
        "fuentes": [{"id": "e1", "texto": "<p>" + cita + "</p>"}, {"id": "e2", "texto": cita}],
    }
    lectura = {
        "fila_id": "f1",
        "afirmaciones": [
            {
                "indice": n,
                "veredicto": "si",
                "respaldos": [{"fuente_id": "e1", "cita": cita}],
                "fundamento": "La afirmación expresa el mismo principio que el pasaje literal.",
            }
            for n in range(2)
        ],
        "tareas": [
            {
                "indice": n,
                "veredicto": "si",
                "comprobacion": "La solución compara igual número de átomos antes y después.",
            }
            for n in range(2)
        ],
        "coherencia_global": "si",
        "hallazgos": [],
    }
    return preparacion, guion, lectura


@pytest.mark.parametrize("fallo", ["cita", "fuente", "omision", "repeticion", "sin_respaldo"])
def test_rechaza_respaldos_falsos_y_cobertura_incompleta(datos, fallo):
    p, g, r = datos
    if fallo == "cita":
        r["afirmaciones"][0]["respaldos"][0]["cita"] = "Matter is always lost in a chemical reaction."
    elif fallo == "fuente":
        r["afirmaciones"][0]["respaldos"][0]["fuente_id"] = "e2"
    elif fallo == "omision":
        g["tareas"].append({})
    elif fallo == "repeticion":
        r["tareas"][1]["indice"] = 0
    else:
        r["afirmaciones"][0]["respaldos"] = []
    with pytest.raises(ValueError):
        validar(RevisionFundamentada.model_validate(r), g, p)


class Proveedor:
    def __init__(self, respuesta):
        self.respuesta, self.llamadas = respuesta, 0

    def generar(self, **kwargs):
        self.llamadas += 1
        return RevisionFundamentada.model_validate(self.respuesta)


def test_reanuda_sin_llamadas_y_detecta_respuesta_cambiada(datos, tmp_path):
    p, g, r = datos
    proveedor = Proveedor(r)
    terminal = revisar(p, g, proveedor, tmp_path)
    assert terminal["favorable"] and not terminal["error"]
    assert revisar(p, g, proveedor, tmp_path) == terminal and proveedor.llamadas == 1
    archivo = tmp_path / "respuesta.json"
    archivo.write_bytes(archivo.read_bytes() + b" ")
    with pytest.raises(ValueError, match="respuesta.*cambió"):
        revisar(p, g, proveedor, tmp_path)


def test_cita_inventada_bloquea_y_no_se_reintenta(datos, tmp_path):
    p, g, r = datos
    r["afirmaciones"][0]["respaldos"][0]["cita"] = "This invented fragment does not exist in the actual source."
    proveedor = Proveedor(r)
    terminal = revisar(p, g, proveedor, tmp_path)
    assert not terminal["favorable"] and "literalmente" in terminal["error"]
    assert revisar(p, g, proveedor, tmp_path) == terminal and proveedor.llamadas == 1
    archivo = tmp_path / "revision.json"
    alterado = json.loads(archivo.read_bytes())
    alterado.update(favorable=True, error=None)
    archivo.write_text(json.dumps(alterado))
    with pytest.raises(ValueError, match="oculta"):
        revisar(p, g, proveedor, tmp_path)


def test_un_hallazgo_material_no_puede_rotularse_favorable(datos):
    p, g, r = datos
    r = deepcopy(r)
    r["hallazgos"] = ["Hay un error material que debe impedir la publicación."]
    with pytest.raises(ValueError, match="hallazgos"):
        validar(RevisionFundamentada.model_validate(r), g, p)
