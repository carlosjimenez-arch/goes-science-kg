"""Application services for verified curriculum queries and local operations."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable
from contextlib import closing
from pathlib import Path
from threading import Lock

from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila
from goes_science_kg.interfaz.consulta import ConsultaInterfaz
from goes_science_kg.producto.runtime import RuntimeProducto

LOGGER = logging.getLogger(__name__)


class FuenteNoDisponible(ValueError):
    """The requested row cannot be verified against its original source."""


class ServicioInterfaz:
    """Reuse one projection while revalidating the published snapshot on every request.

    The reader owns snapshot integrity and invalidation. This service owns query
    indexes and source verification; HTTP handlers only translate its results.
    """

    def __init__(self, leer: Callable[[], RuntimeProducto]) -> None:
        self._leer = leer
        self._consulta: ConsultaInterfaz | None = None
        self._lock = Lock()

    def consultar(self) -> ConsultaInterfaz:
        """Return the projection of the current, verified runtime."""
        runtime = self._leer()
        with self._lock:
            if self._consulta is None or self._consulta.runtime is not runtime:
                self._consulta = ConsultaInterfaz(runtime)
            return self._consulta

    @staticmethod
    def verificar_fila(consulta: ConsultaInterfaz, fila_id: str) -> None:
        """Reopen the original cells before exposing a detail or compiling a brief."""
        try:
            documento = documento_de_fila(consulta.filas[fila_id])
            if not consulta.runtime.fuentes.hidratar_celdas(documento):
                raise ValueError("La fuente no contiene celdas verificables")
        except (ValueError, KeyError, OSError) as error:
            raise FuenteNoDisponible("No se pudo verificar la fuente original de la fila") from error


class RegistroActividad:
    """Read recorded model usage without creating or modifying a ledger."""

    def __init__(self, archivo: Path) -> None:
        self.archivo = archivo

    def consultar(self, ejecucion_id: str) -> dict | None:
        """Return usage for an explicit campaign, or None when it is unavailable.

        An empty campaign is not evidence of zero expenditure. Reservations and
        invoices remain distinct, and the connection is always read-only.
        """
        if not self.archivo.is_file() or self.archivo.is_symlink():
            return None
        try:
            with closing(sqlite3.connect(self.archivo.resolve().as_uri() + "?mode=ro", uri=True)) as db:
                filas = db.execute(
                    "SELECT modelo,rol,estado,COUNT(*),SUM(reserva_usd) FROM llamadas "
                    "WHERE ejecucion=? GROUP BY modelo,rol,estado ORDER BY modelo,rol,estado",
                    (ejecucion_id,),
                ).fetchall()
        except sqlite3.Error:
            LOGGER.warning("AMARILLO: ledger no disponible para la vista operativa")
            return None
        return {
            "ejecucion_id": ejecucion_id,
            "estado": "disponible" if filas else "sin_datos",
            "llamadas": sum(f[3] for f in filas),
            "reserva_usd": sum(f[4] or 0 for f in filas) if filas else None,
            "detalle": [{"modelo": f[0], "rol": f[1], "estado": f[2], "llamadas": f[3]} for f in filas],
            "importe_facturado": None,
        }
