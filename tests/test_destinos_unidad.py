"""Reject unit-package output paths inside primary collections or evaluation datasets."""

import pytest

from goes_science_kg.archivos import PROTEGIDAS
from goes_science_kg.producto.unidades import _directorio


@pytest.mark.parametrize("protegida", PROTEGIDAS)
def test_directorios_de_paquetes_comparten_la_politica_de_fuentes(tmp_path, monkeypatch, protegida):
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    destino = tmp_path / protegida / "paquete-nuevo"
    with pytest.raises(ValueError, match="fuera de originales"):
        _directorio(destino)
    assert not destino.exists()
