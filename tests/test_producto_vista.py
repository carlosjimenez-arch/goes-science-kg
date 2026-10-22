"""Seguridad y trazabilidad de la vista local, sin modelos ni reserva educativa."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from types import SimpleNamespace

import pytest

from goes_science_kg.curriculo.contratos import (
    FASES,
    CeldaCurricular,
    ColumnaCurricular,
    Curriculo,
    FaseCurricular,
    FilaCurricular,
    FuenteCurricular,
    HojaCurricular,
)
from goes_science_kg.producto.vista import markdown, vista


class Documento(HTMLParser):
    """Lee el contenedor JSON con las reglas reales del parser HTML."""

    def __init__(self, contenido: str):
        super().__init__()
        self.en_datos = False
        self.contenido: list[str] = []
        self.scripts: list[dict] = []
        self.feed(contenido)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            atributos = dict(attrs)
            self.scripts.append(atributos)
            self.en_datos = atributos.get("id") == "datos-curriculares"

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.en_datos = False

    def handle_data(self, data: str) -> None:
        if self.en_datos:
            self.contenido.append(data)

    @property
    def datos(self) -> dict:
        return json.loads("".join(self.contenido))


def _celda(coordenada: str, campo: str, valor: str, origen: str | None = None) -> CeldaCurricular:
    return CeldaCurricular(
        coordenada=coordenada,
        fila=int("".join(c for c in coordenada if c.isdigit())),
        columna="".join(c for c in coordenada if c.isalpha()),
        campo=campo,
        valor_original=None if origen else valor,
        valor=valor,
        origen_combinado=origen,
        tipo_excel="s",
    )


def _curriculo(contenido: str = "Materia", url: str = "https://docs.google.com/spreadsheets/d/original") -> Curriculo:
    fuentes = tuple(
        FuenteCurricular(
            id=identidad,
            version="V4",
            archivo=archivo,
            archivo_local="insumos/v4/" + archivo,
            sha256=sha * 64,
            bytes=20,
            procedencia={"archivo": {"url": url}},
        )
        for identidad, archivo, sha in (("FA", "A.xlsx", "a"), ("FB", "B.xlsx", "b"))
    )
    filas = []
    for numero, (grado, fuente, asignatura, hoja, fila) in enumerate(
        (
            (6, "FA", "Ciencias", "Unidad exacta ", 3),
            (6, "FA", "Ciencias", "Unidad exacta ", 4),
            (10, "FB", "Biología", "Biología 10.°", 3),
        ),
        1,
    ):
        fases = {
            nombre: FaseCurricular(
                presente_en_hoja=nombre != "aproximar",
                texto="Comparar observaciones" if nombre == "indagar" else "",
                codigos_locales=("D4",) if nombre == "indagar" else (),
                coordenadas=(f"K{fila}",) if nombre == "indagar" else (),
            )
            for nombre in FASES
        }
        filas.append(
            FilaCurricular(
                id=f"F{numero}",
                fuente_id=fuente,
                version="V4",
                hoja=hoja,
                fila=fila,
                grado=grado,
                asignatura_malla=asignatura,
                unidad="Unidad uno",
                contenido=contenido,
                procedimental="Comparación de dos modelos",
                indicadores_logro="Explica sus límites",
                evidencia_aprendizaje="Registro de observaciones",
                fases=fases,
                celdas=(
                    _celda(f"C{fila}", "contenido", contenido),
                    _celda(f"E{fila}", "procedimental", "Comparación de dos modelos"),
                    _celda(f"W{fila}", "notacion", "Notación", "W3" if fila == 4 else None),
                ),
            )
        )
    return Curriculo(
        version="V4",
        huella="c" * 64,
        fuentes=fuentes,
        filas=tuple(filas),
        agrupaciones=(),
        hojas=(
            HojaCurricular(
                fuente_id="FA",
                nombre="Unidad exacta ",
                tratamiento="curricular",
                motivo="Prueba local",
                grado=6,
                filas_encabezado=(1, 2),
                columnas=(ColumnaCurricular(columna="I", indice=9, encabezados=("Fases", "Explorar")),),
                filas_curriculares=("F1", "F2"),
            ),
        ),
    )


def _catalogo(curriculo: Curriculo, *, huella: str | None = None, filas: tuple = ()) -> SimpleNamespace:
    return SimpleNamespace(
        version_curriculo=curriculo.version,
        huella_curriculo=huella or curriculo.huella,
        filas=filas,
    )


def _decision(fila_id: str, estado: str, disciplinas: tuple[str, ...] = ()) -> SimpleNamespace:
    return SimpleNamespace(
        fila_id=fila_id,
        estado=estado,
        disciplinas=disciplinas,
        metodo="Lecturas independientes",
        justificacion="Clasificación local de prueba",
        errores=(),
    )


def test_todas_las_filas_y_cinco_fases_se_conservan_sin_catalogo():
    curriculo = _curriculo()
    datos = Documento(vista(curriculo)).datos
    assert {f["id"] for f in datos["filas"]} == {f.id for f in curriculo.filas}
    assert len(datos["filas"]) == 3
    assert datos["filas"][0]["clasificacion"]["estado"] == "sin_clasificar"
    assert datos["filas"][2]["clasificacion"]["estado"] == "declarado_malla"
    assert datos["filas"][2]["clasificacion"]["disciplinas"] == ["biologia"]
    for fila in datos["filas"]:
        assert [fase["nombre"] for fase in fila["fases"]] == list(FASES)
        assert not fila["fases"][0]["presente"]
        assert fila["conocimiento_pisa"] == ""
        assert fila["contexto_pisa"] == ""
    assert datos["filas"][0]["fuente"]["hoja"] == "Unidad exacta "
    assert datos["filas"][0]["fuente"]["sha256"] == "a" * 64


@pytest.mark.parametrize(
    "carga",
    [
        '</script><img src=x onerror="alert(1)"><script>',
        '</ScRiPt><svg onload="alert(1)">',
        '<!-- <script> & <h1 onclick="evil()">texto</h1>',
        "Separador\u2028y\u2029saltos < > &",
    ],
)
def test_cargas_xss_son_datos_y_no_crean_nuevas_etiquetas(carga):
    resultado = vista(_curriculo(carga))
    documento = Documento(resultado)
    assert len(documento.scripts) == 2
    assert all("src" not in script for script in documento.scripts)
    assert documento.datos["filas"][0]["contenido"] == carga
    assert carga not in resultado
    assert "innerHTML" not in resultado
    assert "outerHTML" not in resultado
    assert "document.write" not in resultado
    assert "connect-src 'none'" in resultado


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "data:text/html,<script>evil()</script>",
        "https://usuario:clave@docs.google.com/original",
        "https://docs.google.com/\nmalicioso",
    ],
)
def test_enlaces_no_web_o_con_credenciales_no_se_habilitan(url):
    datos = Documento(vista(_curriculo(url=url))).datos
    assert datos["filas"][0]["fuente"]["drive_url"] == ""
    assert datos["filas"][0]["fuente"]["url_declarada"] == url


def test_rechaza_catalogos_ajenos_y_ids_desconocidos_o_duplicados():
    curriculo = _curriculo()
    with pytest.raises(ValueError, match="otra versión o captura"):
        vista(curriculo, _catalogo(curriculo, huella="d" * 64))
    for decisiones in (
        (_decision("F999", "abstencion"),),
        (_decision("F1", "abstencion"), _decision("F1", "abstencion")),
    ):
        with pytest.raises(ValueError, match="repite filas o referencia filas ajenas"):
            vista(curriculo, _catalogo(curriculo, filas=decisiones))


def test_consenso_abstencion_y_catalogo_parcial_no_ocultan_filas():
    curriculo = _curriculo()
    catalogo = _catalogo(
        curriculo,
        filas=(
            _decision("F1", "coincidencia_automatica", ("fisica", "quimica")),
            _decision("F2", "abstencion"),
        ),
    )
    datos = Documento(vista(curriculo, catalogo)).datos
    por_id = {f["id"]: f for f in datos["filas"]}
    assert len(por_id) == 3
    assert por_id["F1"]["clasificacion"]["disciplinas"] == ["fisica", "quimica"]
    assert por_id["F2"]["clasificacion"]["estado"] == "abstencion"
    assert por_id["F3"]["clasificacion"]["estado"] == "declarado_malla"


def test_alertas_se_localizan_por_celda_combinada_encabezado_y_sha():
    curriculo = _curriculo()

    def alerta(identidad, sha, hoja, celdas, contraste=()):
        return {
            "id": identidad,
            "fuente": {"archivo": "insumos/v4/A.xlsx", "sha256": sha, "hoja": hoja, "celdas": celdas},
            "explicacion": "Revisar el texto original",
            "contraste_documental": list(contraste),
        }

    registro = {
        "alertas": [
            alerta("CELDA", "a" * 64, "Unidad exacta ", ["W3"]),
            alerta("ENCABEZADO", "a" * 64, "Notas", ["B3"], ({"hoja": "Unidad exacta ", "celdas": ["I2"]},)),
            alerta("OBSOLETA", "e" * 64, "Unidad exacta ", ["W3"]),
        ]
    }
    datos = Documento(vista(curriculo, alertas=registro)).datos
    por_id = {f["id"]: f for f in datos["filas"]}
    assert por_id["F1"]["alertas"] == [0, 1]
    assert por_id["F2"]["alertas"] == [0, 1]
    assert por_id["F3"]["alertas"] == []
    assert len(datos["alertas"]) == 3
    assert not datos["alertas"][2]["coincide_captura"]


def test_alertas_de_rango_no_se_extienden_a_columnas_ni_encabezados_ajenos():
    curriculo = _curriculo()
    referencia = {"archivo": "A.xlsx", "sha256": "a" * 64, "hoja": "Notas", "celdas": ["B3"]}
    alertas = {
        "alertas": [
            {
                "id": "RANGO",
                "fuente": referencia,
                "contraste_documental": [{"hoja": "Unidad exacta ", "rango": "B3:E4"}],
            },
            {
                "id": "FUERA",
                "fuente": referencia,
                "contraste_documental": [{"hoja": "Unidad exacta ", "rango": "AZ3:AZ4"}],
            },
            {
                "id": "CABECERA_AJENA",
                "fuente": referencia,
                "contraste_documental": [{"hoja": "Unidad exacta ", "celdas": ["AZ2"]}],
            },
        ]
    }
    datos = Documento(vista(curriculo, alertas=alertas)).datos
    assert datos["filas"][0]["alertas"] == [0]
    assert datos["filas"][1]["alertas"] == [0]
    assert datos["filas"][2]["alertas"] == []


def test_no_presenta_filas_de_otra_version_como_parte_de_v4():
    curriculo = _curriculo()
    mezclado = curriculo.model_copy(
        update={
            "filas": (curriculo.filas[0].model_copy(update={"version": "V3"}), *curriculo.filas[1:]),
        }
    )
    with pytest.raises(ValueError, match="mezcla versiones"):
        vista(mezclado)


def test_exporta_markdown_citable_con_ausencias_y_texto_html_escapado():
    curriculo = _curriculo('<script>alert("x")</script>')
    completo = markdown(curriculo)
    ficha = markdown(curriculo, fila_id="F1")
    assert completo.count("**ID de fila:**") == 3
    assert ficha.count("**ID de fila:**") == 1
    assert "Ausente en esta hoja" in ficha
    assert "No declarado en el insumo" in ficha
    assert "<script>" not in ficha
    assert "&lt;script&gt;" in ficha
    assert "a" * 64 in ficha
    assert "Unidad exacta" in ficha
    assert "**Fila física:** 3" in ficha
    assert "W3" in ficha
    assert markdown(curriculo) == completo
    with pytest.raises(ValueError, match="no pertenece"):
        markdown(curriculo, fila_id="AJENA")


def test_captura_vacia_y_registro_ausente_no_se_presentan_como_validacion():
    vacio = Curriculo(version="V4", huella="f" * 64, fuentes=(), filas=(), hojas=(), agrupaciones=())
    datos = Documento(vista(vacio)).datos
    assert datos["filas"] == []
    assert not datos["alertas_cargadas"]
    assert "no acredita" in datos["limite"]
