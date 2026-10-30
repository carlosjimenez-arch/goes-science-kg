"""Test held-out learning materials and honest interpretation of their evidence."""

import copy
import json

import pytest

from goes_science_kg.aprendizaje.cierre_recorridos import (
    materializar_recorrido,
    resumen_mediciones,
    validar_recorrido,
)


@pytest.fixture
def recorrido():
    rubrica = {
        "criterio": "Comparación de datos",
        "logrado": "Compara la magnitud usando los datos completos y sus unidades.",
        "en_proceso": "Compara las magnitudes pero omite una unidad o condición.",
        "requiere_apoyo": "Confunde los datos y no explica la comparación entre magnitudes.",
    }
    return {
        "id": "TEST",
        "titulo": "Comparar cantidades de agua en recipientes",
        "grado": 5,
        "origen": {"tipo": "prueba_sintetica"},
        "objetivos": ["Comparar cantidades usando datos y unidades."],
        "fundamento": ["Las cantidades se comparan con la misma unidad y condiciones explícitas."],
        "fuentes": [{"id": "F1", "titulo": "Fuente sintética", "url": "https://example.org/", "alcance": "Prueba"}],
        "diagnostico": {
            "items": [{"id": "D1", "enunciado": "En A hay 20 mL y en B hay 40 mL. ¿En cuál hay más agua?"}],
            "criterio_derivacion": "Si confunde cantidades, volver a comparar los datos antes de explicar.",
        },
        "refuerzo": {
            "ejemplo_trabajado": {
                "id": "E1",
                "enunciado": "Un recipiente contiene 15 mL y otro 30 mL. Compara usando la misma unidad.",
                "pasos": ["Ambas cantidades están en mL.", "30 es mayor que 15, por tanto el segundo contiene más."],
            },
            "practica_guiada": {
                "items": [{"id": "P1", "enunciado": "La jarra X contiene 80 mL y la Y 50 mL. Compara sus cantidades."}],
                "apoyos": ["Marca primero la unidad que comparten los datos."],
            },
            "retirada_apoyos": "Retirar el ejemplo y las pistas antes de entregar la comprobación nueva.",
        },
        "comprobacion_independiente": {
            "items": [
                {"id": "C1", "enunciado": "Sofía registra 65 mL y Luis 95 mL. ¿Qué registro representa más agua?"}
            ],
            "sin_ayudas": True,
            "administracion": "Responder individualmente sin ejemplo ni ayuda conceptual del tutor.",
            "criterios": ["Comparar cantidades y justificar con datos y unidad."],
            "si_no_logra": "Volver al dato y la unidad que no se comprendieron, y usar otra tarea después.",
        },
        "soluciones_docente": {
            i: {
                "respuesta": "Clave docente reservada: comparar cantidades correctamente.",
                "explicacion": "Comparar los números y conservar la unidad común para justificar.",
                "rubrica": [copy.deepcopy(rubrica)],
            }
            for i in ("D1", "P1", "C1")
        },
        "carga_cognitiva": {"decisiones": ["Una sola comparación en cada tarea."], "no_medida": True},
    }


def test_materiales_integros_no_se_confunden_con_aprendizaje_real(recorrido):
    assert validar_recorrido(recorrido) == []
    resumen = resumen_mediciones(recorrido)
    assert resumen["materiales"] == "completos"
    assert resumen["estado_aprendizaje"] == "sin_evidencia_real"
    assert resumen["carga_cognitiva"]["estado"] == "no_medido"
    assert resumen["eficacia_validada"] is False


@pytest.mark.parametrize("defecto", ["sin_comprobacion", "misma_pregunta_otro_id", "sin_nivel", "sin_solucion"])
def test_rechaza_un_cierre_de_papel_incompleto_o_contaminado(recorrido, defecto):
    if defecto == "sin_comprobacion":
        recorrido["comprobacion_independiente"]["items"] = []
    elif defecto == "misma_pregunta_otro_id":
        recorrido["comprobacion_independiente"]["items"][0]["enunciado"] = recorrido["diagnostico"]["items"][0][
            "enunciado"
        ]
    elif defecto == "sin_nivel":
        del recorrido["soluciones_docente"]["C1"]["rubrica"][0]["requiere_apoyo"]
    else:
        del recorrido["soluciones_docente"]["C1"]
    assert validar_recorrido(recorrido)


def test_aritmetica_erronea_no_se_oculta_con_tolerancia(recorrido):
    recorrido["soluciones_docente"]["C1"]["calculos"] = [{"expresion": "95-65", "resultado": 40, "tolerancia": 9999}]
    assert any("no produce" in e for e in validar_recorrido(recorrido))


def test_hoja_reservada_no_entrega_claves_y_el_docente_conserva_tres_niveles(recorrido, tmp_path):
    destino = tmp_path / "materiales"
    manifest = materializar_recorrido(recorrido, destino)
    alumno = (destino / "estudiante.md").read_text()
    final = (destino / "comprobacion_estudiante.md").read_text()
    docente = (destino / "docente.md").read_text()
    assert "Sofía" not in alumno
    assert "### D1" not in alumno
    assert "Sofía" in final
    assert "### D1" in (destino / "diagnostico_estudiante.md").read_text()
    assert "Clave docente reservada" not in alumno + final
    assert "Requiere apoyo" in docente
    assert json.loads((destino / "recorrido.json").read_text()) == recorrido
    assert manifest["eficacia_validada"] is False
    with pytest.raises(FileExistsError):
        materializar_recorrido(recorrido, destino)


def _respuestas(recorrido, origen="estudiante"):
    return [
        {
            "origen": origen,
            "estudiante_id": "persona_anonima_1",
            "sesion_id": "sesion_1",
            "orden": orden,
            "fase": fase,
            "item_id": item,
            "respuesta": "Una respuesta real que la persona encargada contrastó con la rúbrica.",
            "sin_ayudas": fase == "comprobacion_independiente",
            "contexto_calificacion": "enunciado_rubrica_respuesta",
            "responsable_calificacion": "docente_anonimizado",
            "criterios": {c["criterio"]: "logrado" for c in recorrido["soluciones_docente"][item]["rubrica"]},
            "citas_criterios": {
                c["criterio"]: "Una respuesta real" for c in recorrido["soluciones_docente"][item]["rubrica"]
            },
        }
        for orden, (fase, item) in enumerate(
            (("diagnostico", "D1"), ("practica_guiada", "P1"), ("comprobacion_independiente", "C1")), 1
        )
    ]


def test_respuestas_simuladas_no_cierran_el_aprendizaje(recorrido):
    resumen = resumen_mediciones(recorrido, _respuestas(recorrido, "simulacion"))
    assert resumen["evidencias_simuladas"] == 3 and resumen["evidencias_reales"] == 0
    assert resumen["estado_aprendizaje"] == "sin_evidencia_real"


@pytest.mark.parametrize(
    "defecto",
    [
        "ayuda",
        "sin_diagnostico",
        "sin_practica",
        "duplicada",
        "criterio_incompleto",
        "vacia",
        "otra_persona",
        "sin_cita",
        "fuera_de_orden",
    ],
)
def test_solo_hay_cierre_observado_con_ciclo_completo_y_comprobacion_sin_ayuda(recorrido, defecto):
    respuestas = _respuestas(recorrido)
    assert resumen_mediciones(recorrido, respuestas)["estado_aprendizaje"] == "ciclo_observado_completo"
    if defecto == "ayuda":
        respuestas[-1]["sin_ayudas"] = False
    elif defecto == "sin_diagnostico":
        respuestas = respuestas[1:]
    elif defecto == "sin_practica":
        respuestas.pop(1)
    elif defecto == "duplicada":
        respuestas.append(copy.deepcopy(respuestas[-1]))
    elif defecto == "vacia":
        respuestas[-1]["respuesta"] = "   "
    elif defecto == "otra_persona":
        respuestas[-1]["estudiante_id"] = "persona_distinta"
    elif defecto == "sin_cita":
        respuestas[-1]["citas_criterios"] = {"Comparación de datos": "afirmación no escrita por la persona"}
    elif defecto == "fuera_de_orden":
        respuestas[0]["orden"], respuestas[-1]["orden"] = respuestas[-1]["orden"], respuestas[0]["orden"]
    else:
        respuestas[-1]["criterios"] = {}
    assert resumen_mediciones(recorrido, respuestas)["estado_aprendizaje"] == "requiere_seguimiento"


def test_material_invalido_no_se_confunde_con_falta_de_respuestas(recorrido):
    recorrido["comprobacion_independiente"]["items"] = []
    assert resumen_mediciones(recorrido, _respuestas(recorrido))["estado_aprendizaje"] == "material_invalidado"


def test_los_cinco_sucesores_tienen_materiales_reservados_y_reproducibles(tmp_path):
    from goes_science_kg.aprendizaje.materiales_recorridos import recorridos_finales

    recorridos = recorridos_finales()
    assert {r["id"] for r in recorridos} == {"R1", "R2", "R3", "R4", "R5"}
    for recorrido in recorridos:
        assert validar_recorrido(recorrido) == []
        a, b = tmp_path / "a" / recorrido["id"], tmp_path / "b" / recorrido["id"]
        assert materializar_recorrido(recorrido, a) == materializar_recorrido(recorrido, b)
        for p in a.iterdir():
            assert p.read_bytes() == (b / p.name).read_bytes()
        final = (a / "comprobacion_estudiante.md").read_text()
        practica = (a / "estudiante.md").read_text()
        diagnostico = (a / "diagnostico_estudiante.md").read_text()
        for item in recorrido["comprobacion_independiente"]["items"]:
            assert item["enunciado"] in final
            assert item["enunciado"] not in practica + diagnostico
            for rubrica in recorrido["soluciones_docente"][item["id"]]["rubrica"]:
                assert rubrica["requiere_apoyo"] in (a / "docente.md").read_text()
