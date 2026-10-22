"""Lotes fijados antes de juzgar: varios checkpoints y un único presupuesto durable."""

from __future__ import annotations

import fcntl
import logging
import os
import sqlite3
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from goes_science_kg.archivos import destino_generado
from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.motor.contratos import Contrato, huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.vertex import ConfiguracionVertex
from goes_science_kg.producto._juicios_contratos import ROLES_CONOCIMIENTO, SolicitudConocimiento
from goes_science_kg.producto.juicios import PreparadorConocimiento

LOGGER = logging.getLogger(__name__)


class PlanLoteJuicios(Contrato):
    version: Literal["lote-conocimiento-1"] = "lote-conocimiento-1"
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    ejecucion_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,100}$")
    huella_preparador: str = Field(pattern=r"^[a-f0-9]{64}$")
    solicitudes: tuple[SolicitudConocimiento, ...] = Field(min_length=1, max_length=50)
    expedientes: dict[str, str]
    vertex: ConfiguracionVertex

    @model_validator(mode="after")
    def _identidad_y_limites(self):
        ids = [s.candidato_id for s in self.solicitudes]
        if len(set(ids)) != len(ids) or set(ids) != self.expedientes.keys():
            raise ValueError("El lote requiere solicitudes únicas y la huella de cada expediente")
        if self.vertex.reintentos != 0 or self.vertex.max_llamadas > 4 * len(ids) or self.vertex.max_usd > 20:
            raise ValueError("El lote admite hasta cuatro intentos por candidato y cero reintentos")
        if set(self.vertex.modelos) != set(ROLES_CONOCIMIENTO):
            raise ValueError("El lote requiere los cuatro lectores de conocimiento")
        if self.id != huella(self.model_dump(mode="json", exclude={"id"})):
            raise ValueError("La identidad del plan no corresponde a su contenido")
        return self


def preparar_lote(
    preparador: PreparadorConocimiento,
    candidatos: list[str],
    configuracion: ConfiguracionVertex,
    ejecucion_id: str,
) -> PlanLoteJuicios:
    """Fija todos los expedientes sin modelos; conserva también preparaciones en abstención."""
    if not candidatos or len(set(candidatos)) != len(candidatos) or len(candidatos) > 50:
        raise ValueError("Se requieren entre uno y cincuenta candidatos únicos")
    solicitudes = tuple(SolicitudConocimiento(candidato_id=c) for c in candidatos)
    datos = {
        "version": "lote-conocimiento-1",
        "ejecucion_id": ejecucion_id,
        "huella_preparador": preparador.huella_entorno,
        "solicitudes": [s.model_dump(mode="json") for s in solicitudes],
        "expedientes": {s.candidato_id: huella(preparador.preparar(s)) for s in solicitudes},
        "vertex": configuracion.model_dump(mode="json"),
    }
    return PlanLoteJuicios(id=huella(datos), **datos)


def verificar_lote(plan: PlanLoteJuicios, preparador: PreparadorConocimiento) -> None:
    """Un plan guardado no sustituye la comprobación actual de todas las fuentes."""
    actual = preparar_lote(preparador, [s.candidato_id for s in plan.solicitudes], plan.vertex, plan.ejecucion_id)
    if actual != plan:
        raise ValueError("Cambió el corpus, los soportes o la evidencia del lote preparado")


def ejecutar_lote(plan: PlanLoteJuicios, motor: MotorConocimiento, *, checkpoints: Path) -> dict:
    """Reanuda todos los casos del plan, sin redistribuir ni reiniciar las reservas."""
    verificar_lote(plan, motor.preparador)
    proveedor = motor.modelo
    if (
        getattr(proveedor, "ejecucion_id", None) != plan.ejecucion_id
        or getattr(proveedor, "configuracion", None) != plan.vertex
        or getattr(proveedor, "registro", None) is None
    ):
        raise ValueError("Todos los lectores deben compartir proveedor, límites, ledger e ID del plan")
    archivo = destino_generado(checkpoints, extension=".sqlite")
    archivo.parent.mkdir(parents=True, exist_ok=True)
    lock = archivo.with_name(f".{archivo.name}.lote-{plan.ejecucion_id}.lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("El mismo lote ya está ejecutándose") from error
        entorno = huella({"plan": plan.id, "motor": motor.huella_entorno})
        ledger = proveedor.registro.archivo.resolve()
        estado_ledger = ledger.stat()
        identidad = huella([str(ledger), estado_ledger.st_dev, estado_ledger.st_ino])
        with sqlite3.connect(archivo, timeout=30) as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS lotes_conocimiento "
                "(ejecucion TEXT PRIMARY KEY, plan TEXT, entorno TEXT, ledger TEXT)"
            )
            db.execute("BEGIN IMMEDIATE")
            anterior = db.execute(
                "SELECT plan,entorno,ledger FROM lotes_conocimiento WHERE ejecucion=?", (plan.ejecucion_id,)
            ).fetchone()
            if anterior is not None and tuple(anterior) != (plan.id, entorno, identidad):
                raise ValueError("La ejecución ya está vinculada a otro plan, entorno o ledger")
            db.execute(
                "INSERT OR IGNORE INTO lotes_conocimiento VALUES(?,?,?,?)",
                (plan.ejecucion_id, plan.id, entorno, identidad),
            )
        antes = proveedor.registro.resumen(plan.ejecucion_id)
        estados = []
        for numero, s in enumerate(plan.solicitudes, 1):
            LOGGER.info("Juicio %d/%d: %s", numero, len(plan.solicitudes), s.candidato_id)
            estado = ejecutar_durable(
                motor,
                archivo=archivo,
                solicitud=s.model_dump(mode="json"),
                thread_id=f"conocimiento:{plan.ejecucion_id}:{s.candidato_id}",
                ejecucion_id=plan.ejecucion_id,
                huella_entorno=entorno,
                max_concurrencia=4,
            )
            estados.append(estado)
            if estado["preparacion"]["estado"] == "preparado" and all(
                estado.get(r, {}).get("error") for r in ROLES_CONOCIMIENTO
            ):
                LOGGER.error("ROJO los cuatro lectores fallaron; se detiene el lote conservando gasto y checkpoints")
                break
        despues = proveedor.registro.resumen(plan.ejecucion_id)
        return {
            "fase": "juicio_semantico_lote" if len(estados) == len(plan.solicitudes) else "lote_incompleto",
            "plan": plan.model_dump(mode="json"),
            "workflow": estados,
            "sin_ejecutar": [s.model_dump(mode="json") for s in plan.solicitudes[len(estados) :]],
            "consumo_antes": antes,
            "consumo": despues,
            "consumo_incremental": {k: despues[k] - antes[k] for k in ("llamadas", "reserva_usd")},
        }
    finally:
        os.close(descriptor)
