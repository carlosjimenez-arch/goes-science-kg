"""Una etiqueta vacía no debe hacer desaparecer evidencia primaria."""

import pytest

from goes_science_kg.clases.extractos import parrafos_literales


@pytest.mark.parametrize("vacio", [b"<p/>", b'<p class="espacio" />', b"<P />", b"<para/>"])
def test_etiqueta_vacia_no_consume_el_parrafo_siguiente(vacio):
    cuerpo = "<p>Las abejas elaboran miel a partir de néctar; conservar este texto literal.</p>".encode()
    raw = vacio + cuerpo
    rangos = parrafos_literales(raw)
    assert len(rangos) == 1
    inicio, fin = rangos[0]
    assert raw[inicio:fin] == cuerpo


def test_byte_offsets_con_texto_unicode_y_limites():
    primero = "<para>Una explicación física en español con símbolos y acentos.</para>".encode()
    segundo = b"<p>Otro parrafo suficientemente largo para conservar la fuente completa.</p>"
    raw = "Introducción: ".encode() + primero + b"<p/>" + segundo
    assert [raw[a:z] for a, z in parrafos_literales(raw)] == [primero, segundo]
    assert not parrafos_literales(raw, maximo=55)


def test_no_reconstruye_parrafos_truncados_ni_anidados():
    assert not parrafos_literales(b"<p>" + b"x" * 80)
    assert not parrafos_literales(b"<p>" + b"x" * 80 + b"<p>nested</p></p>")
