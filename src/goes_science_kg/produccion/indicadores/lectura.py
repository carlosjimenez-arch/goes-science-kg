"""Lectura del indicador y de sus preparaciones, sin atribuir una revisión nueva."""

from __future__ import annotations

from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.produccion.indicadores.compilacion import COMPLETO
from goes_science_kg.produccion.revision_docente.lectura import markdown_revision


def markdown_indicador(material):
    d, i = material["documento"], material["documento"]["indicador"]
    estado = (
        "Contextos de origen con cuatro lecturas favorables"
        if material["estado"] == COMPLETO
        else ("Contextos de origen con pendientes")
    )
    texto = (
        f"# Paquete por indicador de logro\n\n{material['grados'][0]}.º · {material['asignatura']} · "
        f"{material['unidad']}\n\n**{estado}.** El reagrupamiento no tiene revisión específica.\n\n"
        "## Indicador de la malla o completación de referencia\n\n"
        f"{i['texto']}\n\n**Origen:** {i['origen']} · "
        f"**Código literal:** {i['codigo'] or 'sin código en el texto'}.\n\n"
    )
    if i["colision_codigo"]:
        texto += "**Código ambiguo:** hay otros textos con este código en el mismo grado, asignatura y unidad.\n\n"
    if i["origen"] == "completacion_derivada":
        texto += "El indicador original está vacío; esta referencia procede de la completación docente separada.\n\n"
    texto += (
        d["limite_biblioteca"] + "\n\n"
        "Las actividades, criterios y casos siguientes conservan su contexto completo. "
        "No se afirma que cada actividad evalúe por separado este indicador. Cuando el texto "
        "literal contiene una formulación corregida, usar el indicador docente de trabajo de "
        "la preparación, conservando el literal como procedencia.\n\n"
    )
    for n, p in enumerate(d["preparaciones"], 1):
        texto += f"## Preparación de origen {n} · {p['id']}\n\n"
        texto += (
            "\n".join("#" + linea if linea.startswith("#") else linea for linea in markdown_revision(p).splitlines())
            + "\n\n"
        )
    texto += (
        "## Archivos y procedencia\n\n"
        "Este ZIP individual incluye la guía, el JSON completo y su manifiesto SHA. Los Excel originales "
        "están en la colección por grado/asignatura y en la biblioteca, sin cambios; sus localizadores, "
        "celdas y SHA se conservan en cada preparación. No hay respuestas observadas de estudiantes.\n"
    )
    return texto


def indice_markdown(items):
    primero = items[0]
    texto = (
        f"# Indicadores · {primero['grado']}.º · {primero['asignatura']}\n\n"
        "Cada indicador tiene un ZIP individual, una guía y JSON. Las revisiones pertenecen a las "
        "preparaciones de origen; los pendientes siguen visibles. El código por sí solo no identifica "
        "un indicador. Los Excel de esta colección conservan los bytes originales.\n\n"
    )
    unidad = None
    for i in items:
        if unidad != i["unidad"]:
            unidad = i["unidad"]
            texto += f"## {unidad}\n\n"
        titulo = i["indicador"].replace("\n", " ").replace("[", "\\[").replace("]", "\\]")
        nombre = sha(i["id"].encode())
        texto += (
            f"- [{titulo}](paquete_indicador/{nombre}.md) · "
            f"[ZIP individual](indicadores/{nombre}.zip) · {i['estado_contextos']}\n"
        )
    return texto
