"""Package portable SHA inventories and consistent SQLite backups."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import tempfile
import time
import zipfile
from contextlib import closing
from pathlib import Path, PurePosixPath

from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto.almacen import cargar_producto

LOGGER = logging.getLogger(__name__)
RAICES = (
    "insumos/v4",
    "data/producto",
    "data/fuentes",
    "data/grafo",
    "data/evaluacion",
    "data/referencias_2026",
    "data/referencias_paises_2026",
    "data/referencias_cientificas_2026",
    "data/referencias_progresiones_2026",
    "data/referencias_web_cientificas_2026",
    "src",
    "tests",
    "config",
    "docs",
    "prompts",
    "specs",
    "scripts",
    ".github",
    ".claude",
)
SIMPLES = (
    "insumos/procedencia_v4.json",
    "pyproject.toml",
    "uv.lock",
    "README.md",
    "CLAUDE.md",
    "HANDOFF.md",
    "HANDOFF_INTERNACIONAL.md",
    "CONTRIBUTING.md",
    "NOTICE",
    ".gitignore",
    ".gitattributes",
    "Makefile",
)
SQLITES = (
    "data/operaciones/registro.sqlite",
    "data/operaciones/checkpoints.sqlite",
    "data/operaciones/alineacion_checkpoints.sqlite",
    "data/operaciones/conocimiento_checkpoints.sqlite",
    "data/operaciones/unidades/checkpoints_unidades.sqlite",
    "data/operaciones/mejoras_checkpoints.sqlite",
    "data/operaciones/mejoras_controles.sqlite",
)
EXTENSIONES = {
    ".pdf",
    ".xlsx",
    ".docx",
    ".html",
    ".json",
    ".jsonl",
    ".md",
    ".csv",
    ".yaml",
    ".yml",
    ".txt",
    ".py",
    ".toml",
    ".lock",
    ".js",
    ".cjs",
    ".css",
    ".woff2",
    ".svg",
    ".png",
}


def nombre_seguro(nombre: str) -> str:
    """Validate a safe relative artifact name without traversal or absolute paths."""

    p = PurePosixPath(nombre)
    if (
        p.is_absolute()
        or ".." in p.parts
        or "\\" in nombre
        or any(
            x
            in {".env", ".envrc", ".git", ".aws", "credentials", "application_default_credentials.json", "__pycache__"}
            for x in p.parts
        )
    ):
        raise ValueError("Ruta de archivo no autorizada en el respaldo")
    if not p.parts or p.as_posix() != nombre:
        raise ValueError("Ruta de archivo ambigua")
    return nombre


def seleccionar_artefactos(raiz: Path) -> list[str]:
    """Select explicitly configured artifacts while excluding secrets and transient files."""

    producto = cargar_producto(raiz / "data/producto/V4")
    seleccion = set()
    actual = producto.manifest.snapshot_id
    for directorio in RAICES:
        for archivo in (raiz / directorio).rglob("*"):
            if archivo.is_symlink():
                raise ValueError("No se respaldan enlaces simbólicos ni destinos implícitos")
            if not archivo.is_file() or archivo.suffix.lower() not in EXTENSIONES:
                continue
            rel = archivo.relative_to(raiz).as_posix()
            if any(p.startswith(".") for p in archivo.relative_to(raiz / directorio).parts):
                continue
            if (
                rel.startswith("data/producto/V4/snapshots/")
                and archivo.relative_to(raiz / "data/producto/V4/snapshots").parts[0] != actual
            ):
                continue
            seleccion.add(nombre_seguro(rel))
    seleccion.update(p for p in SIMPLES if (raiz / p).is_file())
    seleccion.update(p for p in SQLITES if (raiz / p).is_file())
    seleccion.update(p.relative_to(raiz).as_posix() for p in (raiz / "data/operaciones/archivos_codigo").glob("*.zip"))
    return sorted(seleccion)


BACKUP_SEGUNDOS = 300
BLOQUEO_SEGUNDOS = 5


def _sqlite_con_auxiliares(archivo: Path) -> bool:
    return any(
        (aux := archivo.with_name(archivo.name + sufijo)).exists() and aux.stat().st_size
        for sufijo in ("-wal", "-journal")
    )


def _bytes_sqlite_estables(archivo: Path) -> bytes | None:
    """Read a non-WAL database byte for byte under a SHARED lock, or return None when that is not provable."""
    # Conservar los bytes exactos mantiene las bases fijadas por SHA (p. ej. la biblioteca docente); backup() las
    # reescribiría. El bloqueo SHARED impide que un escritor vuelque páginas sin confirmar (incluso con journal en
    # memoria) mientras se leen; ante cualquier duda se usa backup().
    if _sqlite_con_auxiliares(archivo):
        return None
    antes = archivo.stat()
    try:
        with closing(
            sqlite3.connect(archivo.as_uri() + "?mode=ro", uri=True, timeout=BLOQUEO_SEGUNDOS, isolation_level=None)
        ) as db:
            if db.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal":
                return None
            db.execute("BEGIN")
            db.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()
            contenido = archivo.read_bytes()
            db.execute("COMMIT")
    except sqlite3.Error:
        return None
    despues = archivo.stat()
    if _sqlite_con_auxiliares(archivo) or (antes.st_ino, antes.st_size, antes.st_mtime_ns) != (
        despues.st_ino,
        despues.st_size,
        despues.st_mtime_ns,
    ):
        return None
    return contenido


def _copia_consistente(archivo: Path, copia: Path) -> bytes:
    """Copy a live database with SQLite's online backup, failing closed instead of waiting forever."""
    limite = time.monotonic() + BACKUP_SEGUNDOS

    def progreso(_estado, _restantes, _total):
        if time.monotonic() > limite:
            raise TimeoutError("Un escritor SQLite bloquea el respaldo; cierre la ejecución antes de preparar")

    origen = archivo.as_uri() + "?mode=ro"
    with closing(sqlite3.connect(origen, uri=True, timeout=BLOQUEO_SEGUNDOS)) as original, original:
        with closing(sqlite3.connect(copia)) as receptor, receptor:
            original.backup(receptor, pages=256, progress=progreso, sleep=0.05)
    contenido = copia.read_bytes()
    copia.unlink()
    return contenido


def crear_paquete(raiz: Path, archivos: list[str], destino: Path, *, max_bytes: int = 1024**3) -> dict:
    """Inventory exact bytes without implicit roots or external credentials."""
    raiz = raiz.resolve()
    if len(archivos) != len(set(archivos)) or not archivos:
        raise ValueError("Se requieren archivos únicos en una selección explícita")
    if destino.exists() or destino.is_symlink():
        raise ValueError("El paquete de respaldo debe ser un archivo nuevo")
    inventario, total = {}, 0
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="goes-ciencias-sqlite-") as temporal:
        with zipfile.ZipFile(destino, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zip_:
            for rel in sorted(archivos):
                nombre_seguro(rel)
                archivo = raiz / rel
                if archivo.is_symlink() or not archivo.resolve().is_relative_to(raiz) or not archivo.is_file():
                    raise ValueError("El inventario sale de la raíz o contiene un archivo no regular")
                exacto = _bytes_sqlite_estables(archivo) if archivo.suffix == ".sqlite" else archivo.read_bytes()
                consistente = exacto is None
                contenido = (
                    _copia_consistente(archivo, Path(temporal) / "consistente.sqlite") if consistente else exacto
                )
                total += len(contenido)
                if total > max_bytes:
                    raise ValueError("El respaldo excede su cota declarada de bytes")
                inventario[rel] = {
                    "sha256": hashlib.sha256(contenido).hexdigest(),
                    "bytes": len(contenido),
                    "copia_sqlite_consistente": consistente,
                }
                info = zipfile.ZipInfo(rel, date_time=(2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100600 << 16
                zip_.writestr(info, contenido)
            manifest = {
                "version": "respaldo-ciencias-1",
                "archivos": inventario,
                "bytes_sin_comprimir": total,
                "huella_inventario": huella(inventario),
            }
            zip_.writestr("MANIFEST_RESPALDO.json", json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    digest = hashlib.sha256(destino.read_bytes()).hexdigest()
    LOGGER.info("VERDE paquete privado: %d archivos; %d bytes comprimidos", len(inventario), destino.stat().st_size)
    return {
        "archivo": str(destino),
        "sha256": digest,
        "bytes": destino.stat().st_size,
        "archivos": len(inventario),
        "huella_inventario": huella(inventario),
    }


def restaurar_paquete(archivo: Path, destino: Path, *, sha256: str, max_bytes: int = 1024**3) -> dict:
    """Restore into an empty directory without unsafe extraction, links, or overwrites."""
    if hashlib.sha256(archivo.read_bytes()).hexdigest() != sha256:
        raise ValueError("El paquete no conserva su SHA de recepción")
    if destino.is_symlink() or (destino.exists() and (not destino.is_dir() or any(destino.iterdir()))):
        raise ValueError("Restaurar requiere un directorio vacío y propio")
    with zipfile.ZipFile(archivo) as zip_:
        registros = zip_.infolist()
        nombres = [p.filename for p in registros]
        if len(nombres) != len(set(nombres)) or sum(p.file_size for p in registros) > max_bytes:
            raise ValueError("Archivo duplicado o respaldo fuera de presupuesto")
        manifest = json.loads(zip_.read("MANIFEST_RESPALDO.json"))
        inventario = manifest["archivos"]
        if manifest.get("version") != "respaldo-ciencias-1" or manifest.get("huella_inventario") != huella(inventario):
            raise ValueError("El manifiesto no conserva su inventario")
        if set(nombres) != set(inventario) | {"MANIFEST_RESPALDO.json"}:
            raise ValueError("Hay archivos omitidos o no declarados en el respaldo")
        for p in registros:
            if p.filename == "MANIFEST_RESPALDO.json":
                continue
            nombre_seguro(p.filename)
            if ((p.external_attr >> 16) & 0o170000) != 0o100000:
                raise ValueError("Sólo se restauran archivos regulares")
            contenido = zip_.read(p)
            esperado = inventario[p.filename]
            if len(contenido) != esperado["bytes"] or hashlib.sha256(contenido).hexdigest() != esperado["sha256"]:
                raise ValueError("Un archivo no conserva sus bytes originales")
        destino.mkdir(parents=True, exist_ok=True)
        for rel in inventario:
            salida = destino / rel
            salida.parent.mkdir(parents=True, exist_ok=True)
            with salida.open("xb") as stream:
                stream.write(zip_.read(rel))
    return {"archivos_restaurados": len(inventario), "huella_inventario": huella(inventario)}
