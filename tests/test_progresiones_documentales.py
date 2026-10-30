"""Test native progression bands, physical anchors, and documentary chains without grade equivalence."""

from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from goes_science_kg.ingesta.progresiones import CatalogoProgresiones, RepositorioProgresiones


@pytest.fixture
def catalogo():
    datos = yaml.safe_load(Path("config/progresiones_documentales_2026.yaml").read_text())
    return CatalogoProgresiones.model_validate(datos)


@pytest.mark.parametrize("alteracion", ["omision", "duplicada", "edicion", "dimension"])
def test_cadena_no_admite_bandas_duplicadas_omitidas_o_mezcla(catalogo, alteracion):
    d = catalogo.model_dump(mode="json")
    if alteracion == "omision":
        d["expectativas"].pop(0)
    elif alteracion == "duplicada":
        d["expectativas"][1]["id"] = d["expectativas"][0]["id"]
    else:
        d["expectativas"][0]["version_documental" if alteracion == "edicion" else "dimension"] = (
            "otra edición" if alteracion == "edicion" else "practica_cientifica"
        )
    with pytest.raises(ValueError):
        CatalogoProgresiones.model_validate(d)


class Pagina:
    def __init__(self, expectativa, *, encabezado=None, cuerpo=None):
        self.e = expectativa
        self.page_number = expectativa.pagina_pdf
        self.encabezado, self.cuerpo = encabezado, cuerpo

    def crop(self, bbox, *, strict):
        assert strict
        texto = (
            self.encabezado or self.e.banda
            if bbox == self.e.region_banda.bbox
            else (self.cuerpo or self.e.ancla_inicial + " contenido conservado " + self.e.ancla_final)
        )
        return SimpleNamespace(extract_text=lambda: texto)


class PDF:
    def __init__(self, pagina):
        self.pages = [pagina]

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def repositorio(catalogo):
    registros = {
        e.fuente: SimpleNamespace(sha256=e.sha256, version_documental=e.version_documental)
        for e in catalogo.expectativas
    }
    return RepositorioProgresiones(
        SimpleNamespace(
            manifiesto=lambda: SimpleNamespace(referencias=registros), leer_pdf_verificado=lambda id_: b"pdf-prueba"
        ),
        catalogo,
    )


def test_encabezado_fisico_y_extremos_son_obligatorios(catalogo, monkeypatch):
    e = catalogo.expectativas[0]
    r = repositorio(catalogo)
    for pagina, mensaje in [
        (Pagina(e, encabezado="3-5"), "encabezado"),
        (Pagina(e, cuerpo="Texto cortado"), "extremo"),
    ]:
        monkeypatch.setattr("pdfplumber.open", lambda *args, pagina=pagina, **kwargs: PDF(pagina))
        with pytest.raises(ValueError, match=mensaje):
            r.evidencia(e)
    monkeypatch.setattr("pdfplumber.open", lambda *args, **kwargs: PDF(Pagina(e)))
    evidencia = r.evidencia(e)
    assert evidencia.fuente["banda_nativa"] == "K-2"
    assert evidencia.fuente["region_banda"] == e.region_banda.model_dump(mode="json")
    assert evidencia.version == "referencia" and "grado_sv" not in evidencia.fuente
