"""Define engine ports independently of any provider SDK."""

from typing import Protocol, TypeVar

from pydantic import BaseModel

from goes_science_kg.recuperacion import Resultado

T = TypeVar("T", bound=BaseModel)


class Recuperador(Protocol):
    """Define the evidence-retrieval port required by the curriculum engine."""

    def buscar(
        self,
        consulta: str,
        *,
        version: str | None = None,
        grado: int | None = None,
        asignatura: str | None = None,
        k: int = 10,
        saltos_grafo: int = 1,
    ) -> list[Resultado]:
        """Retrieve evidence while preserving curriculum version and relationship semantics."""


class ModeloEstructurado(Protocol):
    """Define structured generation and model-identity ports independently of a provider SDK."""

    def generar(self, *, rol: str, sistema: str, mensaje: str, esquema: type[T]) -> T:
        """Generate and validate a structured contract or raise an explicit failure."""

    def nombre_modelo(self, rol: str) -> str:
        """Return the actual model identity used for traceability."""
