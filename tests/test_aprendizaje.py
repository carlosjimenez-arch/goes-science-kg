"""Sistema de apoyo al aprendizaje (spec 13): relaciones inversas, diagnóstico por hipótesis, límites del refuerzo,
vínculo con los objetivos y separación entre el estado individual y el conocimiento compartido."""

import hashlib
import json
from datetime import date

import pytest

from goes_science_kg.aprendizaje import diagnostico
from goes_science_kg.aprendizaje.estudiante import Almacen, Evidencia, Perfil
from goes_science_kg.aprendizaje.pedagogia import Pedagogia, errores_capa, errores_lote, navegador_compartido
from goes_science_kg.aprendizaje.recorridos import RECORRIDOS, correr, errores_inversas, escribir_recorridos
from goes_science_kg.aprendizaje.relaciones import RELACIONES, antes_en_la_malla
from goes_science_kg.config import cargar, ruta


@pytest.fixture(scope="module")
def nav():
    return navegador_compartido()


@pytest.fixture(scope="module")
def ped():
    return Pedagogia.cargar()


def _huella(*carpetas: str) -> str:
    h = hashlib.sha256()
    for c in carpetas:
        for p in sorted(ruta(c).rglob("*")):
            if p.is_file():
                h.update(p.as_posix().encode() + p.read_bytes())
    return h.hexdigest()


# -- bidireccionalidad A: recorrido del grafo ----------------------------------------------------------------------
def test_cada_relacion_tiene_inversa_explicita_y_solo_equivalencia_es_simetrica():
    for r in RELACIONES.values():
        assert r.inversa and r.significado
        assert r.simetrica == (r.nombre == r.inversa)
    assert [r.nombre for r in RELACIONES.values() if r.simetrica] == ["equivale_a"]


def test_las_inversas_leen_la_misma_arista_en_los_dos_sentidos(nav):
    assert errores_inversas(nav) == []


def test_bases_distinguen_lo_que_la_malla_ensena_despues(nav):
    por = {b.concepto: b for b in nav.bases("TEMA:G09-CIE-U2-2.4")}
    pvt = por["CON:fisica/relaciones-presion-volumen-temperatura-gases"]
    assert pvt.profundidad == 1 and not pvt.antes_del_objetivo            # la malla la trabaja en el mismo tema
    assert por["CON:fisica/temperatura-medicion-escalas"].antes_del_objetivo
    assert all(b.estado_relacion == "propuesta_ia_pendiente" for b in por.values())   # nada se da por revisado
    eq = {b.concepto: b for b in nav.bases("TEMA:G09-CIE-U3-3.6")}["CON:quimica/equilibrio-dinamico"]
    assert eq.antes_del_objetivo and eq.primer_tema == "TEMA:G09-CIE-U3-3.1"   # mismo grado, tema anterior


def test_orden_de_la_malla():
    assert antes_en_la_malla("TEMA:G09-CIE-U3-3.1", "TEMA:G09-CIE-U3-3.6")
    assert not antes_en_la_malla("TEMA:G09-CIE-U2-2.7", "TEMA:G09-CIE-U2-2.4")
    assert not antes_en_la_malla("TEMA:G10-QUI-U1-1.1", "TEMA:G10-FIS-U2-2.1")   # asignaturas en paralelo


def test_apoya_es_el_recorrido_inverso_de_bases(nav):
    for b in nav.bases("TEMA:G09-CIE-U8-8.2", profundidad=1):
        temas = {f["tema"] for f in nav.apoya(b.concepto, profundidad=1)}
        assert "TEMA:G09-CIE-U8-8.2" in temas


# -- capa pedagógica ------------------------------------------------------------------------------------------------
def test_capa_pedagogica_integra_y_vinculada_a_objetivos(nav, ped):
    assert ped.actividades, "la capa pedagógica de los recorridos debe existir"
    assert errores_capa(ped, nav) == []
    assert all(a["objetivos"] and all(t.startswith("TEMA:") for t in a["objetivos"]) for a in ped.actividades.values())
    estados = {x["estado"] for x in [*ped.actividades.values(), *ped.dificultades.values(), *ped.microtemas.values()]}
    assert estados <= {"propuesta_pendiente", "verificado"}
    assert all(x.get("revisado_por") for x in ped.actividades.values() if x["estado"] == "verificado")


def test_lote_rechaza_una_salida_invalida(nav, ped):
    lote = json.loads(next(ruta("data/pedagogia/lotes").glob("lote_*.json")).read_text(encoding="utf-8"))
    salida = json.loads(ruta(f"data/pedagogia/lotes/salida_{lote['lote']}.json").read_text(encoding="utf-8"))
    assert errores_lote(lote, salida, nav, Pedagogia()) == []
    rota = [{**salida[0], "estado": "verificado", "objetivos": []}] + salida[1:-1]
    errores = errores_lote(lote, rota, nav, Pedagogia())
    assert any("propuesta_pendiente" in e for e in errores) and any("ranura sin llenar" in e for e in errores)


# -- bidireccionalidad B: retroalimentación ------------------------------------------------------------------------
def test_una_respuesta_incorrecta_no_cambia_las_bases(nav, ped):
    objetivo = "TEMA:G09-CIE-U8-8.2"
    act = ped.actividades["ACT:G09-CIE-U8-8.2/obj-1"]
    perfil = Perfil("t", 9)
    previas = {c: diagnostico.previa(nav, objetivo, c) for c in act["evalua"]}
    ev = Evidencia("E1", "2026-10-12", act["id"], objetivo, act["evalua"], "x", False)
    perfil.observar(ev, act["formato"], previas)
    assert set(perfil.conceptos) == {c for c in act["evalua"] if c.startswith("CON:")}   # solo lo evaluado
    hs = diagnostico.abrir(perfil, nav, ped, objetivo, act, ev, previas)
    assert hs and all(h.estado == "abierta" for h in hs)                                 # hipótesis, no brechas
    assert all(h.concepto not in perfil.conceptos for h in hs if h.tipo == "base")


def test_confirmar_exige_dos_evidencias(nav, ped):
    perfil = Perfil("t", 9)
    h = diagnostico.Hipotesis("H1", "TEMA:G09-CIE-U8-8.2", "CON:quimica/concentracion-de-disoluciones", "base",
                              "E0", 0.5)
    previas = {h.concepto: (0.6, "visto")}
    for i in (1, 2):
        ev = Evidencia(f"E{i}", "2026-10-12", "x", h.objetivo, [h.concepto], "x", False)
        perfil.observar(ev, "opcion_multiple", previas)
        h.evidencias.append(ev.id)
        estado = diagnostico.resolver(h, perfil)
        assert estado == ("abierta" if i == 1 else "confirmada")


# -- ciclo completo -------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("rec", RECORRIDOS, ids=lambda r: r["id"])
def test_recorrido_respeta_limites_vuelve_al_objetivo_y_registra_todo(rec, nav, ped, tmp_path):
    sesion, resumen = correr(rec, nav, ped, tmp_path)
    r = cargar("aprendizaje")["refuerzo"]
    assert resumen["refuerzos"] <= r["max_por_sesion"] and resumen["minutos_desvio"] <= r["minutos_max_por_sesion"]
    assert resumen["estado"] in ("logrado_provisional", "dominado")
    for i in sesion.perfil.intervenciones:
        assert i.objetivo == rec["objetivo"] and i.profundidad <= r["profundidad_maxima"]
        assert i.motivo and i.recurso and i.criterio and i.condicion_regreso and i.duracion_min > 0
    evaluaciones = [e for e in sesion.perfil.evidencias if rec["objetivo"] in e.evalua]
    assert len({e.actividad for e in evaluaciones}) == len(evaluaciones) >= 2     # reevalúa con OTRA actividad
    assert sesion.perfil.repasos                                                  # repaso posterior programado


def test_r3_descarta_las_bases_y_refuerza_el_objetivo(nav, ped, tmp_path):
    sesion, _ = correr(next(r for r in RECORRIDOS if r["id"] == "R3"), nav, ped, tmp_path)
    estados = {h.concepto.split("/")[-1]: h.estado for h in sesion.perfil.hipotesis}
    assert estados["equilibrio-dinamico"] == "descartada"
    assert estados["molaridad-y-unidades-quimicas-de-concentracion"] == "descartada"
    assert estados["constante-de-equilibrio"] == "confirmada"


def test_r2_activa_la_base_por_la_secuencia_de_la_malla_y_baja_a_profundidad_2(nav, ped, tmp_path):
    sesion, _ = correr(next(r for r in RECORRIDOS if r["id"] == "R2"), nav, ped, tmp_path)
    previo = next(i for i in sesion.perfil.intervenciones if i.momento == "previo")
    assert "secuencia de la malla" in previo.motivo
    assert any(i.profundidad == 2 and i.resultado == "cumplido" for i in sesion.perfil.intervenciones)


# -- separación de capas --------------------------------------------------------------------------------------------
def test_la_evidencia_de_un_estudiante_no_altera_el_conocimiento_compartido(tmp_path):
    antes = _huella("data/grafo", "data/pedagogia")
    escribir_recorridos(tmp_path / "recorridos")
    assert _huella("data/grafo", "data/pedagogia") == antes


@pytest.mark.parametrize("carpeta", ["data/grafo", "data/pedagogia", "data/grafo/grados"])
def test_el_estado_individual_no_puede_guardarse_en_una_capa_compartida(carpeta):
    with pytest.raises(ValueError):
        Almacen(ruta(carpeta))


def test_recorridos_deterministas(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    escribir_recorridos(a)
    escribir_recorridos(b)
    for p in sorted(a.iterdir()):
        assert p.read_bytes() == (b / p.name).read_bytes(), p.name


def test_repasos_espaciados():
    perfil = Perfil("t", 9)
    repasos = perfil.programar_repasos("TEMA:x", date(2026, 10, 12))
    assert [r.intervalo for r in repasos] == cargar("aprendizaje")["repaso"]["intervalos_dias"]
