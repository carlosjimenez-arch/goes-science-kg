"""El cliente Vertex histórico exige tope declarado y sólo reintenta errores transitorios."""

from __future__ import annotations

import json

import pytest

from goes_science_kg.internacional import vertex


class ErrorApi(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def test_sin_tope_declarado_no_paga_ninguna_llamada(monkeypatch):
    monkeypatch.delenv("VERTEX_MAX_CALLS", raising=False)
    with pytest.raises(vertex.PresupuestoAgotadoError, match="VERTEX_MAX_CALLS"):
        vertex._Contador().reservar()
    monkeypatch.setenv("VERTEX_MAX_CALLS", "1")
    contador = vertex._Contador()
    contador.reservar()
    with pytest.raises(vertex.PresupuestoAgotadoError):
        contador.reservar()


@pytest.mark.parametrize(
    ("error", "reintenta"),
    [
        (ErrorApi(429), True),
        (ErrorApi(503), True),
        (ErrorApi(400), False),
        (ErrorApi(403), False),
        (json.JSONDecodeError("truncado", "{", 1), True),
        (TimeoutError(), True),
        (ValueError("esquema"), False),
    ],
)
def test_solo_reintenta_errores_transitorios(error, reintenta):
    assert vertex._reintentable(error) is reintenta
