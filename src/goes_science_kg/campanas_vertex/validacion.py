"""Bind generated components to pinned curriculum, allowed citations, antecedents, and arithmetic."""

from __future__ import annotations

import re

from pydantic import BaseModel

from goes_science_kg.campanas_vertex.contratos import completar_recorrido, validar_alcance_unidad
from goes_science_kg.clases.complementaria import errores_calculos, validar_anexo, validar_evaluacion
from goes_science_kg.clases.contratos import GuionClase


def validar_contexto(tipo: str, contexto: dict) -> set[str]:
    """Require explicit citable evidence and the curricular denominator before a paid call."""
    fuentes = contexto.get("fuentes_citables")
    if not isinstance(fuentes, list) or not fuentes:
        raise ValueError("El contexto debe fijar fuentes_citables pertinentes; los antecedentes no las sustituyen")
    ids = [f.get("id") if isinstance(f, dict) else None for f in fuentes]
    if any(not isinstance(i, str) or not i for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("Las fuentes citables requieren identificadores únicos y no vacíos")
    if tipo in {"guion_sucesor", "recorrido_cerrado", "anexo_implementacion"}:
        if not isinstance(contexto.get("fila_id"), str) or not contexto["fila_id"]:
            raise ValueError("El contexto requiere la identidad curricular literal")
    if tipo in {"guion_sucesor", "recorrido_cerrado"}:
        if not isinstance(contexto.get("objetivo_literal"), str) or not contexto["objetivo_literal"].strip():
            raise ValueError("El contexto requiere el objetivo literal completo")
        if type(contexto.get("grado")) is not int or not 2 <= contexto["grado"] <= 11:
            raise ValueError("El contexto requiere un grado curricular de 2.º a 11.º")
    if tipo in {"guia_sintesis_unidad", "evaluacion_unidad"}:
        objetivos = contexto.get("objetivos_unidad")
        if (
            not isinstance(contexto.get("unidad_id"), str)
            or not contexto["unidad_id"]
            or not isinstance(objetivos, list)
            or not objetivos
            or any(not isinstance(o, str) or not o for o in objetivos)
            or len(objetivos) != len(set(objetivos))
        ):
            raise ValueError("El contexto requiere la unidad y su denominador completo de objetivos únicos")
    if tipo == "anexo_implementacion":
        if not re.fullmatch(r"[0-9a-f]{64}", str(contexto.get("guion_sha256", ""))):
            raise ValueError("El anexo requiere el SHA del guion revisado exacto")
        GuionClase.model_validate(contexto.get("guion_revisado"))
        if not isinstance(contexto.get("candidatos_progresion"), dict):
            raise ValueError("El anexo requiere los candidatos de progresión registrados")
    if tipo == "recorrido_cerrado" and not isinstance(contexto.get("origen_fijado"), dict):
        raise ValueError("El recorrido requiere una procedencia local fijada fuera de la autoría Vertex")
    return set(ids)


def validar_contenido(tipo: str, contenido: BaseModel, contexto: dict) -> None:
    """Reject wrong objective identities, unoffered citations, and recomputed arithmetic errors."""
    citables = validar_contexto(tipo, contexto)
    errores = []
    if tipo == "guion_sucesor":
        if contenido.fila_id != contexto["fila_id"] or contenido.objetivo != contexto["objetivo_literal"]:
            errores.append("El guion cambió la identidad o el objetivo literal del contexto")
        if any(set(a.fuentes_ids) - citables for a in contenido.explicacion_docente):
            errores.append("El guion cita una fuente ajena a las fuentes citables pertinentes del contexto")
        for tarea in contenido.tareas:
            errores.extend(errores_calculos(tarea.calculos))
    elif tipo == "guia_sintesis_unidad":
        validar_alcance_unidad(contenido, contexto["objetivos_unidad"])
        if contenido.unidad_id != contexto["unidad_id"]:
            errores.append("La guía cambió la unidad curricular")
        if set(contenido.fuentes_ids) - citables:
            errores.append("La guía cita fuentes ajenas al contexto pertinente")
    elif tipo == "evaluacion_unidad":
        errores.extend(validar_evaluacion(contenido, contexto["unidad_id"], set(contexto["objetivos_unidad"])))
    elif tipo == "anexo_implementacion":
        guion = GuionClase.model_validate(contexto["guion_revisado"])
        if guion.fila_id != contexto["fila_id"]:
            errores.append("El guion antecedente corresponde a otra fila curricular")
        candidatos = {
            nombre: {tuple(par) for par in contexto["candidatos_progresion"].get(nombre, [])}
            for nombre in ("previas", "continuidad")
        } | {"fuentes": citables}
        errores.extend(validar_anexo(contenido, guion, contexto["guion_sha256"], candidatos))
    elif tipo == "recorrido_cerrado":
        if contenido.grado != contexto["grado"] or contenido.objetivos != [contexto["objetivo_literal"]]:
            errores.append("El recorrido cambió el grado o el objetivo literal")
        completar_recorrido(contenido, origen=contexto["origen_fijado"], fuentes=contexto["fuentes_citables"])
    else:
        errores.append("Tipo de componente no reconocido")
    if errores:
        raise ValueError("; ".join(errores))
