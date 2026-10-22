"""Correspondencia integral de la biblioteca congelada, cuando su corpus está restaurado."""

from __future__ import annotations

import json
from collections import Counter

import pytest

from goes_science_kg.api_producto import _LecturaProducto
from goes_science_kg.config import ruta
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import BANCOS, sha

BASE = ruta(".")
pytestmark = pytest.mark.skipif(
    not (BASE / "data/materiales/manifest.json").is_file(), reason="Biblioteca privada no restaurada"
)


def test_todas_las_propuestas_originales_y_cuatro_votos_corresponden_exactamente():
    runtime = _LecturaProducto(BASE, BASE / "data/producto/V4").leer()
    b = Biblioteca(BASE / "data/materiales")
    assert b.validar()["procedencia"]["snapshot_id"] == runtime.producto.manifest.snapshot_id
    conteo = Counter()
    ids = set()
    for caso in runtime.producto.mejoras.unidades:
        assert caso.resultado.estado == "respaldado_automaticamente"
        for propuesta in caso.resultado.propuesta.filas:
            d = b.detalle(propuesta.fila_id)
            assert d["documento"]["propuesta"] == propuesta.model_dump(mode="json")
            assert d["documento"]["revisiones"]["dictamenes"] == [
                v.model_dump(mode="json") for v in caso.resultado.rondas[-1].dictamenes
            ]
            assert len(d["documento"]["revisiones"]["dictamenes"]) == 4
            assert d["tipo"] == ("fila_fuera_alcance" if propuesta.accion == "fuera_alcance" else "paquete_objetivo")
            assert d["documento"]["fuente_original"]["sha256"]
            assert not d["documento"]["guion_cronometrado"]
            assert d["documento"]["duracion_minutos"] is None
            assert not d["documento"]["material_historico_trasladado"]
            ids.add(d["id"])
            conteo[d["tipo"]] += 1
        u = b.detalle("UNIDAD-DOCENTE:" + caso.preparacion.id)
        assert u["documento"]["filas_ids"] == [f["id"] for f in caso.preparacion.filas_originales]
    assert ids == {f.id for f in runtime.producto.curriculo.filas}
    for fila in runtime.producto.curriculo.filas:
        d = b.detalle(fila.id)["documento"]
        assert d["celdas_originales"] == [c.model_dump(mode="json") for c in fila.celdas]
        assert d["original"] == fila.model_dump(mode="json", exclude={"celdas"})
    assert conteo == {"paquete_objetivo": 1013, "fila_fuera_alcance": 7}


def test_todos_los_historicos_y_originales_se_preservan_byte_a_byte():
    b = Biblioteca(BASE / "data/materiales")
    for nombre, esperado in b.manifest["originales"].items():
        contenido, rutas = b.archivo(esperado["sha256"])
        assert nombre in rutas
        assert contenido == (BASE / nombre).read_bytes()
        assert len(contenido) == esperado["bytes"]
    for banco, tipo in BANCOS.items():
        elementos = json.loads((BASE / f"data/pedagogia/{banco}.json").read_bytes())
        assert b.listar(version="historico", tipo=tipo)["total"] == len(elementos)
        for elemento in elementos:
            d = b.detalle("HIST:" + elemento["id"])
            assert d["documento"]["original"] == elemento
            assert d["estado"] == elemento["estado"]
            assert not d["documento"]["migrado_a_v4"]
    paquetes = sorted((BASE / "entregas/paquetes_clase").glob("*.json"))
    assert len(paquetes) == b.listar(version="V3")["total"] == 150
    for p in paquetes:
        original = json.loads(p.read_bytes())
        assert b.detalle("V3:" + original["tema"]["id"])["documento"]["original"] == original
    ledger = BASE / "data/operaciones/registro.sqlite"
    assert sha(ledger.read_bytes()) == b.manifest["procedencia"]["ledger_sha256"]
    assert sha(ledger.read_bytes()) == "3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae"
