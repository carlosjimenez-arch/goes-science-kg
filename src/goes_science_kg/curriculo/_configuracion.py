"""Configuración explícita de archivos, hojas y campos, sin selección por nombres."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from goes_science_kg.curriculo.contratos import FASES, FilaCurricular

CAMPOS = set(FilaCurricular.model_fields) - {
    "id",
    "fuente_id",
    "version",
    "hoja",
    "fila",
    "grado",
    "asignatura_malla",
    "fases",
    "celdas",
}
CAMPOS.update(f"fase_{fase}" for fase in FASES)


class ConfigHoja(BaseModel):
    """Cada hoja requiere una decisión explícita, motivada y verificable."""

    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1)
    tratamiento: Literal["curricular", "auxiliar", "excluida"]
    motivo: str = Field(min_length=1)
    grado: int | None = Field(default=None, ge=1, le=12)
    asignatura_malla: str | None = None
    unidad: str | None = None
    filas_encabezado: tuple[int, ...] = ()
    campos_por_columna: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validar_esquema(self) -> ConfigHoja:
        """Un tema requiere contexto de grado y encabezados; los campos son conocidos."""
        if not self.motivo.strip():
            raise ValueError("El motivo no puede estar vacío.")
        if self.tratamiento == "curricular" and (
            self.grado is None or not self.asignatura_malla or not self.filas_encabezado
        ):
            raise ValueError(f"Hoja curricular sin grado, asignatura o encabezados: {self.nombre}")
        if any(fila < 1 for fila in self.filas_encabezado) or (
            list(self.filas_encabezado) != sorted(set(self.filas_encabezado))
        ):
            raise ValueError("Las filas de encabezado deben ser positivas, únicas y ordenadas.")
        for columna, campo in self.campos_por_columna.items():
            if not columna.isalpha() or not columna.isascii() or not columna.isupper() or campo not in CAMPOS:
                raise ValueError(f"Columna o campo desconocido: {columna}={campo}")
        return self


class ConfigFuente(BaseModel):
    """Archivo por nombre exacto; los permisos no se deducen de la procedencia."""

    model_config = ConfigDict(extra="forbid")
    archivo: str = Field(min_length=1)
    hojas: tuple[ConfigHoja, ...]

    @model_validator(mode="after")
    def validar_archivo(self) -> ConfigFuente:
        """No admite rutas ni hojas repetidas, aunque los encabezados coincidan."""
        if Path(self.archivo).name != self.archivo or "\\" in self.archivo or not self.archivo.endswith(".xlsx"):
            raise ValueError("Cada archivo debe ser un nombre .xlsx sin directorios.")
        nombres = [hoja.nombre for hoja in self.hojas]
        if len(set(nombres)) != len(nombres):
            raise ValueError(f"Hojas duplicadas en {self.archivo}.")
        return self


class ConfigCurriculo(BaseModel):
    """Manifiesto declarativo de la ingesta, independiente de la malla activa."""

    model_config = ConfigDict(extra="forbid")
    version: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
    raiz: str = ".."
    directorio: str
    procedencia: str
    alias_campos: dict[str, tuple[str, ...]]
    fuentes: tuple[ConfigFuente, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validar_fuentes(self) -> ConfigCurriculo:
        """La configuración no puede sobrescribir archivos o inventar roles de columnas."""
        archivos = [fuente.archivo for fuente in self.fuentes]
        if len(set(archivos)) != len(archivos):
            raise ValueError("Archivos duplicados en configuración.")
        if desconocidos := set(self.alias_campos) - CAMPOS:
            raise ValueError(f"Campos desconocidos: {sorted(desconocidos)}")
        return self
