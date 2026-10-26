"""Casos curados para una captura exacta, sin reutilización por semejanza léxica."""

from __future__ import annotations

from copy import deepcopy

from goes_science_kg.config import cargar


def caso_para(fila, huella_curriculo, *, banco=None):
    banco = cargar("casos_didacticos_ciencias") if banco is None else banco
    if huella_curriculo != banco["huella_curriculo"]:
        return None
    clave = (fila.grado, fila.asignatura_malla, fila.hoja, fila.fila)
    encontrados = []
    for original in banco["casos"]:
        d = original["destino"]
        if (d["grado"], d["asignatura"], d["hoja"], d["fila"]) == clave:
            encontrados.append(original)
    if len(encontrados) > 1:
        raise ValueError("Dos casos curados compiten por la misma fila")
    if not encontrados:
        return None
    caso = deepcopy(encontrados[0])
    caso.update(
        fila_id=fila.id,
        huella_curriculo=huella_curriculo,
        modalidad="preparacion_y_analisis_documental",
        desempeno_practico="no_acreditado_por_el_caso_resuelto",
        estado_revision="curacion_editorial_pendiente_revision_independiente",
    )
    return caso
