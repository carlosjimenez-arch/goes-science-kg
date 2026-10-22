"""Adaptadores explícitos de categorías documentales y redes históricas de referencia."""

from __future__ import annotations

import json
from pathlib import Path

from goes_science_kg.ingesta.dimensiones import CatalogoDimensiones, validar_dimensiones
from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto._validacion import sha
from goes_science_kg.producto.contratos import ReferenciasProducto
from goes_science_kg.recuperacion.grafo import _resolver_version


def referencias_documentales(
    catalogo: CatalogoDimensiones,
    repositorio: RepositorioReferencias,
) -> ReferenciasProducto:
    """Ancla categorías en páginas verificadas; no crea CUBRE ni objetivos oficiales."""
    validacion = validar_dimensiones(catalogo, repositorio)
    manifiesto = repositorio.manifiesto()
    if sha(manifiesto.model_dump_json().encode("utf-8")) != validacion["huella_manifest"]:
        raise ValueError("La edición documental cambió después de verificar sus anclas")
    registros = {d["dimension_id"]: d for d in validacion["dimensiones"]}
    nodos, aristas = [], []
    for fuente in sorted({d.fuente for d in catalogo.dimensiones}):
        registro = manifiesto.referencias[fuente]
        nodos.append(
            Nodo(
                id=f"DOC:{fuente}",
                tipo=TipoNodo.DOCUMENTO,
                etiqueta=registro.titulo,
                props=registro.model_dump(mode="json")
                | {
                    "archivo_local": registro.archivo_pdf,
                    "raiz_fuente": "referencias_2026",
                    "clase_referencia": "documental",
                    "estado_ancla": "ancla_documental_verificada",
                },
            )
        )
        nodos.append(
            Nodo(
                id=f"MARCO:REFERENCIA:{fuente}",
                tipo=TipoNodo.MARCO,
                etiqueta=registro.titulo,
                props={
                    "clase_referencia": "documental",
                    "estado_publicacion": registro.estado_publicacion,
                    "version_documental": registro.version_documental,
                    "fuente_id": fuente,
                },
            )
        )
    for dimension in catalogo.dimensiones:
        comprobacion = registros[dimension.id]
        pagina = comprobacion["paginas_con_ancla"][0]["pagina_pdf"]
        nodos.append(
            Nodo(
                id=dimension.id,
                tipo=TipoNodo.DIMENSION_DOCUMENTAL,
                etiqueta=dimension.etiqueta,
                fuente=Fuente(documento=dimension.fuente, pagina=pagina),
                props=dimension.model_dump(mode="json")
                | {
                    "clase_referencia": "documental",
                    "estado_ancla": "ancla_documental_verificada",
                    "comprobacion": comprobacion,
                    "no_es_codigo_oficial": True,
                    "no_implica_cobertura": True,
                },
            )
        )
        aristas.extend(
            [
                Arista(
                    origen=dimension.id,
                    destino=f"DOC:{dimension.fuente}",
                    tipo=TipoArista.FUENTE,
                    metodo="ancla_documental",
                ),
                Arista(
                    origen=dimension.id,
                    destino=f"MARCO:REFERENCIA:{dimension.fuente}",
                    tipo=TipoArista.EN_MARCO,
                    metodo="catalogo_documental",
                ),
            ]
        )
    return ReferenciasProducto(
        nodos=tuple(nodos),
        aristas=tuple(aristas),
        procedencia={
            "clase": "documental",
            "validacion": validacion,
            "metadatos": catalogo.meta.model_dump(mode="json"),
        },
    )


def cargar_referencias_historicas(directorio: Path) -> ReferenciasProducto:
    """Lee bytes cotejados con manifiesto; preserva su versión y su condición histórica."""
    base = directorio.resolve()
    archivo_manifest = base / "manifest.json"
    if archivo_manifest.is_symlink():
        raise ValueError("Referencia histórica fuera de su directorio")
    manifest_bytes = archivo_manifest.read_bytes()
    manifest = json.loads(manifest_bytes)
    contenidos = {}
    for nombre in ("nodos.jsonl", "aristas.jsonl"):
        archivo = base / nombre
        if archivo.is_symlink() or not archivo.resolve().is_relative_to(base):
            raise ValueError("Referencia histórica fuera de su directorio")
        contenido = archivo.read_bytes()
        if sha(contenido) != manifest.get("sha256", {}).get(nombre):
            raise ValueError("Referencia histórica no coincide con SHA de manifiesto")
        contenidos[nombre] = contenido
    nodos = tuple(Nodo.model_validate_json(linea) for linea in contenidos["nodos.jsonl"].splitlines())
    aristas = tuple(Arista.model_validate_json(linea) for linea in contenidos["aristas.jsonl"].splitlines())
    version = _resolver_version(nodos, manifest.get("version_curriculo"))
    if version != "V3":
        raise ValueError("El adaptador histórico solo admite la referencia explícita V3")
    return ReferenciasProducto(
        nodos=nodos,
        aristas=aristas,
        procedencia={
            "clase": "historica",
            "version_curriculo": version,
            "manifest_sha256": sha(manifest_bytes),
            "sha256": {n: sha(c) for n, c in contenidos.items()},
            "limite": "Red histórica sin revalidar: no acredita vínculos de las nuevas filas V4",
        },
    )


def combinar_referencias(*referencias: ReferenciasProducto) -> ReferenciasProducto:
    """Combina conjuntos explícitos; una colisión de identidad requiere resolución previa."""
    nodos, aristas = [], []
    vistos = set()
    for referencia in referencias:
        for nodo in referencia.nodos:
            if nodo.id in vistos:
                raise ValueError("Referencias con identidad superpuesta; resuelva la colisión explícitamente")
            vistos.add(nodo.id)
            nodos.append(nodo)
        aristas.extend(referencia.aristas)
    return ReferenciasProducto(
        nodos=tuple(nodos),
        aristas=tuple(aristas),
        procedencia={
            "clase": "combinada",
            "conjuntos": [r.procedencia for r in referencias],
        },
    )
