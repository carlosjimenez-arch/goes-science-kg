"""Ejecución por bloques: reanuda terminales y ajusta concurrencia sólo entre bloques cerrados."""

from __future__ import annotations

import json
import logging
from collections import Counter
from threading import BoundedSemaphore

from goes_science_kg.clases.contratos import ROLES
from goes_science_kg.clases.operacion import ejecutar, entorno, estimar
from goes_science_kg.clases.presupuesto import comprobar_continuidad
from goes_science_kg.clases.validacion import certificar_resultado
from goes_science_kg.materiales.compilacion import serializar

LOGGER = logging.getLogger(__name__)


def leer_control(archivo):
    cfg = json.loads(archivo.read_bytes())
    if (
        type(cfg.get("lotes")) is not int
        or not 1 <= cfg["lotes"] <= 16
        or type(cfg.get("vertex")) is not int
        or not 1 <= cfg["vertex"] <= 24
        or type(cfg.get("continuar")) is not bool
    ):
        raise ValueError("El control requiere 1–16 lotes, 1–24 invocaciones paralelas y continuar booleano")
    return cfg


def planificar(lotes, proveedor, corpus, destino, *, tamano=24, protocolo="clases-p5"):
    if not lotes or len({p["id"] for p in lotes}) != len(lotes) or not 1 <= tamano <= 100:
        raise ValueError("La campaña requiere un conjunto único no vacío y tamaño acotado")
    pendientes, terminales = [], 0
    for i in range(0, len(lotes), tamano):
        numero = i // tamano + 1
        identidad = entorno(proveedor, corpus, f"{protocolo}-masivo-{numero:03d}")
        for p in lotes[i : i + tamano]:
            archivo = destino / f"parte_{numero:03d}/resultado_{p['id']}.json"
            if not archivo.exists():
                pendientes.append(p)
                continue
            r = json.loads(archivo.read_bytes())
            certificar_resultado(r, p, {rol: proveedor.nombre_modelo(rol) for rol in ROLES})
            if r["huella_entorno"] != identidad:
                raise ValueError("Un terminal pertenece a otro entorno; no se reinicia la campaña")
            terminales += 1
    return estimar(pendientes, proveedor) | {"terminales_recuperables": terminales}


def ejecutar_campana(lotes, proveedor, corpus, destino, control, *, tamano=24, protocolo="clases-p5"):
    cfg = leer_control(control)
    plan = planificar(lotes, proveedor, corpus, destino, tamano=tamano, protocolo=protocolo)
    if not plan["safe_to_start"]:
        raise ValueError("La cota de toda la campaña pendiente excede el saldo; no se inicia ninguna llamada")
    destino.mkdir(parents=True, exist_ok=True)
    identidad = {
        "version": "campana-clases-1",
        "protocolo": protocolo,
        "tamano": tamano,
        "preparaciones": [p["id"] for p in lotes],
        "entorno_base": entorno(proveedor, corpus, protocolo),
    }
    archivo_plan = destino / "plan_campana.json"
    if archivo_plan.exists():
        if json.loads(archivo_plan.read_bytes()) != identidad:
            raise ValueError("El plan de campaña existente tiene otro conjunto o entorno")
    else:
        with archivo_plan.open("xb") as f:
            f.write(serializar(identidad))
    (destino / "preflight_campana.json").write_bytes(serializar(plan))
    resumen = []
    for i in range(0, len(lotes), tamano):
        # La ejecución anterior terminó todas sus llamadas antes de leer un ajuste de concurrencia.
        cfg = leer_control(control)
        if not cfg["continuar"]:
            LOGGER.warning("AMARILLO campaña detenida por su control antes de otro bloque")
            break
        proveedor.semaforo = BoundedSemaphore(cfg["vertex"])
        n = i // tamano + 1
        LOGGER.info(
            "AMARILLO bloque %s: %s lotes paralelos; %s llamadas simultáneas como máximo",
            n,
            cfg["lotes"],
            cfg["vertex"],
        )
        resultados = ejecutar(
            lotes[i : i + tamano],
            proveedor,
            corpus,
            destino / f"parte_{n:03d}",
            protocolo=f"{protocolo}-masivo-{n:03d}",
            concurrencia=cfg["lotes"],
        )
        conteos = Counter(f["estado"] for r in resultados for f in r["filas"].values())
        balance = comprobar_continuidad(proveedor.registro.archivo)
        resumen.append({"parte": n, "resultados": dict(conteos), "balance": balance, "concurrencia": cfg})
        temporal = destino / "progreso_campana.temporal"
        temporal.write_bytes(serializar(resumen))
        temporal.replace(destino / "progreso_campana.json")
        LOGGER.info(
            "%s bloque %s terminado: %s; balance %s",
            ("VERDE" if conteos["respaldado_automaticamente"] == sum(conteos.values()) else "AMARILLO"),
            n,
            dict(conteos),
            balance,
        )
        if n == 1 and conteos["respaldado_automaticamente"] / sum(conteos.values()) < 0.8:
            raise ValueError("Menos de 80% de respaldo en la primera cohorte: revisar los defectos antes de escalar")
    return resumen
