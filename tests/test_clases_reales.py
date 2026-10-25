"""Verificación sin llamadas: guiones reales frente a respuestas del proveedor y código congelado."""

from __future__ import annotations

import json
from copy import deepcopy

import pytest

from goes_science_kg.clases.auditoria import verificar_trazas
from goes_science_kg.clases.validacion import certificar_resultado
from goes_science_kg.config import ruta
from goes_science_kg.motor.registro import Registro

BASE = ruta(".")
pytestmark = pytest.mark.skipif(
    not (BASE / "data/clases_v4/seleccion_pilotos.json").is_file(), reason="Guiones privados no restaurados"
)


def _expedientes(nombre):
    seleccion = json.loads((BASE / "data/clases_v4" / nombre).read_bytes())
    vistos = set()
    for id_, ref in seleccion.items():
        if ref["resultado"] in vistos:
            continue
        vistos.add(ref["resultado"])
        p = json.loads((BASE / ref["preparacion"]).read_bytes())
        r = json.loads((BASE / ref["resultado"]).read_bytes())
        yield id_, ref, p, r


def test_pilotos_tienen_24_objetivos_y_lecturas_reales_con_el_contexto_exacto():
    sel = json.loads((BASE / "data/clases_v4/seleccion_pilotos.json").read_bytes())
    assert len(sel) == 24
    registro = Registro(BASE / "data/operaciones/registro.sqlite")
    for _, ref, p, r in _expedientes("seleccion_pilotos.json"):
        certificar_resultado(r, p)
        a = verificar_trazas(BASE, BASE / ref["resultado"], p, r, registro)
        assert a["trazas"]
        assert all(t["llamadas"] and t["salida_sha256"] for t in a["trazas"])


def test_adulterar_historia_y_terminal_juntos_no_puede_fabricar_un_dictamen():
    id_, ref, p, r = next(_expedientes("seleccion_pilotos.json"))
    r = deepcopy(r)
    final = r["filas"][id_]
    ronda = r["rondas"][final["ronda_seleccionada"] - 1]
    dictamen = final["dictamenes"][0]
    lector = ronda["lectores"][dictamen["rol"]]
    fila = next(f for f in lector["lectura"]["filas"] if f["fila_id"] == id_)
    fila["hallazgos"].append("Afirmación añadida manualmente y ausente de la respuesta real del proveedor.")
    dictamen["lectura"] = deepcopy(fila)
    certificar_resultado(r, p)  # La coherencia interna por sí sola no prueba una revisión real.
    with pytest.raises(ValueError, match="respuesta real"):
        verificar_trazas(BASE, BASE / ref["resultado"], p, r, Registro(BASE / "data/operaciones/registro.sqlite"))
