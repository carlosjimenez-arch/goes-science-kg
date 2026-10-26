"""Guía docente legible: separar propuesta, original, respuesta esperada y estado de revisión."""

from __future__ import annotations


def _lista(valores):
    return "\n".join(f"- {v}" for v in valores) + "\n\n"


def _dato(valor):
    """Representa datos docentes sin exponer literales de diccionarios Python."""
    if isinstance(valor, dict):
        return _lista(f"{k.replace('_', ' ')}: {v}" for k, v in valor.items())
    if isinstance(valor, list):
        if valor and all(isinstance(v, dict) for v in valor):
            columnas = list(dict.fromkeys(k for fila in valor for k in fila))

            def celda(v):
                return str(v).replace("|", "\\|").replace("\n", " ")

            filas = [" | ".join(c.replace("_", " ") for c in columnas), " | ".join("---" for _ in columnas)]
            filas += [" | ".join(celda(f.get(c, "")) for c in columnas) for f in valor]
            return "\n".join("| " + f + " |" for f in filas) + "\n\n"
        return _lista(valor)
    return str(valor) + "\n\n"


def markdown_didactica(material):
    d = material["documento"]
    texto = (
        f"# {material['titulo']}\n\nGrado: {material['grados'][0]} · {material['asignatura']}\n\n"
        f"**Diseño didáctico propuesto — revisión de contenido pendiente.**\n\n{d['limite_biblioteca']}\n\n"
    )
    if material["tipo"] == "paquete_unidad":
        u = d["didactica_unidad"]
        texto += "## Articulación de la unidad\n\n" + u["articulacion"] + "\n\n"
        texto += "## Desarrollo de la práctica\n\n" + _lista(u["progresion_propuesta"])
        texto += u["regla"] + "\n\n## Mapa de oportunidades por microhabilidad\n\n"
        for codigo, pasos in sorted(u["ruta_por_habilidad"].items()):
            texto += f"### {codigo}\n\n" + _lista(f"{p['fila_id']}: {p['evidencia_propuesta']}" for p in pasos)
        texto += "## Objetivos documentales\n\n" + _lista(f["objetivo"] for f in d["objetivos"])
        if u["filas_sin_tareas"]:
            texto += "## Insumo por completar\n\n" + _lista(u["filas_sin_tareas"])
        return texto
    f = d["didactica"]
    texto += (
        "## Propósito, producto y evidencia\n\n"
        f"**Objetivo original:** {f['objetivo_original']}\n\n"
        f"**Indicador original:** {f['indicador_original'] or 'Falta en el insumo.'}\n\n"
        f"**Producto original:** {f['producto_original'] or 'Falta en el insumo.'}\n\n"
    )
    if f["controles_cientificos"]:
        texto += "## Correcciones y cautelas científicas\n\n"
        texto += (
            "Las notas siguientes son propuestas derivadas. El original bajo "
            "alerta se conserva como evidencia documental.\n\n"
        )
        for c in f["controles_cientificos"]:
            texto += f"- {c['nota_docente_propuesta']} Referencia: {c['referencia_id']}.\n"
        texto += "\n"
    texto += "## Transposición y apoyos\n\n" + _lista(f["transposicion"]["articulacion"])
    texto += _lista(v for k, v in f["perfil_apoyo"].items() if k != "tramo")
    texto += f["transposicion"]["vocabulario"] + "\n\n"
    a = f["transposicion"]["apoyo_contextual_antecedente"]
    if a:
        texto += (
            "### Apoyo específico para contrastar con la edición anterior\n\n"
            f"{a['andamiaje']}\n\nContexto propuesto anterior: {a['contexto_salvador']}\n\n"
            f"{a['limite']}\n\n"
        )
    if f["caso_resuelto"]:
        caso = f["caso_resuelto"]
        texto += f"## Caso de contraste: {caso['id']}\n\n{caso['reto']}\n\n{caso['contexto']}\n\n"
        texto += f"**Ideas previas:** {caso['ideas_previas']}\n\n"
        texto += f"**Origen de los datos:** {caso['datos']['origen']}.\n\n"
        for clave, valor in caso["datos"].items():
            if clave != "origen":
                texto += f"**{clave.replace('_', ' ')}**\n\n" + _dato(valor)
        texto += "\n### Consignas propuestas\n\n" + _lista(caso["consignas"])
        texto += "### Clave razonada para el docente\n\n" + _lista(caso["clave_docente"])
        texto += f"**Andamiaje:** {caso['andamiaje']}\n\n**Transferencia:** {caso['transferencia']}\n\n"
        texto += f"**Seguridad y alcance:** {caso['seguridad']} {caso['desempeno_practico']}.\n\n"
    texto += "## Tareas de la malla y microhabilidades declaradas\n\n"
    if f["controles_cientificos"]:
        texto += (
            "**Originales bajo alerta:** contrastar con las notas y el caso "
            "propuesto antes de usarlos como consignas.\n\n"
        )
    for tarea in f["tareas"]:
        nombre = tarea["definicion"]["nombre"] if tarea["definicion"] else "Definición no disponible"
        texto += f"### {tarea['fase'].title()} · {tarea['codigo']} · {nombre}\n\n{tarea['actividad_literal']}\n\n"
        texto += (
            f"Origen: {tarea['origen']['hoja']}!{','.join(tarea['origen']['celdas'])}. "
            "Alineación semántica no verificada.\n\n"
        )
    texto += "## Observación, retroalimentación y retirada de apoyos\n\n"
    for c in f["criterios"]:
        texto += f"### {c['codigo']}\n\n**Evidencia propuesta:** {c['evidencia_propuesta']}\n\n"
        texto += _lista(c["criterios_observables"])
        texto += (
            f"**Error a indagar, sin atribuirlo al estudiante:** {c['error_a_indagar']}\n\n"
            f"**Apoyo:** {c['apoyo']}\n\n**Retroalimentación:** {c['retroalimentacion']}\n\n"
            f"**Retirar el apoyo:** {c['retirada_del_apoyo']}\n\n"
            f"**Variación para aplicar:** {c['transferencia']}\n\n"
        )
    texto += "## Aplicación y recuperación\n\n" + _lista(f["aplicacion"].values())
    texto += _lista(v for k, v in f["recuperacion"].items() if k != "estado")
    texto += "## Factibilidad y evaluación\n\n" + _lista(
        [
            f["contexto_y_factibilidad"]["si_faltan_instrumentos"],
            f["contexto_y_factibilidad"]["seguridad"],
            f["transposicion"]["rubrica"]["regla"],
            "No se han observado respuestas ni logros de estudiantes; los criterios son propuestas de diseño.",
        ]
    )
    if f["incidencias"]:
        texto += "## Pendientes del diseño\n\n" + _lista(str(i) for i in f["incidencias"])
    fuente = d["fuente_original"]
    texto += (
        f"## Procedencia\n\nFila: {f['fila_id']}\n\nArchivo: {fuente['archivo']}\n\n"
        f"SHA-256 del archivo: {fuente['sha256']}\n\n"
        "El JSON conserva las celdas originales, sus anclas y todo el expediente. "
        "El uso de referentes internacionales no certifica alineación ni equivalencia entre grados.\n"
    )
    return texto
