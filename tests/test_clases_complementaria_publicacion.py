"""Sólo se publica lo válido y liberado por revisión; la API verifica el recibo y responde sin datos si falta."""

from __future__ import annotations

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_clases import guion
from test_clases_complementaria import SHA, anexo, evaluacion, item

from goes_science_kg.api_complementos import crear_router_complementos
from goes_science_kg.clases.complementaria_publicacion import RECIBO, compilar, leer_publicada, publicar

FILA = "CURRICULO:V4:" + "1" * 64
UNIDAD = "CLASE-UNIDAD-V4:" + "2" * 64
CORTO = FILA[-10:]


def escribir(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def preparar(raiz, veredicto_anexo="liberable", veredicto_eval="liberable"):
    r = raiz / "data/clases_v4/complementaria"
    pasaje = {"id": "SVN:doc#p1-1", "documento": "doc", "pagina": 1, "texto": "x" * 80, "temas": ["t"], "grados": [4]}
    escribir(
        r / "fuentes_nacionales/registro.json",
        [
            {
                "id": "doc",
                "institucion": "MARN",
                "titulo": "Informe",
                "anio": 2017,
                "url": "https://x",
                "sha256": "c" * 64,
            }
        ],
    )
    escribir(r / "fuentes_nacionales/pasajes/doc.json", [pasaje])
    g = guion(FILA).model_dump(mode="json")
    escribir(
        r / "expedientes/u1.json",
        {
            "unidad_id": UNIDAD,
            "corto": "u1",
            "asignatura": "Ciencias",
            "grado": 4,
            "unidad": "Unidad 1",
            "fuentes_nacionales": [{"id": pasaje["id"]}],
            "clases": [
                {
                    "fila_id": FILA,
                    "grado": 4,
                    "titulo": g["titulo"],
                    "guion_sha256": SHA,
                    "guion": g,
                    "candidatos_previas": [{"concepto": "CON:x", "fila_id": "fila0"}],
                    "candidatos_continuidad": [],
                }
            ],
        },
    )
    datos = anexo(fila_id=FILA).model_dump(mode="json")
    datos["contexto_nacional"] = {
        "afirmaciones": [
            {"texto": "El informe del MARN registra el dato citado para la clase.", "fuentes_ids": [pasaje["id"]]}
        ],
        "fuente_a_consultar": None,
    }
    escribir(r / "anexos/u1" / f"{CORTO}.json", datos)
    items = [
        item(f"I0{i}", d, fila=FILA) for i, d in enumerate(("conocer", "aplicar", "aplicar", "razonar", "conocer"), 1)
    ]
    ev = evaluacion([*items, item("I06", "razonar", "respuesta_construida", FILA)]).model_dump(mode="json")
    escribir(r / "evaluaciones/u1.json", ev | {"unidad_id": UNIDAD})
    escribir(
        r / "revision/u1.json",
        {
            "anexos": [{"fila_corta": CORTO, "veredicto": veredicto_anexo, "hallazgos": []}],
            "evaluacion": {"veredicto": veredicto_eval, "hallazgos": []},
        },
    )
    return r


def test_publica_lo_liberado_con_sus_fuentes_y_retiene_lo_bloqueado(tmp_path):
    preparar(tmp_path)
    d = compilar(tmp_path)
    assert list(d["clases"]) == [FILA] and list(d["unidades"]) == [UNIDAD] and not d["retenidos"]
    assert d["fuentes_nacionales"]["SVN:doc#p1-1"]["institucion"] == "MARN"
    preparar(tmp_path, veredicto_anexo="bloquear", veredicto_eval="bloquear")
    d = compilar(tmp_path)
    assert not d["clases"] and not d["unidades"] and {x["tipo"] for x in d["retenidos"]} == {"anexo", "evaluacion"}


def test_la_revision_final_prevalece_sobre_la_primera(tmp_path):
    r = preparar(tmp_path, veredicto_anexo="bloquear")
    escribir(
        r / "revision/u1_final.json",
        {"anexos": [{"fila_corta": CORTO, "veredicto": "liberable"}], "evaluacion": {"veredicto": "liberable"}},
    )
    assert FILA in compilar(tmp_path)["clases"]


def test_api_verifica_el_recibo_y_responde_sin_datos_si_falta(tmp_path):
    preparar(tmp_path)
    app = FastAPI()
    app.include_router(crear_router_complementos(tmp_path))
    cliente = TestClient(app)
    assert cliente.get("/api/v4/complementos").status_code == 503
    recibo = publicar(tmp_path)
    escribir(tmp_path / RECIBO, recibo)
    assert cliente.get("/api/v4/complementos").json()["clases"] == 1
    assert cliente.get(f"/api/v4/complementos/clases/{FILA}").json()["guion_sha256"] == SHA
    assert cliente.get(f"/api/v4/complementos/unidades/{UNIDAD}").status_code == 200
    assert cliente.get("/api/v4/complementos/clases/../../etc").status_code == 404
    publicado = tmp_path / recibo["ruta"]
    publicado.write_text(publicado.read_text().replace("MARN", "OTRA"), encoding="utf-8")
    try:
        leer_publicada(tmp_path)
    except ValueError as error:
        assert "recibo" in str(error)
    else:
        raise AssertionError("Una publicación alterada no debe aceptarse")
