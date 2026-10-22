"""Build the V4 graph without inheriting V3 topic decisions or relationships."""

from __future__ import annotations

import logging
from collections import Counter
from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.catalogacion import ASIGNATURAS, CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto._validacion import json_bytes, sha, validar_entrada, verificar_celdas
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones, validar_archivo_alineaciones
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento, validar_archivo_conocimiento
from goes_science_kg.producto.contratos import AlertaSolicitada, ReferenciasProducto
from goes_science_kg.producto.diagnostico import construir_alertas, diagnosticar

LOGGER = logging.getLogger(__name__)
ETIQUETAS = {
    "biologia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
    "ciencias_tierra_espacio": "Ciencias de la Tierra y del Espacio",
}


def _estructura(curriculo: Curriculo, catalogo: CatalogoDisciplinas) -> tuple[list[Nodo], list[Arista]]:
    nodos = [
        Nodo(
            id=f"ASIG:{a}",
            tipo=TipoNodo.ASIGNATURA,
            etiqueta=ETIQUETAS[a],
            asignatura=a,
            props={"version_curriculo": "V4"},
        )
        for a in sorted(ASIGNATURAS)
    ]
    nodos.extend(
        Nodo(
            id=f"GRADO:{g:02d}", tipo=TipoNodo.GRADO, etiqueta=f"Grado {g}", grado=g, props={"version_curriculo": "V4"}
        )
        for g in sorted({f.grado for f in curriculo.filas})
    )
    for fuente in curriculo.fuentes:
        nodos.append(
            Nodo(
                id=f"DOC:{fuente.id}",
                tipo=TipoNodo.DOCUMENTO,
                etiqueta=fuente.archivo,
                props={
                    "version_curriculo": "V4",
                    "fuente_id": fuente.id,
                    "archivo_local": fuente.archivo,
                    "ruta_de_procedencia": fuente.archivo_local,
                    "raiz_fuente": "v4",
                    "sha256": fuente.sha256,
                    "bytes": fuente.bytes,
                    "procedencia": fuente.procedencia,
                },
            )
        )
    unidades = {}
    for grupo in curriculo.agrupaciones:
        clave = grupo.grado, grupo.asignatura_malla, grupo.unidad
        identidad = f"UNIDAD:V4:{sha(json_bytes(clave))}"
        unidades[clave] = identidad
        nodos.append(
            Nodo(
                id=identidad,
                tipo=TipoNodo.UNIDAD,
                etiqueta=grupo.unidad,
                grado=grupo.grado,
                props={
                    "version_curriculo": "V4",
                    "asignatura_malla": grupo.asignatura_malla,
                    "filas": list(grupo.filas),
                },
            )
        )
    clasificaciones = {f.fila_id: f for f in catalogo.filas}
    aristas = []
    for fila in curriculo.filas:
        clasificacion = clasificaciones[fila.id]
        props = fila.model_dump(mode="json", exclude={"id"}) | {
            "version_curriculo": "V4",
            "disciplinas": list(clasificacion.disciplinas),
            "estado_clasificacion": clasificacion.estado,
            "clasificacion": clasificacion.model_dump(mode="json"),
            "campos_por_celda": {c.coordenada: c.campo for c in fila.celdas},
            "estado_alineacion": "declarado_no_verificado",
        }
        nodos.append(
            Nodo(
                id=fila.id,
                tipo=TipoNodo.TEMA,
                etiqueta=fila.procedimental,
                grado=fila.grado,
                asignatura=clasificacion.disciplinas[0] if len(clasificacion.disciplinas) == 1 else None,
                fuente=Fuente(
                    documento=fila.fuente_id, hoja=fila.hoja, fila=fila.fila, celdas=[c.coordenada for c in fila.celdas]
                ),
                props=props,
            )
        )
        aristas.extend(
            [
                Arista(origen=fila.id, destino=f"GRADO:{fila.grado:02d}", tipo=TipoArista.EN_GRADO, metodo="malla"),
                Arista(
                    origen=fila.id,
                    destino=unidades[fila.grado, fila.asignatura_malla, fila.unidad],
                    tipo=TipoArista.EN_UNIDAD,
                    metodo="malla",
                ),
                Arista(origen=fila.id, destino=f"DOC:{fila.fuente_id}", tipo=TipoArista.FUENTE, metodo="malla"),
            ]
        )
        for disciplina in clasificacion.disciplinas:
            aristas.append(
                Arista(
                    origen=fila.id,
                    destino=f"ASIG:{disciplina}",
                    tipo=TipoArista.DE_ASIGNATURA,
                    metodo="malla" if clasificacion.estado == "declarado_malla" else "catalogacion_automatica",
                    version=catalogo.version_pipeline,
                    justificacion=clasificacion.justificacion,
                    props={"estado": clasificacion.estado, "no_acredita_alineacion": True},
                )
            )
    return nodos, aristas


def _incorporar_referencias(
    nodos: list[Nodo],
    aristas: list[Arista],
    referencias: ReferenciasProducto,
) -> None:
    """Retain reference networks without inheriting prior topics, proposals, or orphan documents."""
    prohibidos = {
        TipoNodo.TEMA,
        TipoNodo.PROPUESTA,
        TipoNodo.UNIDAD,
        TipoNodo.GRADO,
        TipoNodo.ASIGNATURA,
        TipoNodo.RELACION_CURRICULAR,
    }
    candidatos = {}
    for nodo in referencias.nodos:
        if nodo.id in candidatos:
            raise ValueError("Referencias con nodos duplicados")
        if nodo.tipo not in prohibidos:
            candidatos[nodo.id] = nodo.model_copy(deep=True)
    # Los documentos que se usen deben existir; nunca se sustituye fuente faltante por metadatos.
    for identidad, nodo in list(candidatos.items()):
        if nodo.fuente is None:
            continue
        documento = nodo.fuente.documento
        id_doc = documento if documento.startswith("DOC:") else f"DOC:{documento}"
        if id_doc not in candidatos or candidatos[id_doc].tipo != TipoNodo.DOCUMENTO:
            del candidatos[identidad]
    usados = set()
    for nodo in candidatos.values():
        if nodo.fuente:
            doc = nodo.fuente.documento
            usados.add(doc if doc.startswith("DOC:") else f"DOC:{doc}")
    for arista in referencias.aristas:
        if arista.tipo == TipoArista.FUENTE and arista.origen in candidatos and arista.destino in candidatos:
            if candidatos[arista.origen].tipo != TipoNodo.DOCUMENTO:
                usados.add(arista.destino)
    candidatos = {i: n for i, n in candidatos.items() if n.tipo != TipoNodo.DOCUMENTO or i in usados}
    existentes = {n.id for n in nodos}
    if existentes.intersection(candidatos):
        raise ValueError("Una referencia intenta sustituir un nodo del currículo V4")
    for nodo in candidatos.values():
        documental = nodo.props.get("clase_referencia") == "documental"
        nodo.props = dict(nodo.props) | {
            "uso_en_producto": "referencia_documental" if documental else "referencia_historica",
            "no_acredita_cobertura_v4": True,
        }
        if not documental:
            nodo.props["version_curriculo_origen"] = referencias.procedencia.get("version_curriculo", "V3")
            nodo.props["estado_documental_uso"] = "historico_sin_revalidar_edicion"
            if "pisa" in (nodo.id + nodo.etiqueta).casefold():
                nodo.props["estado_publicacion"] = "historico_sin_verificar_edicion_no_final_vigente"
        nodos.append(nodo)
    for arista in referencias.aristas:
        if (
            arista.origen in candidatos
            and arista.destino in candidatos
            and arista.tipo
            not in {
                TipoArista.CUBRE,
                TipoArista.REEMPLAZA,
                TipoArista.PROPONE,
                TipoArista.EN_UNIDAD,
                TipoArista.EN_GRADO,
            }
        ):
            nueva = arista.model_copy(deep=True)
            nueva.props = dict(nueva.props) | {"uso_en_producto": "referencia", "no_acredita_cobertura_v4": True}
            aristas.append(nueva)


def construir_producto(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas,
    *,
    destino: Path,
    referencias: ReferenciasProducto | None = None,
    alertas: tuple[AlertaSolicitada, ...] = (),
    raiz_v4: Path | None = None,
    conocimiento: ArchivoConocimiento | None = None,
    modelos_conocimiento: dict[str, str] | None = None,
    raiz_historica: Path | None = None,
    archivo_alertas: Path | None = None,
    alineaciones: ArchivoAlineaciones | None = None,
    modelos_alineacion: dict[str, str] | None = None,
    paginas_alineacion=None,
) -> dict:
    """Validate, build, and publish a complete V4 snapshot outside the historical graph."""
    from goes_science_kg.producto.almacen import publicar_producto

    LOGGER.info("Producto V4: validando integridad de currículo y catálogo")
    # Copias profundas evitan cambios del llamante mientras se construye la generación.
    curriculo = Curriculo.model_validate(curriculo.model_dump(mode="python"))
    catalogo = CatalogoDisciplinas.model_validate(catalogo.model_dump(mode="python"))
    referencias = ReferenciasProducto.model_validate((referencias or ReferenciasProducto()).model_dump(mode="python"))
    validar_entrada(curriculo, catalogo)
    evidencias, estadisticas = verificar_celdas(curriculo, raiz_v4 or ruta("insumos/v4"))
    nodos, aristas = _estructura(curriculo, catalogo)
    _incorporar_referencias(nodos, aristas, referencias)
    if conocimiento is not None:
        from goes_science_kg.producto.consulta_conocimiento import rehidratar_archivo
        from goes_science_kg.producto.grafo_conocimiento import incorporar_conocimiento

        if modelos_conocimiento is None:
            raise ValueError("Publicar conocimiento exige una política explícita de modelos")
        conocimiento = ArchivoConocimiento.model_validate(conocimiento.model_dump(mode="json"))
        validar_archivo_conocimiento(conocimiento, curriculo, catalogo=catalogo, modelos_esperados=modelos_conocimiento)
        rehidratar_archivo(
            conocimiento,
            curriculo,
            raiz_v4=raiz_v4 or ruta("insumos/v4"),
            raiz_historica=raiz_historica,
            archivo_alertas=archivo_alertas,
        )
        if conocimiento.coleccion.proyeccion_dependencias.estado == "bloqueada_por_ciclos":
            raise ValueError("No se publica una colección de conocimiento bloqueada por ciclos")
        incorporar_conocimiento(nodos, aristas, conocimiento)
    if alineaciones is not None:
        from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
        from goes_science_kg.producto.garantias import bloqueos_cientificos
        from goes_science_kg.producto.grafo_alineaciones import incorporar_alineaciones

        if modelos_alineacion is None or paginas_alineacion is None:
            raise ValueError("Publicar alineaciones exige modelos fijados y páginas primarias verificables")
        alineaciones = ArchivoAlineaciones.model_validate(alineaciones.model_dump(mode="json"))
        fuentes_locales = fuentes_del_curriculo(curriculo, raiz_v4=raiz_v4 or ruta("insumos/v4"))
        fuentes_locales.bloqueos_curriculares = bloqueos_cientificos(
            curriculo, fuentes_locales, archivo_alertas or ruta("docs/investigacion/alertas_v4.json")
        )
        validar_archivo_alineaciones(
            alineaciones, curriculo, fuentes=fuentes_locales, paginas=paginas_alineacion, modelos=modelos_alineacion
        )
        incorporar_alineaciones(nodos, aristas, alineaciones)
    nodos.sort(key=lambda n: (n.tipo.value, n.id))
    aristas.sort(key=lambda a: (a.tipo.value, a.origen, a.destino, a.rol or ""))
    diagnostico = diagnosticar(curriculo, catalogo, nodos)
    diagnostico["conocimiento"] = {
        "estado": "sin_juicios" if conocimiento is None else "juicios_documentales_condicionados",
        "filas_con_juicio": len(conocimiento.coleccion.filas_examinadas) if conocimiento else 0,
        "filas_sin_juicio": len(curriculo.filas)
        - (len(conocimiento.coleccion.filas_examinadas) if conocimiento else 0),
        "resultados": dict(Counter(r.estado for r in conocimiento.coleccion.resultados)) if conocimiento else {},
        "relaciones_admitidas": dict(Counter(r.tipo for r in conocimiento.coleccion.relaciones_admisibles))
        if conocimiento
        else {},
        "limite": "Conteos de juicios y relaciones por fila; no desempeños, cobertura ni aprendizaje",
    }
    reporte_alertas = construir_alertas(curriculo, catalogo, evidencias, alertas)
    if alineaciones is not None:
        diagnostico["alineaciones_documentales"] = {
            "archivo_id": alineaciones.id,
            "casos": len(alineaciones.casos),
            "admitidos": len(alineaciones.admitidos),
            "resultados": dict(Counter(c.resultado.estado for c in alineaciones.casos)),
            "limite": alineaciones.limite,
        }
    publicacion = {
        "version_curriculo": "V4",
        "huella_curriculo": curriculo.huella,
        "metodo": "ingesta_verificada_y_catalogacion_sin_alineacion_heredada",
        "catalogacion": {k: v for k, v in catalogo.model_dump(mode="json").items() if k != "filas"},
        "fuentes_verificadas": estadisticas,
        "referencias": referencias.procedencia,
        "estado": "materializado_sin_activar",
        "alineaciones_internacionales_verificadas": 0,
        "conocimiento": {
            "estado": "sin_juicios" if conocimiento is None else "relaciones_condicionadas",
            "huella_archivo": conocimiento.huella_archivo if conocimiento else None,
            "relaciones_admitidas": len(conocimiento.coleccion.relaciones_admisibles) if conocimiento else 0,
        },
    }
    if alineaciones is not None:
        publicacion["alineaciones_documentales_admitidas"] = len(alineaciones.admitidos)
    resultado = publicar_producto(
        destino=destino,
        curriculo=curriculo,
        catalogo=catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=diagnostico,
        alertas=reporte_alertas,
        publicacion=publicacion,
        conocimiento=conocimiento,
        alineaciones=alineaciones,
    )
    LOGGER.info("Producto V4 publicado: %d temas; %s", len(curriculo.filas), resultado["snapshot_id"])
    return resultado
