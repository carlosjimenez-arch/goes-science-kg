"""Cobertura del corpus completo, grafo didáctico y consultas de la edición mejorada."""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from shutil import copy2

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_didactica_ciencias import CASOS
from test_didactica_ciencias import nueva_entrega as nueva_entrega

from goes_science_kg.api_didactica import crear_router_didactica
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.produccion.compilacion import exportar
from goes_science_kg.produccion.didactica.contratos import DisenoDidactico


def test_todas_las_tareas_criterios_definiciones_y_unidades_tienen_origen(nueva_entrega):
    b, rs, fs = nueva_entrega
    c = Curriculo.model_validate_json(fs["curriculo.json"])
    filas = {f.id: f for f in c.filas}
    fuentes = {s.id: s for s in c.fuentes}
    hojas = {(h.fuente_id, h.nombre): h for h in c.hojas}
    indice = json.loads(fs["didactica/indice.json"])
    assert {f["fila_id"] for f in indice["filas"]} == set(filas)
    total_tareas = total_criterios = casos = 0
    for r in rs:
        d = r["documento"]
        assert d["revisiones"] == [] and d["propuesta"] is None
        assert d["estado_revision"] == "propuesta_didactica_pendiente_revision"
        if r["tipo"] == "paquete_unidad":
            assert d["didactica_unidad"]["desempenos_observados"] is None
            for _codigo, pasos in d["didactica_unidad"]["ruta_por_habilidad"].items():
                assert all(p["fila_id"] in d["filas_ids"] and p["tarea_ids"] for p in pasos)
            continue
        original, f = filas[r["id"]], DisenoDidactico.model_validate(d["didactica"])
        assert d["original"] == original.model_dump(mode="json")
        assert f.objetivo_original == original.procedimental
        assert (f.indicador_original, f.producto_original) == (
            original.indicadores_logro,
            original.evidencia_aprendizaje,
        )
        total_tareas += len(f.tareas)
        total_criterios += len(f.criterios)
        casos += f.caso_resuelto is not None
        for t in f.tareas:
            assert t.origen.sha256 == fuentes[original.fuente_id].sha256
            assert t.origen.hoja == original.hoja
            celda = next(x for x in original.celdas if x.coordenada == t.origen.celdas[0])
            assert t.actividad_literal in str(celda.valor)
            assert celda.campo == "fase_" + t.fase
            if t.definicion:
                o = t.definicion.origen
                assert o.fuente_id == original.fuente_id
                aux = hojas[(o.fuente_id, o.hoja)]
                valores = {x.coordenada: x.valor for row in aux.registros for x in row.celdas}
                assert [valores[x] for x in o.celdas] == [
                    t.codigo,
                    t.definicion.competencia_declarada,
                    t.definicion.nombre,
                    t.definicion.contextualizacion_original,
                ]
        for criterio in f.criterios:
            assert criterio.logro_observado is criterio.respuesta_observada is None
        if f.caso_resuelto:
            assert f.caso_resuelto["fila_id"] == original.id
            assert f.caso_resuelto["huella_curriculo"] == c.huella
            assert all(s["estado"] == "descargado" for s in f.caso_resuelto["fuentes"].values())
    assert (total_tareas, total_criterios, casos) == (4880, 4457, 14)
    assert b.manifest["procedencia"]["consumo_acumulado"]["llamadas"] == 3941


def test_grafo_sin_duplicados_extremos_fantasma_ni_dominio_observado(nueva_entrega):
    _, _, fs = nueva_entrega
    g = json.loads(fs["didactica/grafo.json"])
    nodos = {n["id"]: n for n in g["nodos"]}
    assert len(nodos) == len(g["nodos"])
    aristas = [(a["origen"], a["destino"], a["tipo"]) for a in g["aristas"]]
    assert len(set(aristas)) == len(aristas)
    assert all(a in nodos and b in nodos for a, b, _ in aristas)
    assert {t for _, _, t in aristas} == {
        "ORGANIZADO_EN",
        "PROPONE_PRACTICAR_CON",
        "DECLARA_CODIGO_LOCAL",
        "PROPONE_EVALUAR_CON",
    }
    tipos = Counter(n["tipo"] for n in nodos.values())
    assert tipos["objetivo_original"] == 1020 and tipos["tarea_declarada"] == 4880
    assert tipos["criterio_propuesto"] == 4457
    for n in nodos.values():
        if n["tipo"] == "criterio_propuesto":
            assert n["desempeno_observado"] is None
    auditoria = json.loads(fs["didactica/auditoria.json"])
    assert auditoria["invariantes"]["llamadas_vertex_nuevas"] == 0
    assert len(auditoria["despues"]["objetivos_sin_tareas"]) == 1
    assert auditoria["despues"]["incidencias"]["CODIGO_SIN_CONSIGNA_SEPARABLE"] == 6


def test_referencias_descargadas_conservan_bytes_y_no_fingen_descargas_fallidas(nueva_entrega):
    _, _, fs = nueva_entrega
    refs = json.loads(fs["didactica/referencias/manifest.json"])["fuentes"]
    assert len({s["id"] for s in refs}) == len(refs)
    for s in refs:
        if s["estado"] == "descargado":
            raw = fs["didactica/referencias/" + s["archivo"]]
            assert (len(raw), sha(raw)) == (s["bytes"], s["sha256"])
        else:
            assert "sha256" not in s and s["error"]
    assert {s["id"] for s in refs if s["estado"] == "no_descargado"} == {
        "eef_primaria",
        "eef_secundaria",
        "mined_metodologia",
        "nhgri_poliploidia",
    }


def test_claves_de_densidad_calibracion_y_pendiente_son_coherentes():
    d = CASOS["densidad_6"]["datos"]
    densidades = [Decimal(t["masa_g"]) / Decimal(t["volumen_cm3"]) for t in d["tabla"]]
    assert densidades == list(map(Decimal, ["0.5", "2", "0.6", "1.5", "0.5"]))
    assert [t["objeto"] for t, rho in zip(d["tabla"], densidades, strict=True) if rho < d["densidad_fluido_g_cm3"]] == [
        "A",
        "C",
        "E",
    ]
    d = CASOS["calibracion_8"]["datos"]
    a, b = [list(map(lambda v: Decimal(str(v)), d[k])) for k in ("lecturas_A_N", "lecturas_B_N")]
    assert max(a) - min(a) == max(b) - min(b) == Decimal("0.02")
    assert sum(a) / 3 == Decimal("1.2") and sum(b) / 3 == Decimal("1")
    d = CASOS["pendiente_resorte_10"]["datos"]
    tabla = d["tabla"]
    pendiente = (Decimal(str(tabla[-1]["alargamiento_m"])) - Decimal(str(tabla[0]["alargamiento_m"]))) / (
        Decimal(str(tabla[-1]["fuerza_N"])) - Decimal(str(tabla[0]["fuerza_N"]))
    )
    assert pendiente == Decimal("0.01") and 1 / pendiente == d["constante_N_m"]


@pytest.mark.parametrize("nombre", ["manifest.json", "../escape", "didactica/../escape", "didactica//x"])
def test_exportacion_rechaza_rutas_comunes_que_oculten_o_escapen_manifest(tmp_path, nombre):
    destino = tmp_path / "salida"
    with pytest.raises(ValueError, match="rutas propias"):
        exportar([], {}, {}, destino, archivos_comunes={nombre: b"bytes"})
    assert not destino.exists()


def test_api_filtra_interseccion_pagina_y_rechaza_corpus_alterado(nueva_entrega, tmp_path):
    b, _, fs = nueva_entrega
    p = tmp_path / "data/materiales_produccion_v4"
    p.mkdir(parents=True)
    for nombre in ("biblioteca.sqlite", "manifest.json"):
        copy2(b.destino / nombre, p / nombre)
    app = FastAPI()
    app.include_router(crear_router_didactica(tmp_path))
    client = TestClient(app)
    prefix = "/api/v4/produccion/didactica"
    filas = json.loads(fs["didactica/indice.json"])["filas"]
    respuesta = client.get(prefix + "/habilidades").json()
    assert respuesta["total"] == 1020 and respuesta["dominio_observado"] is None
    assert client.get(prefix + "/habilidades?limite=7&offset=7").json()["filas"] == filas[7:14]
    esperadas = [f for f in filas if "D4" in f["codigos"] and f["grado"] == 10 and f["asignatura"] == "Física"]
    consulta = client.get(
        prefix + "/habilidades", params={"codigo": "D4", "grado": 10, "asignatura": "Física", "limite": 200}
    ).json()
    assert consulta["filas"] == esperadas and consulta["total"] == len(esperadas)
    assert len(client.get(prefix + "/macrohabilidades").json()["macrohabilidades"]) == 3
    assert client.get(prefix + "/auditoria").json()["auditoria"]["despues"]["casos_resueltos"] == 14
    for parametros in ({"codigo": "E99"}, {"grado": 1}, {"limite": 201}, {"offset": -1}, {"macro": "dominado"}):
        assert client.get(prefix + "/habilidades", params=parametros).status_code == 422
    with (p / "biblioteca.sqlite").open("ab") as f:
        f.write(b"alteracion")
    assert client.get(prefix + "/habilidades").status_code == 503


def test_api_no_inventa_indice_para_biblioteca_ausente(tmp_path):
    app = FastAPI()
    app.include_router(crear_router_didactica(tmp_path))
    assert TestClient(app).get("/api/v4/produccion/didactica/auditoria").status_code == 503
