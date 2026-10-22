"""La simulación no puede ahorrar tiempo eliminando objetivos ni suponer recursos ausentes."""

from __future__ import annotations

import json

import pytest
from test_unidades import _preparar
from test_unidades import entrega as entrega
from typer.testing import CliRunner

from goes_science_kg.cli.producto import app
from goes_science_kg.producto.escenarios import EscenarioUnidad, RequisitoSesion, evaluar_escenario
from goes_science_kg.producto.unidades import ContextoAula, exportar_unidad


@pytest.fixture
def preparado(entrega):
    paquete = _preparar(entrega)
    requisitos = tuple(
        RequisitoSesion(
            fila_id=f.id,
            bloques_propuestos=2,
            recursos_necesarios=("papel", "lápiz", "regla"),
            justificacion_propuesta="Hipótesis operativa de dos bloques; no es duración validada.",
        )
        for f in paquete.filas
    )
    escenario = EscenarioUnidad(
        nombre="Escenario de prueba",
        paquete_id=paquete.id,
        aula_declarada=ContextoAula(recursos=("papel", "lapiz")),
        minutos_disponibles=80,
        requisitos=requisitos,
    )
    return paquete, escenario


def test_no_inventa_instrumentos_ni_ahorra_tiempo_omitiendo_filas(preparado):
    p, e = preparado
    r = evaluar_escenario(p, e)
    assert r["estado"] == "restricciones_incumplidas"
    assert r["deficit_minutos"] == 80 and r["filas_conservadas"] == 2
    assert [s["recursos_faltantes"] for s in r["sesiones"]] == [["regla"], ["regla"]]
    assert r["llamadas_modelos"] == 0


def test_satisfacer_restricciones_no_declara_respaldo_pedagogico(preparado):
    p, e = preparado
    e = e.model_copy(
        update={"minutos_disponibles": 160, "aula_declarada": ContextoAula(recursos=("papel", "lapiz", "regla"))}
    )
    r = evaluar_escenario(p, e)
    assert r["estado"] == "restricciones_declaradas_satisfechas"
    assert "respaldado_automaticamente" not in json.dumps(r)
    assert r["filas_conservadas"] == len(p.filas)


@pytest.mark.parametrize("cambio", ["omitir", "duplicar", "otra_fila", "otro_paquete"])
def test_escenario_no_puede_ocultar_objetivos_o_cambiar_identidad(preparado, cambio):
    p, e = preparado
    if cambio == "omitir":
        e = e.model_copy(update={"requisitos": e.requisitos[:1]})
    elif cambio == "duplicar":
        e = e.model_copy(update={"requisitos": (e.requisitos[0], e.requisitos[0])})
    elif cambio == "otra_fila":
        e = e.model_copy(
            update={"requisitos": (e.requisitos[0], e.requisitos[1].model_copy(update={"fila_id": "ajena"}))}
        )
    else:
        e = e.model_copy(update={"paquete_id": "b" * 64})
    with pytest.raises(ValueError):
        evaluar_escenario(p, e)


def test_cli_no_sobrescribe_inputs_y_evalua_sin_proveedor(preparado, tmp_path):
    p, e = preparado
    exportar_unidad(p, tmp_path)
    escenario = tmp_path / "escenario.json"
    escenario.write_text(e.model_dump_json())
    args = ["escenario", str(tmp_path / "paquete.json"), str(escenario)]
    original = escenario.read_bytes()
    r = CliRunner().invoke(app, [*args, "--salida", str(escenario)])
    assert r.exit_code != 0 and escenario.read_bytes() == original
    resultado = tmp_path / "resultado.json"
    r = CliRunner().invoke(app, [*args, "--salida", str(resultado)])
    assert r.exit_code == 0, r.output
    assert json.loads(resultado.read_bytes())["deficit_minutos"] == 80
