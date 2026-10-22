"""Adaptador Vertex AI con ADC, esquema, timeout, reintentos selectivos y presupuesto durable."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from functools import cached_property
from threading import Lock
from typing import Literal, TypeVar

from pydantic import BaseModel, Field, ValidationError

from goes_science_kg.motor.contratos import Contrato
from goes_science_kg.motor.registro import Registro

LOGGER = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


def _tokens_salida(uso) -> int | None:
    """Ausencia de telemetría no significa cero tokens generados."""
    candidatos = getattr(uso, "candidates_token_count", None)
    if candidatos is None:
        return None
    return candidatos + (getattr(uso, "thoughts_token_count", None) or 0)


class Tarifa(Contrato):
    """Tarifas configurables, USD por millón; reserva conservadora, no importe facturado."""

    entrada: float = Field(gt=0)
    salida: float = Field(gt=0)


class ConfiguracionVertex(Contrato):
    proyecto: str = Field(min_length=5)
    region: str = "global"
    modelos: dict[str, str]
    tarifas: dict[str, Tarifa]
    max_llamadas: int = Field(default=24, ge=1, le=10000)
    max_usd: float = Field(default=3.0, gt=0)
    max_salida_tokens: int = Field(default=4096, ge=256, le=16384)
    timeout_segundos: int = Field(default=60, ge=5, le=180)
    reintentos: int = Field(default=1, ge=0, le=3)
    niveles_razonamiento: dict[str, Literal["LOW", "MEDIUM", "HIGH"]] = Field(default_factory=dict)


class Vertex:
    def __init__(self, configuracion: ConfiguracionVertex, registro: Registro, ejecucion_id: str):
        self.configuracion = configuracion
        self.registro = registro
        self.ejecucion_id = ejecucion_id
        self._cliente_lock = Lock()
        self._cliente_interno = None

    @cached_property
    def cliente(self):
        from google import genai
        from google.genai import types

        with self._cliente_lock:
            if self._cliente_interno is None:
                cfg = self.configuracion
                self._cliente_interno = genai.Client(
                    vertexai=True,
                    project=cfg.proyecto,
                    location=cfg.region,
                    http_options=types.HttpOptions(
                        timeout=cfg.timeout_segundos * 1000, retry_options=types.HttpRetryOptions(attempts=1)
                    ),
                )
            return self._cliente_interno

    def nombre_modelo(self, rol: str) -> str:
        return self.configuracion.modelos[rol]

    def generar(self, *, rol: str, sistema: str, mensaje: str, esquema: type[T]) -> T:
        from google.genai import types

        cfg = self.configuracion
        modelo = self.nombre_modelo(rol)
        tarifa = cfg.tarifas[modelo]
        contenido_clave = [
            cfg.proyecto,
            cfg.region,
            modelo,
            sistema,
            mensaje,
            esquema.model_json_schema(),
            cfg.max_salida_tokens,
        ]
        nivel = cfg.niveles_razonamiento.get(rol)
        if nivel is not None:
            contenido_clave.append({"thinking_level": nivel})
        clave = hashlib.sha256(json.dumps(contenido_clave, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        if respuesta := self.registro.cache(clave):
            LOGGER.info("VERDE %s: respuesta recuperada de caché", rol)
            return esquema.model_validate(respuesta)
        # Cada byte UTF-8 es una cota conservadora de tokens de entrada. Salida incluye razonamiento.
        entrada_maxima = len((sistema + mensaje + json.dumps(esquema.model_json_schema())).encode())
        reserva = (entrada_maxima * tarifa.entrada + cfg.max_salida_tokens * tarifa.salida) / 1_000_000
        for intento in range(cfg.reintentos + 1):
            id_llamada = self.registro.reservar(
                ejecucion=self.ejecucion_id,
                clave=clave,
                modelo=modelo,
                rol=rol,
                reserva_usd=reserva,
                max_llamadas=cfg.max_llamadas,
                max_usd=cfg.max_usd,
            )
            inicio = time.perf_counter()
            uso = None
            LOGGER.info("%s: llamando %s (intento %d)", rol, modelo, intento + 1)
            try:
                r = self.cliente.models.generate_content(
                    model=modelo,
                    contents=mensaje,
                    config=types.GenerateContentConfig(
                        system_instruction=sistema,
                        response_mime_type="application/json",
                        response_schema=esquema,
                        max_output_tokens=cfg.max_salida_tokens,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                        thinking_config=types.ThinkingConfig(thinking_level=nivel) if nivel else None,
                    ),
                )
                uso = r.usage_metadata
                validada = esquema.model_validate_json(r.text or "")
                self.registro.terminar(
                    id_llamada,
                    estado="completada",
                    latencia_ms=(time.perf_counter() - inicio) * 1000,
                    entrada_tokens=getattr(uso, "prompt_token_count", None),
                    salida_tokens=_tokens_salida(uso),
                )
                self.registro.guardar_cache(clave, validada.model_dump(mode="json"))
                LOGGER.info("VERDE %s: contrato validado", rol)
                return validada
            except Exception as error:
                self.registro.terminar(
                    id_llamada,
                    estado="fallida",
                    latencia_ms=(time.perf_counter() - inicio) * 1000,
                    entrada_tokens=getattr(uso, "prompt_token_count", None),
                    salida_tokens=_tokens_salida(uso),
                )
                if isinstance(error, ValidationError):
                    detalle = [(e["loc"], e["type"]) for e in error.errors(include_input=False)]
                    LOGGER.error("ROJO contrato %s: %s", rol, detalle[:5])
                codigo = getattr(error, "code", None)
                if codigo not in {408, 429, 500, 502, 503, 504} or intento >= cfg.reintentos:
                    LOGGER.error("ROJO %s: %s (código %s)", rol, type(error).__name__, codigo)
                    raise
                LOGGER.warning("AMARILLO %s: fallo transitorio %s", rol, codigo)
                time.sleep(min(8, 2**intento))
        raise RuntimeError("Se agotó el ciclo de llamadas")
