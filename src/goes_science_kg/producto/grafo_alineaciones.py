"""Project conditional documentary relationships without asserting coverage or grade equivalence."""

from __future__ import annotations

from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones


def grafo_alineaciones(archivo: ArchivoAlineaciones) -> tuple[list[Nodo], list[Arista]]:
    """Build typed graph nodes and links for the complete documentary alignment archive."""

    nodos, aristas = [], []
    for id_, fuente in sorted(archivo.fuentes.items()):
        nodos.append(Nodo(id=f"DOC:{id_}", tipo=TipoNodo.DOCUMENTO, etiqueta=fuente["titulo"], props=fuente))
    for ref in archivo.referentes.values():
        id_ = f"CRITERIO:{ref.id}"
        nodos.append(
            Nodo(
                id=id_,
                tipo=TipoNodo.CRITERIO_EVALUATIVO,
                etiqueta=ref.descripcion,
                fuente=Fuente(documento=ref.fuente, pagina=ref.paginas_pdf[0]),
                props=ref.model_dump(mode="json")
                | {"naturaleza": "parafrasis_local", "no_acredita_cobertura_v4": True},
            )
        )
        aristas.append(
            Arista(origen=id_, destino=f"DOC:{ref.fuente}", tipo=TipoArista.FUENTE, metodo="referente_verificado")
        )
    for caso in archivo.admitidos:
        identidad = "ALINEACION_V4:" + huella(caso.solicitud)
        nodos.append(
            Nodo(
                id=identidad,
                tipo=TipoNodo.ALINEACION_DOCUMENTAL,
                etiqueta="Correspondencia documental con " + caso.solicitud.referente_id,
                grado=caso.preparacion.grado,
                props={
                    "archivo_id": archivo.id,
                    "fila_id": caso.solicitud.fila_id,
                    "referente_id": caso.solicitud.referente_id,
                    "huella_tarea": caso.resultado.huella_tarea,
                    "resultado": caso.resultado.model_dump(mode="json"),
                },
            )
        )
        for tipo, destino in (
            (TipoArista.DECLARADA_EN, caso.solicitud.fila_id),
            (TipoArista.CON_CRITERIO, f"CRITERIO:{caso.solicitud.referente_id}"),
        ):
            aristas.append(Arista(origen=identidad, destino=destino, tipo=tipo, metodo="tres_lecturas_documentales"))
        for documento in sorted({e.fuente["documento"] for e in caso.preparacion.evidencias}):
            aristas.append(
                Arista(
                    origen=identidad,
                    destino=f"DOC:{documento}",
                    tipo=TipoArista.FUENTE,
                    metodo="fuente_del_juicio_documental",
                )
            )
    return nodos, aristas


def incorporar_alineaciones(nodos, aristas, archivo: ArchivoAlineaciones) -> None:
    """Add documentary alignments without replacing conflicting existing identities."""

    nuevos, enlaces = grafo_alineaciones(archivo)
    existentes = {n.id: n for n in nodos}
    for nodo in nuevos:
        previo = existentes.get(nodo.id)
        if previo is not None:
            if (
                nodo.tipo != TipoNodo.DOCUMENTO
                or previo.tipo != nodo.tipo
                or any(
                    previo.props.get(campo) != nodo.props.get(campo)
                    for campo in ("sha256", "archivo_local", "raiz_fuente")
                )
            ):
                raise ValueError("La alineación intenta sustituir un nodo o documento del producto")
        else:
            existentes[nodo.id] = nodo
            nodos.append(nodo)
    aristas.extend(enlaces)


def validar_grafo_alineaciones(nodos, aristas, archivo: ArchivoAlineaciones | None) -> None:
    """Require exact graph correspondence with the published alignment archive."""

    tipos_nodos = {TipoNodo.CRITERIO_EVALUATIVO, TipoNodo.ALINEACION_DOCUMENTAL}
    presentes = {n.id: n for n in nodos if n.tipo in tipos_nodos}
    esperados, enlaces = grafo_alineaciones(archivo) if archivo else ([], [])
    if presentes != {n.id: n for n in esperados if n.tipo in tipos_nodos}:
        raise ValueError("Los criterios o alineaciones no corresponden al archivo publicado")
    reales = [
        a
        for a in aristas
        if a.origen in presentes
        or a.destino in presentes
        or a.tipo in {TipoArista.DECLARADA_EN, TipoArista.CON_CRITERIO}
    ]
    if {a.clave: a for a in reales} != {a.clave: a for a in enlaces} or len(reales) != len(enlaces):
        raise ValueError("Las relaciones documentales no corresponden a sus lecturas y fuentes")
    por_id = {n.id: n for n in nodos}
    for esperado in esperados:
        if esperado.tipo == TipoNodo.DOCUMENTO and (
            esperado.id not in por_id
            or any(
                por_id[esperado.id].props.get(campo) != esperado.props.get(campo)
                for campo in ("sha256", "archivo_local", "raiz_fuente")
            )
        ):
            raise ValueError("El documento del grafo difiere de la edición examinada")
