"""Test reference contracts and provenance limits using synthetic PDF sources."""

from __future__ import annotations

import copy
from io import BytesIO

import pytest
import yaml
from pydantic import ValidationError
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias
from goes_science_kg.ingesta.referentes_operativos import (
    CatalogoReferentesOperativos,
    cargar_referentes,
    evidencias_referentes,
    validar_referentes,
)


def _pdf() -> bytes:
    escritor = PdfWriter()
    pagina = escritor.add_blank_page(width=600, height=800)
    fuente = DictionaryObject(
        {
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica"),
        }
    )
    pagina[NameObject("/Resources")] = DictionaryObject(
        {NameObject("/Font"): DictionaryObject({NameObject("/F1"): escritor._add_object(fuente)})}
    )
    contenido = DecodedStreamObject()
    contenido.set_data(b"BT /F1 12 Tf 50 750 Td (Explain phenomena scientifically. Use valid evidence.) Tj ET")
    pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


@pytest.fixture
def base(tmp_path, monkeypatch):
    fuente = FuentePublica(
        id="fuente_prueba",
        titulo="Marco de prueba",
        institucion="Institución de prueba",
        version_documental="Edición sintética 2026",
        url_catalogo="https://www.oecd.org/prueba",
        url_documento="https://www.oecd.org/prueba.pdf",
        estado_publicacion="publicado_final",
    )
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (_pdf(), f.url_documento))
    repo = RepositorioReferencias(tmp_path / "referencias")
    registro = repo.incorporar([fuente], descargar=True).referencias[fuente.id]
    criterio = dict(
        id="LOCAL:explicar",
        marco="PISA",
        ciclo="2025",
        version_documental=registro.version_documental,
        fuente=fuente.id,
        sha256=registro.sha256,
        paginas_pdf=[1],
        ancla="Explain phenomena scientifically",
        descripcion="Elaborar explicaciones con apoyo en evidencia científica.",
        eje="practica",
        tipo="competencia",
        padre=None,
        alcance="Población sintética para pruebas; no fija grados.",
        grado_referencia=None,
        edad_referencia=15,
    )
    datos = dict(
        schema_version="1.0",
        meta=dict(
            clasificacion="parafrasis_del_proyecto",
            no_equivalencia="No equivale a un código oficial ni acredita alineación de tareas.",
            fecha_consulta="2026-10-21",
            alcance="Catálogo sintético para pruebas deterministas de procedencia.",
            exhaustividad="por_unidad_no_global",
            paginas="Numeración PDF desde 1 incluida la portada.",
            procedencia="data/referencias_2026/manifest.json",
            documentacion="docs/prueba.md",
            limites=["No permite inferir eficacia educativa."],
            cobertura=[
                dict(
                    fuente=fuente.id,
                    unidad="Competencias de prueba",
                    paginas_pdf=[1],
                    tipo="competencia",
                    padre=None,
                    esperados=1,
                    incluidos=1,
                    estado="completa_en_unidad_declarada",
                    limites="Sólo la unidad declarada, no el marco completo.",
                )
            ],
        ),
        referentes=[criterio],
    )
    return repo, datos


def test_carga_valida_retorna_criterios_y_evidencia_real(base, tmp_path, monkeypatch):
    repo, datos = base
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda _: pytest.fail("Sin red"))
    archivo = tmp_path / "referentes.yaml"
    archivo.write_text(yaml.safe_dump(datos))
    catalogo = cargar_referentes(archivo, repo)
    assert catalogo.por_id["LOCAL:explicar"].edad_referencia == 15
    evidencia = evidencias_referentes(catalogo, repo)["LOCAL:explicar"][0]
    assert evidencia.fuente["verificacion"] == "contenido_fuente"
    assert evidencia.fuente["pagina"] == 1
    resultado = validar_referentes(catalogo, repo)
    assert resultado["total_referentes"] == 1
    assert resultado["referentes"][0]["evidencias"][0]["contiene_ancla"] is True
    assert "No acredita alineación" in resultado["limite"]


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("id", "PISA:codigo_falso"),
        ("paginas_pdf", [True]),
        ("paginas_pdf", [0]),
        ("paginas_pdf", [1, 1]),
        ("ancla", "word " * 21),
        ("edad_referencia", True),
    ],
)
def test_rechaza_codigos_ajenos_y_localizadores_ambiguos(base, campo, valor):
    _, datos = base
    datos["referentes"][0][campo] = valor
    with pytest.raises(ValidationError):
        CatalogoReferentesOperativos.model_validate(datos)


@pytest.mark.parametrize(
    "campo,valor",
    [
        ("sha256", "a" * 64),
        ("version_documental", "Otra edición 2026"),
        ("ancla", "Fabricated scientific statement"),
        ("fuente", "no_ingerida"),
    ],
)
def test_no_confunde_literal_o_edicion_inventados_con_evidencia(base, campo, valor):
    repo, datos = base
    datos["referentes"][0][campo] = valor
    if campo == "fuente":
        datos["meta"]["cobertura"][0][campo] = valor
    catalogo = CatalogoReferentesOperativos.model_validate(datos)
    with pytest.raises(ValueError):
        evidencias_referentes(catalogo, repo)


def test_no_acepta_doble_conteo_ni_exhaustividad_inventada(base):
    _, datos = base
    mutaciones = []
    duplicados = copy.deepcopy(datos)
    duplicados["referentes"].append(copy.deepcopy(duplicados["referentes"][0]))
    mutaciones.append(duplicados)
    doble_unidad = copy.deepcopy(datos)
    doble_unidad["meta"]["cobertura"].append(copy.deepcopy(doble_unidad["meta"]["cobertura"][0]))
    mutaciones.append(doble_unidad)
    falsa_cobertura = copy.deepcopy(datos)
    falsa_cobertura["meta"]["cobertura"][0]["esperados"] = 2
    mutaciones.append(falsa_cobertura)
    for mutacion in mutaciones:
        with pytest.raises(ValidationError):
            CatalogoReferentesOperativos.model_validate(mutacion)


def _con_hijo(datos):
    hijo = copy.deepcopy(datos["referentes"][0])
    hijo.update(id="LOCAL:usar_evidencia", tipo="subcompetencia", padre="LOCAL:explicar")
    datos["referentes"].append(hijo)
    unidad = copy.deepcopy(datos["meta"]["cobertura"][0])
    unidad.update(tipo="subcompetencia", padre="LOCAL:explicar", unidad="Desempeños de la competencia")
    datos["meta"]["cobertura"].append(unidad)
    return hijo


@pytest.mark.parametrize(
    "cambio",
    [{"padre": None}, {"padre": "LOCAL:ausente"}, {"marco": "ERCE"}, {"edad_referencia": 12}],
)
def test_hierarquia_no_admite_padres_ausentes_o_de_otro_marco(base, cambio):
    _, datos = base
    _con_hijo(datos).update(cambio)
    with pytest.raises(ValidationError):
        CatalogoReferentesOperativos.model_validate(datos)


def test_cada_subcompetencia_tiene_padre_real(base):
    _, datos = base
    hijo = _con_hijo(datos)
    catalogo = CatalogoReferentesOperativos.model_validate(datos)
    assert catalogo.por_id[hijo["padre"]].tipo == "competencia"


def test_pdf_mutado_no_conserva_procedencia(base):
    repo, datos = base
    catalogo = CatalogoReferentesOperativos.model_validate(datos)
    assert evidencias_referentes(catalogo, repo)
    registro = repo.manifiesto().referencias["fuente_prueba"]
    (repo.raiz / registro.archivo_pdf).write_bytes(b"fuente sustituida")
    # El puerto de página puede traducir el error de integridad a "no verificable";
    # nunca debe conservar evidencia anterior después de sustituir los bytes.
    with pytest.raises(ValueError):
        evidencias_referentes(CatalogoReferentesOperativos.model_validate(datos), repo)
