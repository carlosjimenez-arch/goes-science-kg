"""Guía efectiva legible; el original permanece en el expediente, separado de las instrucciones."""

from __future__ import annotations

from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.produccion.didactica.lectura import _dato, _lista


def markdown_revision(material):
    d = material["documento"]
    e, revision = d["edicion_docente"], d["revision_docente"]
    completa = revision["estado"] == "revision_automatica_completa"
    estado = "Cuatro lecturas automáticas favorables" if completa else "Revisión automática con pendientes"
    texto = (
        f"# {material['titulo']}\n\nGrado: {material['grados'][0]} · {material['asignatura']}\n\n"
        f"**{estado}.**\n\n{d['limite_biblioteca']}\n\n"
    )
    if not completa:
        texto += "## Pendientes antes de considerar esta preparación respaldada\n\n"
        if revision["faltan_roles"]:
            texto += "Faltan lecturas válidas: " + ", ".join(revision["faltan_roles"]) + ".\n\n"
        if revision.get("roles_sin_control_superado"):
            texto += "No superaron el control negativo: " + ", ".join(revision["roles_sin_control_superado"]) + ".\n\n"
        for v in revision["lecturas"]:
            if v["veredicto"] != "aprobar":
                texto += f"**{v['rol']} · {v['veredicto']}:** {v['comprobacion']}\n\n"
                texto += _lista(h["problema"] for h in v["hallazgos"])
        if revision.get("dependencias_pendientes"):
            texto += "Hay objetivos de esta unidad pendientes de respaldo; consultar su estado en el mapa.\n\n"
    if material["tipo"] == "paquete_unidad":
        texto += "## Articulación y progresión propuesta\n\n" + e["articulacion"] + "\n\n"
        texto += _lista(e["progresion"]) + e["regla"] + "\n\n"
        texto += "## Objetivos y oportunidades de práctica\n\n"
        for f in d["mapa_docente"]:
            archivo = sha(f["fila_id"].encode()) + ".md"
            texto += (
                f"- [{f['objetivo']}](../paquete_objetivo/{archivo}) · "
                f"{', '.join(f['codigos'])} · {f['estado_revision']}\n"
            )
        texto += "\nLos enlaces entre documentos funcionan dentro del ZIP completo.\n\n"
    else:
        texto += (
            "## Propósito y evaluación de esta edición\n\n"
            f"**Objetivo original:** {d['original']['procedimental']}\n\n"
            f"**Indicador docente:** {e['indicador']}\n\n**Producto:** {e['producto']}\n\n"
        )
        if e["completacion"]:
            texto += (
                "**Completación derivada:** las fases, el indicador y el producto de la fila original "
                "siguen vacíos. Esta preparación los propone en una capa separada.\n\n"
                + e["completacion"]["indicador_procedencia"]
                + "\n\n"
            )
            texto += _lista(e["completacion"]["criterios_especificos"])
        texto += "## Núcleo conceptual de trabajo\n\n" + e["explicacion"] + "\n\n"
        texto += "## Actividades de la edición docente\n\n"
        for t in e["actividades"]:
            texto += f"### {t['fase'].title()} · {t['codigo']}\n\n{t['texto']}\n\n"
        texto += "## Evidencia, retroalimentación y autonomía\n\n"
        for c in e["criterios"]:
            texto += f"### {c['codigo']}\n\n**Evidencia:** {c['evidencia_propuesta']}\n\n"
            texto += _lista(c["criterios_observables"])
            for campo, nombre in (
                ("error_a_indagar", "Error a explorar, sin atribuirlo al estudiante"),
                ("apoyo", "Apoyo"),
                ("retroalimentacion", "Retroalimentación"),
                ("retirada_del_apoyo", "Retirada de ayudas"),
                ("transferencia", "Aplicación"),
            ):
                texto += f"**{nombre}:** {c[campo]}\n\n"
        texto += "## Apoyos y recuperación\n\n" + _lista(v for k, v in e["perfil_apoyo"].items() if k != "tramo")
        texto += _lista(v for k, v in e["aplicacion"].items() if k != "tarea_de_transferencia_original")
        texto += _lista(v for k, v in e["recuperacion"].items() if k != "estado")
        caso = e["caso_resuelto"]
        if caso:
            texto += f"## Caso trabajado · {caso['id']}\n\n{caso['reto']}\n\n{caso['contexto']}\n\n"
            texto += (
                f"**Ideas iniciales:** {caso['ideas_previas']}\n\n"
                f"**Origen de los datos:** {caso['datos']['origen']}\n\n"
            )
            for k, v in caso["datos"].items():
                if k != "origen":
                    texto += f"**{k.replace('_', ' ')}**\n\n" + _dato(v)
            texto += "### Consignas del caso\n\n" + _lista(caso["consignas"])
            texto += "### Clave razonada para el docente\n\n" + _lista(caso["clave_docente"])
            texto += f"**Andamiaje:** {caso['andamiaje']}\n\n**Transferencia:** {caso['transferencia']}\n\n"
            texto += f"**Alcance y seguridad:** {caso['seguridad']}\n\n"
        texto += "## Recursos y seguridad\n\n" + e["seguridad"] + "\n\n"
        texto += (
            "La preparación documental no acredita manipulación, medición o experimentación. "
            "Verificar los recursos y observar el desempeño real cuando el objetivo lo exige.\n\n"
        )
    texto += "## Alcance de la revisión\n\n"
    texto += _lista(f"{v['rol']} · {v['veredicto']}: {v['comprobacion']}" for v in revision["lecturas"])
    enlaces = sorted(
        {
            r["localizador"].get("url")
            for v in revision["lecturas"]
            for r in v["respaldos"]
            if r.get("localizador", {}).get("url")
        }
    )
    if enlaces:
        texto += "### Fuentes citadas por los lectores\n\n" + _lista(f"[Fuente primaria]({u})" for u in enlaces)
    texto += (
        revision["limite"] + "\n\nNo hay respuestas ni logros observados de estudiantes. "
        "Los códigos de habilidades son locales; no son niveles PISA ni equivalencias entre países.\n\n"
        "## Procedencia\n\nEl JSON conserva el original, las actividades de la malla y la edición derivada, "
        "con sus huellas y lecturas exactas. Las instrucciones de esta guía corresponden a la edición derivada.\n"
    )
    return texto


def indice_grupo(registros):
    """Entrada legible al ZIP, con títulos, estados y rutas relativas comprobables."""
    primero = registros[0]
    texto = (
        f"# Preparaciones · {primero['asignatura']} · {primero['grados'][0]}.º\n\n"
        "Abre los enlaces de cada unidad y objetivo para leer su guía. Los JSON conservan la "
        "procedencia y las lecturas. Una preparación pendiente requiere resolver sus observaciones "
        "antes de considerarla respaldada. No son guiones cronometrados ni resultados de aula.\n\n"
    )
    unidades = sorted({r["unidad"] for r in registros})
    for u in unidades:
        texto += f"## {u}\n\n"
        for tipo in ("paquete_unidad", "paquete_objetivo"):
            for r in sorted(
                (r for r in registros if r["unidad"] == u and r["tipo"] == tipo), key=lambda r: r["titulo"]
            ):
                titulo = r["titulo"].replace("\n", " ").replace("[", "\\[").replace("]", "\\]")
                archivo = sha(r["id"].encode()) + ".md"
                estado = "cuatro lecturas favorables" if r["estado"] == "revision_automatica_completa" else "pendiente"
                texto += f"- [{titulo}]({tipo}/{archivo}) · {estado}\n"
        texto += "\n"
    return texto
