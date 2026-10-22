"""Expectativas por banda nativa extraídas de celdas PDF verificadas, sin equivalencias SV."""

from __future__ import annotations

import re
from io import BytesIO
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from goes_science_kg.ingesta.extraccion import RegionPDF
from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.motor.contratos import Contrato, Evidencia, huella

BANDAS = ("K-2", "3-5", "6-8", "9-12")
LIMITE = (
    "Progresión documental en bandas NGSS; no equivale a grados SV, prerrequisito individual ni aprendizaje observado"
)


class ExpectativaNativa(Contrato):
    id: str = Field(pattern=r"^NATIVA:[A-Z0-9_:]+$")
    grupo: str
    titulo: str
    dimension: Literal["idea_disciplinar", "practica_cientifica", "concepto_transversal"]
    codigo_fuente: str
    banda: Literal["K-2", "3-5", "6-8", "9-12"]
    fuente: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    version_documental: str
    pagina_pdf: int = Field(strict=True, ge=1, le=1000)
    region: RegionPDF
    region_banda: RegionPDF
    ancla_inicial: str = Field(min_length=8)
    ancla_final: str = Field(min_length=6)
    alcance_region: str


class CatalogoProgresiones(Contrato):
    version: Literal["progresiones-documentales-1"] = "progresiones-documentales-1"
    expectativas: tuple[ExpectativaNativa, ...] = Field(min_length=4, max_length=1000)
    limite: Literal[LIMITE] = LIMITE

    @model_validator(mode="after")
    def _bandas_integra(self):
        if len({r.id for r in self.expectativas}) != len(self.expectativas):
            raise ValueError("Identidades nativas duplicadas")
        for grupo in {r.grupo for r in self.expectativas}:
            filas = [r for r in self.expectativas if r.grupo == grupo]
            if len(filas) != 4 or {r.banda for r in filas} != set(BANDAS):
                raise ValueError("Cada progresión requiere sus cuatro bandas, sin omisiones")
            if len({(r.dimension, r.codigo_fuente, r.fuente, r.sha256, r.version_documental) for r in filas}) != 1:
                raise ValueError("Una cadena no mezcla conceptos, dimensiones o ediciones")
        return self


class RepositorioProgresiones:
    def __init__(self, repositorio: RepositorioReferencias, catalogo: CatalogoProgresiones):
        self.repositorio, self.catalogo = repositorio, catalogo

    def evidencia(self, expectativa: ExpectativaNativa) -> Evidencia:
        import pdfplumber

        r = self.repositorio.manifiesto().referencias[expectativa.fuente]
        if (r.sha256, r.version_documental) != (expectativa.sha256, expectativa.version_documental):
            raise ValueError("La progresión no corresponde a la edición primaria fijada")
        contenido = self.repositorio.leer_pdf_verificado(expectativa.fuente)
        with pdfplumber.open(BytesIO(contenido), pages=[expectativa.pagina_pdf]) as pdf:
            p = pdf.pages[0]
            if p.page_number != expectativa.pagina_pdf:
                raise ValueError("El extractor leyó otra página")
            texto = p.crop(expectativa.region.bbox, strict=True).extract_text() or ""
            encabezado = p.crop(expectativa.region_banda.bbox, strict=True).extract_text() or ""
        encabezado_normal = encabezado.translate(str.maketrans({"–": "-", "‐": "-", "−": "-"}))
        if set(re.findall(r"K-2|3-5|6-8|9-12", encabezado_normal)) != {expectativa.banda}:
            raise ValueError("La banda declarada no corresponde al encabezado físico de su celda")
        normalizado = " ".join(texto.split())
        if not normalizado.startswith(expectativa.ancla_inicial) or not normalizado.endswith(expectativa.ancla_final):
            raise ValueError("La región perdió un extremo, mezcló columnas o cambió de texto")
        return Evidencia.crear(
            expectativa.id,
            texto,
            {
                "documento": expectativa.fuente,
                "pagina": expectativa.pagina_pdf,
                "sha256": r.sha256,
                "region": expectativa.region.model_dump(mode="json"),
                "region_banda": expectativa.region_banda.model_dump(mode="json"),
                "banda_nativa": expectativa.banda,
                "codigo_fuente": expectativa.codigo_fuente,
                "version_documental": r.version_documental,
                "verificacion": "contenido_fuente",
                "fuente_primaria": True,
                "tipo": "documental",
                "raiz_fuente": "referencias_progresiones_2026",
                "alcance": expectativa.alcance_region,
            },
            "referencia",
        )

    def archivo(self) -> dict:
        evidencias = {r.id: self.evidencia(r).model_dump(mode="json") for r in self.catalogo.expectativas}
        cadenas = []
        for grupo in sorted({r.grupo for r in self.catalogo.expectativas}):
            ids = [next(r.id for r in self.catalogo.expectativas if r.grupo == grupo and r.banda == b) for b in BANDAS]
            cadenas.extend(
                {"origen": a, "destino": b, "tipo": "SIGUE_EN_REFERENCIA", "limite": LIMITE}
                for a, b in zip(ids, ids[1:], strict=False)
            )
        datos = {"catalogo": self.catalogo.model_dump(mode="json"), "evidencias": evidencias, "cadenas": cadenas}
        return {"id": huella(datos), **datos}

    def validar(self, archivo: dict) -> None:
        if archivo != self.archivo():
            raise ValueError("El archivo de progresiones cambió o no conserva sus fuentes originales")


def cargar_progresiones(configuracion: Path, raiz: Path) -> RepositorioProgresiones:
    import yaml

    catalogo = CatalogoProgresiones.model_validate(yaml.safe_load(configuracion.read_text()))
    return RepositorioProgresiones(RepositorioReferencias(raiz), catalogo)
