"""Panel de expertos IA (spec 14): validación de dictámenes, consolidación por unanimidad, deliberación y la secuencia
experto → psicopedagogo → experto del contenido. Nada aquí llama a un modelo."""

from __future__ import annotations

import json

import pytest

from goes_science_kg import panel
from goes_science_kg.config import ruta


def _ev():
    return [{"fuente": "criterio disciplinar", "cita": "argumento breve"}]


def _dic(i, decision, confianza="alta", **extra):
    return {"id": i, "decision": decision, "justificacion": "Criterio técnico breve.", "evidencia": _ev(),
            "confianza": confianza, **extra}


@pytest.fixture
def aislado(tmp_path, monkeypatch):
    """El estado y los lotes del panel en tmp_path."""
    real = panel.ruta
    monkeypatch.setattr(panel, "ruta", lambda rel: tmp_path / rel if str(rel).startswith(panel.DIR) else real(rel))
    return tmp_path


def test_cada_rol_tiene_agente_y_valida_su_salida():
    from goes_science_kg.lotes import AGENTES

    for rol in panel.config()["roles"]:
        assert AGENTES[rol] == "panel"
        texto = ruta(f".claude/agents/{rol}.md").read_text(encoding="utf-8")
        assert "prompts/panel_dictaminar.md" in texto and "no es una confirmación del MINED" in texto


def test_errores_de_un_dictamen():
    lote = {"expedientes": [
        {"id": "A", "tipo": "decision", "opciones": ["aceptar", "rechazar"], "datos": {}},
        {"id": "B", "tipo": "asignacion", "opciones": ["aceptar", "cambiar", "rechazar"],
         "datos": {"asignado_a": ["CON:x"], "opciones": [{"id": "CON:x"}, {"id": "CON:y"}]}},
        {"id": "C", "tipo": "hallazgo", "opciones": ["respaldar", "matizar", "no_respaldar"], "datos": {}}]}
    bien = [_dic("A", "aceptar"), _dic("B", "cambiar", asignado_a=["CON:y"]), _dic("C", "matizar", texto="Matiz.")]
    assert panel.errores_lote(lote, bien) == []
    mal = [_dic("A", "rechazar"), _dic("B", "cambiar", asignado_a=["CON:x"]),
           {**_dic("C", "respaldar"), "evidencia": [], "justificacion": "x " * 80}]
    errores = " | ".join(panel.errores_lote(lote, mal))
    for esperado in ("exige «alternativa»", "distinto del actual", "evidencia", "justificación"):
        assert esperado in errores
    assert any("sin dictamen" in e for e in panel.errores_lote(lote, bien[:2]))


def test_la_correccion_de_contenido_sigue_siendo_valida():
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    act = Pedagogia.cargar().actividades["ACT:G09-CIE-U8-8.2/obj-1"]
    campos = panel.config()["campos_editables"]["actividad"]
    assert panel.errores_elemento_corregido(act, {"retroalimentacion": "Más clara."}, campos) == []
    assert panel.errores_elemento_corregido(act, {"correcta": "Z"}, campos)     # la correcta fuera de las opciones
    assert panel.errores_elemento_corregido(act, {"id": "ACT:otro"}, campos)    # campo no editable


def _expediente(tipo, roles, **extra):
    return {"tipo": tipo, "titulo": "t", "pregunta": "p", "datos": {}, "roles": roles, "dictamenes": [],
            "estado": "pendiente", **extra}


def test_unanimidad_deliberacion_y_sin_consenso(aislado):
    estado = {"X": _expediente("hallazgo", ["experto-fisica", "psicopedagogo"]),
              "Y": _expediente("hallazgo", ["experto-fisica", "psicopedagogo"])}
    panel._guardar_estado(estado)
    lotes = panel.preparar(1)
    assert {p.split("/")[-1] for p in lotes} == {"lote_r1_experto-fisica.json", "lote_r1_psicopedagogo.json"}
    d = aislado / panel.DIR / "lotes"
    (d / "salida_r1_experto-fisica.json").write_text(json.dumps(
        [_dic("X", "respaldar"), _dic("Y", "respaldar")]), encoding="utf-8")
    (d / "salida_r1_psicopedagogo.json").write_text(json.dumps(
        [_dic("X", "respaldar"), _dic("Y", "matizar", texto="Con apoyo concreto.")]), encoding="utf-8")
    panel.consolidar(1)
    e = panel.cargar_estado()
    assert e["X"]["estado"] == "resuelta" and e["Y"]["estado"] == "en_deliberacion"
    panel.preparar(2)
    lote = json.loads((d / "lote_r2_experto-fisica.json").read_text(encoding="utf-8"))
    assert [x["id"] for x in lote["expedientes"]] == ["Y"] and lote["expedientes"][0]["dictamenes_anteriores"]
    (d / "salida_r2_experto-fisica.json").write_text(json.dumps([_dic("Y", "respaldar")]), encoding="utf-8")
    (d / "salida_r2_psicopedagogo.json").write_text(json.dumps([_dic("Y", "matizar", texto="Igual.")]),
                                                    encoding="utf-8")
    panel.consolidar(2)
    assert panel.cargar_estado()["Y"]["estado"] == "sin_consenso"     # sin unanimidad tras deliberar: a una persona


def test_confianza_baja_va_a_una_persona(aislado):
    panel._guardar_estado({"X": _expediente("decision", ["experto-quimica"])})
    panel.preparar(1)
    d = aislado / panel.DIR / "lotes"
    (d / "salida_r1_experto-quimica.json").write_text(json.dumps([_dic("X", "aceptar", "baja")]), encoding="utf-8")
    panel.consolidar(1)
    assert panel.cargar_estado()["X"]["estado"] == "sin_consenso"


def test_contenido_en_secuencia(aislado):
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    act = Pedagogia.cargar().actividades["ACT:G09-CIE-U8-8.2/obj-1"]
    x = _expediente("contenido", ["experto-biologia", "psicopedagogo"], elemento="actividad",
                    etapas=[["experto-biologia"], ["psicopedagogo"], ["experto-biologia"]])
    x["datos"] = {"elemento": act}
    panel._guardar_estado({"P": x})
    d = aislado / panel.DIR / "lotes"
    panel.preparar(1)
    assert (d / "lote_r1_experto-biologia.json").exists() and not (d / "lote_r1_psicopedagogo.json").exists()
    (d / "salida_r1_experto-biologia.json").write_text(json.dumps(
        [_dic("P", "corregir", cambios={"retroalimentacion": "Versión del experto."})]), encoding="utf-8")
    panel.consolidar(1)
    panel.preparar(2)
    lote = json.loads((d / "lote_r2_psicopedagogo.json").read_text(encoding="utf-8"))
    assert lote["expedientes"][0]["datos"]["elemento"]["retroalimentacion"] == "Versión del experto."
    (d / "salida_r2_psicopedagogo.json").write_text(json.dumps([_dic("P", "aprobar")]), encoding="utf-8")
    panel.consolidar(2)
    e = panel.cargar_estado()["P"]
    assert e["estado"] == "resuelta" and e["resolucion"]["decision"] == "corregir"
    assert e["version_vigente"]["retroalimentacion"] == "Versión del experto."


def test_el_dictamen_queda_como_del_panel_y_no_como_confirmacion():
    from goes_science_kg import revision_decisiones as rd

    x = _expediente("decision", ["experto-quimica"])
    x["dictamenes"] = [{**_dic("X", "rechazar", alternativa="Mantener la clase automática."), "ronda": 1,
                        "rol": "experto-quimica"}]
    x["resolucion"] = {"decision": "rechazar", "ronda": 1}
    reg = panel._registro(x)
    assert "no es una confirmación del MINED" in reg["nota"] and reg["alternativa"]
    r = {"dictamenes_panel": [reg]}
    assert rd._estado(r).startswith("dictamen del panel: rechazar")
    assert rd._estado({**r, "confirmaciones": [{"revisado_por": "MINED"}]}) == "confirmada"   # lo humano gana


def test_los_inciertos_son_expedientes_del_experto_de_la_disciplina():
    inc = panel._exp_inciertos()
    assert inc and all(len(x["roles"]) == 1 and x["roles"][0].startswith("experto-") for x in inc.values())
    assert all(x["datos"]["lecturas"]["amplia"] != x["datos"]["lecturas"]["estricta"] for x in inc.values())
