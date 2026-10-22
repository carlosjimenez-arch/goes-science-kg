"""Guiones legibles: hoja del estudiante separada de soluciones, fuentes y dictámenes."""

from __future__ import annotations

import hashlib
import json


def markdown_clase(material: dict, *, estudiante: bool = False) -> str:
    d = material["documento"]
    g = d["guion"]
    lineas = [f"# {g['titulo']}", "", f"Grado: {material['grados'][0]} · {material['asignatura']}", ""]
    lineas += ["## Objetivo", "", g["objetivo"], ""]
    if not estudiante:
        lineas += [
            "Revisión automática de este guion: cuatro roles. No constituye aprobación institucional.",
            "Duración propuesta: " + str(60 * len(g["sesiones"])) + " minutos.",
            "",
            "## Preparación y activación",
            "",
            *["- " + t for t in g["conocimientos_a_activar"]],
            "",
            "## Explicación científica para el docente",
            "",
        ]
        for a in g["explicacion_docente"]:
            lineas += [a["texto"], "Fuentes: " + ", ".join(a["fuentes_ids"]), ""]
        for sesion in g["sesiones"]:
            lineas += [f"## Sesión {sesion['numero']}: {sesion['titulo']} · 60 minutos propuestos", ""]
            for bloque in sesion["bloques"]:
                lineas += [
                    f"### {bloque['fase'].capitalize()} · {bloque['minutos']} minutos",
                    "",
                    "Docente: " + bloque["docente"],
                    "",
                    "Estudiantes: " + bloque["estudiantes"],
                    "",
                    "Evidencia: " + bloque["evidencia_observable"],
                    "",
                ]
    lineas += ["## Hoja de trabajo del estudiante", ""]
    for numero, tarea in enumerate(g["tareas"], 1):
        lineas += [f"### Tarea {numero}", "", tarea["enunciado"], ""]
        if tarea["datos_simulados"]:
            lineas += ["Escenario didáctico con datos simulados; no son mediciones realizadas en el aula.", ""]
    if estudiante:
        lineas += [
            "## Atribución",
            "",
            d["licencia_adaptacion"],
            "",
            "La guía docente del mismo material conserva las fuentes, sus localizadores y las condiciones de uso.",
            "",
        ]
    if not estudiante:
        lineas += ["## Solucionario y evaluación · uso docente", ""]
        for numero, tarea in enumerate(g["tareas"], 1):
            lineas += [f"### Tarea {numero}", "", tarea["respuesta_esperada"], "", tarea["explicacion_solucion"], ""]
            for criterio in tarea["rubrica"]:
                lineas += [
                    "Criterio: " + criterio["criterio"],
                    "",
                    "- Logrado: " + criterio["logrado"],
                    "- En proceso: " + criterio["en_proceso"],
                    "- Requiere apoyo: " + criterio["requiere_apoyo"],
                    "",
                ]
            for calculo in tarea["calculos"]:
                lineas += [f"Comprobación: `{calculo['expresion']}` = {calculo['resultado']} {calculo['unidad']}", ""]
        for campo, titulo in (
            ("recursos", "Recursos propuestos"),
            ("alternativa_sin_recursos", "Alternativa sin recursos adicionales"),
            ("apoyos", "Apoyos"),
            ("dificultad_previsible", "Dificultad previsible"),
            ("retroalimentacion", "Retroalimentación"),
            ("seguridad", "Seguridad"),
            ("implementacion_condicionada", "Condiciones de implementación"),
        ):
            valor = g[campo]
            lineas += ["## " + titulo, "", *(("- " + v for v in valor) if isinstance(valor, list) else [valor]), ""]
        lineas += ["## Fuentes, atribución y trazabilidad", ""]
        for fuente in d["fuentes_cientificas"]:
            f = fuente["fuente"]
            lineas += [
                f"- {fuente['id']}: {f['institucion']}, {f['libro']}, {f['titulo']}. "
                f"[Texto fuente]({f['url']}); bloque {f['localizador']['bloque']}; "
                f"SHA-256 {f['sha256']}. [Licencia {f['licencia']}]({f['licencia_url']})."
            ]
        lineas += [
            "",
            d["licencia_adaptacion"],
            "",
            "Origen curricular, alertas conservadas y dictámenes exactos:",
            "",
            "```json",
            json.dumps(
                {
                    k: d[k]
                    for k in ("snapshot_id", "preparacion_id", "origen", "alerta_original", "enmiendas", "dictamenes")
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
        ]
    return "\n".join(lineas) + "\n"


def markdown_unidad(material: dict) -> str:
    d = material["documento"]
    lineas = [
        "# " + material["titulo"],
        "",
        f"Grado: {material['grados'][0]} · {material['asignatura']}",
        "",
        "Orden documental del currículo. Las duraciones son propuestas por objetivo; "
        "su suma no acredita una carga horaria oficial ni una secuencia pedagógica validada.",
        "",
    ]
    for clase in d["guiones"]:
        archivo = hashlib.sha256(clase["material_id"].encode()).hexdigest()
        lineas += [
            f"- [{clase['titulo']}](../clases/{archivo}.docente.md) — {clase['duracion_minutos']} min. "
            f"[Hoja de estudiante](../clases/{archivo}.estudiante.md).",
            "",
            clase["objetivo"],
            "",
            "Identificador para API: `" + clase["material_id"] + "`.",
            "",
        ]
    lineas += ["", "Los JSON y las hojas docente/estudiante se encuentran en `clases/` dentro de la descarga.", ""]
    lineas += [d["licencia_adaptacion"], ""]
    return "\n".join(lineas)
