"""Benchmark retrieval candidates without modifying weights or reference annotations."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import statistics
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from goes_science_kg.config import relativa, ruta
from goes_science_kg.grafo.almacen import cargar as cargar_grafo
from goes_science_kg.rag import GraphRAG
from goes_science_kg.recuperacion.buscador import Buscador
from goes_science_kg.recuperacion.grafo import _cargar_grafo_validado, _convertir, aristas_del_grafo

CONJUNTOS = (
    "data/evaluacion/rag_preguntas.json",
    "data/evaluacion/rag_preguntas_prueba.json",
    "data/evaluacion/rag_preguntas_prueba2.json",
    "data/evaluacion/rag_preguntas_prueba3.json",
)
VARIANTES = ("baseline", "hibrido_sin_embeddings_saltos0", "hibrido_sin_embeddings_saltos1")


def _resumen_tiempos(tiempos: Sequence[float]) -> dict:
    ordenados = sorted(tiempos)
    return {
        "n": len(ordenados),
        "p50_ms": round(statistics.median(ordenados), 4),
        "p95_ms": round(ordenados[max(0, math.ceil(len(ordenados) * 0.95) - 1)], 4),
        "total_ms": round(sum(ordenados), 4),
    }


def metricas_recuperacion(preguntas: Sequence[dict], ordenes: Sequence[Sequence[str]], *, ks=(5, 10, 25)) -> dict:
    """Retain all relevant references, including missing documents, in evaluation denominators."""
    if not preguntas or len(preguntas) != len(ordenes):
        raise ValueError("Se requiere un ranking por pregunta y al menos una pregunta")
    filas = []
    for pregunta, orden in zip(preguntas, ordenes, strict=True):
        relevantes = set(pregunta["relevantes"])
        if not relevantes:
            raise ValueError(f"La pregunta {pregunta['id']} carece de relevantes")
        rango = next((i for i, documento_id in enumerate(orden, 1) if documento_id in relevantes), None)
        fila = {"id": pregunta["id"], "tipo": pregunta.get("tipo"), "mrr": 1 / rango if rango else 0.0}
        for k in ks:
            hits = len(relevantes.intersection(orden[:k]))
            fila[f"recall@{k}"] = hits / len(relevantes)
            fila[f"acierto@{k}"] = float(hits > 0)
        filas.append(fila)
    medidas = [campo for campo in filas[0] if campo not in {"id", "tipo"}]

    def promedio(sub: Sequence[dict]) -> dict:
        return {m: round(statistics.mean(f[m] for f in sub), 6) for m in medidas}

    return {
        "n": len(filas),
        **promedio(filas),
        "por_tipo": {
            tipo: promedio([f for f in filas if f["tipo"] == tipo])
            for tipo in sorted({f["tipo"] for f in filas if f["tipo"]})
        },
        "filas": filas,
    }


def comparar_recuperacion(
    *,
    conjuntos: Iterable[str | Path] = CONJUNTOS,
    directorio_grafo: str | Path = "data/grafo",
    repeticiones: int = 3,
    ks: tuple[int, ...] = (5, 10, 25),
    preguntas_permitidas: set[str] | None = None,
) -> dict:
    """Compare fixed lexical candidates against the baseline using real graph edges."""

    # Implementation notes:
    # El candidato se denomina híbrido por su capacidad; este experimento NO llama a embeddings.
    # Los conjuntos históricos son regresiones plata y no una muestra representativa de V4.
    if repeticiones < 1 or not ks or min(ks) < 1 or max(ks) > 100:
        raise ValueError("Se requieren repeticiones positivas y k entre 1 y 100")
    archivos = [ruta(p) for p in conjuntos]
    preguntas = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in archivos}
    excluidas = {
        nombre: [
            p["id"] for p in casos if preguntas_permitidas is not None and p["pregunta"] not in preguntas_permitidas
        ]
        for nombre, casos in preguntas.items()
    }
    if preguntas_permitidas is not None:
        preguntas = {
            nombre: [p for p in casos if p["pregunta"] in preguntas_permitidas] for nombre, casos in preguntas.items()
        }
    if len(preguntas) != len(archivos) or not preguntas:
        raise ValueError("Los conjuntos deben tener nombres distintos y no estar vacíos")
    directorio = ruta(directorio_grafo)
    tiempos_carga = defaultdict(list)
    tiempos_indice = defaultdict(list)
    tiempos_consulta = {v: defaultdict(list) for v in VARIANTES}
    ordenes = {v: {} for v in VARIANTES}
    estables = {v: True for v in VARIANTES}
    disponibles: dict[str, set[str]] = {}
    huella_buscador = ""
    version = ""
    for repeticion in range(repeticiones):
        inicio = time.perf_counter()
        nodos, aristas = cargar_grafo(str(directorio))
        tiempos_carga["baseline"].append((time.perf_counter() - inicio) * 1000)
        inicio = time.perf_counter()
        baseline = GraphRAG(nodos, aristas)
        tiempos_indice["baseline"].append((time.perf_counter() - inicio) * 1000)
        inicio = time.perf_counter()
        nuevos_nodos, nuevas_aristas, version = _cargar_grafo_validado(directorio, version=None)
        documentos = _convertir(nuevos_nodos, version)
        enlaces = aristas_del_grafo(nuevas_aristas)
        carga_candidato = (time.perf_counter() - inicio) * 1000
        inicio = time.perf_counter()
        buscador = Buscador(documentos, aristas=enlaces)
        indice_candidato = (time.perf_counter() - inicio) * 1000
        huella_buscador = buscador.huella
        disponibles["baseline"] = set(baseline.por_id)
        for variante in VARIANTES[1:]:
            tiempos_carga[variante].append(carga_candidato)
            tiempos_indice[variante].append(indice_candidato)
            disponibles[variante] = set(buscador.documentos)
        rotacion = repeticion % len(VARIANTES)
        for variante in VARIANTES[rotacion:] + VARIANTES[:rotacion]:
            for nombre, casos in preguntas.items():
                rankings = []
                for caso in casos:
                    inicio = time.perf_counter()
                    if variante == "baseline":
                        contexto = baseline.recuperar(
                            caso["pregunta"],
                            grado=caso.get("grado"),
                            asignatura=caso.get("asignatura"),
                            k_final=max(ks),
                        )
                        ids = [n.id for n, _ in contexto.nodos]
                    else:
                        resultados = buscador.buscar(
                            caso["pregunta"],
                            grado=caso.get("grado"),
                            asignatura=caso.get("asignatura"),
                            version=version,
                            k=max(ks),
                            saltos_grafo=int(variante[-1]),
                        )
                        ids = [r.documento.id for r in resultados]
                    tiempos_consulta[variante][nombre].append((time.perf_counter() - inicio) * 1000)
                    rankings.append(ids)
                if nombre in ordenes[variante] and ordenes[variante][nombre] != rankings:
                    estables[variante] = False
                ordenes[variante][nombre] = rankings
    resultados = {}
    for variante in VARIANTES:
        resultados[variante] = {
            "carga": _resumen_tiempos(tiempos_carga[variante]),
            "indice": _resumen_tiempos(tiempos_indice[variante]),
            "rankings_estables": estables[variante],
            "conjuntos": {},
        }
        for nombre, casos in preguntas.items():
            relevantes = {i for caso in casos for i in caso["relevantes"]}
            ausentes = sorted(relevantes - disponibles[variante])
            resultados[variante]["conjuntos"][nombre] = {
                **metricas_recuperacion(casos, ordenes[variante][nombre], ks=ks),
                "latencia": _resumen_tiempos(tiempos_consulta[variante][nombre]),
                "relevantes_ausentes": ausentes,
                "n_relevantes_ausentes": len(ausentes),
            }
    for variante in VARIANTES[1:]:
        resultados[variante]["pasa_gate_sin_regresion"] = (
            all(
                resultados[variante]["conjuntos"][nombre][metrica]
                >= resultados["baseline"]["conjuntos"][nombre][metrica]
                for nombre in preguntas
                for metrica in ("mrr", "recall@10" if 10 in ks else f"recall@{max(ks)}")
            )
            and estables[variante]
        )
    codigo = [ruta("src/goes_science_kg/rag.py"), *sorted(ruta("src/goes_science_kg/recuperacion").glob("*.py"))]
    datos = [directorio / nombre for nombre in ("manifest.json", "nodos.jsonl", "aristas.jsonl")]
    config = [ruta("config/mallas.yaml")]
    huellas = {relativa(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [*codigo, *datos, *config, *archivos]}
    return {
        "fecha": datetime.now(ZoneInfo("America/Bogota")).isoformat(),
        "entorno": {"python": platform.python_version(), "plataforma": platform.platform()},
        "version_curriculo": version,
        "modelos": {"generacion": None, "embeddings": None},
        "parametros": {"repeticiones": repeticiones, "ks": list(ks), "orden_variantes": "rotativo"},
        "preguntas_excluidas_por_alcance": excluidas,
        "huella_buscador": huella_buscador,
        "sha256": huellas,
        "limitaciones": [
            "Conjuntos históricos plata, parcialmente usados para ajustar el baseline; no es un test ciego nuevo.",
            "Los relevantes ausentes se conservan en el denominador de recall y se reportan por separado.",
            "El grafo sigue la versión local detectada; no representa resultados de un currículo V4 ausente.",
            "Latencias locales con caché de archivos del sistema sin vaciar; no son un SLO cloud.",
            "El nuevo candidato tiene textos y filtros distintos; el estudio evalúa producto completo, no sólo BM25.",
            "Tres repeticiones por defecto no establecen significación estadística ni eficacia pedagógica.",
            "Sin embeddings ni generación: coste de llamadas cloud cero; no demuestra calidad del RAG completo.",
        ],
        "resultados": resultados,
    }


def escribir_comparacion(datos: dict, *, salida_json: str | Path, salida_md: str | Path) -> None:
    """Write complete comparison results and disclose retrieval regressions."""
    destino_json, destino_md = Path(salida_json), Path(salida_md)
    destino_json.parent.mkdir(parents=True, exist_ok=True)
    destino_md.parent.mkdir(parents=True, exist_ok=True)
    destino_json.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lineas = [
        "# Comparación local de recuperación",
        "",
        f"Fecha: {datos['fecha']}. Currículo detectado: **{datos['version_curriculo']}**.",
        "",
        "Benchmark sin ajuste de pesos, sin embeddings y sin llamadas cloud. Ambos candidatos conservan "
        "sus diferencias de texto, filtros y navegación; el baseline permanece disponible.",
        "",
        "| Variante / conjunto | n | MRR | recall@10 | Ausentes | p50 ms | p95 ms |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for variante, resultado in datos["resultados"].items():
        for nombre, conjunto in resultado["conjuntos"].items():
            latencia = conjunto["latencia"]
            lineas.append(
                f"| {variante} / {nombre} | {conjunto['n']} | {conjunto['mrr']:.3f} | "
                f"{conjunto.get('recall@10', 0):.3f} | {conjunto['n_relevantes_ausentes']} | "
                f"{latencia['p50_ms']:.3f} | {latencia['p95_ms']:.3f} |"
            )
    lineas += ["", "| Variante | Carga p50 ms | Índice p50 ms | Gate sin regresión |", "| --- | ---: | ---: | --- |"]
    for variante, resultado in datos["resultados"].items():
        gate = resultado.get("pasa_gate_sin_regresion")
        decision = "Referencia" if gate is None else ("Pasa" if gate else "No pasa")
        lineas.append(
            f"| {variante} | {resultado['carga']['p50_ms']:.3f} | {resultado['indice']['p50_ms']:.3f} | {decision} |"
        )
    lineas += [
        "",
        "Gate fijado antes de medir: no disminuir MRR ni recall@10 en ninguno de los conjuntos "
        "y conservar rankings entre repeticiones. Es una regla de regresión, no validación educativa.",
        "",
        "La velocidad por sí sola no justifica sustituir el baseline. Conservar el nuevo sistema como "
        "candidato hasta medir embeddings y un test vigente e independiente de V4.",
        "",
        "Los hashes, IDs ausentes, métricas por consulta, carga/índice p95 y parámetros se conservan en el JSON.",
        "",
        "## Límites",
        "",
        *[f"- {limite}" for limite in datos["limitaciones"]],
        "",
        "## Reproducción",
        "",
        "```python",
        "from goes_science_kg.recuperacion.evaluacion import comparar_recuperacion, escribir_comparacion",
        "datos = comparar_recuperacion(repeticiones=3)",
        "escribir_comparacion(datos, salida_json='docs/investigacion/resultados_recuperacion.json',",
        "                     salida_md='docs/investigacion/resultados_recuperacion.md')",
        "```",
        "",
    ]
    destino_md.write_text("\n".join(lineas), encoding="utf-8")
