"""Campaña finita: cuatro lecturas por lote, una reparación y presupuesto acumulado compartido."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
from pathlib import Path
from threading import Event, Lock

from goes_science_kg.clases.contratos import esquema_transporte
from goes_science_kg.clases.presupuesto import comprobar_continuidad, configuracion
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, clave_solicitud
from goes_science_kg.produccion.revision_docente.contexto import factorizar, vista_revision
from goes_science_kg.produccion.revision_docente.contratos import (
    ROLES,
    DictamenLote,
    validar_dictamen,
)
from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, procesar
from goes_science_kg.produccion.revision_docente.prompts import sistema
from goes_science_kg.produccion.revision_docente.streaming import VertexStreaming

LOGGER = logging.getLogger(__name__)
CRECIMIENTO_REPARACION = 1.05
TRANSPORTE = esquema_transporte(DictamenSeleccion)


def ejecucion_unica(funcion):
    @wraps(funcion)
    def protegida(solicitudes, destino, ledger, **opciones):
        import fcntl

        archivo = destino / ".revision.lock"
        if archivo.is_symlink():
            raise ValueError("El bloqueo debe ser un archivo propio")
        with archivo.open("a") as bloqueo:
            try:
                fcntl.flock(bloqueo, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise RuntimeError("Ya hay otra ejecución activa de esta captura") from error
            try:
                return funcion(solicitudes, destino, ledger, **opciones)
            finally:
                fcntl.flock(bloqueo, fcntl.LOCK_UN)

    return protegida


def guardar(p, dato):
    raw = serializar(dato)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        if p.read_bytes() != raw:
            raise ValueError("El checkpoint difiere; use otra captura sin sobrescribir votos")
    else:
        with p.open("xb") as f:
            f.write(raw)


def proveedor_cfg():
    from goes_science_kg.config import cargar

    cfg = dict(cargar("mejoras_curriculares")["vertex"])
    cfg["niveles_razonamiento"] = dict(cfg["niveles_razonamiento"])
    for rol in ("revision_ciencia", "revision_curriculo", "revision_adversarial"):
        cfg["niveles_razonamiento"][rol] = "MEDIUM"
    a = configuracion()
    cfg.update(
        max_llamadas=a["max_llamadas_acumuladas"],
        max_usd=a["max_reserva_usd_acumulada"],
        max_salida_tokens=65536,
        reintentos=0,
        timeout_segundos=1200,
    )
    return ConfiguracionVertex.model_validate(cfg)


def mensaje(solicitud):
    return serializar(factorizar(vista_revision(solicitud))).decode()


def reserva(solicitud, cfg, rol):
    tarifa = cfg.tarifas[cfg.modelos[rol]]
    entrada = len((sistema(rol) + mensaje(solicitud) + json.dumps(TRANSPORTE.model_json_schema())).encode())
    return (entrada * tarifa.entrada + cfg.max_salida_tokens * tarifa.salida) / 1e6


def preflight(solicitudes, ledger, cfg):
    consumo = comprobar_continuidad(ledger)
    limites = configuracion()
    reservas = [reserva(s, cfg, rol) for s in solicitudes for rol in ROLES]
    # Contexto reparado como máximo +5%; tres recuperaciones técnicas, sin devolver las reservas.
    max_reserva = sum(reservas) * (1 + CRECIMIENTO_REPARACION) + max(reservas) * 3 * CRECIMIENTO_REPARACION
    max_nuevas = len(reservas) * 2 + 3
    return {
        "version": "preflight-revision-docente-1",
        "consumo_inicial": consumo,
        "ledger_sha256_inicial": sha(ledger.read_bytes()),
        "lotes": len(solicitudes),
        "elementos": sum(len(s["items"]) for s in solicitudes),
        "primera_pasada_llamadas": len(reservas),
        "max_nuevas_llamadas": max_nuevas,
        "max_reserva_nueva_usd": max_reserva,
        "crecimiento_max_contexto_reparado": CRECIMIENTO_REPARACION,
        "saldo_llamadas": limites["max_llamadas_acumuladas"] - consumo["llamadas"],
        "saldo_reserva_usd": limites["max_reserva_usd_acumulada"] - consumo["reserva_usd"],
        "safe_to_start": consumo["llamadas"] + max_nuevas <= limites["max_llamadas_acumuladas"]
        and consumo["reserva_usd"] + max_reserva <= limites["max_reserva_usd_acumulada"],
        "alcance": "Preparaciones efectivas y sus unidades; no catalogación científica del producto-4, "
        "redacción de guiones completos, eficacia observada ni aprobación institucional.",
        "modelos": cfg.modelos,
        "cuatro_lecturas_no_independencia_estadistica": True,
    }


@ejecucion_unica
def ejecutar(
    solicitudes,
    destino: Path,
    ledger: Path,
    *,
    ronda,
    cfg=None,
    proveedor=None,
    solo_lotes=None,
    solo_roles=None,
    concurrencia=2,
):
    if type(concurrencia) is not int or not 1 <= concurrencia <= 4:
        raise ValueError("La concurrencia debe estar entre una y cuatro lecturas")
    cfg = cfg or proveedor_cfg()
    if len({s["lote"] for s in solicitudes}) != len(solicitudes):
        raise ValueError("La ejecución no admite lotes repetidos")
    plan = json.loads((destino / "preflight.json").read_bytes())
    if not plan["safe_to_start"] or ronda not in {1, 2}:
        raise ValueError("No hay un preflight válido o se excede la reparación única")
    iniciales = {s["lote"]: s for s in json.loads((destino / "ronda_1.json").read_bytes())}
    for s in solicitudes:
        anterior = iniciales.get(s["lote"])
        if anterior is None or (ronda == 1 and s != anterior):
            raise ValueError("Los contextos iniciales no pueden cambiar debajo de un checkpoint")
        if ronda == 2 and len(mensaje(s).encode()) > CRECIMIENTO_REPARACION * len(mensaje(anterior).encode()):
            raise ValueError("La reparación excede la cota de contexto presupuestada")
    guardar(destino / f"ronda_{ronda}.json", solicitudes)
    registro, disponibles = None, set()
    if proveedor is None:
        consumo, limites = comprobar_continuidad(ledger), configuracion()
        registro = Registro(ledger)
        nuevas = []
        for s in solicitudes:
            for rol in ROLES:
                if (solo_lotes is not None and s["lote"] not in solo_lotes) or (
                    solo_roles is not None and rol not in solo_roles
                ):
                    continue
                if (destino / "lecturas" / f"r{ronda}_l{s['lote']}_{rol}.json").exists():
                    continue
                clave = clave_solicitud(cfg, rol=rol, sistema=sistema(rol), mensaje=mensaje(s), esquema=TRANSPORTE)
                cache, raw = registro.cache(clave), registro.salida(clave)
                if cache is not None or raw is not None:
                    TRANSPORTE.model_validate(cache) if cache is not None else TRANSPORTE.model_validate_json(raw)
                    disponibles.add((s["lote"], rol))
                else:
                    nuevas.append(reserva(s, cfg, rol))
        if (
            consumo["llamadas"] + len(nuevas) > limites["max_llamadas_acumuladas"]
            or consumo["reserva_usd"] + sum(nuevas) > limites["max_reserva_usd_acumulada"]
        ):
            raise ValueError("El saldo vigente no cubre las lecturas pendientes; no se inicia ninguna invocación")
    vertex = proveedor or VertexStreaming(cfg, registro, configuracion()["ejecucion"])
    intentos_lock = Lock()
    detener = Event()

    def revisar(s, rol):
        if detener.is_set():
            raise RuntimeError("Envíos detenidos por fallo de transporte previo; no se consume Vertex")
        identidad = {
            "lote": s["lote"],
            "ronda": ronda,
            "rol": rol,
            "modelo": cfg.modelos[rol],
            "solicitud_sha256": sha(serializar(s)),
            "mensaje_sha256": sha(mensaje(s).encode()),
            "sistema_sha256": sha(sistema(rol).encode()),
            "esquema_sha256": sha(serializar(DictamenLote.model_json_schema())),
            "transporte_sha256": sha(serializar(TRANSPORTE.model_json_schema())),
        }
        archivo = destino / "lecturas" / f"r{ronda}_l{s['lote']}_{rol}.json"
        if not archivo.exists() or "nivel_razonamiento" in json.loads(archivo.read_bytes())["identidad"]:
            identidad["nivel_razonamiento"] = (
                json.loads(archivo.read_bytes())["identidad"]["nivel_razonamiento"]
                if archivo.exists()
                else cfg.niveles_razonamiento.get(rol)
            )
        if archivo.exists():
            d = json.loads(archivo.read_bytes())
            if d["identidad"] != identidad:
                raise ValueError("El voto tiene otra identidad")
            if "salida_selecciones" in d:
                obtenido = procesar(DictamenSeleccion.model_validate(d["salida_selecciones"]), s, rol)
                if any(d[k] != obtenido[k] for k in obtenido):
                    raise ValueError("La validación local cambió respecto a la selección del lector")
            else:
                validar_dictamen(DictamenLote.model_validate(d["dictamen"]), s)
            return d
        if proveedor is None and (s["lote"], rol) not in disponibles:
            consumo = comprobar_continuidad(ledger)
            if consumo["llamadas"] - plan["consumo_inicial"]["llamadas"] >= plan["max_nuevas_llamadas"]:
                raise ValueError("Se agotó la cota de esta campaña")
        with intentos_lock:
            clave = f"r{ronda}_l{s['lote']}_{rol}"
            intentos = destino / "intentos"
            previos = list(intentos.glob(clave + "_*.json"))
            todos = list(intentos.glob("*.json"))
            extras = sum(p.stem.endswith("_2") for p in todos)
            if (s["lote"], rol) not in disponibles and (len(previos) >= 2 or (previos and extras >= 3)):
                raise ValueError("Se agotó la recuperación técnica: máximo una por lectura y tres globales")
            if (s["lote"], rol) not in disponibles:
                guardar(intentos / (clave + f"_{len(previos) + 1}.json"), identidad)
        d = vertex.generar(rol=rol, sistema=sistema(rol), mensaje=mensaje(s), esquema=TRANSPORTE)
        if isinstance(d, DictamenSeleccion):
            resultado = {"identidad": identidad, **procesar(d, s, rol)}
        else:
            validar_dictamen(d, s)
            resultado = {"identidad": identidad, "dictamen": d.model_dump(mode="json")}
        guardar(archivo, resultado)
        validos = len(resultado["dictamen"]["items"])
        completo = validos == len(s["items"])
        LOGGER.log(
            logging.INFO if completo else logging.WARNING,
            "%s lectura r%s lote %s %s: %s/%s elementos válidos",
            "VERDE" if completo else "AMARILLO",
            ronda,
            s["lote"],
            rol,
            validos,
            len(s["items"]),
        )
        return resultado

    def trabajo(s, rol):
        try:
            return revisar(s, rol)
        except Exception as error:
            if type(error).__name__ in {"ClientError", "ServerError", "ReadTimeout", "TimeoutError", "ConnectError"}:
                detener.set()
            raise

    errores = []
    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        futuros = {
            pool.submit(trabajo, s, rol): (s["lote"], rol)
            for s in solicitudes
            if solo_lotes is None or s["lote"] in solo_lotes
            for rol in ROLES
            if solo_roles is None or rol in solo_roles
        }
        for futuro in as_completed(futuros):
            lote, rol = futuros[futuro]
            try:
                futuro.result()
            except Exception as error:
                errores.append({"lote": lote, "rol": rol, "error": type(error).__name__, "detalle": str(error)[:600]})
                LOGGER.error("ROJO revisión lote %s %s: %s", lote, rol, type(error).__name__)
    numero = len(list(destino.glob(f"resultado_ronda_{ronda}_*.json")))
    guardar(destino / f"resultado_ronda_{ronda}_{numero:03d}.json", {"ronda": ronda, "errores": errores})
    return errores
