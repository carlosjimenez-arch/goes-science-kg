"""Test operational recovery with real SQLite workflows and strictly offline providers."""

from __future__ import annotations

import pytest
from google.auth.exceptions import TransportError
from test_unidades import _motor, _preparar
from test_unidades import entrega as entrega

from goes_science_kg.operacion.recuperacion_unidad import recuperar_unidad_sin_respuesta
from goes_science_kg.producto.unidades import ejecutar_unidad


def _fallar(motor):
    modelo = motor.modelo
    generar = modelo.generar

    def sin_transporte(**kwargs):
        llamada = modelo.registro.reservar(
            ejecucion=modelo.ejecucion_id,
            clave="transporte-sintetico",
            modelo=modelo.nombre_modelo(kwargs["rol"]),
            rol=kwargs["rol"],
            reserva_usd=0.001,
            max_llamadas=modelo.configuracion.max_llamadas,
            max_usd=modelo.configuracion.max_usd,
        )
        modelo.registro.terminar(llamada, estado="fallida", latencia_ms=1)
        raise TransportError("Transporte simulado sin invocar SDK ni ADC")

    modelo.generar = sin_transporte
    return generar


def _original(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    generar = _fallar(motor)
    original = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    motor.modelo.generar = generar
    return paquete, motor, registro, original


def _recuperar(entrega, paquete, motor, registro, original):
    return recuperar_unidad_sin_respuesta(
        paquete,
        original,
        motor=motor,
        registro=registro,
        directorio_operaciones=entrega[3] / "operaciones",
    )


def test_recupera_con_mismo_presupuesto_sin_borrar_terminales_y_reanuda_sin_modelos(entrega):
    paquete, motor, registro, original = _original(entrega)
    antes = original.model_dump_json()
    recuperada = _recuperar(entrega, paquete, motor, registro, original)
    assert recuperada.cobertura["respaldadas"] == 2
    assert recuperada.consumo_antes["llamadas"] == 2 and recuperada.consumo_despues["llamadas"] == 10
    assert recuperada.limites_presupuesto == original.limites_presupuesto
    assert original.model_dump_json() == antes
    assert all(s.thread_id.endswith(":transporte-1") for s in recuperada.sesiones)

    def prohibido(**kwargs):
        pytest.fail("Un terminal recuperado no vuelve a generar")

    motor.modelo.generar = prohibido
    segunda = _recuperar(entrega, paquete, motor, registro, original)
    assert segunda.consumo_incremental == {"llamadas": 0, "reserva_usd": 0}
    intacta = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    assert intacta.cobertura["abstenciones"] == 2 and intacta.consumo_incremental["llamadas"] == 0


def test_no_repite_votos_ni_respuestas_ya_recibidas(entrega):
    paquete = _preparar(entrega)
    motor, registro = _motor(entrega)
    original = ejecutar_unidad(
        paquete,
        motor=motor,
        registro=registro,
        ejecucion_id="unidad-prueba",
        directorio_operaciones=entrega[3] / "operaciones",
    )
    antes = registro.resumen("unidad-prueba")
    with pytest.raises(ValueError, match="sin respuestas ni votos"):
        _recuperar(entrega, paquete, motor, registro, original)
    assert registro.resumen("unidad-prueba") == antes


def test_no_acepta_original_falsificado_aunque_su_esquema_sea_valido(entrega):
    paquete, motor, registro, original = _original(entrega)
    resultado = original.sesiones[0].resultado_motor.model_copy(update={"iteraciones": 2})
    falsa = original.model_copy(
        update={
            "sesiones": (original.sesiones[0].model_copy(update={"resultado_motor": resultado}), original.sesiones[1])
        }
    )
    with pytest.raises(ValueError, match="terminales originales"):
        _recuperar(entrega, paquete, motor, registro, falsa)
    assert registro.resumen("unidad-prueba")["llamadas"] == 2


def test_fallo_de_transporte_en_recuperacion_corta_el_resto_sin_reintentos_ocultos(entrega):
    paquete, motor, registro, original = _original(entrega)
    _fallar(motor)
    resultado = _recuperar(entrega, paquete, motor, registro, original)
    assert resultado.cobertura["abstenciones"] == 1 and resultado.cobertura["no_ejecutadas"] == 1
    assert resultado.consumo_despues["llamadas"] == 3
    repetida = _recuperar(entrega, paquete, motor, registro, original)
    assert repetida.consumo_incremental["llamadas"] == 0


def test_fuente_cambiada_impide_recuperar_antes_de_generar(entrega):
    paquete, motor, registro, original = _original(entrega)
    archivo = entrega[3] / "fisica.xlsx"
    archivo.write_bytes(archivo.read_bytes() + b"cambio")
    with pytest.raises(ValueError, match="cambió"):
        _recuperar(entrega, paquete, motor, registro, original)
    assert registro.resumen("unidad-prueba")["llamadas"] == 2


def test_cambio_de_limites_no_amplia_presupuesto_en_recuperacion(entrega):
    paquete, motor, registro, original = _original(entrega)
    motor.modelo.configuracion = motor.modelo.configuracion.model_copy(update={"max_llamadas": 21})
    with pytest.raises(ValueError, match="límites originales"):
        _recuperar(entrega, paquete, motor, registro, original)
    assert registro.resumen("unidad-prueba")["llamadas"] == 2
