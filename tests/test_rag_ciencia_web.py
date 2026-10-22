"""El RAG auxiliar reabre el párrafo exacto; sólo se evalúa su corpus delimitado."""

import pytest

from goes_science_kg.ingesta.web_cientifica import FuenteWeb, RepositorioWeb, SelectorWeb
from goes_science_kg.recuperacion.ciencia_web import IndiceCienciaWeb, fragmentar_web


def test_recuperacion_bilingue_sin_recortar_parrafos_y_relectura(tmp_path, monkeypatch):
    texto = (
        "Monosaccharides are simple sugars; glucose is a common example. "
        "Polysaccharides are long chains made of linked monosaccharides."
    )
    contenido = f"<main><p>{texto}</p></main>".encode()
    fuente = FuenteWeb(
        id="biologia",
        titulo="Ciencias",
        institucion="Fuente sintética",
        version_documental="prueba-1",
        url="https://openstax.org/prueba",
        selector=SelectorWeb(etiqueta="main"),
        licencia="Sólo fixture",
    )
    monkeypatch.setattr("goes_science_kg.ingesta.web_cientifica.descargar_web", lambda f: contenido)
    repo = RepositorioWeb(tmp_path)
    repo.incorporar(fuente)
    indice = IndiceCienciaWeb(repo)
    recuperadas = indice.buscar("carbohidratos y biomoléculas")
    assert len(recuperadas) == 1 and recuperadas[0].texto == texto
    assert indice.buscar("carbohidratos", max_caracteres=50) == ()
    e = recuperadas[0]
    assert indice.rehidratar(e) == e
    with pytest.raises(ValueError):
        indice.rehidratar(e.model_copy(update={"texto": "Un resumen sin procedencia"}))
    assert all(p.fuente["parrafo_dom"] >= 0 for p in fragmentar_web(repo.evidencia("biologia")))
