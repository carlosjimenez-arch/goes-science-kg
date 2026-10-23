"""Represent row-conditioned knowledge separately from global GraphRAG adjacency."""

from __future__ import annotations

from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento

ARISTAS_CONTEXTO = {TipoArista.EN_CONTEXTO, TipoArista.ORIGEN_RELACION, TipoArista.DESTINO_RELACION}


def grafo_del_conocimiento(archivo: ArchivoConocimiento) -> tuple[list[Nodo], list[Arista]]:
    """Represent a conditioned relationship explicitly without creating universal prerequisites."""
    nodos, aristas = [], []
    extremos = {i for r in archivo.coleccion.relaciones_admisibles for i in (r.origen, r.destino)}
    for original in archivo.nodos_referencia:
        if original.id not in extremos:
            continue
        nodo = original.model_copy(deep=True)
        nodo.grado = None
        nodo.fuente = None
        nodo.props = dict(nodo.props) | {
            "uso_en_producto": "referencia_de_relacion_condicionada",
            "grado_legacy_no_equivalente": original.grado,
            "fuente_referencia_historica": original.fuente.model_dump(mode="json") if original.fuente else None,
            "no_acredita_cobertura_v4": True,
            "definicion_historica_no_validada_globalmente": True,
        }
        nodos.append(nodo)
    for doc, props in sorted(archivo.fuentes.items()):
        nodos.append(
            Nodo(id="DOC:" + doc, tipo=TipoNodo.DOCUMENTO, etiqueta=str(props.get("titulo", doc)), props=dict(props))
        )
    resultados = {r.relacion.id: r for r in archivo.coleccion.resultados if r.relacion is not None}
    for relacion in archivo.coleccion.relaciones_admisibles:
        resultado = resultados[relacion.id]
        expediente = archivo.expediente(resultado.solicitud.candidato_id)
        nodos.append(
            Nodo(
                id=relacion.id,
                tipo=TipoNodo.RELACION_CURRICULAR,
                etiqueta=f"{relacion.tipo}: {relacion.origen} → {relacion.destino}",
                grado=relacion.grado_sv,
                props=relacion.model_dump(mode="json")
                | {
                    "version_curriculo": "V4",
                    "tipo_evidencia": "inferencia_semantica_juzgada",
                    "candidato_id": resultado.solicitud.candidato_id,
                    "huella_archivo": archivo.huella_archivo,
                    "no_es_fuente_primaria": True,
                    "limite": resultado.limite,
                },
            )
        )
        for tipo, destino in (
            (TipoArista.EN_CONTEXTO, relacion.fila_id),
            (TipoArista.ORIGEN_RELACION, relacion.origen),
            (TipoArista.DESTINO_RELACION, relacion.destino),
        ):
            aristas.append(Arista(origen=relacion.id, destino=destino, tipo=tipo, metodo="publicacion_de_juicio"))
        for doc in sorted({e.fuente["documento"].removeprefix("DOC:") for e in expediente.evidencias}):
            aristas.append(
                Arista(
                    origen=relacion.id,
                    destino="DOC:" + doc,
                    tipo=TipoArista.FUENTE,
                    metodo="evidencia_del_juicio",
                    props={"huella_archivo": archivo.huella_archivo},
                )
            )
    return nodos, aristas


def incorporar_conocimiento(nodos: list[Nodo], aristas: list[Arista], archivo: ArchivoConocimiento) -> None:
    """Preserve existing source identities and endpoints rather than replacing their content."""
    nuevos, enlaces = grafo_del_conocimiento(archivo)
    usados = {a.destino for a in enlaces if a.tipo == TipoArista.FUENTE}
    existentes = {n.id: n for n in nodos}
    for nodo in nuevos:
        if nodo.tipo == TipoNodo.DOCUMENTO and nodo.id not in usados:
            continue  # Fuentes de juicios rechazados permanecen en el archivo, no como documentos huérfanos.
        if nodo.id in existentes:
            previo = existentes[nodo.id]
            if nodo.tipo == TipoNodo.DOCUMENTO:
                campos = ("sha256", "archivo_local", "raiz_fuente")
                if previo.tipo != nodo.tipo or any(
                    previo.props.get(c, "principal" if c == "raiz_fuente" else None)
                    != nodo.props.get(c, "principal" if c == "raiz_fuente" else None)
                    for c in campos
                ):
                    raise ValueError("Conocimiento intenta sustituir una fuente del grafo")
            elif previo != nodo:
                raise ValueError("Conocimiento intenta sustituir un extremo existente del grafo")
        else:
            nodos.append(nodo)
            existentes[nodo.id] = nodo
    aristas.extend(enlaces)


def validar_grafo_conocimiento(nodos, aristas, archivo: ArchivoConocimiento | None) -> None:
    """Require exact correspondence between the reified graph and its review archive."""
    presentes = {n.id: n for n in nodos if n.tipo == TipoNodo.RELACION_CURRICULAR}
    if archivo is None:
        if presentes or any(a.tipo in ARISTAS_CONTEXTO for a in aristas):
            raise ValueError("Relaciones curriculares sin archivo de conocimiento verificado")
        return
    esperados, enlaces = grafo_del_conocimiento(archivo)
    esperados = {n.id: n for n in esperados if n.tipo == TipoNodo.RELACION_CURRICULAR}
    if presentes != esperados:
        raise ValueError("Los nodos de relación no corresponden al archivo de conocimiento")
    reales = [a for a in aristas if a.origen in presentes or a.destino in presentes or a.tipo in ARISTAS_CONTEXTO]
    if {a.clave: a for a in reales} != {a.clave: a for a in enlaces} or len(reales) != len(enlaces):
        raise ValueError("Los papeles o fuentes de una relación no corresponden a sus juicios")
    por_id = {n.id: n for n in nodos}
    documentos = {a.destino for a in enlaces if a.tipo == TipoArista.FUENTE}
    for id_doc in documentos:
        esperado = archivo.fuentes[id_doc.removeprefix("DOC:")]
        real = por_id[id_doc]
        if real.tipo != TipoNodo.DOCUMENTO or any(
            real.props.get(c, "principal" if c == "raiz_fuente" else None)
            != esperado.get(c, "principal" if c == "raiz_fuente" else None)
            for c in ("sha256", "archivo_local", "raiz_fuente", "bytes")
        ):
            raise ValueError("Una fuente del grafo difiere de la utilizada por los juicios")
    for nodo in grafo_del_conocimiento(archivo)[0]:
        if nodo.tipo not in {TipoNodo.DOCUMENTO, TipoNodo.RELACION_CURRICULAR} and por_id.get(nodo.id) != nodo:
            raise ValueError("Un extremo del grafo no corresponde a su registro de conocimiento")
