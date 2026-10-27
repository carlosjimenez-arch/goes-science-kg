"""Cierre acotado: corpus íntegro, votos no transferibles y cero llamadas sin saldo."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.indicadores.cierre import preparar, propuesta_presupuesto, recuperar_fuentes
from goes_science_kg.produccion.revision_docente.contexto import vista_revision
from goes_science_kg.produccion.revision_docente.contratos import ROLES
from goes_science_kg.produccion.revision_docente.ejecucion import ejecutar, guardar, mensaje, proveedor_cfg

BASE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def captura():
    p = BASE / "data/cierre_indicadores_20261027/campana_p1"
    if not (p / "preflight.json").is_file():
        pytest.skip("Preparar la captura de cierre sin Vertex")
    biblioteca = Biblioteca(BASE / "data/materiales_produccion_v4")
    rs, _ = biblioteca.exportar()
    plan = json.loads((p / "preflight.json").read_bytes())
    if biblioteca.manifest["id"] != plan["biblioteca_preparaciones"]:
        pytest.skip("La captura conserva la biblioteca anterior a su revisión")
    return (
        plan,
        json.loads((p / "candidato_1.json").read_bytes()),
        json.loads((p / "ronda_1.json").read_bytes())[0],
        {r["id"]: r for r in rs},
    )


@pytest.mark.parametrize("limite_usd,requiere", [(3500, False), (3300, True)])
def test_propuesta_no_reinicia_consumo_ni_concede_autorizacion(limite_usd, requiere):
    p = propuesta_presupuesto(
        {
            "consumo_inicial": {"llamadas": 3999, "reserva_usd": 3275.614266},
            "primera_pasada_llamadas": 4,
            "max_nuevas_llamadas": 11,
            "max_reserva_nueva_usd": 43.6629726,
        },
        {"max_llamadas_acumuladas": 4000, "max_reserva_usd_acumulada": limite_usd},
    )
    assert p["minimo_max_llamadas_primera_pasada"] == 4003
    assert p["max_llamadas_acumuladas_propuesto"] == 4010
    assert p["aumento_llamadas_recomendado"] == 10
    assert p["reserva_acumulada_max_prevista"] == pytest.approx(3319.2772386)
    assert p["requiere_aumentar_reserva_usd"] is requiere
    assert p["safe_si_se_autorizan_solo_las_llamadas"] is not requiere
    assert p["autorizado"] is False


def fuente(alias, real, texto):
    return {
        "id": alias,
        "identidad_original": real,
        "fragmentos": [texto],
        "texto_visible_sha256": sha(texto.encode()),
        "fuente": {"url": "https://example.org/primaria"},
    }


def test_recuperacion_no_propaga_fuentes_ajenas_ni_corrige_ids_inexistentes():
    a = {
        "fuentes": [fuente("F0", "comun", "Texto común"), fuente("F1", "local_a", "Texto A")],
        "items": [{"id": "I0", "identidad_original": "fila_a", "fuentes_recuperadas_ids": ["F1"]}],
    }
    b = {
        "fuentes": [fuente("F0", "comun", "Texto común"), fuente("F1", "local_b", "Texto B")],
        "items": [{"id": "I0", "identidad_original": "fila_b", "fuentes_recuperadas_ids": ["F1"]}],
    }
    fuentes, enlaces, comunes = recuperar_fuentes([a, b], {"fila_a"})
    assert {f["id"] for f in fuentes} == {"comun", "local_a"}
    assert enlaces == {"fila_a": ["local_a"]} and comunes == 1
    invalida = deepcopy(a)
    invalida["items"][0]["fuentes_recuperadas_ids"] = ["F0116"]
    with pytest.raises(KeyError):
        recuperar_fuentes([invalida, b], {"fila_a"})
    invalida = deepcopy(b)
    invalida["fuentes"][0] = fuente("F0", "comun", "Texto sustituido con otra huella válida")
    with pytest.raises(ValueError, match="contenidos diferentes"):
        recuperar_fuentes([a, invalida], {"fila_a"})
    invalida["fuentes"][0]["texto_visible_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="texto literal"):
        recuperar_fuentes([a, invalida], {"fila_a"})


def test_contexto_incluye_unidades_completas_y_solo_cambia_la_propuesta_si(captura):
    plan, nuevos, s, anteriores = captura
    assert len(plan["indicadores_pendientes"]) == len(plan["objetivos_pendientes"]) == 8
    assert len(nuevos) == plan["elementos_reales"] == 70
    assert sum(r["tipo"] == "paquete_objetivo" for r in nuevos) == 63
    assert len(plan["unidades_dependientes"]) == 7
    presentes = {r["id"] for r in nuevos}
    modificados = []
    for r in nuevos:
        d, previo = r["documento"], anteriores[r["id"]]["documento"]
        assert d.get("original") == previo.get("original")
        assert d["revision_docente_previa_cierre"] == previo["revision_docente"]
        assert d["revision_docente"]["lecturas"] == []
        assert set(d["revision_docente"]["faltan_roles"]) == set(ROLES)
        assert d["revision_docente"]["edicion_sha256"] == sha(serializar(d["edicion_docente"]))
        assert r["estado"] == "revision_automatica_con_pendientes"
        if d["edicion_docente"] != previo["edicion_docente"]:
            modificados.append(r["id"])
        if r["tipo"] == "paquete_unidad":
            assert set(d["filas_ids"]) <= presentes
    assert modificados == ["CURRICULO:V4:380e17185a52cb7023e4c3f43913a9aa7cc598b1628d01a37f02279e208e216e"]
    ids = {i["identidad_original"]: i["id"] for i in s["items"]}
    assert presentes <= ids.keys()


def test_mensaje_expone_notacion_literal_y_oculta_claves_de_controles(captura):
    plan, nuevos, s, anteriores = captura
    vista = vista_revision(s)
    assert len(s["items"]) == plan["elementos"] == 73
    assert len(s["controles_revision"]["claves"]) == 3
    assert "controles_revision" not in vista
    assert "CONTROL_NEGATIVO:" not in mensaje(s)
    assert len(s["restricciones_originales"]) == 63
    reales = {i["id"]: i["identidad_original"] for i in s["items"]}
    for restriccion in vista["restricciones_originales"]:
        d = anteriores[reales[restriccion["item_id"]]]["documento"]["original"]
        assert restriccion["notacion"] == d["notacion"]
        assert restriccion["indicador_logro_literal"] == d["indicadores_logro"]
    disponibles = {f["id"] for f in s["fuentes"]}
    assert all(set(i["fuentes_recuperadas_ids"]) <= disponibles for i in s["items"])
    assert len(mensaje(s).encode()) == plan["mensaje_bytes"]


def test_preflight_bloquea_antes_del_proveedor_y_no_toca_el_ledger(captura, tmp_path, monkeypatch):
    plan, _, s, _ = captura
    assert plan["safe_to_start"] is False
    assert plan["saldo_llamadas"] == 1
    assert plan["max_nuevas_llamadas"] == 11
    assert plan["max_reserva_nueva_usd"] < plan["saldo_reserva_usd"]
    ledger = BASE / "data/operaciones/registro.sqlite"
    antes = sha(ledger.read_bytes())

    def no_crear_proveedor(*args, **kwargs):
        pytest.fail("El preflight bloqueado no debe construir un cliente de Vertex")

    monkeypatch.setattr("goes_science_kg.produccion.revision_docente.ejecucion.VertexStreaming", no_crear_proveedor)
    guardar(tmp_path / "preflight.json", plan)
    guardar(tmp_path / "ronda_1.json", [s])
    with pytest.raises(ValueError, match="preflight válido"):
        ejecutar([s], tmp_path, ledger, ronda=1, cfg=proveedor_cfg())
    assert sha(ledger.read_bytes()) == antes
    assert not (tmp_path / "intentos").exists()


def test_preparacion_reproduce_la_captura_sin_mutar_publicaciones_o_consumo(captura, tmp_path):
    plan, _, _, _ = captura
    ledger = BASE / "data/operaciones/registro.sqlite"
    if sha(ledger.read_bytes()) != plan["ledger_sha256_inicial"]:
        pytest.skip("El ledger avanzó después del diagnóstico sin consumo")
    salida = tmp_path / "captura_nueva"
    nuevo = preparar(BASE, salida, BASE / "data/cierre_indicadores_20261027/fuentes")
    original = BASE / "data/cierre_indicadores_20261027/campana_p1"
    # La comparación incluye originales, fuentes y votos retirados, no sólo el resumen.
    for archivo in original.glob("*.json"):
        if archivo.name != "preflight.json":
            assert (salida / archivo.name).read_bytes() == archivo.read_bytes()
    assert nuevo["llamadas_nuevas_preparacion"] == nuevo["originales_modificados"] == 0
    assert nuevo["ledger_sha256_inicial"] == sha(ledger.read_bytes())
    with pytest.raises(ValueError, match="directorio nuevo"):
        preparar(BASE, salida, BASE / "data/cierre_indicadores_20261027/fuentes")
