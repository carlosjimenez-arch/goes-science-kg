"""Constrain proposal generation to registered quotation identifiers."""

from typing import Literal

from pydantic import Field, create_model

from goes_science_kg.producto.mejoras_contratos import BorradorMejora, MejoraFila


def esquema_redaccion(preparacion):
    """Constrain proposal transport to the preparation's registered fragments and rows."""

    ids = Literal.__getitem__(tuple(f.id for f in preparacion.fragmentos))
    fila = create_model(
        "MejoraFilaContextual", __base__=MejoraFila, fragmentos_ids=(tuple[ids, ...], Field(min_length=2, max_length=6))
    )
    return create_model(
        "BorradorMejoraContextual",
        __base__=BorradorMejora,
        filas=(tuple[fila, ...], Field(min_length=1, max_length=30)),
    )
