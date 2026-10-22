"""Colecciones documentales separadas y exportación protegida, sin red ni modelos."""

from __future__ import annotations

import json
from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from typer.testing import CliRunner

from goes_science_kg.archivos import PROTEGIDAS, destino_generado
from goes_science_kg.cli import app
from goes_science_kg.cli import referencias as cli_referencias
from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias

RUNNER = CliRunner()
RUTA = ["investigacion", "referencias"]
COMANDOS = (("estado",), ("ingerir", "fuente_comun"), ("buscar", "evidence"), ("pagina", "fuente_comun", "1"))


def _pdf(texto):
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
    contenido.set_data(f"BT /F1 12 Tf 50 750 Td ({texto}) Tj ET".encode("ascii"))
    pagina[NameObject("/Contents")] = escritor._add_object(contenido)
    salida = BytesIO()
    escritor.write(salida)
    return salida.getvalue()


@pytest.fixture
def colecciones(tmp_path, monkeypatch):
    """Un mismo ID con contenidos distintos demuestra aislamiento real entre repositorios."""
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    repositorios = {}
    catalogos = {}
    for coleccion, directorio, marca in (
        ("evaluacion", "data/referencias_2026", "Evaluation"),
        ("paises", "data/referencias_paises_2026", "Country"),
        ("cientificas", "data/referencias_cientificas_2026", "Scientific"),
        ("progresiones", "data/referencias_progresiones_2026", "Progression"),
    ):
        fuente = FuentePublica(
            id="fuente_comun",
            titulo=f"{marca} source",
            institucion="Institución sintética",
            version_documental=f"{marca} 2026",
            url_catalogo=f"https://www.gov.uk/{coleccion}",
            url_documento=f"https://assets.publishing.service.gov.uk/{coleccion}.pdf",
            estado_publicacion="publicado_final",
        )
        pdf = _pdf(f"{marca} source evidence.")
        monkeypatch.setattr(
            "goes_science_kg.ingesta.referencias.descargar_pdf", lambda f, contenido=pdf: (contenido, f.url_documento)
        )
        repositorio = RepositorioReferencias(tmp_path / directorio)
        repositorio.incorporar([fuente], descargar=True)
        repositorios[coleccion] = repositorio
        nombre_catalogo = {
            "evaluacion": "referentes_2026",
            "paises": "curriculos_paises_2026",
            "cientificas": "fuentes_cientificas_2026",
            "progresiones": "progresiones_2026",
        }[coleccion]
        catalogos[nombre_catalogo] = {
            "fuentes": {
                fuente.id: {
                    "titulo": fuente.titulo,
                    "institucion": fuente.institucion,
                    "version": fuente.version_documental,
                    "url": fuente.url_catalogo,
                    "url_documento": fuente.url_documento,
                    "estado_publicacion": fuente.estado_publicacion,
                }
            }
        }
        if coleccion == "paises":
            catalogos["curriculos_paises_2026"]["fuentes"][fuente.id]["sha256_verificado"] = (
                repositorio.manifiesto().referencias[fuente.id].sha256
            )
    catalogos_leidos = []
    llamadas_default = []

    def cargar(nombre):
        catalogos_leidos.append(nombre)
        return catalogos[nombre]

    def repositorio_default():
        llamadas_default.append("sin_argumentos")
        return repositorios["evaluacion"]

    def prohibir(*args, **kwargs):
        pytest.fail("Las pruebas locales no admiten red ni modelos remotos")

    monkeypatch.setattr(cli_referencias, "cargar", cargar)
    monkeypatch.setattr(cli_referencias, "_repositorio", repositorio_default)
    monkeypatch.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", prohibir)
    monkeypatch.setattr("goes_science_kg.motor.vertex.Vertex", prohibir)
    estado_inicial = {
        str(p): p.read_bytes()
        for repositorio in repositorios.values()
        for p in repositorio.raiz.rglob("*")
        if p.is_file()
    }
    return SimpleNamespace(
        base=tmp_path,
        repositorios=repositorios,
        catalogos_leidos=catalogos_leidos,
        llamadas_default=llamadas_default,
        estado_inicial=estado_inicial,
    )


def _sin_mutar_fuentes(colecciones):
    actuales = {
        str(p): p.read_bytes()
        for repositorio in colecciones.repositorios.values()
        for p in repositorio.raiz.rglob("*")
        if p.is_file()
    }
    assert actuales == colecciones.estado_inicial


@pytest.mark.parametrize("comando", COMANDOS, ids=lambda c: c[0])
@pytest.mark.parametrize("coleccion", [None, "evaluacion", "paises", "cientificas", "progresiones"])
def test_cada_comando_selecciona_solo_su_catalogo_y_repositorio(colecciones, comando, coleccion):
    opciones = [] if coleccion is None else ["--coleccion", coleccion]
    resultado = RUNNER.invoke(app, [*RUTA, *comando, *opciones])
    assert resultado.exit_code == 0, resultado.output
    marcas = {
        "evaluacion": "Evaluation",
        "paises": "Country",
        "cientificas": "Scientific",
        "progresiones": "Progression",
    }
    elegida = coleccion or "evaluacion"
    assert marcas[elegida] in resultado.stdout
    assert all(m not in resultado.stdout for c, m in marcas.items() if c != elegida)
    assert colecciones.llamadas_default == (["sin_argumentos"] if elegida == "evaluacion" else [])
    nombres_catalogo = {
        "evaluacion": "referentes_2026",
        "paises": "curriculos_paises_2026",
        "cientificas": "fuentes_cientificas_2026",
        "progresiones": "progresiones_2026",
    }
    assert colecciones.catalogos_leidos == ([nombres_catalogo[elegida]] if comando[0] == "ingerir" else [])
    if comando[0] == "pagina":
        evidencia = json.loads(resultado.stdout)
        registro = colecciones.repositorios[coleccion or "evaluacion"].manifiesto().referencias["fuente_comun"]
        assert evidencia["fuente"]["sha256"] == registro.sha256 and evidencia["fuente"]["pagina"] == 1
    _sin_mutar_fuentes(colecciones)


@pytest.mark.parametrize("comando", COMANDOS, ids=lambda c: c[0])
def test_ayuda_colecciones_no_carga_catalogos_ni_repositorios(colecciones, monkeypatch, comando):
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: pytest.fail("Ayuda sin repositorio"))
    resultado = RUNNER.invoke(app, [*RUTA, comando[0], "--help"])
    assert resultado.exit_code == 0 and "--coleccion" in resultado.stdout
    assert "evaluacion" in resultado.stdout and "paises" in resultado.stdout
    assert not colecciones.catalogos_leidos


@pytest.mark.parametrize("comando", COMANDOS, ids=lambda c: c[0])
@pytest.mark.parametrize("nombre", ["desconocida", "PAISES", "../evaluacion"])
def test_coleccion_invalida_es_rechazada_por_parser_antes_de_io(colecciones, monkeypatch, comando, nombre):
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: pytest.fail("Colección inválida antes de IO"))
    resultado = RUNNER.invoke(app, [*RUTA, *comando, "--coleccion", nombre])
    assert resultado.exit_code == 2 and "Invalid value" in resultado.output
    assert not colecciones.catalogos_leidos and not colecciones.llamadas_default
    _sin_mutar_fuentes(colecciones)


def test_coleccion_desconocida_no_cae_silenciosamente_en_paises(colecciones):
    with pytest.raises(ValueError, match="desconocida"):
        cli_referencias._coleccion("desconocida")
    assert not colecciones.llamadas_default


@pytest.mark.parametrize("coleccion", ["evaluacion", "paises"])
def test_ingerir_pasa_solo_huellas_de_seleccion_y_preserva_firma_antigua(colecciones, monkeypatch, coleccion):
    llamadas = []
    manifiesto = colecciones.repositorios[coleccion].manifiesto()

    def incorporar(fuentes, *, descargar=False, **opciones):
        llamadas.append(([f.id for f in fuentes], descargar, opciones))
        return manifiesto

    original = cli_referencias.cargar

    def cargar_con_otra_fuente(nombre):
        datos = original(nombre)
        return {"fuentes": datos["fuentes"] | {"no_seleccionada": {"sha256_verificado": "d" * 64}}}

    monkeypatch.setattr(cli_referencias, "cargar", cargar_con_otra_fuente)
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: SimpleNamespace(incorporar=incorporar))
    resultado = RUNNER.invoke(app, [*RUTA, "ingerir", "fuente_comun", "--coleccion", coleccion, "--descargar"])
    assert resultado.exit_code == 0, resultado.output
    esperado = (
        {"sha256_esperados": {"fuente_comun": manifiesto.referencias["fuente_comun"].sha256}}
        if coleccion == "paises"
        else {}
    )
    assert llamadas == [(["fuente_comun"], True, esperado)]
    _sin_mutar_fuentes(colecciones)


@pytest.mark.parametrize("sha", ["d" * 64, "no_es_sha256", None])
def test_ingerir_rechaza_edicion_o_huella_invalida_sin_descargar_ni_mutar(colecciones, monkeypatch, sha):
    original = cli_referencias.cargar

    def cargar_con_sha(nombre):
        datos = original(nombre)
        fuente = datos["fuentes"]["fuente_comun"] | {"sha256_verificado": sha}
        return {"fuentes": {"fuente_comun": fuente}}

    monkeypatch.setattr(cli_referencias, "cargar", cargar_con_sha)
    resultado = RUNNER.invoke(app, [*RUTA, "ingerir", "fuente_comun", "--coleccion", "paises"])
    assert resultado.exit_code == 2 and ("esperada" in resultado.output or "SHA-256" in resultado.output)
    _sin_mutar_fuentes(colecciones)


@pytest.mark.parametrize("protegida", PROTEGIDAS)
@pytest.mark.parametrize("coleccion", ["evaluacion", "paises"])
def test_pagina_rechaza_todas_raices_protegidas_antes_de_hidratar(colecciones, monkeypatch, protegida, coleccion):
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: pytest.fail("Salida inválida antes de hidratar"))
    salida = colecciones.base / protegida / "evidencia_nueva.json"
    resultado = RUNNER.invoke(
        app, [*RUTA, "pagina", "fuente_comun", "1", "--coleccion", coleccion, "--salida", str(salida)]
    )
    assert resultado.exit_code == 2 and "fuera de originales" in resultado.output
    assert not salida.exists()
    _sin_mutar_fuentes(colecciones)


@pytest.mark.parametrize("nombre", [".env", ".envrc", "pyproject.toml", "uv.lock", "evidencia.md"])
def test_pagina_rechaza_archivos_reservados_y_extension_antes_de_hidratar(colecciones, monkeypatch, nombre):
    salida = colecciones.base / nombre
    salida.write_text("conservar", encoding="utf-8")
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: pytest.fail("Destino inválido antes de IO"))
    resultado = RUNNER.invoke(app, [*RUTA, "pagina", "fuente_comun", "1", "--salida", str(salida)])
    assert resultado.exit_code == 2 and salida.read_text(encoding="utf-8") == "conservar"


@pytest.mark.parametrize("tipo", ["archivo_enlazado", "directorio_enlazado_protegido", "directorio_como_archivo"])
def test_pagina_rechaza_enlaces_o_directorio_antes_de_repositorio(colecciones, monkeypatch, tipo):
    salida = colecciones.base / "evidencia.json"
    fuente = colecciones.base / "conservar.json"
    fuente.write_text('{"conservar": true}', encoding="utf-8")
    if tipo == "archivo_enlazado":
        salida.symlink_to(fuente)
    elif tipo == "directorio_enlazado_protegido":
        alias = colecciones.base / "alias"
        alias.symlink_to(colecciones.repositorios["paises"].raiz, target_is_directory=True)
        salida = alias / "evidencia.json"
    else:
        salida.mkdir()
    monkeypatch.setattr(cli_referencias, "_coleccion", lambda nombre: pytest.fail("Salida inválida antes de IO"))
    resultado = RUNNER.invoke(app, [*RUTA, "pagina", "fuente_comun", "1", "--salida", str(salida)])
    assert resultado.exit_code == 2 and fuente.read_text(encoding="utf-8") == '{"conservar": true}'
    _sin_mutar_fuentes(colecciones)


def test_repositorio_default_personalizado_sigue_protegido_sin_cambiar_firma(colecciones, monkeypatch):
    raiz = colecciones.base / "almacen_personalizado"
    repositorio = SimpleNamespace(raiz=raiz, pagina=lambda *a: pytest.fail("No hidratar dentro del almacén"))
    monkeypatch.setattr(cli_referencias, "_repositorio", lambda: repositorio)
    salida = raiz / "evidencia.json"
    resultado = RUNNER.invoke(app, [*RUTA, "pagina", "fuente_comun", "1", "--salida", str(salida)])
    assert resultado.exit_code == 2 and "fuera del almacén" in resultado.output
    assert not raiz.exists()


@pytest.mark.parametrize("coleccion", ["evaluacion", "paises"])
def test_pagina_guarda_json_completo_en_salida_local_sin_mutar_almacenes(colecciones, coleccion):
    salida = colecciones.base / "derivados/evidencia.json"
    resultado = RUNNER.invoke(
        app, [*RUTA, "pagina", "fuente_comun", "1", "--coleccion", coleccion, "--salida", str(salida)]
    )
    assert resultado.exit_code == 0 and resultado.stdout.strip() == str(salida.resolve())
    evidencia = json.loads(salida.read_text(encoding="utf-8"))
    marca = "Country" if coleccion == "paises" else "Evaluation"
    assert marca in evidencia["texto"] and evidencia["fuente"]["verificacion"] == "contenido_fuente"
    assert evidencia["version"] == "referencia" and evidencia["fuente"]["pagina"] == 1
    assert not list(salida.parent.glob("*.tmp"))
    _sin_mutar_fuentes(colecciones)


@pytest.mark.parametrize("argumentos", [("desconocida", "1"), ("fuente_comun", "2")])
def test_error_fuente_o_pagina_no_sustituye_resultado_previo(colecciones, argumentos):
    salida = colecciones.base / "evidencia.json"
    salida.write_text('{"previo": true}', encoding="utf-8")
    resultado = RUNNER.invoke(app, [*RUTA, "pagina", *argumentos, "--salida", str(salida)])
    assert resultado.exit_code == 2 and salida.read_text(encoding="utf-8") == '{"previo": true}'
    _sin_mutar_fuentes(colecciones)


def test_salida_se_revalida_si_cambia_a_enlace_durante_hidratacion(colecciones, monkeypatch):
    salida = colecciones.base / "evidencia.json"
    protegido = colecciones.base / "conservar.json"
    protegido.write_text('{"original": true}', encoding="utf-8")
    real = colecciones.repositorios["evaluacion"]
    evidencia = real.pagina("fuente_comun", 1)

    def hidratar(*args):
        salida.symlink_to(protegido)
        return evidencia

    monkeypatch.setattr(cli_referencias, "_repositorio", lambda: SimpleNamespace(raiz=real.raiz, pagina=hidratar))
    resultado = RUNNER.invoke(app, [*RUTA, "pagina", "fuente_comun", "1", "--salida", str(salida)])
    assert resultado.exit_code == 2 and protegido.read_text(encoding="utf-8") == '{"original": true}'


def test_helper_compartido_protege_ambos_almacenes(colecciones):
    for repositorio in colecciones.repositorios.values():
        with pytest.raises(ValueError, match="fuera de originales"):
            destino_generado(repositorio.raiz / "salida.json", raiz=colecciones.base)
