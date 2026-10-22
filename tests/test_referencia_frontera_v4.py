"""La red importada de referencia no puede crear enlaces al currículo V4 publicado."""

from __future__ import annotations

from copy import deepcopy

import pytest

from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto.construccion import _incorporar_referencias
from goes_science_kg.producto.contratos import ReferenciasProducto


@pytest.mark.parametrize("tipo_origen", [TipoNodo.CONCEPTO, TipoNodo.PRACTICA, TipoNodo.OBJETIVO_PAIS])
@pytest.mark.parametrize("tipo_arista", [TipoArista.TRABAJA, TipoArista.ALINEA_CON, TipoArista.PRERREQUISITO_DE])
def test_ninguna_arista_historica_cruza_desde_referencia_a_fila_v4(tipo_origen, tipo_arista):
    tema = Nodo(
        id="CURRICULO:V4:fila_actual",
        tipo=TipoNodo.TEMA,
        etiqueta="Objetivo local vigente",
        grado=6,
        props={"version_curriculo": "V4"},
    )
    referencia = Nodo(id="referencia_opaca", tipo=tipo_origen, etiqueta="Vocabulario histórico")
    arista = Arista(origen=referencia.id, destino=tema.id, tipo=tipo_arista, metodo="IA", version="V3")
    referencias = ReferenciasProducto(nodos=(referencia,), aristas=(arista,), procedencia={"version_curriculo": "V3"})
    antes = referencias.model_dump(mode="json")
    nodos, aristas = [tema], []
    _incorporar_referencias(nodos, aristas, referencias)
    assert {n.id for n in nodos} == {tema.id, referencia.id}
    assert aristas == []
    assert referencias.model_dump(mode="json") == antes
    assert nodos[0] == tema and "uso_en_producto" not in tema.props


def test_frontera_tambien_protege_documentos_y_clasificaciones_del_producto():
    referencia = Nodo(id="concepto_historico", tipo=TipoNodo.CONCEPTO, etiqueta="Concepto")
    documento_v4 = Nodo(id="DOC:fuente_v4", tipo=TipoNodo.DOCUMENTO, etiqueta="Malla V4")
    asignatura_v4 = Nodo(id="ASIG:fisica", tipo=TipoNodo.ASIGNATURA, etiqueta="Física")
    nodos, aristas = [documento_v4, asignatura_v4], []
    referencias = ReferenciasProducto(
        nodos=(referencia,),
        aristas=(
            Arista(origen=referencia.id, destino=documento_v4.id, tipo=TipoArista.FUENTE),
            Arista(origen=referencia.id, destino=asignatura_v4.id, tipo=TipoArista.DE_ASIGNATURA),
        ),
    )
    _incorporar_referencias(nodos, aristas, referencias)
    assert len(nodos) == 3 and aristas == []


def test_red_historica_interna_se_conserva_rotulada_sin_enlazar_tema_v4():
    tema_v4 = Nodo(id="fila_actual", tipo=TipoNodo.TEMA, etiqueta="Objetivo V4")
    documento = Nodo(id="DOC:historico", tipo=TipoNodo.DOCUMENTO, etiqueta="Documento histórico")
    concepto_a = Nodo(
        id="concepto_a",
        tipo=TipoNodo.CONCEPTO,
        etiqueta="Definición A",
        fuente=Fuente(documento="historico", pagina=1),
    )
    concepto_b = Nodo(id="concepto_b", tipo=TipoNodo.CONCEPTO, etiqueta="Definición B")
    tema_v3 = Nodo(id="tema_anterior", tipo=TipoNodo.TEMA, etiqueta="Objetivo V3")
    internas = (
        Arista(origen=concepto_a.id, destino=concepto_b.id, tipo=TipoArista.PRERREQUISITO_DE),
        Arista(origen=concepto_a.id, destino=documento.id, tipo=TipoArista.FUENTE),
    )
    referencias = ReferenciasProducto(
        nodos=(concepto_a, concepto_b, documento, tema_v3),
        aristas=(
            *internas,
            Arista(origen=concepto_b.id, destino=tema_v4.id, tipo=TipoArista.TRABAJA),
            Arista(origen=tema_v4.id, destino=concepto_a.id, tipo=TipoArista.TRABAJA),
            Arista(origen=tema_v3.id, destino=concepto_a.id, tipo=TipoArista.TRABAJA),
        ),
        procedencia={"version_curriculo": "V3"},
    )
    original = deepcopy(referencias.model_dump(mode="json"))
    nodos, aristas = [tema_v4], []
    _incorporar_referencias(nodos, aristas, referencias)
    assert {n.id for n in nodos} == {tema_v4.id, concepto_a.id, concepto_b.id, documento.id}
    assert {(a.origen, a.destino, a.tipo) for a in aristas} == {(a.origen, a.destino, a.tipo) for a in internas}
    assert all(a.props["uso_en_producto"] == "referencia" for a in aristas)
    assert all(a.props["no_acredita_cobertura_v4"] for a in aristas)
    assert all(tema_v4.id not in (a.origen, a.destino) for a in aristas)
    assert referencias.model_dump(mode="json") == original
