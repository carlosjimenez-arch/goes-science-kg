"""Adaptación offline de localizadores V4 y evaluación local del baseline congelado."""

from __future__ import annotations

import hashlib
import json
import time
from collections import Counter
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.recuperacion.baseline import BuscadorBaseline
from goes_science_kg.recuperacion.evaluacion_agentic import (
    ConfiguracionComparacion,
    ConsultaEvaluacion,
    Contextualizador,
    ObjetivoRelevante,
    _metricas,
    _resumir,
    _validar_evidencias,
    resolver_objetivos,
)


def _huella(datos) -> str:
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def preparar_conjunto_v4(datos: dict, curriculo: Curriculo) -> dict:
    """Transcribe todas las celdas declaradas; no interpreta juicios privados ni afina preguntas.

    Sólo consulta id, consulta, grado, asignatura, fuente y referencias_adicionales. Los archivos son
    identidades del currículo ingerido; este adaptador no abre rutas proporcionadas por el dataset.
    """
    if curriculo.version != "V4":
        raise ValueError("Esta adaptación requiere un currículo V4 verificado")
    fuentes = {f.archivo_local: f for f in curriculo.fuentes}
    fuentes_por_nombre = {f.archivo: f for f in curriculo.fuentes}
    if len(fuentes_por_nombre) != len(curriculo.fuentes):
        raise ValueError("Los nombres de archivo de las fuentes no son inequívocos")
    celdas_originales = {
        (hoja.fuente_id, hoja.nombre, celda.coordenada): celda
        for hoja in curriculo.hojas for registro in hoja.registros for celda in registro.celdas
    }
    filas = {(f.fuente_id, f.hoja, f.fila): f for f in curriculo.filas}
    consultas, gold, localizadores, avisos = [], {}, {}, []
    for caso in datos["casos"]:
        consulta = ConsultaEvaluacion(id=caso["id"], consulta=caso["consulta"], version="V4",
                                      grado=caso["grado"], asignatura=caso["asignatura"])
        if consulta.id in gold:
            raise ValueError("El conjunto contiene consultas duplicadas")
        consultas.append(consulta.model_dump(mode="json"))
        objetivos, registro_localizadores = [], []
        for indice, localizador in enumerate([caso["fuente"], *caso.get("referencias_adicionales", [])]):
            archivo = localizador["archivo"]
            path = PurePosixPath(archivo)
            if path.is_absolute() or ".." in path.parts or "\\" in archivo:
                raise ValueError("El localizador debe identificar una fuente relativa registrada")
            fuente = fuentes.get(archivo)
            if fuente is None and len(path.parts) == 1:
                fuente = fuentes_por_nombre.get(archivo)
            if fuente is None or fuente.sha256 != localizador["sha256"]:
                raise ValueError("El localizador no coincide con una fuente y SHA del currículo ingerido")
            filas_declaradas = localizador["filas"]
            if not filas_declaradas or len(filas_declaradas) != len(set(filas_declaradas)):
                raise ValueError("El localizador debe declarar filas únicas")
            pendientes = set(localizador["celdas"])
            if len(pendientes) != len(localizador["celdas"]):
                raise ValueError("El localizador no admite celdas repetidas")
            for fila in filas_declaradas:
                coordenadas = tuple(c for c in localizador["celdas"] if c.rstrip("0123456789") != c
                                    and c[len(c.rstrip('0123456789')):] == str(fila))
                objetivo = ObjetivoRelevante(documento=fuente.id, hoja=localizador["hoja"],
                                             fila=fila, celdas=coordenadas)
                objetivos.append(objetivo.model_dump(mode="json"))
                pendientes.difference_update(coordenadas)
                fila_curricular = filas.get((fuente.id, objetivo.hoja, fila))
                registro_localizadores.append({"rol": "fuente" if indice == 0 else "referencia_adicional",
                                               "archivo": fuente.archivo_local, "sha256": fuente.sha256,
                                               **objetivo.model_dump(mode="json"),
                                               "fila_curricular_id": fila_curricular.id if fila_curricular else None})
                if fila_curricular is None:
                    avisos.append({"caso": consulta.id, "tipo": "fila_no_curricular_o_ausente",
                                   **objetivo.model_dump(mode="json")})
                for coordenada in coordenadas:
                    celda = celdas_originales.get((fuente.id, objetivo.hoja, coordenada))
                    if celda is None or celda.valor is None or not str(celda.valor).strip():
                        avisos.append({"caso": consulta.id, "tipo": "celda_ausente_o_vacia",
                                       "documento": fuente.id, "hoja": objetivo.hoja, "celda": coordenada})
            if pendientes:
                raise ValueError("Hay celdas fuera de las filas declaradas en el localizador")
        gold[consulta.id], localizadores[consulta.id] = objetivos, registro_localizadores
    if not consultas:
        raise ValueError("El conjunto no contiene consultas")
    return {
        "consultas": {"schema_version": "1.0", "conjunto_id": datos.get("conjunto_id"),
                      "nivel": datos.get("nivel"), "casos": consultas},
        "gold_offline": {"schema_version": "1.0", "conjunto_id": datos.get("conjunto_id"),
                         "huella_curriculo": curriculo.huella, "objetivos": gold,
                         "localizadores_originales": localizadores, "avisos": avisos,
                         "regla": "Transcripción íntegra de fuente y referencias_adicionales, sin filtrar labels"},
    }


def escribir_conjunto_v4(conjunto: dict, destino: Path) -> dict[str, str]:
    """Guarda consultas públicas y localizadores de evaluación en archivos separados."""
    destino.mkdir(parents=True, exist_ok=True)
    rutas = {"consultas": destino / "consultas_publicas.json", "gold_offline": destino / "gold_offline.json"}
    for clave, archivo in rutas.items():
        archivo.write_text(json.dumps(conjunto[clave], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {clave: hashlib.sha256(archivo.read_bytes()).hexdigest() for clave, archivo in rutas.items()}


def evaluar_baseline_v4(
    consultas: Sequence[ConsultaEvaluacion], gold_offline: dict, *, baseline: BuscadorBaseline,
    curriculo: Curriculo, catalogo: CatalogoDisciplinas, contextualizar: Contextualizador,
    congelacion: dict, configuracion: ConfiguracionComparacion | None = None,
) -> dict:
    """Sólo recuperación/hidratación local; no instancia modelos ni publica snapshots piloto."""
    cfg = configuracion or ConfiguracionComparacion()
    if catalogo.huella_curriculo != curriculo.huella or gold_offline["huella_curriculo"] != curriculo.huella:
        raise ValueError("El currículo, catálogo y gold no comparten la misma huella")
    if set(gold_offline["objetivos"]) != {c.id for c in consultas} or len({c.id for c in consultas}) != len(consultas):
        raise ValueError("El gold debe corresponder exactamente a las consultas únicas")
    por_clasificacion = {f.fila_id: f for f in catalogo.filas}
    if len(por_clasificacion) != len(catalogo.filas) or set(por_clasificacion) != {f.id for f in curriculo.filas}:
        raise ValueError("El catálogo debe contener exactamente una decisión por fila")
    objetivos = {i: [ObjetivoRelevante.model_validate(g) for g in gs]
                 for i, gs in gold_offline["objetivos"].items()}
    gold = {c.id: resolver_objetivos(objetivos[c.id], baseline.documentos, version=c.version) for c in consultas}
    filas, cobertura = [], {}
    for caso in consultas:
        objetivo_filas = set(gold[caso.id]["filas"])
        clasificaciones = []
        for id_fila in objetivo_filas:
            clasificacion = por_clasificacion.get(id_fila)
            clasificaciones.append({"fila_id": id_fila,
                                    "estado": clasificacion.estado if clasificacion else "sin_fila_curricular",
                                    "disciplinas": list(clasificacion.disciplinas) if clasificacion else [],
                                    "admite_asignatura": bool(clasificacion and caso.asignatura in
                                                               clasificacion.disciplinas)})
        cobertura[caso.id] = clasificaciones
        for repeticion in range(cfg.repeticiones):
            inicio = time.perf_counter()
            fila = {"id": caso.id, "grado": caso.grado, "repeticion": repeticion, "errores": [],
                    "traza": None, "consumo": {"llamadas": 0, "reserva_usd": 0.0}}
            resultados, evidencias = [], []
            try:
                resultados = baseline.buscar(caso.consulta, version=caso.version, grado=caso.grado,
                                             asignatura=caso.asignatura, k=cfg.k, saltos_grafo=cfg.saltos_grafo)
                evidencias = contextualizar(resultados, version=caso.version, max_caracteres=cfg.max_caracteres)
                _validar_evidencias(evidencias, resultados)
                caracteres = len(json.dumps([e.model_dump(mode="json") for e in evidencias], ensure_ascii=False))
                if len(resultados) > cfg.k or caracteres > cfg.max_caracteres:
                    raise ValueError("El baseline o su contexto excedió el presupuesto predeclarado")
                fila["caracteres_contexto"] = caracteres
            except Exception as error:
                fila["errores"].append(type(error).__name__)
                resultados, evidencias = [], []
                fila["caracteres_contexto"] = 0
            fila["latencia_ms"] = (time.perf_counter() - inicio) * 1000
            fila["ranking_filas"] = [r.documento.id for r in resultados]
            fila["ranking_celdas"] = [e.id for e in evidencias]
            fila["filas"] = _metricas(fila["ranking_filas"], gold[caso.id]["filas"], cfg.k)
            n_celdas = max(1, len(evidencias))
            fila["celdas"] = _metricas(fila["ranking_celdas"], gold[caso.id]["celdas"], n_celdas)
            fila["celdas"]["recall_contexto"] = fila["celdas"].pop(f"recall@{n_celdas}")
            fila["abstencion_contexto"] = not any(e.version == caso.version for e in evidencias)
            filas.append(fila)
    resumen = _resumir(filas, cfg.k)
    resumen["por_grado"] = {str(g): _resumir([f for f in filas if f["grado"] == g], cfg.k)
                             for g in sorted({c.grado for c in consultas})}
    estados = dict(Counter(f.estado for f in catalogo.filas))
    pendientes = [f for f in catalogo.filas if f.estado == "abstencion"]
    return {
        "estado": "provisional_catalogo_piloto" if catalogo.modo == "piloto" else "catalogo_completo",
        "tipo_experimento": "baseline_local_sin_generacion",
        "configuracion": cfg.model_dump(mode="json"), "congelacion_previa_al_gold": congelacion,
        "huella_curriculo": curriculo.huella, "huella_baseline": baseline.huella,
        "sha256_consultas": _huella([c.model_dump(mode="json") for c in consultas]),
        "sha256_gold": _huella(gold_offline), "sha256_catalogo": _huella(catalogo.model_dump(mode="json")),
        "sha256_adaptador": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "catalogacion": {"modo": catalogo.modo, "filas": len(catalogo.filas), "estados": estados,
                         "sin_disciplina_utilizable": len(pendientes),
                         "sin_lecturas": sum(not f.lecturas for f in pendientes),
                         "abstenciones_con_lecturas": sum(bool(f.lecturas) for f in pendientes)},
        "gold_resuelto_offline": gold, "cobertura_catalogo_por_caso": cobertura,
        "avisos_gold": gold_offline["avisos"], "resumen": resumen, "ejecuciones": filas,
        "consumo_experimento": {"llamadas_gcp": 0, "usd_llamadas": 0},
        "seleccion": {"default": "baseline", "seleccionar_agentic": False,
                      "motivos": ["agentic_no_ejecutado", *(["muestra_total_insuficiente"]
                                  if len(consultas) < cfg.min_casos_totales else []),
                                  *(["catalogo_parcial"] if catalogo.modo == "piloto" else [])]},
        "limites": [
            "Las 19 consultas y condiciones son sintéticas plata; no son eficacia educativa ni oro oficial.",
            "El clasificador parcial no se completa por reglas, nombres o inferencia del evaluador.",
            "Fuente y referencias adicionales se mantienen completas, incluso encabezados y celdas vacías.",
            "La latencia es local, incluye hidratación y reutiliza caché; no es latencia de generación cloud.",
            "Esta lectura expone el conjunto a análisis; no debe usarse para afinar prompts y llamarlo ciego.",
        ],
    }


def escribir_baseline_v4(reporte: dict, *, salida_json: Path, salida_md: Path) -> None:
    salida_json.parent.mkdir(parents=True, exist_ok=True)
    salida_md.parent.mkdir(parents=True, exist_ok=True)
    salida_json.write_text(json.dumps(reporte, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    resumen = reporte["resumen"]
    k = reporte["configuracion"]["k"]
    lineas = ["# Baseline V4: medición local provisional", "",
              f"Estado: **{reporte['estado']}**. Sin llamadas a GCP; sin ejecución del candidato AgenticRAG.", "",
              f"Muestra: {resumen['n_consultas']} consultas; {resumen['n_ejecuciones']} ejecuciones locales. "
              f"Mínimo predeclarado: {reporte['configuracion']['min_casos_totales']}; selección insuficiente.", "",
              f"Catálogo: {reporte['catalogacion']['sin_disciplina_utilizable']} filas pendientes o en abstención "
              f"sin disciplina utilizable ({reporte['catalogacion']['sin_lecturas']} sin lecturas y "
              f"{reporte['catalogacion']['abstenciones_con_lecturas']} con lecturas). No se infirieron etiquetas.", "",
              "| Grado | n | MRR filas | Recall filas | MRR celdas | Recall contexto |",
              "|---|---:|---:|---:|---:|---:|"]
    for grado, datos in {"Todos": resumen, **resumen["por_grado"]}.items():
        lineas.append(f"| {grado} | {datos['n_consultas']} | {datos['filas']['mrr']:.4f} | "
                      f"{datos['filas'][f'recall@{k}']:.4f} | {datos['celdas']['mrr']:.4f} | "
                      f"{datos['celdas']['recall_contexto']:.4f} |")
    lineas += ["", "| Caso | Relevantes no resueltos en índice | Asignatura admitida en gold | Abstención contexto |",
               "|---|---:|---|---|"]
    for caso, gold in reporte["gold_resuelto_offline"].items():
        ejecucion = next(f for f in reporte["ejecuciones"] if f["id"] == caso)
        admite = any(f["admite_asignatura"] for f in reporte["cobertura_catalogo_por_caso"][caso])
        lineas.append(f"| {caso} | {len(gold['ausentes_en_indice'])} | {admite} | "
                      f"{ejecucion['abstencion_contexto']} |")
    lineas += ["", f"Latencia p50/p95: {resumen['latencia']['p50_ms']:.3f} / "
               f"{resumen['latencia']['p95_ms']:.3f} ms. Errores: {resumen['errores']}.", "",
               "Los localizadores no resueltos, blancos y encabezados permanecen en los denominadores. "
               "Los hashes, rankings completos y diagnósticos por caso están en el JSON.", "",
               "## Límites", "", *[f"- {limite}" for limite in reporte["limites"]], ""]
    salida_md.write_text("\n".join(lineas), encoding="utf-8")
