"""Contrato del grafo: tipos de nodo, tipos de arista y evidencia.

Es la versión ejecutable de specs/02_modelo_del_grafo.md. Si cambia una, cambia la otra.

Invariantes (las revisa grafo.validar):
- Todo nodo que sale de un documento trae `fuente` (documento + página, u hoja + fila en las mallas).
- Toda arista inferida por IA trae confianza, justificación (≤ 15 palabras) y versión.
- Los ids son estables y no dependen del orden de lectura.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TipoNodo(StrEnum):
    ASIGNATURA = "Asignatura"        # ASIG:biologia
    GRADO = "Grado"                  # GRADO:07 (grados de El Salvador)
    MARCO = "Marco"                  # MARCO:T8_27
    OBJETIVO_MARCO = "ObjetivoMarco"  # OBJ:T8_27-B1.2 · OBJ:PISA-V3 · OBJ:TA-M1.1
    PAIS = "Pais"                    # PAIS:UY
    OBJETIVO_PAIS = "ObjetivoPais"   # OP:UY-BIO-G3-01
    TEMA = "Tema"                    # TEMA:G07-U2-2.3 (tema procedimental de la malla SV)
    DOCUMENTO = "Documento"          # DOC:timss27
    # Fase 3 en adelante (specs/08): conceptos, prácticas y propuesta.
    CONCEPTO = "Concepto"            # CON:fotosintesis
    PRACTICA = "Practica"            # PRAC:controlar-variables
    PROPUESTA = "PropuestaTema"      # PROP:biologia-G05-001


class TipoArista(StrEnum):
    EN_GRADO = "EN_GRADO"                # Tema → Grado
    DE_ASIGNATURA = "DE_ASIGNATURA"      # Tema | ObjetivoMarco | ObjetivoPais → Asignatura
    EN_MARCO = "EN_MARCO"                # ObjetivoMarco → Marco
    DE_PAIS = "DE_PAIS"                  # ObjetivoPais → Pais
    FUENTE = "FUENTE"                    # cualquier nodo → Documento (con página)
    CUBRE = "CUBRE"                      # Tema → ObjetivoMarco (rol principal|secundario)
    ALINEA_CON = "ALINEA_CON"            # ObjetivoPais → ObjetivoMarco (rol principal|secundario)
    EQUIVALE_A = "EQUIVALE_A"            # ObjetivoMarco 2023 → ObjetivoMarco 2027
    # Fase 3 en adelante.
    TRABAJA = "TRABAJA"                  # Tema | ObjetivoPais | ObjetivoMarco → Concepto | Practica
    PRERREQUISITO_DE = "PRERREQUISITO_DE"  # Concepto → Concepto
    PROPONE = "PROPONE"                  # PropuestaTema → ObjetivoMarco | Concepto
    REEMPLAZA = "REEMPLAZA"              # PropuestaTema → Tema


# Aristas que siempre son inferencia (IA o regla) y por eso exigen trazabilidad completa.
ARISTAS_INFERIDAS = {
    TipoArista.CUBRE, TipoArista.ALINEA_CON, TipoArista.TRABAJA,
    TipoArista.PRERREQUISITO_DE, TipoArista.PROPONE, TipoArista.REEMPLAZA,
}


class Confianza(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Fuente(BaseModel):
    """De dónde sale un nodo: documento externo (id del manifiesto + página o localizador) o malla (hoja + fila)."""

    model_config = ConfigDict(extra="forbid")

    documento: str
    pagina: int | None = None
    localizador: str | None = None  # p. ej. código oficial cuando el documento no tiene páginas (HTML)
    hoja: str | None = None
    fila: int | None = None


class Nodo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    tipo: TipoNodo
    etiqueta: str
    asignatura: str | None = None
    grado: int | None = None
    fuente: Fuente | None = None
    props: dict[str, Any] = Field(default_factory=dict)


class Arista(BaseModel):
    model_config = ConfigDict(extra="forbid")

    origen: str
    destino: str
    tipo: TipoArista
    rol: str | None = None               # principal | secundario
    confianza: Confianza | None = None
    justificacion: str | None = None
    version: str | None = None           # versión de la clasificación/regla que la produjo
    metodo: str | None = None            # ia | regla | malla | catalogo
    props: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _trazable(self) -> Arista:
        if self.tipo in ARISTAS_INFERIDAS and self.metodo == "ia":
            faltan = [c for c in ("confianza", "justificacion", "version") if getattr(self, c) in (None, "")]
            if faltan:
                raise ValueError(f"Arista {self.tipo} {self.origen}→{self.destino} sin {faltan}")
        return self

    @property
    def clave(self) -> tuple[str, str, str, str | None]:
        return (self.origen, self.destino, self.tipo, self.rol)
