"""Bucle de fortalecimiento del panel (spec 14, sección 7): anclaje de citas por código, impugnación adversarial,
sonda ciega, réplica y solidez. Nada aquí llama a un modelo: las salidas de los subagentes se escriben a mano."""

from __future__ import annotations

import json

import pytest

from goes_science_kg import bucle, panel
from goes_science_kg.config import ruta

HK = "HK_Science_S1-3_CurriculumFramework_2025.pdf p. 60"
HK_CITA = "recognise that a solution is a mixture formed when a solute is dissolved in a solvent"


@pytest.fixture
def aislado(tmp_path, monkeypatch):
    """El estado y los lotes del panel y del bucle en tmp_path."""
    real = panel.ruta

    def falsa(rel):
        return tmp_path / rel if str(rel).startswith(panel.DIR) else real(rel)

    monkeypatch.setattr(panel, "ruta", falsa)
    monkeypatch.setattr(bucle, "ruta", falsa)
    return tmp_path


def _dic(i, decision, rol, ronda=1, confianza="alta", **extra):
    return {"id": i, "decision": decision, "justificacion": "Criterio técnico breve.", "confianza": confianza,
            "evidencia": [{"fuente": "criterio disciplinar", "cita": "argumento"}], "rol": rol, "ronda": ronda,
            **extra}


def _resuelto(tipo, roles, decision, **extra):
    return {"tipo": tipo, "titulo": "t", "pregunta": "p", "datos": {}, "roles": roles, "estado": "resuelta",
            "dictamenes": [_dic("?", decision, r) for r in roles], "resolucion": {"decision": decision, "ronda": 1},
            "aplicado": "2026-10-12", **extra}


def _escribir(carpeta, nombre, datos):
    (carpeta / nombre).write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")


def test_verificar_clasifica_y_ancla_en_la_fuente():
    tema = bucle.verificar("TEMA:G03-CIE-U3-3.5 (fila 7)", "Emplea un modelo de un acuífero para estudiar")
    assert tema["estado"] == "anclada" and "fila 7" in tema["donde"]
    assert bucle.verificar("TEMA:G03-CIE-U3-3.5", "un acuífero en 3.° grado")["estado"] == "ubicada"   # paráfrasis
    assert bucle.verificar("TEMA:G03-CIE-U3-3.5", "Acuíferos")["estado"] == "ubicada"   # muy corta para anclar
    falso = bucle.verificar("TEMA:G99-CIE-U3-3.5", "lo que sea")
    assert falso["estado"] == "inexistente" and falso["inexistentes"] == ["G99-CIE-U3-3.5"]
    assert bucle.verificar(HK, HK_CITA)["estado"] == "anclada"
    assert bucle.verificar("HK p. 60", HK_CITA.upper())["estado"] == "anclada"   # sin depender de mayúsculas
    # La página impresa no es la posición en el PDF (KR: 6 páginas de diferencia): la ventana la encuentra.
    assert bucle.verificar("KR p. 49", "평면거울에서 상이 생기는 원리를 설명하고")["estado"] == "anclada"
    assert bucle.verificar("internacional/2_8/README.md", HK_CITA)["tipo"] == "interna"   # circular
    # Un objetivo de país ancla con su original (aquí, el .ttl del Course of Study de Japón), no con la paráfrasis
    # en español que escribió el proyecto.
    jp = "JP-8361223413100000"
    assert bucle.verificar(jp, "En una reacción química la masa total de los reactivos es igual")["estado"] == "ubicada"
    assert bucle.verificar(jp, "反応物の質量の総和と生成物の質量の総和が等しい")["estado"] == "anclada"
    assert bucle.verificar("HK-BIO-hk_bio-p020-01", "compare the structure of prokaryotic cells")["estado"] == "anclada"
    assert bucle.verificar("criterio disciplinar", "x")["tipo"] == "argumento"
    assert bucle.verificar("Driver et al. (1994)", "x")["tipo"] == "literatura"


def _lote_refutador():
    return {"expedientes": [
        {"id": "A", "tipo": "decision", "opciones": ["aceptar", "rechazar"], "resolucion": {"decision": "aceptar"}},
        {"id": "B", "tipo": "hallazgo", "opciones": ["respaldar", "matizar", "no_respaldar"],
         "resolucion": {"decision": "respaldar"}}]}


def _ver(i, veredicto, **extra):
    return {"id": i, "veredicto": veredicto, "argumento": "Busqué en la fuente.", "confianza": "alta", **extra}


def test_el_refutador_solo_impugna_con_citas_que_estan_en_la_fuente():
    lote = _lote_refutador()
    contra = [{"fuente": HK, "cita_literal": HK_CITA, "dice": "HK lo enseña en el núcleo"}]
    bien = [_ver("A", "refutada", contraevidencia=contra, patron="conteo_de_paises", propuesta="rechazar"),
            _ver("B", "se_sostiene", anclas=contra)]
    assert bucle.errores_lote(lote, bien) == []
    inventada = [{"fuente": HK, "cita_literal": "students must memorise the periodic table by heart", "dice": "x"}]
    mal = [_ver("A", "refutada", contraevidencia=inventada, patron="conteo_de_paises", propuesta="aceptar"),
           _ver("B", "debilitada")]
    errores = " | ".join(bucle.errores_lote(lote, mal))
    for esperado in ("no aparece", "distinta de la resolución", "exige contraevidencia", "patrón"):
        assert esperado in errores
    circular = [{"fuente": "internacional/2_8/README.md", "cita_literal": HK_CITA, "dice": "x"}]
    assert "no es una fuente primaria" in " ".join(bucle.errores_lote(lote, [bien[0], _ver("B", "se_sostiene",
                                                                                              anclas=circular)]))


def test_en_contenido_refutar_exige_una_correccion_valida():
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    act = Pedagogia.cargar().actividades["ACT:G09-CIE-U8-8.2/obj-1"]
    lote = {"expedientes": [{"id": "P", "tipo": "contenido", "opciones": ["aprobar", "corregir"],
                             "resolucion": {"decision": "aprobar"}, "elemento_vigente": act,
                             "campos_editables": panel.config()["campos_editables"]["actividad"]}]}
    assert bucle.errores_lote(lote, [_ver("P", "refutada", patron="error_cientifico")])     # sin cambios
    assert bucle.errores_lote(lote, [_ver("P", "refutada", patron="error_cientifico", cambios={"correcta": "Z"})])
    assert bucle.errores_lote(lote, [_ver("P", "refutada", patron="error_cientifico",
                                          cambios={"retroalimentacion": "Más precisa."})]) == []


def test_vuelta_completa_impugnacion_replica_y_nueva_impugnacion(aislado):
    roles = ["experto-fisica", "psicopedagogo"]
    panel._guardar_estado({"X": _resuelto("hallazgo", roles, "respaldar"),
                           "Y": _resuelto("hallazgo", roles, "respaldar")})
    lotes = bucle.impugnar(1)
    assert [p.split("/")[-1] for p in lotes] == ["lote_b1_refutador_fisica.json"]
    d_b = aislado / bucle.DIR / "lotes"
    contra = [{"fuente": HK, "cita_literal": HK_CITA, "dice": "lo enseña antes"}]
    _escribir(d_b, "salida_b1_refutador_fisica.json", [
        _ver("X", "refutada", contraevidencia=contra, patron="grado_mal_mapeado", propuesta="matizar"),
        _ver("Y", "debilitada", confianza="baja", contraevidencia=contra, patron="otro")])   # baja: no reabre
    m = bucle.cerrar_impugnacion(1)
    assert m["impugnada"] == 1 and m["sostenida"] == 1
    e = panel.cargar_estado()
    assert e["X"]["bucle"]["vueltas"][0]["replica"] == "pendiente_paso_1"
    assert "replica" not in e["Y"]["bucle"]["vueltas"][0]
    bucle.replicar(1, 1)
    d_p = aislado / panel.DIR / "lotes"
    lote = json.loads((d_p / "lote_r11_experto-fisica.json").read_text(encoding="utf-8"))
    assert [x["id"] for x in lote["expedientes"]] == ["X"]
    assert lote["expedientes"][0]["impugnacion"]["contraevidencia"][0]["donde"].endswith("p. 60")
    for rol in roles:
        _escribir(d_p, f"salida_r11_{rol}.json", [{k: v for k, v in _dic("X", "matizar", rol, texto="Con matiz.")
                                                   .items() if k not in ("rol", "ronda")}])
    bucle.cerrar_replica(1, 1)
    x = panel.cargar_estado()["X"]
    assert x["resolucion"]["decision"] == "matizar" and x["historial_resoluciones"][0]["decision"] == "respaldar"
    assert x["aplicado"] is None and x["bucle"]["solidez"] == "fragil"   # cambió y aún no se volvió a impugnar
    # Vuelta 2: solo lo que cambió; se sostiene con una cita literal → sólido.
    assert [p.split("/")[-1] for p in bucle.impugnar(2)] == ["lote_b2_refutador_fisica.json"]
    _escribir(d_b, "salida_b2_refutador_fisica.json", [_ver("X", "se_sostiene", anclas=contra)])
    bucle.cerrar_impugnacion(2)
    s = bucle.solidez()
    assert s["hallazgo"] == {"solido": 1, "fragil": 1}   # Y: sobrevivió, pero sin fuente primaria
    with pytest.raises(ValueError, match="vueltas"):
        bucle.impugnar(bucle.config()["vueltas_max"] + 1)


def test_replica_sin_unanimidad_tras_deliberar_va_a_una_persona(aislado):
    roles = ["experto-quimica", "psicopedagogo"]
    x = _resuelto("propuesta", roles, "adoptar")
    x["bucle"] = {"vueltas": [{"vuelta": 1, "resultado": "impugnada", "replica": "pendiente_paso_1"}]}
    panel._guardar_estado({"X": x})
    d = aislado / panel.DIR / "lotes"
    for paso, (a, b) in ((1, ("adoptar", "descartar")), (2, ("adoptar", "descartar"))):
        bucle.replicar(1, paso)
        _escribir(d, f"salida_r1{paso}_experto-quimica.json", [{"id": "X", "decision": a, "justificacion": "j",
                                                                "evidencia": _dic("X", a, "")["evidencia"],
                                                                "confianza": "alta"}])
        _escribir(d, f"salida_r1{paso}_psicopedagogo.json", [{"id": "X", "decision": b, "justificacion": "j",
                                                              "evidencia": _dic("X", b, "")["evidencia"],
                                                              "confianza": "alta"}])
        bucle.cerrar_replica(1, paso)
    x = panel.cargar_estado()["X"]
    assert x["estado"] == "sin_consenso" and "sin unanimidad" in x["motivo"]
    assert x["bucle"]["solidez"] == "sin_consenso"


def test_la_sonda_ciega_no_ve_la_resolucion_y_su_discrepancia_reabre(aislado):
    panel._guardar_estado({f"D{i}": _resuelto("decision", ["experto-biologia"], "aceptar") for i in range(3)})
    lotes = bucle.sonda(1, n=2, semilla=1)
    lote = json.loads((ruta(lotes[0]) if not lotes[0].startswith(panel.DIR) else aislado / lotes[0])
                      .read_text(encoding="utf-8"))
    assert lote["ciega"] and all("resolucion" not in x and "dictamenes" not in x for x in lote["expedientes"])
    ids = [x["id"] for x in lote["expedientes"]]
    salida = [{"id": i, "decision": "rechazar" if i == ids[0] else "aceptar", "justificacion": "j",
               "alternativa": "otra", "evidencia": _dic(i, "", "")["evidencia"], "confianza": "media"} for i in ids]
    _escribir(aislado / panel.DIR / "lotes", "salida_c1_experto-biologia.json", salida)
    m = bucle.cerrar_impugnacion(1)
    assert m["sonda"] == {"decision": {"acuerdo": len(ids) - 1, "discrepa": 1}}
    assert panel.cargar_estado()[ids[0]]["bucle"]["vueltas"][0]["replica"] == "pendiente_paso_1"


def test_el_refutador_es_un_subagente_validado_por_el_hook():
    from goes_science_kg.lotes import AGENTES

    assert AGENTES["refutador"] == "bucle"
    assert "refutador" in ruta(".claude/settings.json").read_text(encoding="utf-8")
    texto = ruta(".claude/agents/refutador.md").read_text(encoding="utf-8")
    assert "prompts/bucle_refutar.md" in texto and "gskg bucle cita" in texto
    assert set(bucle.config()["patrones"]) >= {"evidencia_circular", "electiva_como_nucleo", "error_cientifico"}


def test_una_resolucion_posterior_supera_la_observacion_del_panel():
    r = {"observaciones": [{"revisado_por": "MINED", "comentario": "humana"}]}
    panel._observacion_del_panel(r, {"decision": "rechazar", "fecha": "2026-10-12", "alternativa": "otra"})
    assert len(r["observaciones"]) == 2
    panel._observacion_del_panel(r, {"decision": "aceptar", "fecha": "2026-10-13"})
    assert r["observaciones"] == [{"revisado_por": "MINED", "comentario": "humana"}]   # la humana no se toca
    assert r["observaciones_superadas"][0]["superada"] == "2026-10-13"


def test_rechazar_una_asignacion_la_observa_sin_observar_toda_la_division():
    from goes_science_kg import revision_decisiones as rd

    d = {"asignaciones": {"internacional": {"OBJ-1": ["CON:x"]}},
         "observaciones_asignaciones": {"internacional::OBJ-1": {"comentario": "retirar la etiqueta"}},
         "dictamenes_panel": [{"decision": "aceptar", "solidez": "solido"}]}
    assert rd._estado_asignacion(d, "internacional::OBJ-1").startswith("observada")
    assert rd._estado(d) == "dictamen del panel: aceptar, sólido (pendiente de confirmar)"   # la división, no


def test_la_sonda_se_compara_con_la_resolucion_vigente():
    """Si la réplica corrige el dictamen y llega a lo que la sonda dictaminó a ciegas, eso corrobora (no es inestable);
    si la sonda discrepa de lo que quedó, el dictamen es inestable."""
    ancla = {"fuente": HK, "cita_literal": HK_CITA, "dice": "x", "vuelta": 1}

    def exp(final, ciega):
        x = _resuelto("clase_incierta", ["experto-fisica"], final)
        x["dictamenes"] = [{**_dic("?", final, "experto-fisica", ronda=11), "evidencia": [
            {"fuente": HK, "cita": HK_CITA}]}]
        x["resolucion"] = {"decision": final, "ronda": 11}
        x["bucle"] = {"anclas": [ancla], "vueltas": [
            {"vuelta": 1, "resultado": "impugnada", "replica": "cambiada",
             "impugnacion": {"veredicto": "se_sostiene"},
             "sonda": {"acuerdo": False, "dictamenes": [{"decision": ciega, "rol": "experto-fisica"}]}},
            {"vuelta": 2, "resultado": "sostenida", "impugnacion": {"veredicto": "se_sostiene"}}]}
        return x

    s, motivo = bucle._solidez(exp("adelantado", "adelantado"))
    assert s == "solido" and "sonda ciega" in motivo
    s, motivo = bucle._solidez(exp("alineado", "adelantado"))
    assert s == "respaldado" and motivo.startswith("inestable")


def test_los_objetivos_de_otros_paises_no_se_cuentan_en_los_grados_de_la_malla():
    x = _resuelto("asignacion", ["experto-quimica"], "aceptar")
    i_pais = "ASG:CON:quimica/configuracion-electronica::internacional::HK-QUI-hk_qui-p019-02"
    i_malla = "ASG:CON:quimica/configuracion-electronica::malla_v2::G10-QUI-U13-13.1"
    assert bucle.grados_de(i_pais, x) == [] and bucle.tramo_de(i_pais, x) == "9-11"
    assert bucle.grados_de(i_malla, x) == [10]
    h = _resuelto("hallazgo", ["experto-fisica"], "matizar",
                  datos={"titulo": "El efecto invernadero no se retoma en 9.°–11.°", "evidencia": "", "tramo": "9_11"})
    assert bucle.grados_de("HAL:x", h) == [9, 10, 11]
    h["datos"]["titulo"] = "Física nuclear tardía"
    assert bucle.grados_de("HAL:x", h) == [] and bucle.tramo_de("HAL:x", h) == "9-11"


def test_el_contraste_usa_las_etiquetas_revisadas():
    """El contraste lee el grafo principal con sus revisiones (data/interim/revisiones/), no el etiquetado crudo: la
    corrección del bucle que agrega epidemiología a 9.° (inmunidad colectiva, boletín del MINSAL) llega al contraste."""
    from goes_science_kg.ingesta.mallas import extraer
    from goes_science_kg.internacional.contraste import puntos_sv

    temas = {t.id: {"grado": t.grado} for t in extraer()}
    assert "G09-CIE-U9-9.1" in puntos_sv(temas)["CON:biologia/epidemiologia-y-control-de-brotes"]


def test_lo_sin_consenso_decidido_por_delegacion_queda_como_delegado():
    x = {**_resuelto("clase_incierta", ["experto-fisica"], "alineado"), "estado": "sin_consenso",
         "motivo": "confianza baja de experto-fisica"}
    assert bucle._solidez(x)[0] == "sin_consenso"
    x["decision_delegada"] = {"decision": "alineado", "justificacion": "regla del umbral", "evidencia": []}
    s, motivo = bucle._solidez(x)
    assert s == "delegada" and "pendiente de confirmar" in motivo
