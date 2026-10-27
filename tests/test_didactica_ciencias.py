"""Diseño contrastable: procedencia, semántica declarada y casos con cálculos independientes."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml
from pydantic import ValidationError
from test_curriculo_v4 import _mutar_libro
from test_curriculo_v4 import configuracion as configuracion

from goes_science_kg.curriculo.ingesta import cargar_curriculo
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import markdown
from goes_science_kg.produccion.didactica.casos import caso_para
from goes_science_kg.produccion.didactica.catalogo import extraer_tareas, perfil
from goes_science_kg.produccion.didactica.compilacion import enriquecer
from goes_science_kg.produccion.didactica.contratos import DisenoDidactico

BASE = Path(__file__).resolve().parents[1]
BANCO = yaml.safe_load((BASE / "config/casos_didacticos_ciencias.yaml").read_bytes())
CASOS = {c["id"]: c for c in BANCO["casos"]}


def test_extraccion_conserva_duplicados_fisicos_y_declara_codigos_desconocidos(configuracion):
    def cambiar(w):
        h = w["Unidad exacta "]
        h["H3"] = "E1 · Explica la medida. E99: Revisa el instrumento."
        h["I3"] = "E1 · Explica la medida."
        h["J3"] = "Sin consigna separable E3"

    _mutar_libro(configuracion, cambiar)
    c = cargar_curriculo(configuracion)
    tareas, incidencias = extraer_tareas(c.filas[0], c.fuentes[0], {})
    assert [t.codigo for t in tareas] == ["E1", "E99", "E1"]
    assert len({t.id for t in tareas}) == 3
    assert all(t.definicion is None for t in tareas)
    assert [t.origen.celdas for t in tareas] == [("H3",), ("H3",), ("I3",)]
    assert {i["codigo"] for i in incidencias} == {"CODIGO_SIN_DEFINICION", "CODIGO_SIN_CONSIGNA_SEPARABLE"}
    _mutar_libro(configuracion, lambda w: w["Unidad exacta "].merge_cells("H3:I3"))
    c = cargar_curriculo(configuracion)
    tareas, _ = extraer_tareas(c.filas[0], c.fuentes[0], {})
    assert len(tareas) == 2


@pytest.mark.parametrize("caso", BANCO["casos"], ids=lambda c: c["id"])
def test_casos_solo_aplican_a_captura_y_localizador_exactos(caso):
    destino = caso["destino"]
    f = SimpleNamespace(
        grado=destino["grado"],
        asignatura_malla=destino["asignatura"],
        hoja=destino["hoja"],
        fila=destino["fila"],
        id="fila-de-prueba",
    )
    actual = caso_para(f, BANCO["huella_curriculo"])
    assert actual["id"] == caso["id"] and actual["fila_id"] == f.id
    assert actual["desempeno_practico"] == "no_acreditado_por_el_caso_resuelto"
    assert caso_para(f, "0" * 64) is None
    f.hoja += " alterada"
    assert caso_para(f, BANCO["huella_curriculo"]) is None
    actual["datos"]["origen"] = "alteracion"
    assert caso["datos"]["origen"] != "alteracion"


def test_casos_cubren_cada_grupo_y_no_fingen_datos_de_campo():
    esperados = {(g, "Ciencias") for g in range(2, 10)}
    esperados |= {(g, a) for g in (10, 11) for a in ("Física", "Química", "Biología")}
    assert {(c["destino"]["grado"], c["destino"]["asignatura"]) for c in CASOS.values()} == esperados
    assert len(CASOS) == 14
    for c in CASOS.values():
        assert c["datos"]["origen"] in {
            "modelo_didactico_sintetico",
            "modelo_didactico_sintetico_ideal_sin_rozamiento",
            "ejemplos_conceptuales_documentales",
            "referencia_publicada_redondeada",
        }
        assert c["consignas"] and c["clave_docente"] and c["transferencia"] and c["seguridad"]


def test_claves_de_energia_y_conversion_no_confunden_fuerza_trabajo_ni_area():
    c = CASOS["energia_oscilador_11"]["datos"]
    k, m, a, e = (Decimal(str(c[x])) for x in ("constante_N_m", "masa_kg", "amplitud_m", "energia_mecanica_J"))
    assert k * a**2 / 2 == e == Decimal("0.5")
    for posicion in c["posiciones_m"]:
        potencial = k * Decimal(str(posicion)) ** 2 / 2
        assert potencial in (Decimal("0"), e) and e - potencial >= 0
    assert (2 * e / m).sqrt() == Decimal(2).sqrt()
    d = CASOS["medicion_si_5"]["datos"]
    assert Decimal(d["largo_cm"]) * Decimal(d["ancho_cm"]) / 10000 == Decimal("0.60")
    assert Decimal("6") * Decimal("0.2") == Decimal("2") * Decimal("0.6") == Decimal("1.2")


def test_claves_genoma_y_decision_con_restricciones():
    tablas = CASOS["genoma_ploidia_11"]["datos"]["tarjetas"]
    totales = [
        (
            t["juegos_en_celula_no_replicada"] * t["cromosomas_por_juego"],
            t["juegos_en_celula_no_replicada"] * t["ADN_Mb_por_juego"],
        )
        for t in tablas
    ]
    assert totales == [(8, 200), (8, 400), (16, 400)]
    datos = CASOS["materiales_electronica_11"]["datos"]

    def viables(costo):
        return [
            m["material"]
            for m in datos["muestras"]
            if m["costo_indice"] <= costo and m["resistencia_ohm"] <= 2 and m["requisito_union"] == "compatible"
        ]

    assert viables(3) == ["aleacion_B"]
    assert viables(4) == ["metal_A", "aleacion_B"]
    b = CASOS["biodiversidad_7"]["datos"]
    assert b["sitio_A"]["individuos"] > b["sitio_B"]["individuos"]
    assert b["sitio_A"]["especies"] < b["sitio_B"]["especies"]


def test_agua_global_no_equivale_a_oceanos_ni_potabilidad():
    d = CASOS["agua_global_3"]["datos"]
    assert d["porcentaje_agua_dulce"] + d["porcentaje_agua_salada_por_complemento"] == 100
    assert d["porcentaje_oceanos_mares_bahias"] < d["porcentaje_agua_salada_por_complemento"]
    assert d["unidades_modelo"] * d["porcentaje_agua_dulce"] / 100 == 5
    assert "potabilidad" in " ".join(CASOS["agua_global_3"]["clave_docente"])


@pytest.fixture(scope="module")
def nueva_entrega():
    p = BASE / "data/materiales_produccion_v4"
    if not (p / "manifest.json").exists():
        pytest.skip("Restaurar biblioteca de producción")
    b = Biblioteca(p)
    if b.manifest["procedencia"].get("version_diseno") != "preparacion-malla-final-2":
        p = BASE / "data/materiales_produccion_v4_didactica_v2"
        if not p.exists():
            pytest.skip("Construir la edición de diseño didáctico")
        b = Biblioteca(p)
    b.validar()
    rs, fs = b.exportar()
    return b, rs, fs


def test_contratos_rechazan_dominio_inventado_omisiones_y_cruces_de_criterios(nueva_entrega):
    _, rs, _ = nueva_entrega
    original = next(
        r["documento"]["didactica"]
        for r in rs
        if r["tipo"] == "paquete_objetivo" and len(r["documento"]["didactica"]["criterios"]) > 2
    )
    DisenoDidactico.model_validate(original)
    for cambiar in (
        lambda d: d.update(eficacia_observada=True),
        lambda d: d.update(alineacion_internacional_acreditada=True),
        lambda d: d["criterios"][0].update(logro_observado="dominado"),
        lambda d: d["criterios"].pop(),
        lambda d: d["criterios"][0]["tarea_ids"].append("otra-tarea"),
        lambda d: d.update(macrohabilidades=[]),
        lambda d: d["criterios"][0].update(codigo="I99"),
        lambda d: d["tareas"].append(deepcopy(d["tareas"][0])),
    ):
        d = deepcopy(original)
        cambiar(d)
        with pytest.raises(ValidationError):
            DisenoDidactico.model_validate(d)


def test_no_aplica_enriquecimiento_dos_veces(nueva_entrega):
    _, rs, fs = nueva_entrega
    from goes_science_kg.curriculo.contratos import Curriculo

    c = Curriculo.model_validate_json(fs["curriculo.json"])
    with pytest.raises(ValueError, match="dos veces"):
        enriquecer(rs, c, {}, sha_reglas="a" * 64, biblioteca_base="b" * 64)


@pytest.mark.parametrize(
    "grado,tramo",
    [(2, "2-4"), (4, "2-4"), (5, "5-6"), (6, "5-6"), (7, "7-9"), (9, "7-9"), (10, "10-11"), (11, "10-11")],
)
def test_apoyo_por_grado_sin_equivalencia_psicometrica(grado, tramo):
    assert perfil(grado)["tramo"] == tramo


def test_render_docente_preserva_alertas_y_no_publica_dump_tecnico(nueva_entrega):
    _, rs, _ = nueva_entrega
    for r in rs:
        md = markdown(r)
        assert "revisión de contenido pendiente" in md
        assert "```json" not in md
        if r["tipo"] == "paquete_objetivo":
            d = r["documento"]["didactica"]
            if d["caso_resuelto"]:
                assert "Clave razonada para el docente" in md
                assert d["caso_resuelto"]["datos"]["origen"] in md
            if d["controles_cientificos"]:
                assert "Originales bajo alerta" in md
            assert r["documento"]["original"]["procedimental"] in md


def test_banco_explicito_impide_reutilizar_configuracion_cacheada():
    caso = BANCO["casos"][0]
    d = caso["destino"]
    f = SimpleNamespace(grado=d["grado"], asignatura_malla=d["asignatura"], hoja=d["hoja"], fila=d["fila"], id="fila")
    assert caso_para(f, BANCO["huella_curriculo"])["id"] == caso["id"]
    assert (
        caso_para(f, BANCO["huella_curriculo"], banco={"huella_curriculo": BANCO["huella_curriculo"], "casos": []})
        is None
    )
