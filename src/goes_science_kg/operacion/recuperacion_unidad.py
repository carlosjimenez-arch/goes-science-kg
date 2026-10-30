"""Recover unanswered transport failures while preserving terminal states and budgets."""

from __future__ import annotations

import fcntl
import hashlib
import logging
import os
import sqlite3
import time
from collections import Counter
from contextlib import closing
from pathlib import Path

from goes_science_kg.config import relativa
from goes_science_kg.motor.contratos import ResultadoMotor, huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.motor.registro import Registro
from goes_science_kg.producto.unidades import (
    PaqueteUnidad,
    ResultadoUnidad,
    SesionEjecutada,
    _anclaje_exacto,
    _archivo_propio,
    _comprobar_paquete,
    _directorio,
    _entorno,
)

LOGGER = logging.getLogger(__name__)
MOTIVO_TRANSPORTE = "Redacción no disponible: TransportError"


def _sin_respuesta(resultado: ResultadoMotor) -> bool:
    return (
        resultado.estado == "abstencion"
        and resultado.propuesta is None
        and not resultado.dictamenes
        and resultado.motivos == [MOTIVO_TRANSPORTE]
    )


def recuperar_unidad_sin_respuesta(
    paquete: PaqueteUnidad,
    original: ResultadoUnidad,
    *,
    motor: Motor,
    registro: Registro,
    directorio_operaciones: Path,
) -> ResultadoUnidad:
    """Create one recovery thread only when no response or review was received."""

    # Implementation notes:
    # Sólo admite una unidad cuyos terminales originales fallaron íntegramente antes de recibir
    # propuestas o dictámenes. Comprueba los checkpoints, fuentes y entorno originales. El ID,
    # ledger y límites se conservan; la recuperación se puede reanudar, pero no volver a votar.
    # Un nuevo fallo de transporte detiene el resto de la unidad.
    from langgraph.checkpoint.sqlite import SqliteSaver

    _comprobar_paquete(paquete)
    cfg = motor.modelo.configuracion
    ejecucion_id = original.ejecucion_id
    if (
        original.paquete_id != paquete.id
        or motor.modelo.ejecucion_id != ejecucion_id
        or motor.modelo.registro.archivo.resolve() != registro.archivo.resolve()
        or _entorno(motor, paquete) != original.huella_entorno
        or original.limites_presupuesto != {"max_llamadas": cfg.max_llamadas, "max_usd": cfg.max_usd}
    ):
        raise ValueError("La recuperación exige el paquete, entorno, ledger y límites originales")
    if (
        any(s.solicitud is None for s in paquete.sesiones)
        or tuple(s.sesion_id for s in original.sesiones) != tuple(s.id for s in paquete.sesiones)
        or any(s.resultado_motor is None or not _sin_respuesta(s.resultado_motor) for s in original.sesiones)
    ):
        raise ValueError("Sólo se recuperan unidades sin respuestas ni votos, con fallo exclusivo de transporte")
    inicial = original.consumo_despues
    detalle = inicial.get("detalle", [])
    if not detalle or any(
        d["estado"] != "fallida"
        or d["rol"] != "redactor"
        or d["entrada_tokens"] is not None
        or d["salida_tokens"] is not None
        for d in detalle
    ):
        raise ValueError("El consumo original contiene respuestas o telemetría; no se recupera automáticamente")
    base = _directorio(directorio_operaciones)
    archivo = _archivo_propio(base, "checkpoints_unidades.sqlite")
    if not archivo.is_file() or Path(original.checkpoints).resolve() != archivo.resolve():
        raise ValueError("Faltan los checkpoints originales de la unidad")
    lock = _archivo_propio(base, f"{ejecucion_id}.recuperacion-transporte.lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ValueError("La recuperación ya está en curso") from error
        with closing(sqlite3.connect(archivo, check_same_thread=False, timeout=30)) as db, db:
            checkpointer = SqliteSaver(db)
            flujo = motor.compilar(checkpointer=checkpointer)
            for sesion, previa in zip(paquete.sesiones, original.sesiones, strict=True):
                thread = f"unidad:{ejecucion_id}:{sesion.id}"
                estado = flujo.get_state({"configurable": {"thread_id": thread}})
                if (
                    previa.thread_id != thread
                    or estado.next
                    or not estado.values
                    or estado.values.get("propuesta") is not None
                    or any(estado.values.get(r) for r in ("cientifico", "psicopedagogo", "adversarial"))
                    or huella(estado.values.get("solicitud")) != huella(sesion.solicitud.model_dump())
                    or estado.values.get("huella_entorno") != original.huella_entorno
                    or huella(estado.values.get("resultado")) != huella(previa.resultado_motor)
                ):
                    raise ValueError("El archivo no coincide con los terminales originales")
                motor.validar_estado(estado.values)
            consumo = registro.resumen(ejecucion_id)
            # SQLite fecha con resolución de segundos; ordenar por UUID no conserva el prefijo.
            if not Counter(map(huella, detalle)) <= Counter(map(huella, consumo["detalle"])):
                raise ValueError("El ledger no conserva los intentos originales")
            db.execute("CREATE TABLE IF NOT EXISTS recuperaciones_unidad (id TEXT PRIMARY KEY, protocolo TEXT)")
            protocolo = huella(
                [original.model_dump(mode="json"), hashlib.sha256(Path(__file__).read_bytes()).hexdigest()]
            )
            previo = db.execute("SELECT protocolo FROM recuperaciones_unidad WHERE id=?", (ejecucion_id,)).fetchone()
            if previo and previo[0] != protocolo:
                raise ValueError("La recuperación ya está vinculada a otro original o protocolo")
            db.execute("INSERT OR IGNORE INTO recuperaciones_unidad VALUES(?,?)", (ejecucion_id, protocolo))
            db.commit()
            reutilizados = {
                s.id: bool(
                    flujo.get_state(
                        {"configurable": {"thread_id": f"unidad:{ejecucion_id}:{s.id}:transporte-1"}}
                    ).values
                )
                for s in paquete.sesiones
            }
        inicio = time.perf_counter()
        sesiones = []
        detenido = False
        for sesion, fila in zip(paquete.sesiones, paquete.filas, strict=True):
            if detenido:
                sesiones.append(
                    SesionEjecutada(
                        sesion_id=sesion.id,
                        fila_id=fila.id,
                        estado="no_ejecutada",
                        motivos=("Recuperación detenida tras un fallo de transporte",),
                    )
                )
                continue
            thread = f"unidad:{ejecucion_id}:{sesion.id}:transporte-1"
            salida = ejecutar_durable(
                motor,
                archivo=archivo,
                solicitud=sesion.solicitud.model_dump(),
                thread_id=thread,
                ejecucion_id=ejecucion_id,
                huella_entorno=original.huella_entorno,
            )
            resultado = ResultadoMotor.model_validate(salida["resultado"])
            motivos = list(resultado.motivos)
            if resultado.estado == "respaldado_automaticamente" and not _anclaje_exacto(resultado, fila):
                motivos.append("El Motor no citó la fila objetivo exacta")
            sesiones.append(
                SesionEjecutada(
                    sesion_id=sesion.id,
                    fila_id=fila.id,
                    estado=(
                        "respaldado_automaticamente"
                        if resultado.estado == "respaldado_automaticamente" and not motivos
                        else "abstencion"
                    ),
                    motivos=tuple(motivos),
                    thread_id=thread,
                    checkpoint_reutilizado=reutilizados[sesion.id],
                    resultado_motor=resultado,
                )
            )
            detenido = _sin_respuesta(resultado)
            if detenido:
                LOGGER.error("ROJO vuelve a fallar el transporte; no se inician otros objetivos")
        despues = registro.resumen(ejecucion_id)
        conteos = Counter(s.estado for s in sesiones)
        return ResultadoUnidad(
            paquete_id=paquete.id,
            ejecucion_id=ejecucion_id,
            huella_entorno=original.huella_entorno,
            sesiones=tuple(sesiones),
            cobertura={
                "filas_totales": len(paquete.filas),
                "sesiones_propuestas": len(sesiones),
                "respaldadas": conteos["respaldado_automaticamente"],
                "abstenciones": conteos["abstencion"],
                "no_ejecutadas": conteos["no_ejecutada"],
            },
            tiempo_ms=(time.perf_counter() - inicio) * 1000,
            consumo_antes=consumo,
            consumo_despues=despues,
            consumo_incremental={k: despues[k] - consumo[k] for k in ("llamadas", "reserva_usd")},
            limites_presupuesto=original.limites_presupuesto,
            checkpoints=relativa(archivo),
        )
    finally:
        os.close(descriptor)
