"""Comparación real de embeddings Vertex sin ajustar parámetros a las métricas."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime
from importlib.metadata import version as version_paquete
from pathlib import Path
from zoneinfo import ZoneInfo

from goes_science_kg.config import relativa, ruta
from goes_science_kg.recuperacion.buscador import Buscador
from goes_science_kg.recuperacion.embeddings import IndiceEmbeddings
from goes_science_kg.recuperacion.evaluacion import (
    CONJUNTOS,
    _resumen_tiempos,
    comparar_recuperacion,
    metricas_recuperacion,
)
from goes_science_kg.recuperacion.grafo import _cargar_grafo_validado, _convertir, aristas_del_grafo
from goes_science_kg.recuperacion.vertex_embeddings import VertexEmbeddings

LOGGER = logging.getLogger(__name__)


def ejecutar_experimento(
    *,
    proyecto: str,
    directorio_operacion: str | Path = "data/operaciones/embeddings/gemini-embedding-001",
    salida_json: str | Path = "docs/investigacion/resultados_embeddings_vertex.json",
    salida_md: str | Path = "docs/investigacion/resultados_embeddings_vertex.md",
    repeticiones: int = 3,
    max_preguntas_autorizadas: int = 98,
) -> dict:
    """Vectoriza V3 detectada, mide variantes fijas y conserva contabilidad y regresiones.

    La disponibilidad de V4 no se presume: la versión se fija desde el grafo cargado. El corpus
    histórico no es un test independiente; estos resultados no cambian el default automáticamente.
    """
    if not 1 <= repeticiones <= 10 or not 1 <= max_preguntas_autorizadas <= 98:
        raise ValueError("El benchmark admite entre una y diez repeticiones")
    operacion = ruta(directorio_operacion)
    proveedor = VertexEmbeddings(
        proyecto=proyecto,
        directorio_cache=operacion / "cache",
        ledger=operacion / "experimento_20261021.jsonl",
    )
    contabilidad_inicio = proveedor.resumen()
    nodos, aristas, version_curriculo = _cargar_grafo_validado("data/grafo", version=None)
    documentos = _convertir(nodos, version_curriculo)
    if len(documentos) > 3158:
        raise ValueError("El corpus excede los 3.158 documentos expresamente autorizados")
    enlaces = aristas_del_grafo(aristas)
    conjuntos = {ruta(p).name: json.loads(ruta(p).read_text(encoding="utf-8")) for p in CONJUNTOS}
    total_casos = sum(len(casos) for casos in conjuntos.values())
    textos_todos = list(
        dict.fromkeys(
            p["pregunta"] for nombre in sorted(conjuntos) for p in sorted(conjuntos[nombre], key=lambda p: p["id"])
        )
    )
    textos_preguntas = textos_todos[:max_preguntas_autorizadas]
    permitidas = set(textos_preguntas)
    omitidas = [
        {"conjunto": nombre, "id": p["id"], "motivo": "Fuera del límite de preguntas expresamente autorizado"}
        for nombre in sorted(conjuntos)
        for p in conjuntos[nombre]
        if p["pregunta"] not in permitidas
    ]
    conjuntos = {nombre: [p for p in casos if p["pregunta"] in permitidas] for nombre, casos in conjuntos.items()}
    LOGGER.info(
        "Preflight: %s; %d documentos; %d consultas únicas", version_curriculo, len(documentos), len(textos_preguntas)
    )
    inicio = time.perf_counter()
    proveedor.vectorizar_texto(documentos[0].texto, tarea="RETRIEVAL_DOCUMENT")
    proveedor.vectorizar_texto(documentos[1].texto, tarea="RETRIEVAL_DOCUMENT")
    proveedor.vectorizar_texto(textos_preguntas[0], tarea="RETRIEVAL_QUERY")
    matriz = proveedor.vectorizar([d.texto for d in documentos], tarea="RETRIEVAL_DOCUMENT")
    tiempo_documentos = (time.perf_counter() - inicio) * 1000
    inicio = time.perf_counter()
    matriz_consultas = proveedor.vectorizar(textos_preguntas, tarea="RETRIEVAL_QUERY")
    tiempo_consultas = (time.perf_counter() - inicio) * 1000
    por_pregunta = dict(zip(textos_preguntas, matriz_consultas, strict=True))
    indice = IndiceEmbeddings(documentos, matriz, modelo=proveedor.modelo)
    indice.guardar(operacion / "corpus_768.npz")
    buscador = Buscador(documentos, indice_embeddings=indice, aristas=enlaces)
    # La comparación local se mide de nuevo para el mismo host y la misma versión de código.
    reporte = comparar_recuperacion(repeticiones=repeticiones, preguntas_permitidas=permitidas)
    if reporte["version_curriculo"] != version_curriculo:
        raise RuntimeError("El currículo cambió durante el experimento; no se pueden comparar versiones")
    variantes = ("denso_768", "hibrido_768_saltos0", "hibrido_768_saltos1")
    for variante in variantes:
        resultados = {"conjuntos": {}, "rankings_estables": True}
        for nombre, preguntas in conjuntos.items():
            tiempos = []
            orden_anterior = None
            for _ in range(repeticiones):
                rankings = []
                for pregunta in preguntas:
                    inicio = time.perf_counter()
                    vector = por_pregunta[pregunta["pregunta"]]
                    if variante == "denso_768":
                        permitidos = buscador._permitidos(
                            version_curriculo,
                            pregunta.get("grado"),
                            pregunta.get("asignatura"),
                        )
                        ranking = indice.buscar(vector, modelo=proveedor.modelo, permitidos=permitidos, limite=25)
                        ids = [documento_id for documento_id, _ in ranking]
                    else:
                        ranking = buscador.buscar(
                            pregunta["pregunta"],
                            grado=pregunta.get("grado"),
                            asignatura=pregunta.get("asignatura"),
                            version=version_curriculo,
                            k=25,
                            vector_consulta=vector,
                            modelo_embeddings=proveedor.modelo,
                            saltos_grafo=int(variante[-1]),
                        )
                        ids = [r.documento.id for r in ranking]
                    tiempos.append((time.perf_counter() - inicio) * 1000)
                    rankings.append(ids)
                if orden_anterior is not None and rankings != orden_anterior:
                    resultados["rankings_estables"] = False
                orden_anterior = rankings
            ausentes = sorted({i for p in preguntas for i in p["relevantes"]} - set(buscador.documentos))
            resultados["conjuntos"][nombre] = {
                **metricas_recuperacion(preguntas, rankings),
                "latencia": _resumen_tiempos(tiempos),
                "relevantes_ausentes": ausentes,
                "n_relevantes_ausentes": len(ausentes),
            }
        resultados["pasa_gate_sin_regresion"] = (
            all(
                resultados["conjuntos"][nombre][metrica]
                >= reporte["resultados"]["baseline"]["conjuntos"][nombre][metrica]
                for nombre in conjuntos
                for metrica in ("mrr", "recall@10")
            )
            and resultados["rankings_estables"]
        )
        reporte["resultados"][variante] = resultados
    eventos = [json.loads(linea) for linea in proveedor.ledger.read_text(encoding="utf-8").splitlines()]
    latencias_cloud = [e["latencia_ms"] for e in eventos if e["evento"] == "completada"]
    reporte.update(
        {
            "fecha": datetime.now(ZoneInfo("America/Bogota")).isoformat(),
            "estado": "completado",
            "sdk_google_genai": version_paquete("google-genai"),
            "modelos": {"generacion": None, "embeddings": proveedor.modelo},
            "huella_buscador_denso": buscador.huella,
            "huella_vectores": indice.huella_vectores,
            "contabilidad_inicio": contabilidad_inicio,
            "contabilidad_fin": proveedor.resumen(),
            "tiempos_vectorizacion": {
                "documentos_y_preflight_ms": tiempo_documentos,
                "consultas_ms": tiempo_consultas,
                "peticion_cloud": _resumen_tiempos(latencias_cloud) if latencias_cloud else None,
            },
            "corpus": {
                "documentos": len(documentos),
                "preguntas_unicas": len(textos_preguntas),
                "casos_disponibles": total_casos,
                "preguntas_unicas_disponibles": len(textos_todos),
                "casos_evaluados": sum(len(casos) for casos in conjuntos.values()),
                "preguntas_no_ejecutadas": omitidas,
                "caracteres": sum(len(d.texto) for d in documentos),
                "dtype": str(matriz.dtype),
                "dimensiones": list(matriz.shape),
                "bytes_matriz": int(matriz.nbytes),
            },
            "decision": "Mantener baseline; un benchmark histórico reutilizado no valida V4 ni eficacia educativa.",
        }
    )
    for archivo in [
        operacion / "corpus_768.npz",
        proveedor.ledger,
        ruta("src/goes_science_kg/recuperacion/vertex_embeddings.py"),
        ruta("src/goes_science_kg/recuperacion/experimento_vertex.py"),
    ]:
        reporte["sha256"][relativa(archivo)] = hashlib.sha256(archivo.read_bytes()).hexdigest()
    reporte["limitaciones"] += [
        "Las latencias locales densas excluyen la petición de embedding de consulta; ésta se reporta aparte.",
        "El ledger incluye el intento inicial sin red y sus reservas; no se afirma que esos tokens fueran facturados.",
        "USD se estima con tokens reportados y tarifa documentada; no representa una factura reconciliada.",
        "La API puede cambiar internamente el modelo: se conservan vectores y sus hashes para repetición.",
        "Los conjuntos suman 100 textos únicos, no 98. Se enviaron sólo los 98 primeros por conjunto/id; "
        "dos casos fuera del permiso no se enviaron ni se incluyeron en ninguna métrica de esta comparación.",
    ]
    _escribir_reporte(reporte, ruta(salida_json), ruta(salida_md))
    return reporte


def _escribir_reporte(datos: dict, json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    contabilidad = datos["contabilidad_fin"]
    lineas = [
        "# Experimento real de recuperación con Vertex",
        "",
        f"Fecha: {datos['fecha']}. Currículo: **{datos['version_curriculo']}**. "
        f"Modelo: **{contabilidad['modelo']}**, 768 dimensiones, {contabilidad['region']}.",
        "",
        "Se usaron ADC y proyecto explícito. No se ajustaron pesos después de observar resultados. "
        "Los 98 casos históricos son regresión reutilizada; esta comparación no valida la V4.",
        "",
        "Los archivos contienen 100 preguntas únicas. Se limitó el envío a las 98 autorizadas por orden "
        "de conjunto/id; dos casos se reportan sin ejecución y se excluyen por igual de todas las variantes.",
        "",
        "| Variante / conjunto | MRR | recall@10 | Ausentes | p50 local ms | p95 local ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variante, resultado in datos["resultados"].items():
        for nombre, conjunto in resultado["conjuntos"].items():
            lineas.append(
                f"| {variante} / {nombre} | {conjunto['mrr']:.3f} | {conjunto['recall@10']:.3f} | "
                f"{conjunto['n_relevantes_ausentes']} | {conjunto['latencia']['p50_ms']:.3f} | "
                f"{conjunto['latencia']['p95_ms']:.3f} |"
            )
    lineas += ["", "Gate previo: MRR y recall@10 sin regresión en cada conjunto y rankings estables.", ""]
    for variante, resultado in datos["resultados"].items():
        if variante != "baseline":
            lineas.append(f"- {variante}: {'pasa' if resultado['pasa_gate_sin_regresion'] else 'no pasa'}.")
    lineas += [
        "",
        datos["decision"],
        "",
        "## Contabilidad",
        "",
        f"- Peticiones reservadas: {contabilidad['requests_reservadas']}; completadas: "
        f"{contabilidad['completadas']}; errores: {contabilidad['errores']}; cache hits: {contabilidad['cache_hits']}.",
        f"- Tokens reportados: {contabilidad['tokens_reportados']}; reserva conservadora: "
        f"{contabilidad['tokens_reservados']}.",
        f"- USD estimados por tokens reportados: **{contabilidad['usd_estimado_tokens_reportados']:.6f}**; "
        f"USD reservados: {contabilidad['usd_reservado']:.6f}; límite: {contabilidad['limite_usd']}.",
        "- Tarifa consultada: [precios oficiales de Vertex](https://cloud.google.com/vertex-ai/generative-ai/pricing).",
        "- Una petición por texto, RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY, truncamiento desactivado, "
        "SDK attempts=1, timeout 30 segundos, concurrencia 3 y caché incremental por contenido/configuración.",
        "",
        "Los hashes, datos por consulta y ruta del ledger figuran en el JSON. "
        "Los vectores/cache operativos no se versionan en Git.",
        "",
        "## Límites",
        "",
        *[f"- {limite}" for limite in datos["limitaciones"]],
        "",
        "## Reproducción",
        "",
        "```python",
        "from goes_science_kg.recuperacion.experimento_vertex import ejecutar_experimento",
        f"ejecutar_experimento(proyecto={contabilidad['proyecto']!r})",
        "```",
        "",
    ]
    md_path.write_text("\n".join(lineas), encoding="utf-8")
