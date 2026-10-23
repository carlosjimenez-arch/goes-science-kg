"""Contexto P10: conserva alcance y fuentes, separa el historial editorial."""

from __future__ import annotations

from copy import deepcopy

from goes_science_kg.clases.preparacion import contexto as contexto_historico

CAMPOS_FILA = (
    "fila_id", "grado", "asignatura", "unidad", "propuesta", "fuentes_cientificas_ids",
    "datos_contextuales", "enmienda_didactica_auditoria",
)
CAMPOS_PROPUESTA = (
    "objetivo_propuesto", "indicador_observable", "criterio_evaluacion", "producto_evaluable",
    "orientacion_didactica", "andamiaje", "contexto_salvador", "disciplinas_propuestas",
    "recursos_condicionales", "seguridad",
)


def contexto(preparacion, *, ids=None):
    """Sin recortar pasajes ni objetivos; los originales siguen en la preparación inmutable."""
    datos = contexto_historico(preparacion, ids=ids)
    filas = []
    for original in datos["filas"]:
        fila = {k: original[k] for k in CAMPOS_FILA if k in original}
        fila["propuesta"] = {k: original["propuesta"][k] for k in CAMPOS_PROPUESTA if k in original["propuesta"]}
        filas.append(fila)
    return deepcopy(datos | {"filas": filas})
