"""Ingesta real de PDF sintético, sin red, credenciales ni fuentes históricas."""

from __future__ import annotations

import json
from io import BytesIO

import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from typer.testing import CliRunner

from goes_science_kg.cli import app
from goes_science_kg.ingesta.dimensiones import CatalogoDimensiones, validar_dimensiones
from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias, fuentes_del_catalogo
from goes_science_kg.recuperacion import Buscador


def pdf_de_prueba(textos=("Scientific reasoning requires evidence.", "Compare plants under controlled conditions.")):
    escritor = PdfWriter()
    fuente = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    for texto in textos:
        pagina = escritor.add_blank_page(width=600, height=800)
        pagina[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): escritor._add_object(fuente)})}
        )
        contenido = DecodedStreamObject()
        contenido.set_data(f"BT /F1 12 Tf 50 750 Td ({texto}) Tj ET".encode("ascii"))
        pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


@pytest.fixture
def fuente():
    return FuentePublica(
        id="marco_prueba",
        titulo="Marco sintético para pruebas",
        institucion="Institución de prueba",
        version_documental="2026",
        url_catalogo="https://www.oecd.org/marco",
        url_documento="https://www.oecd.org/marco.pdf",
        estado_publicacion="publicado_final",
    )


@pytest.fixture
def repositorio(tmp_path, monkeypatch, fuente):
    contenido = pdf_de_prueba()
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (contenido, f.url_documento))
    repositorio = RepositorioReferencias(tmp_path / "referencias")
    repositorio.incorporar([fuente], descargar=True)
    return repositorio


def test_fuente_original_pagina_y_recuperacion_comparten_identidad(repositorio, fuente):
    registro = repositorio.manifiesto().referencias[fuente.id]
    assert registro.paginas == registro.paginas_con_texto == 2
    assert registro.extractor.startswith("pypdf/")
    documentos = repositorio.documentos()
    resultados = Buscador(documentos).buscar("plants controlled", version="referencia", saltos_grafo=0)
    assert resultados[0].documento.fuente["pagina"] == 2
    evidencia = repositorio.pagina(fuente.id, 2)
    assert "plants" in evidencia.texto
    assert evidencia.fuente["sha256"] == registro.sha256
    assert evidencia.fuente["verificacion"] == "contenido_fuente"
    assert evidencia.version == "referencia"


def test_por_defecto_no_hace_red_y_valida_objetos(repositorio, fuente, monkeypatch):
    def prohibir(_):
        pytest.fail("La comprobación local no debe acceder a la red")

    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", prohibir)
    assert repositorio.incorporar([fuente]).referencias[fuente.id].paginas == 2


def test_fuente_pendiente_no_se_presenta_como_ingerida(tmp_path, fuente):
    with pytest.raises(FileNotFoundError, match="pendiente"):
        RepositorioReferencias(tmp_path).incorporar([fuente])


def test_servidor_cambiado_no_sustituye_documento_fijado(repositorio, fuente, monkeypatch):
    anterior = repositorio.archivo_manifest.read_bytes()
    monkeypatch.setattr(
        "goes_science_kg.ingesta.referencias.descargar_pdf",
        lambda f: (pdf_de_prueba(("Changed source.",)), f.url_documento),
    )
    with pytest.raises(ValueError, match="servidor cambió"):
        repositorio.incorporar([fuente], descargar=True)
    assert repositorio.archivo_manifest.read_bytes() == anterior
    assert "Scientific reasoning" in repositorio.pagina(fuente.id, 1).texto


@pytest.mark.parametrize("objeto", ["archivo_pdf", "archivo_paginas"])
def test_no_se_confia_en_objetos_mutados(repositorio, fuente, objeto):
    registro = repositorio.manifiesto().referencias[fuente.id]
    (repositorio.raiz / getattr(registro, objeto)).write_bytes(b"alterado")
    with pytest.raises(ValueError, match="Integridad"):
        repositorio.documentos()


def test_lote_incompleto_no_publica_manifest_parcial(tmp_path, fuente, monkeypatch):
    primera = fuente.model_copy(update={"id": "primera"})
    segunda = fuente.model_copy(update={"id": "segunda"})

    def descargar(fuente):
        if fuente.id == "segunda":
            raise OSError("Servidor caído")
        return pdf_de_prueba(), fuente.url_documento

    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", descargar)
    repositorio = RepositorioReferencias(tmp_path)
    with pytest.raises(OSError):
        repositorio.incorporar([primera, segunda], descargar=True)
    assert not repositorio.manifiesto().referencias


def test_no_ingerir_html_ni_pdf_sin_texto(tmp_path, fuente, monkeypatch):
    repositorio = RepositorioReferencias(tmp_path)
    for contenido in (b"<html>Access denied</html>", pdf_de_prueba(("",))):
        monkeypatch.setattr(
            "goes_science_kg.ingesta.referencias.descargar_pdf", lambda f, c=contenido: (c, f.url_documento)
        )
        with pytest.raises(ValueError):
            repositorio.incorporar([fuente], descargar=True)
    assert not repositorio.manifiesto().referencias


@pytest.mark.parametrize(
    "url", ["http://example.org/a.pdf", "https://user:password@example.org/a.pdf", "file:///a.pdf"]
)
def test_solo_urls_https_sin_credenciales(fuente, url):
    with pytest.raises(ValidationError):
        FuentePublica.model_validate(fuente.model_dump() | {"url_documento": url})


def test_no_inventar_url_documental(fuente):
    catalogo = {"fuentes": {"sin_pdf": {"url": fuente.url_catalogo}}}
    with pytest.raises(ValueError, match="URL documental"):
        fuentes_del_catalogo(catalogo, ["sin_pdf"])


def test_cambio_metadatos_documentales_exige_identidad_nueva(repositorio, fuente):
    with pytest.raises(ValueError, match="identidad"):
        repositorio.incorporar([fuente.model_copy(update={"version_documental": "2027"})])


def test_pagina_fuera_de_rango_no_devuelve_otra(repositorio, fuente):
    with pytest.raises(ValueError, match="rango"):
        repositorio.pagina(fuente.id, 3)


def test_cli_estado_busqueda_y_pagina_son_solo_lectura(repositorio, fuente, monkeypatch, tmp_path):
    monkeypatch.setattr("goes_science_kg.cli.referencias._repositorio", lambda: repositorio)
    runner = CliRunner()
    resultado = runner.invoke(app, ["investigacion", "referencias", "estado"])
    assert resultado.exit_code == 0, resultado.output
    assert json.loads(resultado.stdout)["referencias"][fuente.id]["paginas"] == 2
    resultado = runner.invoke(app, ["investigacion", "referencias", "buscar", "plants"])
    assert resultado.exit_code == 0, resultado.output
    assert "P0002" in resultado.stdout
    destino = tmp_path / "evidencia.json"
    resultado = runner.invoke(app, ["investigacion", "referencias", "pagina", fuente.id, "2", "--salida", str(destino)])
    assert resultado.exit_code == 0, resultado.output
    assert json.loads(destino.read_text())["fuente"]["pagina"] == 2
    prohibido = repositorio.raiz / "evidencia.json"
    resultado = runner.invoke(
        app, ["investigacion", "referencias", "pagina", fuente.id, "2", "--salida", str(prohibido)]
    )
    assert resultado.exit_code != 0
    assert not prohibido.exists()


def _catalogo(fuente, **cambios):
    return {
        "schema_version": "1.0",
        "meta": {
            "clasificacion": "parafrasis_del_proyecto",
            "no_equivalencia": "No es una alineación ni un código oficial",
            "corte": "2026-10-21",
            "alcance": "Documento sintético utilizado solo para pruebas",
            "paginas": "Numeración PDF desde 1, incluyendo portada",
            "procedencia": "data/referencias_2026/manifest.json",
            "auditoria": "docs/investigacion/auditoria_fuentes_primarias.md",
            "limites": ["No acredita cobertura de una tarea ni eficacia pedagógica"],
        },
        "dimensiones": [
            {
                "id": "LOCAL:razonamiento",
                "fuente": fuente.id,
                "eje": "practica",
                "etiqueta": "Usar evidencia al razonar",
                "paginas_pdf": [1],
                "ancla": "Scientific reasoning requires evidence.",
                "alcance": "Documento sintético de pruebas; sin equivalencia por grado",
            }
            | cambios
        ],
    }


def test_dimension_verificada_solo_acredita_ancla_documental(repositorio, fuente):
    catalogo = CatalogoDimensiones.model_validate(_catalogo(fuente))
    resultado = validar_dimensiones(catalogo, repositorio)
    assert resultado["estado"] == "anclas_documentales_verificadas"
    assert resultado["dimensiones"][0]["paginas_con_ancla"][0]["pagina_pdf"] == 1
    assert "no cobertura curricular" in resultado["limite"]


@pytest.mark.parametrize(
    "cambios",
    [
        {"ancla": "A made up quote not present in any source"},
        {"paginas_pdf": [2]},
        {"paginas_pdf": [3]},
    ],
)
def test_dimension_cita_inexistente_o_pagina_incorrecta_falla(repositorio, fuente, cambios):
    catalogo = CatalogoDimensiones.model_validate(_catalogo(fuente, **cambios))
    with pytest.raises(ValueError):
        validar_dimensiones(catalogo, repositorio)


@pytest.mark.parametrize(
    "cambios",
    [{"id": "PISA:codigo_inventado"}, {"paginas_pdf": [0]}, {"paginas_pdf": [1, 1]}, {"ancla": "word " * 21}],
)
def test_contrato_impide_codigos_oficiales_falsos_y_anclas_invalidas(fuente, cambios):
    with pytest.raises(ValidationError):
        CatalogoDimensiones.model_validate(_catalogo(fuente, **cambios))


def test_dimension_no_se_valida_sobre_fuente_original_mutada(repositorio, fuente):
    registro = repositorio.manifiesto().referencias[fuente.id]
    (repositorio.raiz / registro.archivo_pdf).write_bytes(pdf_de_prueba(("Changed source.",)))
    with pytest.raises(ValueError, match="Integridad"):
        validar_dimensiones(CatalogoDimensiones.model_validate(_catalogo(fuente)), repositorio)
