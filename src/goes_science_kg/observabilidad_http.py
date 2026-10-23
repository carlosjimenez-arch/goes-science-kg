"""Correlate local HTTP operations without recording payloads or identifying query values."""

from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

LOGGER = logging.getLogger(__name__)


class ObservabilidadHTTP:
    """Assign request identities and record route templates, status, and elapsed time.

    Logging uses the application's existing handlers. No exporter, account identity,
    request body, query string, or raw path is required to observe an operation.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Pass through ASGI traffic and correlate handled HTTP responses locally."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = uuid4().hex
        inicio = perf_counter()
        estado = 500

        async def enviar(mensaje: Message) -> None:
            nonlocal estado
            if mensaje["type"] == "http.response.start":
                estado = mensaje["status"]
                cabeceras = MutableHeaders(scope=mensaje)
                cabeceras["X-Request-ID"] = request_id
                cabeceras["Server-Timing"] = f"app;dur={(perf_counter() - inicio) * 1000:.3f}"
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        finally:
            ruta = getattr(scope.get("route"), "path", None) or "ruta_no_resuelta"
            LOGGER.info(
                "GOEs HTTP request completed",
                extra={
                    "request_id": request_id,
                    "http_method": scope["method"],
                    "http_route": ruta,
                    "http_status": estado,
                    "duration_ms": round((perf_counter() - inicio) * 1000, 3),
                },
            )
