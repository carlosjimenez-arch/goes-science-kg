"""Reconstrucción determinista de juicios; no ejecuta modelos ni rehidrata las fuentes.

El llamador verifica previamente el expediente y su vínculo con la solicitud contra los originales.
Estos helpers aplican las mismas rúbricas, citas y reglas de cierre utilizadas por el Motor.
"""

from __future__ import annotations

from collections.abc import Mapping

from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto._juicios_contratos import (
    ESQUEMAS_CONOCIMIENTO,
    ROLES_CONOCIMIENTO,
    DictamenConocimiento,
    ExpedienteConocimiento,
    RelacionRespaldada,
    ResultadoConocimiento,
    SolicitudConocimiento,
)


def validar_citas(dictamen: DictamenConocimiento, expediente: ExpedienteConocimiento) -> None:
    registro = {(f.evidencia_id, f.literal) for f in expediente.fragmentos}
    if len({(c.evidencia_id, c.literal) for c in dictamen.citas}) != len(dictamen.citas) or any(
        (c.evidencia_id, c.literal) not in registro for c in dictamen.citas
    ):
        raise ValueError("Citas duplicadas o ajenas al registro de fragmentos")
    seleccionadas = {c.evidencia_id for c in dictamen.citas}
    if any(not seleccionadas.intersection(ids) for ids in expediente.grupos.values()):
        raise ValueError("El dictamen omite un grupo de evidencia obligatorio")


def validar_dictamen(
    datos: dict | DictamenConocimiento | None,
    rol: str,
    expediente: ExpedienteConocimiento,
    modelos: Mapping[str, str] | None,
) -> DictamenConocimiento:
    """Exige identidad, modelo, rúbrica exacta y citas únicas que cubran todos los grupos."""
    dictamen = DictamenConocimiento.model_validate(datos)
    esperados = set(ESQUEMAS_CONOCIMIENTO[rol].model_fields["criterios"].annotation.model_fields)
    if (
        dictamen.rol != rol
        or dictamen.huella_tarea != huella(expediente)
        or set(dictamen.criterios) != esperados
        or modelos is None
        or dictamen.modelo != modelos[rol]
    ):
        raise ValueError("Identidad, modelo o criterios incompatibles con la tarea")
    validar_citas(dictamen, expediente)
    return dictamen


def resolver_resultado(
    *,
    expediente: ExpedienteConocimiento,
    solicitud: SolicitudConocimiento,
    ejecucion_id: str,
    huella_motor: str,
    modelos: Mapping[str, str] | None,
    salidas: Mapping[str, dict],
) -> ResultadoConocimiento:
    """Reconstruye respaldo, veto o abstención sin confiar en un terminal persistido.

    Cada salida conserva el contrato ``{dictamen: datos|None, error: str|None}`` del workflow.
    Un expediente no preparado conserva sus motivos y no admite dictámenes ni relación.
    """
    motivos = list(expediente.motivos)
    dictamenes = []
    for rol in ROLES_CONOCIMIENTO:
        salida = salidas.get(rol, {})
        if expediente.estado != "preparado":
            continue
        try:
            dictamenes.append(validar_dictamen(salida.get("dictamen"), rol, expediente, modelos))
        except (ValueError, KeyError) as error:
            motivos.append(f"{rol}: dictamen no verificable ({type(error).__name__})")
    decision, relacion = "abstencion", None
    if not motivos and len(dictamenes) == len(ROLES_CONOCIMIENTO):
        valores = {v for d in dictamenes for v in d.criterios.values()}
        if valores == {"si"}:
            decision = "respaldado"
            datos = dict(
                tipo=expediente.tipo_relacion,
                origen=expediente.origen,
                destino=expediente.destino,
                fila_id=expediente.fila_id,
                grado_sv=expediente.grado,
                huella_curriculo=expediente.huella_curriculo,
                huella_tarea=huella(expediente),
            )
            relacion = RelacionRespaldada(id="RELACION_V4:" + huella(datos), **datos)
        elif "no" in valores:
            decision = "no_respaldado"
            motivos.append("Existe al menos un veto explícito; no se promedian criterios ni lectores")
        else:
            motivos.append("La evidencia no permite resolver todos los criterios")
    return ResultadoConocimiento(
        estado=decision,
        solicitud=solicitud,
        ejecucion_id=ejecucion_id,
        huella_tarea=huella(expediente),
        huella_motor=huella_motor,
        dictamenes=tuple(dictamenes),
        relacion=relacion,
        motivos=tuple(motivos),
    )
