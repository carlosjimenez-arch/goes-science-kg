"""Validate references, quotations, versions, resources, and exact-output reviews."""

from __future__ import annotations

import re
from collections.abc import Sequence

from goes_science_kg.motor.contratos import Dictamen, Evidencia, Propuesta, Solicitud, huella
from goes_science_kg.motor.recursos import canonico

CRITERIOS = {
    "cientifico": {"correccion_cientifica", "respaldo_de_afirmaciones", "alineacion_curricular"},
    "psicopedagogo": {"adecuacion_al_grado", "carga_cognitiva", "evaluacion_del_objetivo", "accesibilidad"},
    "adversarial": {"sin_contradicciones", "citas_implican_afirmaciones", "seguridad_y_factibilidad"},
}


def normalizar(texto: str) -> str:
    """Normalize whitespace for deterministic evidence comparisons."""

    return re.sub(r"\s+", " ", texto).strip().casefold()


def validar_propuesta(propuesta: Propuesta, solicitud: Solicitud, evidencias: Sequence[Evidencia]) -> list[str]:
    """Validate proposal claims, citations, curriculum version, and declared resources."""

    por_id = {e.id: e for e in evidencias}
    errores = []
    grupos = [(f"Afirmación {n}", a.citas) for n, a in enumerate(propuesta.afirmaciones, start=1)]
    grupos.append(("Anclaje curricular", propuesta.anclaje_curricular))
    for nombre, citas in grupos:
        for cita in citas:
            evidencia = por_id.get(cita.evidencia_id)
            if evidencia is None:
                errores.append(f"{nombre}: evidencia desconocida {cita.evidencia_id}")
            elif normalizar(cita.literal) not in normalizar(evidencia.texto):
                errores.append(f"{nombre}: cita no localizada en {evidencia.id}")
            elif not evidencia.fuente.get("documento"):
                errores.append(f"{nombre}: evidencia sin documento de procedencia")
            elif evidencia.fuente.get("tipo") == "derivada" or evidencia.fuente.get("fuente_primaria") is False:
                errores.append(f"{nombre}: fuente derivada, se requiere evidencia primaria")
            elif evidencia.fuente.get("verificacion") != "contenido_fuente":
                errores.append(f"{nombre}: falta verificación del contenido contra el archivo original")
            elif evidencia.version not in (solicitud.version_curriculo, "referencia"):
                errores.append(f"{nombre}: versión de evidencia incompatible {evidencia.version}")
            elif nombre == "Anclaje curricular" and evidencia.version != solicitud.version_curriculo:
                errores.append("El objetivo requiere un anclaje en el currículo local vigente")
            elif (
                nombre == "Anclaje curricular"
                and solicitud.fila_id is not None
                and (evidencia.id.partition("#CELDA:")[0] != solicitud.fila_id)
            ):
                errores.append("El anclaje no corresponde a la fila objetivo exacta de la solicitud")
    if propuesta.actividad.minutos > solicitud.minutos:
        errores.append("La actividad supera el tiempo disponible")
    faltan = set(map(canonico, propuesta.actividad.recursos)) - set(map(canonico, solicitud.recursos))
    if faltan:
        errores.append(f"Recursos no disponibles: {', '.join(sorted(faltan))}")
    return errores


def validar_dictamenes(
    propuesta: Propuesta, dictamenes: Sequence[Dictamen], evidencias: Sequence[Evidencia]
) -> list[str]:
    """Require all mandatory roles to review the exact proposal under complete criteria."""

    errores = []
    por_rol = {d.rol: d for d in dictamenes}
    ids = {e.id for e in evidencias}
    citados = {c.evidencia_id for a in propuesta.afirmaciones for c in a.citas}
    citados.update(c.evidencia_id for c in propuesta.anclaje_curricular)
    if len(por_rol) != len(dictamenes):
        errores.append("Hay roles de revisión duplicados")
    for rol, criterios in CRITERIOS.items():
        d = por_rol.get(rol)
        if d is None:
            errores.append(f"Falta revisión {rol}")
            continue
        if d.huella_propuesta != huella(propuesta):
            errores.append(f"{rol}: dictamen de otra propuesta")
        r = d.revision
        if not r.aprobado or r.errores:
            errores.extend(f"{rol}: {e}" for e in r.errores or ["no aprobada"])
        if not criterios.issubset(r.criterios) or not all(r.criterios.get(c, False) for c in criterios):
            errores.append(f"{rol}: no satisface todos los criterios obligatorios")
        if not r.evidencia_ids or not set(r.evidencia_ids).issubset(ids):
            errores.append(f"{rol}: evidencias inexistentes o sin evidencia evaluada")
        elif not citados.issubset(r.evidencia_ids):
            errores.append(f"{rol}: no revisó todas las evidencias citadas")
    return errores
