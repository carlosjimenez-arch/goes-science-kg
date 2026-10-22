"""Anchor evaluation dimensions in documentary evidence without equating frameworks or grades."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goes_science_kg.ingesta.referencias import RepositorioReferencias


def _normalizar(texto: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", texto).split()).casefold()


class DimensionEvaluativa(BaseModel):
    """Represent a project-defined category for analyzing assessment tasks."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^LOCAL:[a-z0-9_]+$")
    fuente: str = Field(min_length=1)
    eje: Literal["contenido", "practica", "conocimiento", "demanda", "contexto"]
    etiqueta: str = Field(min_length=5)
    paginas_pdf: list[int] = Field(min_length=1, max_length=5)
    ancla: str = Field(min_length=12, max_length=280)
    alcance: str = Field(min_length=20)

    @field_validator("paginas_pdf")
    @classmethod
    def _paginas_positivas_unicas(cls, paginas: list[int]) -> list[int]:
        if any(pagina < 1 for pagina in paginas) or len(set(paginas)) != len(paginas):
            raise ValueError("Las páginas PDF deben ser positivas y únicas")
        return paginas

    @field_validator("ancla")
    @classmethod
    def _ancla_breve(cls, texto: str) -> str:
        if len(texto.split()) > 20 or not texto.strip():
            raise ValueError("El ancla debe ser un literal de hasta veinte palabras")
        return texto


class MetadatosDimensiones(BaseModel):
    """Describe dimension-catalog scope, provenance, limitations, and audit metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clasificacion: Literal["parafrasis_del_proyecto"]
    no_equivalencia: str = Field(min_length=20)
    corte: date
    alcance: str = Field(min_length=20)
    paginas: str = Field(min_length=20)
    procedencia: Literal["data/referencias_2026/manifest.json"]
    auditoria: str = Field(min_length=10)
    limites: list[str] = Field(min_length=1)


class CatalogoDimensiones(BaseModel):
    """Collect documentary assessment dimensions under a versioned schema."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    meta: MetadatosDimensiones
    dimensiones: list[DimensionEvaluativa] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def _ids_unicos(self) -> CatalogoDimensiones:
        if len({d.id for d in self.dimensiones}) != len(self.dimensiones):
            raise ValueError("El catálogo de dimensiones contiene IDs duplicados")
        return self


def validar_dimensiones(catalogo: CatalogoDimensiones, repositorio: RepositorioReferencias) -> dict:
    """Verify document bytes and locators without asserting task alignment."""
    # Se lee un único manifiesto para comprobar que todas las páginas usan la misma edición.
    manifiesto = repositorio.manifiesto()
    huella_manifest = hashlib.sha256(manifiesto.model_dump_json().encode("utf-8")).hexdigest()
    fuentes = repositorio.fuentes_verificadas()
    documentos = {
        (d.fuente["documento"], d.fuente["pagina"]): d
        for d in repositorio.documentos(sorted({d.fuente for d in catalogo.dimensiones}))
    }
    salida = []
    for dimension in catalogo.dimensiones:
        registro = manifiesto.referencias[dimension.fuente]
        anclas = []
        for pagina in dimension.paginas_pdf:
            documento = documentos.get((dimension.fuente, pagina))
            if documento is None:
                raise ValueError(f"{dimension.id}: página ausente o sin texto")
            evidencia = fuentes.hidratar(documento)
            if evidencia is None or evidencia.fuente["sha256"] != registro.sha256:
                raise ValueError(f"{dimension.id}: fuente no verificable")
            if _normalizar(dimension.ancla) in _normalizar(evidencia.texto):
                anclas.append({"pagina_pdf": pagina, "evidencia_id": evidencia.id, "huella_texto": evidencia.huella})
        if not anclas:
            raise ValueError(f"{dimension.id}: ancla ausente de las páginas indicadas")
        salida.append(
            {
                "dimension_id": dimension.id,
                "fuente": dimension.fuente,
                "sha256": registro.sha256,
                "paginas_con_ancla": anclas,
            }
        )
    actual = repositorio.manifiesto()
    if hashlib.sha256(actual.model_dump_json().encode("utf-8")).hexdigest() != huella_manifest:
        raise ValueError("El manifiesto cambió durante la validación; repita con una edición estable")
    identidad = json.dumps(catalogo.model_dump(mode="json"), sort_keys=True, ensure_ascii=False).encode("utf-8")
    return {
        "estado": "anclas_documentales_verificadas",
        "huella_catalogo": hashlib.sha256(identidad).hexdigest(),
        "huella_manifest": huella_manifest,
        "limite": "Verifica procedencia y literales; no cobertura curricular, equivalencia ni eficacia pedagógica",
        "dimensiones": salida,
    }
