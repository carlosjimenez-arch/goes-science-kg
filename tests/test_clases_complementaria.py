"""La capa complementaria se ancla al guion exacto, decide sobre cada bloque y sólo usa enlaces registrados."""

from __future__ import annotations

import pytest
from pydantic import ValidationError
from test_clases import guion

from goes_science_kg.clases.complementaria import (
    AnexoClase,
    EvaluacionUnidad,
    markdown_anexo,
    validar_anexo,
    validar_evaluacion,
)

SHA = "a" * 64
FASES = ("aproximar", "explorar", "explicar", "indagar", "reforzar")
CANDIDATOS = {"previas": {("CON:x", "fila0")}, "continuidad": {("CON:x", "fila9")}, "fuentes": set()}


def anexo(**cambios):
    base = {
        "version": "anexo-clase-1",
        "fila_id": "fila1",
        "guion_sha256": SHA,
        "recursos": {
            "nivel": "sin_materiales",
            "materiales": [{"material": "papel", "sustituto_casero": None, "imprescindible": False}],
            "requiere_electricidad": False,
            "requiere_agua": False,
            "requiere_exterior": False,
            "requiere_conectividad": False,
            "costo": "nulo",
        },
        "version_minima": {
            "minutos_efectivos": 45,
            "ajustes": [
                {
                    "sesion": 1,
                    "bloque": i,
                    "accion": "conservar" if f != "reforzar" else "acortar",
                    "minutos": 9,
                    "nota": None if f != "reforzar" else "Se resume el refuerzo en una pregunta oral de cierre.",
                }
                for i, f in enumerate(FASES, 1)
            ],
            "tarea_prioritaria": 1,
            "evidencia_minima": "Tabla con dos propiedades observables y una explicación del criterio.",
        },
        "progresion": {
            "ideas_previas": [
                {
                    "concepto": "CON:x",
                    "fila_id": "fila0",
                    "grado": 2,
                    "como_usarlo": "Recordar cómo se describían objetos en 2.º grado.",
                }
            ],
            "continuidad": [],
            "sin_antecedente": None,
        },
        "inclusion": {
            "adecuaciones": [
                {"necesidad": n, "ajuste": "Ajuste concreto y aplicable para esta clase de comparación de materiales."}
                for n in ("discapacidad_visual", "discapacidad_auditiva", "dificultad_lectora", "discapacidad_motora")
            ],
            "multigrado": "El grado inferior describe una propiedad y el superior justifica la clasificación completa.",
            "contexto_rural": "Se usan materiales del entorno escolar: hojas, piedras, madera y recipientes plásticos.",
            "hoja_lectura_facil": "1. Mira los dos dibujos. 2. Escribe cómo se ve cada material. " * 4,
        },
        "indagacion": {
            "nivel_actual": "estructurada",
            "nivel_propuesto": "guiada",
            "pregunta_ejemplo": "¿Qué material se raya más fácilmente?",
            "como_formulan_preguntas": "Cada equipo propone una pregunta comprobable que compare dos materiales.",
            "variable_independiente": "material",
            "variable_dependiente": "marca visible tras rayar",
            "variables_controladas": ["fuerza aplicada"],
            "diseno_por_estudiantes": "El equipo decide con qué raya y cómo registra el resultado en una tabla.",
            "error_y_repeticion": "Repiten tres veces y discuten por qué los resultados pueden variar entre intentos.",
            "seguridad": "No se usan objetos cortantes ni vidrio.",
        },
        "contexto_nacional": {"afirmaciones": [], "fuente_a_consultar": "Programa de estudio de Ciencias del MINED."},
    }
    return AnexoClase.model_validate(base | cambios)


def test_anexo_valido_y_su_lectura_docente():
    a = anexo()
    assert validar_anexo(a, guion(), SHA, CANDIDATOS) == []
    texto = markdown_anexo(a.model_dump(mode="json"), "Comparar materiales")
    assert "Versión mínima (45 minutos" in texto and "Viene de 2.º" in texto


def test_anexo_exige_el_guion_exacto_cada_bloque_y_enlaces_registrados():
    a = anexo()
    assert "anclado" in validar_anexo(a, guion(), "b" * 64, CANDIDATOS)[0]
    datos = a.model_dump(mode="json")
    datos["version_minima"]["ajustes"] = datos["version_minima"]["ajustes"][:-1]
    assert any("cada bloque" in e for e in validar_anexo(AnexoClase.model_validate(datos), guion(), SHA, CANDIDATOS))
    datos = a.model_dump(mode="json")
    datos["progresion"]["ideas_previas"][0]["fila_id"] = "inventada"
    assert any("no registrado" in e for e in validar_anexo(AnexoClase.model_validate(datos), guion(), SHA, CANDIDATOS))


def test_version_minima_conserva_explicacion_y_cabe_en_el_tiempo_efectivo():
    datos = anexo().model_dump(mode="json")
    datos["version_minima"]["ajustes"][2] |= {"accion": "omitir", "minutos": 0, "nota": "Se omite la explicación."}
    errores = validar_anexo(AnexoClase.model_validate(datos), guion(), SHA, CANDIDATOS)
    assert any("conserva la explicación" in e for e in errores)
    datos = anexo().model_dump(mode="json")
    datos["version_minima"]["minutos_efectivos"] = 30
    assert any("debe sumar" in e for e in validar_anexo(AnexoClase.model_validate(datos), guion(), SHA, CANDIDATOS))


def test_inclusion_exige_las_cuatro_discapacidades_basicas():
    datos = anexo().model_dump(mode="json")
    datos["inclusion"]["adecuaciones"][3]["necesidad"] = "altas_capacidades"
    with pytest.raises(ValidationError, match="obligatorias"):
        AnexoClase.model_validate(datos)


def item(id_, dominio, formato="opcion_multiple", fila="fila1"):
    opciones = [
        {
            "letra": letra,
            "texto": f"Opción {letra}",
            "concepcion_que_detecta": None if letra == "A" else "Confunde utilidad con propiedad.",
        }
        for letra in "ABCD"
    ]
    rubrica = [
        {
            "criterio": "Explica su razonamiento con evidencia.",
            "logrado": "Usa dos evidencias coherentes.",
            "en_proceso": "Usa una evidencia coherente.",
            "requiere_apoyo": "No relaciona la evidencia con la conclusión.",
        }
    ]
    return {
        "id": id_,
        "fila_id": fila,
        "dominio": dominio,
        "formato": formato,
        "enunciado": "Una estudiante compara dos materiales del aula. ¿Qué propiedad puede comprobar?",
        "opciones": opciones if formato == "opcion_multiple" else [],
        "clave": "A" if formato == "opcion_multiple" else "Compara la dureza rayando ambos con la misma moneda.",
        "justificacion": "La dureza se comprueba observando cuál material se raya con el mismo objeto.",
        "rubrica": [] if formato == "opcion_multiple" else rubrica,
        "calculos": [],
        "datos_simulados": False,
    }


def evaluacion(items):
    return EvaluacionUnidad.model_validate(
        {"version": "evaluacion-unidad-1", "unidad_id": "U1", "minutos": 40, "items": items}
    )


def test_evaluacion_balancea_dominios_y_cubre_cada_objetivo():
    items = [item(f"I0{i}", d) for i, d in enumerate(("conocer", "aplicar", "aplicar", "razonar", "conocer"), 1)]
    ev = evaluacion([*items, item("I06", "razonar", "respuesta_construida", "fila2")])
    assert validar_evaluacion(ev, "U1", {"fila1", "fila2"}) == []
    assert any("Faltan" in e for e in validar_evaluacion(ev, "U1", {"fila1", "fila2", "fila3"}))
    with pytest.raises(ValidationError, match="razonamiento"):
        evaluacion(
            [item(f"I0{i}", "conocer" if i < 3 else "aplicar") for i in range(1, 6)]
            + [item("I06", "aplicar", "respuesta_construida")]
        )


def test_distractor_sin_concepcion_alternativa_se_rechaza():
    malo = item("I01", "aplicar")
    malo["opciones"][1]["concepcion_que_detecta"] = None
    with pytest.raises(ValidationError, match="concepción alternativa"):
        evaluacion([malo] + [item(f"I0{i}", "razonar", "respuesta_construida") for i in range(2, 7)])
