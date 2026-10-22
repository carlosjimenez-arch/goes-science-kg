"""Composición de cohortes completas: conserva protocolos originales y rechaza rondas repetidas."""

from __future__ import annotations

from collections.abc import Sequence

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento, validar_archivo_conocimiento
from goes_science_kg.producto.relaciones import coleccionar_resultados


def componer_archivos(
    archivos: Sequence[ArchivoConocimiento],
    curriculo: Curriculo,
    *,
    catalogo: CatalogoDisciplinas | None = None,
    modelos_esperados: dict[str, str] | None = None,
    validar_resultado: bool = True,
) -> ArchivoConocimiento:
    """Revalida cada entrada, une todos sus resultados y comprueba ciclos entre cohortes.

    Los componentes originales se conservan completos para verificar su hash y su cierre. La vista
    conjunta deduplica fuentes y evidencia para recuperación; nunca selecciona sólo los respaldos.
    """
    if not 2 <= len(archivos) <= 50 or any(a.version != "conocimiento-publicado-1" for a in archivos):
        raise ValueError("Se requieren de dos a cincuenta archivos originales, sin composiciones anidadas")
    archivos = tuple(sorted(archivos, key=lambda a: a.huella_archivo))
    primero = archivos[0]
    candidatos, resultados = set(), []
    expedientes, evidencias, fuentes, nodos = {}, {}, {}, {}

    def unir(destino, nuevos):
        for id_, valor in nuevos.items():
            if id_ in destino and destino[id_] != valor:
                raise ValueError("Los componentes atribuyen valores distintos a la misma identidad")
            destino[id_] = valor

    for archivo in archivos:
        validar_archivo_conocimiento(archivo, curriculo, catalogo=catalogo, modelos_esperados=modelos_esperados)
        if (archivo.huella_referencia, archivo.politica, archivo.modelos) != (
            primero.huella_referencia,
            primero.politica,
            primero.modelos,
        ):
            raise ValueError("Los componentes necesitan referencia, política y modelos compatibles")
        if candidatos.intersection(archivo.expedientes):
            raise ValueError("Candidato repetido: no se selecciona una ronda más favorable")
        candidatos.update(archivo.expedientes)
        resultados.extend(archivo.coleccion.resultados)
        unir(expedientes, archivo.expedientes)
        unir(evidencias, archivo.evidencias)
        unir(fuentes, archivo.fuentes)
        unir(nodos, {n.id: n for n in archivo.nodos_referencia})
    perfiles = {(a.configuracion_modelo.get("proyecto"), a.configuracion_modelo.get("region")) for a in archivos}
    if len(perfiles) != 1:
        raise ValueError("No se componen resultados de proyectos o regiones diferentes")
    motores = {r.solicitud.candidato_id: r.huella_motor for r in resultados}
    coleccion = coleccionar_resultados(
        resultados,
        huella_curriculo=curriculo.huella,
        huella_motor=huella(dict(sorted(motores.items()))),
        motores_por_candidato=motores,
        filas_por_candidato={i: a.expediente(i).fila_id for a in archivos for i in a.expedientes},
    )
    datos = {
        "version": "conocimiento-publicado-2",
        "huella_curriculo": curriculo.huella,
        "huella_referencia": primero.huella_referencia,
        "modelos": primero.modelos,
        "configuracion_modelo": {"procedencia": "configuración original conservada en cada componente"},
        "politica": primero.politica.model_dump(mode="json"),
        "fuentes": dict(sorted(fuentes.items())),
        "nodos_referencia": [n.model_dump(mode="json") for _, n in sorted(nodos.items())],
        "evidencias": {i: e.model_dump(mode="json") for i, e in sorted(evidencias.items())},
        "expedientes": {i: e.model_dump(mode="json") for i, e in sorted(expedientes.items())},
        "coleccion": coleccion.model_dump(mode="json"),
        "componentes": [a.model_dump(mode="json") for a in archivos],
    }
    resultado = ArchivoConocimiento(huella_archivo=huella(datos), **datos)
    if validar_resultado:
        validar_archivo_conocimiento(resultado, curriculo, catalogo=catalogo, modelos_esperados=modelos_esperados)
    return resultado
