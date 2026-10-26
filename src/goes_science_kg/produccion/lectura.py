"""Lectura docente de la edición final sin convertir anotaciones en validaciones."""

from __future__ import annotations

import json


def markdown_produccion(material: dict) -> str:
    d = material["documento"]
    texto = (
        f"# {material['titulo']}\n\n"
        f"Grados: {', '.join(map(str, material['grados']))} · {material['asignatura']}\n\n"
        f"**Estado: {material['estado']}**\n\n{d['limite_biblioteca']}\n\n"
    )
    if d["alertas"]:
        texto += "## Incidencias que requieren resolución\n\n"
        for a in d["alertas"]:
            texto += f"- {a['codigo']}: {a['descripcion']}\n"
        texto += "\n"
    if material["tipo"] == "paquete_unidad":
        texto += "## Objetivos en orden documental\n\n"
        for f in d["objetivos"]:
            texto += f"- {f['objetivo']} ({f['id']})\n"
    else:
        f = d["original"]
        for campo, titulo in (
            ("procedimental", "Objetivo original"),
            ("contenido", "Contenido"),
            ("subcontenido", "Subcontenidos"),
            ("indicadores_logro", "Indicadores declarados"),
            ("indicador_avanzado", "Indicador avanzado declarado"),
            ("evidencia_aprendizaje", "Evidencia de aprendizaje declarada"),
            ("actitudinal", "Actitudinal"),
            ("actividad_digital", "Actividad digital declarada"),
        ):
            texto += f"## {titulo}\n\n{f[campo] or 'No consta en la malla.'}\n\n"
        texto += "## Fases de la malla final\n\n"
        for nombre, fase in f["fases"].items():
            if fase["presente_en_hoja"]:
                texto += f"### {nombre.title()}\n\n{fase['texto'] or 'Celda vacía.'}\n\n"
        if d["celdas_sin_rol"]:
            texto += "## Celdas conservadas sin fase o campo asignado\n\n"
            for c in d["celdas_sin_rol"]:
                texto += f"- {c['coordenada']}: {c['valor']}\n"
    texto += "\n## Trazabilidad y límites\n\n```json\n"
    texto += json.dumps(
        {k: v for k, v in d.items() if k not in {"original", "objetivos"}}, ensure_ascii=False, indent=2
    )
    return texto + "\n```\n"
