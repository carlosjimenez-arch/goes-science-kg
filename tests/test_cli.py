"""Compatibilidad de los comandos públicos al reorganizar la interfaz de terminal.

El contrato se capturó antes de dividir la CLI; admite nuevos comandos, pero evita
romper scripts existentes y comprueba que la ayuda no ejecute trabajo de dominio.
"""

from pathlib import Path

import pytest
from typer.main import get_command
from typer.testing import CliRunner

from goes_science_kg.cli import app

CONTRATO = Path(__file__).parent / "contracts" / "cli_v1.txt"
COMANDOS = tuple(linea.split() for linea in CONTRATO.read_text(encoding="utf-8").splitlines() if linea)
GRUPOS = sorted({partes[0] for partes in COMANDOS if len(partes) > 1})


def _rutas(comando, prefijo: tuple[str, ...] = ()) -> set[tuple[str, ...]]:
    hijos = getattr(comando, "commands", None)
    if hijos is None:
        return {prefijo}
    return {ruta for nombre, hijo in hijos.items() for ruta in _rutas(hijo, (*prefijo, nombre))}


def test_catalogo_publico_anterior_sigue_disponible():
    """Toda ruta histórica sigue resolviendo; nuevas capacidades pueden ampliarla."""
    assert {tuple(partes) for partes in COMANDOS} <= _rutas(get_command(app))


@pytest.mark.parametrize(
    "partes", [(), *((grupo,) for grupo in GRUPOS), *COMANDOS], ids=lambda p: " ".join(p) or "gskg"
)
def test_ayuda_publica_resuelve_sin_ejecutar_comandos(partes):
    """La ayuda atraviesa todos los grupos y conserva el parser sin necesitar datos ni red."""
    resultado = CliRunner().invoke(app, [*partes, "--help"])
    assert resultado.exit_code == 0, resultado.output
    assert "Usage:" in resultado.output
