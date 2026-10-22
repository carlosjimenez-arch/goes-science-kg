"""El motor depende de contratos, no de un SDK o proveedor específico."""

from typing import Protocol, TypeVar

from pydantic import BaseModel

from goes_science_kg.recuperacion import Resultado

T = TypeVar("T", bound=BaseModel)


class Recuperador(Protocol):
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
        """Recupera evidencia preservando la versión y el significado de las relaciones."""


class ModeloEstructurado(Protocol):
    def generar(self, *, rol: str, sistema: str, mensaje: str, esquema: type[T]) -> T:
        """Genera y valida un contrato, o lanza una excepción explícita."""

    def nombre_modelo(self, rol: str) -> str:
        """Identificador real del modelo utilizado, para trazabilidad."""
