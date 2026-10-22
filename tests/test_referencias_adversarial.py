"""Regresiones adversariales offline: rutas, concurrencia y procedencia de referencias."""

from __future__ import annotations

import socket
import threading
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from urllib.request import HTTPRedirectHandler, Request

import pytest
from pydantic import ValidationError
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from typer.testing import CliRunner

from goes_science_kg.cli import app
from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias, descargar_pdf


def _pdf(texto: str = "Scientific claims need independently traceable evidence.") -> bytes:
    escritor = PdfWriter()
    pagina = escritor.add_blank_page(width=612, height=792)
    fuente = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    pagina[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): escritor._add_object(fuente)}),
    })
    contenido = DecodedStreamObject()
    literal = texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    contenido.set_data(f"BT /F1 12 Tf 72 720 Td ({literal}) Tj ET".encode("ascii"))
    pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


def _fuente(identificador="marco_adversarial", *, url_documento=None) -> FuentePublica:
    return FuentePublica(
        id=identificador,
        titulo="Documento sintético para pruebas de integridad",
        institucion="OECD",
        version_documental="Prueba sin vigencia curricular",
        url_catalogo="https://www.oecd.org/en/publications/",
        url_documento=url_documento or "https://www.oecd.org/content/dam/synthetic-test.pdf",
        estado_publicacion="publicado_final",
    )


@pytest.mark.parametrize("subdirectorio", ["objetos", "paginas"])
def test_symlink_no_permite_escribir_fuera_del_almacen(tmp_path, monkeypatch, subdirectorio):
    almacen = tmp_path / "almacen"
    externo = tmp_path / "fuera_del_almacen"
    almacen.mkdir()
    externo.mkdir()
    (almacen / subdirectorio).symlink_to(externo, target_is_directory=True)
    contenido = _pdf()
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (contenido, f.url_documento))
    repositorio = RepositorioReferencias(almacen)
    with pytest.raises((ValueError, OSError)):
        repositorio.incorporar([_fuente()], descargar=True)
    assert not list(externo.iterdir()), "La comprobación de ruta debe ocurrir antes de crear temporales u objetos"
    assert not repositorio.archivo_manifest.exists()


def test_ingestas_concurrentes_no_pierden_registros(tmp_path, monkeypatch):
    contenido = _pdf()
    primera_en_descarga = threading.Event()
    segunda_en_descarga = threading.Event()

    def descargar(fuente):
        if fuente.id == "primera":
            primera_en_descarga.set()
            # Sin lock, ambas leen el manifiesto vacío antes de continuar. Con lock completo,
            # expira esta espera breve y la segunda ingesta lee el manifiesto ya publicado.
            segunda_en_descarga.wait(timeout=0.4)
        else:
            segunda_en_descarga.set()
        return contenido, fuente.url_documento

    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", descargar)
    primero = RepositorioReferencias(tmp_path)
    segundo = RepositorioReferencias(tmp_path)
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        f1 = ejecutor.submit(primero.incorporar, [_fuente("primera")], descargar=True)
        assert primera_en_descarga.wait(timeout=2)
        f2 = ejecutor.submit(segundo.incorporar, [_fuente("segunda")], descargar=True)
        f1.result(timeout=10)
        f2.result(timeout=10)
    assert set(primero.manifiesto().referencias) == {"primera", "segunda"}
    assert {d.fuente["documento"] for d in primero.documentos()} == {"primera", "segunda"}


@pytest.mark.parametrize("url_final", [
    "https://attacker.invalid/marco.pdf",
    "https://www.oecd.org.attacker.invalid/marco.pdf",
    "http://www.oecd.org/marco.pdf",
    "https://127.0.0.1/marco.pdf",
])
def test_incorporar_verifica_url_final_independientemente_del_descargador(tmp_path, monkeypatch, url_final):
    contenido = _pdf()
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (contenido, url_final))
    repositorio = RepositorioReferencias(tmp_path)
    with pytest.raises((ValueError, ValidationError)):
        repositorio.incorporar([_fuente()], descargar=True)
    assert not repositorio.archivo_manifest.exists()
    assert not list(tmp_path.rglob("*.pdf"))


@pytest.mark.parametrize("url", [
    "https://localhost/marco.pdf",
    "https://127.0.0.1/marco.pdf",
    "https://[::1]/marco.pdf",
    "https://169.254.169.254/marco.pdf",
    "https://www.oecd.org.attacker.invalid/marco.pdf",
])
def test_destino_no_oficial_se_rechaza_antes_de_dns_o_red(monkeypatch, url):
    def prohibir_red(*args, **kwargs):
        pytest.fail("La URL no permitida debe rechazarse antes de resolver DNS o abrir conexiones")

    monkeypatch.setattr(socket, "getaddrinfo", prohibir_red)
    monkeypatch.setattr(socket, "create_connection", prohibir_red)
    with pytest.raises((ValueError, ValidationError)):
        descargar_pdf(_fuente(url_documento=url))


def test_cli_id_desconocido_informa_error_de_entrada_sin_traceback(monkeypatch):
    monkeypatch.setattr("goes_science_kg.cli.referencias.cargar", lambda nombre: {"fuentes": {}})
    resultado = CliRunner().invoke(app, ["investigacion", "referencias", "ingerir", "no_existe"])
    assert resultado.exit_code == 2
    assert "Invalid value" in resultado.output or "Error" in resultado.output
    assert not isinstance(resultado.exception, KeyError)


@pytest.mark.parametrize("destino", ["https://attacker.invalid/a.pdf", "http://www.oecd.org/a.pdf"])
def test_redireccion_no_oficial_se_bloquea_antes_de_delegar_su_seguimiento(monkeypatch, destino):
    from goes_science_kg.ingesta.referencias import _RedireccionOficial

    seguidas = []

    def seguir(*args, **kwargs):
        seguidas.append(destino)
        pytest.fail("No debe delegarse el seguimiento de una redirección fuera de la política")

    monkeypatch.setattr(HTTPRedirectHandler, "redirect_request", seguir)
    solicitud = Request("https://www.oecd.org/origen.pdf")
    with pytest.raises(ValueError):
        _RedireccionOficial().redirect_request(solicitud, None, 302, "Found", {}, destino)
    assert not seguidas
