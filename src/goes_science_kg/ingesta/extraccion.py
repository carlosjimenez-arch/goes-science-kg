"""Vistas de texto por regiones PDF explícitas, versionadas y ligadas a bytes verificados.

Se conserva la extracción original. Un perfil es configuración de confianza auditada, no una
instrucción elegida por un modelo. Cambiar regiones, orden, biblioteca o código cambia su identidad.
"""

from __future__ import annotations

import hashlib
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.motor.contratos import Evidencia, huella

Coordenada = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class RegionPDF(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^LOCAL:[a-z0-9_]+$")
    bbox: tuple[Coordenada, Coordenada, Coordenada, Coordenada]

    @field_validator("bbox", mode="before")
    @classmethod
    def _sin_booleanos(cls, valores):
        if any(isinstance(v, bool) for v in valores):
            raise ValueError("Las coordenadas no pueden ser booleanos")
        return valores

    @model_validator(mode="after")
    def _superficie_positiva(self):
        x0, top, x1, bottom = self.bbox
        if x0 >= x1 or top >= bottom:
            raise ValueError("La región requiere superficie positiva")
        return self


class PerfilPaginaPDF(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^LOCAL:[a-z0-9_]+$")
    fuente: str = Field(pattern=r"^[a-z0-9_]+$")
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pagina_pdf: int = Field(strict=True, ge=1, le=1000)
    extractor: Literal["pdfplumber"]
    version: Literal["1"]
    regiones: tuple[RegionPDF, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def _regiones_distintas(self):
        if len({r.id for r in self.regiones}) != len(self.regiones):
            raise ValueError("El perfil repite una identidad de región")
        for i, a in enumerate(self.regiones):
            for b in self.regiones[i + 1:]:
                if min(a.bbox[2], b.bbox[2]) > max(a.bbox[0], b.bbox[0]) and (
                    min(a.bbox[3], b.bbox[3]) > max(a.bbox[1], b.bbox[1])
                ):
                    raise ValueError("Las regiones no pueden duplicar superficie de la misma página")
        return self


class CatalogoPerfilesPDF(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    perfiles: tuple[PerfilPaginaPDF, ...] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def _identidades_unicas(self):
        if len({p.id for p in self.perfiles}) != len(self.perfiles) or len({
            (p.fuente, p.pagina_pdf) for p in self.perfiles
        }) != len(self.perfiles):
            raise ValueError("Cada página admite un perfil inequívoco en este catálogo")
        return self


def cargar_perfiles(archivo: Path) -> CatalogoPerfilesPDF:
    return CatalogoPerfilesPDF.model_validate(yaml.safe_load(archivo.read_text(encoding="utf-8")))


class PaginasConPerfil:
    """Puerto de páginas primarias con perfiles optativos; el raw permanece accesible en repositorio."""

    def __init__(self, repositorio: RepositorioReferencias, perfiles: CatalogoPerfilesPDF):
        self.repositorio = repositorio
        self.perfiles = CatalogoPerfilesPDF.model_validate(perfiles.model_dump(mode="json"))
        self._por_pagina = {(p.fuente, p.pagina_pdf): p for p in self.perfiles.perfiles}
        self._cache: dict[tuple, Evidencia] = {}
        self._lock = RLock()
        self._verificar_ediciones()

    def _verificar_ediciones(self):
        registros = self.manifiesto().referencias
        for p in self.perfiles.perfiles:
            r = registros.get(p.fuente)
            if r is None or r.sha256 != p.sha256 or p.pagina_pdf > r.paginas:
                raise ValueError("El perfil no pertenece a la edición/página documental fijada")

    def manifiesto(self):
        return self.repositorio.manifiesto()

    @property
    def huella_extraccion(self) -> str:
        return huella({
            "perfiles": self.perfiles.model_dump(mode="json"),
            "biblioteca": f"pdfplumber/{version('pdfplumber')}",
            "opciones": {"layout": True},
            "codigo": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        })

    def pagina(self, identificador: str, pagina: int) -> Evidencia:
        if isinstance(pagina, bool) or not isinstance(pagina, int) or not 1 <= pagina <= 1000:
            raise ValueError("La página PDF requiere un entero entre uno y mil")
        perfil = self._por_pagina.get((identificador, pagina))
        if perfil is None:
            return self.repositorio.pagina(identificador, pagina)
        self._verificar_ediciones()
        # La caché no evita comprobar los bytes: una sustitución se rechaza incluso después de leerlos.
        contenido = self.repositorio.leer_pdf_verificado(identificador)
        if hashlib.sha256(contenido).hexdigest() != perfil.sha256:
            raise ValueError("El PDF no coincide con el perfil")
        identidad = self.huella_extraccion
        clave = (identificador, pagina, perfil.sha256, identidad)
        with self._lock:
            if clave not in self._cache:
                import pdfplumber

                partes = []
                with pdfplumber.open(BytesIO(contenido), pages=[pagina]) as pdf:
                    hoja = pdf.pages[0]
                    if hoja.page_number != pagina:
                        raise ValueError("El extractor devolvió otra página")
                    for region in perfil.regiones:
                        if region.bbox[2] > hoja.width or region.bbox[3] > hoja.height:
                            raise ValueError("La región excede las dimensiones de la página PDF")
                        texto = hoja.crop(region.bbox, strict=True).extract_text(layout=True) or ""
                        if not texto.strip():
                            raise ValueError("Una región declarada no contiene texto extraíble")
                        partes.append(texto.strip())
                texto = "\n\n".join(partes)
                self._cache[clave] = Evidencia.crear(
                    f"REF:{identificador}:P{pagina:04d}:PERFIL:{identidad[:16]}", texto,
                    {"documento": identificador, "pagina": pagina, "tipo": "documental",
                     "sha256": perfil.sha256, "verificacion": "contenido_fuente",
                     "extractor": f"pdfplumber/{version('pdfplumber')}", "perfil_id": perfil.id,
                     "perfil_huella": identidad, "regiones": [r.model_dump(mode="json") for r in perfil.regiones],
                     "alcance": "Sólo las regiones declaradas, en su orden; no es la página completa ni OCR"},
                    "referencia",
                )
            return self._cache[clave].model_copy(deep=True)
