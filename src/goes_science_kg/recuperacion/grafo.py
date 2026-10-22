"""Adaptadores del grafo existente; la versión del formato no es la del currículo."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.grafo.almacen import cargar as cargar_grafo
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.recuperacion.buscador import Buscador
from goes_science_kg.recuperacion.modelos import Documento, Enlace

TIPOS_RECUPERABLES = {
    TipoNodo.TEMA,
    TipoNodo.CONCEPTO,
    TipoNodo.PRACTICA,
    TipoNodo.OBJETIVO_MARCO,
    TipoNodo.OBJETIVO_PAIS,
    TipoNodo.DIMENSION_DOCUMENTAL,
}
PESOS_RELACION = {
    TipoArista.TRABAJA: 1.0,
    TipoArista.CUBRE: 0.9,
    TipoArista.ALINEA_CON: 0.8,
    TipoArista.PRERREQUISITO_DE: 0.95,
}
CAMPOS_TEXTO = (
    "definicion",
    "unidad",
    "contenido",
    "subcontenido",
    "indicador",
    "evidencia",
    "competencia_pisa",
    "habilidad_timss",
    "area",
    "tema",
    "texto_en",
    "titulo_en",
    "progresion",
)


def _version_nodos(nodos: Iterable[Nodo]) -> str | None:
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA]
    versiones = {n.props["version_curriculo"] for n in temas if n.props.get("version_curriculo")}
    if len(versiones) > 1:
        raise ValueError("El grafo mezcla versiones curriculares de temas")
    if versiones and any(not n.props.get("version_curriculo") for n in temas):
        raise ValueError("Sólo algunos temas declaran su versión curricular")
    return next(iter(versiones), None)


def _version_fuentes(nodos: Iterable[Nodo]) -> str | None:
    """Compatibilidad legacy desde procedencia inmutable, nunca desde config mutable."""
    nodos = tuple(nodos)
    documentos = {n.id: n for n in nodos if n.tipo == TipoNodo.DOCUMENTO}
    versiones = set()
    for tema in (n for n in nodos if n.tipo == TipoNodo.TEMA):
        if tema.fuente is None:
            return None
        id_documento = tema.fuente.documento
        documento = documentos.get(id_documento if id_documento.startswith("DOC:") else f"DOC:{id_documento}")
        if documento is None or not re.fullmatch(r"[a-f0-9]{64}", documento.props.get("sha256", "")):
            return None
        archivo = str(documento.props.get("archivo_local", "")).replace("\\", "/").casefold()
        coincidencia = re.search(r"/mallas sugeridas(?: v(\d+))?/", archivo)
        if not coincidencia:
            return None
        versiones.add(f"V{coincidencia.group(1) or '1'}")
    if len(versiones) > 1:
        raise ValueError("Las fuentes del grafo mezclan entregas curriculares distintas")
    return next(iter(versiones), None)


def _resolver_version(nodos: Iterable[Nodo], version_manifest: str | None = None) -> str:
    nodos = tuple(nodos)
    declaradas = {v for v in (version_manifest, _version_nodos(nodos), _version_fuentes(nodos)) if v}
    if len(declaradas) > 1:
        raise ValueError("El manifiesto, los temas o sus fuentes declaran versiones curriculares distintas")
    if not declaradas:
        raise ValueError("Falta procedencia de la versión curricular: reconstruir con metadatos explícitos")
    return declaradas.pop()


def documentos_del_grafo(nodos: Iterable[Nodo], *, version: str | None = None) -> list[Documento]:
    """Convierte nodos; sólo los temas pertenecen a una versión de currículo local.

    En memoria se verifica contra metadatos del nodo o la configuración vigente. Los conceptos sin
    fuente se marcan como derivados; no se presentan como páginas de una fuente primaria.
    """
    nodos = tuple(nodos)
    verificada = _resolver_version(nodos)
    if version is not None and version != verificada:
        raise ValueError(f"No se puede etiquetar como {version} un grafo curricular {verificada}")
    return _convertir(nodos, verificada)


def _convertir(nodos: Iterable[Nodo], version: str) -> list[Documento]:
    documentos = []
    for nodo in nodos:
        if nodo.tipo not in TIPOS_RECUPERABLES or nodo.props.get("marco") == "T23":
            continue
        partes = [nodo.etiqueta]
        partes.extend(
            nodo.props[c] for c in CAMPOS_TEXTO if isinstance(nodo.props.get(c), str) and nodo.props[c].strip()
        )
        partes.extend(s for s in nodo.props.get("sinonimos", []) if isinstance(s, str) and s.strip())
        if nodo.tipo == TipoNodo.DIMENSION_DOCUMENTAL:
            partes.extend(nodo.props[c] for c in ("alcance", "ancla") if isinstance(nodo.props.get(c), str))
        if nodo.tipo == TipoNodo.TEMA and nodo.props.get("version_curriculo") == "V4":
            partes.extend(
                nodo.props[c]
                for c in ("procedimental", "indicadores_logro", "indicador_avanzado", "evidencia_aprendizaje")
                if isinstance(nodo.props.get(c), str) and nodo.props[c].strip()
            )
        texto = "\n".join(dict.fromkeys(partes))
        fuente = (
            nodo.fuente.model_dump(exclude_none=True)
            if nodo.fuente is not None
            else {"documento": "grafo_derivado", "localizador": nodo.id, "tipo": "derivada"}
        )
        documentos.append(
            Documento(
                id=nodo.id,
                texto=texto,
                fuente=fuente,
                version=version if nodo.tipo == TipoNodo.TEMA else "referencia",
                grado=nodo.grado,
                asignatura=nodo.asignatura,
                metadata={"tipo_nodo": nodo.tipo.value, "fuente_primaria": nodo.fuente is not None}
                | {
                    campo: nodo.props[campo]
                    for campo in ("campos_por_celda", "disciplinas", "estado_clasificacion", "archivo", "hoja", "fila")
                    if campo in nodo.props
                },
            )
        )
    return documentos


def aristas_del_grafo(aristas: Iterable[Arista]) -> list[Enlace]:
    """Conserva direcciones curriculares; recorre prerrequisitos hacia sus antecedentes."""
    resultado = []
    for arista in aristas:
        if arista.tipo not in PESOS_RELACION:
            continue
        origen, destino = arista.origen, arista.destino
        if arista.tipo == TipoArista.PRERREQUISITO_DE:
            origen, destino = destino, origen
        resultado.append(
            Enlace(
                origen=origen,
                destino=destino,
                tipo=arista.tipo.value,
                peso=PESOS_RELACION[arista.tipo],
            )
        )
    return resultado


def cargar_documentos_grafo(
    directorio: str | Path = "data/grafo",
    *,
    version: str | None = None,
) -> list[Documento]:
    """Carga el grafo y rechaza un pedido que cambiaría su versión curricular.

    `manifest.version` describe el formato y no se usa. Los grafos nuevos deben declarar
    `version_curriculo`; para el legado se consulta `config/mallas.yaml`.
    """
    nodos, _, verificada = _cargar_grafo_validado(directorio, version=version)
    return _convertir(nodos, verificada)


def _cargar_grafo_validado(
    directorio: str | Path,
    *,
    version: str | None,
) -> tuple[list[Nodo], list[Arista], str]:
    directorio = ruta(directorio)
    manifest = json.loads((directorio / "manifest.json").read_text(encoding="utf-8"))
    for nombre in ("nodos.jsonl", "aristas.jsonl"):
        esperada = manifest.get("sha256", {}).get(nombre)
        if not esperada or hashlib.sha256((directorio / nombre).read_bytes()).hexdigest() != esperada:
            raise ValueError(f"El archivo {nombre} no coincide con el SHA-256 del manifiesto")
    nodos, aristas = cargar_grafo(str(directorio))
    verificada = _resolver_version(nodos, manifest.get("version_curriculo"))
    if version is not None and version != verificada:
        raise ValueError(f"El grafo contiene {verificada}; se solicitó {version}")
    return nodos, aristas, verificada


def cargar_buscador_grafo(directorio: str | Path = "data/grafo", *, version: str | None = None) -> Buscador:
    """Carga una vez el grafo validado y añade sus relaciones al buscador local."""
    nodos, aristas, verificada = _cargar_grafo_validado(directorio, version=version)
    return Buscador(_convertir(nodos, verificada), aristas=aristas_del_grafo(aristas))
