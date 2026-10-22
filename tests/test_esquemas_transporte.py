"""La simplificación de gramática nunca relaja la validación que acepta respuestas."""

import pytest
from pydantic import Field, ValidationError

from goes_science_kg.motor.contratos import Contrato
from goes_science_kg.motor.esquemas import contrato_transporte


class Muestra(Contrato):
    title: str = Field(min_length=5, max_length=10)
    filas: tuple[str, ...] = Field(min_length=1, max_length=3)


def test_campos_requeridos_sobreviven_y_limites_se_exigen_localmente():
    schema = contrato_transporte(Muestra)
    enviado = schema.model_json_schema()
    assert set(enviado["properties"]) == {"title", "filas"}
    assert set(enviado["required"]) == {"title", "filas"}
    assert "maxLength" not in enviado["properties"]["title"]
    assert "maxItems" not in enviado["properties"]["filas"]
    for datos in (
        {"title": "a", "filas": ["x"]},
        {"title": "válido", "filas": []},
        {"title": "válido", "filas": ["x"], "otro": True},
    ):
        with pytest.raises(ValidationError):
            schema.model_validate(datos)
    assert schema.model_validate({"title": "válido", "filas": ["x"]}).title == "válido"
