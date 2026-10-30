from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from goes_science_kg.campanas_vertex import presupuesto
from goes_science_kg.motor.registro import PresupuestoAgotado, Registro


def _bytes(valor):
    return (json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


@pytest.fixture
def campana(tmp_path, monkeypatch):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    archivo = tmp_path / "data/operaciones/registro.sqlite"
    registro = Registro(archivo)
    historico = registro.reservar(
        ejecucion="historica", clave="clave", modelo="m", rol="r", reserva_usd=2, max_llamadas=20, max_usd=20
    )
    registro.terminar(historico, estado="completada", latencia_ms=1)
    registro.guardar_salida(historico, '{"historica":true}')
    registro.guardar_cache("clave", {"historica": True})
    monkeypatch.setattr(presupuesto, "configuracion", lambda: {"ejecucion": "historica"})
    monkeypatch.setattr(presupuesto, "comprobar_continuidad", lambda p: {"baseline_verificado": p == archivo})
    plan = {
        "campana_id": "piloto_nuevo",
        "max_llamadas": 2,
        "max_reserva_usd": 3,
        "modelos": {"redactor": "m"},
        "prompts_sha256": {"redactor": "a" * 64},
        "esquemas_sha256": {"recorrido": "b" * 64},
        "componentes": [{"id": "recorrido:objetivo1"}],
        "limites": {"plazas_por_componente": 2},
    }
    recibo = {
        "version": presupuesto.VERSION_AUTORIZACION,
        "campana_id": plan["campana_id"],
        "plan_sha256": hashlib.sha256(_bytes(plan)).hexdigest(),
        "autorizacion_usuario_explicita": True,
        "texto_usuario": "AUTORIZACIÓN SINTÉTICA DE PRUEBA: dos llamadas y reserva USD 3 para este plan.",
        "fecha": "2026-10-29",
        "max_llamadas": 2,
        "max_reserva_usd": 3,
    }
    autorizacion = tmp_path / "autorizacion_prueba.json"
    autorizacion.write_bytes(_bytes(recibo))
    return plan, recibo, autorizacion, archivo, registro, historico


def _crear(datos):
    plan, _, autorizacion, archivo, _, _ = datos
    return presupuesto.PresupuestoCampana(plan, autorizacion, archivo)


def _reservar(campana, ronda=0, **kwargs):
    return campana.autorizar_reserva(
        **{
            "clave": "clave" if ronda == 0 else "correccion",
            "modelo": "m",
            "rol": f"recorrido:objetivo1:ronda{ronda}",
            "reserva_usd": 1,
            **kwargs,
        }
    )


def test_sin_recibo_no_crea_ni_abre_ledger(tmp_path, monkeypatch):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    destino = tmp_path / "data/operaciones/registro.sqlite"
    with pytest.raises(ValueError, match="autorización presupuestaria"):
        presupuesto.PresupuestoCampana({}, None, destino)
    assert not destino.exists()


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("version", "otra"),
        ("campana_id", "otra_campana"),
        ("plan_sha256", "0" * 64),
        ("autorizacion_usuario_explicita", 1),
        ("texto_usuario", "  "),
        ("fecha", "ayer"),
        ("max_llamadas", True),
        ("max_llamadas", 3),
        ("max_reserva_usd", 4),
        ("max_reserva_usd", float("nan")),
    ],
)
def test_recibo_no_permite_inferir_autorizacion_o_cambiar_tope(campana, campo, valor):
    plan, recibo, autorizacion, _, _, _ = campana
    autorizacion.write_bytes(_bytes({**recibo, campo: valor}))
    with pytest.raises(ValueError):
        presupuesto.verificar_autorizacion(plan, autorizacion)


def test_cualquier_cambio_de_prompt_o_esquema_invalida_recibo(campana):
    plan, _, autorizacion, _, _, _ = campana
    plan["esquemas_sha256"]["recorrido"] = "c" * 64
    with pytest.raises(ValueError, match="versión exacta"):
        presupuesto.verificar_autorizacion(plan, autorizacion)


def test_recibo_no_admite_rutas_externas_o_enlaces(campana, tmp_path):
    plan, _, autorizacion, _, _, _ = campana
    enlace = tmp_path / "enlace.json"
    enlace.symlink_to(autorizacion)
    with pytest.raises(ValueError, match="simbólicos"):
        presupuesto.verificar_autorizacion(plan, enlace)
    with pytest.raises(ValueError, match="dentro del repositorio"):
        presupuesto.verificar_autorizacion(plan, tmp_path.parent / "externo.json")


def test_verifica_continuidad_antes_de_instanciar_registro(campana, monkeypatch):
    def sin_continuidad(archivo):
        raise ValueError("histórico alterado")

    def nunca_crear(archivo):
        pytest.fail("No debe abrir un Registro antes de verificar el histórico")

    monkeypatch.setattr(presupuesto, "comprobar_continuidad", sin_continuidad)
    monkeypatch.setattr(presupuesto, "Registro", nunca_crear)
    with pytest.raises(ValueError, match="histórico alterado"):
        _crear(campana)


def test_rechaza_un_ledger_alternativo(campana, tmp_path):
    plan, _, autorizacion, _, _, _ = campana
    with pytest.raises(ValueError, match="mismo ledger"):
        presupuesto.PresupuestoCampana(plan, autorizacion, tmp_path / "nuevo.sqlite")


def test_nueva_campana_no_adopta_cache_salida_ni_consumo_historicos(campana):
    _, _, _, _, registro, historico = campana
    antes = registro.resumen("historica")
    nueva = _crear(campana)
    assert nueva.cache("clave") is None
    assert nueva.salida("clave") is None
    llamada = _reservar(nueva)
    nueva.guardar_salida(llamada, '{"nueva":true}')
    nueva.guardar_cache("clave", {"nueva": True})
    nueva.terminar(llamada, estado="completada", latencia_ms=4, entrada_tokens=10, salida_tokens=20)
    assert nueva.cache("clave") == {"nueva": True}
    assert nueva.salida("clave") == '{"nueva":true}'
    assert registro.cache("clave") == {"historica": True}
    assert registro.salida("clave") == '{"historica":true}'
    assert registro.resumen("historica") == antes
    assert registro.resumen(nueva.ejecucion_id)["llamadas"] == 1
    for metodo, kwargs in ((nueva.guardar_salida, {"texto": "otro"}), (nueva.terminar, {})):
        with pytest.raises(ValueError, match="no pertenece"):
            metodo(historico, **kwargs)


def test_reanudacion_mantiene_reservas_y_no_repite_rol_incluso_si_fallo(campana):
    primera = _crear(campana)
    llamada = _reservar(primera)
    primera.terminar(llamada, estado="fallida", latencia_ms=1)
    reanudada = _crear(campana)
    with pytest.raises(PresupuestoAgotado, match="plaza"):
        _reservar(reanudada)
    _reservar(reanudada, 1)
    assert reanudada.registro.resumen(reanudada.ejecucion_id)["llamadas"] == 2
    with pytest.raises(PresupuestoAgotado):
        _reservar(reanudada, 1)


def test_reserva_concurrente_por_rol_solo_crea_una_fila(campana):
    nueva = _crear(campana)

    def competir(_):
        try:
            return _reservar(nueva)
        except PresupuestoAgotado:
            return None

    with ThreadPoolExecutor(max_workers=6) as pool:
        resultados = list(pool.map(competir, range(12)))
    assert sum(r is not None for r in resultados) == 1
    assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == 1


def test_reserva_usd_y_roles_frenan_antes_del_insert(campana):
    nueva = _crear(campana)
    for cambios in ({"modelo": "otro"}, {"rol": "ajeno:ronda0"}, {"reserva_usd": float("inf")}):
        with pytest.raises(ValueError):
            _reservar(nueva, **cambios)
    with pytest.raises(ValueError, match="primera plaza"):
        _reservar(nueva, 1)
    _reservar(nueva, reserva_usd=2.5)
    with pytest.raises(PresupuestoAgotado, match="USD"):
        _reservar(nueva, 1)
    assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == 1


def test_mismo_id_no_permite_reemplazar_plan_autorizado_para_reiniciar(campana):
    plan, recibo, autorizacion, _, _, _ = campana
    _crear(campana)
    plan["modelos"]["redactor"] = "otro"
    recibo["plan_sha256"] = hashlib.sha256(_bytes(plan)).hexdigest()
    autorizacion.write_bytes(_bytes(recibo))
    with pytest.raises(ValueError, match="otro plan o recibo"):
        _crear(campana)


def test_maximo_llamadas_bloquea_aunque_quede_reserva_usd(campana):
    plan, recibo, autorizacion, _, _, _ = campana
    plan["max_llamadas"] = recibo["max_llamadas"] = 1
    recibo["plan_sha256"] = hashlib.sha256(_bytes(plan)).hexdigest()
    autorizacion.write_bytes(_bytes(recibo))
    nueva = _crear(campana)
    _reservar(nueva)
    with pytest.raises(PresupuestoAgotado, match="máximo de llamadas"):
        _reservar(nueva, 1)
    assert nueva.registro.resumen(nueva.ejecucion_id)["reserva_usd"] == 1


def test_otra_campana_nueva_tampoco_adopta_cache_de_la_primera(campana):
    plan, recibo, autorizacion, _, _, _ = campana
    primera = _crear(campana)
    primera.guardar_cache("misma_clave", {"primera": True})
    plan["campana_id"] = recibo["campana_id"] = "otra_campana_nueva"
    recibo["plan_sha256"] = hashlib.sha256(_bytes(plan)).hexdigest()
    autorizacion.write_bytes(_bytes(recibo))
    segunda = _crear(campana)
    assert segunda.cache("misma_clave") is None
    assert primera.cache("misma_clave") == {"primera": True}
    assert segunda.registro.resumen(segunda.ejecucion_id)["llamadas"] == 0


@pytest.mark.parametrize("mutacion", ["plan", "autorizacion", "ambos"])
@pytest.mark.parametrize("operacion", ["reservar", "cache", "guardar_cache", "salida", "guardar_salida", "terminar"])
def test_mutar_plan_o_autorizacion_en_memoria_bloquea_todas_las_operaciones(campana, mutacion, operacion):
    nueva = _crear(campana)
    if mutacion in {"plan", "ambos"}:
        nueva.plan["max_reserva_usd"] = 3000
    if mutacion == "autorizacion":
        nueva.autorizacion["max_llamadas"] = 2000
    elif mutacion == "ambos":
        nueva.autorizacion["plan_sha256"] = hashlib.sha256(_bytes(nueva.plan)).hexdigest()
    operaciones = {
        "reservar": lambda: _reservar(nueva),
        "cache": lambda: nueva.cache("clave"),
        "guardar_cache": lambda: nueva.guardar_cache("clave", {"ilegible": True}),
        "salida": lambda: nueva.salida("clave"),
        "guardar_salida": lambda: nueva.guardar_salida("inexistente", "texto"),
        "terminar": lambda: nueva.terminar("inexistente", estado="completada", latencia_ms=0),
    }
    with pytest.raises(ValueError, match="cambiaron después"):
        operaciones[operacion]()
    assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == 0


def test_mutar_plan_entre_inicio_y_transaccion_no_reserva(campana, monkeypatch):
    nueva = _crear(campana)
    comprobar = nueva._verificar_plan
    revisiones = []

    def cambiar_tras_primera_validacion():
        revisiones.append(True)
        comprobar()
        if len(revisiones) == 1:
            nueva.plan["max_reserva_usd"] = 3000

    monkeypatch.setattr(nueva, "_verificar_plan", cambiar_tras_primera_validacion)
    with pytest.raises(ValueError, match="cambiaron después"):
        _reservar(nueva)
    assert len(revisiones) == 2
    assert nueva.registro.resumen(nueva.ejecucion_id)["llamadas"] == 0
