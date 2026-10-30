"""Reject empty dynamic solutions and preserve every received value through typed list transport."""

from __future__ import annotations

import copy
import json
from types import SimpleNamespace

import pytest
from test_campanas_vertex_proveedor import _cliente, _crear, _recibo
from test_campanas_vertex_proveedor import datos as datos
from test_cierre_recorridos import recorrido as recorrido

from goes_science_kg.campanas_vertex.contratos import (
    ESQUEMAS,
    PERFIL_LISTA,
    PERFIL_MAPA,
    RecorridoAutor,
    canonico,
    completar_recorrido,
    contrato_autor_api,
    equivalencia_raw_normalizado,
    esquema_transporte,
    leer_objeto_autor,
    normalizar_autoria,
    sha256,
)
from goes_science_kg.campanas_vertex.proveedor import SalidaNoUtilizable, preparar_solicitud


@pytest.fixture
def caso(datos, recorrido):
    base = copy.deepcopy(recorrido)
    origen, fuentes = base.pop("origen"), base.pop("fuentes")
    base["fuentes_ids"] = ["F1"]
    for solucion in base["soluciones_docente"].values():
        solucion["calculos"] = []
    wire = copy.deepcopy(base)
    wire["soluciones_docente"] = [
        {"item_id": item_id, **copy.deepcopy(solucion)} for item_id, solucion in base["soluciones_docente"].items()
    ]
    datos.tipo, datos.id = "recorrido_cerrado", "recorrido:objetivo1"
    datos.contexto = {
        "fila_id": "fila_sintetica",
        "grado": base["grado"],
        "objetivo_literal": base["objetivos"][0],
        "origen_fijado": origen,
        "fuentes_citables": fuentes,
    }
    datos.plan["componentes"] = [
        {"id": datos.id, "tipo": datos.tipo, "contexto_sha256": sha256(canonico(datos.contexto))}
    ]
    datos.plan["prompts_sha256"] = {datos.tipo: sha256(datos.sistema.encode())}
    datos.plan["perfiles_transporte"] = {datos.tipo: PERFIL_LISTA}
    datos.plan["esquemas_negocio_sha256"] = {datos.tipo: sha256(canonico(ESQUEMAS[datos.tipo].model_json_schema()))}
    datos.plan["esquemas_sha256"] = {
        datos.tipo: sha256(canonico(esquema_transporte(contrato_autor_api(datos.tipo)).model_json_schema()))
    }
    _recibo(datos.plan, datos.autorizacion)
    return SimpleNamespace(datos=datos, base=base, wire=wire)


def generar(caso, raw):
    datos = caso.datos
    cliente, llamadas = _cliente(texto=raw)
    proveedor = _crear(datos, cliente)
    return proveedor, llamadas


def solicitar(caso, proveedor):
    datos = caso.datos
    return proveedor.generar(datos.id, contexto=datos.contexto, sistema=datos.sistema)


def test_wire_has_three_explicit_solutions_and_typed_calculations(caso):
    from google.genai import _transformers

    api = contrato_autor_api("recorrido_cerrado")
    schema = esquema_transporte(api).model_json_schema()
    assert schema["properties"]["soluciones_docente"]["minItems"] == 3
    assert schema["properties"]["soluciones_docente"]["type"] == "array"
    assert schema["$defs"]["SolucionItemAutor"]["properties"]["calculos"]["items"]["$ref"].endswith(
        "/ComprobacionCalculo"
    )
    converted = _transformers.t_schema(SimpleNamespace(vertexai=True), esquema_transporte(api))
    if hasattr(converted, "model_dump"):
        converted = converted.model_dump(mode="json", by_alias=True, exclude_none=True)
    assert converted["properties"]["soluciones_docente"]["minItems"] == 3
    assert str(converted["properties"]["soluciones_docente"]["type"]).upper().endswith("ARRAY")


def test_only_the_new_solution_array_keeps_remote_cardinality():
    schema = esquema_transporte(contrato_autor_api("recorrido_cerrado")).model_json_schema()

    def limits(value, path=""):
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "minItems":
                    yield path + "/" + key
                yield from limits(child, path + "/" + key)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from limits(child, path + "/" + str(index))

    assert list(limits(schema)) == ["/properties/soluciones_docente/minItems"]
    assert list(limits(esquema_transporte(RecorridoAutor).model_json_schema())) == []


def test_empty_legacy_map_is_shape_valid_but_not_complete(caso):
    empty = caso.base | {"soluciones_docente": {}}
    assert RecorridoAutor.model_validate(empty)
    with pytest.raises(ValueError, match="cubrir exactamente"):
        normalizar_autoria("recorrido_cerrado", empty, perfil=PERFIL_MAPA)


def test_round_trip_preserves_all_text_numbers_and_fields_without_defaults(caso):
    wire = copy.deepcopy(caso.wire)
    wire["soluciones_docente"][0]["respuesta"] += "\nTexto con ñ, <símbolos>, unidades y espacios  exactos."
    wire["soluciones_docente"][0]["calculos"] = [{"expresion": "95-65", "resultado": 30, "unidad": "mL"}]
    raw = (json.dumps(wire, ensure_ascii=False, indent=3) + "\n").encode()
    before = copy.deepcopy(wire)
    proof = equivalencia_raw_normalizado(raw, "recorrido_cerrado")
    normalized = proof["autor_normalizado"]
    assert proof["conversion_biyectiva"] is True and proof["raw_sha256"] == sha256(raw)
    assert wire == before
    assert {k: v for k, v in normalized.items() if k != "soluciones_docente"} == {
        k: v for k, v in wire.items() if k != "soluciones_docente"
    }
    for item in wire["soluciones_docente"]:
        assert normalized["soluciones_docente"][item["item_id"]] == {k: v for k, v in item.items() if k != "item_id"}
    calculo = normalized["soluciones_docente"]["D1"]["calculos"][0]
    assert type(calculo["resultado"]) is int and "tolerancia" not in calculo
    final = completar_recorrido(
        normalized, origen=caso.datos.contexto["origen_fijado"], fuentes=caso.datos.contexto["fuentes_citables"]
    )
    assert final["soluciones_docente"]["D1"]["respuesta"] == wire["soluciones_docente"][0]["respuesta"]


@pytest.mark.parametrize(
    "defect", ["empty", "duplicate", "missing", "extra", "example", "bad_calculation", "unknown_field"]
)
def test_invalid_lists_never_enter_cache_and_raw_is_kept(caso, defect):
    wire = copy.deepcopy(caso.wire)
    if defect == "empty":
        wire["soluciones_docente"] = []
    elif defect == "duplicate":
        wire["soluciones_docente"].append(copy.deepcopy(wire["soluciones_docente"][0]))
    elif defect == "missing":
        wire["soluciones_docente"][-1]["item_id"] = "missing_other"
    elif defect == "extra":
        extra = copy.deepcopy(wire["soluciones_docente"][0])
        extra["item_id"] = "extra"
        wire["soluciones_docente"].append(extra)
    elif defect == "example":
        wire["soluciones_docente"][0]["item_id"] = wire["refuerzo"]["ejemplo_trabajado"]["id"]
    elif defect == "bad_calculation":
        wire["soluciones_docente"][0]["calculos"] = [{"expresion": "95-65", "resultado": 999, "unidad": "mL"}]
    else:
        wire["soluciones_docente"][0]["campo_no_ofrecido"] = "No debe desaparecer silenciosamente."
    raw = canonico(wire).decode()
    provider, calls = generar(caso, raw)
    with pytest.raises(SalidaNoUtilizable):
        solicitar(caso, provider)
    request = preparar_solicitud(
        caso.datos.plan, caso.datos.id, contexto=caso.datos.contexto, sistema=caso.datos.sistema
    )
    assert provider.presupuesto.cache(request["clave"]) is None
    assert provider.presupuesto.salida(request["clave"]) == raw
    assert len(calls) == 1


@pytest.mark.parametrize("value", [True, "30", float("nan"), float("inf")])
def test_calculation_values_are_finite_original_numbers_not_coercions(caso, value):
    wire = copy.deepcopy(caso.wire)
    wire["soluciones_docente"][0]["calculos"] = [{"expresion": "95-65", "resultado": value, "unidad": "mL"}]
    with pytest.raises(ValueError):
        normalizar_autoria("recorrido_cerrado", wire)


@pytest.mark.parametrize("value", [{"resultado": 30}, {"expresion": "95-65", "resultado": 30}, "95-65=30"])
def test_malformed_calculations_are_not_accepted(caso, value):
    wire = copy.deepcopy(caso.wire)
    wire["soluciones_docente"][0]["calculos"] = [value]
    with pytest.raises(ValueError):
        normalizar_autoria("recorrido_cerrado", wire)


@pytest.mark.parametrize(
    "raw", ['{"respuesta":"primera","respuesta":"otra"}', '{"resultado":NaN}', '{"resultado":Infinity}']
)
def test_parser_never_silently_discards_duplicate_fields_or_nonfinite_values(raw):
    with pytest.raises(ValueError):
        leer_objeto_autor(raw)


def test_cache_keeps_original_array_and_replay_repeats_identical_adapter(caso):
    raw = json.dumps(caso.wire, ensure_ascii=False, indent=4) + "\n"
    provider, calls = generar(caso, raw)
    first = solicitar(caso, provider)
    second = solicitar(caso, provider)
    assert first == second and first.soluciones_docente.keys() == caso.base["soluciones_docente"].keys()
    assert len(calls) == 1
    request = preparar_solicitud(
        caso.datos.plan, caso.datos.id, contexto=caso.datos.contexto, sistema=caso.datos.sistema
    )
    cache = provider.presupuesto.cache(request["clave"])
    assert cache["texto"] == provider.presupuesto.salida(request["clave"]) == raw
    assert isinstance(json.loads(cache["texto"])["soluciones_docente"], list)
    assert cache["normalizado_sha256"] == sha256(canonico(caso.base))
    assert cache["perfil_transporte"] == request["identidad"]["perfil_transporte"] == PERFIL_LISTA


def test_map_is_supported_only_when_the_plan_pins_legacy_profile(caso):
    datos = caso.datos
    datos.plan["perfiles_transporte"][datos.tipo] = PERFIL_MAPA
    datos.plan["esquemas_sha256"][datos.tipo] = sha256(canonico(esquema_transporte(RecorridoAutor).model_json_schema()))
    _recibo(datos.plan, datos.autorizacion)
    provider, calls = generar(caso, canonico(caso.base).decode())
    assert solicitar(caso, provider)
    assert len(calls) == 1


def test_new_list_profile_never_adopts_a_map_response(caso):
    provider, calls = generar(caso, canonico(caso.base).decode())
    with pytest.raises(SalidaNoUtilizable):
        solicitar(caso, provider)
    assert len(calls) == 1


def test_wrong_business_schema_fails_before_paid_reservation(caso):
    datos = caso.datos
    datos.plan["esquemas_negocio_sha256"][datos.tipo] = "0" * 64
    _recibo(datos.plan, datos.autorizacion)
    provider, calls = generar(caso, canonico(caso.wire).decode())
    with pytest.raises(ValueError, match="contrato de negocio"):
        solicitar(caso, provider)
    assert calls == []
    assert datos.registro.resumen(datos.plan["campana_id"])["llamadas"] == 0


@pytest.mark.parametrize(
    "field", ["normalizado_sha256", "perfil_transporte", "adapter_version", "adapter_codigo_sha256"]
)
def test_replay_never_silently_repairs_changed_normalization_evidence(caso, field):
    raw = canonico(caso.wire).decode()
    provider, calls = generar(caso, raw)
    solicitar(caso, provider)
    datos = caso.datos
    request = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    cache = provider.presupuesto.cache(request["clave"])
    cache[field] = "alterado"
    provider.presupuesto.guardar_cache(request["clave"], cache)
    with pytest.raises(ValueError, match="traza de normalización"):
        solicitar(caso, provider)
    assert len(calls) == 1
    assert provider.presupuesto.cache(request["clave"])[field] == "alterado"
