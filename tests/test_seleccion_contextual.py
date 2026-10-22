"""Localizadores permitidos y grupos obligatorios sin relajar dictámenes ni agregar citas."""

from __future__ import annotations

import copy
import json

import pytest
from pydantic import ValidationError
from test_juicios_conocimiento import LectoresSimulados, entrada

from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.motor.seleccion import esquema_por_grupos, ids_seleccionados
from goes_science_kg.producto._juicios_contratos import ESQUEMAS_CONOCIMIENTO
from goes_science_kg.producto.juicios import datos_juicio


@pytest.fixture
def seleccion(tmp_path):
    e = entrada(tmp_path)
    expediente = e.preparador.preparar(e.solicitud)
    esquema = esquema_por_grupos(ESQUEMAS_CONOCIMIENTO["juez_ciencia"], expediente.fragmentos, expediente.grupos)
    lectura = LectoresSimulados().generar(
        rol="juez_ciencia",
        sistema="No ves otros lectores",
        esquema=esquema,
        mensaje=json.dumps(datos_juicio(expediente)),
    )
    return e, expediente, esquema, lectura


@pytest.mark.parametrize("cambio", ["grupo_omitido", "id_ajeno", "otra_fuente", "grupo_extra"])
def test_estructura_incompleta_o_fuente_invertida_no_puede_validar(seleccion, cambio):
    _, _, esquema, lectura = seleccion
    datos = lectura.model_dump(mode="json")
    grupos = datos["fragmentos_por_grupo"]
    local = next(g for g in grupos if g != "objetivo_extranjero")
    if cambio == "grupo_omitido":
        del grupos[local]
    elif cambio == "id_ajeno":
        grupos[local] = "F:inventado"
    elif cambio == "otra_fuente":
        grupos[local] = grupos["objetivo_extranjero"]
    else:
        grupos["instruccion_ajena"] = grupos[local]
    with pytest.raises(ValidationError):
        esquema.model_validate(datos)


def test_no_se_inventan_citas_al_unificar_fragmentos_compartidos(seleccion):
    _, expediente, _, lectura = seleccion
    ids = ids_seleccionados(lectura)
    assert len(ids) == len(set(ids))
    seleccionados = {f.evidencia_id for f in expediente.fragmentos if f.id in ids}
    assert all(seleccionados.intersection(g) for g in expediente.grupos.values())
    assert set(ids) == set(lectura.fragmentos_por_grupo.model_dump().values())


def test_veto_semantico_permanece_aunque_todos_los_grupos_esten_citados(seleccion):
    e, _, _, _ = seleccion
    modelo = LectoresSimulados({"juez_ciencia": {"fuentes_implican_relacion": "no"}})
    estado = (
        MotorConocimiento(e.preparador, modelo)
        .compilar()
        .invoke(
            {
                "solicitud": e.solicitud.model_dump(),
                "ejecucion_id": "sintetico-veto",
            }
        )
    )
    assert estado["resultado"]["estado"] == "no_respaldado"
    assert len(modelo.llamadas) == 4


def test_criterios_y_limites_del_contrato_base_siguen_vigentes(seleccion):
    _, _, _, lectura = seleccion
    base = ESQUEMAS_CONOCIMIENTO["juez_ciencia"]
    datos = lectura.model_dump(mode="json")
    datos["fragmentos_ids"] = ids_seleccionados(lectura)
    del datos["fragmentos_por_grupo"]
    for campo, valor in (("limites", ["repetido", "repetido"]), ("criterios", {"aprobar": "si"})):
        alterado = copy.deepcopy(datos)
        alterado[campo] = valor
        with pytest.raises(ValidationError):
            base.model_validate(alterado)
