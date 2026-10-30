"""Repara sólo textos de tareas demasiado largos, con un parche explícito y nueva revisión."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Literal

from pydantic import Field, ValidationError

from goes_science_kg.clases.contratos import BorradorClases, GuionClase
from goes_science_kg.motor.contratos import Contrato

LIMITES = {"enunciado": 1100, "respuesta_esperada": 1400, "explicacion_solucion": 1200}


class CambioTarea(Contrato):
    fila_id: str
    tarea: int = Field(ge=0, le=2)
    campo: Literal["enunciado", "respuesta_esperada", "explicacion_solucion"]
    texto: str = Field(min_length=30, max_length=1400)


class EdicionesClases(Contrato):
    cambios: tuple[CambioTarea, ...] = Field(min_length=1, max_length=12)


def preparar_edicion(raw, ids, ids_anteriores):
    """Devuelve None ante cualquier defecto distinto de longitud en los tres campos permitidos."""
    if not raw or len(raw.encode()) > 120000:
        return None
    try:
        d = json.loads(raw)
        if set(d) != {"guiones"} or not isinstance(d["guiones"], list):
            return None
        guiones = d["guiones"]
        if len(guiones) != len(ids_anteriores) or {g["fila_id"] for g in guiones} != set(ids_anteriores):
            return None
        filas, cambios = [], 0
        for id_ in ids:
            original = next(g for g in guiones if g["fila_id"] == id_)
            try:
                GuionClase.model_validate(original)
                return None  # Una fila con veto científico no se envía a un editor de estilo.
            except ValidationError as e:
                errores = e.errors(include_input=False)
            campos, prueba = [], deepcopy(original)
            for error in errores:
                loc = error["loc"]
                if (
                    error["type"] == "string_too_long"
                    and len(loc) == 3
                    and loc[0] == "tareas"
                    and type(loc[1]) is int
                    and loc[2] in LIMITES
                ):
                    campos.append({"tarea": loc[1], "campo": loc[2], "maximo": LIMITES[loc[2]]})
                    # Sólo comprueba que no hay otros fallos; este marcador nunca es una salida publicable.
                    prueba["tareas"][loc[1]][loc[2]] = "Comprobación interna de la estructura del campo."
            if not campos:
                return None
            GuionClase.model_validate(prueba)
            filas.append({"fila_id": id_, "guion_original": original, "campos": campos})
            cambios += len(campos)
        if not 1 <= cambios <= 12:
            return None
        return {"antecedente_sha256": hashlib.sha256(raw.encode()).hexdigest(), "filas": filas}
    except (ValueError, TypeError, KeyError, StopIteration):
        return None


def aplicar_ediciones(solicitud, respuesta):
    respuesta = EdicionesClases.model_validate(respuesta)
    esperados = {(f["fila_id"], c["tarea"], c["campo"]): c["maximo"] for f in solicitud["filas"] for c in f["campos"]}
    recibidos = [(c.fila_id, c.tarea, c.campo) for c in respuesta.cambios]
    if len(recibidos) != len(set(recibidos)) or set(recibidos) != set(esperados):
        raise ValueError("La edición debe cambiar exactamente los campos solicitados, sin omisiones ni extras")
    guiones = {f["fila_id"]: deepcopy(f["guion_original"]) for f in solicitud["filas"]}
    for c in respuesta.cambios:
        if len(c.texto) > esperados[(c.fila_id, c.tarea, c.campo)]:
            raise ValueError("El campo editado sigue excediendo su presupuesto de caracteres")
        guiones[c.fila_id]["tareas"][c.tarea][c.campo] = c.texto
    return BorradorClases.model_validate({"guiones": list(guiones.values())})
