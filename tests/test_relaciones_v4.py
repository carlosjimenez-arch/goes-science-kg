"""Rehydrate cross-batch review collections and reject cycles without inventing progressions."""

from __future__ import annotations

import copy

import pytest
from test_conocimiento_v4 import _concepto, _curriculo, _pais, _referencia
from test_juicios_conocimiento import LectoresSimulados, ejecutar, entrada

from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.modelos import Arista, TipoArista
from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.producto._juicios_contratos import SolicitudConocimiento, SoporteSemantico
from goes_science_kg.producto.conocimiento import EdicionEsperada, PoliticaConocimiento, generar_candidatos_conocimiento
from goes_science_kg.producto.juicios import PreparadorConocimiento
from goes_science_kg.producto.relaciones import consolidar_relaciones


def red(tmp_path, *, ciclo):
    curriculo = _curriculo(tmp_path, texto="Relaciona el agua, la temperatura y la energía.")
    documento, _, digest = _pais(tmp_path)
    conceptos = [_concepto(i, nombre) for i, nombre in [("uno", "Agua"), ("dos", "Temperatura"), ("tres", "Energía")]]
    pares = [("uno", "dos"), ("dos", "tres")] + ([("tres", "uno")] if ciclo else [])
    referencia = _referencia(
        documento, *conceptos, aristas=[Arista(origen=a, destino=b, tipo=TipoArista.PRERREQUISITO_DE) for a, b in pares]
    )
    informe = generar_candidatos_conocimiento(
        curriculo,
        referencia,
        raiz_v4=tmp_path / "v4",
        raiz_historica=tmp_path,
        politica=PoliticaConocimiento(
            ediciones_por_documento={
                "documento-pais": EdicionEsperada(sha256=digest, version_documental="2013"),
            }
        ),
    )
    candidatos = [c for c in informe.candidatos if c.tipo == "prerrequisito"]
    soportes = [
        SoporteSemantico(
            candidato_id=c.id, grupo=g, documento="documento-pais", pagina=1, sha256=digest, version_documental="2013"
        )
        for c in candidatos
        for g in ("origen", "destino", "dependencia")
    ]
    fuentes = fuentes_del_curriculo(
        curriculo,
        raiz_v4=tmp_path / "v4",
        raiz_historica=tmp_path,
        catalogo_historico={"documento-pais": documento.props},
    )
    motor = MotorConocimiento(
        PreparadorConocimiento(curriculo, informe, referencia, fuentes, soportes=soportes), LectoresSimulados()
    )
    estados = [
        motor.compilar().invoke(
            {"solicitud": SolicitudConocimiento(candidato_id=c.id).model_dump(), "ejecucion_id": "lote-" + str(i)}
        )
        for i, c in enumerate(candidatos)
    ]
    return motor, estados


def test_ciclo_detectado_al_unir_lotes_conserva_todos_los_respaldos(tmp_path):
    motor, estados = red(tmp_path, ciclo=True)
    assert all(e["resultado"]["estado"] == "respaldado" for e in estados)
    parcial = consolidar_relaciones(motor, estados[:1])
    assert parcial.proyeccion_dependencias.estado == "aciclica"
    coleccion = consolidar_relaciones(motor, estados)
    assert coleccion.proyeccion_dependencias.estado == "bloqueada_por_ciclos"
    assert len(coleccion.relaciones_respaldadas) == 3 and coleccion.relaciones_admisibles == ()
    assert coleccion.proyeccion_dependencias.componentes_ciclicas == (("dos", "tres", "uno"),)
    assert len(coleccion.proyeccion_dependencias.aristas) == 3
    assert coleccion.proyeccion_dependencias.orden_topologico == ()


def test_orden_estructural_no_inventa_clausura_transitiva(tmp_path):
    motor, estados = red(tmp_path, ciclo=False)
    coleccion = consolidar_relaciones(motor, estados)
    assert coleccion.proyeccion_dependencias.orden_topologico == ("uno", "dos", "tres")
    assert {(r.origen, r.destino) for r in coleccion.relaciones_admisibles} == {("uno", "dos"), ("dos", "tres")}
    assert "condicionadas_a_filas" in coleccion.proyeccion_dependencias.alcance


def test_duplicar_o_reescoger_ronda_no_fabrica_aprobacion(tmp_path):
    motor, _, estado = ejecutar(entrada(tmp_path))
    with pytest.raises(ValueError, match="repetido"):
        consolidar_relaciones(motor, [estado, copy.deepcopy(estado)])


def test_terminal_corrupto_no_ingresa_a_coleccion(tmp_path):
    motor, _, estado = ejecutar(entrada(tmp_path))
    estado["resultado"]["relacion"]["destino"] = "otro"
    with pytest.raises(ValueError, match="terminal"):
        consolidar_relaciones(motor, [estado])


def test_abstencion_mantiene_fila_examinada_sin_dag_ficticio(tmp_path):
    e = entrada(tmp_path, tipo="fila_concepto")
    motor, _, estado = ejecutar(e)
    coleccion = consolidar_relaciones(motor, [estado])
    assert coleccion.filas_examinadas == (e.candidato.fila_id,)
    assert coleccion.relaciones_respaldadas == coleccion.relaciones_admisibles == ()
    assert coleccion.proyeccion_dependencias.estado == "sin_prerrequisitos_respaldados"


def test_coleccion_vacia_no_declara_progresion_comprobada(tmp_path):
    motor = MotorConocimiento(entrada(tmp_path).preparador, LectoresSimulados())
    coleccion = consolidar_relaciones(motor, [])
    assert coleccion.resultados == () and coleccion.filas_examinadas == ()
    assert coleccion.proyeccion_dependencias.estado == "sin_prerrequisitos_respaldados"
