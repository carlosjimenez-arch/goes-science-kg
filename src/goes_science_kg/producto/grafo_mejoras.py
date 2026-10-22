"""Grafo de propuestas por fila y progresiones nativas: separado de los prerrequisitos reales."""

from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto._validacion import json_bytes, sha
from goes_science_kg.producto.mejoras_publicadas import ArchivoMejoras

TIPOS = {TipoNodo.EXPECTATIVA_NATIVA, TipoNodo.REVISION_UNIDAD, TipoNodo.MEJORA_CURRICULAR}
ENLACES = {
    TipoArista.SIGUE_EN_REFERENCIA,
    TipoArista.REVISA_UNIDAD,
    TipoArista.PROPUESTA_PARA,
    TipoArista.PARTE_DE_REVISION,
}


def grafo_mejoras(archivo: ArchivoMejoras):
    nodos, aristas = [], []
    for id_, fuente in sorted(archivo.fuentes_progresiones.items()):
        nodos.append(Nodo(id="DOC:" + id_, tipo=TipoNodo.DOCUMENTO, etiqueta=fuente["titulo"], props=fuente))
    for expectativa in archivo.progresiones["catalogo"]["expectativas"]:
        e = archivo.progresiones["evidencias"][expectativa["id"]]
        nodos.append(
            Nodo(
                id=expectativa["id"],
                tipo=TipoNodo.EXPECTATIVA_NATIVA,
                etiqueta=expectativa["titulo"] + " · " + expectativa["banda"],
                fuente=Fuente(documento=expectativa["fuente"], pagina=expectativa["pagina_pdf"]),
                props={
                    "expectativa": expectativa,
                    "evidencia": e,
                    "archivo_id": archivo.id,
                    "no_equivale_a_grado_sv": True,
                },
            )
        )
        aristas.append(
            Arista(
                origen=expectativa["id"],
                destino="DOC:" + expectativa["fuente"],
                tipo=TipoArista.FUENTE,
                metodo="celda_pdf_verificada",
            )
        )
    aristas.extend(
        Arista(
            origen=c["origen"],
            destino=c["destino"],
            tipo=TipoArista.SIGUE_EN_REFERENCIA,
            metodo="orden_documental_nativo",
            props={"limite": c["limite"]},
        )
        for c in archivo.progresiones["cadenas"]
    )
    for caso in archivo.unidades:
        p, r = caso.preparacion, caso.resultado
        id_unidad = "REVISION_V4:" + huella(p.solicitud)
        clave = (p.solicitud.grado, p.solicitud.asignatura_malla, p.solicitud.unidad)
        nodos.append(
            Nodo(
                id=id_unidad,
                tipo=TipoNodo.REVISION_UNIDAD,
                etiqueta=p.solicitud.unidad,
                grado=p.solicitud.grado,
                props={
                    "archivo_id": archivo.id,
                    "preparacion_id": p.id,
                    "estado": r.estado,
                    "motivos": list(r.motivos),
                    "filas": len(p.filas_originales),
                },
            )
        )
        aristas.append(
            Arista(
                origen=id_unidad,
                destino="UNIDAD:V4:" + sha(json_bytes(clave)),
                tipo=TipoArista.REVISA_UNIDAD,
                metodo="cuatro_especialistas",
            )
        )
        if not r.propuesta:
            continue
        originales = {f["id"]: f for f in p.filas_originales}
        for f in r.propuesta.filas:
            if f.accion == "fuera_alcance":
                continue
            original = originales[f.fila_id]
            identidad = "MEJORA_V4:" + huella([p.id, huella(r.propuesta), f.fila_id])
            nodos.append(
                Nodo(
                    id=identidad,
                    tipo=TipoNodo.MEJORA_CURRICULAR,
                    etiqueta=f.objetivo_propuesto,
                    grado=p.solicitud.grado,
                    fuente=Fuente(documento=original["fuente_id"], hoja=original["hoja"], fila=original["fila"]),
                    props={
                        "archivo_id": archivo.id,
                        "fila_id": f.fila_id,
                        "propuesta": f.model_dump(mode="json"),
                        "estado": r.estado,
                        "no_es_texto_original": True,
                    },
                )
            )
            for tipo, destino in (
                (TipoArista.PROPUESTA_PARA, f.fila_id),
                (TipoArista.PARTE_DE_REVISION, id_unidad),
                (TipoArista.FUENTE, "DOC:" + original["fuente_id"]),
            ):
                aristas.append(Arista(origen=identidad, destino=destino, tipo=tipo, metodo="cuatro_especialistas"))
    return nodos, aristas


def incorporar_mejoras(nodos, aristas, archivo):
    nuevos, enlaces = grafo_mejoras(archivo)
    existentes = {n.id: n for n in nodos}
    for n in nuevos:
        previo = existentes.get(n.id)
        if previo is not None:
            if (
                n.tipo != TipoNodo.DOCUMENTO
                or previo.tipo != n.tipo
                or any(previo.props.get(c) != n.props.get(c) for c in ("sha256", "archivo_local", "raiz_fuente"))
            ):
                raise ValueError("Las propuestas intentan sustituir un nodo original o documento distinto")
        else:
            existentes[n.id] = n
            nodos.append(n)
    aristas.extend(enlaces)


def validar_grafo_mejoras(nodos, aristas, archivo):
    nuevos, enlaces = grafo_mejoras(archivo) if archivo else ([], [])
    presentes = {n.id: n for n in nodos if n.tipo in TIPOS}
    esperados = {n.id: n for n in nuevos if n.tipo in TIPOS}
    if presentes != esperados:
        raise ValueError("El grafo de propuestas no corresponde a las unidades y sus votos")
    reales = [a for a in aristas if a.origen in presentes or a.destino in presentes or a.tipo in ENLACES]
    if len(reales) != len(enlaces) or {a.clave: a for a in reales} != {a.clave: a for a in enlaces}:
        raise ValueError("Las aristas curriculares mezclan relaciones documentales o propuestas ajenas")
    por_id = {n.id: n for n in nodos}
    for n in nuevos:
        if n.tipo == TipoNodo.DOCUMENTO and (
            n.id not in por_id
            or any(por_id[n.id].props.get(c) != n.props.get(c) for c in ("sha256", "archivo_local", "raiz_fuente"))
        ):
            raise ValueError("La progresión no conserva su documento primario")
