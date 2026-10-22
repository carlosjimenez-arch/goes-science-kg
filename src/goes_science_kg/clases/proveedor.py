"""Mismos modelos y ledger; concurrencia global acotada y configuración por tarea."""

from __future__ import annotations

from threading import BoundedSemaphore

from goes_science_kg.clases.contratos import ROLES
from goes_science_kg.clases.presupuesto import comprobar_continuidad, configuracion
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex

EJECUCION = "ciencias_v4_curricularizacion_20261022"
MODELOS = dict.fromkeys((*ROLES, "clases_redactor"), "gemini-4-argon") | {
    "clases_psicopedagogia": "gemini-3.8-flash",
    "clases_consulta": "gemini-3.8-flash",
}
TARIFAS = {"gemini-4-argon": {"entrada": 4, "salida": 20}, "gemini-3.8-flash": {"entrada": 1.5, "salida": 7.5}}


class ProveedorClases:
    def __init__(self, registro, *, concurrencia=6, max_llamadas=4000, max_usd=3500):
        autorizacion = configuracion()
        comprobar_continuidad(registro.archivo, autorizacion)
        if (
            max_llamadas > autorizacion["max_llamadas_acumuladas"]
            or max_usd > autorizacion["max_reserva_usd_acumulada"]
        ):
            raise ValueError("La configuración excede el máximo acumulado autorizado")
        self.registro = registro
        self.ejecucion_id = EJECUCION
        self.semaforo = BoundedSemaphore(concurrencia)
        self.proveedores = {}
        for rol in MODELOS:
            cfg = ConfiguracionVertex(
                proyecto="g-edu-lxp-xai-dev-prj-976d",
                region="global",
                modelos=MODELOS,
                tarifas=TARIFAS,
                max_llamadas=max_llamadas,
                max_usd=max_usd,
                timeout_segundos=600 if rol == "clases_redactor" else 360,
                reintentos=0,
                max_salida_tokens=32768 if rol == "clases_redactor" else 16384,
                niveles_razonamiento={
                    r: "LOW"
                    if r == "clases_consulta"
                    else "MEDIUM"
                    if r in {"clases_redactor", "clases_psicopedagogia", "clases_consulta"}
                    else "HIGH"
                    for r in MODELOS
                },
            )
            self.proveedores[rol] = Vertex(cfg, registro, self.ejecucion_id)
        self.proveedores_tecnicos = {
            rol: Vertex(
                self.proveedores[rol].configuracion.model_copy(update={"max_salida_tokens": 32768}),
                registro,
                self.ejecucion_id,
            )
            for rol in ROLES
        }

    def nombre_modelo(self, rol):
        return MODELOS[rol]

    def generar(self, **kwargs):
        tecnico = kwargs.pop("recuperacion_tecnica", False)
        if tecnico and kwargs["rol"] not in ROLES:
            raise ValueError("La recuperación técnica se limita a un lector sin dictamen válido")
        with self.semaforo:
            proveedores = self.proveedores_tecnicos if tecnico else self.proveedores
            return proveedores[kwargs["rol"]].generar(**kwargs)
