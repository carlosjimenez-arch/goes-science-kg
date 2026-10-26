"""`gskg servir` escucha en loopback y no deja que uvicorn registre valores de consulta."""

from __future__ import annotations

import sys
import types

import pytest
from typer.testing import CliRunner

from goes_science_kg.cli import app


@pytest.fixture
def uvicorn_falso(monkeypatch):
    llamadas = []
    monkeypatch.setitem(sys.modules, "uvicorn", types.SimpleNamespace(run=lambda *a, **k: llamadas.append((a, k))))
    return llamadas


def test_servir_desactiva_el_access_log_en_loopback(uvicorn_falso):
    resultado = CliRunner().invoke(app, ["servir", "--puerto", "8123"])
    assert resultado.exit_code == 0, resultado.output
    ((args, kwargs),) = uvicorn_falso
    assert kwargs == {"host": "127.0.0.1", "port": 8123, "access_log": False}


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.10", "servidor.local"])
def test_servir_en_red_exige_permiso_explicito(uvicorn_falso, host):
    resultado = CliRunner().invoke(app, ["servir", "--host", host])
    assert resultado.exit_code != 0 and not uvicorn_falso
    assert CliRunner().invoke(app, ["servir", "--host", host, "--permitir-red"]).exit_code == 0
    assert uvicorn_falso[-1][1]["host"] == host
