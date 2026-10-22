"""Medición local de cobertura del contexto; no juzga relaciones ni consulta modelos."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from collections.abc import Sequence
from datetime import date
from pathlib import Path

import numpy as np

from goes_science_kg.producto._juicios_contratos import SolicitudConocimiento
from goes_science_kg.producto.juicios import PreparadorConocimiento, datos_juicio


def _percentiles(valores: Sequence[float]) -> dict[str, float | None]:
    if not valores:
        return {"p50": None, "p95": None}
    p50, p95 = np.percentile(valores, [50, 95])
    return {"p50": round(float(p50), 3), "p95": round(float(p95), 3)}


def medir_contexto_paises(
    preparador: PreparadorConocimiento, presupuestos: Sequence[int] = (18000, 24000, 40000)
) -> dict:
    """Repite el mismo corpus completo de contrastes con edición fijada en cada presupuesto.

    Sólo accede al preparador y sus fuentes verificadas; no recibe un proveedor ni un gold.
    Reutiliza la caché local y restaura el presupuesto original incluso ante un error.
    """
    if (
        not presupuestos
        or len(set(presupuestos)) != len(presupuestos)
        or any(type(p) is not int or not 2000 <= p <= 40000 for p in presupuestos)
    ):
        raise ValueError("Se requieren presupuestos únicos de entre 2000 y 40000 caracteres")
    politica = preparador.informe.politica
    candidatos = [
        c
        for c in preparador.informe.candidatos
        if c.tipo == "contraste_pais"
        and preparador.nodos[c.destino].fuente is not None
        and preparador.nodos[c.destino].fuente.documento.removeprefix("DOC:") in politica.ediciones_por_documento
    ]
    if not candidatos:
        raise ValueError("No hay contrastes de países con edición fijada en la política")
    mediciones = []
    original = preparador.max_caracteres
    try:
        for presupuesto in presupuestos:
            preparador.max_caracteres = presupuesto
            estados, motivos, filas, latencias, longitudes, fallidos = Counter(), Counter(), set(), [], [], []
            inicio = time.perf_counter()
            for candidato in candidatos:
                antes = time.perf_counter()
                expediente = preparador.preparar(SolicitudConocimiento(candidato_id=candidato.id))
                latencias.append((time.perf_counter() - antes) * 1000)
                estados[expediente.estado] += 1
                if expediente.estado == "preparado":
                    filas.add(candidato.fila_id)
                    longitudes.append(len(json.dumps(datos_juicio(expediente), ensure_ascii=False)))
                else:
                    motivos.update(expediente.motivos)
                    fallidos.append(candidato.id)
            mediciones.append(
                {
                    "max_caracteres": presupuesto,
                    "estados": dict(estados),
                    "filas_con_preparacion": len(filas),
                    "segundos_total": round(time.perf_counter() - inicio, 3),
                    "latencia_local_ms": _percentiles(latencias),
                    "longitud_payload_caracteres": _percentiles(longitudes),
                    "motivos_abstencion": dict(motivos),
                    "candidatos_sin_contexto": fallidos,
                }
            )
    finally:
        preparador.max_caracteres = original
    raiz = Path(__file__).resolve().parents[1]
    return {
        "fecha": date.today().isoformat(),
        "corpus": (
            f"Todos los {len(candidatos)} contrastes de países con edición fijada en la política; "
            "no son un gold semántico"
        ),
        "candidatos": len(candidatos),
        "huella_candidatos": preparador.informe.huella_candidatos,
        "huella_curriculo": preparador.curriculo.huella,
        "codigo_preparacion_sha256": hashlib.sha256((raiz / "producto/juicios.py").read_bytes()).hexdigest(),
        "codigo_fragmentos_sha256": hashlib.sha256((raiz / "motor/fragmentos.py").read_bytes()).hexdigest(),
        "modelos_ejecutados": 0,
        "presupuestos": mediciones,
        "limites": [
            "Se mide preparación y cobertura estructural de grupos, no implicación semántica ni calidad de enseñanza",
            "Cada contexto conserva fuentes verificadas y límites de citas; "
            "una ventana no acredita todo el alcance normativo",
            "Medición secuencial local con caché compartida; "
            "no se interpreta como comparativa causal de latencia de modelos",
            "Los presupuestos comparten una instancia sin ejecutar ni reanudar juicios; "
            "no se reutiliza un dictamen entre políticas",
        ],
        "fuentes_verificadas": preparador.fuentes.estadisticas(),
    }
