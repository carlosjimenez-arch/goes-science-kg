"""Indicadores: ámbitos, literales, estados, agrupación y archivos reproducibles."""

from __future__ import annotations

import csv
import io
import json
import posixpath
import re
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from goes_science_kg.api_indicadores import crear_router_indicadores
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.indicadores.compilacion import (
    COMPLETO,
    PENDIENTE,
    codigo_literal,
    compilar,
)
from goes_science_kg.produccion.indicadores.exportacion import catalogo_csv, zip_verificable

BASE = Path(__file__).resolve().parents[1]


def padre(id_, texto, *, grado=3, unidad="Unidad 2", pendiente=False, completado=False):
    edicion = {
        "indicador": texto or "Efectúa experimentos con mezclas.",
        "completacion": {"original_intacto": True} if completado else None,
    }
    estado = "revision_automatica_con_pendientes" if pendiente else "revision_automatica_completa"
    return {
        "id": id_,
        "tipo": "paquete_objetivo",
        "grados": [grado],
        "asignatura": "Ciencias",
        "unidad": unidad,
        "estado": estado,
        "documento": {
            "version_contenido": "preparacion-malla-final-3",
            "snapshot_id": "s",
            "original": {"indicadores_logro": texto, "grado": grado, "asignatura_malla": "Ciencias", "unidad": unidad},
            "edicion_docente": edicion,
            "estado_revision": estado,
            "revision_docente": {"edicion_sha256": sha(serializar(edicion)), "estado": estado},
            "fuente_original": {"archivo_local": "insumos/final.xlsx", "sha256": "a" * 64},
        },
    }


def agrupar(rs):
    return compilar(rs, biblioteca_id="b", snapshot_id="s")


@pytest.mark.parametrize(
    "texto,codigo",
    [
        ("4.9. Calcula pH 7.4", "4.9"),
        ("23. Ejemplifica trabajo.", "23"),
        ("Sin código, retoma (2.8).", None),
        ("1.6. Interpreta.\nDemuestra.", "1.6"),
        (" 10.15. Compara.", "10.15"),
        ("", None),
    ],
)
def test_el_codigo_es_literal_y_no_una_cifra_en_el_enunciado(texto, codigo):
    assert codigo_literal(texto) == codigo


def test_agrupa_duplicados_exactos_solo_dentro_del_ambito_y_no_promueve_pendientes():
    rs = [
        padre("a", "2.5. Separa mezclas."),
        padre("b", "2.5. Separa mezclas.", pendiente=True),
        padre("c", "2.5. Separa mezclas.", grado=4),
        padre("d", "2.5. Separa mezclas.", unidad="Unidad 3"),
    ]
    antes = deepcopy(rs)
    paquetes, indice, informe = agrupar(rs)
    assert len(paquetes) == 3 and informe["filas_cubiertas"] == 4
    grupo = next(p for p in paquetes if len(p["documento"]["preparaciones"]) == 2)
    assert grupo["estado"] == PENDIENTE
    assert grupo["documento"]["revision"]["preparaciones_pendientes"] == ["b"]
    assert all(i["estado_reagrupamiento"] == "sin_revision_especifica" for i in indice)
    assert rs == antes
    assert set(i for p in paquetes for i in [r["id"] for r in p["documento"]["preparaciones"]]) == {"a", "b", "c", "d"}
    assert agrupar(list(reversed(rs))) == (paquetes, indice, informe)


def test_mismo_codigo_con_texto_distinto_y_enunciados_compuestos_no_se_fusionan():
    rs = [
        padre("a", "3.12. Explica magnetismo."),
        padre("b", "3.12. Explica seguridad."),
        padre("c", "Identifica aparatos.\nReconoce fuentes."),
    ]
    paquetes, indice, informe = agrupar(rs)
    assert len(paquetes) == 3 and len(informe["codigos_ambiguos"]) == 1
    assert sum(i["colision_codigo"] for i in indice) == 2
    assert informe["celdas_compuestas_conservadas"] == ["c"]
    assert (
        next(i for i in indice if i["codigo"] is None)["indicador"]
        == rs[2]["documento"]["original"]["indicadores_logro"]
    )


def test_completacion_permanece_derivada_sin_asignar_codigo_inventado():
    r = padre("a", "", completado=True)
    paquetes, indice, informe = agrupar([r])
    assert indice[0]["origen"] == "completacion_derivada" and indice[0]["codigo"] is None
    assert paquetes[0]["documento"]["preparaciones"][0]["documento"]["original"]["indicadores_logro"] == ""
    assert informe["originales_modificados"] == informe["llamadas_modelos"] == 0
    assert paquetes[0]["estado"] == COMPLETO
    with pytest.raises(ValueError, match="completación"):
        agrupar([padre("b", "")])


@pytest.mark.parametrize("cambio", ["snapshot", "hash", "estado", "ambito"])
def test_rechaza_contextos_que_no_conservan_procedencia_y_estado(cambio):
    r = padre("a", "2.5. Separa.")
    if cambio == "snapshot":
        r["documento"]["snapshot_id"] = "otra"
    elif cambio == "hash":
        r["documento"]["edicion_docente"]["indicador"] = "Cambio sin relectura"
    elif cambio == "estado":
        r["estado"] = "aprobado"
    else:
        r["grados"] = [4]
    with pytest.raises(ValueError):
        agrupar([r])


def test_zip_reproducible_y_rutas_acotadas():
    archivos = {"LEEME.md": b"# Guia", "indicador.json": b"{}"}
    a = zip_verificable(archivos, {"version": "test"})
    assert a == zip_verificable(dict(reversed(list(archivos.items()))), {"version": "test"})
    with ZipFile(io.BytesIO(a)) as z:
        m = json.loads(z.read("manifest.json"))
        assert set(z.namelist()) == set(m["archivos"]) | {"manifest.json"}
        assert m["archivos"]["LEEME.md"]["sha256"] == sha(archivos["LEEME.md"])
    for ruta in ("../fuera", "/fuera", ".env", "a/../fuera"):
        with pytest.raises(ValueError):
            zip_verificable({ruta: b"prohibido"}, {})


def test_csv_no_ejecuta_formulas_y_conserva_literales_en_la_vista_json():
    i = {
        "id": "indicador",
        "indicador": "=1+1",
        "filas_ids": ["a"],
        "zip_individual": {"sha256": "b" * 64, "bytes": 20},
    }
    fila = next(csv.DictReader(io.StringIO(catalogo_csv([i]).decode("utf-8-sig"))))
    assert fila["indicador"] == "'=1+1"
    assert i["indicador"] == "=1+1"


@pytest.fixture(scope="module")
def real():
    p = BASE / "data/materiales_indicadores_v4"
    if not p.exists():
        pytest.skip("Restaurar la biblioteca por indicadores para verificar los artefactos reales")
    b = Biblioteca(p)
    rs, fs = b.exportar()
    origen = Biblioteca(BASE / "data/materiales_produccion_v4")
    padres, _ = origen.exportar()
    return b, rs, fs, origen, {p["id"]: p for p in padres if p["tipo"] == "paquete_objetivo"}


def test_entrega_real_cubre_todas_las_filas_sin_cambiar_originales_ni_lecturas(real):
    b, rs, fs, origen, padres = real
    assert b.manifest["materiales"] == 1019 and len(padres) == 1020
    assert b.manifest["procedencia"]["biblioteca_preparaciones_id"] == origen.manifest["id"]
    cubiertas = []
    for r in rs:
        d = r["documento"]
        assert d["revision"]["estado_reagrupamiento"] == "sin_revision_especifica"
        completo = all(p["estado"] == "revision_automatica_completa" for p in d["preparaciones"])
        assert (r["estado"] == COMPLETO) == completo
        for p in d["preparaciones"]:
            assert p == padres[p["id"]]
            cubiertas.append(p["id"])
    assert len(cubiertas) == len(set(cubiertas)) == 1020 and set(cubiertas) == set(padres)
    a = json.loads(fs["indicadores/auditoria.json"])
    assert a["por_estado_contextos"] == {COMPLETO: 1011, PENDIENTE: 8}
    assert len(a["codigos_ambiguos"]) == 8 and len(a["celdas_compuestas_conservadas"]) == 3
    assert a["por_origen"] == {"malla_final": 1018, "completacion_derivada": 1}
    # Sesenta indicadores de 2.º y la completación de 3.º no tienen prefijo numérico.
    # Una referencia interna como "(2.8)" no asigna código al indicador.
    assert a["sin_codigo_en_texto"] == 61
    for nombre, ref in b.manifest["originales"].items():
        if nombre.endswith(".xlsx"):
            assert origen.manifest["originales"][nombre] == ref


def comprobar_zip(raw):
    with ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None
        m = json.loads(z.read("manifest.json"))
        assert set(z.namelist()) == set(m["archivos"]) | {"manifest.json"}
        for nombre, ref in m["archivos"].items():
            contenido = z.read(nombre)
            assert ref == {"sha256": sha(contenido), "bytes": len(contenido)}
        return m


def test_zip_individuales_y_colecciones_tienen_contenido_completo_y_enlaces_validos(real):
    _, rs, fs, _, _ = real
    indice = json.loads(fs["indicadores/indice.json"])["indicadores"]
    por_id = {r["id"]: r for r in rs}
    for i in indice:
        ref = i["zip_individual"]
        raw = fs[ref["ruta"]]
        assert (sha(raw), len(raw)) == (ref["sha256"], ref["bytes"])
        m = comprobar_zip(raw)
        assert m["indicador_id"] == i["id"]
        with ZipFile(io.BytesIO(raw)) as z:
            assert json.loads(z.read("indicador.json"))["documento"] == por_id[i["id"]]["documento"]
            assert "no tiene revisión específica" in z.read("LEEME.md").decode()
    colecciones = json.loads(fs["paquetes/indice.json"])["paquetes"]
    assert len(colecciones) == 14 and sum(c["paquetes"] for c in colecciones) == 1019
    ids = []
    for c in colecciones:
        raw = fs["paquetes/" + c["archivo"]]
        assert sha(raw) == c["sha256"]
        comprobar_zip(raw)
        with ZipFile(io.BytesIO(raw)) as z:
            items = json.loads(z.read("indice.json"))["indicadores"]
            ids.extend(i["id"] for i in items)
            for enlace in re.findall(r"\]\(([^)]+)\)", z.read("LEEME.md").decode()):
                assert posixpath.normpath(enlace) in z.namelist()
            assert all(z.read(i["zip_individual"]["ruta"]) == fs[i["zip_individual"]["ruta"]] for i in items)
    assert len(ids) == len(set(ids)) == 1019


def test_api_real_indicadores_filtra_colisiones_y_descarga_zip_csv_json_y_md(real):
    b, _, fs, _, _ = real
    app = FastAPI()
    app.include_router(crear_router_indicadores(BASE))
    c = TestClient(app)
    pref = "/api/v4/produccion/indicadores"
    assert c.get(pref + "/salud").json()["biblioteca_id"] == b.manifest["id"]
    assert c.get(pref + "/indice").json()["total"] == 1019
    repetidos = c.get(pref + "/indice", params={"codigo": "3.12", "grado": 6}).json()
    assert repetidos["total"] == 2 and all(i["colision_codigo"] for i in repetidos["indicadores"])
    assert len({i["id"] for i in repetidos["indicadores"]}) == 2
    derivado = c.get(pref + "/indice", params={"origen": "completacion_derivada"}).json()
    assert derivado["total"] == 1
    i = derivado["indicadores"][0]
    assert c.get(pref + "/indice", params={"fila_id": i["filas_ids"][0]}).json()["total"] == 1
    for formato in ("json", "md", "zip"):
        r = c.get(pref + "/descarga/" + i["id"], params={"formato": formato})
        assert r.status_code == 200
        if formato == "zip":
            assert r.content == fs[i["zip_individual"]["ruta"]]
            assert r.headers["etag"] == '"' + i["zip_individual"]["sha256"] + '"'
    assert len(list(csv.DictReader(io.StringIO(c.get(pref + "/catalogo.csv").content.decode("utf-8-sig"))))) == 1019
    assert c.get(pref + "/indice", params={"estado_contextos": PENDIENTE}).json()["total"] == 8
    for consulta in ("?grado=1", "?limite=999", "?offset=-1", "?origen=otro", "?estado_contextos=aprobado"):
        assert c.get(pref + "/indice" + consulta).status_code == 422
    assert c.get(pref + "/indice", params={"codigo": "' OR 1=1 --"}).json()["total"] == 0
    assert c.get(pref + "/descarga/desconocido?formato=zip").status_code == 404
