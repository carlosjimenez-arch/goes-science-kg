"""Una solicitud SSE con ledger existente; no sigue continuaciones ni conserva pensamiento interno."""

from __future__ import annotations

import logging
import time
from functools import cached_property
from types import SimpleNamespace

from goes_science_kg.motor.vertex import Vertex

LOGGER = logging.getLogger(__name__)


class ModeloStreaming:
    def __init__(self, modelos):
        self.modelos = modelos

    def generate_content(self, **solicitud):
        config = solicitud["config"]
        if not config.automatic_function_calling.disable or config.max_output_tokens > 65536:
            raise ValueError("La revisión admite una solicitud SSE, sin funciones automáticas ni continuaciones")
        textos, uso = [], None
        ultimo_aviso, caracteres = time.monotonic(), 0
        # SDK 2.28: con AFC deshabilitado, este método llama una vez a request_streamed.
        for chunk in self.modelos.generate_content_stream(**solicitud):
            if chunk.usage_metadata is not None:
                uso = chunk.usage_metadata
            for candidato in chunk.candidates or []:
                if candidato.content is None:
                    continue
                for parte in candidato.content.parts or []:
                    if not parte.thought and parte.text:
                        textos.append(parte.text)
                        caracteres += len(parte.text)
            if time.monotonic() - ultimo_aviso >= 60:
                LOGGER.info(
                    "AMARILLO stream %s activo: %s caracteres visibles recibidos", solicitud.get("model"), caracteres
                )
                ultimo_aviso = time.monotonic()
        return SimpleNamespace(text="".join(textos), usage_metadata=uso)


class VertexStreaming(Vertex):
    @cached_property
    def cliente(self):
        # Reutiliza ADC, timeout, transporte sin reintentos y bloqueo de inicialización del adaptador base.
        real = Vertex.cliente.func(self)
        return SimpleNamespace(models=ModeloStreaming(real.models))
