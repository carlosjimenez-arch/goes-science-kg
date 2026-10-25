"""Guiones legibles: hoja del estudiante separada de soluciones, fuentes y dictámenes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict


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
    datos = d.get("datos_contextuales")
    if datos:
        lineas += ["## Datos para las actividades", "", datos["titulo"], "", datos["descripcion_pedagogica"], ""]
        columnas = list(datos["columnas"])
        lineas += ["| " + " | ".join(datos["columnas"][k] for k in columnas) + " |"]
        lineas += ["| " + " | ".join("---" for _ in columnas) + " |"]
        lineas += ["| " + " | ".join(str(f[k]) for k in columnas) + " |" for f in datos["filas"]]
        lineas += ["", *datos["limites_inferencia"], ""]
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
        if datos:
            lineas += [datos["metodo_verificacion"], "", datos["limite_verificacion"], ""]
            for f in datos["fuentes"]:
                lineas += [f"- [Fuente del insumo tabular]({f['url']}).", ""]
        for fuente in d["fuentes_cientificas"]:
            f = fuente["fuente"]
            localizador = f["localizador"]
            ubicacion = (
                "bloque " + localizador["bloque"]
                if "bloque" in localizador
                else "rangos de bytes " + ", ".join(f"{a}:{z}" for a, z in localizador["selecciones"])
            )
            edicion = f.get("libro", f.get("version_publicacion", f.get("fecha_publicacion", "")))
            lineas += [
                f"- {fuente['id']}: {f['institucion']}, {edicion}, {f['titulo']}. "
                f"[Texto fuente]({f['url']}); {ubicacion}; "
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
                }
                | (
                    {"ajuste_didactico_auditoria": d["ajuste_didactico_auditoria"]}
                    if d.get("ajuste_didactico_auditoria")
                    else {}
                ),
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


def markdown_indice(materiales: list[dict]) -> str:
    grupos = defaultdict(list)
    for m in materiales:
        grupos[(m["grados"][0], m["asignatura"])].append(m)
    lineas = [
        "# Índice de guiones de Ciencias V4",
        "",
        "Abre una unidad y sigue sus enlaces a la guía docente y a la hoja del estudiante.",
        "Los archivos se pueden consultar sin conexión; los enlaces a las fuentes oficiales requieren Internet.",
        "",
    ]
    for (grado, asignatura), grupo in sorted(grupos.items()):
        lineas += [f"## Grado {grado} · {asignatura}", ""]
        unidades = sorted((m for m in grupo if m["tipo"] == "guion_unidad"), key=lambda m: m["titulo"])
        incluidos = {g["material_id"] for u in unidades for g in u["documento"]["guiones"]}
        for m in unidades:
            nombre = hashlib.sha256(m["id"].encode()).hexdigest()
            lineas.append(f"- [{m['titulo']}](unidades/{nombre}.md) · {len(m['documento']['guiones'])} guiones.")
        for m in sorted(
            (m for m in grupo if m["tipo"] == "guion_clase" and m["id"] not in incluidos),
            key=lambda m: m["titulo"],
        ):
            nombre = hashlib.sha256(m["id"].encode()).hexdigest()
            lineas.append(
                f"- [{m['titulo']}](clases/{nombre}.docente.md) · [Hoja de estudiante](clases/{nombre}.estudiante.md)."
            )
        lineas.append("")
    return "\n".join(lineas) + "\n"
