"""Controles de relevancia para defectos observados en la revisión del contenido."""

from __future__ import annotations

import pytest

from goes_science_kg.clases.fuentes import CorpusClases
from goes_science_kg.clases.recuperacion import buscar_fuentes, es_expositivo
from goes_science_kg.config import ruta


@pytest.mark.parametrize(
    "texto",
    [
        "Approximately how many mass extinction events occurred?",
        "Calculate the mass of the products from these reactants.",
        "Considering that mass is extensive, explain why density is intensive.",
        "Complete and balance the equations for the following reactions.",
        "Which of the following statements is correct?",
    ],
)
def test_pregunta_o_consigna_sola_no_se_presenta_como_evidencia(texto):
    assert not es_expositivo(texto)


def test_pasaje_declarativo_expositivo_se_conserva():
    assert es_expositivo("Matter has mass. During a chemical reaction, the total mass remains constant.")


@pytest.fixture(scope="module")
def corpus():
    p = ruta("data/referencias_clases_2026")
    if not (p / "manifest.json").is_file():
        pytest.skip("Fuentes primarias privadas no restauradas")
    return CorpusClases(p)


def test_conservacion_recupera_ley_y_no_otras_leyes_fisicas(corpus):
    fila = {
        "propuesta": {"disciplinas_propuestas": ["quimica"]},
        "consulta_recuperacion": (
            "law of conservation of mass experimental verification chemical reactions closed system reactants products"
        ),
    }
    fuentes = buscar_fuentes(corpus, fila)
    assert any("law of conservation of matter" in e.texto for e in fuentes)
    assert all(e.fuente["libro"] == "chemistry-2e" and es_expositivo(e.texto) for e in fuentes)
    assert not any("angular momentum" in e.texto for e in fuentes)


def test_taxismos_tambien_recupera_alternativa_kinesis(corpus):
    fila = {
        "propuesta": {"disciplinas_propuestas": ["biologia"]},
        "consulta_recuperacion": "taxis kinesis animal responses stimuli directed movement",
    }
    fuentes = buscar_fuentes(corpus, fila)
    assert any("undirected movement" in e.texto for e in fuentes)
    assert any("directed movement towards or away" in e.texto for e in fuentes)


def test_falta_de_consulta_no_se_disimula_con_resultados_genericos(corpus):
    with pytest.raises(ValueError, match="consulta bilingüe"):
        buscar_fuentes(corpus, {"propuesta": {"disciplinas_propuestas": ["quimica"]}})
