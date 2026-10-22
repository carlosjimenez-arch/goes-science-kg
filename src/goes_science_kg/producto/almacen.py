"""Snapshots de producto inmutables y selección atómica de una generación completa."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field

from goes_science_kg.archivos import destino_generado
from goes_science_kg.config import ruta
from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import ContratoCurricular, Curriculo
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.producto._validacion import json_bytes, sha, validar_entrada
from goes_science_kg.producto.alineaciones import ArchivoAlineaciones, validar_archivo_alineaciones
from goes_science_kg.producto.conocimiento_publicado import ArchivoConocimiento, validar_archivo_conocimiento
from goes_science_kg.producto.contratos import ManifestProducto, ProductoMaterializado
from goes_science_kg.producto.grafo_alineaciones import validar_grafo_alineaciones
from goes_science_kg.producto.grafo_conocimiento import validar_grafo_conocimiento
from goes_science_kg.producto.grafo_mejoras import validar_grafo_mejoras
from goes_science_kg.producto.mejoras_publicadas import ArchivoMejoras, validar_archivo_mejoras

ARCHIVOS = frozenset(
    {
        "nodos.jsonl",
        "aristas.jsonl",
        "curriculo.json",
        "catalogo.json",
        "diagnostico_v4.json",
        "alertas_v4.json",
        "publicacion.json",
        "conocimiento.json",
    }
)
LIMITES = (
    "Materializado sin activar el grafo ni la configuración histórica",
    "Declaraciones y códigos locales no equivalen a alineaciones internacionales verificadas",
    "Integridad respecto al manifiesto local; no autenticidad por firma digital ni aprobación oficial",
)


def archivos_producto(version: str) -> frozenset[str]:
    if version == "producto-2":
        return ARCHIVOS
    if version == "producto-3":
        return ARCHIVOS | {"alineaciones.json"}
    if version == "producto-4":
        return ARCHIVOS | {"alineaciones.json", "mejoras.json"}
    raise ValueError("Formato de publicación no admitido")


class _Puntero(ContratoCurricular):
    version: Literal["producto-2", "producto-3", "producto-4"]
    version_curriculo: Literal["V4"]
    snapshot_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    manifest_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


def _segura(base: Path, relativo: str) -> Path:
    """No sigue enlaces bajo el almacén ni admite rutas fuera de su raíz."""
    subruta = Path(relativo)
    if subruta.is_absolute() or ".." in subruta.parts:
        raise ValueError("Ruta fuera del almacén del producto")
    acumulada = base
    for parte in subruta.parts:
        acumulada /= parte
        if acumulada.is_symlink():
            raise ValueError("El almacén no admite enlaces simbólicos en sus artefactos")
    if not acumulada.resolve().is_relative_to(base):
        raise ValueError("Ruta fuera del almacén del producto")
    return acumulada


def _destino(destino: Path, *, crear: bool) -> Path:
    if destino.is_symlink():
        raise ValueError("La raíz del producto no puede ser un enlace simbólico")
    base = destino.resolve()
    for protegido in (
        "data/grafo",
        "data/fuentes",
        "insumos",
        "reportes",
        "data/referencias_2026",
        "data/referencias_paises_2026",
        "data/referencias_cientificas_2026",
    ):
        if base.is_relative_to(ruta(protegido).resolve()):
            raise ValueError("El producto debe publicarse fuera del grafo histórico y de las fuentes originales")
    destino_generado(base / "actual.json", raiz=ruta("."))
    if crear:
        base.mkdir(parents=True, exist_ok=True)
    return base


def _escribir_archivo(archivo: Path, contenido: bytes) -> None:
    with archivo.open("xb") as salida:
        salida.write(contenido)
        salida.flush()
        os.fsync(salida.fileno())


def _sincronizar(directorio: Path) -> None:
    descriptor = os.open(directorio, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _identidad(huellas: dict[str, str], version: str = "producto-2") -> str:
    return sha(json_bytes({"version": version, "version_curriculo": "V4", "sha256": huellas}))


def _verificar_grafo(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas,
    nodos: tuple[Nodo, ...],
    aristas: tuple[Arista, ...],
    conocimiento: ArchivoConocimiento | None = None,
    alineaciones: ArchivoAlineaciones | None = None,
    mejoras: ArchivoMejoras | None = None,
) -> None:
    if conocimiento is not None and conocimiento.coleccion.proyeccion_dependencias.estado == "bloqueada_por_ciclos":
        raise ValueError("Una colección bloqueada por ciclos no puede formar parte del producto")
    por_id = {n.id: n for n in nodos}
    if len(por_id) != len(nodos) or len({a.clave for a in aristas}) != len(aristas):
        raise ValueError("El grafo contiene nodos o aristas duplicados")
    if any(a.origen not in por_id or a.destino not in por_id for a in aristas):
        raise ValueError("El grafo contiene aristas con extremos inexistentes")
    temas = {n.id: n for n in nodos if n.tipo == TipoNodo.TEMA}
    if set(temas) != {f.id for f in curriculo.filas} or any(n.tipo == TipoNodo.PROPUESTA for n in nodos):
        raise ValueError("El grafo omite temas V4 o incorpora temas/propuestas de otras versiones")
    if any(a.tipo == TipoArista.CUBRE for a in aristas):
        raise ValueError("Esta publicación no dispone de alineaciones CUBRE verificadas")
    clasificaciones = {f.fila_id: f for f in catalogo.filas}
    por_tema = {}
    for arista in aristas:
        por_tema.setdefault(arista.origen, []).append(arista)
        if arista.tipo == TipoArista.FUENTE and por_id[arista.destino].tipo != TipoNodo.DOCUMENTO:
            raise ValueError("Una arista FUENTE no apunta a un Documento")
        if arista.tipo in {TipoArista.TRABAJA, TipoArista.PRERREQUISITO_DE, TipoArista.ALINEA_CON} and (
            arista.origen in temas or arista.destino in temas
        ):
            raise ValueError("Las inferencias globales históricas no se heredan a filas V4")
    for fila in curriculo.filas:
        tema = temas[fila.id]
        decision = clasificaciones[fila.id]
        asignatura = decision.disciplinas[0] if len(decision.disciplinas) == 1 else None
        if tema.grado != fila.grado or tema.asignatura != asignatura or tema.etiqueta != fila.procedimental:
            raise ValueError("Tema distinto de su fila curricular o su catálogo disciplinar")
        esperado = fila.model_dump(mode="json", exclude={"id"})
        if any(tema.props.get(k) != v for k, v in esperado.items()):
            raise ValueError("El tema perdió o alteró campos del currículo rico")
        if tema.props.get("version_curriculo") != "V4" or tema.props.get("disciplinas") != list(decision.disciplinas):
            raise ValueError("Versión o disciplinas del tema incoherentes")
        if tema.props.get("estado_clasificacion") != decision.estado:
            raise ValueError("El estado de clasificación del tema difiere del catálogo")
        if (
            tema.fuente is None
            or tema.fuente.documento != fila.fuente_id
            or (
                tema.fuente.hoja != fila.hoja
                or tema.fuente.fila != fila.fila
                or tema.fuente.celdas != [c.coordenada for c in fila.celdas]
            )
        ):
            raise ValueError("El tema perdió sus localizadores originales")
        if tema.props.get("campos_por_celda") != {c.coordenada: c.campo for c in fila.celdas}:
            raise ValueError("El mapa de campos por celda difiere del insumo")
        enlaces = por_tema.get(fila.id, [])
        asignadas = {a.destino for a in enlaces if a.tipo == TipoArista.DE_ASIGNATURA}
        if asignadas != {f"ASIG:{a}" for a in decision.disciplinas}:
            raise ValueError("Los enlaces de asignatura no coinciden con el catálogo")
        if sum(a.tipo == TipoArista.EN_UNIDAD for a in enlaces) != 1 or (
            sum(a.tipo == TipoArista.EN_GRADO for a in enlaces) != 1
            or sum(a.tipo == TipoArista.FUENTE for a in enlaces) != 1
        ):
            raise ValueError("Tema sin unidad, grado o fuente únicos")
        por_tipo = {
            a.tipo: a
            for a in enlaces
            if a.tipo
            in {
                TipoArista.EN_UNIDAD,
                TipoArista.EN_GRADO,
                TipoArista.FUENTE,
            }
        }
        unidad = por_id[por_tipo[TipoArista.EN_UNIDAD].destino]
        if (
            unidad.tipo != TipoNodo.UNIDAD
            or unidad.grado != fila.grado
            or unidad.etiqueta != fila.unidad
            or (unidad.props.get("asignatura_malla") != fila.asignatura_malla)
        ):
            raise ValueError("El tema está enlazado a una unidad de otro contexto")
        if por_tipo[TipoArista.EN_GRADO].destino != f"GRADO:{fila.grado:02d}" or (
            por_tipo[TipoArista.FUENTE].destino != f"DOC:{fila.fuente_id}"
        ):
            raise ValueError("El enlace del tema no corresponde a su grado o fuente")
    usados = set()
    for nodo in nodos:
        if nodo.fuente:
            documento = nodo.fuente.documento
            identificador = documento if documento.startswith("DOC:") else f"DOC:{documento}"
            if identificador not in por_id or por_id[identificador].tipo != TipoNodo.DOCUMENTO:
                raise ValueError("Nodo con fuente huérfana")
            usados.add(identificador)
    usados.update(a.destino for a in aristas if a.tipo == TipoArista.FUENTE)
    if any(n.tipo == TipoNodo.DOCUMENTO and n.id not in usados for n in nodos):
        raise ValueError("Documento sin ningún nodo o relación que lo utilice")
    validar_grafo_conocimiento(nodos, aristas, conocimiento)
    validar_grafo_alineaciones(nodos, aristas, alineaciones)
    validar_grafo_mejoras(nodos, aristas, mejoras)


def _cargar_snapshot(base: Path, esperada: str, identidad: str) -> ProductoMaterializado:
    manifest_bytes = _segura(base, "manifest.json").read_bytes()
    if sha(manifest_bytes) != esperada:
        raise ValueError("El manifiesto no coincide con el SHA del puntero")
    manifest = ManifestProducto.model_validate_json(manifest_bytes)
    if manifest.snapshot_id != identidad or _identidad(manifest.sha256, manifest.version) != identidad:
        raise ValueError("Identidad de snapshot incoherente")
    archivos = archivos_producto(manifest.version)
    if set(manifest.sha256) != archivos or set(manifest.bytes) != archivos:
        raise ValueError("El manifiesto no describe exactamente los archivos del producto")
    contenidos = {}
    for nombre in sorted(archivos):
        esperada_archivo = manifest.sha256[nombre]
        if not re.fullmatch(r"[a-f0-9]{64}", esperada_archivo):
            raise ValueError("SHA de artefacto inválido")
        contenido = _segura(base, nombre).read_bytes()
        if sha(contenido) != esperada_archivo or len(contenido) != manifest.bytes[nombre]:
            raise ValueError(f"El artefacto {nombre} no coincide con su SHA o tamaño")
        contenidos[nombre] = contenido
    curriculo = Curriculo.model_validate_json(contenidos["curriculo.json"])
    catalogo = CatalogoDisciplinas.model_validate_json(contenidos["catalogo.json"])
    validar_entrada(curriculo, catalogo)
    if manifest.huella_curriculo != curriculo.huella or manifest.huella_catalogo != sha(contenidos["catalogo.json"]):
        raise ValueError("Huella curricular o del catálogo incoherente con el manifiesto")
    nodos = tuple(Nodo.model_validate_json(linea) for linea in contenidos["nodos.jsonl"].splitlines())
    aristas = tuple(Arista.model_validate_json(linea) for linea in contenidos["aristas.jsonl"].splitlines())
    datos_conocimiento = json.loads(contenidos["conocimiento.json"])
    conocimiento = ArchivoConocimiento.model_validate(datos_conocimiento) if datos_conocimiento is not None else None
    if conocimiento is not None:
        validar_archivo_conocimiento(conocimiento, curriculo, catalogo=catalogo)
    alineaciones = None
    if manifest.version in {"producto-3", "producto-4"}:
        datos = json.loads(contenidos["alineaciones.json"])
        if datos is not None:
            alineaciones = ArchivoAlineaciones.model_validate(datos)
            validar_archivo_alineaciones(alineaciones, curriculo)
    mejoras = None
    if manifest.version == "producto-4":
        mejoras = ArchivoMejoras.model_validate_json(contenidos["mejoras.json"])
        validar_archivo_mejoras(mejoras, curriculo, catalogo)
    if manifest.nodos != dict(Counter(n.tipo.value for n in nodos)) or (
        manifest.aristas != dict(Counter(a.tipo.value for a in aristas))
    ):
        raise ValueError("Los conteos del manifiesto no corresponden al grafo")
    _verificar_grafo(curriculo, catalogo, nodos, aristas, conocimiento, alineaciones, mejoras)
    derivados = {
        nombre: json.loads(contenidos[nombre])
        for nombre in ("diagnostico_v4.json", "alertas_v4.json", "publicacion.json")
    }
    for datos in derivados.values():
        if (
            not isinstance(datos, dict)
            or datos.get("version_curriculo") != "V4"
            or (datos.get("huella_curriculo") != curriculo.huella)
        ):
            raise ValueError("Derivado de otra versión o huella curricular")
    return ProductoMaterializado(
        ruta_grafo=base,
        manifest=manifest,
        curriculo=curriculo,
        catalogo=catalogo,
        nodos=nodos,
        aristas=aristas,
        diagnostico=derivados["diagnostico_v4.json"],
        alertas=derivados["alertas_v4.json"],
        publicacion=derivados["publicacion.json"],
        conocimiento=conocimiento,
        alineaciones=alineaciones,
        mejoras=mejoras,
    )


def publicar_producto(
    *,
    destino: Path,
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas,
    nodos: list[Nodo],
    aristas: list[Arista],
    diagnostico: dict,
    alertas: dict,
    publicacion: dict,
    conocimiento: ArchivoConocimiento | None = None,
    alineaciones: ArchivoAlineaciones | None = None,
    mejoras: ArchivoMejoras | None = None,
) -> dict:
    """Escribe una generación completa y cambia el puntero solo después de verificarla."""
    import fcntl

    if conocimiento is not None:
        validar_archivo_conocimiento(conocimiento, curriculo, catalogo=catalogo)
    if alineaciones is not None:
        validar_archivo_alineaciones(alineaciones, curriculo)
    if mejoras is not None:
        validar_archivo_mejoras(mejoras, curriculo, catalogo)
    _verificar_grafo(curriculo, catalogo, tuple(nodos), tuple(aristas), conocimiento, alineaciones, mejoras)
    base = _destino(destino, crear=True)
    snapshots = _segura(base, "snapshots")
    snapshots.mkdir(exist_ok=True)
    contenidos = {
        "curriculo.json": curriculo.model_dump_json().encode() + b"\n",
        "catalogo.json": catalogo.model_dump_json().encode() + b"\n",
        "nodos.jsonl": b"".join(json_bytes(n.model_dump(mode="json", exclude_none=True)) + b"\n" for n in nodos),
        "aristas.jsonl": b"".join(json_bytes(a.model_dump(mode="json", exclude_none=True)) + b"\n" for a in aristas),
        "diagnostico_v4.json": json_bytes(diagnostico) + b"\n",
        "alertas_v4.json": json_bytes(alertas) + b"\n",
        "publicacion.json": json_bytes(publicacion) + b"\n",
        "conocimiento.json": json_bytes(conocimiento.model_dump(mode="json") if conocimiento else None) + b"\n",
    }
    huellas = {n: sha(c) for n, c in contenidos.items()}
    formato = "producto-3" if alineaciones is not None else "producto-2"
    if alineaciones is not None:
        contenidos["alineaciones.json"] = alineaciones.model_dump_json().encode() + b"\n"
        huellas["alineaciones.json"] = sha(contenidos["alineaciones.json"])
    if mejoras is not None:
        formato = "producto-4"
        if alineaciones is None:
            contenidos["alineaciones.json"] = b"null\n"
            huellas["alineaciones.json"] = sha(contenidos["alineaciones.json"])
        contenidos["mejoras.json"] = mejoras.model_dump_json().encode() + b"\n"
        huellas["mejoras.json"] = sha(contenidos["mejoras.json"])
    identidad = _identidad(huellas, formato)
    manifest = ManifestProducto(
        version=formato,
        snapshot_id=identidad,
        huella_curriculo=curriculo.huella,
        huella_catalogo=huellas["catalogo.json"],
        nodos=dict(sorted(Counter(n.tipo.value for n in nodos).items())),
        aristas=dict(sorted(Counter(a.tipo.value for a in aristas).items())),
        sha256=huellas,
        bytes={n: len(c) for n, c in contenidos.items()},
        limites=LIMITES,
    )
    manifest_bytes = manifest.model_dump_json().encode() + b"\n"
    manifest_sha = sha(manifest_bytes)
    final = _segura(base, f"snapshots/{identidad}")
    temporal = Path(tempfile.mkdtemp(prefix=".publicando-", dir=base))
    try:
        for nombre, contenido in contenidos.items():
            _escribir_archivo(temporal / nombre, contenido)
        _escribir_archivo(temporal / "manifest.json", manifest_bytes)
        _sincronizar(temporal)
        _cargar_snapshot(temporal, manifest_sha, identidad)
        with _segura(base, ".publicacion.lock").open("a+b") as bloqueo:
            fcntl.flock(bloqueo, fcntl.LOCK_EX)
            try:
                if final.exists():
                    _cargar_snapshot(final, manifest_sha, identidad)
                else:
                    temporal.replace(final)
                    _sincronizar(snapshots)
                puntero = _Puntero(
                    version=formato, version_curriculo="V4", snapshot_id=identidad, manifest_sha256=manifest_sha
                )
                actual = _segura(base, "actual.json")
                with tempfile.NamedTemporaryFile(prefix=".actual-", dir=base, delete=False) as salida:
                    nombre_temporal = Path(salida.name)
                    salida.write(puntero.model_dump_json().encode() + b"\n")
                    salida.flush()
                    os.fsync(salida.fileno())
                try:
                    nombre_temporal.replace(actual)
                    _sincronizar(base)
                finally:
                    nombre_temporal.unlink(missing_ok=True)
            finally:
                fcntl.flock(bloqueo, fcntl.LOCK_UN)
    finally:
        shutil.rmtree(temporal, ignore_errors=True)
    return manifest.model_dump(mode="json") | {"ruta_grafo": str(final), "destino": str(base)}


def cargar_producto(destino: Path) -> ProductoMaterializado:
    """Fija un puntero una vez; valida todos los bytes antes de exponer una generación."""
    base = _destino(destino, crear=False)
    puntero = _Puntero.model_validate_json(_segura(base, "actual.json").read_bytes())
    snapshot = _segura(base, f"snapshots/{puntero.snapshot_id}")
    producto = _cargar_snapshot(snapshot, puntero.manifest_sha256, puntero.snapshot_id)
    if producto.manifest.version != puntero.version:
        raise ValueError("El puntero y el manifiesto indican formatos distintos")
    return producto
