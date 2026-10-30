"""Sólo se publica lo válido y liberado por revisión; la API verifica el recibo y responde sin datos si falta."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_clases import guion
from test_clases_complementaria import SHA, anexo, evaluacion, item

from goes_science_kg.api_complementos import crear_router_complementos
from goes_science_kg.clases.complementaria_publicacion import RECIBO, compilar, leer_publicada, publicar
from goes_science_kg.clases.complementaria_revision import digest, estado_revisiones, informe_observaciones

FILA = "CURRICULO:V4:" + "1" * 64
UNIDAD = "CLASE-UNIDAD-V4:" + "2" * 64
CORTO = FILA[-10:]


def escribir(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def dictamen(r, veredicto_anexo="liberable", veredicto_eval="liberable"):
    return {
        "version": "revision-complementaria-2",
        "unidad_id": UNIDAD,
        "expediente_sha256": digest(r / "expedientes/u1.json"),
        "revisor": "revisor-independiente",
        "ronda": "inicial",
        "anexos": [
            {
                "fila_corta": CORTO,
                "sha256": digest(r / "anexos/u1" / f"{CORTO}.json"),
                "veredicto": veredicto_anexo,
                "hallazgos": ["Defecto concreto"] if veredicto_anexo == "bloquear" else [],
            }
        ],
        "evaluacion": {
            "sha256": digest(r / "evaluaciones/u1.json"),
            "veredicto": veredicto_eval,
            "hallazgos": ["Clave incorrecta"] if veredicto_eval == "bloquear" else [],
            "items_con_defecto": [],
        },
        "observaciones_sobre_guiones": [],
    }


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
            "fuentes_nacionales": [
                pasaje | {"institucion": "MARN", "titulo": "Informe", "anio": 2017},
            ],
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
        dictamen(r, veredicto_anexo, veredicto_eval),
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


@pytest.mark.parametrize(
    ("corrector", "revisor", "mismo_actor"),
    [
        ("corrector-distinto", "revisor-independiente", "corrector-distinto"),
        ("codex-corrector-a", "codex-revisor-b", "codex-revisor-a"),
        ("codex-corrector-b", "codex-revisor-c", "codex-revisor-b"),
        ("codex-corrector-c", "codex-revisor-root", "codex-revisor-c"),
        ("codex-corrector-root", "codex-revisor-a", " CODEX-REVISOR-ROOT "),
        ("codex-root", "codex-revisor-c", "codex-revisor-root"),
    ],
)
def test_la_revision_final_prevalece_y_exige_otro_actor(tmp_path, corrector, revisor, mismo_actor):
    r = preparar(tmp_path, veredicto_anexo="bloquear")
    escribir(
        r / "revision/u1_codex_r1.json",
        dictamen(r, veredicto_anexo="bloquear"),
    )
    cambio = {
        "ruta": f"anexos/u1/{CORTO}.json",
        "antes_sha256": digest(r / "anexos/u1" / f"{CORTO}.json"),
    }
    archivo = r / cambio["ruta"]
    archivo.write_bytes(archivo.read_bytes() + b"\n")
    cambio["despues_sha256"] = digest(archivo)
    escribir(
        r / "correcciones/u1_codex.json",
        {
            "version": "correccion-complementaria-1",
            "unidad_id": UNIDAD,
            "corrector": corrector,
            "revision_inicial_sha256": digest(r / "revision/u1_codex_r1.json"),
            "cambios": [cambio],
        },
    )
    final = dictamen(r) | {
        "revisor": revisor,
        "ronda": "final",
        "correccion_sha256": digest(r / "correcciones/u1_codex.json"),
    }
    escribir(r / "revision/u1_codex_final.json", final)
    assert FILA in compilar(tmp_path)["clases"]
    final["revisor"] = mismo_actor
    escribir(r / "revision/u1_codex_final.json", final)
    assert not compilar(tmp_path)["clases"]


def test_revision_omitida_duplicada_o_ilegible_nunca_libera_contenido(tmp_path):
    r = preparar(tmp_path)
    for anexos in ([], dictamen(r)["anexos"] * 2):
        escribir(r / "revision/u1.json", dictamen(r) | {"anexos": anexos})
        assert not compilar(tmp_path)["clases"]
    (r / "revision/u1_codex_final.json").write_text("{incompleto")
    assert not compilar(tmp_path)["clases"]
    assert estado_revisiones(tmp_path)["pendientes_revision"] == 1


def test_edicion_posterior_invalida_la_revision_aunque_siga_siendo_valida(tmp_path):
    r = preparar(tmp_path)
    archivo = r / "evaluaciones/u1.json"
    archivo.write_bytes(archivo.read_bytes() + b"\n")
    d = compilar(tmp_path)
    assert not d["clases"] and not d["unidades"]
    assert "evaluación no coincide" in str(d["retenidos"])
    assert estado_revisiones(tmp_path)["pendientes_revision"] == 1


def test_una_fuente_editada_no_hereda_aprobacion_del_expediente(tmp_path):
    r = preparar(tmp_path)
    p = r / "fuentes_nacionales/pasajes/doc.json"
    datos = json.loads(p.read_bytes())
    datos[0]["texto"] = "Texto diferente que nadie ha revisado." * 3
    escribir(p, datos)
    assert not compilar(tmp_path)["clases"]
    assert FILA not in compilar(tmp_path)["clases"]


def test_un_manifiesto_vacio_no_aborta_ni_libera_la_compilacion(tmp_path):
    r = preparar(tmp_path)
    escribir(r / "revision/u1_codex_r1.json", dictamen(r))
    final = dictamen(r) | {"ronda": "final", "correccion_sha256": "0" * 64}
    escribir(r / "revision/u1_codex_final.json", final)
    for datos in (None, [], {}):
        escribir(r / "correcciones/u1_codex.json", datos)
        assert not compilar(tmp_path)["clases"]
        assert estado_revisiones(tmp_path)["pendientes_revision"] == 1
    final["ronda"] = "inicial"
    escribir(r / "revision/u1_codex_final.json", final)
    assert not compilar(tmp_path)["clases"]


def test_estado_no_confunde_bloqueos_con_trabajo_terminado_y_conserva_observaciones(tmp_path):
    r = preparar(tmp_path, veredicto_anexo="bloquear")
    escribir(
        r / "revision/u1_codex_r1.json",
        dictamen(r, "bloquear")
        | {
            "observaciones_sobre_guiones": ["Posible defecto en el original."],
        },
    )
    anterior = json.loads((r / "revision/u1.json").read_bytes())
    anterior["observaciones_sobre_guiones"] = ["Posible  defecto en el original.", "Otra observación."]
    escribir(r / "revision/u1.json", anterior)
    estado = estado_revisiones(tmp_path)
    assert estado["liberables"] == 0 and estado["retenidas"] == 1
    assert estado["unidades"][0]["requiere_correccion"]
    informe = informe_observaciones(tmp_path)
    assert len(informe["observaciones"]) == 2
    assert len(informe["observaciones"][0]["evidencias"]) == 2
    assert all(o["estado"] == "pendiente_de_contraste" for o in informe["observaciones"])


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
