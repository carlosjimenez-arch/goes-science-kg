"""Recover a rejected remote schema without weakening local checks or returning spent attempts."""

from __future__ import annotations

import copy

import pytest
from test_campanas_vertex_proveedor import _cliente, _crear, _generar, _recibo
from test_campanas_vertex_proveedor import datos as datos
from test_clases import guion

from goes_science_kg.campanas_vertex.contratos import esquema_transporte, plazas_disponibles
from goes_science_kg.campanas_vertex.proveedor import preflight, preparar_solicitud
from goes_science_kg.clases.contratos import GuionClase
from goes_science_kg.motor.registro import PresupuestoAgotado


def _una_plaza(datos):
    """Authorize only the remaining paid attempt in a synthetic replacement plan."""
    datos.plan["componentes"][0]["plazas_disponibles"] = 1
    datos.plan["max_llamadas"] = 1
    _recibo(datos.plan, datos.autorizacion)


def test_transporte_compacto_quita_cotas_remotas_y_mantiene_validacion_local():
    transporte = esquema_transporte(GuionClase)
    remotos_omitidos = {"minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum", "default", "title"}

    def comprobar(nodo):
        if isinstance(nodo, dict):
            assert not (set(nodo) & remotos_omitidos)
            for hijo in nodo.values():
                comprobar(hijo)
        elif isinstance(nodo, list):
            for hijo in nodo:
                comprobar(hijo)

    comprobar(transporte.model_json_schema())
    original = guion().model_dump(mode="json")
    assert transporte.model_validate(original).fila_id == "fila1"
    for mutacion in ("titulo", "tiempo", "cantidad_tareas"):
        invalido = copy.deepcopy(original)
        if mutacion == "titulo":
            invalido["titulo"] = "x"
        elif mutacion == "tiempo":
            invalido["sesiones"][0]["bloques"][0]["minutos"] = 1
        else:
            invalido["tareas"] = invalido["tareas"][:1]
        with pytest.raises(ValueError):
            transporte.model_validate(invalido)


@pytest.mark.parametrize("valor", [0, 3, True, 1.0, "1", None])
def test_plazas_disponibles_solo_admite_uno_o_dos_enteros(valor):
    with pytest.raises(ValueError):
        plazas_disponibles({"plazas_disponibles": valor})


def test_preflight_de_recuperacion_reserva_solo_una_llamada_por_componente(datos):
    _una_plaza(datos)
    resultado = preflight(datos.plan, {datos.id: datos.contexto}, {datos.tipo: datos.sistema})
    solicitud = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    assert resultado["llamadas_maximas"] == 1
    assert resultado["reserva_maxima_usd"] == solicitud["reserva_usd"]
    assert resultado["detalle"][0]["reserva_segunda_plaza_usd"] == 0


def test_preflight_mixto_suma_las_plazas_reales_sin_reponerlas(datos):
    inicial = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    extra = copy.deepcopy(datos.plan["componentes"][0]) | {"id": "guia:unidad2", "plazas_disponibles": 1}
    datos.plan["componentes"].append(extra)
    datos.plan["max_llamadas"] = 3
    datos.plan["max_reserva_usd"] = 10
    resultado = preflight(
        datos.plan, {datos.id: datos.contexto, extra["id"]: datos.contexto}, {datos.tipo: datos.sistema}
    )
    assert resultado["llamadas_maximas"] == 3
    assert [r["plazas_disponibles"] for r in resultado["detalle"]] == [2, 1]
    assert resultado["reserva_maxima_usd"] > inicial["reserva_usd"] * 2


def test_proveedor_y_presupuesto_bloquean_otra_plaza_incluso_tras_fallo_tecnico(datos):
    _una_plaza(datos)
    cliente, llamadas = _cliente(error=RuntimeError("400 sintético sin respuesta"))
    proveedor = _crear(datos, cliente)
    with pytest.raises(RuntimeError, match="400 sintético"):
        _generar(proveedor, datos)
    with pytest.raises(ValueError, match="otra plaza"):
        _generar(proveedor, datos, ronda=1, anterior=None, hallazgos=["Intento técnico ya agotado"])
    with pytest.raises(ValueError, match="otra plaza"):
        proveedor.presupuesto.autorizar_reserva(
            clave="otro", modelo="gemini-4-argon", rol=datos.id + ":ronda1", reserva_usd=1
        )
    reanudado = _crear(datos, cliente)
    with pytest.raises(PresupuestoAgotado):
        _generar(reanudado, datos)
    assert len(llamadas) == 1
    assert datos.registro.resumen(datos.plan["campana_id"])["llamadas"] == 1


def test_recuperacion_exitosa_reproduce_sin_consumir_otra_plaza(datos):
    _una_plaza(datos)
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    assert _generar(proveedor, datos).completa is False
    assert _generar(_crear(datos, cliente), datos).completa is False
    with pytest.raises(ValueError, match="otra plaza"):
        _generar(proveedor, datos, ronda=1, anterior=b"otro", hallazgos=["No hay segunda plaza"])
    assert len(llamadas) == 1
