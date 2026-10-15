"""Contrato de la proyección de refuerzo: evidencia y capacidades, sin inventar dominio.

Se contrasta la proyección con la entrega congelada, no con datos del productor.
Las mutaciones adversariales se hacen exclusivamente en copias de memoria o tmp_path.
"""

from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path

import pytest

from goes_science_kg import grafo_refuerzo as refuerzo
from goes_science_kg.motor.archivos import canonico, firma, id_manifiesto, sha

ENTREGA = Path(__file__).resolve().parents[1] / "entregas/motor/0.2.0"


def _jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _consultar_ruta(datos, identificador):
    resultado = refuerzo.consultar(datos, identificador)
    assert "detalle" in resultado
    assert set(resultado["detalle"]) == {"secuencia", "criterios", "componentes"}
    return {k: v for k, v in resultado.items() if k != "detalle"}


@pytest.fixture(scope="module")
def fuente():
    return {name: _jsonl(ENTREGA / f"{name}.jsonl")
            for name in ("nodos", "relaciones", "temas", "secuencias", "componentes")}


@pytest.fixture(scope="module")
def datos():
    return refuerzo.compilar(ENTREGA)


def test_conserva_todos_los_nodos_y_relaciones_de_la_entrega(datos, fuente):
    """La proyección agrega una capa; no reescribe la evidencia científica/curricular."""
    nodos = {n["id"]: n for n in datos["nodos"]}
    aristas = {a["id"]: a for a in datos["aristas"]}
    assert len(fuente["nodos"]) == 3303
    assert len(fuente["relaciones"]) == 18177
    assert all(nodos[n["id"]] == n for n in fuente["nodos"])
    assert all(aristas[a["id"]] == a for a in fuente["relaciones"])


def test_cobertura_incluye_920_temas_y_cada_grado_aunque_falten_recursos(datos, fuente):
    rutas = datos["rutas"]
    esperados = {t["id"] for t in fuente["temas"] if t["en_alcance_ciencias"]}
    assert len(rutas) == len(esperados) == 920
    assert {r["tema_id"] for r in rutas} == esperados
    assert {r["grado"] for r in rutas} == set(range(2, 12))
    assert all(r["alumno_sin_evidencia"] is True for r in rutas)
    assert all("evaluacion_objetivo" in r and "bases" in r for r in rutas)
    assert any(r["evaluacion_objetivo"]["pareja_autoria"] is None for r in rutas)


def test_identidad_grado_fuente_y_orden_provienen_del_catalogo(datos, fuente):
    temas = {t["id"]: t for t in fuente["temas"]}
    for r in datos["rutas"]:
        t = temas[r["tema_id"]]
        for key in ("grado", "asignatura", "orden", "fuente", "aliases"):
            assert r[key] == t[key], (r["tema_id"], key)


def test_retenciones_y_permisos_no_se_promueven_por_tener_ruta(datos, fuente):
    secuencias = {s["tema_id"]: s for s in fuente["secuencias"]}
    assert sum(s["autoria_asistida"] for s in secuencias.values()) == 444
    assert sum(not s["autoria_asistida"] for s in secuencias.values()) == 476
    for r in datos["rutas"]:
        s = secuencias[r["tema_id"]]
        for key in ("id", "estado", "autoria_asistida", "motivos_retencion", "tiempo_observado_min",
                    "aula_habilitada"):
            assert r["secuencia"][key] == s[key]
        assert r["secuencia"]["aula_habilitada"] is False
        assert r["secuencia"]["tiempo_observado_min"] is None


def test_componentes_y_dictamenes_de_secuencias_se_conservan_integros(datos, fuente):
    nodos = {n["id"]: n for n in datos["nodos"]}
    assert len(fuente["componentes"]) == 1547
    assert len(datos["nodos"]) == 3303 + 920 + 2760 + 1547
    for original in fuente["componentes"] + fuente["secuencias"]:
        assert nodos[original["id"]]["props"]["registro"] == original


def test_parejas_evaluan_el_objetivo_con_dos_actividades_aptas_del_grado(datos, fuente):
    componentes = {c["id"]: c for c in fuente["componentes"]}
    parejas = 0
    for r in datos["rutas"]:
        pareja = r["evaluacion_objetivo"]["pareja_autoria"]
        if pareja is None:
            continue
        parejas += 1
        assert pareja["objetivo"] != pareja["reevaluacion"]
        for aid in (pareja["objetivo"], pareja["reevaluacion"]):
            c = componentes[aid]
            assert c["tipo"] == "actividad" and c["usos"]["autoria"] is True
            assert c["contenido"]["rol"] == "objetivo"
            assert r["tema_id"] in c["contenido"]["evalua"]
            assert r["grado"] in c["contenido"]["grados"]
            assert c["contenido"]["formato"] != "abierta"
            assert all(componentes[dep]["usos"]["autoria"] for dep in c["componentes_requeridos"])
    assert parejas > 0
    assert parejas < 920


def test_materiales_conservan_calidad_y_permisos_y_requieren_grado_explicito(datos, fuente):
    componentes = {c["id"]: c for c in fuente["componentes"]}
    for ruta in datos["rutas"]:
        for material in ruta["materiales"]:
            original = componentes[material["id"]]
            assert material["tipo"] == original["tipo"]
            assert material["usos"] == original["usos"]
            assert material["calidad"] == original["calidad"]
            grados = original["contenido"].get("grados")
            if grados and original["tipo"] in ("actividad", "microtema", "experimento"):
                assert ruta["grado"] in grados, (ruta["tema_id"], material["id"])


def test_cada_base_es_una_relacion_original_en_el_sentido_correcto(datos, fuente):
    aristas = {a["id"]: a for a in fuente["relaciones"]}
    for ruta in datos["rutas"]:
        for base in ruta["bases"]:
            arista = aristas[base["arista_id"]]
            assert arista["tipo"] == "PRERREQUISITO_DE"
            assert arista["origen"] == base["concepto"]
            assert arista["destino"] == base["para_concepto"]
            assert arista["confianza"] == base["confianza"]
            assert base["confianza"] in ("media", "alta")


def test_roles_y_confianza_del_foco_no_se_reinventan(datos, fuente):
    aristas = {a["id"]: a for a in fuente["relaciones"]}
    for ruta in datos["rutas"]:
        for foco in ruta["conceptos"] + ruta["practicas"]:
            arista = aristas[foco["arista_id"]]
            assert arista["tipo"] == "TRABAJA"
            assert arista["origen"] == ruta["tema_id"]
            assert arista["destino"] == foco["id"]
            assert arista["rol"] == foco["rol"]
            assert arista["confianza"] == foco["confianza"]


def test_criterios_propuestos_no_inventan_relacion_con_conceptos(datos):
    secuencias = [n for n in datos["nodos"] if n["tipo"] == "SecuenciaPropuesta"]
    criterios = [n for n in datos["nodos"] if n["tipo"] == "CriterioPropuesto"]
    assert len(secuencias) == 920
    assert len(criterios) == 2760
    ids = {n["id"] for n in criterios}
    assert set().union(*(set(r["criterios"]) for r in datos["rutas"])) == ids
    assert all(len(r["criterios"]) == 3 for r in datos["rutas"])
    assert not [a for a in datos["aristas"]
                if a["origen"] in ids and a["destino"].startswith("CON:")]
    assert not [a for a in datos["aristas"]
                if a["destino"] in ids and a["origen"].startswith("CON:")]


def test_criterios_conservan_texto_ia_y_anclaje_a_la_secuencia_sin_certificar_habilidad(datos, fuente):
    nodos = {n["id"]: n for n in datos["nodos"]}
    secuencias = {s["id"]: s for s in fuente["secuencias"]}
    manifiesto = json.loads((ENTREGA / "manifiesto.json").read_text(encoding="utf-8"))
    for ruta in datos["rutas"]:
        secuencia = secuencias[ruta["secuencia"]["id"]]
        for posicion, cid in enumerate(ruta["criterios"]):
            criterio = nodos[cid]
            props = criterio["props"]
            assert criterio["etiqueta"] == secuencia["criterios_evaluacion"][posicion]
            assert props["estado_mapeo"] == "mapeo_pendiente"
            assert props["evalua"] == []
            procedencia = props["procedencia"]
            assert procedencia["archivo"] == "secuencias.jsonl"
            assert procedencia["registro_id"] == secuencia["id"]
            assert procedencia["campo"] == f"criterios_evaluacion[{posicion}]"
            assert procedencia["id_entrega"] == manifiesto["id_entrega"]
            assert procedencia["sha256"] == manifiesto["archivos"]["secuencias.jsonl"]["sha256"]


def test_objetivos_metodologicos_sin_concepto_principal_siguen_consultables(datos, fuente):
    principales = {a["origen"] for a in fuente["relaciones"]
                   if a["tipo"] == "TRABAJA" and a["destino"].startswith("CON:")
                   and a["rol"] == "principal"}
    sin_principal = [r for r in datos["rutas"] if r["tema_id"] not in principales]
    assert len(sin_principal) == 6
    for ruta in sin_principal:
        assert ruta["tipo_objetivo"] == "practica_metodologica"
        assert ruta["practicas"]
        assert not [c for c in ruta["conceptos"] if c["rol"] == "principal"]
        assert _consultar_ruta(datos, ruta["tema_id"]) == ruta


def test_proyeccion_compartida_no_contiene_perfiles_ni_estados_de_alumnos(datos):
    prohibidos = {"Perfil", "Estudiante", "EstadoAlumno", "EvidenciaAlumno", "HipotesisAlumno"}
    assert not [n for n in datos["nodos"] if n["tipo"] in prohibidos]
    assert all(r["alumno_sin_evidencia"] is True for r in datos["rutas"])
    assert all("estudiante_id" not in r and "perfil_individual" not in r for r in datos["rutas"])


def test_cola_prioriza_carencias_de_oferta_sin_declarar_deficit_del_alumno(datos):
    temas = {r["tema_id"] for r in datos["rutas"]}
    cola = datos["cola"]
    assert cola
    assert [e["impacto_estructural"] for e in cola] == sorted(
        (e["impacto_estructural"] for e in cola), reverse=True)
    for posicion, entrada in enumerate(cola, 1):
        assert entrada["prioridad"] == posicion
        assert entrada["estado"] == "candidato_a_revisar"
        assert entrada["recomendacion_firme"] is False
        assert len(entrada["temas_afectados"]) == len(set(entrada["temas_afectados"]))
        assert entrada["impacto_estructural"] == len(entrada["temas_afectados"])
        assert set(entrada["temas_afectados"]) <= temas
    sin_instrumento = {r["tema_id"] for r in datos["rutas"]
                      if r["evaluacion_objetivo"]["pareja_autoria"] is None}
    en_cola = set().union(*(set(e["temas_afectados"]) for e in cola
                            if e["tipo"] == "falta_evaluacion_objetivo"))
    assert sin_instrumento <= en_cola


def test_sondeo_unico_o_recurso_bloqueado_no_ocultan_la_necesidad_de_autoria(datos, fuente):
    componentes = {c["id"]: c for c in fuente["componentes"]}
    cola_sondeos = {(e["clave"], tema) for e in datos["cola"] if e["tipo"] == "falta_sondeo"
                    for tema in e["temas_afectados"]}
    cola_microtemas = {(e["clave"], tema) for e in datos["cola"] if e["tipo"] == "falta_microtema"
                       for tema in e["temas_afectados"]}
    insuficientes = 0
    for ruta in datos["rutas"]:
        for base in ruta["bases"]:
            clave = f"{ruta['grado']}:{base['concepto']}"
            aptos = base["sondeos_cerrados_autoria"]
            assert len(aptos) == len(set(aptos))
            for aid in aptos:
                c = componentes[aid]
                assert c["usos"]["autoria"] is True
                assert ruta["grado"] in c["contenido"]["grados"]
                assert base["concepto"] in c["contenido"]["evalua"]
                assert c["contenido"]["formato"] != "abierta"
            if len(aptos) < 2:
                insuficientes += 1
                assert (clave, ruta["tema_id"]) in cola_sondeos
            if not any(x["autoria"] and not x["requiere_evaluador"] for x in base["refuerzos_completos"]):
                assert (clave, ruta["tema_id"]) in cola_microtemas
    assert insuficientes > 0


def test_propuestas_curriculares_se_separan_de_material_del_alumno(datos, fuente):
    componentes = {c["id"]: c for c in fuente["componentes"]}
    casos = 0
    for ruta in datos["rutas"]:
        assert all(m["tipo"] != "refuerzo" for m in ruta["materiales"])
        for propuesta in ruta["propuestas_curriculares"]:
            casos += 1
            original = componentes[propuesta["id"]]
            assert original["tipo"] == "refuerzo"
            assert propuesta["grados_destino"] == (original["contenido"].get("grados_destino")
                                                     or original["contenido"].get("grados", []))
            assert propuesta["usos"] == original["usos"]
    assert casos > 0


def test_actividad_asociada_al_tema_que_no_lo_evalua_no_sirve_para_la_pareja(tmp_path):
    """Una asociación sirve_a no reemplaza la arista evalua para atribuir evidencia."""
    entrega = tmp_path / "fuente_adversarial"
    shutil.copytree(ENTREGA, entrega)
    archivo = entrega / "componentes.jsonl"
    componentes = _jsonl(archivo)
    tema = "TEMA:G03-CIE-U1-1.3"
    actividad = next(c for c in componentes if c["id"] == "ACT:G03-CIE-U1-1.3/obj-1")
    actividad["contenido"]["evalua"].remove(tema)
    archivo.write_text("".join(canonico(c) + "\n" for c in componentes), encoding="utf-8")
    manifest_path = entrega / "manifiesto.json"
    manifiesto = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifiesto["archivos"][archivo.name]["sha256"] = sha(archivo)
    manifiesto["archivos"][archivo.name]["bytes"] = archivo.stat().st_size
    manifiesto["id_entrega"] = id_manifiesto(manifiesto)
    manifest_path.write_text(canonico(manifiesto) + "\n", encoding="utf-8")
    proyeccion = refuerzo.compilar(entrega)
    ruta = next(r for r in proyeccion["rutas"] if r["tema_id"] == tema)
    assert ruta["evaluacion_objetivo"]["pareja_autoria"] is None


def test_ninguna_arista_tiene_extremos_inexistentes_ni_identidad_duplicada(datos):
    ids = [n["id"] for n in datos["nodos"]]
    aids = [a["id"] for a in datos["aristas"]]
    assert len(ids) == len(set(ids))
    assert len(aids) == len(set(aids))
    existentes = set(ids)
    assert all(a["origen"] in existentes and a["destino"] in existentes for a in datos["aristas"])
    refuerzo.validar(datos)


@pytest.mark.parametrize("coleccion", ["nodos", "aristas", "rutas"])
def test_validador_rechaza_identidades_duplicadas(datos, coleccion):
    alterados = copy.deepcopy(datos)
    alterados[coleccion].append(copy.deepcopy(alterados[coleccion][0]))
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_validador_rechaza_arista_a_un_concepto_inexistente(datos):
    alterados = copy.deepcopy(datos)
    alterados["aristas"][0]["destino"] = "CON:auditoria/inexistente"
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_validador_rechaza_cambiar_relacion_propuesta_por_prerrequisito(datos):
    alterados = copy.deepcopy(datos)
    arista = next(a for a in alterados["aristas"] if a["tipo"] == "DEFINE_CRITERIO")
    arista["tipo"] = "PRERREQUISITO_DE"
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_validador_rechaza_modificar_la_capa_base(datos, fuente):
    alterados = copy.deepcopy(datos)
    nodo = next(n for n in alterados["nodos"] if n["id"] == fuente["nodos"][0]["id"])
    nodo["etiqueta"] = "Afirmación reemplazada sin fuente"
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_sha_del_manifiesto_fuente_no_se_sustituye_por_una_huella_auxiliar(datos, fuente):
    """Actualizar un checksum derivado no autoriza reemplazar la fuente congelada."""
    alterados = copy.deepcopy(datos)
    nodo = next(n for n in alterados["nodos"] if n["id"] == fuente["nodos"][0]["id"])
    nodo["etiqueta"] = "Etiqueta reemplazada y huella auxiliar recalculada"
    meta = alterados["metadatos"]
    ids_base = set(meta["nodos_base_ids"])
    nodos_base = sorted((n for n in alterados["nodos"] if n["id"] in ids_base), key=lambda n: n["id"])
    meta["huellas_colecciones_fuente"]["nodos"] = firma(nodos_base)
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_validador_rechaza_promover_permiso_de_aula(datos):
    alterados = copy.deepcopy(datos)
    alterados["rutas"][0]["secuencia"]["aula_habilitada"] = True
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_validador_rechaza_reutilizar_diagnostico_como_reevaluacion(datos):
    alterados = copy.deepcopy(datos)
    ruta = next(r for r in alterados["rutas"] if r["evaluacion_objetivo"]["pareja_autoria"])
    pareja = ruta["evaluacion_objetivo"]["pareja_autoria"]
    pareja["reevaluacion"] = pareja["objetivo"]
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


@pytest.mark.parametrize("cambio", ["tipo", "texto", "mapeo", "fuente"])
def test_validador_rechaza_criterio_reclasificado_o_cita_inventada(datos, cambio):
    alterados = copy.deepcopy(datos)
    criterio = next(n for n in alterados["nodos"] if n["tipo"] == "CriterioPropuesto")
    if cambio == "tipo":
        criterio["tipo"] = "Concepto"
    elif cambio == "texto":
        criterio["etiqueta"] = "Domina todas las competencias de ciencias"
    elif cambio == "mapeo":
        criterio["props"]["evalua"] = ["CON:fisica/presion"]
    else:
        criterio["props"]["procedencia"]["campo"] = "malla.criterio_inexistente"
    with pytest.raises(ValueError):
        refuerzo.validar(alterados)


def test_aliases_se_resuelven_por_puente_exacto_y_no_por_prefijo(datos):
    ruta = next(r for r in datos["rutas"] if r["aliases"])
    assert _consultar_ruta(datos, ruta["tema_id"]) == ruta
    assert _consultar_ruta(datos, ruta["tema_id"].removeprefix("TEMA:")) == ruta
    for alias in ruta["aliases"]:
        assert _consultar_ruta(datos, alias) == ruta
    with pytest.raises(ValueError):
        refuerzo.consultar(datos, "NM26-G99-CIE-U1-1.1")


def test_modificar_una_consulta_no_modifica_la_capa_compartida(datos):
    copia = copy.deepcopy(datos)
    tema = copia["rutas"][0]["tema_id"]
    resultado = refuerzo.consultar(copia, tema)
    resultado["detalle"]["secuencia"]["aula_habilitada"] = True
    resultado["detalle"]["criterios"][0]["etiqueta"] = "Criterio reemplazado por el consumidor"
    assert copia == datos
    refuerzo.validar(copia)


def test_exportacion_roundtrip_repetible_y_destino_inmutable(tmp_path, datos):
    uno, dos = tmp_path / "uno", tmp_path / "dos"
    assert Path(refuerzo.exportar(uno, ENTREGA)) == uno
    assert refuerzo.cargar(uno) == datos
    refuerzo.exportar(dos, ENTREGA)
    bytes_uno = {p.name: p.read_bytes() for p in uno.iterdir() if p.is_file()}
    assert bytes_uno == {p.name: p.read_bytes() for p in dos.iterdir() if p.is_file()}
    refuerzo.exportar(uno, ENTREGA)
    assert bytes_uno == {p.name: p.read_bytes() for p in uno.iterdir() if p.is_file()}
    payload = next(p for p in uno.iterdir() if p.name != "manifiesto.json" and p.is_file())
    payload.write_bytes(payload.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        refuerzo.cargar(uno)
    with pytest.raises((ValueError, FileExistsError)):
        refuerzo.exportar(uno, ENTREGA)
