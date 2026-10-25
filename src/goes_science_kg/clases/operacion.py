"""Presupuesto del conjunto, entorno inmutable y ejecución reanudable por lote."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from goes_science_kg.clases import prompts
from goes_science_kg.clases.contexto import contexto
from goes_science_kg.clases.contratos import (
    MAX_BYTES_BORRADOR,
    MAX_HALLAZGOS_BYTES,
    ROLES,
    BorradorClases,
    esquema_lectura,
)
from goes_science_kg.clases.motor import MotorClases
from goes_science_kg.clases.preparacion import leer_preparacion
from goes_science_kg.clases.proveedor import EJECUCION
from goes_science_kg.clases.validacion import certificar_resultado
from goes_science_kg.materiales.compilacion import serializar
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import ejecutar_durable

LOGGER = logging.getLogger(__name__)


def reserva(proveedor, rol, sistema, mensaje, esquema, *, tecnica=False):
    proveedores = proveedor.proveedores_tecnicos if tecnica else proveedor.proveedores
    cfg = proveedores[rol].configuracion
    tarifa = cfg.tarifas[proveedor.nombre_modelo(rol)]
    entrada = len((sistema + mensaje + json.dumps(esquema.model_json_schema())).encode())
    return (entrada * tarifa.entrada + cfg.max_salida_tokens * tarifa.salida) / 1_000_000


def estimar(lotes, proveedor):
    total = 0.0
    for p in lotes:
        mensaje = json.dumps(contexto(p), ensure_ascii=False, sort_keys=True)
        if p.get("hallazgos_previos"):
            mensaje = json.dumps(
                contexto(p) | {"hallazgos_a_corregir": p["hallazgos_previos"]}, ensure_ascii=False, sort_keys=True
            )
        primera = reserva(proveedor, "clases_redactor", prompts.REDACTOR, mensaje, BorradorClases)
        # Un borrador anterior completo puede ser necesario para reparar formato o contenido.
        reparacion = reserva(
            proveedor,
            "clases_redactor",
            prompts.REDACTOR,
            mensaje + "x" * (MAX_BYTES_BORRADOR + MAX_HALLAZGOS_BYTES + 12000),
            BorradorClases,
        )
        revisiones = sum(
            reserva(
                proveedor,
                rol,
                prompts.JUEZ + "\n" + prompts.ESPECIALIDADES[rol],
                mensaje + "x" * (MAX_BYTES_BORRADOR + 3000),
                esquema_lectura(rol),
            )
            for rol in ROLES
        )
        tecnicas = sum(
            reserva(
                proveedor,
                rol,
                prompts.JUEZ + "\n" + prompts.ESPECIALIDADES[rol],
                mensaje + "x" * (MAX_BYTES_BORRADOR + 3000),
                esquema_lectura(rol),
                tecnica=True,
            )
            for rol in ROLES
        )
        total += primera + revisiones + max(reparacion + revisiones, tecnicas)
    consumido = proveedor.registro.resumen(EJECUCION)
    cfg = proveedor.proveedores["clases_redactor"].configuracion
    return {
        "lotes": len(lotes),
        "filas": sum(len(p["filas"]) for p in lotes),
        "llamadas_minimas": sum(4 if p.get("borrador_inicial") else 5 for p in lotes),
        "llamadas_maximas_dos_rondas": len(lotes) * 10,
        "reserva_maxima_lotes_usd": total,
        "consumo_anterior": {k: consumido[k] for k in ("llamadas", "reserva_usd")},
        "limites": {"llamadas": cfg.max_llamadas, "reserva_usd": cfg.max_usd},
        "safe_to_start": (
            consumido["llamadas"] + len(lotes) * 10 <= cfg.max_llamadas
            and consumido["reserva_usd"] + total <= cfg.max_usd
        ),
    }


def entorno(proveedor, corpus, protocolo):
    raiz = Path(__file__).parent
    archivos = (
        "contratos.py",
        "fuentes.py",
        "motor.py",
        "prompts.py",
        "preparacion.py",
        "validacion.py",
        "proveedor.py",
        "operacion.py",
        "edicion.py",
    )
    numero = re.fullmatch(r"clases-p([0-9]+)(?:-.*)?", protocolo)
    if numero and int(numero[1]) >= 9:
        archivos += ("editorial.py",)
    if numero and int(numero[1]) >= 10:
        archivos += ("contexto.py",)
    return huella(
        {
            "protocolo": protocolo,
            "corpus_sha256": corpus.huella,
            "codigo": {n: hashlib.sha256((raiz / n).read_bytes()).hexdigest() for n in archivos},
            "configuracion": {
                r: {
                    "modelo": proveedor.nombre_modelo(r),
                    "max_salida": proveedor.proveedores[r].configuracion.max_salida_tokens,
                    "razonamiento": proveedor.proveedores[r].configuracion.niveles_razonamiento[r],
                }
                for r in (*ROLES, "clases_redactor")
            },
            "configuracion_tecnica": {
                r: {
                    "modelo": proveedor.nombre_modelo(r),
                    "max_salida": proveedor.proveedores_tecnicos[r].configuracion.max_salida_tokens,
                    "razonamiento": proveedor.proveedores_tecnicos[r].configuracion.niveles_razonamiento[r],
                }
                for r in ROLES
            },
        }
    )


def ejecutar(lotes, proveedor, corpus, destino: Path, *, protocolo="clases-p1", concurrencia=3):
    if not lotes or not 1 <= concurrencia <= 16 or len({p["id"] for p in lotes}) != len(lotes):
        raise ValueError("Lotes repetidos, vacíos o concurrencia fuera de límites")
    huella_entorno = entorno(proveedor, corpus, protocolo)
    protocolo_archivo = destino / "protocolo.json"
    identidad = {
        "protocolo": protocolo,
        "huella_entorno": huella_entorno,
        "ejecucion": EJECUCION,
        "preparaciones": [p["id"] for p in lotes],
    }
    if protocolo_archivo.exists():
        if json.loads(protocolo_archivo.read_bytes()) != identidad:
            raise ValueError("La ejecución existente tiene otro entorno o conjunto; no se modifica")
    else:
        destino.mkdir(parents=True, exist_ok=True)
        with protocolo_archivo.open("xb") as f:
            f.write(serializar(identidad))
    modelos = {r: proveedor.nombre_modelo(r) for r in ROLES}
    recuperados, pendientes_lotes = [], []
    for p in lotes:
        salida = destino / f"resultado_{p['id']}.json"
        if salida.exists():
            r = json.loads(salida.read_bytes())
            certificar_resultado(r, p, modelos)
            if r["huella_entorno"] != huella_entorno:
                raise ValueError("El resultado terminal pertenece a otro entorno")
            recuperados.append(r)
        else:
            pendientes_lotes.append(p)
    plan = estimar(pendientes_lotes, proveedor)
    plan["lotes_terminales_recuperados"] = len(recuperados)
    if not plan["safe_to_start"]:
        raise ValueError("El conjunto pendiente no cabe en el saldo acumulado; no se inicia ninguna generación")
    (destino / "preflight.json").write_bytes(serializar(plan))
    motor = MotorClases(proveedor, corpus)

    def procesar(p):
        estado = ejecutar_durable(
            motor,
            archivo=destino / "checkpoints.sqlite",
            solicitud=p,
            thread_id=protocolo + ":" + p["id"],
            ejecucion_id=EJECUCION,
            huella_entorno=huella_entorno,
            max_concurrencia=4,
        )
        salida = destino / f"resultado_{p['id']}.json"
        raw = serializar(estado["resultado"])
        if salida.exists():
            if salida.read_bytes() != raw:
                raise ValueError("Un resultado terminal cambió")
        else:
            with salida.open("xb") as f:
                f.write(raw)
        return estado["resultado"]

    resultados = list(recuperados)
    restantes = iter(pendientes_lotes)
    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        pendientes = {pool.submit(procesar, p) for p in [next(restantes, None) for _ in range(concurrencia)] if p}
        try:
            while pendientes:
                terminados, pendientes = wait(pendientes, timeout=30, return_when=FIRST_COMPLETED)
                for futuro in terminados:
                    resultados.append(futuro.result())
                    siguiente = next(restantes, None)
                    if siguiente:
                        pendientes.add(pool.submit(procesar, siguiente))
                if terminados:
                    filas = [f for r in resultados for f in r["filas"].values()]
                    respaldadas = sum(f["estado"] == "respaldado_automaticamente" for f in filas)
                    LOGGER.info(
                        "%s progreso durable: %s/%s lotes terminados; %s/%s guiones respaldados",
                        "VERDE" if respaldadas == len(filas) else "AMARILLO",
                        len(resultados),
                        len(lotes),
                        respaldadas,
                        len(filas),
                    )
        except BaseException:
            for futuro in pendientes:
                futuro.cancel()
            raise
    return resultados


def cargar_lotes(directorio):
    return [leer_preparacion(p) for p in sorted(directorio.glob("lote_*.json"))]
