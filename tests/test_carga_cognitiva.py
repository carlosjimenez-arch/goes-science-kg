from copy import deepcopy

import pytest
from pydantic import ValidationError

from goes_science_kg.aprendizaje.carga_cognitiva import resumen_esfuerzo


def registro(id_, respuesta, **cambios):
    return {
        "registro_id": id_,
        "instrumento_id": "esfuerzo-local",
        "version": "piloto-1",
        "referencia": "protocolo-local-pendiente-de-validacion",
        "idioma": "es-SV",
        "pregunta": "¿Cuánto esfuerzo mental te exigió resolver esta tarea?",
        "escala": {"minimo": 1, "categorias": ["poco", "intermedio", "mucho"]},
        "grado": 5,
        "tarea": "suelo-comprobacion-A",
        "momento": "despues_de_responder_antes_de_retroalimentacion",
        "contexto_aplicacion": "piloto-local-sesion-A-material-suelo-v2",
        "ayuda_conceptual": False,
        "origen": "estudiante",
        "respuesta": respuesta,
        **cambios,
    }


def test_sin_respuestas_no_inventa_medicion_ni_carga_cero():
    vacio = resumen_esfuerzo()
    assert vacio["estado"] == "no_medido"
    assert vacio["grupos"] == []
    assert vacio["n_respuestas_reales"] == 0
    faltante = resumen_esfuerzo([registro("a", None)])
    assert faltante["estado"] == "no_medido"
    assert faltante["n_faltantes_reales"] == 1
    assert faltante["grupos"][0]["categorias_centrales"] is None


def test_simulaciones_no_mejoran_la_distribucion_real():
    datos = [registro("real", 3), registro("simulado", 1, origen="simulacion")]
    r = resumen_esfuerzo(datos)
    assert r["n_reales"] == 1 and r["n_simulados"] == 1
    assert r["grupos"][0]["categorias_centrales"] == [3, 3]
    assert [c["n"] for c in r["grupos"][0]["distribucion"]] == [0, 0, 1]
    solo = resumen_esfuerzo(datos[1:])
    assert solo["estado"] == "solo_simulado" and solo["grupos"] == []


@pytest.mark.parametrize(
    "cambio",
    [
        {"grado": 6},
        {"tarea": "suelo-comprobacion-B"},
        {"momento": "despues_de_retroalimentacion"},
        {"contexto_aplicacion": "otra-sesion-u-otra-version-del-material"},
        {"ayuda_conceptual": True},
        {"adaptaciones_acceso": ["lectura oral literal"]},
        {"version": "piloto-2"},
        {"idioma": "en"},
        {"pregunta": "¿Qué tan difícil te pareció?"},
        {"escala": {"minimo": 0, "categorias": ["bajo", "medio", "alto"]}},
    ],
)
def test_condiciones_no_comparables_no_se_agregan(cambio):
    r = resumen_esfuerzo([registro("a", 1), registro("b", 2, **cambio)])
    assert len(r["grupos"]) == 2
    assert [g["n_respuestas"] for g in r["grupos"]] == [1, 1]


def test_ordinal_conserva_las_categorias_centrales_sin_promedio_artificial():
    r = resumen_esfuerzo([registro("a", 1), registro("b", 3), registro("c", None)])
    grupo = r["grupos"][0]
    assert grupo["categorias_centrales"] == [1, 3]
    assert grupo["n_respuestas"] == 2 and grupo["n_faltantes"] == 1
    assert all(k not in r for k in ("eficacia", "porcentaje_carga", "sobrecarga", "aprendizaje"))


@pytest.mark.parametrize("respuesta", [True, "2", 1.5, float("nan"), -1, 4])
def test_rechaza_valores_que_no_son_categorias_validas(respuesta):
    with pytest.raises(ValidationError):
        resumen_esfuerzo([registro("a", respuesta)])


def test_no_cuenta_dos_veces_un_registro_y_rechaza_metadatos_ambiguos():
    r = registro("a", 2)
    with pytest.raises(ValueError, match="dos veces"):
        resumen_esfuerzo([r, deepcopy(r)])
    for cambios in (
        {"instrumento_id": " "},
        {"pregunta": ""},
        {"adaptaciones_acceso": [""]},
        {"escala": {"categorias": ["bajo", " BAJO "]}},
        {"origen": "modelo_estimando_esfuerzo"},
    ):
        with pytest.raises(ValidationError):
            resumen_esfuerzo([registro("a", 2, **cambios)])


def test_no_muta_registros_y_orden_de_adaptaciones_no_fabrica_grupos():
    a = registro("a", 1, adaptaciones_acceso=["lector", "ampliacion"])
    b = registro("b", 2, adaptaciones_acceso=["ampliacion", "lector"])
    original = deepcopy([a, b])
    resumen = resumen_esfuerzo([a, b])
    assert [a, b] == original
    assert len(resumen["grupos"]) == 1
