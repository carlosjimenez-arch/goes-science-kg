"""Validate complete learning materials separately from observed learning evidence."""

from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from goes_science_kg.clases.validacion import calcular


class _Contrato(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ItemRecorrido(_Contrato):
    """Keep a pupil-facing task free of its answer key."""

    id: str = Field(min_length=1)
    enunciado: str = Field(min_length=20)


class RubricaRecorrido(_Contrato):
    """Retain observable performance descriptions at all three rubric levels."""

    criterio: str = Field(min_length=5)
    logrado: str = Field(min_length=10)
    en_proceso: str = Field(min_length=10)
    requiere_apoyo: str = Field(min_length=10)


class SolucionRecorrido(_Contrato):
    """Store the complete answer and arithmetic evidence exclusively for teachers."""

    respuesta: str = Field(min_length=10)
    explicacion: str = Field(min_length=10)
    rubrica: list[RubricaRecorrido] = Field(min_length=1)
    calculos: list[dict[str, Any]] = Field(default_factory=list)


class DiagnosticoRecorrido(_Contrato):
    """Specify evidence collection and the rule for selecting reinforcement."""

    items: list[ItemRecorrido] = Field(min_length=1)
    criterio_derivacion: str = Field(min_length=20)


class EjemploRecorrido(_Contrato):
    """Provide a fully worked example before partially supported practice."""

    id: str = Field(min_length=1)
    enunciado: str = Field(min_length=20)
    pasos: list[str] = Field(min_length=2)


class PracticaRecorrido(_Contrato):
    """Keep task data together with the specific support pupils may use."""

    items: list[ItemRecorrido] = Field(min_length=1)
    apoyos: list[str] = Field(min_length=1)


class RefuerzoRecorrido(_Contrato):
    """Fade worked support before a held-out assessment."""

    ejemplo_trabajado: EjemploRecorrido
    practica_guiada: PracticaRecorrido
    retirada_apoyos: str = Field(min_length=20)


class ComprobacionRecorrido(_Contrato):
    """Declare a fresh task and administration without instructional assistance."""

    items: list[ItemRecorrido] = Field(min_length=1)
    sin_ayudas: Literal[True] = Field(description="Sin ayuda conceptual; las adaptaciones de acceso se conservan.")
    administracion: str = Field(min_length=20)
    criterios: list[str] = Field(min_length=1)
    si_no_logra: str = Field(min_length=20)


class CargaRecorrido(_Contrato):
    """Describe design decisions without presenting them as a measured construct."""

    decisiones: list[str] = Field(min_length=1)
    no_medida: Literal[True]


class RecorridoFinal(_Contrato):
    """Require executable materials for each stage while preserving provenance."""

    version: str = "recorrido-ciencias-2"
    id: str = Field(min_length=1)
    titulo: str = Field(min_length=8)
    grado: int = Field(ge=2, le=11)
    origen: dict[str, Any]
    objetivos: list[str] = Field(min_length=1)
    fundamento: list[str] = Field(min_length=1)
    fuentes: list[dict[str, Any]] = Field(min_length=1)
    diagnostico: DiagnosticoRecorrido
    refuerzo: RefuerzoRecorrido
    comprobacion_independiente: ComprobacionRecorrido
    soluciones_docente: dict[str, SolucionRecorrido]
    carga_cognitiva: CargaRecorrido
    implementacion_docente: list[str] = Field(default_factory=list)


def _normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", texto))


def _items(recorrido: RecorridoFinal) -> list[ItemRecorrido]:
    return [
        *recorrido.diagnostico.items,
        *recorrido.refuerzo.practica_guiada.items,
        *recorrido.comprobacion_independiente.items,
    ]


def validar_recorrido(recorrido: dict) -> list[str]:
    """Check material coverage, held-out tasks, rubric preservation, and declared arithmetic."""
    try:
        r = RecorridoFinal.model_validate(recorrido)
    except ValidationError as error:
        return [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()]
    errores = []
    items = _items(r)
    ids = [i.id for i in items] + [r.refuerzo.ejemplo_trabajado.id]
    if len(ids) != len(set(ids)):
        errores.append("Los ítems y el ejemplo trabajado requieren identidades distintas")
    esperadas = {i.id for i in items}
    if set(r.soluciones_docente) != esperadas:
        errores.append("El solucionario debe cubrir exactamente diagnóstico, práctica y comprobación")
    enunciados = [_normalizar(i.enunciado) for i in items]
    enunciados += [_normalizar(r.refuerzo.ejemplo_trabajado.enunciado)]
    if len(enunciados) != len(set(enunciados)):
        errores.append("La comprobación no puede reutilizar un enunciado de diagnóstico, ejemplo o práctica")
    for fuente in r.fuentes:
        if not all(isinstance(fuente.get(k), str) and fuente[k].strip() for k in ("id", "titulo", "url", "alcance")):
            errores.append("Cada fuente requiere id, título, URL y alcance explícitos")
        url = urlparse(str(fuente.get("url", "")))
        if url.scheme not in {"https", "http"} or not url.netloc:
            errores.append("Cada URL de fuente debe ser HTTP(S) absoluta")
    for item_id, solucion in r.soluciones_docente.items():
        criterios = [c.criterio for c in solucion.rubrica]
        if len(criterios) != len(set(criterios)):
            errores.append(f"{item_id}: criterios de rúbrica repetidos")
        for calculo in solucion.calculos:
            try:
                esperado = calculo["resultado"]
                if type(esperado) not in (int, float) or not math.isfinite(esperado):
                    raise ValueError("Resultado no finito")
                obtenido = calcular(calculo["expresion"])
                if not math.isclose(obtenido, esperado, rel_tol=1e-6, abs_tol=abs(esperado) * 1e-6):
                    errores.append(f"{item_id}: {calculo['expresion']} no produce {esperado}")
            except (KeyError, TypeError, ValueError, SyntaxError, ZeroDivisionError, OverflowError):
                errores.append(f"{item_id}: comprobación aritmética inválida")
    return errores


def resumen_mediciones(recorrido: dict, evidencias: list[dict] | None = None) -> dict:
    """Separate technical completeness, simulation, real responses, and unmeasured outcomes."""
    from goes_science_kg.aprendizaje.carga_cognitiva import resumen_esfuerzo

    fallos = validar_recorrido(recorrido)
    registros = evidencias or []
    if not isinstance(registros, list) or not all(isinstance(e, dict) for e in registros):
        raise ValueError("Las evidencias requieren una lista de registros explícitos")
    reales = [e for e in registros if e.get("origen") == "estudiante"]
    simulados = [e for e in registros if e.get("origen") == "simulacion"]
    estado = "material_invalidado" if fallos else "sin_evidencia_real"
    razones = []
    if not fallos and reales:
        r = RecorridoFinal.model_validate(recorrido)
        pares = [(e.get("estudiante_id"), e.get("sesion_id")) for e in reales]
        identidad_valida = all(isinstance(x, str) and x.strip() for par in pares for x in par)
        if not identidad_valida or len(set(pares)) != 1:
            razones.append("Las respuestas deben pertenecer a la misma persona seudonimizada y sesión")
        ordenes = [e.get("orden") for e in reales]
        if any(type(n) is not int or n < 1 for n in ordenes) or len(set(ordenes)) != len(ordenes):
            razones.append("El registro requiere orden temporal explícito, positivo y sin duplicados")
        else:
            niveles = {"diagnostico": 0, "practica_guiada": 1, "comprobacion_independiente": 2}
            fases_ordenadas = [niveles.get(e.get("fase"), -1) for e in sorted(reales, key=lambda e: e["orden"])]
            if fases_ordenadas != sorted(fases_ordenadas) or -1 in fases_ordenadas:
                razones.append("El orden observado debe ser diagnóstico → práctica → comprobación independiente")
        fases = {
            "diagnostico": r.diagnostico.items,
            "practica_guiada": r.refuerzo.practica_guiada.items,
            "comprobacion_independiente": r.comprobacion_independiente.items,
        }
        for fase, items in fases.items():
            for item in items:
                observaciones = [e for e in reales if e.get("fase") == fase and e.get("item_id") == item.id]
                if (
                    len(observaciones) != 1
                    or not isinstance(observaciones[0].get("respuesta"), str)
                    or not observaciones[0]["respuesta"].strip()
                ):
                    razones.append(f"{item.id}: falta una respuesta real única de {fase}")
                    continue
                if fase != "comprobacion_independiente":
                    continue
                ev = observaciones[0]
                esperados = {c.criterio for c in r.soluciones_docente[item.id].rubrica}
                criterios = ev.get("criterios")
                citas = ev.get("citas_criterios")
                if (
                    ev.get("sin_ayudas") is not True
                    or ev.get("contexto_calificacion") != "enunciado_rubrica_respuesta"
                    or not isinstance(criterios, dict)
                    or set(criterios) != esperados
                    or any(v != "logrado" for v in criterios.values())
                    or not isinstance(citas, dict)
                    or set(citas) != esperados
                    or any(
                        not isinstance(cita, str)
                        or not _normalizar(cita)
                        or _normalizar(cita) not in _normalizar(ev["respuesta"])
                        for cita in citas.values()
                    )
                    or not str(ev.get("responsable_calificacion", "")).strip()
                ):
                    razones.append(f"{item.id}: comprobación nueva sin ayuda o criterios no acreditados")
        estado = "requiere_seguimiento" if razones else "ciclo_observado_completo"
    return {
        "materiales": "completos" if not fallos else "incompletos",
        "errores_materiales": fallos,
        "evidencias_reales": len(reales),
        "evidencias_simuladas": len(simulados),
        "estado_aprendizaje": estado,
        "razones": razones,
        "eficacia_validada": False,
        "carga_cognitiva": resumen_esfuerzo(),
        "limite": (
            "La completitud del material y una respuesta correcta no miden carga cognitiva ni eficacia. "
            "Las respuestas simuladas sólo verifican software. Un cierre observado según el registro no acredita "
            "retención futura ni prueba por sí solo el origen humano declarado de los datos."
        ),
    }


def _actividad(items: list[ItemRecorrido]) -> list[str]:
    return [linea for i in items for linea in (f"### {i.id}", "", i.enunciado, "")]


def materializar_recorrido(recorrido: dict, destino: Path) -> dict:
    """Write separate complete teacher, guided pupil, and held-out pupil materials without overwriting."""
    errores = validar_recorrido(recorrido)
    if errores:
        raise ValueError("; ".join(errores))
    r = RecorridoFinal.model_validate(recorrido)
    if destino.is_symlink() or any(p.is_symlink() for p in destino.parents):
        raise ValueError("El destino requiere una carpeta propia sin enlaces simbólicos")
    cabecera = [f"# {r.titulo}", "", f"Grado {r.grado}.º · {r.id}", "", "## Objetivos", ""]
    cabecera += [f"- {x}" for x in r.objetivos] + [""]
    ejemplo = r.refuerzo.ejemplo_trabajado
    diagnostico = cabecera + ["## Diagnóstico: entregar y recoger antes del refuerzo", ""]
    diagnostico += _actividad(r.diagnostico.items)
    estudiante = cabecera + ["## Refuerzo: entregar después de recoger el diagnóstico", ""]
    estudiante += [*r.fundamento, "", "### Ejemplo trabajado", "", ejemplo.enunciado, ""]
    estudiante += [f"{n}. {paso}" for n, paso in enumerate(ejemplo.pasos, 1)]
    estudiante += ["", "## Práctica guiada", "", *r.refuerzo.practica_guiada.apoyos, ""]
    estudiante += _actividad(r.refuerzo.practica_guiada.items)
    estudiante += ["## Retirada de apoyos", "", r.refuerzo.retirada_apoyos, ""]
    comprobacion = cabecera + ["## Comprobación independiente", "", r.comprobacion_independiente.administracion, ""]
    comprobacion += [
        "Se conservan los apoyos de acceso: lectura literal o formato accesible sin pistas conceptuales.",
        "",
    ]
    comprobacion += _actividad(r.comprobacion_independiente.items)
    docente = diagnostico + ["## Derivación y decisiones del docente", "", r.diagnostico.criterio_derivacion, ""]
    docente += estudiante
    docente += ["## Comprobación independiente: hoja reservada hasta terminar el refuerzo", ""]
    docente += _actividad(r.comprobacion_independiente.items)
    docente += [r.comprobacion_independiente.administracion, "", "### Criterio de cierre", ""]
    docente += [f"- {x}" for x in r.comprobacion_independiente.criterios]
    docente += ["", "Si no se logra: " + r.comprobacion_independiente.si_no_logra, "", "## Soluciones y rúbricas", ""]
    for item in _items(r):
        solucion = r.soluciones_docente[item.id]
        docente += [f"### {item.id}", "", solucion.respuesta, "", solucion.explicacion, ""]
        for criterio in solucion.rubrica:
            docente += [
                "Criterio: " + criterio.criterio,
                "- Logrado: " + criterio.logrado,
                "- En proceso: " + criterio.en_proceso,
                "- Requiere apoyo: " + criterio.requiere_apoyo,
                "",
            ]
        for calculo in solucion.calculos:
            docente += [
                f"Comprobación: `{calculo['expresion']}` = {calculo['resultado']} {calculo.get('unidad', '')}",
                "",
            ]
    docente += ["## Diseño de carga cognitiva", "", *r.carga_cognitiva.decisiones, ""]
    docente += [
        "Carga cognitiva y eficacia: no medidas; las decisiones de diseño requieren contraste con estudiantes.",
        "",
    ]
    if r.implementacion_docente:
        docente += ["## Implementación docente", "", *r.implementacion_docente, ""]
    docente += ["## Fuentes y alcance", ""]
    for fuente in r.fuentes:
        docente += [f"- [{fuente['titulo']}]({fuente['url']}): {fuente['alcance']}"]
    serializar = lambda x: (json.dumps(x, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()  # noqa: E731
    archivos = {
        "docente.md": ("\n".join(docente) + "\n").encode(),
        "diagnostico_estudiante.md": ("\n".join(diagnostico) + "\n").encode(),
        "estudiante.md": ("\n".join(estudiante) + "\n").encode(),
        "comprobacion_estudiante.md": ("\n".join(comprobacion) + "\n").encode(),
        "recorrido.json": serializar(recorrido),
        "mediciones.json": serializar(resumen_mediciones(recorrido)),
    }
    manifest = {
        "version": "materiales-recorrido-2",
        "recorrido": r.id,
        "aprobacion_institucional": False,
        "eficacia_validada": False,
        "archivos": {n: {"sha256": hashlib.sha256(b).hexdigest(), "bytes": len(b)} for n, b in archivos.items()},
    }
    destino.mkdir(parents=True, exist_ok=False)
    for nombre, raw in archivos.items():
        with (destino / nombre).open("xb") as stream:
            stream.write(raw)
    with (destino / "manifest.json").open("xb") as stream:
        stream.write(serializar(manifest))
    return manifest
