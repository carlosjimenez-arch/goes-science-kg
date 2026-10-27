"""Auditoría acotada: identidad, citas, cobertura, campos protegidos y ausencia de aprendizaje inventado."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.produccion.revision_docente.contexto import factorizar, lotes_equilibrados
from goes_science_kg.produccion.revision_docente.contratos import DictamenLote, leer_ruta, validar_dictamen
from goes_science_kg.produccion.revision_docente.edicion import crear, validar_edicion
from goes_science_kg.produccion.revision_docente.ejecucion import guardar

BASE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def candidato():
    p = BASE / "data/materiales_produccion_v4"
    if not p.exists():
        pytest.skip("Restaurar la edición didáctica V2")
    b = Biblioteca(p)
    if b.manifest["procedencia"].get("version_diseno") != "preparacion-malla-final-2":
        b = Biblioteca(BASE / "data/materiales_produccion_v4_didactica_v2")
    rs, fs = b.exportar()
    cfg = yaml.safe_load((BASE / "config/completacion_mezclas_ciencias.yaml").read_bytes())
    nuevos = crear(rs, cfg, yaml.safe_load(fs["didactica/reglas.yaml"]), b.manifest["procedencia"]["snapshot_id"])
    return rs, nuevos, cfg


def test_completa_solo_derivacion_y_no_iguala_analisis_a_ejecucion(candidato):
    anteriores, nuevos, cfg = candidato
    por_id = {r["id"]: r for r in anteriores}
    assert len(nuevos) == 1128
    for r in nuevos:
        antes = por_id[r["id"]]["documento"]
        assert {k: v for k, v in r["documento"].items() if k != "edicion_docente"} == antes
        validar_edicion(r["documento"]["edicion_docente"])
    fila = next(r for r in nuevos if r["id"] == cfg["fila_id"])["documento"]
    assert fila["original"]["indicadores_logro"] == ""
    assert fila["original"]["evidencia_aprendizaje"] == ""
    assert all(not f["texto"] for f in fila["original"]["fases"].values())
    e = fila["edicion_docente"]
    assert e["indicador"] and e["producto"] and len(e["actividades"]) == 5
    assert {t["fase"] for t in e["actividades"]} == {"explorar", "explicar", "indagar", "reforzar"}
    assert all(t["origen_tarea_id"] is None for t in e["actividades"])
    assert e["completacion"]["original_intacto"] is True
    assert "sólo se evalúa interpretación" in e["actividades"][3]["texto"]
    assert "no ingerir" in e["seguridad"]


def test_lotes_cubren_todos_y_no_separan_unidades(candidato):
    _, nuevos, _ = candidato
    grupos = lotes_equilibrados(nuevos, [])
    assert len(grupos) == 5
    ids = [i["id"] for g in grupos for i in g["items"]]
    assert len(ids) == len(set(ids)) == 1128
    for g in grupos:
        presentes = {i["id"] for i in g["items"]}
        assert len(presentes) <= 230
        for i in g["items"]:
            if i["tipo"] == "paquete_unidad":
                assert set(i["edicion"]["filas_ids"]) <= presentes


def test_factorizacion_reversible_sin_resumen(candidato):
    _, nuevos, _ = candidato
    solicitud = lotes_equilibrados(nuevos, [])[0]
    f = factorizar(solicitud)

    def expandir(x):
        if isinstance(x, dict) and set(x) == {"$texto"}:
            return f["textos_compartidos"][x["$texto"]]
        if isinstance(x, dict) and set(x) == {"$valor"}:
            return expandir(f["valores_compartidos"][x["$valor"]])
        if isinstance(x, dict):
            return {k: expandir(v) for k, v in x.items()}
        if isinstance(x, list):
            return [expandir(v) for v in x]
        return x

    assert expandir(f["solicitud"]) == solicitud


def ejemplo():
    s = {
        "items": [{"id": "objetivo", "edicion": {"explicacion": "La mezcla se separa físicamente."}}],
        "fuentes": [
            {
                "id": "primaria",
                "texto": "Las mezclas pueden separarse\npor procesos físicos.",
                "fuente": {"url": "https://www.mined.gob.sv/primaria"},
            }
        ],
    }
    d = {
        "items": [
            {
                "id": "objetivo",
                "veredicto": "aprobar",
                "comprobacion": "La explicación conserva la separación física sin afirmar nuevas sustancias.",
                "respaldos": [{"fuente_id": "primaria", "cita": "Las mezclas pueden separarse por procesos físicos."}],
                "hallazgos": [],
            }
        ],
        "observaciones": "",
    }
    return s, d


def test_citas_normalizan_solo_espacios_y_se_exige_cobertura_exacta():
    s, d = ejemplo()
    validar_dictamen(DictamenLote.model_validate(d), s)
    for cambiar in (
        lambda x: x["items"][0].update(id="otro"),
        lambda x: x["items"].append(deepcopy(x["items"][0])),
        lambda x: x["items"][0]["respaldos"][0].update(cita="Las mezclas siempre son sustancias nuevas."),
        lambda x: x["items"][0].update(respaldos=[]),
        lambda x: x["items"][0].update(veredicto="abstener"),
    ):
        x = deepcopy(d)
        cambiar(x)
        with pytest.raises(ValueError):
            validar_dictamen(DictamenLote.model_validate(x), s)


@pytest.mark.parametrize(
    "ruta",
    [
        "original/contenido",
        "id",
        "actividades/0/origen_tarea_id",
        "caso_resuelto/fuentes/url",
        "criterios/0/logro_observado",
        "actividades/-1/texto",
        "__class__/__name__",
    ],
)
def test_revisor_no_puede_alterar_procedencia_o_crear_logro_observado(ruta):
    with pytest.raises((ValueError, KeyError, IndexError)):
        leer_ruta({"actividades": [{"id": "fija", "texto": "Consigna."}]}, ruta)


def test_ancla_no_permite_veto_sobre_otro_campo():
    s, d = ejemplo()
    i = d["items"][0]
    i.update(
        veredicto="vetar",
        hallazgos=[
            {
                "ruta": "explicacion",
                "ancla": "Texto que no existe",
                "problema": "El ejemplo no conserva el modelo científico.",
                "reemplazo": "Otro texto.",
                "respaldo": [],
            }
        ],
    )
    with pytest.raises(ValueError, match="ancla"):
        validar_dictamen(DictamenLote.model_validate(d), s)


def test_checkpoint_igual_no_gasta_otro_voto_y_otro_contenido_se_rechaza(tmp_path):
    p = tmp_path / "lectura.json"
    guardar(p, {"voto": "uno"})
    guardar(p, {"voto": "uno"})
    with pytest.raises(ValueError, match="checkpoint"):
        guardar(p, {"voto": "dos"})


def test_no_acepta_veredictos_de_eficacia_o_respuestas_de_estudiantes():
    _, d = ejemplo()
    d["items"][0]["logro_observado"] = "dominado"
    with pytest.raises(ValidationError):
        DictamenLote.model_validate(d)


def test_fuentes_de_un_lote_no_se_propagan_a_los_demas(candidato):
    _, nuevos, _ = candidato
    grupos = lotes_equilibrados(nuevos, [{"id": "comun", "texto": "fuente"}])
    grupos[0]["fuentes"].append({"id": "solo_primero", "texto": "fuente específica"})
    assert all(len(g["fuentes"]) == 1 for g in grupos[1:])


def test_ejecucion_recupera_votos_exactos_sin_repetir_proveedor(tmp_path):
    from goes_science_kg.produccion.revision_docente.ejecucion import ejecutar, proveedor_cfg

    s, d = ejemplo()
    s["lote"] = 0
    guardar(tmp_path / "preflight.json", {"safe_to_start": True})
    guardar(tmp_path / "ronda_1.json", [s])

    class Proveedor:
        llamadas = 0

        def generar(self, **kwargs):
            self.llamadas += 1
            return DictamenLote.model_validate(d)

    p = Proveedor()
    assert ejecutar([s], tmp_path, tmp_path / "no_crear_ledger", ronda=1, cfg=proveedor_cfg(), proveedor=p) == []
    assert p.llamadas == 4
    assert ejecutar([s], tmp_path, tmp_path / "no_crear_ledger", ronda=1, cfg=proveedor_cfg(), proveedor=p) == []
    assert p.llamadas == 4 and not (tmp_path / "no_crear_ledger").exists()


def test_streaming_reune_solo_texto_visible_y_hace_una_solicitud():
    from types import SimpleNamespace as N

    from goes_science_kg.produccion.revision_docente.streaming import ModeloStreaming

    class Modelos:
        llamadas = 0

        def generate_content_stream(self, **kwargs):
            self.llamadas += 1
            yield N(
                usage_metadata=None,
                candidates=[N(content=N(parts=[N(thought=True, text="interno"), N(thought=False, text="{")]))],
            )
            yield N(
                usage_metadata=N(candidates_token_count=7, thoughts_token_count=5),
                candidates=[N(content=N(parts=[N(thought=False, text='"items":[]}')]))],
            )

    m = Modelos()
    config = N(automatic_function_calling=N(disable=True), max_output_tokens=65536)
    r = ModeloStreaming(m).generate_content(model="aprobado", contents="datos", config=config)
    assert r.text == '{"items":[]}' and m.llamadas == 1
    assert r.usage_metadata.thoughts_token_count == 5
    config.automatic_function_calling.disable = False
    with pytest.raises(ValueError):
        ModeloStreaming(m).generate_content(config=config)
    assert m.llamadas == 1


def test_transporte_compacto_mantiene_las_cotas_locales():
    import json

    from goes_science_kg.produccion.revision_docente.ejecucion import TRANSPORTE

    schema = json.dumps(TRANSPORTE.model_json_schema())
    assert "maxItems" not in schema and "minLength" not in schema
    _, d = ejemplo()
    d["items"][0]["comprobacion"] = "corta"
    with pytest.raises(ValidationError):
        TRANSPORTE.model_validate(d)


def seleccion_ejemplo():
    from goes_science_kg.produccion.revision_docente.procesamiento import numerar_fuentes

    s, _ = ejemplo()
    s["fuentes"][0]["identidad_original"] = "mined_primaria:pdf:48"
    s["items"].append({"id": "segundo", "edicion": {"explicacion": "Otra mezcla física."}})
    s = numerar_fuentes(s)
    salida = {
        "banco_citas": [{"id": "C0", "fuente_id": "primaria", "fragmento": 0}],
        "items": [
            {
                "id": i["id"],
                "veredicto": "aprobar",
                "comprobacion": "La explicación diferencia mezclas y sustancias sin cambiar la evidencia.",
                "respaldo_ids": ["C0"],
                "hallazgos": [],
            }
            for i in s["items"]
        ],
        "observaciones": "",
    }
    return s, salida


def test_fragmentos_no_pierden_ni_un_caracter_y_citas_son_literales():
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, fragmentar, procesar

    texto = "αβ mezcla\n   moléculas. " * 100
    partes = fragmentar(texto)
    assert "".join(partes) == texto
    assert max(map(len, partes)) <= 350
    s, d = seleccion_ejemplo()
    r = procesar(DictamenSeleccion.model_validate(d), s, "revision_ciencia")
    assert r["validacion_local"]["elementos_validos"] == 2
    assert r["dictamen"]["items"][0]["respaldos"][0]["cita"] == "".join(s["fuentes"][0]["fragmentos"])


@pytest.mark.parametrize("fallo", ["fuente", "indice", "duplicado", "ausente", "ruta"])
def test_error_aislado_no_fabrica_abstenciones_ni_aprobaciones(fallo):
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar

    s, d = seleccion_ejemplo()
    if fallo in {"fuente", "indice"}:
        d["banco_citas"].append(
            {
                "id": "mala",
                "fuente_id": "inventada" if fallo == "fuente" else "primaria",
                "fragmento": 999 if fallo == "indice" else 0,
            }
        )
        d["items"][0]["respaldo_ids"] = ["mala"]
    elif fallo == "duplicado":
        d["items"].append(deepcopy(d["items"][0]))
    elif fallo == "ausente":
        d["items"].pop(0)
    else:
        d["items"][0].update(
            veredicto="vetar",
            hallazgos=[
                {
                    "ruta": "original/explicacion",
                    "problema": "Esta ruta intenta modificar el original protegido.",
                    "reemplazo": "No permitido.",
                    "respaldo_ids": ["C0"],
                }
            ],
        )
    r = procesar(DictamenSeleccion.model_validate(d), s, "revision_ciencia")
    assert [i["id"] for i in r["dictamen"]["items"]] == ["segundo"]
    assert list(r["validacion_local"]["errores_por_item"]) == ["objetivo"]
    assert r["dictamen"]["items"][0]["veredicto"] == "aprobar"


def test_psicopedagogia_requiere_evidencia_de_diseno_educativo():
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar

    s, d = seleccion_ejemplo()
    s["fuentes"][0]["identidad_original"] = "ciencia_sin_principio_educativo"
    r = procesar(DictamenSeleccion.model_validate(d), s, "revision_psicopedagogia")
    assert not r["dictamen"]["items"]
    assert len(r["validacion_local"]["errores_por_item"]) == 2


def test_resumen_deja_pendiente_un_rol_invalido_y_rechaza_edicion_alterada(tmp_path):
    import json

    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.produccion.revision_docente.contratos import ROLES
    from goes_science_kg.produccion.revision_docente.correcciones import resumir
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar

    s, d = seleccion_ejemplo()
    s["lote"] = 0
    s["fuentes"][0]["fuente"] = {"url": "https://www.mined.gob.sv/primaria"}
    guardar(tmp_path / "ronda_1.json", [s])
    for rol in ROLES:
        elegido = deepcopy(d)
        if rol == "revision_ciencia":
            elegido["items"][0]["respaldo_ids"] = ["cita_inventada"]
        resultado = {
            "identidad": {"solicitud_sha256": sha(serializar(s)), "rol": rol, "modelo": "modelo-prueba"},
            **procesar(DictamenSeleccion.model_validate(elegido), s, rol),
        }
        guardar(tmp_path / "lecturas" / f"r1_l0_{rol}.json", resultado)
    registros = [{"id": i["id"], "documento": {"edicion_docente": i["edicion"]}} for i in s["items"]]
    r = resumir(registros, tmp_path)
    assert r["objetivo"]["faltan_roles"] == ["revision_ciencia"]
    assert r["objetivo"]["estado"] == "revision_automatica_con_pendientes"
    assert len(r["objetivo"]["lecturas"]) == 3
    assert r["segundo"]["estado"] == "revision_automatica_completa"
    registros[0]["documento"]["edicion_docente"]["explicacion"] = "Cambio después del voto"
    with pytest.raises(ValueError, match="difiere del contenido revisado"):
        resumir(registros, tmp_path)
    voto = tmp_path / "lecturas" / "r1_l0_revision_ciencia.json"
    falsificado = json.loads(voto.read_bytes())
    falsificado["validacion_local"]["errores_por_item"] = {}
    voto.write_bytes(serializar(falsificado))
    with pytest.raises(ValueError, match="no reproducen"):
        resumir(registros, tmp_path)


def test_vista_no_resume_contenido_docente_y_reemplaza_solo_identidades(candidato):
    from goes_science_kg.produccion.revision_docente.contexto import (
        codificar_identidades,
        lotes_equilibrados,
        vista_revision,
    )
    from goes_science_kg.produccion.revision_docente.procesamiento import numerar_fuentes

    _, registros, _ = candidato
    grupos = lotes_equilibrados(registros, [])
    assert len(grupos) == 5 and sum(len(s["items"]) for s in grupos) == 1128
    for s in grupos:
        presentes = {i["id"] for i in s["items"]}
        assert len(presentes) <= 230
        assert all(set(i["edicion"]["filas_ids"]) <= presentes for i in s["items"] if i["tipo"] == "paquete_unidad")
    s = numerar_fuentes(codificar_identidades(grupos[0]))
    v = vista_revision(s)
    for antes, despues in zip(s["items"], v["items"], strict=True):
        a, b = antes["edicion"], despues["edicion"]
        if "actividades" not in a:
            assert a["articulacion"] == b["articulacion"] and a["progresion"] == b["progresion"]
            continue
        for n, (x, y) in enumerate(zip(a["actividades"], b["actividades"], strict=True)):
            assert {k: z for k, z in x.items() if k not in {"id", "origen_tarea_id"}} == {
                k: z for k, z in y.items() if k != "id"
            }
            assert y["id"] == f"A{n}"
        for x, y in zip(a["criterios"], b["criterios"], strict=True):
            assert {k: z for k, z in x.items() if k != "tarea_ids"} == {k: z for k, z in y.items() if k != "tarea_ids"}
        for k in (
            "explicacion",
            "indicador",
            "producto",
            "perfil_apoyo",
            "rubrica",
            "seguridad",
            "aplicacion",
            "recuperacion",
        ):
            assert a[k] == b[k]
        if a["caso_resuelto"]:
            for k in ("datos", "consignas", "clave_docente", "contexto", "transferencia", "andamiaje"):
                assert a["caso_resuelto"][k] == b["caso_resuelto"][k]


def test_fallo_de_transporte_detiene_la_cola_sin_consumir_todos_los_lotes(tmp_path):
    from goes_science_kg.produccion.revision_docente.ejecucion import ejecutar, proveedor_cfg

    class ServerError(Exception):
        pass

    class Proveedor:
        llamadas = 0

        def generar(self, **kwargs):
            self.llamadas += 1
            raise ServerError("504 simulado")

    s, _ = ejemplo()
    s["lote"] = 0
    solicitudes = [s | {"lote": n} for n in range(5)]
    guardar(tmp_path / "preflight.json", {"safe_to_start": True})
    guardar(tmp_path / "ronda_1.json", solicitudes)
    p = Proveedor()
    errores = ejecutar(solicitudes, tmp_path, tmp_path / "no_crear", ronda=1, cfg=proveedor_cfg(), proveedor=p)
    assert errores and p.llamadas <= 4
    assert not (tmp_path / "no_crear").exists()


def test_voto_archivado_debe_existir_en_la_respuesta_real_del_ledger(tmp_path):
    import hashlib
    import json

    from goes_science_kg.clases.presupuesto import configuracion
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.produccion.revision_docente.auditoria import vincular
    from goes_science_kg.produccion.revision_docente.ejecucion import TRANSPORTE, mensaje, proveedor_cfg
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar
    from goes_science_kg.produccion.revision_docente.prompts import sistema

    s, salida = seleccion_ejemplo()
    s["lote"] = 0
    guardar(tmp_path / "ronda_1.json", [s])
    cfg = proveedor_cfg()
    rol = "revision_ciencia"
    m = mensaje(s)
    datos = [
        cfg.proyecto,
        cfg.region,
        cfg.modelos[rol],
        sistema(rol),
        m,
        TRANSPORTE.model_json_schema(),
        cfg.max_salida_tokens,
        {"thinking_level": cfg.niveles_razonamiento[rol]},
    ]
    clave = hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    ledger = tmp_path / "registro.sqlite"
    registro = Registro(ledger)
    llamada = registro.reservar(
        ejecucion=configuracion()["ejecucion"],
        clave=clave,
        modelo=cfg.modelos[rol],
        rol=rol,
        reserva_usd=0.1,
        max_llamadas=1,
        max_usd=1,
    )
    registro.guardar_salida(llamada, json.dumps(salida, ensure_ascii=False))
    registro.terminar(llamada, estado="completada", latencia_ms=1)
    identidad = {
        "ronda": 1,
        "lote": 0,
        "rol": rol,
        "modelo": cfg.modelos[rol],
        "nivel_razonamiento": cfg.niveles_razonamiento[rol],
        "solicitud_sha256": sha(serializar(s)),
        "mensaje_sha256": sha(m.encode()),
        "sistema_sha256": sha(sistema(rol).encode()),
        "transporte_sha256": sha(serializar(TRANSPORTE.model_json_schema())),
    }
    lectura = tmp_path / "lecturas" / "r1_l0_revision_ciencia.json"
    guardar(lectura, {"identidad": identidad, **procesar(DictamenSeleccion.model_validate(salida), s, rol)})
    assert vincular(tmp_path, ledger)["lecturas"][lectura.name]["llamada_id"] == llamada
    falsificado = json.loads(lectura.read_bytes())
    falsificado["salida_selecciones"]["items"][0]["comprobacion"] = (
        "Esta afirmación fue cambiada después de la llamada real."
    )
    lectura.write_bytes(serializar(falsificado))
    with pytest.raises(ValueError, match="no reproduce"):
        vincular(tmp_path, ledger)


def test_controles_negativos_no_filtran_la_clave_ni_se_convierten_en_paquetes(candidato):
    from goes_science_kg.produccion.revision_docente.calibracion import agregar, evaluar
    from goes_science_kg.produccion.revision_docente.contexto import (
        codificar_identidades,
        lotes_equilibrados,
        vista_revision,
    )
    from goes_science_kg.produccion.revision_docente.ejecucion import mensaje
    from goes_science_kg.produccion.revision_docente.procesamiento import numerar_fuentes

    _, registros, _ = candidato
    anteriores = deepcopy(registros)
    s = numerar_fuentes(codificar_identidades(lotes_equilibrados(registros, [])[0]))
    antes = len(s["items"])
    viejo = len(mensaje(s).encode())
    agregar(s, registros)
    assert registros == anteriores
    assert len(s["items"]) == antes + 3 <= 230
    assert len(mensaje(s).encode()) <= viejo * 1.05
    assert "controles_revision" not in vista_revision(s)
    assert "CONTROL_NEGATIVO" not in mensaje(s)
    assert len(s["controles_revision"]["claves"]) == 3
    votos = {
        rol: {
            "dictamen": {
                "items": [
                    {"id": id_, "veredicto": "aprobar", "hallazgos": []} for id_ in s["controles_revision"]["claves"]
                ]
            }
        }
        for rol in ("revision_ciencia", "revision_curriculo", "revision_psicopedagogia", "revision_adversarial")
    }
    assert all(not v["superado"] for v in evaluar(s, votos).values())
    for rol, voto in votos.items():
        for i in voto["dictamen"]["items"]:
            r = s["controles_revision"]["claves"][i["id"]]
            if rol in r["roles"]:
                i.update(
                    veredicto="vetar",
                    hallazgos=[
                        {
                            "ruta": r["rutas"][0] + "campo",
                            "problema": "Error intencional localizado: " + r["terminos"][0],
                        }
                    ],
                )
    assert all(v["superado"] for v in evaluar(s, votos).values())


def test_timeout_y_banco_de_evidencia_tienen_cotas_coherentes():
    from goes_science_kg.produccion.revision_docente.ejecucion import proveedor_cfg
    from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion

    cfg = proveedor_cfg()
    assert cfg.timeout_segundos == 1200 and cfg.reintentos == 0
    with pytest.raises(ValidationError):
        type(cfg).model_validate(cfg.model_dump() | {"timeout_segundos": 1201})
    _, d = seleccion_ejemplo()
    d["banco_citas"] = [{"id": str(i), "fuente_id": "primaria", "fragmento": 0} for i in range(690)]
    DictamenSeleccion.model_validate(d)
    d["banco_citas"].append({"id": "691", "fuente_id": "primaria", "fragmento": 0})
    with pytest.raises(ValidationError):
        DictamenSeleccion.model_validate(d)


def test_editar_derivacion_no_muta_la_edicion_historica_por_alias(candidato):
    _, nuevos, _ = candidato
    rs = deepcopy(nuevos)
    objetivo = next(r["documento"] for r in rs if r["tipo"] == "paquete_objetivo")
    anterior = deepcopy(objetivo["didactica"])
    objetivo["edicion_docente"]["perfil_apoyo"]["apoyo"] = "Ayuda propuesta diferente."
    objetivo["edicion_docente"]["aplicacion"]["contraste"] = "Otra comparación."
    objetivo["edicion_docente"]["rubrica"]["regla"] = "Otra regla."
    assert objetivo["didactica"] == anterior
    unidad = next(r["documento"] for r in rs if r["tipo"] == "paquete_unidad")
    antes = deepcopy(unidad["didactica_unidad"])
    unidad["edicion_docente"]["progresion"].append("Una propuesta derivada adicional.")
    assert unidad["didactica_unidad"] == antes


def test_recuperacion_parcial_conserva_objetos_exactos_y_no_inventa_la_fila_truncada():
    import json

    from goes_science_kg.produccion.revision_docente.recuperacion import extraer_prefijo

    _, d = seleccion_ejemplo()
    d["items"][0]["comprobacion"] = (
        'Un texto con llaves { } y la clave "items" no cambia la estructura ni la evidencia.'
    )
    prefijo = json.dumps({"banco_citas": d["banco_citas"], "items": d["items"]}, ensure_ascii=False)
    truncado = prefijo[:-2] + ', {"id":"tercero","veredicto":"apro'
    obtenido, meta = extraer_prefijo(truncado)
    assert obtenido.model_dump()["items"] == d["items"]
    assert meta["decisiones_completas"] == 2 and meta["votos_inventados"] == 0
    assert meta["observaciones_modelo_recibidas"] is False
    for i, r in enumerate(meta["rangos_decisiones"]):
        assert json.loads(truncado[r["inicio"] : r["fin"]]) == d["items"][i]
    with pytest.raises(ValueError):
        extraer_prefijo(json.dumps(d))
    with pytest.raises(ValueError):
        extraer_prefijo('{"banco_citas":[{"id":"R0","fuente_id":"incompleto')
    with pytest.raises(ValueError):
        extraer_prefijo('{"banco_citas":[],"items":[{"id":"incompleto')


def test_saldo_insuficiente_no_envia_y_cache_completa_reanuda_incluso_al_limite(tmp_path, monkeypatch):

    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.motor.vertex import clave_solicitud
    from goes_science_kg.produccion.revision_docente import ejecucion as ej
    from goes_science_kg.produccion.revision_docente.contratos import ROLES
    from goes_science_kg.produccion.revision_docente.prompts import sistema

    s, salida = seleccion_ejemplo()
    s["lote"] = 0
    guardar(
        tmp_path / "preflight.json",
        {"safe_to_start": True, "consumo_inicial": {"llamadas": 4000}, "max_nuevas_llamadas": 43},
    )
    guardar(tmp_path / "ronda_1.json", [s])
    ledger = tmp_path / "ledger.sqlite"
    reg = Registro(ledger)
    monkeypatch.setattr(ej, "comprobar_continuidad", lambda _: {"llamadas": 4000, "reserva_usd": 0})
    with pytest.raises(ValueError, match="saldo vigente"):
        ej.ejecutar([s], tmp_path, ledger, ronda=1)
    assert not (tmp_path / "intentos").exists()
    cfg = ej.proveedor_cfg()
    for rol in ROLES:
        clave = clave_solicitud(cfg, rol=rol, sistema=sistema(rol), mensaje=ej.mensaje(s), esquema=ej.TRANSPORTE)
        reg.guardar_cache(clave, salida)
    assert ej.ejecutar([s], tmp_path, ledger, ronda=1) == []
    assert reg.resumen("ciencias_v4_curricularizacion_20261022")["llamadas"] == 0
    assert not (tmp_path / "intentos").exists()
    assert len(list((tmp_path / "lecturas").glob("*.json"))) == 4


def test_una_captura_no_puede_ejecutarse_dos_veces_en_paralelo(tmp_path):
    import fcntl

    from goes_science_kg.produccion.revision_docente.ejecucion import ejecutar

    with (tmp_path / ".revision.lock").open("a") as f:
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="otra ejecución activa"):
            ejecutar([], tmp_path, tmp_path / "no_crear_ledger", ronda=1)
    assert not (tmp_path / "no_crear_ledger").exists()


def test_preparacion_no_admite_logros_inventados(candidato):
    _, registros, _ = candidato
    e = deepcopy(next(r["documento"]["edicion_docente"] for r in registros if r["tipo"] == "paquete_objetivo"))
    e["criterios"][0]["logro_observado"] = "Alcanzado por todo el grupo"
    with pytest.raises(ValueError, match="observados"):
        validar_edicion(e)


def test_ajuste_posterior_invalida_cuatro_votos_y_no_modifica_el_original(candidato):
    from goes_science_kg.materiales.compilacion import serializar, sha
    from goes_science_kg.produccion.revision_docente.contratos import ROLES
    from goes_science_kg.produccion.revision_docente.edicion import ajustes_posteriores

    _, rs, _ = candidato
    r = deepcopy(next(r for r in rs if r["tipo"] == "paquete_objetivo"))
    id_ = r["id"]
    r["documento"]["edicion_docente"]["explicacion"] = "Ejemplo sintético: longitud 0,10 m."
    original = deepcopy(r["documento"]["original"])
    e = r["documento"]["edicion_docente"]
    voto = {
        "estado": "revision_automatica_completa",
        "edicion_sha256": sha(serializar(e)),
        "contexto_sha256": "contexto anterior",
        "lote": 0,
        "lecturas": [{"rol": rol, "veredicto": "aprobar"} for rol in ROLES],
    }
    previo = deepcopy(voto)
    revision = {id_: voto}
    cambio = {
        "item_id": id_,
        "edicion_previa_sha256": sha(serializar(e)),
        "ruta": "explicacion",
        "anterior": e["explicacion"],
        "nuevo": "Ejemplo sintético: longitud 0.10 m.",
        "tipo": "notacion_decimal",
    }
    cfg = {"version": "ajuste de prueba", "cambios": [cambio]}
    contextos = ajustes_posteriores([r], revision, cfg)
    assert r["documento"]["original"] == original
    assert revision[id_]["antecedente_revisado"] == previo
    assert not revision[id_]["lecturas"] and set(revision[id_]["faltan_roles"]) == set(ROLES)
    assert revision[id_]["estado"] == "revision_automatica_con_pendientes"
    assert revision[id_]["contexto_sha256"] == sha(serializar(contextos[0]))
    assert revision[id_]["edicion_sha256"] == sha(serializar(r["documento"]["edicion_docente"]))
    r["documento"]["edicion_docente"]["explicacion"] = cambio["anterior"]
    cambio["nuevo"] = "Ejemplo sintético: longitud 9.99 m."
    with pytest.raises(ValueError, match="otros caracteres"):
        ajustes_posteriores([r], {id_: previo}, cfg)
