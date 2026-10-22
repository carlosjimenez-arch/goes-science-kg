"""Extracción estructurada real y adversarial, sin red, nube ni metadatos como evidencia."""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

import pytest
from test_conocimiento_v4 import _concepto, _generar, _referencia

from goes_science_kg.config import ruta
from goes_science_kg.ingesta import estructurados
from goes_science_kg.ingesta.estructurados import extraer_codigo, huella_implementacion, indexar_documento
from goes_science_kg.modelos import Fuente, Nodo, TipoNodo
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.producto.conocimiento import EdicionEsperada, PoliticaConocimiento
from goes_science_kg.recuperacion import Documento

CODIGO = "AC9S3U01"
DESCRIPCION = "Compare the life cycles of plants and animals using observations and evidence."


def _docx(cuerpo: str, *, estilos: str | None = None) -> bytes:
    salida = BytesIO()
    with ZipFile(salida, "w", compression=ZIP_DEFLATED) as paquete:
        paquete.writestr("word/document.xml", (
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            f"<w:body>{cuerpo}</w:body></w:document>"
        ))
        if estilos:
            paquete.writestr("word/styles.xml", estilos)
    return salida.getvalue()


def _fila(codigo=CODIGO, texto=DESCRIPCION):
    return (f"<w:tr><w:tc><w:p><w:r><w:t>{texto}</w:t></w:r></w:p>"
            f"<w:p><w:r><w:t>{codigo}</w:t></w:r></w:p></w:tc>"
            "<w:tc><w:p><w:r><w:t>Observe, compare and justify conclusions.</w:t></w:r></w:p></w:tc></w:tr>")


def _html(interior: str, *, codigo="ACSBL001", attrs="", antes="") -> bytes:
    return (f'<!DOCTYPE html><html><head>{antes}</head><body><section id="{codigo}" {attrs}>'
            f"{interior}</section></body></html>").encode()


@pytest.mark.parametrize("relativo,codigo,literal", [
    ("paises/australia/AU_Science_F-6_v9_contenido.docx", "AC9S3U01", "compare characteristics of living"),
    ("paises/australia/AU_Science_7-10_v9_contenido.docx", "AC9S7U01", "investigate the role of classification"),
    ("bachillerato/AU_SeniorSecondary_Biology_v8.4_U1-3.html", "ACSBL001", "propose hypotheses"),
])
def test_nativos_reales_conservan_ingles_codigo_unidad_y_bytes(relativo, codigo, literal):
    archivo = ruta("data/fuentes/externos") / relativo
    contenido = archivo.read_bytes()
    sha = hashlib.sha256(contenido).hexdigest()
    resultado = extraer_codigo(contenido, archivo.suffix[1:], codigo)
    assert literal in resultado.texto and codigo in resultado.texto
    assert resultado.localizador == codigo
    assert resultado.huella_implementacion == huella_implementacion()
    assert "stdlib." in resultado.metodo and "sin paginación" in resultado.limites
    assert "pagina" not in resultado.ubicacion
    assert hashlib.sha256(archivo.read_bytes()).hexdigest() == sha
    if archivo.suffix == ".docx":
        assert resultado.ubicacion["parte"] == "word/document.xml"
        assert "/w:tbl[" in resultado.ubicacion["ruta_xml"]
        assert "Observe" in resultado.texto or "classifying" in resultado.texto or "observing" in resultado.texto
    else:
        assert resultado.ubicacion["section_id"] == codigo
        assert "</" not in resultado.texto


def test_docx_elige_fila_completa_sin_otra_fila_y_une_runs_del_codigo():
    cuerpo = "<w:tbl>" + _fila().replace(CODIGO, "AC9S</w:t></w:r><w:r><w:t>3U01")
    cuerpo += _fila("AC9S4U01", "Unrelated content must remain outside this extraction.") + "</w:tbl>"
    resultado = extraer_codigo(_docx(cuerpo), "docx", CODIGO)
    assert DESCRIPCION in resultado.texto and CODIGO in resultado.texto
    assert "Observe, compare and justify conclusions." in resultado.texto
    assert "Unrelated" not in resultado.texto
    assert resultado.ubicacion["ruta_xml"].endswith("/w:tbl[1]/w:tr[1]")


@pytest.mark.parametrize("codigo", ["ac9s3u01", " AC9S3U01", "AC9S3U01 ", "AC9S3U01-extra", "A_001", "123", True, None])
def test_codigo_solicitado_es_estricto_sin_normalizacion_que_fuerce_match(codigo):
    with pytest.raises(ValueError, match="código"):
        extraer_codigo(_docx("<w:tbl>" + _fila() + "</w:tbl>"), "docx", codigo)


@pytest.mark.parametrize("ancla", ["XAC9S3U01", "AC9S3U01X", "ac9s3u01", "AC9S3U01_extra"])
def test_docx_no_acepta_prefijos_sufijos_o_codigo_con_diferente_caja(ancla):
    with pytest.raises(ValueError, match="único"):
        extraer_codigo(_docx("<w:tbl>" + _fila(ancla) + "</w:tbl>"), "docx", CODIGO)


@pytest.mark.parametrize("cuerpo", [
    "<w:tbl>" + _fila() + _fila() + "</w:tbl>",
    "<w:tbl>" + _fila(texto=f"A second occurrence of {CODIGO} makes this ambiguous.") + "</w:tbl>",
    f"<w:p><w:r><w:t>{CODIGO}</w:t></w:r></w:p>",
])
def test_docx_no_resuelve_codigo_ambiguo_ni_fuera_de_tabla(cuerpo):
    with pytest.raises(ValueError):
        extraer_codigo(_docx(cuerpo), "docx", CODIGO)


def test_docx_omite_texto_oculto_eliminado_e_instrucciones_de_campos():
    adicional = ("<w:p><w:r><w:rPr><w:vanish/></w:rPr><w:t>Hidden scientific assertion.</w:t></w:r>"
                 "<w:del><w:r><w:delText>Deleted scientific assertion.</w:delText></w:r></w:del>"
                 "<w:r><w:instrText>INCLUDETEXT external.docx</w:instrText></w:r></w:p>")
    cuerpo = "<w:tbl>" + _fila().replace("</w:tc>", adicional + "</w:tc>", 1) + "</w:tbl>"
    resultado = extraer_codigo(_docx(cuerpo), "docx", CODIGO)
    assert "Hidden" not in resultado.texto and "Deleted" not in resultado.texto and "INCLUDETEXT" not in resultado.texto


def test_docx_codigo_solamente_oculto_no_se_vuelve_ancla():
    cuerpo = "<w:tbl>" + _fila().replace(f"<w:t>{CODIGO}", f"<w:rPr><w:webHidden/></w:rPr><w:t>{CODIGO}") + "</w:tbl>"
    with pytest.raises(ValueError, match="único"):
        extraer_codigo(_docx(cuerpo), "docx", CODIGO)


def test_docx_rechaza_estilos_ocultos_sin_interpretar_su_herencia():
    estilos = ('<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
               '<w:style w:styleId="Hidden"><w:rPr><w:vanish/></w:rPr></w:style></w:styles>')
    with pytest.raises(ValueError, match="estilos"):
        extraer_codigo(_docx("<w:tbl>" + _fila() + "</w:tbl>", estilos=estilos), "docx", CODIGO)


@pytest.mark.parametrize("xml", [
    b'<!DOCTYPE doc [<!ENTITY fuga SYSTEM "file:///etc/passwd">]><doc>&fuga;</doc>',
    '<?xml version="1.0" encoding="UTF-16"?><doc/>'.encode("utf-16"),
])
def test_xml_no_expande_entidades_ni_acepta_codificacion_alternativa(xml):
    salida = BytesIO()
    with ZipFile(salida, "w") as paquete:
        paquete.writestr("word/document.xml", xml)
    with pytest.raises((ValueError, UnicodeDecodeError)):
        indexar_documento(salida.getvalue(), "docx")


def test_zip_bomb_acotada_y_partes_duplicadas_no_producen_indice(monkeypatch):
    contenido = _docx("<w:tbl>" + _fila(texto="Z" * 10000) + "</w:tbl>")
    monkeypatch.setattr(estructurados, "MAX_ZIP", 1000)
    with pytest.raises(ValueError, match="ZIP"):
        indexar_documento(contenido, "docx")
    salida = BytesIO()
    with ZipFile(salida, "w") as paquete:
        paquete.writestr("word/document.xml", "<doc/>")
        with pytest.warns(UserWarning, match="Duplicate"):
            paquete.writestr("word/document.xml", "<otro/>")
    with pytest.raises(ValueError, match="duplicadas"):
        indexar_documento(salida.getvalue(), "docx")


@pytest.mark.parametrize("formato", ["docx", "html"])
def test_limite_de_elementos_rechaza_estructura_antes_de_indexarla(monkeypatch, formato):
    monkeypatch.setattr(estructurados, "MAX_ELEMENTOS", 5)
    contenido = _docx("<w:tbl>" + _fila() + "</w:tbl>") if formato == "docx" else _html(
        "<p>Identify questions (ACSBL001)</p><p>Observe evidence</p>",
    )
    with pytest.raises(ValueError, match="límites|límite"):
        indexar_documento(contenido, formato)


def test_html_preserva_orden_inline_y_excluye_scripts_estilos_y_nodos_ocultos():
    contenido = _html(
        '<p>Identify <span>questions</span> &amp; propose hypotheses (ACSBL001)</p>'
        '<script>Invented script assertion</script><style>.safe {color:red}</style>'
        '<p hidden>Hidden assertion</p><p aria-hidden="true">ARIA assertion</p>'
        '<div style="display: none"><p>Display assertion</p></div>'
        '<span style="visibility:hidden">Invisible assertion</span>'
        '<template>Template assertion</template><noscript>Conditional assertion</noscript>'
        '<details><summary>Summary visible</summary><p>Collapsed assertion</p></details>'
        '<p class="oculto">CSS assertion</p>',
        antes="<style>.oculto {display: none !important}</style>",
    )
    resultado = extraer_codigo(contenido, "html", "ACSBL001")
    assert "Identify questions & propose hypotheses (ACSBL001)" in resultado.texto
    assert "Summary visible" in resultado.texto
    assert "assertion" not in resultado.texto


@pytest.mark.parametrize("attrs", ['hidden', 'hidden="false"', 'aria-hidden="TRUE"', 'style="display:none"'])
def test_html_codigo_en_seccion_oculta_no_da_evidencia(attrs):
    with pytest.raises(ValueError, match="visible"):
        extraer_codigo(_html("<p>Observation (ACSBL001)</p>", attrs=attrs), "html", "ACSBL001")


@pytest.mark.parametrize("html", [
    b'<section id="ACSBL001"><p>Data (ACSBL001X)</p></section>',
    b'<section id="ACSBL001"><span>Data (ACSBL001)</span></section>',
    b'<section id="ACSBL001"><p>Data <span hidden>(ACSBL001)</span></p></section>',
    b'<section id="ACSBL001"><p>Data (ACSBL001) and (ACSBL001)</p></section>',
    b'<section id="ACSBL001"><p>Data (ACSBL001)</p></section><section id="ACSBL001" hidden></section>',
    b'<div id="ACSBL001"><p>Data (ACSBL001)</p></div>',
    b'<section id="ACSBL001" id="ACSBL002"><p>Data (ACSBL001)</p></section>',
    b'<section id="ACSBL001"><p>Data (ACSBL001)</p>',
])
def test_html_no_acepta_anclajes_parciales_ambiguos_o_sin_unidad_fisica(html):
    with pytest.raises(ValueError):
        extraer_codigo(html, "html", "ACSBL001")


@pytest.mark.parametrize("contenido", [
    b'<!DOCTYPE html SYSTEM "https://example.org/externo.dtd"><section/>',
    b'<!ENTITY ext SYSTEM "file:///etc/passwd"><section/>',
    _html('<p>Data (ACSBL001)</p>', attrs='style="d\\69splay:none"'),
    _html('<p>Data (ACSBL001)</p>', attrs='style="display:var(--oculto)"'),
    _html('<p>Data (ACSBL001)</p>', antes='<style>section:not(.visible) {display:none}</style>'),
])
def test_html_no_expande_dtd_o_asume_visible_css_que_no_puede_interpretar(contenido):
    with pytest.raises(ValueError):
        extraer_codigo(contenido, "html", "ACSBL001")


def test_unidad_grande_se_rechaza_entera_y_resultado_no_muta_indice(monkeypatch):
    indice = indexar_documento(_docx("<w:tbl>" + _fila() + "</w:tbl>"), "docx")
    uno = indice.extraer(CODIGO)
    uno.ubicacion["ruta_xml"] = "coordenada inventada"
    assert indice.extraer(CODIGO).ubicacion["ruta_xml"] != "coordenada inventada"
    monkeypatch.setattr(estructurados, "MAX_UNIDAD", 20)
    with pytest.raises(ValueError, match="no se recorta"):
        indice.extraer(CODIGO)


def test_hidratacion_estructurada_verifica_sha_una_vez_cachea_indice_y_limpia_metadata(tmp_path, monkeypatch):
    archivo = tmp_path / "fuente.docx"
    archivo.write_bytes(_docx("<w:tbl>" + _fila() + _fila("AC9S4U01", "Study another native objective.") + "</w:tbl>"))
    sha = hashlib.sha256(archivo.read_bytes()).hexdigest()
    fuentes = FuentesVerificadas({"au": {"archivo_local": archivo.name, "sha256": sha}}, raiz_fuentes=tmp_path)
    llamadas = []
    original = estructurados.indexar_documento

    def observar(*args):
        llamadas.append(1)
        return original(*args)

    monkeypatch.setattr(estructurados, "indexar_documento", observar)

    def documento(codigo):
        return Documento(id=codigo, texto="Invented metadata scientific assertion.", version="referencia", fuente={
            "documento": "au", "localizador": codigo, "pagina": 999, "hoja": "falsa", "fila": 30,
            "celdas": ["X99"], "rango": "A1:Z99", "ubicacion": {"falsa": True},
            "extractor": "inventado", "huella_implementacion": "0" * 64, "sha256": "0" * 64,
        })

    with ThreadPoolExecutor(max_workers=4) as ejecutor:
        evidencias = list(ejecutor.map(fuentes.hidratar, [documento(CODIGO), documento("AC9S4U01")] * 3))
    assert len(llamadas) == fuentes.estadisticas_estructuradas()["indices_parseados"] == 1
    assert fuentes.estadisticas()["archivos_leidos"] == 1
    assert fuentes.estadisticas()["bytes_verificados"] == archivo.stat().st_size
    for evidencia in evidencias:
        assert evidencia is not None
        assert "Invented" not in evidencia.texto
        assert evidencia.fuente["sha256"] == sha
        assert evidencia.fuente["extractor"] != "inventado"
        assert evidencia.fuente["huella_implementacion"] == huella_implementacion()
        assert not {"pagina", "hoja", "fila", "celdas", "rango"}.intersection(evidencia.fuente)
        assert "falsa" not in evidencia.fuente["ubicacion"]
    assert fuentes.hidratar(documento("AC9S3U099")) is None
    archivo.write_bytes(b"Fuente reemplazada despues de cachear indice")
    assert fuentes.hidratar(documento(CODIGO)) is None
    assert len(llamadas) == 1


def test_html_hidratado_no_usa_pagina_ni_fallback_y_sha_incorrecto_falla_antes_del_parser(tmp_path):
    archivo = tmp_path / "fuente.html"
    archivo.write_bytes(_html("<p>Identify questions for investigation (ACSBL001)</p>"))
    sha = hashlib.sha256(archivo.read_bytes()).hexdigest()
    fuente = {"documento": "au", "localizador": "ACSBL001", "pagina": 7, "hoja": "malla"}
    documento = Documento(id="objetivo", texto="Metadata is not evidence.", fuente=fuente, version="referencia")
    fuentes = FuentesVerificadas({"au": {"archivo_local": archivo.name, "sha256": sha}}, raiz_fuentes=tmp_path)
    evidencia = fuentes.hidratar(documento)
    assert evidencia is not None and "Identify questions" in evidencia.texto
    assert evidencia.fuente["ubicacion"]["section_id"] == "ACSBL001"
    assert "pagina" not in evidencia.fuente and "hoja" not in evidencia.fuente
    assert fuentes.hidratar(documento.model_copy(update={"fuente": {"documento": "au", "pagina": 7}})) is None
    incorrectas = FuentesVerificadas({"au": {"archivo_local": archivo.name, "sha256": "0" * 64}}, raiz_fuentes=tmp_path)
    assert incorrectas.hidratar(documento) is None
    assert incorrectas.estadisticas_estructuradas()["indices_parseados"] == 0


@pytest.mark.parametrize("relativo,codigo,literal", [
    ("paises/australia/AU_Science_F-6_v9_contenido.docx", "AC9S3U01", "compare characteristics of living"),
    ("paises/australia/AU_Science_7-10_v9_contenido.docx", "AC9S7U01", "investigate the role of classification"),
    ("bachillerato/AU_SeniorSecondary_Biology_v8.4_U1-3.html", "ACSBL001", "propose hypotheses"),
])
def test_au_real_produce_evidencia_nativa_sin_aceptar_relacion_curricular(tmp_path, relativo, codigo, literal):
    original = ruta("data/fuentes/externos") / relativo
    contenido = original.read_bytes()
    archivo = tmp_path / original.name
    archivo.write_bytes(contenido)
    sha = hashlib.sha256(contenido).hexdigest()
    documento = Nodo(id="DOC:au", tipo=TipoNodo.DOCUMENTO, etiqueta="Australia: snapshot de prueba",
                     props={"archivo_local": archivo.name, "sha256": sha, "version_documental": "edicion-fijada"})
    objetivo = Nodo(id=f"OP:AU:{codigo}", tipo=TipoNodo.OBJETIVO_PAIS,
                    etiqueta="Representación histórica de seres vivos por revalidar.",
                    fuente=Fuente(documento="au", localizador=codigo, pagina=999),
                    props={"pais": "AU", "grado_o_tramo": "Tramo extranjero sin equivalencia"})
    politica = PoliticaConocimiento(ediciones_por_documento={
        "au": EdicionEsperada(sha256=sha, version_documental="edicion-fijada"),
    })
    informe = _generar(tmp_path, _referencia(_concepto("vida", "Seres vivos"), documento, objetivo),
                       texto="Compara seres vivos y registra las diferencias.", contenido="Seres vivos",
                       politica=politica)
    candidato = next(c for c in informe.candidatos if c.tipo == "contraste_pais")
    assert candidato.estado == "candidato" and candidato.referencias_evidencia
    assert "juicio_especializado_pendiente" in candidato.bloqueos_aceptacion
    assert "fuente_original_no_verificable" not in candidato.bloqueos_aceptacion
    assert not informe.aceptados and not informe.dag_aceptado.aristas
    assert informe.resumen["aceptados"] == informe.resumen["alineaciones_confirmadas"] == 0
    assert candidato.contexto["equivalencia_grado_sv"] is None
    evidencia = informe.evidencias[candidato.referencias_evidencia[0]]
    assert literal in evidencia.texto and "Representación histórica" not in evidencia.texto
    assert evidencia.fuente["sha256"] == sha and evidencia.fuente["localizador"] == codigo
    assert "pagina" not in evidencia.fuente
    assert informe.metricas["unidades_estructuradas_referencia"] == {"indices_parseados": 1}
    assert hashlib.sha256(original.read_bytes()).hexdigest() == sha
