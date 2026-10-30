"""Provide explicit language-model adapters for tutoring and assessment."""

# Historical implementation notes:
# El tutor y el evaluador no dependen de un proveedor: reciben un objeto con `generar(sistema, prompt, esquema)` que
# devuelve un dict con el esquema pedido.
# - `ModeloVertex`: Gemini en Vertex AI (proyecto GOES, credenciales por defecto). Sin caché en disco: los prompts
# llevan
#   respuestas de estudiantes. Cada llamada se paga; la CLI solo lo usa con `--confirmar` (el hook pide aprobación).
# - `ModeloGuion`: respuestas preparadas y deterministas, para pruebas, recorridos y para correr sin gasto.
# Ningún prompt lleva el nombre ni el identificador del estudiante: solo su grado, su evidencia y su respuesta.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from goes_science_kg.config import cargar


def config() -> dict:
    """Load the configured tutor and evaluator model settings."""

    return cargar("aprendizaje")["llm"]


@dataclass
class Llamada:
    """Record a model request and response for auditability."""

    rol: str
    modelo: str
    prompt: str
    respuesta: dict


@dataclass
class ModeloGuion:
    """Provide scripted model responses and record every simulated invocation."""

    responder: Callable[[str, str, dict], dict]
    nombre: str = "guion"
    llamadas: list[Llamada] = field(default_factory=list)

    def generar(self, sistema: str, prompt: str, esquema: dict, rol: str = "") -> dict:
        """Return the scripted response and retain its request for audit."""

        r = self.responder(sistema, prompt, esquema)
        self.llamadas.append(Llamada(rol, self.nombre, prompt, r))
        return r


@dataclass
class ModeloVertex:
    """Invoke Gemini through Vertex AI without caching learner exchanges."""

    nombre: str
    temperatura: float = 0.2
    llamadas: list[Llamada] = field(default_factory=list)

    def generar(self, sistema: str, prompt: str, esquema: dict, rol: str = "") -> dict:
        """Generate a structured response through the explicit Vertex adapter."""

        from goes_science_kg.internacional import vertex

        r = vertex.generar_json(
            prompt,
            modelo=self.nombre,
            sistema=sistema,
            esquema=esquema,
            cache=False,
            temperatura=self.temperatura,
            max_tokens=4096,
            reintentos=3,
        )
        self.llamadas.append(Llamada(rol, self.nombre, prompt, r))
        return r


def de_config(rol: str) -> ModeloVertex:
    """Create the model configured for the tutor or evaluator role."""
    c = config()[rol]
    return ModeloVertex(c["modelo"], c.get("temperatura", 0.2))
