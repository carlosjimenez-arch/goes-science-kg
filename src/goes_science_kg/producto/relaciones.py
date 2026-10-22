"""Revalidate reviewed relationships and reject cycles across complete cohorts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import TYPE_CHECKING

import networkx as nx

from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto._juicios_contratos import (
    ColeccionConocimiento,
    ProyeccionDependencias,
    ResultadoConocimiento,
)

if TYPE_CHECKING:
    from goes_science_kg.motor.conocimiento import MotorConocimiento


def consolidar_relaciones(motor: MotorConocimiento, estados: Sequence[dict]) -> ColeccionConocimiento:
    """Inspect the complete selected collection without claiming curriculum-wide completeness."""

    # Implementation notes:
    # No confía en archivos de relaciones previamente respaldadas. Cada estado conserva preparación,
    # roles y terminal reconstruibles. Un conflicto entre juicios de un candidato invalida la unión;
    # un ciclo conserva todos los respaldos pero bloquea la admisión de la colección entera.
    por_candidato = {}
    for estado in estados:
        if not estado.get("preparacion") or not estado.get("resultado"):
            raise ValueError("La consolidación requiere estados terminales completos, no expedientes preparados")
        motor.validar_estado(estado)
        resultado = ResultadoConocimiento.model_validate(estado["resultado"])
        id_ = resultado.solicitud.candidato_id
        if id_ in por_candidato:
            raise ValueError("Candidato repetido: no se selecciona la ronda más favorable ni se cuenta dos veces")
        por_candidato[id_] = resultado
    return coleccionar_resultados(
        tuple(por_candidato.values()),
        huella_curriculo=motor.preparador.curriculo.huella,
        huella_motor=motor.huella_entorno,
        filas_por_candidato={k: c.fila_id for k, c in motor.preparador.candidatos.items()},
    )


def coleccionar_resultados(
    resultados: Sequence[ResultadoConocimiento],
    *,
    huella_curriculo: str,
    huella_motor: str,
    filas_por_candidato: Mapping[str, str],
    motores_por_candidato: Mapping[str, str] | None = None,
) -> ColeccionConocimiento:
    """Combine reconstructed results without independently verifying sources or authorizing reviews."""
    por_candidato = {r.solicitud.candidato_id: r for r in resultados}
    if len(por_candidato) != len(resultados):
        raise ValueError("Candidato repetido en la colección")
    esperados = motores_por_candidato or {i: huella_motor for i in por_candidato}
    if motores_por_candidato is not None and (
        esperados.keys() != por_candidato.keys() or huella_motor != huella(dict(sorted(esperados.items())))
    ):
        raise ValueError("La identidad compuesta no corresponde a todos sus motores y candidatos")
    if any(
        r.huella_motor != esperados[r.solicitud.candidato_id] or r.solicitud.candidato_id not in filas_por_candidato
        for r in resultados
    ):
        raise ValueError("Los resultados pertenecen a otro motor o a una fila no identificada")
    resultados = tuple(por_candidato[k] for k in sorted(por_candidato))
    relaciones = tuple(sorted((r.relacion for r in resultados if r.relacion is not None), key=lambda r: r.id))
    dependencias = tuple(r for r in relaciones if r.tipo == "prerrequisito_necesario")
    grafo = nx.DiGraph((r.origen, r.destino) for r in dependencias)
    ciclos = tuple(
        sorted(
            tuple(sorted(c))
            for c in nx.strongly_connected_components(grafo)
            if len(c) > 1 or any(grafo.has_edge(n, n) for n in c)
        )
    )
    proyeccion = ProyeccionDependencias(
        estado="bloqueada_por_ciclos" if ciclos else ("aciclica" if dependencias else "sin_prerrequisitos_respaldados"),
        nodos=tuple(sorted(grafo.nodes)),
        aristas=dependencias,
        componentes_ciclicas=ciclos,
        orden_topologico=() if ciclos else tuple(nx.lexicographical_topological_sort(grafo)),
    )
    datos = {
        "huella_curriculo": huella_curriculo,
        "huella_motor": huella_motor,
        "resultados": [r.model_dump(mode="json") for r in resultados],
        "proyeccion": proyeccion.model_dump(mode="json"),
    }
    return ColeccionConocimiento(
        huella_curriculo=huella_curriculo,
        huella_motor=huella_motor,
        huella_coleccion=huella(datos),
        resultados=resultados,
        relaciones_respaldadas=relaciones,
        relaciones_admisibles=() if ciclos else relaciones,
        proyeccion_dependencias=proyeccion,
        filas_examinadas=tuple(sorted({filas_por_candidato[r.solicitud.candidato_id] for r in resultados})),
    )
