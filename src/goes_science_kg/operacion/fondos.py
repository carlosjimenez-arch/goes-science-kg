"""Admisión concurrente conservadora: reserva margen para todas las unidades en curso."""

from contextlib import contextmanager
from threading import Condition


class FondosCampana:
    def __init__(self, registro, ejecucion_id, *, max_llamadas, max_usd):
        self.registro, self.ejecucion_id = registro, ejecucion_id
        self.max_llamadas, self.max_usd = max_llamadas, max_usd
        self.condicion = Condition()
        self.pendientes = {}

    @contextmanager
    def unidad(self, id_, cota):
        """Las cotas activas se cuentan completas hasta cerrar; nunca descuenta llamadas reales."""
        with self.condicion:
            if id_ in self.pendientes:
                raise ValueError("La misma unidad ya tiene fondos asignados")
            while True:
                usado = self.registro.resumen(self.ejecucion_id)
                llamadas = sum(c["max_llamadas"] for c in self.pendientes.values())
                usd = sum(c["max_reserva_usd"] for c in self.pendientes.values())
                if usado["llamadas"] + llamadas + cota["max_llamadas"] <= self.max_llamadas and (
                    usado["reserva_usd"] + usd + cota["max_reserva_usd"] <= self.max_usd
                ):
                    self.pendientes[id_] = cota
                    break
                if not self.pendientes:
                    raise ValueError("safe_to_start=false: presupuesto insuficiente para la unidad completa")
                self.condicion.wait()
        try:
            yield
        finally:
            with self.condicion:
                self.pendientes.pop(id_)
                self.condicion.notify_all()
