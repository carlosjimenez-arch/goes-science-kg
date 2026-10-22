"""Test two complete dossiers under one shared counter and an immutable review plan."""

from __future__ import annotations

import json

import pytest
from test_cli_juicios import interfaz as interfaz
from test_conocimiento_v4 import _referencia
from test_juicios_conocimiento import LectoresSimulados
from typer.testing import CliRunner

from goes_science_kg.cli import juicios
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.registro import Registro
from goes_science_kg.producto.conocimiento import generar_candidatos_conocimiento
from goes_science_kg.producto.juicios import PreparadorConocimiento


@pytest.fixture
def lote(interfaz, tmp_path, monkeypatch):
    e = interfaz
    referencia = _referencia(
        *e.referencia.nodos,
        e.objetivo.model_copy(deep=True, update={"id": "otro-objetivo-extranjero"}),
    )
    informe = generar_candidatos_conocimiento(
        e.curriculo,
        referencia,
        raiz_v4=tmp_path / "v4",
        raiz_historica=tmp_path,
        politica=e.informe.politica,
    )
    preparador = PreparadorConocimiento(e.curriculo, informe, referencia, e.fuentes)
    monkeypatch.setattr(juicios, "_contexto", lambda *_: preparador)
    ids = [c.id for c in informe.candidatos if c.tipo == "contraste_pais"]
    assert len(ids) == 2
    seleccion = tmp_path / "seleccion.json"
    seleccion.write_text(json.dumps(ids))
    return e, ids, seleccion, tmp_path / "plan.json", tmp_path / "resultado.json"


def preparar(lote, *, max_llamadas=8):
    _, _, seleccion, plan, _ = lote
    r = CliRunner().invoke(
        juicios.app,
        [
            "preparar-lote",
            str(seleccion),
            "--ejecucion",
            "lote-dos",
            "--max-llamadas",
            str(max_llamadas),
            "--max-usd",
            "0.4",
            "--salida",
            str(plan),
        ],
    )
    assert r.exit_code == 0, r.output


def ejecutar(lote, *, remoto=True):
    _, _, _, plan, resultado = lote
    return CliRunner().invoke(
        juicios.app,
        [
            "ejecutar-lote",
            str(plan),
            "--salida",
            str(resultado),
            *(["--ejecutar"] if remoto else []),
        ],
    )


def test_preparacion_y_verificacion_no_instancian_proveedor(lote, tmp_path):
    preparar(lote)
    r = ejecutar(lote, remoto=False)
    assert r.exit_code == 0, r.output
    assert lote[0].creados == []
    assert not (tmp_path / lote[0].cfg["registro"]).exists()


def test_dos_casos_comparten_presupuesto_y_reanudar_no_gasta(lote, tmp_path):
    preparar(lote)
    for _ in range(2):
        r = ejecutar(lote)
        assert r.exit_code == 0, r.output
    datos = json.loads(lote[-1].read_bytes())
    assert len(datos["workflow"]) == 2
    assert all(e["resultado"]["estado"] == "respaldado" for e in datos["workflow"])
    assert datos["consumo"]["llamadas"] == 8
    assert datos["consumo_incremental"]["llamadas"] == 0
    registro = Registro(tmp_path / lote[0].cfg["registro"])
    with registro.conexion() as db:
        assert db.execute("SELECT DISTINCT ejecucion FROM llamadas").fetchall()[0][0] == "lote-dos"
        assert db.execute("SELECT COUNT(DISTINCT ejecucion) FROM llamadas").fetchone()[0] == 1
    archivo = tmp_path / "coleccion.json"
    r = CliRunner().invoke(juicios.app, ["consolidar", str(lote[-1]), "--salida", str(archivo)])
    assert r.exit_code == 0, r.output
    assert len(json.loads(archivo.read_bytes())["coleccion"]["resultados"]) == 2
    assert sum(len(m.llamadas) for m in lote[0].creados) == 8


def test_no_se_reinicia_el_limite_al_pasar_al_segundo_caso(lote):
    preparar(lote, max_llamadas=4)
    r = ejecutar(lote)
    assert r.exit_code == 0, r.output
    datos = json.loads(lote[-1].read_bytes())
    assert datos["consumo"]["llamadas"] == 4
    assert [e["resultado"]["estado"] for e in datos["workflow"]] == ["respaldado", "abstencion"]
    assert sum(len(m.llamadas) for m in lote[0].creados) == 4


def test_cambiar_orden_del_plan_no_reasigna_la_ejecucion(lote):
    preparar(lote)
    assert ejecutar(lote).exit_code == 0
    plan = json.loads(lote[-2].read_bytes())
    plan["solicitudes"].reverse()
    plan["id"] = huella({k: v for k, v in plan.items() if k != "id"})
    lote[-2].write_text(json.dumps(plan))
    r = ejecutar(lote)
    assert r.exit_code != 0 and "otro plan" in r.output
    assert sum(len(m.llamadas) for m in lote[0].creados) == 8


def test_fuentes_cambiadas_se_rechazan_antes_del_proveedor(lote, tmp_path):
    preparar(lote)
    fuente = tmp_path / "v4" / "malla.xlsx"
    fuente.write_bytes(b"fuente alterada")
    r = ejecutar(lote)
    assert r.exit_code != 0
    assert lote[0].creados == []


def test_consolidar_rechaza_omitir_un_caso_del_lote(lote, tmp_path):
    preparar(lote)
    assert ejecutar(lote).exit_code == 0
    datos = json.loads(lote[-1].read_bytes())
    datos["workflow"].pop()
    lote[-1].write_text(json.dumps(datos))
    r = CliRunner().invoke(juicios.app, ["consolidar", str(lote[-1]), "--salida", str(tmp_path / "coleccion.json")])
    assert r.exit_code != 0 and "todas sus solicitudes" in r.output


def test_cuatro_fallos_detienen_el_lote_sin_gastar_en_el_siguiente_caso(lote, monkeypatch):
    preparar(lote)

    def falla(*args, **kwargs):
        raise RuntimeError("Proveedor de prueba indisponible")

    monkeypatch.setattr(LectoresSimulados, "generar", falla)
    r = ejecutar(lote)
    assert r.exit_code == 0, r.output
    datos = json.loads(lote[-1].read_bytes())
    assert datos["fase"] == "lote_incompleto"
    assert len(datos["workflow"]) == len(datos["sin_ejecutar"]) == 1
    assert datos["consumo"]["llamadas"] == 4
