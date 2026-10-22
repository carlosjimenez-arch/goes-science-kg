"""Preparación, ejecución durable simulada y consolidación real por CLI; sin red ni credenciales."""

from __future__ import annotations

import copy
import json

import pytest
from test_juicios_conocimiento import LectoresSimulados, entrada
from typer.testing import CliRunner

from goes_science_kg.cli import juicios
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.registro import Registro
from goes_science_kg.producto._juicios_contratos import ROLES_CONOCIMIENTO


@pytest.fixture
def interfaz(tmp_path, monkeypatch):
    e = entrada(tmp_path)
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    cfg = dict(
        candidatos="data/candidatos.json",
        grafo_historico="data/grafo",
        raiz_historica="data/fuentes",
        raiz_v4="insumos/v4",
        alertas="docs/alertas.json",
        registro="data/operaciones/registro.sqlite",
        checkpoints="data/operaciones/checkpoints.sqlite",
        log="data/operaciones/log.log",
        max_caracteres=24000,
        max_concurrencia=4,
        max_llamadas=4,
        max_usd=0.4,
        reintentos=0,
        roles_vertex={r: r for r in ROLES_CONOCIMIENTO},
    )
    motor_cfg = {
        "vertex": dict(
            proyecto="proyecto-sintetico",
            region="global",
            modelos={r: "simulado-" + r for r in ROLES_CONOCIMIENTO},
            tarifas={"simulado-" + r: {"entrada": 1, "salida": 2} for r in ROLES_CONOCIMIENTO},
            max_llamadas=4,
            max_usd=0.4,
        )
    }
    monkeypatch.setattr(
        juicios, "cargar", lambda nombre: copy.deepcopy(cfg if nombre == "juicios_conocimiento" else motor_cfg)
    )
    monkeypatch.setattr(juicios, "_contexto", lambda *_: e.preparador)
    e.cfg, e.motor_cfg = cfg, motor_cfg
    e.creados = []

    class VertexFalso(LectoresSimulados):
        def __init__(self, configuracion, registro, ejecucion_id):
            super().__init__()
            self.configuracion, self.registro, self.ejecucion_id = configuracion, registro, ejecucion_id
            e.creados.append(self)

        def generar(self, **kwargs):
            rol = kwargs["rol"]
            reserva = self.registro.reservar(
                ejecucion=self.ejecucion_id,
                clave=huella({"rol": rol, "mensaje": kwargs["mensaje"]}),
                modelo=self.nombre_modelo(rol),
                rol=rol,
                reserva_usd=0.05,
                max_llamadas=self.configuracion.max_llamadas,
                max_usd=self.configuracion.max_usd,
            )
            salida = super().generar(**kwargs)
            self.registro.terminar(reserva, estado="completada", latencia_ms=1)
            return salida

    monkeypatch.setattr("goes_science_kg.motor.vertex.Vertex", VertexFalso)
    return e


def test_default_prepara_sin_proveedor_ni_ledger(interfaz, tmp_path):
    salida = tmp_path / "preparado.json"
    r = CliRunner().invoke(juicios.app, ["evaluar", interfaz.candidato.id, "--salida", str(salida)])
    assert r.exit_code == 0, r.output
    assert json.loads(salida.read_bytes())["fase"] == "preparacion_local"
    assert interfaz.creados == [] and not (tmp_path / interfaz.cfg["registro"]).exists()


def test_ejecucion_reanudacion_y_consolidacion_no_duplican_gasto(interfaz, tmp_path):
    salida, coleccion = tmp_path / "resultado.json", tmp_path / "coleccion.json"
    argumentos = ["evaluar", interfaz.candidato.id, "--ejecutar", "--ejecucion", "uno", "--salida", str(salida)]
    for _ in range(2):
        r = CliRunner().invoke(juicios.app, argumentos)
        assert r.exit_code == 0, r.output
    datos = json.loads(salida.read_bytes())
    assert datos["resultado"]["estado"] == "respaldado"
    assert datos["workflow"]["resultado"] == datos["resultado"]
    assert Registro(tmp_path / interfaz.cfg["registro"]).resumen("uno")["llamadas"] == 4
    assert sum(len(m.llamadas) for m in interfaz.creados) == 4
    r = CliRunner().invoke(juicios.app, ["consolidar", str(salida), "--salida", str(coleccion)])
    assert r.exit_code == 0, r.output
    datos = json.loads(coleccion.read_bytes())
    assert len(datos["coleccion"]["relaciones_admisibles"]) == 1
    assert datos["coleccion"]["proyeccion_dependencias"]["estado"] == "sin_prerrequisitos_respaldados"
    assert datos["evidencias"] and datos["expedientes"] and datos["fuentes"]
    assert len(interfaz.creados) == 2  # Consolidar no instancia otro proveedor.


@pytest.mark.parametrize("campo", ["registro", "checkpoints", "log"])
@pytest.mark.parametrize("input_", ["candidatos", "soportes"])
def test_ninguna_salida_puede_corromper_inputs(interfaz, tmp_path, campo, input_):
    argumentos = ["evaluar", interfaz.candidato.id, "--ejecutar", "--salida", str(tmp_path / "salida.json")]
    if input_ == "candidatos":
        interfaz.cfg[campo] = interfaz.cfg["candidatos"]
    else:
        argumentos += ["--soportes", str(tmp_path / interfaz.cfg[campo])]
    r = CliRunner().invoke(juicios.app, argumentos)
    assert r.exit_code != 0 and "destinos distintos" in r.output
    assert interfaz.creados == []


def test_consolidar_no_acepta_preparaciones(interfaz, tmp_path):
    archivo = tmp_path / "preparado.json"
    archivo.write_text(json.dumps({"fase": "preparacion_local"}))
    r = CliRunner().invoke(juicios.app, ["consolidar", str(archivo), "--salida", str(tmp_path / "coleccion.json")])
    assert r.exit_code != 0 and interfaz.creados == []


@pytest.mark.parametrize("salida", ["data/fuentes/salida.json", "data/grafo/salida.json", "config/salida.json"])
def test_destinos_protegidos_antes_de_contexto(interfaz, tmp_path, monkeypatch, salida):
    def prohibido(*_):
        raise AssertionError("No debe leer contexto antes de validar destino")

    monkeypatch.setattr(juicios, "_contexto", prohibido)
    r = CliRunner().invoke(juicios.app, ["evaluar", interfaz.candidato.id, "--ejecutar", "--salida", salida])
    assert r.exit_code != 0 and interfaz.creados == []


def test_consolidacion_inconsistente_no_acepta_resultado_visible(interfaz, tmp_path):
    archivo = tmp_path / "resultado.json"
    archivo.write_text(
        json.dumps(
            {
                "fase": "juicio_semantico",
                "resultado": {"estado": "respaldado"},
                "workflow": {"resultado": {"estado": "abstencion"}},
            }
        )
    )
    r = CliRunner().invoke(juicios.app, ["consolidar", str(archivo), "--salida", str(tmp_path / "coleccion.json")])
    assert r.exit_code != 0 and "no corresponden" in r.output


def test_medicion_contexto_no_instancia_proveedor_ni_modifica_el_presupuesto(interfaz, tmp_path):
    salida = tmp_path / "medicion.json"
    original = interfaz.preparador.max_caracteres
    r = CliRunner().invoke(
        juicios.app, ["medir-contexto", "--presupuesto", "18000", "--presupuesto", "24000", "--salida", str(salida)]
    )
    assert r.exit_code == 0, r.output
    datos = json.loads(salida.read_bytes())
    assert datos["candidatos"] == 1 and datos["modelos_ejecutados"] == 0
    assert [p["max_caracteres"] for p in datos["presupuestos"]] == [18000, 24000]
    assert all(p["estados"] == {"preparado": 1} for p in datos["presupuestos"])
    assert interfaz.preparador.max_caracteres == original
    assert interfaz.creados == [] and not (tmp_path / interfaz.cfg["registro"]).exists()


def test_medicion_contexto_restaura_presupuesto_tras_error_de_preparacion(interfaz, monkeypatch):
    from goes_science_kg.producto.medicion_contexto import medir_contexto_paises

    original = interfaz.preparador.max_caracteres

    def falla(*_):
        raise ValueError("Fuente cambiada durante la medición")

    monkeypatch.setattr(interfaz.preparador, "preparar", falla)
    with pytest.raises(ValueError, match="Fuente cambiada"):
        medir_contexto_paises(interfaz.preparador, [18000])
    assert interfaz.preparador.max_caracteres == original
