"""Auditoría del artefacto entregado: contenido revisado, dependencia y original íntegro."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from goes_science_kg.api_didactica import crear_router_didactica
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.revision_docente.contratos import ROLES
from goes_science_kg.produccion.revision_docente.edicion import validar_edicion
from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar

BASE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def entrega_revisada():
    p = BASE / "data/materiales_produccion_v4"
    if not p.exists():
        pytest.skip("Restaurar biblioteca de preparaciones revisadas")
    b = Biblioteca(p)
    if b.manifest["procedencia"].get("version_diseno") != "preparacion-malla-final-3":
        pytest.skip("La biblioteca seleccionada todavía no es la edición revisada")
    b.validar()
    rs, fs = b.exportar()
    return b, rs, fs


def test_todos_los_votos_reproducen_su_contexto_y_no_se_cambia_el_original(entrega_revisada):
    b, registros, fs = entrega_revisada
    base = Biblioteca(BASE / "data/materiales_produccion_v4_didactica_v2")
    originales, _ = base.exportar()
    anteriores = {r["id"]: r for r in originales}
    solicitudes = json.loads(fs["didactica/revision/ronda_1.json"])
    solicitudes += json.loads(fs.get("didactica/revision/ronda_2.json", b"[]"))
    contextos = {sha(serializar(s)): s for s in solicitudes}
    posteriores = json.loads(fs["didactica/revision/edicion_editorial_posterior.json"])["contextos"]
    contextos.update({sha(serializar(s)): s for s in posteriores})
    for nombre, raw in fs.items():
        if not nombre.startswith("didactica/revision/lecturas/"):
            continue
        d = json.loads(raw)
        s = contextos[d["identidad"]["solicitud_sha256"]]
        obtenido = procesar(DictamenSeleccion.model_validate(d["salida_selecciones"]), s, d["identidad"]["rol"])
        assert all(d[k] == v for k, v in obtenido.items())
    por_id = {r["id"]: r for r in registros}
    for r in registros:
        d = r["documento"]
        revision = d["revision_docente"]
        validar_edicion(d["edicion_docente"])
        assert sha(serializar(d["edicion_docente"])) == revision["edicion_sha256"]
        assert b.manifest["procedencia"]["snapshot_id"] == d["snapshot_id"]
        assert revision["contexto_sha256"] in contextos
        if revision.get("etapa") == "ajuste_editorial_sin_relectura":
            assert not revision["lecturas"] and set(revision["faltan_roles"]) == set(ROLES)
            assert revision["antecedente_revisado"]["edicion_sha256"] != revision["edicion_sha256"]
            assert contextos[revision["contexto_sha256"]]["edicion"] == d["edicion_docente"]
        if r["tipo"] == "paquete_objetivo":
            assert d["original"] == anteriores[r["id"]]["documento"]["original"]
            assert all(
                c["logro_observado"] is None and c["respuesta_observada"] is None
                for c in d["edicion_docente"]["criterios"]
            )
        favorable = {v["rol"] for v in revision["lecturas"] if v["veredicto"] == "aprobar"} == set(ROLES)
        pendientes = r["tipo"] == "paquete_unidad" and any(
            por_id[f]["estado"] != "revision_automatica_completa" for f in d["filas_ids"]
        )
        assert (r["estado"] == "revision_automatica_completa") == (
            favorable and not pendientes and not revision.get("roles_sin_control_superado")
        )
        assert d["estado_revision"] == revision["estado"] == r["estado"]
    for nombre, ref in base.manifest["originales"].items():
        if nombre.startswith("insumos/") and nombre.endswith(".xlsx"):
            assert b.manifest["originales"][nombre] == ref


def test_api_filtra_completacion_y_estado_sin_confundirlos_con_dominio(entrega_revisada):
    b, registros, _ = entrega_revisada
    app = FastAPI()
    app.include_router(crear_router_didactica(BASE))
    c = TestClient(app)
    prefijo = "/api/v4/produccion/didactica"
    resumen = c.get(prefijo + "/revision").json()
    assert resumen["biblioteca_id"] == b.manifest["id"]
    assert sum(resumen["por_estado"].values()) == 1128
    assert resumen["originales_modificados"] == 0 and resumen["eficacia_observada"] is None
    assert resumen["llamadas_modelos_por_peticion"] == 0
    fila = c.get(prefijo + "/habilidades", params={"completacion_derivada": True}).json()
    assert fila["total"] == 1 and fila["filas"][0]["grado"] == 3
    assert fila["filas"][0]["fila_id"] in resumen["completaciones_derivadas"]
    for estado in ("revision_automatica_completa", "revision_automatica_con_pendientes"):
        esperado = sum(r["tipo"] == "paquete_objetivo" and r["estado"] == estado for r in registros)
        d = c.get(prefijo + "/habilidades", params={"estado_revision": estado}).json()
        assert d["total"] == esperado and d["dominio_observado"] is None


def test_grafo_efectivo_conserva_habilidades_criterios_y_extremos_validos(entrega_revisada):
    _, rs, fs = entrega_revisada
    g = json.loads(fs["didactica/grafo.json"])
    nodos = {n["id"]: n for n in g["nodos"]}
    assert len(nodos) == len(g["nodos"])
    aristas = {(a["origen"], a["destino"], a["tipo"]) for a in g["aristas"]}
    assert len(aristas) == len(g["aristas"])
    assert all(a in nodos and b in nodos for a, b, _ in aristas)
    assert len([n for n in nodos.values() if n["tipo"] == "macro_propuesta"]) == 3
    assert len([n for n in nodos.values() if n["tipo"] == "microhabilidad_local"]) == 15
    actividades = sum(
        len(r["documento"]["edicion_docente"]["actividades"]) for r in rs if r["tipo"] == "paquete_objetivo"
    )
    for tipo in ("PROPONE_ACTIVIDAD_DERIVADA", "DECLARA_CODIGO_LOCAL", "PROPONE_EVALUAR_CON"):
        assert sum(t == tipo for _, _, t in aristas) == actividades
    assert all(n.get("desempeno_observado") is None for n in nodos.values())


def test_cada_zip_tiene_indice_legible_y_todos_sus_enlaces_resuelven(entrega_revisada):
    import re
    from io import BytesIO
    from zipfile import ZipFile

    _, registros, fs = entrega_revisada
    indice = json.loads(fs["paquetes/indice.json"])
    ids = []
    for p in indice["paquetes"]:
        with ZipFile(BytesIO(fs["paquetes/" + p["archivo"]])) as z:
            texto = z.read("LEEME.md").decode()
            enlaces = re.findall(r"\]\(([^)]+)\)", texto)
            assert len(enlaces) == p["paquetes"]
            assert len(enlaces) == len(set(enlaces))
            assert all(e in z.namelist() for e in enlaces)
            for e in enlaces:
                registro = json.loads(z.read(e.removesuffix(".md") + ".json"))
                ids.append(registro["id"])
    assert len(ids) == len(set(ids)) == len(registros) == 1128
