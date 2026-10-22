"""Comparación reproducible de jueces sobre casos sembrados; no mide eficacia educativa."""

from __future__ import annotations

import json
import logging
import platform
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import Field

from goes_science_kg.motor.contratos import Contrato, huella
from goes_science_kg.motor.prompts import BASE, serializar
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex

LOGGER = logging.getLogger(__name__)


class Veredicto(Contrato):
    decision: Literal["aprobar", "rechazar", "abstenerse"]
    hallazgos: list[str] = Field(max_length=8)
    fuentes_ids: list[str]


VARIANTES = {
    "directo": "Evalúa la propuesta en el contexto del rol indicado. Aprueba si es correcta; rechaza si tiene errores.",
    "rubrica_evidencia": BASE
    + """
Evalúa la propuesta de manera independiente. Comprueba las afirmaciones contra la evidencia disponible.
Busca una razón concreta por la que pueda ser incorrecta: sentido científico, causalidad no demostrada,
edad/grado, conocimiento procedimental, carga cognitiva, accesibilidad, recursos o seguridad.
Una cita verdadera que no implica la conclusión no la respalda. Los rankings no demuestran causalidad.
Una analogía o representación no es un experimento real; verifica que el texto lo distinga explícitamente.
Aprueba si satisface la evidencia y las condiciones de la tarea. Rechaza si hay un error identificable.
Si no alcanza la evidencia para decidir, abstente. Devuelve razones breves observables, sin razonamiento privado.
""",
}


def resumir(filas: list[dict]) -> dict:
    total = len(filas)
    evaluadas = [f for f in filas if not f.get("error")]
    n = len(evaluadas)
    negativos = [f for f in evaluadas if f["esperado"] == "rechazar"]
    positivos = [f for f in evaluadas if f["esperado"] == "aprobar"]
    return {
        "total": total,
        "errores_ejecucion": total - n,
        "exactitud_sobre_total": sum(f["decision"] == f["esperado"] for f in evaluadas) / max(1, total),
        "aceptaciones_incorrectas": sum(f["decision"] == "aprobar" for f in negativos),
        "negativos": len(negativos),
        "rechazos_incorrectos": sum(f["decision"] == "rechazar" for f in positivos),
        "positivos": len(positivos),
        "abstenciones": sum(f["decision"] == "abstenerse" for f in evaluadas),
        "latencia_media_ms": sum(f["latencia_ms"] for f in filas) / max(1, total),
    }


def comparar_jueces(
    dataset: Path,
    *,
    configuracion: ConfiguracionVertex,
    registro: Registro,
    ejecucion_id: str,
    modelos: tuple[str, ...],
    concurrencia: int = 3,
) -> dict:
    datos = json.loads(dataset.read_text(encoding="utf-8"))
    casos = datos["casos"]
    if not casos or len({c["id"] for c in casos}) != len(casos):
        raise ValueError("El conjunto debe tener casos con IDs únicos")
    if datos.get("nivel") != "sintetico_plata":
        raise ValueError("Este experimento requiere el conjunto sintético identificado como tal")
    if not 1 <= concurrencia <= 6:
        raise ValueError("La concurrencia debe estar entre uno y seis")
    tareas = [(caso, modelo, variante) for caso in casos for modelo in modelos for variante in VARIANTES]
    random.Random(20261021).shuffle(tareas)
    LOGGER.info(
        "Experimento: %d casos, %d modelos, %d variantes, %d tareas",
        len(casos),
        len(modelos),
        len(VARIANTES),
        len(tareas),
    )

    def evaluar(tarea):
        caso, modelo, variante = tarea
        cfg = configuracion.model_copy(update={"modelos": {"juez": modelo}})
        proveedor = Vertex(cfg, registro, ejecucion_id)
        # Lista blanca: nunca enviar etiquetas esperadas ni la explicación de su construcción.
        visibles = {
            k: caso[k]
            for k in ("rol", "especialidad", "contexto", "contexto_fuente", "propuesta", "fuentes_ids")
            if k in caso
        }
        visibles["fuentes"] = {id: datos["fuentes"][id] for id in caso["fuentes_ids"]}
        inicio = time.perf_counter()
        fila = {
            "id": caso["id"],
            "modelo": modelo,
            "variante": variante,
            "esperado": caso["esperado"],
            "rol": caso["rol"],
        }
        try:
            respuesta = proveedor.generar(
                rol="juez", sistema=VARIANTES[variante], mensaje=serializar(visibles), esquema=Veredicto
            )
            fila.update(respuesta.model_dump())
        except Exception as error:
            fila.update({"decision": "error", "error": type(error).__name__})
        fila["latencia_ms"] = (time.perf_counter() - inicio) * 1000
        return fila

    with ThreadPoolExecutor(max_workers=concurrencia) as pool:
        resultados = list(pool.map(evaluar, tareas))
    resumen = {
        f"{modelo}/{variante}": resumir([r for r in resultados if r["modelo"] == modelo and r["variante"] == variante])
        for modelo in modelos
        for variante in VARIANTES
    }
    return {
        "ejecucion_id": ejecucion_id,
        "dataset_sha256": huella(datos),
        "nivel": datos["nivel"],
        "python": platform.python_version(),
        "plataforma": platform.platform(),
        "configuracion": configuracion.model_dump(mode="json"),
        "concurrencia": concurrencia,
        "prompts_sha256": huella(VARIANTES),
        "resumen": resumen,
        "resultados": resultados,
        "consumo": registro.resumen(ejecucion_id),
        "limites": [
            "Casos sintéticos conocidos, sin validación humana independiente ni eficacia educativa",
            "Una ejecución por combinación; no estima estabilidad ni generalización",
            "La comparación puede contaminar este conjunto para ajustes posteriores",
        ],
    }
