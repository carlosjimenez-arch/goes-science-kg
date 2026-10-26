"""Provide the historical Vertex AI client for international graph processing."""

# Historical implementation notes:
# - Credenciales: las de gcloud por defecto (ADC). El proyecto sale de `.env` (GOOGLE_CLOUD_PROJECT); el código
#   nunca lee ni imprime claves.
# - Caché en disco con clave sha256(modelo, sistema, prompt, esquema): reconstruir no vuelve a pagar y las
#   corridas se pueden reproducir. La caché no se versiona.
# - Respuestas JSON con esquema (`response_schema`), temperatura 0, reintentos con espera exponencial y un
#   tope obligatorio de llamadas por proceso (`VERTEX_MAX_CALLS` > 0).

from __future__ import annotations

import copy
import hashlib
import json
import os
import random
import threading
import time
from functools import cache
from typing import Any

from goes_science_kg.config import ruta

DIR_CACHE = "data/interim/internacional/cache"
REGION = os.environ.get("GSKG_VERTEX_REGION", "global")
MODELO_EXTRAER = os.environ.get("GSKG_MODELO_EXTRAER", "gemini-3.1-pro-preview")
MODELO_VALIDAR = os.environ.get("GSKG_MODELO_VALIDAR", "gemini-2.5-pro")
MODELO_ETIQUETAR = os.environ.get("GSKG_MODELO_ETIQUETAR", "gemini-2.5-pro")


class PresupuestoAgotadoError(RuntimeError):
    """Stop execution when the process-level paid-call limit is reached."""


TIMEOUT_MS = 180_000
CODIGOS_REINTENTABLES = {408, 429, 500, 502, 503, 504}


class _Contador:
    """Count paid model calls shared across process threads."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total = 0

    def reservar(self) -> None:
        """Reserve one paid call atomically under the process-level limit."""

        tope = int(os.environ.get("VERTEX_MAX_CALLS", "0"))
        if tope <= 0:
            raise PresupuestoAgotadoError("Declare VERTEX_MAX_CALLS (> 0) antes de pagar llamadas a Vertex")
        with self._lock:
            if self.total >= tope:
                raise PresupuestoAgotadoError(f"Se agotó el presupuesto de {tope} llamadas")
            self.total += 1


_contador = _Contador()


@cache
def _cliente():
    from dotenv import load_dotenv
    from google import genai

    load_dotenv(ruta(".env"))
    proyecto = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not proyecto:
        raise RuntimeError("Falta GOOGLE_CLOUD_PROJECT en .env")
    from google.genai import types

    # Sin reintentos del SDK: los reintentos se cuentan aquí contra el tope.
    opciones = types.HttpOptions(timeout=TIMEOUT_MS, retry_options=types.HttpRetryOptions(attempts=1))
    return genai.Client(vertexai=True, project=proyecto, location=REGION, http_options=opciones)


def _reintentable(error: Exception) -> bool:
    """Retry only quota, transient server, timeout, network, and truncated-JSON failures."""
    if isinstance(error, (json.JSONDecodeError, TimeoutError, ConnectionError)):
        return True
    return getattr(error, "code", None) in CODIGOS_REINTENTABLES


def _clave(modelo: str, sistema: str, prompt: str, esquema: dict | None, adjuntos: list) -> str:
    huellas = [[hashlib.sha256(datos).hexdigest(), mime] for datos, mime in adjuntos]
    bruto = json.dumps([modelo, sistema, prompt, esquema, huellas], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(bruto.encode()).hexdigest()


def llamadas() -> int:
    """Return the process's paid calls, excluding cache hits."""
    return _contador.total


CUENTA_ESPERADA = ".claude/harness.json"  # correo_git: la cuenta GOES con la que se trabaja


def cuenta_adc() -> str | None:
    """Identify the ADC account through Google's token-information endpoint."""

    # Implementation notes:
    # None si no se puede saber (sin credenciales o sin red). No imprime ni guarda el token.
    import urllib.parse
    import urllib.request

    try:
        import google.auth
        import google.auth.transport.requests

        credenciales, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        credenciales.refresh(google.auth.transport.requests.Request())
        url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"access_token": credenciales.token})
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read()).get("email")
    except Exception:  # noqa: BLE001 — cualquier fallo significa «no se pudo verificar»
        return None


def verificar_cuenta() -> None:
    """Verify the configured GOEs account before permitting paid model calls."""

    # Implementation notes:
    # con la instrucción para volver a autenticarse si no lo son o no se puede verificar.
    esperada = json.loads(ruta(CUENTA_ESPERADA).read_text(encoding="utf-8"))["correo_git"]
    actual = cuenta_adc()
    if actual != esperada:
        raise RuntimeError(
            f"Las credenciales de Vertex (ADC) son de {actual or 'una cuenta que no se pudo verificar'}, "
            f"no de {esperada}. "
            f"Vuelve a autenticarte con la cuenta GOES: gcloud auth application-default login (elige {esperada}) y "
            "gcloud auth application-default set-quota-project <proyecto de .env>."
        )


def en_cache(
    prompt: str,
    *,
    modelo: str,
    sistema: str = "",
    esquema: dict | None = None,
    adjuntos: list[tuple[bytes, str]] | None = None,
) -> bool:
    """Check whether a request already has a reusable cached response."""
    clave = _clave(modelo, sistema, prompt, esquema, adjuntos or [])
    return (ruta(DIR_CACHE) / clave[:2] / f"{clave}.json").exists()


def generar_json(
    prompt: str,
    *,
    modelo: str,
    sistema: str = "",
    esquema: dict | None = None,
    adjuntos: list[tuple[bytes, str]] | None = None,
    max_tokens: int = 32768,
    reintentos: int = 5,
    cache: bool = True,
    temperatura: float = 0,
) -> Any:
    """Generate structured JSON with optional explicitly supplied document attachments."""

    # Implementation notes:
    # Usa la caché si la llamada ya se hizo (la clave incluye el sha256 de cada adjunto). Con `cache=False` ni lee ni
    # escribe la caché: lo usa el tutor (spec 13), porque sus prompts llevan respuestas de estudiantes y la caché es una
    # carpeta del proyecto, no la del estudiante.
    adjuntos = adjuntos or []
    clave = _clave(modelo, sistema, prompt, esquema, adjuntos)
    archivo = ruta(DIR_CACHE) / clave[:2] / f"{clave}.json"
    if cache and archivo.exists():
        return json.loads(archivo.read_text(encoding="utf-8"))["respuesta"]

    from google.genai import types

    conf = types.GenerateContentConfig(
        temperature=temperatura,
        max_output_tokens=max_tokens,
        response_mime_type="application/json",
        # Copia: el SDK modifica el esquema que recibe, y eso cambiaría la clave de caché de las llamadas siguientes.
        response_schema=copy.deepcopy(esquema),
        system_instruction=sistema or None,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    ultimo: Exception | None = None
    for intento in range(reintentos):
        _contador.reservar()
        try:
            partes = [types.Part.from_bytes(data=d, mime_type=m) for d, m in adjuntos] + [prompt]
            r = _cliente().models.generate_content(model=modelo, contents=partes, config=conf)
            texto = r.text or ""
            respuesta = json.loads(texto)
            if cache:
                archivo.parent.mkdir(parents=True, exist_ok=True)
                archivo.write_text(
                    json.dumps({"modelo": modelo, "respuesta": respuesta}, ensure_ascii=False), encoding="utf-8"
                )
            return respuesta
        except PresupuestoAgotadoError:
            raise
        except Exception as e:
            if not _reintentable(e):  # 400, permisos o esquema: reintentar sólo gastaría llamadas
                raise
            ultimo = e
            time.sleep(min(60, 2**intento + random.random() * 2))
    raise RuntimeError(f"{modelo}: falló tras {reintentos} intentos: {ultimo}")
