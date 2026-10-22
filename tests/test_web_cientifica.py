"""Extracción HTML localizada, sin código activo ni confianza en texto cacheado."""

import json

import pytest

from goes_science_kg.ingesta.web_cientifica import FuenteWeb, RepositorioWeb, SelectorWeb, _url, extraer_html

TEXTO = "La fuente científica describe materia, evidencia y condiciones de aplicación con suficiente detalle."
SELECTOR = SelectorWeb(etiqueta="main", atributo="id", valor="main")


def html(texto=TEXTO):
    return (
        f'<html><nav>no citar navegación</nav><main id="main"><p>{texto}</p>'
        '<script>código</script><p hidden>secreto</p></main></html>'
    ).encode()


def test_selector_no_incorpora_scripts_ni_texto_oculto():
    assert extraer_html(html(), SELECTOR) == TEXTO


def test_dos_anclajes_o_fuente_ilegible_no_se_aceptan():
    for contenido in (html() + html(), b"<main>nada</main>", b"\xff"):
        with pytest.raises((ValueError, UnicodeDecodeError)):
            extraer_html(contenido, SELECTOR)


@pytest.mark.parametrize(
    "url", ["http://openstax.org/a", "https://evil.test/a", "https://a@openstax.org/a", "https://openstax.org/a#otro"]
)
def test_solo_https_oficial_sin_credenciales(url):
    with pytest.raises(ValueError):
        _url(url)


def test_captura_releida_y_mutacion_rechazada(tmp_path, monkeypatch):
    fuente = FuenteWeb(
        id="oficial",
        titulo="Prueba",
        institucion="Prueba",
        version_documental="captura-1",
        url="https://openstax.org/prueba",
        selector=SELECTOR,
        licencia="Atribución de prueba",
    )
    monkeypatch.setattr("goes_science_kg.ingesta.web_cientifica.descargar_web", lambda f: html())
    repo = RepositorioWeb(tmp_path)
    r = repo.incorporar(fuente)
    e = repo.evidencia("oficial")
    assert e.texto == TEXTO and e.fuente["verificacion"] == "contenido_fuente"
    manifest = json.loads((tmp_path / "manifest.json").read_bytes())
    assert manifest["fuentes"]["oficial"]["sha256"] == r["sha256"]
    (tmp_path / "objetos" / f"{r['sha256']}.html").write_bytes(html("Captura distinta"))
    with pytest.raises(ValueError, match="captura"):
        repo.evidencia("oficial")
