import pytest

from goes_science_kg.grafo.construir import construir


@pytest.fixture(scope="session")
def grafo():
    return construir()
