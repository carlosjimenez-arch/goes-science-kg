"""Harness de recuperación: consultas públicas al candidato, gold de celdas sólo offline."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import re
import statistics
import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.puertos import Recuperador
from goes_science_kg.recuperacion.agentic import COORDENADA, BuscadorAgentic
from goes_science_kg.recuperacion.modelos import Documento, Resultado, huella_corpus


def _huella(datos: Any) -> str:
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


class ConsultaEvaluacion(BaseModel):
    """Lista blanca que puede salir hacia el recuperador; ningún campo de respuesta esperada."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1)
    consulta: str = Field(min_length=3, max_length=2000)
    version: str = Field(min_length=1, max_length=32)
    grado: int = Field(ge=1, le=13)
    asignatura: str | None = Field(default=None, max_length=80)


class ObjetivoRelevante(BaseModel):
    """Localizador de gold offline; documento es la identidad de fuente, no el ID de una fila."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    documento: str = Field(min_length=1)
    hoja: str = Field(min_length=1)
    fila: int = Field(ge=1)
    celdas: tuple[str, ...] = Field(min_length=1, max_length=64)

    @model_validator(mode="after")
    def _coordenadas(self):
        if len(self.celdas) != len(set(self.celdas)):
            raise ValueError("El gold no admite celdas duplicadas")
        if any(not COORDENADA.fullmatch(celda) or int(re.search(r"\d+$", celda)[0]) != self.fila
               for celda in self.celdas):
            raise ValueError("Cada celda relevante debe pertenecer a su fila física")
        return self


class ConfiguracionComparacion(BaseModel):
    """Gate de regresión predeclarado; cambiarlo exige otro experimento, no reetiquetar éste."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    k: int = Field(default=10, ge=1, le=100)
    max_caracteres: int = Field(default=18000, ge=100)
    saltos_grafo: int = Field(default=1, ge=0, le=2)
    repeticiones: int = Field(default=3, ge=1, le=10)
    max_p95_total_ms: float = Field(default=6000, gt=0, allow_inf_nan=False)
    max_p95_incremental_ms: float = Field(default=5000, gt=0, allow_inf_nan=False)
    max_reserva_usd_por_consulta: float = Field(default=0.02, gt=0, allow_inf_nan=False)
    min_casos_totales: int = Field(default=20, ge=1)
    min_casos_por_grado: int = Field(default=3, ge=1)
    grados_esperados: tuple[int, ...] = ()
    conjunto_independiente: bool = False

    @model_validator(mode="after")
    def _grados(self):
        if len(self.grados_esperados) != len(set(self.grados_esperados)) or any(
            not 1 <= grado <= 13 for grado in self.grados_esperados
        ):
            raise ValueError("Los grados esperados deben ser únicos y estar entre uno y trece")
        return self


class Contextualizador(Protocol):
    def __call__(
        self, resultados: Sequence[Resultado], *, version: str, max_caracteres: int,
    ) -> list[Evidencia]:
        """Mismo hidratador verificable y presupuesto para las dos variantes."""


def cargar_consultas(archivo: Path) -> list[ConsultaEvaluacion]:
    """Extrae sólo consultas/filtros, aunque el archivo contenga claves privadas de evaluación.

    No consulta ni envía campos privados del evaluador. La correspondencia del gold debe
    suministrarse mediante un mapping separado, construido fuera del modelo y del recuperador.
    """
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    casos = datos["casos"] if isinstance(datos, dict) else datos
    campos = tuple(ConsultaEvaluacion.model_fields)
    consultas = [ConsultaEvaluacion.model_validate({k: caso[k] for k in campos if k in caso}) for caso in casos]
    if not consultas or len({c.id for c in consultas}) != len(consultas):
        raise ValueError("Las consultas deben tener IDs únicos y un conjunto no vacío")
    return consultas


def _fila_documento(documento: Documento) -> tuple[str, str, int] | None:
    fuente = documento.fuente
    fila = fuente.get("fila")
    if not isinstance(fila, int) or isinstance(fila, bool) or not fuente.get("hoja"):
        return None
    return fuente["documento"], fuente["hoja"], fila


def resolver_objetivos(
    objetivos: Sequence[ObjetivoRelevante], documentos: Mapping[str, Documento], *, version: str,
) -> dict:
    """Resuelve celdas a IDs y filas; los ausentes permanecen en todos los denominadores."""
    if not objetivos:
        raise ValueError("Cada consulta necesita al menos un objetivo relevante offline")
    por_fila: dict[tuple, Documento] = {}
    for documento in documentos.values():
        clave = _fila_documento(documento)
        if documento.version != version or clave is None:
            continue
        if clave in por_fila:
            raise ValueError("El índice representa ambiguamente una misma fila física")
        por_fila[clave] = documento
    filas, celdas, ausentes = set(), set(), []
    for objetivo in objetivos:
        clave = (objetivo.documento, objetivo.hoja, objetivo.fila)
        documento = por_fila.get(clave)
        id_fila = documento.id if documento else "AUSENTE_FILA:" + _huella(clave)
        filas.add(id_fila)
        for coordenada in objetivo.celdas:
            celdas.add(f"{id_fila}#CELDA:{coordenada}")
            if documento is None or coordenada not in documento.fuente.get("celdas", []):
                ausentes.append({**objetivo.model_dump(mode="json"), "celda": coordenada,
                                 "motivo": "fila_ausente" if documento is None else "selector_ausente"})
    return {"filas": sorted(filas), "celdas": sorted(celdas), "ausentes_en_indice": ausentes}


def _metricas(orden: Sequence[str], relevantes: Sequence[str], k: int) -> dict:
    esperados = set(relevantes)
    unicos = list(dict.fromkeys(orden))[:k]
    rango = next((i for i, identificador in enumerate(unicos, 1) if identificador in esperados), None)
    return {"mrr": 1 / rango if rango else 0.0,
            f"recall@{k}": len(esperados.intersection(unicos)) / len(esperados)}


def _tiempos(valores: Sequence[float]) -> dict:
    orden = sorted(valores)
    return {"n": len(orden), "p50_ms": statistics.median(orden),
            "p95_ms": orden[math.ceil(len(orden) * 0.95) - 1], "max_ms": max(orden)}


def _consumo(medir: Callable[[], Mapping] | None) -> dict | None:
    if medir is None:
        return None
    datos = medir()
    llamadas, reserva = datos["llamadas"], datos["reserva_usd"]
    if not isinstance(llamadas, int) or llamadas < 0 or not math.isfinite(reserva) or reserva < 0:
        raise ValueError("La medición de consumo debe ser acumulativa, finita y no negativa")
    return {"llamadas": llamadas, "reserva_usd": reserva}


def _diferencia(antes: dict | None, despues: dict | None) -> dict | None:
    if antes is None or despues is None:
        return None
    diferencia = {k: despues[k] - antes[k] for k in antes}
    if any(valor < -1e-12 for valor in diferencia.values()):
        raise ValueError("El ledger de una ejecución no puede retroceder durante la comparación")
    return diferencia


def _validar_evidencias(evidencias: Sequence[Evidencia], resultados: Sequence[Resultado]) -> None:
    """Comprueba correspondencia estructural; el callback confiable verifica los bytes de origen."""
    documentos = {r.documento.id: r.documento for r in resultados}
    vistos = set()
    for evidencia in evidencias:
        if evidencia.id in vistos or hashlib.sha256(evidencia.texto.encode()).hexdigest() != evidencia.huella:
            raise ValueError("La evidencia duplica identidad o no conserva su huella de texto")
        vistos.add(evidencia.id)
        id_fila, separador, coordenada = evidencia.id.partition("#CELDA:")
        documento = documentos.get(id_fila)
        if documento is None or documento.version != evidencia.version:
            raise ValueError("La evidencia no pertenece a una fila recuperada de la misma versión")
        if any(evidencia.fuente.get(k) != documento.fuente.get(k) for k in ("documento", "hoja")):
            raise ValueError("La evidencia cambió la identidad de su fuente")
        if separador and (not COORDENADA.fullmatch(coordenada) or evidencia.fuente.get("celdas") != [coordenada]):
            raise ValueError("El identificador no corresponde a la celda hidratada")


def _resumir(filas: Sequence[dict], k: int) -> dict:
    salida = {"n_consultas": len({f["id"] for f in filas}), "n_ejecuciones": len(filas),
              "errores": sum(bool(f["errores"]) for f in filas),
              "latencia": _tiempos([f["latencia_ms"] for f in filas]),
              "latencia_por_repeticion": {
                  str(r): _tiempos([f["latencia_ms"] for f in filas if f["repeticion"] == r])
                  for r in sorted({f["repeticion"] for f in filas})
              }}
    for unidad in ("filas", "celdas"):
        medidas = ("mrr", f"recall@{k}" if unidad == "filas" else "recall_contexto")
        salida[unidad] = {m: statistics.mean(f[unidad][m] for f in filas) for m in medidas}
    salida["rankings_estables"] = all(len({
        json.dumps([f["ranking_filas"], f["ranking_celdas"]]) for f in filas if f["id"] == identificador
    }) == 1 for identificador in {f["id"] for f in filas})
    return salida


def comparar_agentic(
    consultas: Sequence[ConsultaEvaluacion],
    objetivos_relevantes: Mapping[str, Sequence[ObjetivoRelevante]],
    *,
    baseline: Recuperador,
    candidato: BuscadorAgentic,
    contextualizar: Contextualizador,
    configuracion: ConfiguracionComparacion | None = None,
    medir_consumo: Callable[[], Mapping] | None = None,
) -> dict:
    """Ejecuta explícitamente una comparación; importar el módulo nunca hace llamadas de nube.

    La integración autoriza por separado corpus, consultas, modelo y presupuesto. Sólo esta función
    ejecutada con un ModeloEstructurado real puede consumir el ledger y la red de ese proveedor.
    """
    cfg = configuracion or ConfiguracionComparacion()
    consultas = [ConsultaEvaluacion.model_validate(c.model_dump()) for c in consultas]
    ids = {c.id for c in consultas}
    if not consultas or len(ids) != len(consultas) or ids != set(objetivos_relevantes):
        raise ValueError("Se requieren consultas únicas y una correspondencia exacta de gold offline")
    documentos = getattr(baseline, "documentos", None)
    if not isinstance(documentos, Mapping) or huella_corpus(documentos.values()) != huella_corpus(
        candidato.documentos.values()
    ):
        raise ValueError("Las variantes deben recuperar exactamente el mismo corpus")
    gold = {c.id: resolver_objetivos(objetivos_relevantes[c.id], documentos, version=c.version) for c in consultas}
    config_hash = _huella(cfg.model_dump(mode="json"))
    consultas_hash = _huella([c.model_dump(mode="json") for c in consultas])
    gold_hash = _huella({i: [g.model_dump(mode="json") for g in objetivos_relevantes[i]] for i in sorted(ids)})
    ejecuciones: dict[str, list[dict]] = {"baseline": [], "agentic": []}
    for repeticion in range(cfg.repeticiones):
        variantes = ("baseline", "agentic") if repeticion % 2 == 0 else ("agentic", "baseline")
        for variante in variantes:
            for caso in consultas:
                consumo_inicial = _consumo(medir_consumo)
                inicio = time.perf_counter()
                fila = {"id": caso.id, "grado": caso.grado, "repeticion": repeticion,
                        "errores": [], "traza": None}
                resultados, evidencias = [], []
                try:
                    parametros = {"version": caso.version, "grado": caso.grado, "asignatura": caso.asignatura,
                                  "k": cfg.k, "saltos_grafo": cfg.saltos_grafo}
                    if variante == "baseline":
                        resultados = baseline.buscar(caso.consulta, **parametros)
                    else:
                        busqueda = candidato.buscar_con_traza(caso.consulta, **parametros)
                        resultados, fila["traza"] = busqueda.resultados, busqueda.traza
                        fila["errores"].extend(busqueda.traza["errores"])
                    if len(resultados) > cfg.k:
                        raise ValueError("El recuperador excedió el mismo K predeclarado")
                    if any(documentos.get(r.documento.id) != r.documento for r in resultados):
                        raise ValueError("El recuperador devolvió un ID o contenido ajeno al índice")
                    evidencias = contextualizar(resultados, version=caso.version, max_caracteres=cfg.max_caracteres)
                    _validar_evidencias(evidencias, resultados)
                    caracteres = len(json.dumps([e.model_dump(mode="json") for e in evidencias], ensure_ascii=False))
                    if caracteres > cfg.max_caracteres:
                        raise ValueError("El contextualizador excedió el presupuesto común de contexto")
                    fila["caracteres_contexto"] = caracteres
                except Exception as error:
                    fila["errores"].append(type(error).__name__)
                    resultados, evidencias = [], []
                    fila["caracteres_contexto"] = 0
                fila["latencia_ms"] = (time.perf_counter() - inicio) * 1000
                fila["consumo"] = _diferencia(consumo_inicial, _consumo(medir_consumo))
                fila["ranking_filas"] = [r.documento.id for r in resultados]
                fila["ranking_celdas"] = [e.id for e in evidencias]
                fila["filas"] = _metricas(fila["ranking_filas"], gold[caso.id]["filas"], cfg.k)
                # K significa filas recuperadas. El contexto puede contener varias celdas por fila;
                # no se trunca artificialmente a K celdas ni se oculta su presupuesto común.
                fila["celdas"] = _metricas(fila["ranking_celdas"], gold[caso.id]["celdas"],
                                           max(1, len(fila["ranking_celdas"])))
                fila["celdas"]["recall_contexto"] = fila["celdas"].pop(
                    f"recall@{max(1, len(fila['ranking_celdas']))}"
                )
                ejecuciones[variante].append(fila)
    resumen = {}
    for variante, filas in ejecuciones.items():
        resumen[variante] = _resumir(filas, cfg.k)
        resumen[variante]["por_grado"] = {
            str(g): _resumir([f for f in filas if f["grado"] == g], cfg.k)
            for g in sorted({c.grado for c in consultas})
        }
    gate = _evaluar_gate(consultas, ejecuciones, resumen, cfg)
    return {
        "fecha": datetime.now(UTC).isoformat(), "python": platform.python_version(),
        "configuracion": cfg.model_dump(mode="json"), "configuracion_sha256": config_hash,
        "consultas_sha256": consultas_hash, "gold_sha256": gold_hash,
        "corpus_sha256": huella_corpus(documentos.values()), "candidato": candidato.identidad,
        "candidato_sha256": candidato.huella,
        "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "gold_resuelto_offline": gold, "resumen": resumen, "ejecuciones": ejecuciones, "gate": gate,
        "limites": [
            "Los objetivos relevantes sólo intervienen offline; nunca forman parte del mensaje al planner.",
            "Los ausentes permanecen en recall y se reportan como defectos de cobertura del índice.",
            "La latencia incluye recuperación e hidratación, no redacción, jueces ni publicación.",
            "La reserva es una cota conservadora del ledger, no un importe facturado ni un precio universal.",
            "Cada repetición puede reutilizar caché del modelo; el gate usa el peor p95 entre repeticiones.",
            "Un gate técnico aprobado no demuestra eficacia educativa ni generalización a otros grados.",
        ],
    }


def _evaluar_gate(consultas, ejecuciones, resumen, cfg: ConfiguracionComparacion) -> dict:
    motivos = []
    if not cfg.conjunto_independiente:
        motivos.append("conjunto_no_declarado_independiente")
    if len(consultas) < cfg.min_casos_totales:
        motivos.append("muestra_total_insuficiente")
    grados = {c.grado for c in consultas}
    if set(cfg.grados_esperados) - grados:
        motivos.append("faltan_grados_predeclarados")
    if any(sum(c.grado == g for c in consultas) < cfg.min_casos_por_grado for g in grados):
        motivos.append("muestra_por_grado_insuficiente")
    mejora = False
    for unidad in ("filas", "celdas"):
        for metrica in ("mrr", f"recall@{cfg.k}" if unidad == "filas" else "recall_contexto"):
            if resumen["agentic"][unidad][metrica] < resumen["baseline"][unidad][metrica] - 1e-12:
                motivos.append(f"regresion_global:{unidad}:{metrica}")
            mejora |= resumen["agentic"][unidad][metrica] > resumen["baseline"][unidad][metrica] + 1e-12
            for g in sorted(grados):
                if resumen["agentic"]["por_grado"][str(g)][unidad][metrica] < (
                    resumen["baseline"]["por_grado"][str(g)][unidad][metrica] - 1e-12
                ):
                    motivos.append(f"regresion_grado:{g}:{unidad}:{metrica}")
    if not mejora:
        motivos.append("sin_mejora_estricta")
    if any(f["errores"] for filas in ejecuciones.values() for f in filas):
        motivos.append("errores_de_ejecucion")
    if any(not resultado["rankings_estables"] for resultado in resumen.values()):
        motivos.append("rankings_inestables")
    p95_total = max(v["p95_ms"] for v in resumen["agentic"]["latencia_por_repeticion"].values())
    base = {(f["id"], f["repeticion"]): f for f in ejecuciones["baseline"]}
    incrementos = {r: [] for r in range(cfg.repeticiones)}
    for fila in ejecuciones["agentic"]:
        incrementos[fila["repeticion"]].append(max(0.0, fila["latencia_ms"] - base[
            fila["id"], fila["repeticion"]
        ]["latencia_ms"]))
    p95_incremental = max(_tiempos(v)["p95_ms"] for v in incrementos.values())
    if p95_total > cfg.max_p95_total_ms or p95_incremental > cfg.max_p95_incremental_ms:
        motivos.append("presupuesto_latencia_excedido")
    consumos = [f["consumo"] for filas in ejecuciones.values() for f in filas]
    reserva = None
    if any(c is None for c in consumos):
        motivos.append("consumo_no_medido")
    else:
        reserva = max(statistics.mean(f["consumo"]["reserva_usd"] for f in ejecuciones["agentic"]
                                     if f["repeticion"] == r) for r in range(cfg.repeticiones))
        if reserva > cfg.max_reserva_usd_por_consulta:
            motivos.append("presupuesto_coste_excedido")
    return {"seleccionar_candidato": not motivos, "default": "baseline", "motivos": motivos,
            "p95_total_peor_repeticion_ms": p95_total, "p95_incremental_peor_repeticion_ms": p95_incremental,
            "reserva_media_peor_repeticion_usd": reserva}
