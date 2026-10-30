from __future__ import annotations

from multiprocessing import get_context

import pytest
from test_campanas_vertex_proveedor import _cliente, _crear, _generar
from test_campanas_vertex_proveedor import datos as datos

from goes_science_kg.campanas_vertex.presupuesto import PresupuestoCampana
from goes_science_kg.motor.registro import PresupuestoAgotado


def test_fallo_de_persistencia_externa_no_permite_llamada_ni_adopcion(monkeypatch, datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)

    def falla(reservas):
        raise OSError("fsync simulado fallido")

    monkeypatch.setattr(proveedor.presupuesto.continuidad, "_escribir", falla)
    with pytest.raises(OSError, match="fsync"):
        _generar(proveedor, datos)
    assert not llamadas
    assert datos.registro.resumen(datos.plan["campana_id"])["llamadas"] == 1
    with pytest.raises(ValueError, match="punto externo"):
        _crear(datos, cliente)


def test_cambiar_reserva_inmutable_bloquea_siguiente_operacion(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    _generar(proveedor, datos)
    with datos.registro.conexion() as db:
        db.execute("UPDATE llamadas SET reserva_usd=0 WHERE ejecucion=?", (datos.plan["campana_id"],))
    with pytest.raises(ValueError, match="punto externo"):
        _generar(proveedor, datos)
    assert len(llamadas) == 1


def _reservar_desde_proceso(plan, autorizacion, archivo, salida):
    try:
        presupuesto = PresupuestoCampana(plan, autorizacion, archivo)
        presupuesto.autorizar_reserva(
            clave="solicitud", modelo="gemini-4-argon", rol=plan["componentes"][0]["id"] + ":ronda0", reserva_usd=1
        )
        salida.put("reservada")
    except PresupuestoAgotado:
        salida.put("bloqueada")
    except Exception as error:
        salida.put(type(error).__name__)


def test_punto_externo_y_reserva_no_compiten_entre_procesos(datos):
    # Fork inherits the synthetic root and continuity verifier; no real credentials or ledger are available.
    contexto = get_context("fork")
    salida = contexto.Queue()
    procesos = [
        contexto.Process(target=_reservar_desde_proceso, args=(datos.plan, datos.autorizacion, datos.archivo, salida))
        for _ in range(4)
    ]
    for proceso in procesos:
        proceso.start()
    for proceso in procesos:
        proceso.join(10)
        assert proceso.exitcode == 0
    estados = [salida.get(timeout=1) for _ in procesos]
    assert estados.count("reservada") == 1 and estados.count("bloqueada") == 3
    presupuesto = PresupuestoCampana(datos.plan, datos.autorizacion, datos.archivo)
    with presupuesto.continuidad.bloqueo():
        presupuesto.continuidad.verificar(datos.registro)
