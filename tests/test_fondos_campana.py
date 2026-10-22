"""Admisión paralela sin sobreasignar margen ni descontar consumos históricos."""

from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from goes_science_kg.motor.registro import Registro
from goes_science_kg.operacion.fondos import FondosCampana


def test_segunda_unidad_espera_fondos_y_respeta_consumo_persistido(tmp_path):
    registro = Registro(tmp_path / "registro.sqlite")
    fondos = FondosCampana(registro, "unico", max_llamadas=2, max_usd=2)
    cota = {"max_llamadas": 2, "max_reserva_usd": 2}
    intentando = Event()
    entro = Event()

    def segunda():
        intentando.set()
        with fondos.unidad("segunda", cota):
            entro.set()

    with ThreadPoolExecutor(max_workers=1) as pool:
        with fondos.unidad("primera", cota):
            futuro = pool.submit(segunda)
            assert intentando.wait(2)
            assert not entro.is_set()
        futuro.result(timeout=2)
    assert entro.is_set() and fondos.pendientes == {}
    registro.reservar(
        ejecucion="unico", clave="a", modelo="simulado", rol="redactor", reserva_usd=1, max_llamadas=2, max_usd=2
    )
    with pytest.raises(ValueError, match="safe_to_start=false"):
        with fondos.unidad("no_cabe", cota):
            pytest.fail("No debe admitir más trabajo")
    assert registro.resumen("unico")["llamadas"] == 1


def test_excepcion_libera_margen_sin_borrar_reservas(tmp_path):
    registro = Registro(tmp_path / "registro.sqlite")
    fondos = FondosCampana(registro, "unico", max_llamadas=1, max_usd=1)
    with pytest.raises(RuntimeError):
        with fondos.unidad("primera", {"max_llamadas": 1, "max_reserva_usd": 1}):
            raise RuntimeError("Fallo sintético")
    assert fondos.pendientes == {}
    with fondos.unidad("segunda", {"max_llamadas": 1, "max_reserva_usd": 1}):
        pass
