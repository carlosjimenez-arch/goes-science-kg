"""Immutable SQLite teacher library with fingerprints, full validation, and query indexes."""

from __future__ import annotations

import json
import logging
import sqlite3
from collections import Counter
from contextlib import closing
from pathlib import Path
from threading import Lock

from goes_science_kg.archivos import destino_generado
from goes_science_kg.interfaz.consulta import normalizar
from goes_science_kg.materiales.compilacion import serializar, sha

LOGGER = logging.getLogger(__name__)
VERSION = "biblioteca-docente-1"
# Las páginas se ordenan por grado y título para docentes; el id desempata de forma determinista.
COLUMNAS = "id,version_curriculo,tipo,titulo,asignatura,unidad,fila_id,estado,sha256"
SQL = """
CREATE TABLE materiales (
 id TEXT PRIMARY KEY, version_curriculo TEXT NOT NULL, tipo TEXT NOT NULL, titulo TEXT NOT NULL,
 asignatura TEXT NOT NULL, unidad TEXT NOT NULL, fila_id TEXT NOT NULL, estado TEXT NOT NULL,
 sha256 TEXT NOT NULL, documento BLOB NOT NULL, texto_busqueda TEXT NOT NULL
);
CREATE TABLE grados (material_id TEXT REFERENCES materiales(id), grado INTEGER CHECK(grado BETWEEN 2 AND 11),
 PRIMARY KEY(material_id, grado));
CREATE TABLE archivos (sha256 TEXT PRIMARY KEY, contenido BLOB NOT NULL);
CREATE TABLE rutas (ruta TEXT PRIMARY KEY, sha256 TEXT NOT NULL REFERENCES archivos(sha256));
CREATE INDEX material_seleccion ON materiales(version_curriculo,tipo,asignatura);
CREATE INDEX material_fila ON materiales(fila_id);
CREATE INDEX material_grado ON grados(grado,material_id);
"""


def _firma(p):
    if p.is_symlink() or not p.is_file():
        raise ValueError("La biblioteca requiere archivos regulares")
    s = p.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns


def _conectar(p):
    db = sqlite3.connect(p.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA trusted_schema=OFF")
    db.row_factory = sqlite3.Row
    return db


def construir(registros: list[dict], archivos: dict[str, bytes], destino: Path, *, procedencia: dict) -> dict:
    """Write a new immutable library database and manifest into an empty destination."""
    destino_generado(destino / "biblioteca.sqlite")
    destino_generado(destino / "manifest.json")
    if destino.exists() or destino.is_symlink():
        raise ValueError("La compilación requiere un directorio nuevo")
    ordenados = sorted(registros, key=lambda r: r["id"])
    if not ordenados or len({r["id"] for r in ordenados}) != len(ordenados):
        raise ValueError("Los materiales deben tener identidades únicas y no estar vacíos")
    destino.mkdir(parents=True)
    base = destino / "biblioteca.sqlite"
    with closing(sqlite3.connect(base)) as db:
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SQL)
        for registro in ordenados:
            documento = serializar(registro["documento"])
            valores = [registro[c] for c in COLUMNAS.split(",")[:-1]]
            texto = normalizar(" ".join(str(registro[c]) for c in ("titulo", "unidad", "asignatura", "id", "fila_id")))
            if registro["tipo"] == "guion_clase":
                texto += " " + normalizar(registro["documento"]["guion"]["objetivo"])
            elif registro["tipo"] == "guion_unidad":
                texto += " " + normalizar(" ".join(g["objetivo"] for g in registro["documento"]["guiones"]))
            db.execute(
                "INSERT INTO materiales VALUES (?,?,?,?,?,?,?,?,?,?,?)", (*valores, sha(documento), documento, texto)
            )
            db.executemany("INSERT INTO grados VALUES (?,?)", [(registro["id"], g) for g in registro["grados"]])
        for ruta, contenido in sorted(archivos.items()):
            digest = sha(contenido)
            db.execute("INSERT OR IGNORE INTO archivos VALUES (?,?)", (digest, contenido))
            db.execute("INSERT INTO rutas VALUES (?,?)", (ruta, digest))
        db.commit()
        db.execute("VACUUM")
    contenido = base.read_bytes()
    manifest = {
        "version": VERSION,
        "biblioteca": {"archivo": "biblioteca.sqlite", "sha256": sha(contenido), "bytes": len(contenido)},
        "materiales": len(registros),
        "por_tipo": dict(sorted(Counter(r["tipo"] for r in registros).items())),
        "por_version": dict(sorted(Counter(r["version_curriculo"] for r in registros).items())),
        "por_estado": dict(sorted(Counter(r["estado"] for r in registros).items())),
        "originales": {r: {"sha256": sha(b), "bytes": len(b)} for r, b in sorted(archivos.items())},
        "procedencia": procedencia,
        "llamadas_modelos_compilacion": 0,
    }
    manifest["id"] = sha(serializar(manifest))
    (destino / "manifest.json").write_bytes(serializar(manifest))
    Biblioteca(destino).validar()
    LOGGER.info("VERDE biblioteca compilada: %s materiales, %s archivos originales", len(registros), len(archivos))
    return manifest


class Biblioteca:
    """Pin the generation on load; any later modification invalidates the instance."""

    def __init__(self, destino: Path):
        self.destino = destino
        self.base = destino / "biblioteca.sqlite"
        self.archivo_manifest = destino / "manifest.json"
        self._lock = Lock()
        self._invalida = False
        self._firmas = self._observar()
        self.manifest = json.loads(self.archivo_manifest.read_bytes())
        m = self.manifest
        if m["version"] != VERSION or m["id"] != sha(serializar({k: v for k, v in m.items() if k != "id"})):
            raise ValueError("Manifest de biblioteca incompatible")
        contenido = self.base.read_bytes()
        if (len(contenido), sha(contenido)) != (m["biblioteca"]["bytes"], m["biblioteca"]["sha256"]):
            raise ValueError("La biblioteca no corresponde al manifest")
        self.comprobar()

    def _observar(self):
        # La carpeta publicada y todos sus antecesores deben ser propios.
        if any(p.is_symlink() for p in (self.destino, *self.destino.parents)):
            raise ValueError("La biblioteca no admite directorios enlazados")
        return _firma(self.base), _firma(self.archivo_manifest)

    def comprobar(self):
        """Fail closed if the loaded library files changed after startup."""
        with self._lock:
            try:
                if self._invalida or self._firmas != self._observar():
                    raise ValueError("La biblioteca cambió tras cargarse; restaure y reinicie el servicio")
            except (ValueError, OSError):
                self._invalida = True
                raise

    def validar(self):
        """Run SQLite integrity checks and verify every record against the manifest."""
        self.comprobar()
        with closing(_conectar(self.base)) as db:
            if (
                db.execute("PRAGMA integrity_check").fetchone()[0] != "ok"
                or db.execute("PRAGMA foreign_key_check").fetchall()
            ):
                raise ValueError("La biblioteca no supera la verificación de integridad")
            filas = db.execute("SELECT documento,sha256,tipo,version_curriculo,estado FROM materiales").fetchall()
            if len(filas) != self.manifest["materiales"]:
                raise ValueError("Denominador de materiales incompatible")
            for r in filas:
                if sha(r["documento"]) != r["sha256"] or not isinstance(json.loads(r["documento"]), dict):
                    raise ValueError("Contenido de material modificado")
            for campo, clave in (("tipo", "por_tipo"), ("version_curriculo", "por_version"), ("estado", "por_estado")):
                if dict(Counter(r[campo] for r in filas)) != self.manifest[clave]:
                    raise ValueError("Conteos incompatibles con el manifest")
            originales = {}
            for r in db.execute("SELECT ruta,sha256,contenido FROM rutas JOIN archivos USING(sha256)"):
                if sha(r["contenido"]) != r["sha256"]:
                    raise ValueError("Archivo original modificado")
                originales[r["ruta"]] = {"sha256": r["sha256"], "bytes": len(r["contenido"])}
            if originales != self.manifest["originales"]:
                raise ValueError("Inventario original incompatible")
        self.comprobar()
        return self.manifest

    @staticmethod
    def _ficha(db, row):
        d = dict(row)
        d["grados"] = [
            r[0] for r in db.execute("SELECT grado FROM grados WHERE material_id=? ORDER BY grado", (d["id"],))
        ]
        return d

    def listar(self, *, version="V4", tipo=None, grado=None, asignatura=None, fila_id=None, q="", limite=40, offset=0):
        """Return a filtered, paginated page of material summaries."""
        self.comprobar()
        if not 1 <= limite <= 200 or not 0 <= offset <= 100000 or len(q) > 200:
            raise ValueError("Consulta fuera de límites")
        filtros, valores = ["version_curriculo=?"], [version]
        for campo, valor in (("tipo", tipo), ("asignatura", asignatura), ("fila_id", fila_id)):
            if valor is not None:
                filtros.append(f"{campo}=?")
                valores.append(valor)
        if grado is not None:
            filtros.append("id IN (SELECT material_id FROM grados WHERE grado=?)")
            valores.append(grado)
        if q.strip():
            filtros.append("instr(texto_busqueda,?)>0")
            valores.append(normalizar(q).strip())
        # Sólo se concatenan fragmentos SQL constantes; todo valor del usuario va como parámetro «?».
        condicion = " AND ".join(filtros)
        with closing(_conectar(self.base)) as db:
            total = db.execute("SELECT COUNT(*) FROM materiales WHERE " + condicion, valores).fetchone()[0]  # nosec B608
            registros = db.execute(  # nosec B608
                "SELECT "
                + COLUMNAS
                + " FROM materiales WHERE "
                + condicion
                + " ORDER BY (SELECT MIN(grado) FROM grados WHERE material_id=materiales.id), titulo, id"
                + " LIMIT ? OFFSET ?",
                (*valores, limite, offset),
            ).fetchall()
            salida = {
                "biblioteca_id": self.manifest["id"],
                "total": total,
                "limite": limite,
                "offset": offset,
                "materiales": [self._ficha(db, r) for r in registros],
            }
        self.comprobar()
        return salida

    def detalle(self, id_):
        """Return one material with its full document and provenance."""
        self.comprobar()
        with closing(_conectar(self.base)) as db:
            r = db.execute("SELECT " + COLUMNAS + ",documento FROM materiales WHERE id=?", (id_,)).fetchone()  # nosec B608
            if r is None:
                raise KeyError(id_)
            d = self._ficha(db, r)
            documento = d.pop("documento")
            if sha(documento) != d["sha256"]:
                raise ValueError("Documento alterado")
            d["documento"] = json.loads(documento)
        self.comprobar()
        return d

    def archivo(self, digest):
        """Return the original bytes stored under a SHA-256 digest."""
        self.comprobar()
        with closing(_conectar(self.base)) as db:
            r = db.execute("SELECT contenido FROM archivos WHERE sha256=?", (digest,)).fetchone()
            if r is None:
                raise KeyError(digest)
            contenido = r[0]
            if sha(contenido) != digest:
                raise ValueError("Archivo alterado")
            rutas = [r[0] for r in db.execute("SELECT ruta FROM rutas WHERE sha256=? ORDER BY ruta", (digest,))]
        self.comprobar()
        return contenido, rutas

    def exportar(self):
        """Copy the whole library into a derived generation without changing the selected one."""
        self.validar()
        with closing(_conectar(self.base)) as db:
            registros = []
            for fila in db.execute("SELECT " + COLUMNAS + ",documento FROM materiales ORDER BY id"):  # nosec B608
                r = self._ficha(db, fila)
                r["documento"] = json.loads(r["documento"])
                registros.append(r)
            archivos = {
                r["ruta"]: r["contenido"]
                for r in db.execute("SELECT ruta,contenido FROM rutas JOIN archivos USING(sha256) ORDER BY ruta")
            }
        self.comprobar()
        return registros, archivos
