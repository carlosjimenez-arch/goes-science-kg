"""Citas por registro: procedencia, límites de contexto y resolución sin literales libres."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from goes_science_kg.motor.contratos import Actividad, Evidencia
from goes_science_kg.motor.fragmentos import (
    AfirmacionBorrador,
    Borrador,
    Fragmento,
    datos_fragmentos,
    preparar_fragmentos,
    resolver_borrador,
)


def _evidencia(evidencia_id="TEMA:local", texto=None, version="V4", fuente=None):
    return Evidencia.crear(
        evidencia_id,
        texto or "Identifica las necesidades de agua y luz de las plantas mediante una observación sencilla.",
        fuente or {"documento": "malla.xlsx", "hoja": "Unidad 1", "fila": 3, "verificacion": "contenido_fuente"},
        version,
    )


def _borrador(fragmentos):
    return Borrador(
        afirmaciones=[
            AfirmacionBorrador(
                texto="Las plantas requieren agua y luz para su desarrollo.",
                fragmentos_ids=[fragmentos[0].id],
            )
        ],
        anclaje_curricular=[fragmentos[0].id],
        actividad=Actividad(
            objetivo="Identificar necesidades de las plantas mediante observación.",
            pasos=["Comparar dos dibujos de plantas con distintas condiciones."],
            comprobacion="Justificar qué condición ayuda al crecimiento de la planta.",
            minutos=20,
            recursos=["papel", "lapiz"],
            adaptacion_salvador="Usar ejemplos de plantas del entorno de la escuela.",
        ),
        limites=["La actividad es una propuesta y no demuestra eficacia educativa."],
    )


def test_lectura_completa_no_se_confunde_con_el_limite_de_la_cita():
    e = _evidencia(texto=" ".join(f"término{i}" for i in range(130)) + ".")
    f = preparar_fragmentos([e], "término0", 5000, lectura_completa=True)
    datos = datos_fragmentos(f, [e], lectura_completa=True)
    assert datos["lectura_primaria"][e.id] == e.texto
    assert all(len(v.literal.split()) <= 20 for v in f)
    assert len(json.dumps(datos, ensure_ascii=False)) <= 5000
    assert "lectura_primaria" not in datos_fragmentos(f, [e])


def test_lectura_completa_que_no_cabe_no_se_recorta_para_seguir():
    e = _evidencia(texto=" ".join(f"término{i}" for i in range(130)) + ".")
    with pytest.raises(ValueError, match="presupuesto"):
        preparar_fragmentos([e], "término0", 1000, lectura_completa=True)


def test_glifos_fuera_del_fragmento_tambien_bloquean_lectura_completa():
    e = _evidencia(texto="Esta frase permite una cita completamente verificable. Luego aparece (cid:78).")
    f = preparar_fragmentos([e], "frase permite", 3000)
    with pytest.raises(ValueError, match="glifos"):
        datos_fragmentos(f, [e], lectura_completa=True)


def test_literales_son_subcadenas_con_whitespace_normalizado_y_maximo_veinte_palabras():
    texto = "  Las plantas\nrequieren\t agua y luz. " + " ".join(f"palabra{i}" for i in range(75))
    evidencia = _evidencia(texto=texto)
    fragmentos = preparar_fragmentos([evidencia], "necesidades de las plantas")
    assert len(fragmentos) > 3
    normalizado = " ".join(texto.split())
    for fragmento in fragmentos:
        assert fragmento.literal in normalizado
        assert len(fragmento.literal.split()) <= 20
        assert 12 <= len(fragmento.literal) <= 280
        assert fragmento.evidencia_id == evidencia.id


def test_preserva_anclaje_local_aunque_la_consulta_coincida_mas_con_referencia():
    local = _evidencia(texto="Describe el ciclo de vida de las plantas del entorno.")
    referencia = _evidencia("PISA:1", "Diseña una indagación experimental sobre luz solar y energía.", "referencia")
    fragmentos = preparar_fragmentos([referencia, local], "indagación experimental luz solar energía", max_fragmentos=1)
    assert len(fragmentos) == 1
    assert fragmentos[0].evidencia_id == local.id


def test_presupuesto_cuenta_fuentes_versiones_huellas_y_sintaxis_json():
    local = _evidencia(texto=" ".join(f"contenido{i}" for i in range(120)))
    referencia = _evidencia(
        "PISA:1",
        "Pregunta de investigación científica con evidencia de un experimento.",
        "referencia",
    )
    fragmentos = preparar_fragmentos([local, referencia], "investigación", max_caracteres=1200)
    assert len(json.dumps(datos_fragmentos(fragmentos, [local, referencia]), ensure_ascii=False)) <= 1200
    assert any(f.evidencia_id == local.id for f in fragmentos)
    with pytest.raises(ValueError, match="presupuesto"):
        preparar_fragmentos([local], "contenido", max_caracteres=100)


def test_metadatos_largos_no_pueden_eludir_presupuesto():
    local = _evidencia(fuente={"documento": "malla.xlsx", "localizador": "x" * 3000})
    with pytest.raises(ValueError, match="presupuesto"):
        preparar_fragmentos([local], "plantas", max_caracteres=1000)


def test_ids_deterministas_y_sensibles_a_version_y_fuente():
    local = _evidencia()
    referencia = _evidencia(
        "PISA:1",
        "Explica las observaciones mediante el uso de evidencia científica.",
        "referencia",
    )
    original = preparar_fragmentos([local, referencia], "plantas")
    assert original == preparar_fragmentos([referencia, local], "plantas")
    nuevo = _evidencia(version="V3")
    assert preparar_fragmentos([nuevo], "plantas")[0].id != original[0].id
    otra_fuente = local.model_copy(update={"fuente": {"documento": "otra.xlsx", "fila": 1}})
    assert preparar_fragmentos([otra_fuente], "plantas")[0].id != original[0].id


def test_resuelve_citas_desde_registro_y_deduplica_ids():
    evidencia = _evidencia()
    fragmentos = preparar_fragmentos([evidencia], "plantas")
    borrador = _borrador(fragmentos)
    borrador.afirmaciones[0].fragmentos_ids.append(fragmentos[0].id)
    propuesta = resolver_borrador(borrador, fragmentos)
    assert len(propuesta.afirmaciones[0].citas) == 1
    assert propuesta.afirmaciones[0].citas[0].literal == fragmentos[0].literal
    assert propuesta.afirmaciones[0].citas[0].evidencia_id == evidencia.id
    assert propuesta.anclaje_curricular[0].literal in evidencia.texto


def test_ids_desconocidos_no_se_reparan_ni_se_ignoran():
    fragmentos = preparar_fragmentos([_evidencia()], "plantas")
    borrador = _borrador(fragmentos)
    borrador.anclaje_curricular.append("inventado")
    with pytest.raises(ValueError, match="desconocido"):
        resolver_borrador(borrador, fragmentos)
    with pytest.raises(ValueError, match="duplicados"):
        resolver_borrador(_borrador(fragmentos), [fragmentos[0], fragmentos[0]])


@pytest.mark.parametrize("cambio", [{"texto": "Texto diferente sin su huella original."}, {"huella": "inventada"}])
def test_rechaza_evidencia_modificada(cambio):
    evidencia = _evidencia().model_copy(update=cambio)
    with pytest.raises(ValueError, match="huella"):
        preparar_fragmentos([evidencia], "plantas")


def test_rechaza_fuentes_derivadas_y_versions_ambiguas():
    derivada = _evidencia(fuente={"documento": "grafo_derivado", "tipo": "derivada"})
    with pytest.raises(ValueError, match="procedencia"):
        preparar_fragmentos([derivada], "plantas")
    with pytest.raises(ValueError, match="exactamente una versión"):
        preparar_fragmentos([_evidencia(), _evidencia("TEMA:viejo", version="V3")], "plantas")
    with pytest.raises(ValueError, match="exactamente una versión"):
        preparar_fragmentos([_evidencia(version="referencia")], "plantas")


def test_rechaza_registros_ambiguos_y_evidencia_demasiado_corta():
    with pytest.raises(ValueError, match="ambigua"):
        preparar_fragmentos([_evidencia(), _evidencia(texto="Otra definición curricular diferente.")], "plantas")
    with pytest.raises(ValueError, match="fragmento citable"):
        preparar_fragmentos([_evidencia(texto="Célula.")], "célula")


def test_modelo_no_puede_introducir_literal_libre_ni_contenido_vacio():
    fragmentos = preparar_fragmentos([_evidencia()], "plantas")
    datos = _borrador(fragmentos).model_dump()
    datos["afirmaciones"][0]["literal"] = "Una cita escrita por el modelo."
    with pytest.raises(ValidationError):
        Borrador.model_validate(datos)
    with pytest.raises(ValidationError):
        Fragmento(id="F1", evidencia_id="TEMA:1", literal=" " * 30)


def test_resolucion_literal_no_certifica_implicacion_semantica():
    fragmentos = preparar_fragmentos([_evidencia()], "plantas")
    borrador = _borrador(fragmentos)
    afirmacion_incorrecta = AfirmacionBorrador(
        texto="La gravedad terrestre se produce porque las plantas reciben luz.",
        fragmentos_ids=[fragmentos[0].id],
    )
    borrador = borrador.model_copy(update={"afirmaciones": [afirmacion_incorrecta]})
    propuesta = resolver_borrador(borrador, fragmentos)
    assert propuesta.afirmaciones[0].texto == afirmacion_incorrecta.texto
    assert propuesta.afirmaciones[0].citas[0].literal == fragmentos[0].literal


def test_reserva_grupos_antes_de_llenar_contexto_con_coincidencias_lexicas():
    objetivo = _evidencia("A:objetivo", "Describe agua energía plantas mediante una observación sencilla.")
    evaluacion = _evidencia("Z:evaluacion", "Justifica la conclusión mediante los resultados registrados.")
    extranjero = _evidencia(
        "Z:extranjero", "Evaluate claims using observations from a scientific investigation.", "referencia"
    )
    distractores = [
        _evidencia(f"B:{i}", f"Agua energía plantas luz agua energía suelo observaciones {i}.") for i in range(20)
    ]
    evidencias = [objetivo, *distractores, evaluacion, extranjero]
    grupos = {"objetivo": [objetivo.id], "evaluacion": [evaluacion.id], "extranjero": [extranjero.id]}
    anterior = preparar_fragmentos(evidencias, "agua energía plantas", 2400)
    assert extranjero.id not in {f.evidencia_id for f in anterior}
    actual = preparar_fragmentos(evidencias, "agua energía plantas", 2400, grupos_obligatorios=grupos)
    seleccionados = {f.evidencia_id for f in actual}
    assert {objetivo.id, evaluacion.id, extranjero.id} <= seleccionados
    assert len(json.dumps(datos_fragmentos(actual, evidencias), ensure_ascii=False)) <= 2400
    assert actual == preparar_fragmentos(
        list(reversed(evidencias)), "agua energía plantas", 2400, grupos_obligatorios=grupos
    )


def test_un_fragmento_cubre_grupos_superpuestos_sin_duplicarse():
    local = _evidencia()
    fragmentos = preparar_fragmentos(
        [local], "plantas", max_fragmentos=1, grupos_obligatorios={"fila": [local.id], "objetivo": [local.id]}
    )
    assert len(fragmentos) == 1
    assert fragmentos[0].evidencia_id == local.id


@pytest.mark.parametrize(
    "grupos", [{"": ["TEMA:local"]}, {"a": []}, {"a": ["inexistente"]}, {"a": ["TEMA:local"] * 2}, {"a": "TEMA:local"}]
)
def test_rechaza_grupos_sin_identidad_o_evidencia(grupos):
    with pytest.raises(ValueError, match="grupo obligatorio"):
        preparar_fragmentos([_evidencia()], "plantas", grupos_obligatorios=grupos)


@pytest.mark.parametrize("limite, max_fragmentos", [(100, 48), (18000, 1)])
def test_grupos_imposibles_producen_error_sin_omitir_fuentes(limite, max_fragmentos):
    local = _evidencia()
    referencia = _evidencia("PISA:1", version="referencia")
    with pytest.raises(ValueError, match="cada grupo obligatorio"):
        preparar_fragmentos(
            [local, referencia],
            "plantas",
            limite,
            max_fragmentos=max_fragmentos,
            grupos_obligatorios={"extranjero": [referencia.id]},
        )


def test_grupo_con_fuente_sin_fragmento_citable_no_pasa_por_presencia_de_metadatos():
    local = _evidencia()
    corta = _evidencia("PISA:1", texto="Luz.", version="referencia")
    with pytest.raises(ValueError, match="cada grupo obligatorio"):
        preparar_fragmentos([local, corta], "plantas", grupos_obligatorios={"extranjero": [corta.id]})
