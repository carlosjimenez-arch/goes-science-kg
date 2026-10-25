"""La cota no puede truncar evidencia, fabricar documentos ni ocultar una laguna."""

from types import SimpleNamespace

import pytest

from goes_science_kg.clases.curacion import curar
from goes_science_kg.materiales.compilacion import serializar
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.recuperacion.lexico import IndiceLexico
from goes_science_kg.recuperacion.modelos import Documento


def entorno(textos):
    evidencias, documentos, verificados = {}, {}, []
    for doc, pasajes in textos.items():
        es = [Evidencia.crear(f"{doc}#{n}", t, {"documento": doc}, "v1") for n, t in enumerate(pasajes)]
        evidencias.update((e.id, e) for e in es)
        documentos[doc] = {"evidencias": es}
    indice = IndiceLexico(
        Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version) for e in evidencias.values()
    )
    c = SimpleNamespace(evidencias=evidencias, indice=indice, verificar=lambda e: verificados.append(e.id))
    return c, documentos, verificados


def test_preserva_pasajes_completos_diversos_y_deduplica_texto():
    a = "Mitosis separates duplicated chromosomes into daughter nuclei. " * 4
    b = "Cytokinesis separates the cell cytoplasm after nuclear division. " * 4
    c, docs, vistos = entorno({"d1": [a, a], "d2": [b]})
    res = curar(c, docs, ["d1", "d2"], ["mitosis chromosomes", "cytokinesis cell cytoplasm"])
    assert not res["pendientes"] and len(res["fuentes"]) == 2
    assert {e["texto"] for e in res["fuentes"]} == {a, b}
    assert set(vistos) == {e["id"] for e in res["fuentes"]}
    assert res["bytes"] == len(serializar(res["fuentes"]))


def test_un_pasaje_que_no_cabe_se_declara_pendiente_sin_recortarlo():
    texto = "Mitosis separates chromosomes. " * 120
    c, docs, vistos = entorno({"d": [texto]})
    res = curar(c, docs, ["d"], ["mitosis chromosomes"], max_bytes=2000)
    assert res["pendientes"] and not res["fuentes"] and not vistos
    assert c.evidencias["d#0"].texto == texto


def test_una_pregunta_y_un_documento_inventado_no_se_convierten_en_evidencia():
    pregunta = "Why do cells require mitosis to separate their chromosomes into daughter cells?"
    c, docs, _ = entorno({"d": [pregunta]})
    assert curar(c, docs, ["d"], ["mitosis chromosomes"])["pendientes"]
    with pytest.raises(ValueError, match="ajeno"):
        curar(c, docs, ["inventado"], ["mitosis"])


def test_un_pasaje_que_no_tiene_coincidencia_no_cubre_un_capitulo():
    c, docs, _ = entorno(
        {"d": ["Elastic materials deform under applied forces and recover their shape when unloaded."]}
    )
    assert curar(c, docs, ["d"], ["mitosis chromosomes"])["pendientes"]
