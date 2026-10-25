"""Contratos del etiquetado de conceptos V4 y de las trayectorias 2.°–11.° con datos sintéticos."""

from __future__ import annotations

import json

import pytest

from goes_science_kg.producto import conceptos_v4 as c4
from goes_science_kg.producto import progresion_v4 as p4

VOC = {
    "CON:fisica/fuerza": {"id": "CON:fisica/fuerza", "nombre": "Fuerza", "definicion": "d", "asignatura": "fisica"},
    "CON:fisica/energia": {"id": "CON:fisica/energia", "nombre": "Energía", "definicion": "d", "asignatura": "fisica"},
    "CON:biologia/celula": {
        "id": "CON:biologia/celula",
        "nombre": "Célula",
        "definicion": "d",
        "asignatura": "biologia",
    },
}
PRAC = {"PRAC:medir": {"id": "PRAC:medir", "nombre": "Medir", "definicion": "d"}}


def _item(id_, grado, disciplinas, procedimental, origen="original"):
    base = {"id": id_, "origen": origen, "grado": grado, "asignatura_malla": "Ciencias", "unidad": "U1"}
    base["disciplinas_catalogo"] = disciplinas
    if origen == "original":
        return base | {"contenido": "", "subcontenido": "", "procedimental": procedimental, "indicadores_logro": ""}
    return base | {"objetivo_propuesto": procedimental, "indicador_observable": ""}


def _lote():
    items = [_item("F1", 3, ["fisica"], "Empuje y fuerza en objetos"), _item("F2", 3, ["fisica"], "Energía del sol")]
    return c4.armar_lotes(items, VOC, PRAC, snapshot_id="s" * 64, por_lote=4)[0]


def _salida(**cambios):
    filas = [
        {"id": "F1", "conceptos": ["CON:fisica/fuerza"], "practicas": [], "evidencia": "fuerza en objetos"},
        {"id": "F2", "conceptos": ["CON:fisica/energia"], "practicas": ["PRAC:medir"], "evidencia": "Energía del sol"},
    ]
    for fila in filas:
        fila |= {"nuevos": [], "confianza": "alta", "justificacion": "Encaje directo."}
    filas[0] |= cambios
    return filas


def test_lote_limita_el_vocabulario_a_la_disciplina_catalogada():
    lote = _lote()
    assert {c["asignatura"] for c in lote["vocabulario"]} == {"fisica"}
    assert lote["lote"] == "v4_G03_fisica_1" and len(lote["items"]) == 2
    assert c4.errores_lote_v4(lote, _salida()) == []


@pytest.mark.parametrize(
    ("cambios", "mensaje"),
    [
        ({"conceptos": ["CON:biologia/celula"]}, "fuera del vocabulario"),
        ({"evidencia": "fuerza inventada"}, "fragmento literal"),
        ({"evidencia": ""}, "evidencia literal"),
        ({"conceptos": [], "practicas": []}, "sin conceptos"),
        ({"confianza": "total"}, "confianza"),
        ({"justificacion": "una " * 16}, "justificación"),
        ({"id": "OTRA"}, "ids ajenos"),
    ],
)
def test_validacion_rechaza_salidas_que_no_se_pueden_verificar(cambios, mensaje):
    assert any(mensaje in e for e in c4.errores_lote_v4(_lote(), _salida(**cambios)))


def test_evidencia_tolera_espacios_y_mayusculas_pero_no_otro_texto():
    assert c4.errores_lote_v4(_lote(), _salida(evidencia="FUERZA   en objetos")) == []


def test_lotes_mixtos_reciben_todo_el_vocabulario_y_no_se_sobrescriben(tmp_path):
    items = [_item("M1", 5, ["biologia", "fisica"], "Energía en la célula")]
    lote = c4.armar_lotes(items, VOC, PRAC, snapshot_id="s" * 64)[0]
    assert lote["lote"] == "v4_G05_mixta_1" and len(lote["vocabulario"]) == 3
    carpeta = tmp_path / "data" / "lotes_v4"
    c4.escribir_lotes([lote], carpeta)
    assert json.loads((carpeta / "lote_v4_G05_mixta_1.json").read_text())["items"][0]["id"] == "M1"
    with pytest.raises(ValueError, match="no se sobrescriben"):
        c4.escribir_lotes([lote], carpeta)


@pytest.mark.parametrize(
    ("grados", "esperado"),
    [([4], "aislado"), ([4, 5], "concentrado"), ([2, 3, 5, 6], "espiral"), ([2, 6], "intermitente")],
)
def test_patron_de_trayectoria(grados, esperado):
    assert p4.patron(grados) == esperado


def test_dominios_timss_en_orden_canonico():
    assert p4.dominios_timss("Razonar: justificar. Conocer: nombrar") == ("conocer", "razonar")
    assert p4.dominios_timss("") == ()


def _escenario():
    filas = {f"R{g}": {"grado": g, "dominios_timss": ("conocer",)} for g in (2, 3, 4, 7, 10)}
    etiquetas = [
        {"fila_id": "R2", "origen": "original", "conceptos": ["CON:fisica/energia"], "practicas": ["PRAC:medir"]},
        {"fila_id": "R3", "origen": "original", "conceptos": ["CON:fisica/energia"], "practicas": []},
        {"fila_id": "R4", "origen": "original", "conceptos": ["CON:fisica/fuerza"], "practicas": []},
        {"fila_id": "R7", "origen": "original", "conceptos": ["CON:fisica/energia"], "practicas": []},
        {"fila_id": "R10", "origen": "original", "conceptos": ["CON:fisica/fuerza"], "practicas": ["PRAC:medir"]},
        {"fila_id": "R10", "origen": "propuesta", "conceptos": ["CON:biologia/celula"], "practicas": []},
    ]
    return filas, etiquetas


def test_analisis_detecta_refuerzo_prerrequisito_tardio_y_transicion():
    filas, etiquetas = _escenario()
    # La fuerza (4.°) se declara prerrequisito de la energía, que aparece antes (2.°).
    aristas = [("CON:fisica/fuerza", "CON:fisica/energia"), ("CON:biologia/celula", "CON:fisica/fuerza")]
    vista = p4.analizar(filas, etiquetas, VOC, aristas, vista="original")
    energia = vista["conceptos"]["CON:fisica/energia"]
    assert energia["grados"] == [2, 3, 7] and energia["patron"] == "intermitente" and energia["max_hueco"] == 3
    assert vista["conceptos"]["CON:fisica/fuerza"]["patron"] == "intermitente"
    prer = vista["prerrequisitos"]
    assert [t["desfase"] for t in prer["tardias"]] == [2]
    ausente = prer["ausentes"][0]
    assert len(prer["ausentes"]) == 1 and ausente["prerrequisito"] == "CON:biologia/celula" and ausente["grado"] == 4
    assert ausente["nombre_prerrequisito"] == "Célula" and ausente["prerrequisito_solo_mencion"]
    fisica = vista["transicion_bachillerato"]["fisica"]
    assert fisica["conceptos_en_bachillerato"] == 1 and fisica["con_antecedente_2_9"] == 1
    g2 = next(g for g in vista["grados"] if g["grado"] == 2)
    assert g2["introducidos"] == 1 and g2["practicas"] == ["PRAC:medir"]


def test_vista_propuesta_reemplaza_solo_las_filas_precisadas():
    filas, etiquetas = _escenario()
    vista = p4.analizar(filas, etiquetas, VOC, [], vista="propuesta")
    assert vista["conceptos"]["CON:biologia/celula"]["grados"] == [10]
    assert vista["conceptos"]["CON:fisica/fuerza"]["grados"] == [4]
    with pytest.raises(ValueError):
        p4.asignaciones(etiquetas, "otra")


def test_acuerdo_con_v3_mide_consistencia_entre_pasadas():
    v4 = {"A": {"conceptos": ["CON:x", "CON:y"]}, "B": {"conceptos": ["CON:z"]}}
    v3 = {"a": {"conceptos": ["CON:x"]}, "b": {"conceptos": ["CON:w"]}}
    r = p4.acuerdo(v4, v3, [("a", "A"), ("b", "B"), ("c", "C")])
    assert r["pares_evaluados"] == 2 and r["principal_coincide"] == 0.5
    assert r["precision_vs_v3"] == pytest.approx(1 / 3, abs=1e-4) and r["exhaustividad_vs_v3"] == 0.5


def test_equivalencias_entre_disciplinas_unen_la_trayectoria():
    filas = {"A": {"grado": 3, "dominios_timss": ()}, "B": {"grado": 5, "dominios_timss": ()}}
    etiquetas = [
        {"fila_id": "A", "origen": "original", "conceptos": ["CON:quimica/estados"], "practicas": []},
        {"fila_id": "B", "origen": "original", "conceptos": ["CON:fisica/estados"], "practicas": []},
    ]
    eq = [("CON:quimica/estados", "CON:fisica/estados")]
    vista = p4.analizar(
        filas, etiquetas, {}, [("CON:quimica/estados", "CON:fisica/estados")], vista="original", equivalencias=eq
    )
    unido = vista["conceptos"]["CON:fisica/estados"]
    assert unido["grados"] == [3, 5] and unido["agrupa"] == ["CON:fisica/estados", "CON:quimica/estados"]
    assert vista["clases_equivalencia"] == 1 and vista["prerrequisitos"]["aristas_evaluables"] == 0


@pytest.mark.parametrize(
    ("nivel", "desfase", "confianza", "clase"),
    [
        ("primaria", 6, "alta", "introduccion_cualitativa"),
        ("secundaria", 2, "alta", "prioritaria"),
        ("bachillerato", 1, "alta", "revisar"),
        ("secundaria", 4, "media", "revisar"),
    ],
)
def test_clase_de_prerrequisito_tardio(nivel, desfase, confianza, clase):
    assert p4.clase_tardia(nivel, desfase, confianza) == clase


def test_claves_lexicas_descartan_palabras_genericas_y_aceptan_plurales():
    voc = {
        "CON:q/catalizadores": {"nombre": "Catalizadores", "sinonimos": ["catálisis"]},
        "CON:f/energia-cinetica": {"nombre": "Energía cinética", "sinonimos": []},
        "CON:f/energia-potencial": {"nombre": "Energía potencial y elástica", "sinonimos": []},
        "CON:q/lewis": {"nombre": "Notación y estructuras de Lewis", "sinonimos": []},
    }
    claves = p4.claves_lexicas(voc)
    assert "catalizadores" in claves["CON:q/catalizadores"] and "energia" not in claves["CON:f/energia-potencial"]
    assert "estructuras de lewis" in claves["CON:q/lewis"]
    textos = {"a": (6, p4.plano("Las enzimas como Catalizadores biológicos")), "b": (3, p4.plano("La energía"))}
    m = p4.menciones(textos, claves)
    assert m == {"CON:q/catalizadores": [6]}


def test_una_mencion_anterior_evita_un_falso_prerrequisito_tardio():
    conceptos = {
        "A": {"primera": 10, "nivel": "secundaria"},
        "B": {"primera": 6, "nivel": "secundaria"},
    }
    sin = p4.coherencia_prerrequisitos(conceptos, [("A", "B")], {("A", "B"): "alta"})
    con = p4.coherencia_prerrequisitos(conceptos, [("A", "B")], {("A", "B"): "alta"}, {"A": 5})
    assert len(sin["tardias"]) == 1 and con["tardias"] == [] and con["ordenadas"] == 1


def test_siglas_distintivas_cuentan_como_mencion():
    voc = {
        "CON:b/atp": {"nombre": "ATP y energía en los sistemas vivos", "sinonimos": []},
        "CON:b/adn": {"nombre": "Estructura del ADN", "sinonimos": []},
        "CON:b/rep": {"nombre": "Replicación del ADN", "sinonimos": []},
    }
    claves = p4.claves_lexicas(voc)
    assert "atp" in claves["CON:b/atp"] and "adn" not in claves["CON:b/adn"]
    assert p4.menciones({"f": (6, p4.plano("Formación de ATP"))}, claves) == {"CON:b/atp": [6]}


def test_prerrequisito_solo_mencionado_conserva_nombre_y_se_marca():
    filas = {
        "A": {"grado": 3, "dominios_timss": (), "texto": p4.plano("Estructura y función de las enzimas")},
        "B": {"grado": 9, "dominios_timss": (), "texto": p4.plano("Los catalizadores aceleran reacciones")},
    }
    etiquetas = [{"fila_id": "A", "origen": "original", "conceptos": ["CON:b/enzimas"], "practicas": []}]
    voc = {
        "CON:b/enzimas": {"nombre": "Enzimas", "asignatura": "biologia", "nivel": "secundaria"},
        "CON:q/catalizadores": {"nombre": "Catalizadores", "asignatura": "quimica", "nivel": "secundaria"},
    }
    vista = p4.analizar(filas, etiquetas, voc, [("CON:q/catalizadores", "CON:b/enzimas")], vista="original")
    tardia = vista["prerrequisitos"]["tardias"][0]
    assert tardia["prerrequisito_solo_mencion"] and tardia["nombre_prerrequisito"] == "Catalizadores"
    assert tardia["grado_prerrequisito"] == 9
