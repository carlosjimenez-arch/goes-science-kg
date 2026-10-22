"""Conservación de negativos, relectura física y ataques contra la publicación documental."""

from __future__ import annotations

from copy import deepcopy

import pytest
from test_alineacion import LectorSimulado, ejecutar
from test_alineacion import entrada as entrada

from goes_science_kg.motor.alineacion import ROLES_ALINEACION
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.alineaciones import (
    ArchivoAlineaciones,
    coleccionar_alineaciones,
    validar_archivo_alineaciones,
)
from goes_science_kg.producto.grafo_alineaciones import grafo_alineaciones, validar_grafo_alineaciones


def archivo(entrada, **opciones):
    modelo = LectorSimulado(**opciones)
    motor = entrada.crear(modelo)
    estado = ejecutar(motor, entrada.solicitud)
    estado["huella_entorno"] = motor.huella_entorno
    a = coleccionar_alineaciones(
        [estado],
        entrada.curriculo,
        {entrada.referente.id: entrada.referente},
        {r: modelo.nombre_modelo(r) for r in ROLES_ALINEACION},
        entrada.fuentes,
        entrada.repositorio,
    )
    return a, modelo


@pytest.mark.parametrize(
    "opciones,esperado",
    [
        ({}, "respaldo_documental_automatico"),
        ({"negativo": True}, "no_respaldado"),
        ({"falla": ROLES_ALINEACION[0]}, "abstencion"),
    ],
)
def test_archiva_cualquier_cierre_y_revalida_sin_nuevos_modelos(entrada, opciones, esperado):
    a, modelo = archivo(entrada, **opciones)
    validar_archivo_alineaciones(a, entrada.curriculo, fuentes=entrada.fuentes, paginas=entrada.repositorio)
    assert a.casos[0].resultado.estado == esperado and len(modelo.llamadas) == 3
    assert len(a.admitidos) == int(esperado == "respaldo_documental_automatico")


@pytest.mark.parametrize("campo", ["estado", "modelo", "fila", "cita", "literal", "caso_duplicado", "fuente"])
def test_rechaza_falsificaciones_aunque_recalculen_hash_exterior(entrada, campo):
    a, _ = archivo(entrada)
    datos = deepcopy(a.model_dump(mode="json"))
    caso = datos["casos"][0]
    rol = ROLES_ALINEACION[0]
    if campo == "estado":
        caso["resultado"]["estado"] = "no_respaldado"
    elif campo == "modelo":
        caso["lecturas"][rol]["dictamen"]["modelo"] = "ajeno"
    elif campo == "fila":
        caso["preparacion"]["grado"] = 7
    elif campo == "cita":
        caso["lecturas"][rol]["dictamen"]["citas_referente"][0]["literal"] = "Una cita inventada ajena a la página"
    elif campo == "literal":
        caso["preparacion"]["fragmentos"][0]["id"] = "F:inventado"
    elif campo == "caso_duplicado":
        datos["casos"].append(deepcopy(caso))
    else:
        datos["fuentes"][entrada.referente.fuente]["sha256"] = "b" * 64
    datos["id"] = huella({k: v for k, v in datos.items() if k != "id"})
    with pytest.raises(ValueError):
        validar_archivo_alineaciones(
            ArchivoAlineaciones.model_validate(datos),
            entrada.curriculo,
            fuentes=entrada.fuentes,
            paginas=entrada.repositorio,
        )


def test_releer_fuente_cambiada_impide_usar_el_archivo_anterior(entrada):
    a, _ = archivo(entrada)
    entrada.archivo.write_bytes(entrada.archivo.read_bytes() + b"edicion nueva")
    with pytest.raises(ValueError, match="releer"):
        validar_archivo_alineaciones(a, entrada.curriculo, fuentes=entrada.fuentes, paginas=entrada.repositorio)


def test_grafo_no_promueve_negativos_ni_permite_saltar_a_otra_fila(entrada):
    a, _ = archivo(entrada)
    nodos, aristas = grafo_alineaciones(a)
    validar_grafo_alineaciones(nodos, aristas, a)
    assert all(x.tipo.value != "CUBRE" for x in aristas)
    cambiadas = [
        x.model_copy(update={"destino": "otra-fila"}) if x.tipo.value == "DECLARADA_EN" else x for x in aristas
    ]
    with pytest.raises(ValueError, match="relaciones documentales"):
        validar_grafo_alineaciones(nodos, cambiadas, a)
    negativa, _ = archivo(entrada, negativo=True)
    nodos, aristas = grafo_alineaciones(negativa)
    assert not any(n.tipo.value == "AlineacionDocumental" for n in nodos)
    validar_grafo_alineaciones(nodos, aristas, negativa)
