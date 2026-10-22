"""Embeddings Vertex por ADC con caché incremental y presupuesto persistente.

No lee .env ni registra texto, credenciales o tokens de acceso. La reserva usa al menos
el límite de 2048 tokens aceptados por el modelo; el uso real se registra aparte.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

LOGGER = logging.getLogger(__name__)
TAREAS = frozenset({"RETRIEVAL_DOCUMENT", "RETRIEVAL_QUERY"})
PRECIO_USD_MILLON = 0.15
LIMITE_TOKENS_MODELO = 2048
URL_PRECIO = "https://cloud.google.com/vertex-ai/generative-ai/pricing"


class PresupuestoEmbeddingsAgotado(RuntimeError):
    """La siguiente petición excedería el máximo de llamadas o USD reservados."""


class VertexEmbeddings:
    """Un texto por llamada con task type real; no tiene fallback silencioso de modelo."""

    def __init__(
        self,
        *,
        proyecto: str,
        directorio_cache: str | Path,
        ledger: str | Path,
        modelo: str = "gemini-embedding-001",
        region: str = "us-central1",
        dimensiones: int = 768,
        max_requests: int = 3500,
        max_usd: float = 2.0,
        concurrencia: int = 3,
        timeout_ms: int = 30000,
        max_caracteres: int = 6000,
        cliente: Any = None,
    ):
        if not proyecto.strip() or modelo != "gemini-embedding-001":
            raise ValueError("Se requiere proyecto explícito y gemini-embedding-001, que soporta task_type")
        if dimensiones != 768 or not 1 <= concurrencia <= 3 or not 1 <= max_requests <= 3500:
            raise ValueError("Este experimento admite 768 dimensiones, concurrencia hasta 3 y hasta 3500 llamadas")
        if not 0 < max_usd <= 2 or not 1 <= timeout_ms <= 30000 or not 1 <= max_caracteres <= 6000:
            raise ValueError("Límites inválidos: máximo USD 2, timeout 30 segundos y 6000 caracteres")
        self.proyecto = proyecto
        self.modelo = modelo
        self.region = region
        self.dimensiones = dimensiones
        self.max_requests = max_requests
        self.max_usd = max_usd
        self.concurrencia = concurrencia
        self.timeout_ms = timeout_ms
        self.max_caracteres = max_caracteres
        self.directorio_cache = Path(directorio_cache)
        self.ledger = Path(ledger)
        self._lock = threading.Lock()
        self._abortar = threading.Event()
        self._cliente = cliente
        self._requests = 0
        self._cache_hits = 0
        self._tokens_reservados = 0
        self._tokens_reportados = 0
        self._completadas = 0
        self._errores = 0
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self._restaurar_ledger()

    def _restaurar_ledger(self) -> None:
        if not self.ledger.exists():
            return
        for linea in self.ledger.read_text(encoding="utf-8").splitlines():
            evento = json.loads(linea)
            if evento.get("proyecto") != self.proyecto or evento.get("modelo") != self.modelo:
                raise ValueError("El ledger pertenece a otro proyecto o modelo")
            tipo = evento["evento"]
            if tipo == "reserva":
                self._requests += 1
                self._tokens_reservados += evento["tokens_reservados"]
            elif tipo == "completada":
                self._completadas += 1
                self._tokens_reportados += evento["tokens_reportados"]
            elif tipo == "cache":
                self._cache_hits += 1
            elif tipo == "error":
                self._errores += 1

    def _evento(self, tipo: str, **campos) -> None:
        evento = {
            "fecha": datetime.now(UTC).isoformat(),
            "evento": tipo,
            "proyecto": self.proyecto,
            "modelo": self.modelo,
            **campos,
        }
        with self.ledger.open("a", encoding="utf-8") as salida:
            salida.write(json.dumps(evento, ensure_ascii=False, sort_keys=True) + "\n")

    def _identidad(self, texto: str, tarea: str) -> dict:
        return {
            "texto_sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
            "modelo": self.modelo,
            "tarea": tarea,
            "dimensiones": self.dimensiones,
            "region": self.region,
            "api_version": "v1",
            "formato_cache": 1,
        }

    def _reservar(self, clave: str, tokens: int) -> None:
        with self._lock:
            if self._abortar.is_set():
                raise RuntimeError("La corrida de embeddings se detuvo por un fallo anterior")
            coste = (self._tokens_reservados + tokens) * PRECIO_USD_MILLON / 1_000_000
            if self._requests >= self.max_requests or coste > self.max_usd:
                self._abortar.set()
                raise PresupuestoEmbeddingsAgotado("Se agotó el límite persistente de peticiones o USD")
            self._evento("reserva", clave=clave, tokens_reservados=tokens)
            self._requests += 1
            self._tokens_reservados += tokens

    def _obtener_cliente(self):
        with self._lock:
            if self._cliente is None:
                from google import genai
                from google.genai import types

                self._cliente = genai.Client(
                    vertexai=True,
                    project=self.proyecto,
                    location=self.region,
                    http_options=types.HttpOptions(
                        api_version="v1",
                        timeout=self.timeout_ms,
                        retry_options=types.HttpRetryOptions(attempts=1),
                    ),
                )
            return self._cliente

    def _leer_cache(self, archivo: Path, identidad: dict) -> np.ndarray:
        with np.load(archivo, allow_pickle=False) as datos:
            if json.loads(str(datos["metadata"].item())) != identidad:
                raise ValueError("La caché de embeddings no coincide con la solicitud")
            return self._validar_vector(datos["vector"])

    def _validar_vector(self, vector) -> np.ndarray:
        vector = np.asarray(vector, dtype=np.float32)
        if vector.shape != (self.dimensiones,) or not np.isfinite(vector).all():
            raise ValueError("Vector de embeddings incompleto, no finito o de dimensión incorrecta")
        if float(np.linalg.norm(vector.astype(np.float64))) == 0:
            raise ValueError("El proveedor devolvió un vector de norma cero")
        return vector

    def _escribir_cache(self, archivo: Path, identidad: dict, vector: np.ndarray) -> None:
        archivo.parent.mkdir(parents=True, exist_ok=True)
        temporal = None
        try:
            with tempfile.NamedTemporaryFile(dir=archivo.parent, prefix=".embedding-", delete=False) as salida:
                temporal = Path(salida.name)
                np.savez_compressed(salida, vector=vector, metadata=np.asarray(json.dumps(identidad, sort_keys=True)))
            os.replace(temporal, archivo)
        finally:
            if temporal is not None:
                temporal.unlink(missing_ok=True)

    def vectorizar_texto(self, texto: str, *, tarea: str) -> np.ndarray:
        """Recupera de caché o realiza exactamente una petición de texto; nunca trunca."""
        if tarea not in TAREAS or not texto.strip() or len(texto) > self.max_caracteres:
            raise ValueError("Texto vacío/demasiado largo o task_type no permitido")
        identidad = self._identidad(texto, tarea)
        clave = hashlib.sha256(json.dumps(identidad, sort_keys=True).encode("utf-8")).hexdigest()
        archivo = self.directorio_cache / clave[:2] / f"{clave}.npz"
        if archivo.exists():
            vector = self._leer_cache(archivo, identidad)
            with self._lock:
                self._cache_hits += 1
                self._evento("cache", clave=clave, tarea=tarea)
            return vector
        tokens_reservados = max(LIMITE_TOKENS_MODELO, len(texto.encode("utf-8")) + 256)
        self._reservar(clave, tokens_reservados)
        inicio = time.perf_counter()
        try:
            from google.genai import types

            respuesta = self._obtener_cliente().models.embed_content(
                model=self.modelo,
                contents=texto,
                config=types.EmbedContentConfig(
                    task_type=tarea,
                    output_dimensionality=self.dimensiones,
                    auto_truncate=False,
                ),
            )
            if not respuesta.embeddings or len(respuesta.embeddings) != 1:
                raise ValueError("El proveedor no devolvió exactamente un embedding por texto")
            embedding = respuesta.embeddings[0]
            stats = embedding.statistics
            if stats is None or stats.truncated:
                raise ValueError("El proveedor no confirmó un embedding sin truncamiento")
            tokens = int(stats.token_count or 0)
            if tokens < 1 or tokens > min(tokens_reservados, LIMITE_TOKENS_MODELO):
                raise ValueError("El conteo de tokens no confirma la reserva conservadora")
            vector = self._validar_vector(embedding.values)
            with self._lock:
                self._tokens_reportados += tokens
                self._completadas += 1
                self._evento(
                    "completada",
                    clave=clave,
                    tarea=tarea,
                    tokens_reportados=tokens,
                    latencia_ms=round((time.perf_counter() - inicio) * 1000, 3),
                )
            self._escribir_cache(archivo, identidad, vector)
            return vector
        except Exception as error:
            self._abortar.set()
            with self._lock:
                self._errores += 1
                self._evento("error", clave=clave, tarea=tarea, tipo_error=type(error).__name__)
            LOGGER.error("Falló embedding %s: %s", clave[:12], type(error).__name__)
            raise

    def vectorizar(self, textos: list[str], *, tarea: str) -> np.ndarray:
        """Resuelve duplicados antes de paralelizar y devuelve float32 en el orden original."""
        if not textos:
            return np.empty((0, self.dimensiones), dtype=np.float32)
        unicos = list(dict.fromkeys(textos))
        vectores = {}
        ejecutor = ThreadPoolExecutor(max_workers=self.concurrencia)
        futuros = {ejecutor.submit(self.vectorizar_texto, texto, tarea=tarea): texto for texto in unicos}
        try:
            for futuro in as_completed(futuros):
                vectores[futuros[futuro]] = futuro.result()
                n = len(vectores)
                if n % 100 == 0 or n == len(unicos):
                    LOGGER.info("Embeddings %s: %d/%d", tarea, n, len(unicos))
        except BaseException:
            self._abortar.set()
            ejecutor.shutdown(wait=True, cancel_futures=True)
            raise
        else:
            ejecutor.shutdown(wait=True)
        return np.asarray([vectores[texto] for texto in textos], dtype=np.float32)

    def resumen(self) -> dict:
        """Contabilidad persistente: reserva superior y coste estimado por tokens reportados."""
        with self._lock:
            return {
                "proyecto": self.proyecto,
                "modelo": self.modelo,
                "region": self.region,
                "dimensiones": self.dimensiones,
                "sdk_attempts": 1,
                "timeout_ms": self.timeout_ms,
                "concurrencia": self.concurrencia,
                "requests_reservadas": self._requests,
                "completadas": self._completadas,
                "errores": self._errores,
                "cache_hits": self._cache_hits,
                "tokens_reservados": self._tokens_reservados,
                "tokens_reportados": self._tokens_reportados,
                "usd_reservado": self._tokens_reservados * PRECIO_USD_MILLON / 1_000_000,
                "usd_estimado_tokens_reportados": self._tokens_reportados * PRECIO_USD_MILLON / 1_000_000,
                "precio_usd_millon": PRECIO_USD_MILLON,
                "fuente_precio": URL_PRECIO,
                "limite_requests": self.max_requests,
                "limite_usd": self.max_usd,
                "max_tokens_texto": LIMITE_TOKENS_MODELO,
                "max_caracteres_texto": self.max_caracteres,
                "ledger": str(self.ledger.resolve()),
                "nota": "Coste estimado de texto; la reserva conservadora no se libera ante fallos. No es factura.",
            }
