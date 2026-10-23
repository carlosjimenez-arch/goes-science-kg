"""Un dictamen automático positivo no libera una versión cuyo defecto ya está documentado."""

from __future__ import annotations

import json

import pytest

from goes_science_kg.clases.revision_contenido import validar_seleccion
from goes_science_kg.materiales.compilacion import serializar, sha


@pytest.fixture
def expediente(tmp_path):
    raiz = tmp_path / "data/clases_v4/auditoria_contenido"
    raiz.mkdir(parents=True)
    plan = {"version": "auditoria-contenido-desarrollo-1", "casos": [{"fila_id": "f"}]}
    (raiz / "plan.json").write_bytes(serializar(plan))
    guion = {"fila_id": "f", "titulo": "Anterior", "objetivo": "Objetivo conservado", "contenido": "dato erróneo"}
    raw = serializar({"filas": {"f": {"guion": guion}}})
    (tmp_path / "anterior.json").write_bytes(raw)
    revision = {
        "version": "revision-contenido-desarrollo-1",
        "plan_sha256": sha(serializar(plan)),
        "revisiones": [
            {
                "fila_id": "f",
                "resultado": "anterior.json",
                "resultado_sha256": sha(raw),
                "guion_sha256": sha(serializar(guion)),
                "estado": "requiere_correccion",
                "hallazgos": ["La explicación contiene un dato científico erróneo."],
            }
        ],
    }
    (raiz / "revision_desarrollo.json").write_bytes(serializar(revision))
    seleccion = {"f": {"preparacion": "preparacion.json", "resultado": "anterior.json"}}
    return tmp_path, raiz, revision, seleccion, guion


def test_no_se_libera_una_version_con_defecto_conocido(expediente):
    base, _, _, seleccion, _ = expediente
    with pytest.raises(ValueError, match="defectos"):
        validar_seleccion(base, seleccion)


def test_falta_de_casos_en_muestra_impide_cierre(expediente):
    base, raiz, revision, seleccion, _ = expediente
    revision["revisiones"] = []
    (raiz / "revision_desarrollo.json").write_bytes(serializar(revision))
    with pytest.raises(ValueError, match="exactamente la muestra"):
        validar_seleccion(base, seleccion)


def test_requiere_correccion_sustantiva_y_resolucion_exacta(expediente):
    base, raiz, _, seleccion, guion = expediente
    nuevo = guion | {"contenido": "Explicación corregida y sustentada en una fuente verificable."}
    raw = serializar({"filas": {"f": {"guion": nuevo}}})
    (base / "nuevo.json").write_bytes(raw)
    seleccion["f"]["resultado"] = "nuevo.json"
    with pytest.raises(ValueError, match="resolución exacta"):
        validar_seleccion(base, seleccion)
    resolucion = {
        "f": {
            "estado": "corregido_y_revisado",
            "expediente": seleccion["f"],
            "resultado_sha256": sha(raw),
            "guion_sha256": sha(serializar(nuevo)),
            "hallazgos_atendidos": ["Se sustituyó el dato erróneo por el dato científico sustentado."],
        }
    }
    (raiz / "resoluciones.json").write_bytes(serializar(resolucion))
    assert validar_seleccion(base, seleccion)["casos"] == 1
    (base / "nuevo.json").write_bytes(serializar({"filas": {"f": {"guion": nuevo | {"contenido": "alterado"}}}}))
    with pytest.raises(ValueError, match="resolución exacta"):
        validar_seleccion(base, seleccion)


def test_cambiar_solo_titulo_no_resuelve_defecto(expediente):
    base, _, _, seleccion, guion = expediente
    raw = serializar({"filas": {"f": {"guion": guion | {"titulo": "Nuevo título"}}}})
    (base / "nuevo.json").write_bytes(raw)
    seleccion["f"]["resultado"] = "nuevo.json"
    with pytest.raises(ValueError, match="defectos"):
        validar_seleccion(base, seleccion)


def test_guion_sin_defecto_solo_permite_version_exactamente_revisada(expediente):
    base, raiz, revision, seleccion, guion = expediente
    revision["revisiones"][0]["estado"] = "sin_defecto_material_en_revision"
    (raiz / "revision_desarrollo.json").write_bytes(serializar(revision))
    assert validar_seleccion(base, seleccion)["casos"] == 1
    (base / "otro.json").write_bytes(serializar({"filas": {"f": {"guion": guion | {"contenido": "cambiado"}}}}))
    seleccion["f"]["resultado"] = "otro.json"
    with pytest.raises(ValueError, match="resolución exacta"):
        validar_seleccion(base, seleccion)


def test_entrega_completa_no_puede_omitir_o_reducir_muestra(tmp_path, expediente):
    with pytest.raises(ValueError, match="Falta un archivo"):
        validar_seleccion(tmp_path / "sin_archivos", {}, obligatoria=True)
    base, _, _, seleccion, _ = expediente
    with pytest.raises(ValueError, match="32 casos"):
        validar_seleccion(base, seleccion, obligatoria=True)


def test_no_se_acepta_auditoria_que_no_corresponde_a_los_bytes(expediente):
    base, _, _, seleccion, _ = expediente
    p = base / "anterior.json"
    r = json.loads(p.read_bytes())
    r["filas"]["f"]["guion"]["contenido"] = "alterado después de auditar"
    p.write_bytes(serializar(r))
    with pytest.raises(ValueError, match="guion archivado"):
        validar_seleccion(base, seleccion)


def test_un_hallazgo_posterior_retiene_incluso_una_version_antes_considerada_correcta(expediente):
    base, raiz, revision, seleccion, _ = expediente
    revision["revisiones"][0]["estado"] = "sin_defecto_material_en_revision"
    (raiz / "revision_desarrollo.json").write_bytes(serializar(revision))
    assert validar_seleccion(base, seleccion)["casos"] == 1
    hallazgo = revision["revisiones"][0] | {"estado": "requiere_correccion"}
    (raiz / "seguimiento.json").write_bytes(
        serializar({"version": "seguimiento-contenido-clases-1", "revisiones": [hallazgo]})
    )
    with pytest.raises(ValueError, match="defectos"):
        validar_seleccion(base, seleccion)
