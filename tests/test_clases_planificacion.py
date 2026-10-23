"""Agrupar para reducir llamadas no puede perder objetivos, fuentes, límites ni antecedentes."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from goes_science_kg.clases.planificacion import reagrupar
from goes_science_kg.motor.contratos import Evidencia, huella


def preparacion(n, fuentes, *, grado=4):
    fila_id = f"fila{n}"
    p = {
        "version": "preparacion-clases-1",
        "biblioteca_id": "biblioteca",
        "snapshot_id": "snapshot",
        "corpus_sha256": "anterior",
        "escenario": {"recursos": ["papel", "lapiz"]},
        "filas": [
            {
                "fila_id": fila_id,
                "grado": grado,
                "asignatura": "fisica",
                "unidad": f"unidad{n}",
                "origen": {"hoja": "fisica", "fila": n},
                "propuesta": {"fila_id": fila_id, "objetivo_propuesto": f"Objetivo literal {n}"},
                "fuentes_cientificas_ids": [e["id"] for e in fuentes],
            }
        ],
        "fuentes": fuentes,
        "recuperacion": {"seleccion": f"seleccion{n}.json"},
        "hallazgos_previos": {fila_id: ["Hallazgo que debe conservarse para redactar la nueva versión."]},
        "huellas_vetadas": {fila_id: [f"contenido_vetado{n}"]},
    }
    p["id"] = huella(p)
    return p


def fuente(id_, texto="Información científica literal del documento primario, conservada íntegramente."):
    return Evidencia.crear(id_, texto, {"documento": id_}, "referencia").model_dump(mode="json")


def corpus():
    return SimpleNamespace(huella="actual", huellas_compatibles={"anterior", "actual"}, verificar=lambda e: None)


def test_agrupar_deduplica_fuentes_y_conserva_cada_objetivo_y_su_antecedente():
    e = fuente("compartida")
    ps = [preparacion(n, [e]) for n in range(1, 6)]
    originales = deepcopy(ps)
    nuevos = reagrupar(ps, corpus())
    assert sorted(len(p["filas"]) for p in nuevos) == [1, 4]
    assert ps == originales
    por_id = {f["fila_id"]: (p, f) for p in nuevos for f in p["filas"]}
    for anterior in ps:
        f0 = anterior["filas"][0]
        p, f = por_id[f0["fila_id"]]
        assert f == f0 and p["fuentes"] == [e]
        assert p["antecedentes_documentales"][f["fila_id"]]["preparacion_id"] == anterior["id"]
        assert p["hallazgos_previos"][f["fila_id"]] == anterior["hallazgos_previos"][f["fila_id"]]
        assert p["huellas_vetadas"][f["fila_id"]] == anterior["huellas_vetadas"][f["fila_id"]]
        assert p["corpus_sha256"] == "actual"


def test_grados_diferentes_se_procesan_en_lotes_diferentes():
    ps = [preparacion(1, [fuente("e")], grado=4), preparacion(2, [fuente("e")], grado=5)]
    assert len(reagrupar(ps, corpus())) == 2


def test_opiniones_previas_de_recuperacion_se_conservan_fuera_del_contexto_de_los_jueces():
    from goes_science_kg.clases.preparacion import contexto

    p = preparacion(1, [fuente("e")])
    anterior = {"cobertura": "insuficiente", "lagunas": ["Opinión del selector sobre los pasajes previos."]}
    p["filas"][0]["seleccion_documental_anterior"] = anterior
    p["id"] = huella({k: v for k, v in p.items() if k != "id"})
    nuevo = reagrupar([p], corpus())[0]
    assert "seleccion_documental_anterior" not in contexto(nuevo)["filas"][0]
    assert nuevo["antecedentes_documentales"]["fila1"]["historico_recuperacion"] == {
        "seleccion_documental_anterior": anterior
    }


def test_limite_de_contexto_divide_lote_sin_recortar_pasajes():
    fuentes = [[fuente(f"e{fila}_{i}", "dato científico " * 600) for i in range(8)] for fila in range(2)]
    ps = [preparacion(n + 1, es) for n, es in enumerate(fuentes)]
    nuevos = reagrupar(ps, corpus())
    assert len(nuevos) == 2
    assert sorted(len(e["texto"]) for p in nuevos for e in p["fuentes"]) == sorted(
        len(e["texto"]) for es in fuentes for e in es
    )


@pytest.mark.parametrize("campo,valor", [("biblioteca_id", "otra"), ("snapshot_id", "otro"), ("escenario", {})])
def test_no_se_mezclan_identidades_o_escenarios(campo, valor):
    a, b = [preparacion(n, [fuente("e")]) for n in (1, 2)]
    b[campo] = valor
    b["id"] = huella({k: v for k, v in b.items() if k != "id"})
    with pytest.raises(ValueError, match="No se mezclan"):
        reagrupar([a, b], corpus())


def test_rechaza_fila_duplicada_y_corpus_desconocido():
    p = preparacion(1, [fuente("e")])
    with pytest.raises(ValueError, match="más de una"):
        reagrupar([p, deepcopy(p)], corpus())
    p["corpus_sha256"] = "no_registrado"
    p["id"] = huella({k: v for k, v in p.items() if k != "id"})
    with pytest.raises(ValueError, match="registro de corpus"):
        reagrupar([p], corpus())


@pytest.mark.parametrize("campo", ["borrador_inicial", "insumos_tabulares"])
def test_no_desliga_borradores_o_datos_externos_de_sus_preparaciones(campo):
    p = preparacion(1, [fuente("e")])
    p[campo] = ["dato ligado al antecedente"]
    p["id"] = huella({k: v for k, v in p.items() if k != "id"})
    with pytest.raises(ValueError, match="preparación específica"):
        reagrupar([p], corpus())
