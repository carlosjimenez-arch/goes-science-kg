"""Render complete teaching materials while keeping measurement claims explicit."""

from __future__ import annotations

import hashlib

from goes_science_kg.clases.complementaria import EvaluacionUnidad, markdown_anexo


def nombre(identidad: str) -> str:
    """Return a portable content-independent filename for a stable identity."""
    return hashlib.sha256(identidad.encode()).hexdigest()


def markdown_evaluacion(datos: dict, titulo: str, *, estudiante: bool = False) -> str:
    """Render every assessment item and all rubric levels only in the teacher sheet."""
    evaluacion = EvaluacionUnidad.model_validate(datos)
    lineas = [f"# Evaluación · {titulo}", "", f"Duración sugerida: {evaluacion.minutos} minutos.", ""]
    lineas += [
        "Hoja del estudiante. Responde sin consultar el solucionario."
        if estudiante
        else "Guía docente. Una respuesta a estos ítems no demuestra transferencia estable ni mide carga cognitiva.",
        "",
    ]
    for item in evaluacion.items:
        lineas += [f"## {item.id}", "", item.enunciado, ""]
        if item.datos_simulados:
            lineas += ["Datos simulados para esta actividad; no son mediciones de una población real.", ""]
        lineas += [f"- {o.letra}) {o.texto}" for o in item.opciones]
        lineas.append("")
        if estudiante:
            lineas += ["Respuesta y justificación: __________________________________________", ""]
            continue
        lineas += [
            f"Objetivo: `{item.fila_id}`. Dominio declarado por el autor: {item.dominio}.",
            "",
            f"Clave: {item.clave}",
            "",
            f"Justificación: {item.justificacion}",
            "",
        ]
        lineas += [
            f"- Distractor {o.letra}: {o.concepcion_que_detecta}" for o in item.opciones if o.concepcion_que_detecta
        ]
        for criterio in item.rubrica:
            lineas += [
                f"### Criterio: {criterio.criterio}",
                "",
                f"- Logrado: {criterio.logrado}",
                f"- En proceso: {criterio.en_proceso}",
                f"- Requiere apoyo: {criterio.requiere_apoyo}",
                "",
            ]
        for calculo in item.calculos:
            lineas += [f"Comprobación docente: `{calculo.expresion}` = {calculo.resultado} {calculo.unidad}.", ""]
    return "\n".join(lineas) + "\n"


def markdown_unidad(material: dict) -> str:
    """Show both available scripts and every missing objective with its exact reason."""
    datos = material["documento"]
    faltan = datos.get("objetivos_sin_guion_liberado", [])
    lineas = [
        f"# {material['titulo']}",
        "",
        f"Grado: {material['grados'][0]} · {material['asignatura']}",
        "",
        f"Cobertura de guiones: {len(datos['guiones'])} disponibles; {len(faltan)} objetivos sin guion liberado.",
        "",
        "**Unidad incompleta: los objetivos que faltan se detallan abajo.**"
        if faltan or datos.get("completa") is False
        else "Todos los objetivos de esta unidad tienen guion en el catálogo de procedencia.",
        "",
        "El orden es documental. La disponibilidad de archivos no acredita aprendizaje ni carga horaria oficial.",
        "",
    ]
    for clase in datos["guiones"]:
        prefijo = nombre(clase["fila_id"])
        lineas += [
            f"- [{clase['titulo']}](../clases/{prefijo}.docente.md) · "
            f"[Hoja de estudiante](../clases/{prefijo}.estudiante.md).",
            "",
            clase["objetivo"],
            "",
        ]
    if faltan:
        lineas += ["## Objetivos sin guion liberado", ""]
        for pendiente in faltan:
            lineas += [
                f"### {pendiente.get('titulo', pendiente['fila_id'])}",
                "",
                f"Identidad: `{pendiente['fila_id']}`. Estado: `{pendiente['estado']}`.",
                "",
                pendiente["motivo"],
                "",
            ]
    lineas += ["## Alcance de la edición", "", datos["licencia_adaptacion"], ""]
    return "\n".join(lineas)


def markdown_anexo_completo(datos: dict, titulo: str) -> str:
    """Retain annex content and expose every progression destination as a local link."""
    lineas = [markdown_anexo(datos, titulo), "## Destinos verificables de progresión", ""]
    for grupo in ("ideas_previas", "continuidad"):
        for enlace in datos["progresion"][grupo]:
            lineas += [
                f"- [{enlace['concepto']} · {enlace['grado']}.º]"
                f"(../objetivos/{nombre(enlace['fila_id'])}.md) · `{enlace['fila_id']}`.",
            ]
    lineas += ["", "## Trazabilidad", "", f"Guion antecedente SHA-256: `{datos['guion_sha256']}`.", ""]
    return "\n".join(lineas)


def plan_cognitivo(material: dict) -> str:
    """Provide a usable teaching plan without converting word counts into cognitive-load scores."""
    guion = material["documento"]["guion"]
    lineas = [
        "## Organización del trabajo y observación del esfuerzo",
        "",
        "**Estado de carga cognitiva: no medida.** Este plan organiza el material; no asigna una puntuación "
        "de carga a partir de palabras, minutos, fases, grado o aprobación automática.",
        "",
        "1. Active las ideas previas de abajo con una pregunta oral y pida que expliquen una razón. "
        "Una respuesta aislada abre una hipótesis; registre qué parte necesita apoyo.",
        "2. Muestre una representación y una consigna cada vez. Deje a la vista datos y unidades junto al "
        "paso que los usa; permita explicación oral o dibujo accesible.",
        "3. Use la primera tarea como ejemplo trabajado sólo después del diagnóstico: explique el dato, "
        "la decisión y la comprobación de cada paso. Luego oculte pasos de forma gradual y pida completarlos.",
        "4. Reserve la tarea siguiente para trabajo sin pistas. Compruebe que no repite el ejemplo, sus datos "
        "o su solución; si los repite, diseñe otra situación antes de inferir transferencia. "
        "Los cinco recorridos finales adjuntos sí incluyen pruebas nuevas separadas.",
        "5. Registre corrección y explicación con la rúbrica. Una actividad posterior debe comprobar retención; "
        "la entrega de archivos y la práctica asistida no sustituyen esa evidencia.",
        "",
        "### Ideas previas de esta clase",
        "",
        *[f"- {idea}" for idea in guion["conocimientos_a_activar"]],
        "",
        "### Ajustes disponibles",
        "",
        *[f"- {apoyo}" for apoyo in guion["apoyos"]],
        "",
        "### Registro docente (en blanco; sin datos de estudiantes)",
        "",
        "| Momento | Ítem y versión | Apoyos usados | Respuesta y criterio | Esfuerzo informado y condiciones |",
        "|---|---|---|---|---|",
        "| Diagnóstico | | | | |",
        "| Práctica guiada | | | | |",
        "| Comprobación sin ayuda | | | | |",
        "| Retención posterior | | | | |",
        "",
        "Un autoinforme mide esfuerzo percibido bajo condiciones descritas, no identifica por sí solo "
        "carga intrínseca/extrínseca ni diagnostica capacidad. Consulte el protocolo pedagógico adjunto "
        "antes de aplicar una escala al grado correspondiente.",
        "",
    ]
    return "\n".join(lineas)
