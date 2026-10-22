"""Publish explicit graph derivatives and verify their article-level provenance."""

# Historical implementation notes:
# Un sidecar sólo se publica desde un generador que verificó sus entradas contra el
# archivo de grafo. Capturar archivos históricos juntos no acredita su procedencia.

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from threading import RLock

from goes_science_kg.config import raiz
from goes_science_kg.modelos import Arista, Nodo
from goes_science_kg.rag import GraphRAG

ARCHIVOS_GRAFO = ("nodos.jsonl", "aristas.jsonl")
DIRECTORIO_PUBLICACIONES = "data/grafo/publicaciones_api"


class PublicacionNoDisponible(RuntimeError):
    """Signal that an article cannot be verified against the pinned graph."""


def _sha(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


def _leer_grafo(base: Path) -> tuple[dict, dict[str, bytes]]:
    archivos = {nombre: (base / "data/grafo" / nombre).read_bytes() for nombre in (*ARCHIVOS_GRAFO, "manifest.json")}
    manifest = json.loads(archivos["manifest.json"])
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sha256"), dict):
        raise ValueError("El manifiesto no declara las huellas del grafo")
    if any(manifest["sha256"].get(nombre) != _sha(archivos[nombre]) for nombre in ARCHIVOS_GRAFO):
        raise ValueError("El grafo no coincide con las huellas de su manifiesto")
    return manifest, archivos


def _huella_modelos(modelos: Sequence[Nodo] | Sequence[Arista]) -> str:
    digest = hashlib.sha256()
    for modelo in modelos:
        linea = (
            json.dumps(
                modelo.model_dump(mode="json", exclude_none=True, exclude_defaults=True),
                ensure_ascii=False,
                sort_keys=True,
            )
            + "\n"
        )
        digest.update(linea.encode("utf-8"))
    return digest.hexdigest()


def comprobar_entrada(nodos: list[Nodo], aristas: list[Arista], *, base: Path | None = None) -> dict[str, str]:
    """Reject generators using foreign models or a graph being rewritten."""
    manifest, _ = _leer_grafo(base or raiz())
    esperadas = {nombre: manifest["sha256"][nombre] for nombre in ARCHIVOS_GRAFO}
    reales = dict(zip(ARCHIVOS_GRAFO, (_huella_modelos(nodos), _huella_modelos(aristas)), strict=True))
    if reales != esperadas:
        raise ValueError("Los modelos del generador no coinciden con el grafo persistido")
    return esperadas


def _ruta_sidecar(base: Path, articulo: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,120}", articulo):
        raise ValueError("Identificador de artículo inválido")
    destino = (base / DIRECTORIO_PUBLICACIONES / f"{articulo}.json").resolve()
    if not destino.is_relative_to(base.resolve()):
        raise ValueError("La publicación resuelve fuera del repositorio autorizado")
    return destino


def publicar_articulo(
    articulo: str, archivos: Sequence[str], grafo: dict[str, str], *, generador: str, base: Path | None = None
) -> None:
    """Publish regenerated derivatives only after checking inputs and outputs before and after writing."""

    # Implementation notes:
    # No es un comando de adopción de resultados históricos. Los llamadores deben
    # producir todos los archivos con los modelos validados por comprobar_entrada.
    base = (base or raiz()).resolve()
    manifest, _ = _leer_grafo(base)
    if any(manifest["sha256"].get(nombre) != grafo.get(nombre) for nombre in ARCHIVOS_GRAFO):
        raise ValueError("El grafo cambió durante la generación; no se publica el artículo")
    contenidos = {}
    for relativo in archivos:
        archivo = (base / relativo).resolve()
        if not archivo.is_relative_to(base) or Path(relativo).is_absolute():
            raise ValueError("Los derivados deben estar dentro del repositorio")
        contenidos[relativo] = archivo.read_bytes()
    despues, _ = _leer_grafo(base)
    if any(despues["sha256"].get(nombre) != grafo.get(nombre) for nombre in ARCHIVOS_GRAFO):
        raise ValueError("El grafo cambió durante la generación; no se publica el artículo")
    if any((base / relativo).read_bytes() != contenido for relativo, contenido in contenidos.items()):
        raise ValueError("Los derivados cambiaron durante su publicación")
    datos = {
        "esquema_version": "1",
        "articulo": articulo,
        "generador": generador,
        "grafo": grafo,
        "archivos": {relativo: _sha(contenido) for relativo, contenido in contenidos.items()},
    }
    destino = _ruta_sidecar(base, articulo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destino.parent, delete=False) as salida:
            temporal = Path(salida.name)
            json.dump(datos, salida, ensure_ascii=False, indent=2, sort_keys=True)
            salida.write("\n")
        os.replace(temporal, destino)
    finally:
        if temporal is not None:
            temporal.unlink(missing_ok=True)


class LecturaPublicada:
    """Pin graph and article identities until process restart."""

    # Implementation notes:
    # Los artículos aún no cargados pueden publicarse después si pertenecen al mismo
    # grafo. Un artículo inválido nunca invalida otro ni los servicios del grafo.

    def __init__(self, base: Path):
        self.base = base.resolve()
        self._lock = RLock()
        self._error_grafo: str | None = None
        self._errores_articulos: dict[str, str] = {}
        self._articulos: dict[str, dict[str, bytes]] = {}
        try:
            manifest, self._bytes_grafo = _leer_grafo(self.base)
            nodos = [Nodo.model_validate_json(linea) for linea in self._bytes_grafo["nodos.jsonl"].splitlines()]
            aristas = [Arista.model_validate_json(linea) for linea in self._bytes_grafo["aristas.jsonl"].splitlines()]
            por_id = {n.id: n for n in nodos}
            if len(por_id) != len(nodos) or any(a.origen not in por_id or a.destino not in por_id for a in aristas):
                raise ValueError("El grafo contiene identificadores duplicados o relaciones sin nodo")
            if manifest.get("nodos") != dict(Counter(n.tipo.value for n in nodos)) or manifest.get("aristas") != dict(
                Counter(a.tipo.value for a in aristas)
            ):
                raise ValueError("Los conteos del manifiesto no corresponden a los modelos del grafo")
            self._manifest = manifest
            self._grafo = por_id, aristas, GraphRAG(nodos, aristas)
            self.verificar_grafo()
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise PublicacionNoDisponible(f"Grafo no disponible: {error}") from error

    def verificar_grafo(self) -> None:
        """Verify that persisted graph files still match the generation pinned by this reader."""

        with self._lock:
            if self._error_grafo:
                raise PublicacionNoDisponible(self._error_grafo)
            try:
                if any(
                    (self.base / "data/grafo" / nombre).read_bytes() != contenido
                    for nombre, contenido in self._bytes_grafo.items()
                ):
                    raise ValueError("Los archivos del grafo cambiaron")
            except (OSError, ValueError) as error:
                self._error_grafo = f"Grafo modificado o inaccesible; reinicia el servicio tras publicar: {error}"
                raise PublicacionNoDisponible(self._error_grafo) from error

    def grafo(self):
        """Return the pinned graph models and reusable retrieval index."""

        self.verificar_grafo()
        return self._grafo

    def manifest(self) -> dict:
        """Return the verified manifest for this reader's pinned graph."""

        self.verificar_grafo()
        return json.loads(self._bytes_grafo["manifest.json"])

    def articulos_cargados(self) -> tuple[str, ...]:
        """Retain known article identities even if their files disappear."""
        with self._lock:
            return tuple(sorted(self._articulos))

    def articulo(self, nombre: str, archivos: Sequence[str]) -> dict[str, object]:
        """Read only endpoint-approved paths rather than arbitrary sidecar paths."""
        with self._lock:
            self.verificar_grafo()
            if nombre in self._errores_articulos:
                raise PublicacionNoDisponible(self._errores_articulos[nombre])
            try:
                sidecar = _ruta_sidecar(self.base, nombre)
            except ValueError as error:
                raise PublicacionNoDisponible(f"{nombre}: destino de publicación no autorizado") from error
            relativos = [*archivos, sidecar.relative_to(self.base).as_posix()]
            if nombre in self._articulos:
                capturados = self._articulos[nombre]
                try:
                    if set(capturados) != set(relativos) or any(
                        (self.base / relativo).read_bytes() != contenido for relativo, contenido in capturados.items()
                    ):
                        raise ValueError("El artículo cambió después de cargarlo")
                except (OSError, ValueError) as error:
                    detalle = f"{nombre}: publicación modificada; reinicia el servicio: {error}"
                    self._errores_articulos[nombre] = detalle
                    raise PublicacionNoDisponible(detalle) from error
            else:
                try:
                    capturados = {relativo: (self.base / relativo).read_bytes() for relativo in relativos}
                    publicacion = json.loads(capturados[relativos[-1]])
                    if publicacion.get("esquema_version") != "1" or publicacion.get("articulo") != nombre:
                        raise ValueError("Sidecar inválido")
                    if publicacion.get("grafo") != {n: self._manifest["sha256"][n] for n in ARCHIVOS_GRAFO}:
                        raise ValueError("El artículo fue generado con otro grafo")
                    if publicacion.get("archivos") != {r: _sha(capturados[r]) for r in archivos}:
                        raise ValueError("El artículo no coincide con su publicación")
                    for relativo in archivos:
                        json.loads(capturados[relativo])
                    if any((self.base / relativo).read_bytes() != valor for relativo, valor in capturados.items()):
                        raise ValueError("El artículo cambió durante su lectura")
                    self.verificar_grafo()
                    self._articulos[nombre] = capturados
                except (OSError, ValueError, TypeError, AttributeError) as error:
                    raise PublicacionNoDisponible(f"{nombre}: no hay publicación verificable: {error}") from error
            self.verificar_grafo()
            return {relativo: json.loads(capturados[relativo]) for relativo in archivos}
