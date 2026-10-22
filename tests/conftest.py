import logging
from functools import cached_property

import pytest

from goes_science_kg.grafo.construir import construir


@pytest.fixture(scope="session")
def grafo():
    return construir()


@pytest.fixture(autouse=True)
def proveedores_sin_red_y_logging_aislado(monkeypatch):
    """Require injected offline providers and restore isolated logging handlers after each test."""
    from goes_science_kg.motor.vertex import Vertex

    def prohibido(self):
        pytest.fail("El test intentó crear un cliente real de Vertex; inyecte un proveedor sin red")

    cliente = cached_property(prohibido)
    cliente.__set_name__(Vertex, "cliente")
    monkeypatch.setattr(Vertex, "cliente", cliente)
    logger = logging.getLogger()
    anteriores = tuple(logger.handlers)
    yield
    for handler in tuple(logger.handlers):
        if handler not in anteriores:
            logger.removeHandler(handler)
            handler.close()
    for handler in anteriores:
        if handler not in logger.handlers:
            logger.addHandler(handler)
