"""Texto de una fase en varias columnas, conservando los anclajes físicos de Excel."""

from __future__ import annotations

from collections.abc import Sequence

from goes_science_kg.curriculo.contratos import CeldaCurricular


def texto_fase(celdas: Sequence[CeldaCurricular]) -> str:
    vistos, partes = set(), []
    for celda in celdas:
        origen = celda.origen_combinado or celda.coordenada
        if origen in vistos:
            continue
        vistos.add(origen)
        texto = "" if celda.valor is None else str(celda.valor).strip()
        if texto:
            partes.append(texto)
    return "\n".join(partes)
