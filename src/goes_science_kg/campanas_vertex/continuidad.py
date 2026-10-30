"""Detect SQLite-only rollback using durable reservation evidence outside that database."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from threading import RLock
from uuid import uuid4

from goes_science_kg.config import ruta

_CAMPOS = ("id", "ejecucion", "clave", "modelo", "rol", "reserva_usd", "creada")
_LOCKS: dict[str, RLock] = {}
_LOCKS_GUARDIA = RLock()


def _canonico(valor) -> bytes:
    return (
        json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


class ContinuidadCampana:
    """Fail closed when the durable external reservation set and the SQLite rows diverge."""

    def __init__(self, campana_id: str, plan_sha256: str, autorizacion_sha256: str):
        self.identidad = {
            "version": "continuidad-campana-vertex-1",
            "campana_id": campana_id,
            "plan_sha256": plan_sha256,
            "autorizacion_sha256": autorizacion_sha256,
        }
        carpeta_cruda = ruta("data/operaciones/campanas_vertex") / _sha(campana_id.encode())
        if any(p.is_symlink() for p in (carpeta_cruda, *carpeta_cruda.parents)):
            raise ValueError("La continuidad externa no puede usar enlaces simbólicos")
        carpeta = carpeta_cruda.resolve()
        if not carpeta.is_relative_to(ruta(".").resolve()):
            raise ValueError("La continuidad externa debe permanecer dentro del repositorio")
        self.archivo = carpeta / "reservas.json"
        self.lock = carpeta / "reservas.lock"
        with _LOCKS_GUARDIA:
            self._thread_lock = _LOCKS.setdefault(str(self.lock), RLock())

    @contextmanager
    def bloqueo(self):
        """Serialize readers and reservations across threads and local processes."""
        with self._thread_lock:
            if any(p.is_symlink() for p in (self.archivo.parent, *self.archivo.parents)):
                raise ValueError("La continuidad externa no puede usar enlaces simbólicos")
            self.archivo.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(self.lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                yield
            finally:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
                os.close(descriptor)

    def _leer(self) -> list[dict]:
        if self.archivo.is_symlink() or not self.archivo.is_file() or self.archivo.stat().st_size > 16_000_000:
            raise ValueError("Falta o es inválido el punto externo de continuidad de la campaña")
        try:
            documento = json.loads(self.archivo.read_bytes())
            reservas = documento["reservas"]
            if (
                {k: documento.get(k) for k in self.identidad} != self.identidad
                or not isinstance(reservas, list)
                or documento["reservas_sha256"] != _sha(_canonico(reservas))
                or any(set(r) != set(_CAMPOS) for r in reservas)
                or len({r["id"] for r in reservas}) != len(reservas)
            ):
                raise ValueError("El punto externo de continuidad cambió o pertenece a otra versión")
        except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
            raise ValueError("El punto externo de continuidad no conserva un documento válido") from error
        return reservas

    def _escribir(self, reservas: list[dict]) -> None:
        documento = self.identidad | {"reservas": reservas, "reservas_sha256": _sha(_canonico(reservas))}
        temporal = self.archivo.with_name("reservas." + uuid4().hex + ".tmp")
        try:
            with temporal.open("xb") as archivo:
                archivo.write(_canonico(documento))
                archivo.flush()
                os.fsync(archivo.fileno())
            os.replace(temporal, self.archivo)
            descriptor = os.open(self.archivo.parent, os.O_RDONLY)
            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
        finally:
            temporal.unlink(missing_ok=True)

    def filas(self, registro) -> list[dict]:
        """Read only immutable reservation fields; later usage/state updates do not reset spending."""
        with registro.conexion() as db:
            return [
                dict(fila)
                for fila in db.execute(
                    "SELECT " + ",".join(_CAMPOS) + " FROM llamadas WHERE ejecucion=? ORDER BY id",
                    (self.identidad["campana_id"],),
                )
            ]

    def inicializar(self, registro, *, nueva: bool) -> None:
        """Create an empty point once or compare an existing point without adopting missing evidence."""
        actuales = self.filas(registro)
        if nueva:
            if actuales or self.archivo.exists() or self.archivo.is_symlink():
                raise ValueError("No se adopta consumo ni continuidad externa anterior como una campaña nueva")
            self._escribir([])
        else:
            self.verificar(registro)

    def verificar(self, registro) -> None:
        """Block missing, rewound, altered, or unexpectedly advanced SQLite reservation sets."""
        if self._leer() != self.filas(registro):
            raise ValueError("La campaña diverge del punto externo de continuidad; posible restauración de SQLite")

    def registrar(self, registro, reserva: dict) -> None:
        """Persist a specific committed reservation durably before authorizing the external call."""
        anteriores = self._leer()
        if any(r["id"] == reserva["id"] for r in anteriores):
            raise ValueError("La reserva ya existe en la continuidad externa")
        nuevas = sorted([*anteriores, reserva], key=lambda r: r["id"])
        if nuevas != self.filas(registro):
            raise ValueError("La reserva SQL no corresponde exactamente al avance externo esperado")
        self._escribir(nuevas)
