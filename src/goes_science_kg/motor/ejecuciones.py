"""Invocación durable común: identidad de solicitud, entorno y presupuesto inmutables."""

from __future__ import annotations

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Protocol

from goes_science_kg.archivos import destino_generado
from goes_science_kg.motor.contratos import huella


class MotorPersistible(Protocol):
    def compilar(self, *, checkpointer=None):
        """Construye un workflow sin ejecutar modelos durante la compilación."""


def _identidad_presupuesto(motor: MotorPersistible, ejecucion_id: str) -> str | None:
    modelo = getattr(motor, "modelo", None)
    if hasattr(modelo, "ejecucion_id") and modelo.ejecucion_id != ejecucion_id:
        raise ValueError("El ID del proveedor no corresponde al presupuesto de esta ejecución")
    registro = getattr(modelo, "registro", None)
    if registro is None:
        return None
    archivo = Path(registro.archivo).resolve()
    identidad: dict = {"ruta": str(archivo)}
    if archivo.exists():
        estado = archivo.stat()
        identidad.update({"dispositivo": estado.st_dev, "inodo": estado.st_ino})
    return json.dumps(identidad, sort_keys=True)


def _vincular_presupuesto(db: sqlite3.Connection, ejecucion_id: str, identidad: str | None) -> None:
    if identidad is None:
        return
    db.execute("CREATE TABLE IF NOT EXISTS checkpoint_presupuestos (ejecucion TEXT PRIMARY KEY, ledger TEXT NOT NULL)")
    db.execute("BEGIN IMMEDIATE")
    anterior = db.execute("SELECT ledger FROM checkpoint_presupuestos WHERE ejecucion=?", (ejecucion_id,)).fetchone()
    if anterior is not None and anterior[0] != identidad:
        raise ValueError("La ejecución pertenece a otro ledger; no se reinicia ni divide su presupuesto")
    db.execute("INSERT OR IGNORE INTO checkpoint_presupuestos VALUES(?,?)", (ejecucion_id, identidad))
    db.commit()


@contextmanager
def _bloqueo(archivo: Path, nombre: str, *, esperar: bool = False) -> Iterator[None]:
    """Exclusión entre procesos y threads; el sistema libera el lock tras una interrupción."""
    import fcntl

    lock = archivo.with_name(f".{archivo.name}.{nombre}.lock")
    if lock.is_symlink():
        raise ValueError("El bloqueo del checkpoint no puede ser un enlace")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | (0 if esperar else fcntl.LOCK_NB))
        except BlockingIOError as error:
            raise ValueError("El mismo checkpoint ya está en curso; no se ejecuta dos veces") from error
        yield
    finally:
        os.close(descriptor)


def ejecutar_durable(
    motor: MotorPersistible,
    *,
    archivo: Path,
    solicitud: dict,
    thread_id: str,
    ejecucion_id: str,
    huella_entorno: str,
    max_concurrencia: int = 3,
    recursion_limit: int = 30,
) -> dict:
    """Reanuda un workflow sobre el mismo input; no crea ni reinicia un ledger.

    ``thread_id`` identifica el checkpoint; ``ejecucion_id`` identifica el presupuesto compartido.
    Una unidad puede tener varios threads, conservando un único ID de presupuesto en su proveedor.
    La exclusión por thread comprende lectura y ejecución; otros threads siguen siendo paralelos.
    Si el proveedor expone Registro, se fijan su ruta e identidad física sin reiniciar reservas.
    Antes de reutilizar un estado, el hook optativo ``motor.validar_estado(estado)`` debe comprobar
    localmente sus fuentes, sin consumir modelos. El controlador calcula la huella de datos/código;
    un motor sin ese hook conserva la responsabilidad de verificar sus fuentes antes de invocar.
    """
    from langgraph.checkpoint.sqlite import SqliteSaver

    if not thread_id or len(thread_id) > 500 or "\x00" in thread_id:
        raise ValueError("El identificador de checkpoint no es válido")
    if not ejecucion_id or not huella_entorno or not 1 <= max_concurrencia <= 16 or not 1 <= recursion_limit <= 100:
        raise ValueError("Se requieren identidad, entorno y límites válidos")
    # Canoniza tuplas/listas como JSON y rechaza NaN o valores que no sean datos serializables.
    datos = json.loads(json.dumps(solicitud, ensure_ascii=False, allow_nan=False))
    identidad_presupuesto = _identidad_presupuesto(motor, ejecucion_id)
    archivo = destino_generado(archivo)
    archivo.parent.mkdir(parents=True, exist_ok=True)
    with _bloqueo(archivo, huella({"thread_id": thread_id})), sqlite3.connect(
        archivo, check_same_thread=False, timeout=30
    ) as db:
        checkpointer = SqliteSaver(db)
        # Inicializar WAL y tablas en paralelo puede fallar aun con timeout SQLite. La exclusión
        # de esquema termina antes del workflow y no serializa otros threads de esta base.
        with _bloqueo(archivo, "esquema", esperar=True):
            checkpointer.setup()
            _vincular_presupuesto(db, ejecucion_id, identidad_presupuesto)
        flujo = motor.compilar(checkpointer=checkpointer)
        parametros = {
            "configurable": {"thread_id": thread_id},
            "max_concurrency": max_concurrencia,
            "recursion_limit": recursion_limit,
        }
        previo = flujo.get_state(parametros)
        if previo.values:
            if huella(previo.values.get("solicitud", {})) != huella(datos):
                raise ValueError("El ID pertenece a otra solicitud; usa un ID nuevo")
            if previo.values.get("huella_entorno") != huella_entorno:
                raise ValueError("Cambió el corpus, configuración o prompts; usa una ejecución nueva")
            if previo.values.get("ejecucion_id") != ejecucion_id:
                raise ValueError("El checkpoint pertenece a otro presupuesto; no se reasigna su ejecución")
            if validar := getattr(motor, "validar_estado", None):
                validar(previo.values)
            if not previo.next and previo.values.get("resultado"):
                return previo.values
        entrada = None if previo.values else {
            "solicitud": datos,
            "ejecucion_id": ejecucion_id,
            "huella_entorno": huella_entorno,
        }
        return flujo.invoke(entrada, parametros, durability="sync")
