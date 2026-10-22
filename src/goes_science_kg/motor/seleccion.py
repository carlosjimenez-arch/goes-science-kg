"""Contratos de selección ligados al contexto: el modelo no inventa localizadores."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, Field, create_model

from goes_science_kg.motor.contratos import Contrato


def _campo_id(ids: Sequence[str]):
    opciones = tuple(dict.fromkeys(ids))
    if not opciones:
        raise ValueError("Un grupo obligatorio carece de fragmentos seleccionables")
    # Literal conserva los IDs completos y se exporta como enum en el esquema JSON de Vertex.
    tipo_id = Literal.__getitem__(opciones)
    return tipo_id, Field(description="Un fragmento del grupo; la evidencia insuficiente exige abstención")


def esquema_por_grupos(base: type[BaseModel], fragmentos, grupos: Mapping[str, Sequence[str]]) -> type[BaseModel]:
    """Exige selección explícita en cada grupo; no completa citas por cuenta del modelo."""
    if "fragmentos_ids" not in base.model_fields or not grupos:
        raise ValueError("Se requiere el contrato de lectura y sus grupos de evidencia")
    seleccion = create_model(
        base.__name__ + "Grupos",
        __base__=Contrato,
        **{nombre: _campo_id([f.id for f in fragmentos if f.evidencia_id in ids]) for nombre, ids in grupos.items()},
    )
    campos = {
        nombre: (campo.annotation, deepcopy(campo))
        for nombre, campo in base.model_fields.items()
        if nombre != "fragmentos_ids"
    }
    return create_model(
        base.__name__ + "Contextual",
        __base__=Contrato,
        fragmentos_por_grupo=(seleccion, ...),
        **campos,
    )


def ids_seleccionados(lectura: BaseModel) -> tuple[str, ...]:
    """Un fragmento puede satisfacer varios grupos; se cita una sola vez después de seleccionarlo."""
    return tuple(dict.fromkeys(lectura.fragmentos_por_grupo.model_dump().values()))
