"""Test adversarial alignment resumption against shared synthetic physical sources."""

from __future__ import annotations

from copy import deepcopy

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from test_alineacion import LectorSimulado, ejecutar
from test_alineacion import entrada as entrada

from goes_science_kg.motor.alineacion import ROLES_ALINEACION
from goes_science_kg.motor.ejecuciones import ejecutar_durable


@pytest.mark.parametrize("rol", ROLES_ALINEACION)
def test_modelo_ajeno_no_respalda_ni_se_reanuda_aunque_rol_y_huella_coincidan(entrada, rol):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    estado = ejecutar(motor, entrada.solicitud)
    estado[rol]["dictamen"]["modelo"] = "otro-modelo"
    cierre = motor._cerrar(estado)["resultado"]
    assert cierre["estado"] == "abstencion" and len(cierre["dictamenes"]) == 2
    assert any("otro modelo" in motivo for motivo in cierre["motivos"])
    with pytest.raises(ValueError, match="modelo"):
        motor.validar_estado(estado)
    assert len(modelo.llamadas) == 3


def test_dictamen_parcial_de_otro_modelo_se_rechaza_antes_de_continuar_lecturas(entrada):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    estado = ejecutar(motor, entrada.solicitud)
    estado.pop("resultado")
    for rol in ROLES_ALINEACION[1:]:
        estado.pop(rol)
    estado[ROLES_ALINEACION[0]]["dictamen"]["modelo"] = "modelo-del-checkpoint-ajeno"
    with pytest.raises(ValueError, match="modelo"):
        motor.validar_estado(estado)
    assert len(modelo.llamadas) == 3


@pytest.mark.parametrize(
    "campo",
    ["estado", "solicitud", "ejecucion", "huella", "version", "criterios", "cita", "evidencia", "limite", "motivos"],
)
def test_terminal_alterado_no_sustituye_el_cierre_reconstruido(entrada, campo):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    estado = ejecutar(motor, entrada.solicitud)
    resultado = estado["resultado"]
    if campo == "estado":
        resultado["estado"] = "no_respaldado"
    elif campo == "solicitud":
        resultado["solicitud"]["fila_id"] = "fila-ajena"
    elif campo == "ejecucion":
        resultado["ejecucion_id"] = "presupuesto-ajeno"
    elif campo == "huella":
        resultado["huella_tarea"] = "b" * 64
    elif campo == "version":
        resultado["version_pipeline"] = "otro-pipeline"
    elif campo == "criterios":
        resultado["dictamenes"][0]["criterios"]["evidencia_explicita"] = "no"
    elif campo == "cita":
        resultado["dictamenes"][0]["citas_locales"][0]["literal"] = "Una cita inventada dentro del resultado"
    elif campo == "evidencia":
        resultado["evidencias"][0]["fuente"]["sha256"] = "d" * 64
    elif campo == "limite":
        resultado["limite"] = "Se atribuye indebidamente una cobertura completa"
    else:
        resultado["motivos"] = ["Motivo distinto del cierre"]
    with pytest.raises(ValueError, match="resultado terminal"):
        motor.validar_estado(estado)
    assert motor._cerrar(estado)["resultado"]["estado"] == "respaldo_documental_automatico"
    assert len(modelo.llamadas) == 3


def test_resultado_sin_preparacion_o_con_contrato_invalido_no_se_reutiliza(entrada):
    motor = entrada.crear()
    estado = ejecutar(motor, entrada.solicitud)
    sin_preparacion = {k: v for k, v in estado.items() if k != "preparacion"}
    with pytest.raises(ValueError, match="preparación"):
        motor.validar_estado(sin_preparacion)
    with pytest.raises(ValueError):
        motor.validar_estado(estado | {"resultado": {}})


def test_terminal_verdadero_reconstruye_sin_recursion_ni_nuevas_llamadas(entrada):
    modelo = LectorSimulado()
    motor = entrada.crear(modelo)
    estado = ejecutar(motor, entrada.solicitud)
    original = deepcopy(estado)
    for _ in range(3):
        motor.validar_estado(estado)
        assert motor._cerrar(estado)["resultado"] == estado["resultado"]
    assert estado == original and len(modelo.llamadas) == 3


def test_checkpoint_negativo_promovido_a_positivo_se_rechaza_sin_mas_modelos(entrada, tmp_path):
    modelo = LectorSimulado(negativo=True)
    motor = entrada.crear(modelo)
    archivo = tmp_path / "checkpoint-adversarial.sqlite"
    configuracion = {"configurable": {"thread_id": "alineacion-controlada"}}
    argumentos = dict(
        archivo=archivo,
        solicitud=entrada.solicitud.model_dump(),
        thread_id="alineacion-controlada",
        ejecucion_id="presupuesto-controlado",
        huella_entorno=motor.huella_entorno,
    )
    original = ejecutar_durable(motor, **argumentos)
    assert original["resultado"]["estado"] == "no_respaldado" and len(modelo.llamadas) == 3
    with SqliteSaver.from_conn_string(str(archivo)) as checkpointer:
        flujo = motor.compilar(checkpointer=checkpointer)
        resultado = deepcopy(original["resultado"])
        resultado["estado"] = "respaldo_documental_automatico"
        resultado["motivos"] = []
        flujo.update_state(configuracion, {"resultado": resultado}, as_node="cerrar")
        assert not flujo.get_state(configuracion).next
    with pytest.raises(ValueError, match="resultado terminal"):
        ejecutar_durable(motor, **argumentos)
    assert len(modelo.llamadas) == 3
