from __future__ import annotations

import copy
from types import SimpleNamespace

import pytest

from goes_science_kg.campanas_vertex import presupuesto
from goes_science_kg.campanas_vertex.contratos import (
    ESQUEMAS,
    GuiaUnidad,
    canonico,
    esquema_transporte,
    sha256,
    validar_alcance_unidad,
)
from goes_science_kg.campanas_vertex.proveedor import (
    LIMITES,
    ProveedorCampana,
    SalidaNoUtilizable,
    huella_codigo,
    preflight,
    preparar_solicitud,
)
from goes_science_kg.motor.registro import PresupuestoAgotado, Registro


def _guia():
    return {
        "unidad_id": "unidad1",
        "titulo": "Unidad de prueba sintética",
        "objetivos_cubiertos": ["objetivo1"],
        "objetivos_pendientes": [
            {"fila_id": "objetivo2", "motivo": "Objetivo reservado para otra etapa; no se finge su cobertura."}
        ],
        "completa": False,
        "orientaciones_docente": ["Utilizar sólo los materiales aprobados para el objetivo seleccionado."],
        "secuencia_componentes": ["guion:objetivo1"],
        "fuentes_ids": ["fuente1"],
        "carga_cognitiva_no_medida": True,
    }


@pytest.fixture
def datos(tmp_path, monkeypatch):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    archivo = tmp_path / "data/operaciones/registro.sqlite"
    registro = Registro(archivo)
    id_historico = registro.reservar(
        ejecucion="historica", clave="historica", modelo="m", rol="h", reserva_usd=1, max_llamadas=2, max_usd=2
    )
    registro.terminar(id_historico, estado="completada", latencia_ms=1)
    monkeypatch.setattr(presupuesto, "configuracion", lambda: {"ejecucion": "historica"})
    monkeypatch.setattr(presupuesto, "comprobar_continuidad", lambda p: {"baseline_verificado": p == archivo})
    tipo = "guia_sintesis_unidad"
    sistema = "Escribe una guía sintética; conserva los objetivos pendientes y no midas aprendizaje."
    contexto = {
        "unidad_id": "unidad1",
        "objetivos_unidad": ["objetivo1", "objetivo2"],
        "fuentes_citables": [{"id": "fuente1"}],
    }
    identificador = "guia:unidad1"
    plan = {
        "campana_id": "piloto_provider_sintetico",
        "max_llamadas": 2,
        "max_reserva_usd": 5,
        "modelos": {"redactor": "gemini-4-argon"},
        "prompts_sha256": {tipo: sha256(sistema.encode())},
        "esquemas_sha256": {tipo: sha256(canonico(esquema_transporte(ESQUEMAS[tipo]).model_json_schema()))},
        "componentes": [{"id": identificador, "tipo": tipo, "contexto_sha256": sha256(canonico(contexto))}],
        "limites": dict(LIMITES),
        "codigo_sha256": huella_codigo(),
    }
    autorizacion = tmp_path / "autorizacion_sintetica.json"
    _recibo(plan, autorizacion)
    return SimpleNamespace(
        archivo=archivo,
        registro=registro,
        plan=plan,
        autorizacion=autorizacion,
        contexto=contexto,
        sistema=sistema,
        id=identificador,
        tipo=tipo,
    )


def _recibo(plan, archivo):
    archivo.write_bytes(
        canonico(
            {
                "version": presupuesto.VERSION_AUTORIZACION,
                "campana_id": plan["campana_id"],
                "plan_sha256": sha256(canonico(plan)),
                "autorizacion_usuario_explicita": True,
                "texto_usuario": "AUTORIZACIÓN SINTÉTICA, sin proveedor real, para este test local.",
                "fecha": "2026-10-29",
                "max_llamadas": plan["max_llamadas"],
                "max_reserva_usd": plan["max_reserva_usd"],
            }
        )
    )


def _cliente(*, texto=None, finish_reason="STOP", error=None):
    llamadas = []

    def generate_content(**kwargs):
        llamadas.append(kwargs)
        if error:
            raise error
        return SimpleNamespace(
            text=texto if texto is not None else canonico(_guia()).decode(),
            candidates=[SimpleNamespace(finish_reason=SimpleNamespace(value=finish_reason))],
            usage_metadata=SimpleNamespace(prompt_token_count=100, candidates_token_count=20, thoughts_token_count=30),
        )

    return SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)), llamadas


def _crear(datos, cliente):
    return ProveedorCampana(datos.plan, datos.autorizacion, datos.archivo, cliente=cliente)


def _generar(proveedor, datos, **kwargs):
    return proveedor.generar(datos.id, contexto=datos.contexto, sistema=datos.sistema, **kwargs)


def test_constructor_sin_autorizacion_no_crea_cliente_ni_ledger(tmp_path):
    with pytest.raises(ValueError, match="autorización presupuestaria"):
        ProveedorCampana({}, None, tmp_path / "no_existe.sqlite")
    assert not (tmp_path / "no_existe.sqlite").exists()


@pytest.mark.parametrize("tipo", list(ESQUEMAS))
def test_todos_los_contratos_se_convierten_offline_con_sdk_instalado(tipo):
    from google.genai import _transformers

    assert _transformers.t_schema(SimpleNamespace(vertexai=True), esquema_transporte(ESQUEMAS[tipo]))


def test_transporte_acepta_booleano_pero_validacion_local_exige_true():
    transporte = esquema_transporte(GuiaUnidad)
    assert "const" not in transporte.model_json_schema()["properties"]["carga_cognitiva_no_medida"]
    with pytest.raises(ValueError):
        transporte.model_validate(_guia() | {"carga_cognitiva_no_medida": False})


def test_guia_no_puede_ocultar_objetivos_del_denominador():
    guia = _guia() | {"objetivos_pendientes": [], "completa": True}
    assert GuiaUnidad.model_validate(guia)
    with pytest.raises(ValueError, match="cada objetivo curricular"):
        validar_alcance_unidad(guia, ["objetivo1", "objetivo2"])


def test_preflight_cubre_conjunto_exacto_y_segunda_plaza(datos):
    resultado = preflight(datos.plan, {datos.id: datos.contexto}, {datos.tipo: datos.sistema})
    assert resultado["llamadas_efectuadas"] == 0
    assert resultado["llamadas_maximas"] == 2
    assert 2.54272 < resultado["reserva_maxima_usd"] < 5
    with pytest.raises(ValueError, match="exactamente"):
        preflight(datos.plan, {}, {datos.tipo: datos.sistema})


@pytest.mark.parametrize("campo", ["prompt", "contexto", "esquema", "codigo"])
def test_huellas_modificadas_bloquean_antes_de_reservar(datos, campo):
    plan = copy.deepcopy(datos.plan)
    sistema, contexto = datos.sistema, datos.contexto
    if campo == "prompt":
        sistema += " cambió"
    elif campo == "contexto":
        contexto = contexto | {"nuevo": "no autorizado"}
    elif campo == "codigo":
        plan["codigo_sha256"]["proveedor.py"] = "0" * 64
    else:
        plan["esquemas_sha256"][datos.tipo] = "0" * 64
    with pytest.raises(ValueError):
        preparar_solicitud(plan, datos.id, contexto=contexto, sistema=sistema)
    assert datos.registro.resumen(plan["campana_id"])["llamadas"] == 0


def test_mide_payload_real_sdk_y_no_recorta_contexto_excesivo(datos):
    contexto = datos.contexto | {"texto": "á" * 130000}
    datos.plan["componentes"][0]["contexto_sha256"] = sha256(canonico(contexto))
    with pytest.raises(ValueError, match="no se recorta ni invoca"):
        preparar_solicitud(datos.plan, datos.id, contexto=contexto, sistema=datos.sistema)


def test_reinicio_recupera_exito_exacto_sin_segunda_llamada_y_con_uso_real(datos):
    cliente, llamadas = _cliente()
    primero = _crear(datos, cliente)
    assert _generar(primero, datos).completa is False
    segundo = _crear(datos, cliente)
    assert _generar(segundo, datos).completa is False
    assert len(llamadas) == 1
    consumo = datos.registro.resumen(datos.plan["campana_id"])
    assert consumo["llamadas"] == 1
    assert consumo["detalle"][0]["salida_tokens"] == 50
    assert datos.registro.resumen("historica")["llamadas"] == 1


def test_recupera_salida_con_finish_reason_si_se_interrumpe_cache(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    _generar(proveedor, datos)
    with datos.registro.conexion() as db:
        db.execute("DELETE FROM cache")
    _generar(_crear(datos, cliente), datos)
    assert len(llamadas) == 1


def test_recupera_exito_tras_interrupcion_antes_de_terminar_la_reserva(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    _generar(proveedor, datos)
    with datos.registro.conexion() as db:
        db.execute(
            "UPDATE llamadas SET estado='reservada',latencia_ms=NULL WHERE ejecucion=?", (datos.plan["campana_id"],)
        )
    _generar(_crear(datos, cliente), datos)
    detalle = datos.registro.resumen(datos.plan["campana_id"])["detalle"][0]
    assert detalle["estado"] == "completada" and detalle["latencia_ms"] is None
    assert detalle["salida_tokens"] == 50
    assert len(llamadas) == 1


def test_no_adopta_cache_sin_finish_metadata_recuperable(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    _generar(proveedor, datos)
    with datos.registro.conexion() as db:
        db.execute("DELETE FROM campanas_vertex_respuestas")
    with pytest.raises(SalidaNoUtilizable, match="terminación verificable"):
        _generar(proveedor, datos)
    assert len(llamadas) == 1


def test_cache_alterada_no_adopta_respuesta_distinta_del_original(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    _generar(proveedor, datos)
    solicitud = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    cache = proveedor.presupuesto.cache(solicitud["clave"])
    texto = canonico(_guia() | {"titulo": "Contenido alterado en caché"}).decode()
    cache.update(texto=texto, respuesta_sha256=sha256(texto.encode()))
    proveedor.presupuesto.guardar_cache(solicitud["clave"], cache)
    with pytest.raises(ValueError, match="SHA de la caché"):
        _generar(proveedor, datos)
    assert len(llamadas) == 1


def test_json_valido_truncado_por_max_tokens_se_retiene_sin_repetir(datos):
    cliente, llamadas = _cliente(finish_reason="MAX_TOKENS")
    proveedor = _crear(datos, cliente)
    for _ in range(2):
        with pytest.raises(SalidaNoUtilizable):
            _generar(proveedor, datos)
    assert len(llamadas) == 1
    assert datos.registro.resumen(datos.plan["campana_id"])["detalle"][0]["estado"] == "fallida"


def test_recupera_rechazo_truncado_tras_interrupcion_sin_cobrar_otra_vez(datos):
    cliente, llamadas = _cliente(finish_reason="MAX_TOKENS")
    proveedor = _crear(datos, cliente)
    with pytest.raises(SalidaNoUtilizable):
        _generar(proveedor, datos)
    with datos.registro.conexion() as db:
        db.execute("UPDATE llamadas SET estado='reservada' WHERE ejecucion=?", (datos.plan["campana_id"],))
    with pytest.raises(SalidaNoUtilizable):
        _generar(_crear(datos, cliente), datos)
    assert datos.registro.resumen(datos.plan["campana_id"])["detalle"][0]["estado"] == "fallida"
    assert len(llamadas) == 1


def test_json_invalido_se_conserva_y_solo_permite_una_correccion_anclada(datos):
    cliente, llamadas = _cliente(texto="{incompleto")
    proveedor = _crear(datos, cliente)
    with pytest.raises(SalidaNoUtilizable) as error:
        _generar(proveedor, datos)
    anterior = error.value.texto_respuesta.encode()
    proveedor._cliente, correcciones = _cliente()
    proveedor.__dict__.pop("cliente", None)
    assert (
        _generar(proveedor, datos, ronda=1, anterior=anterior, hallazgos=["JSON incompleto conservado"]).completa
        is False
    )
    assert len(llamadas) == len(correcciones) == 1
    with pytest.raises(PresupuestoAgotado):
        _generar(proveedor, datos, ronda=1, anterior=anterior, hallazgos=["Otro intento no autorizado"])
    assert datos.registro.resumen(datos.plan["campana_id"])["llamadas"] == 2


def test_no_permite_correccion_sin_primera_plaza_o_con_otra_respuesta(datos):
    cliente, llamadas = _cliente(texto="{incompleto")
    proveedor = _crear(datos, cliente)
    with pytest.raises(ValueError, match="primera plaza"):
        _generar(proveedor, datos, ronda=1, anterior=b"inventado", hallazgos=["No se permite"])
    with pytest.raises(SalidaNoUtilizable):
        _generar(proveedor, datos)
    with pytest.raises(ValueError, match="exactamente"):
        _generar(proveedor, datos, ronda=1, anterior=b"otro borrador", hallazgos=["No coincide"])
    assert len(llamadas) == 1


def test_guia_que_oculta_objetivo_se_retiene_antes_de_cachear(datos):
    cliente, _ = _cliente(texto=canonico(_guia() | {"objetivos_pendientes": [], "completa": True}).decode())
    proveedor = _crear(datos, cliente)
    with pytest.raises(SalidaNoUtilizable, match="contrato local"):
        _generar(proveedor, datos)
    solicitud = preparar_solicitud(datos.plan, datos.id, contexto=datos.contexto, sistema=datos.sistema)
    assert proveedor.presupuesto.cache(solicitud["clave"]) is None


def test_plan_original_se_copia_y_plan_interno_alterado_se_bloquea(datos):
    cliente, llamadas = _cliente()
    proveedor = _crear(datos, cliente)
    datos.plan["max_reserva_usd"] = 1000
    assert proveedor.plan["max_reserva_usd"] == 5
    proveedor.plan["max_reserva_usd"] = 1000
    with pytest.raises(ValueError, match="plan autorizado cambió"):
        _generar(proveedor, datos)
    assert not llamadas
