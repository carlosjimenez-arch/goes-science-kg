"""Build bounded transport schemas while preserving full local validation."""

# Historical implementation notes:
# Vertex documenta rechazos 400 por esquemas con demasiadas restricciones. La gramática enviada
# conserva estructura, tipos, campos requeridos y enums; longitudes y cardinalidades se verifican
# localmente por el mismo modelo Pydantic antes de aceptar o cachear cualquier respuesta.

from __future__ import annotations

from copy import deepcopy
from functools import cache

from pydantic import BaseModel

LIMITES_LOCALES = frozenset(
    {"minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum", "pattern", "title"}
)


def simplificar_transporte(schema: dict) -> dict:
    """Reduce transport schema complexity while retaining local validation requirements."""

    def limpiar(x):
        if isinstance(x, dict):
            return {
                k: (
                    {nombre: limpiar(campo) for nombre, campo in v.items()}
                    if k in {"properties", "$defs", "definitions"}
                    else limpiar(v)
                )
                for k, v in x.items()
                if k not in LIMITES_LOCALES
            }
        return [limpiar(v) for v in x] if isinstance(x, list) else x

    return limpiar(deepcopy(schema))


@cache
def contrato_transporte(base: type[BaseModel]) -> type[BaseModel]:
    """Build the provider-facing contract for an explicitly selected local schema."""

    class Transporte(base):
        @classmethod
        def model_json_schema(cls, *args, **kwargs):
            """Expose the bounded JSON transport schema used by the provider adapter."""

            return simplificar_transporte(super().model_json_schema(*args, **kwargs))

    Transporte.__name__ = base.__name__ + "TransporteV1"
    return Transporte
