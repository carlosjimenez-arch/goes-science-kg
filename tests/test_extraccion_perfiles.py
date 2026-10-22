"""Perfiles sobre la edición ERCE real; sin red y sin reescribir su extracción original."""

import re
import shutil

import pytest
from pydantic import ValidationError

from goes_science_kg.config import ruta
from goes_science_kg.ingesta.extraccion import (
    CatalogoPerfilesPDF,
    PaginasConPerfil,
    PerfilPaginaPDF,
    RegionPDF,
    cargar_perfiles,
)
from goes_science_kg.ingesta.referencias import ManifiestoReferencias, RepositorioReferencias

FUENTE = "erce_2019_reporte_tecnico_2025"


@pytest.fixture(scope="module")
def originales():
    return RepositorioReferencias(ruta("data/referencias_2026")), cargar_perfiles(
        ruta("config/extraccion_referencias_2026.yaml")
    )


def test_regiones_recuperan_glifos_y_orden_sin_cambiar_el_raw(originales):
    repo, perfiles = originales
    manifest = repo.archivo_manifest.read_bytes()
    raw = repo.pagina(FUENTE, 11)
    assert "/f_i" in raw.texto or ".oldstyle" in raw.texto
    paginas = PaginasConPerfil(repo, perfiles)
    izquierda_derecha = paginas.pagina(FUENTE, 11)
    tabla = paginas.pagina(FUENTE, 19)
    assert not re.search(r"/(?:[a-z]_[a-z]+|[a-z]+\.oldstyle)\b", izquierda_derecha.texto + tabla.texto)
    assert "Aprendizajes evaluados en Ciencias" in izquierda_derecha.texto
    assert "Tabla 2.9." in tabla.texto
    assert "Energía" in izquierda_derecha.texto
    assert len(izquierda_derecha.fuente["regiones"]) == 4
    assert izquierda_derecha.id != raw.id and izquierda_derecha.huella != raw.huella
    assert izquierda_derecha.fuente["sha256"] == raw.fuente["sha256"]
    assert izquierda_derecha.fuente["verificacion"] == "contenido_fuente"
    assert repo.archivo_manifest.read_bytes() == manifest
    assert repo.pagina(FUENTE, 11).texto == raw.texto


def test_sin_perfil_se_conserva_identidad_y_extraccion_original(originales):
    repo, perfiles = originales
    envuelto = PaginasConPerfil(repo, perfiles)
    assert envuelto.pagina("pisa_2025_marco_final", 34) == repo.pagina("pisa_2025_marco_final", 34)


def test_cambiar_orden_del_perfil_cambia_huella_y_no_reutiliza_otra_vista(originales):
    repo, perfiles = originales
    p = perfiles.perfiles[0]
    otro = CatalogoPerfilesPDF(
        schema_version="1.0", perfiles=(p.model_copy(update={"regiones": tuple(reversed(p.regiones))}),)
    )
    primero = PaginasConPerfil(repo, perfiles)
    segundo = PaginasConPerfil(repo, otro)
    assert primero.huella_extraccion != segundo.huella_extraccion
    assert primero.pagina(FUENTE, 11).huella != segundo.pagina(FUENTE, 11).huella


def test_cache_no_encubre_mutacion_del_pdf_y_no_se_expone_mutable(originales, tmp_path):
    repo, perfiles = originales
    registro = repo.manifiesto().referencias[FUENTE]
    copia = RepositorioReferencias(tmp_path / "referencias")
    destino = copia.raiz / registro.archivo_pdf
    destino.parent.mkdir(parents=True)
    shutil.copyfile(repo.raiz / registro.archivo_pdf, destino)
    copia.archivo_manifest.write_text(ManifiestoReferencias(referencias={FUENTE: registro}).model_dump_json())
    paginas = PaginasConPerfil(copia, perfiles)
    uno = paginas.pagina(FUENTE, 11)
    uno.fuente["perfil_id"] = "mutacion-del-consumidor"
    assert paginas.pagina(FUENTE, 11).fuente["perfil_id"] != "mutacion-del-consumidor"
    destino.write_bytes(b"Alteracion de la fuente")
    with pytest.raises(ValueError, match="Integridad"):
        paginas.pagina(FUENTE, 11)


@pytest.mark.parametrize("bbox", [(0, 0, 0, 20), (0, 0, 20, -1), (False, 0, 20, 30), (0, 0, float('nan'), 20)])
def test_coordenadas_no_ambiguas_o_no_finitas_no_forman_un_perfil(bbox):
    with pytest.raises(ValidationError):
        RegionPDF(id="LOCAL:region", bbox=bbox)


def test_regiones_solapadas_y_perfiles_duplicados_son_invalidos(originales):
    _, perfiles = originales
    p = perfiles.perfiles[0]
    with pytest.raises(ValidationError):
        PerfilPaginaPDF.model_validate(p.model_dump() | {"regiones": [p.regiones[0], p.regiones[0]]})
    with pytest.raises(ValidationError):
        CatalogoPerfilesPDF(schema_version="1.0", perfiles=(p, p))


@pytest.mark.parametrize("campo,valor", [("sha256", "0" * 64), ("pagina_pdf", 999)])
def test_perfil_requiere_la_edicion_y_pagina_fijadas(originales, campo, valor):
    repo, perfiles = originales
    p = perfiles.perfiles[0].model_copy(update={campo: valor})
    with pytest.raises(ValueError):
        PaginasConPerfil(repo, CatalogoPerfilesPDF(schema_version="1.0", perfiles=(p,)))


def test_region_fuera_de_la_pagina_se_rechaza_al_leer(originales):
    repo, perfiles = originales
    p = perfiles.perfiles[0].model_copy(update={
        "regiones": (RegionPDF(id="LOCAL:fuera", bbox=(0, 0, 1000, 1000)),)
    })
    paginas = PaginasConPerfil(repo, CatalogoPerfilesPDF(schema_version="1.0", perfiles=(p,)))
    with pytest.raises(ValueError, match="dimensiones"):
        paginas.pagina(FUENTE, 11)
