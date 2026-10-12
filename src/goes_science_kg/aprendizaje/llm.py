"""Modelos de lenguaje del tutor y del evaluador (spec 13, «Funciones agénticas»).

El tutor y el evaluador no dependen de un proveedor: reciben un objeto con `generar(sistema, prompt, esquema)` que
devuelve un dict con el esquema pedido.
- `ModeloVertex`: Gemini en Vertex AI (proyecto GOES, credenciales por defecto). Sin caché en disco: los prompts llevan
  respuestas de estudiantes. Cada llamada se paga; la CLI solo lo usa con `--confirmar` (el hook pide aprobación).
- `ModeloGuion`: respuestas preparadas y deterministas, para pruebas, recorridos y para correr sin gasto.
Ningún prompt lleva el nombre ni el identificador del estudiante: solo su grado, su evidencia y su respuesta.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from goes_science_kg.config import cargar


def config() -> dict:
    return cargar("aprendizaje")["llm"]


@dataclass
class Llamada:
    """Registro de una llamada (para auditar qué se envió y qué volvió)."""

    rol: str
    modelo: str
    prompt: str
    respuesta: dict


@dataclass
class ModeloGuion:
    """Modelo simulado: `responder(sistema, prompt, esquema)` devuelve la salida. Registra cada llamada."""

    responder: Callable[[str, str, dict], dict]
    nombre: str = "guion"
    llamadas: list[Llamada] = field(default_factory=list)

    def generar(self, sistema: str, prompt: str, esquema: dict, rol: str = "") -> dict:
        r = self.responder(sistema, prompt, esquema)
        self.llamadas.append(Llamada(rol, self.nombre, prompt, r))
        return r


@dataclass
class ModeloVertex:
    """Gemini en Vertex AI, sin caché (ver el docstring del módulo)."""

    nombre: str
    temperatura: float = 0.2
    llamadas: list[Llamada] = field(default_factory=list)

    def generar(self, sistema: str, prompt: str, esquema: dict, rol: str = "") -> dict:
        from goes_science_kg.internacional import vertex

        r = vertex.generar_json(prompt, modelo=self.nombre, sistema=sistema, esquema=esquema, cache=False,
                                temperatura=self.temperatura, max_tokens=4096, reintentos=3)
        self.llamadas.append(Llamada(rol, self.nombre, prompt, r))
        return r


def de_config(rol: str) -> ModeloVertex:
    """El modelo de Vertex configurado para el rol («tutor» o «evaluador») en config/aprendizaje.yaml."""
    c = config()[rol]
    return ModeloVertex(c["modelo"], c.get("temperatura", 0.2))
