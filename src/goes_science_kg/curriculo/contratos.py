"""Contratos del currículo versionado, independientes del grafo y sus decisiones."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Literal, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator

ValorCelda: TypeAlias = str | int | float | bool | datetime | date | time | timedelta | None
NombreFase: TypeAlias = Literal["aproximar", "explorar", "explicar", "indagar", "reforzar"]
FASES: tuple[NombreFase, ...] = ("aproximar", "explorar", "explicar", "indagar", "reforzar")


class ContratoCurricular(BaseModel):
    """Rechaza atributos desconocidos; la ingesta no modifica contratos emitidos."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class FuenteCurricular(ContratoCurricular):
    """Identidad del archivo exacto y su procedencia, sin otorgar permisos de lectura."""

    id: str
    version: str
    archivo: str
    archivo_local: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(gt=0)
    procedencia: dict[str, Any]


class ColumnaCurricular(ContratoCurricular):
    """Una columna física: encabezados completos y rol lógico opcional."""

    columna: str
    indice: int = Field(ge=1)
    encabezados: tuple[ValorCelda, ...]
    campo: str | None = None


class CeldaCurricular(ContratoCurricular):
    """Valor original y valor de ancla combinada; nunca arrastra blancos ordinarios."""

    coordenada: str
    fila: int = Field(ge=1)
    columna: str
    campo: str | None = None
    valor_original: ValorCelda = None
    valor: ValorCelda = None
    origen_combinado: str | None = None
    tipo_excel: str
    comentario: str | None = None
    hipervinculo: str | None = None


class RegistroHoja(ContratoCurricular):
    """Fila física no vacía, incluso si no representa un tema curricular."""

    fila: int = Field(ge=1)
    celdas: tuple[CeldaCurricular, ...]


class FaseCurricular(ContratoCurricular):
    """Anotación local del insumo: sus códigos no constituyen una taxonomía OECD."""

    presente_en_hoja: bool
    texto: str = ""
    codigos_locales: tuple[str, ...] = ()
    autoridad_codigos: Literal["insumo_local"] = "insumo_local"
    coordenadas: tuple[str, ...] = ()


class FilaCurricular(ContratoCurricular):
    """Tema identificado por versión, archivo, hoja, fila física y contenido."""

    id: str
    fuente_id: str
    version: str
    hoja: str
    fila: int = Field(ge=1)
    grado: int = Field(ge=1, le=12)
    asignatura_malla: str
    unidad: str
    contenido: str = ""
    subcontenido: str = ""
    procedimental: str = Field(min_length=1)
    indicador_avanzado: str = ""
    indicadores_logro: str = ""
    evidencia_aprendizaje: str = ""
    fases: dict[NombreFase, FaseCurricular]
    eje_integrador: str = ""
    numero_tema: str = ""
    numero_clase: str = ""
    actitudinal: str = ""
    competencia_pisa: str = ""
    conocimiento_pisa: str = ""
    contexto_pisa: str = ""
    habilidad_timss: str = ""
    habilidad_siglo_xxi: str = ""
    competencia_digital: str = ""
    actividad_digital: str = ""
    habilidad_transversal: str = ""
    competencia_men: str = ""
    dominio_clave: str = ""
    notacion: str = ""
    notas: str = ""
    origen_contenido: str = ""
    celdas: tuple[CeldaCurricular, ...]

    @model_validator(mode="after")
    def cinco_fases_explicitas(self) -> FilaCurricular:
        """Una ausencia debe declararse, nunca desaparecer del contrato."""
        if set(self.fases) != set(FASES):
            raise ValueError("Cada fila debe declarar exactamente las cinco fases, incluso las ausentes.")
        return self


class HojaCurricular(ContratoCurricular):
    """Inventario exhaustivo de hojas y sus registros originales, no inferencias."""

    fuente_id: str
    nombre: str
    tratamiento: Literal["curricular", "auxiliar", "excluida"]
    motivo: str
    grado: int | None = None
    asignatura_malla: str | None = None
    unidad: str | None = None
    filas_encabezado: tuple[int, ...] = ()
    columnas: tuple[ColumnaCurricular, ...] = ()
    combinaciones: tuple[str, ...] = ()
    registros: tuple[RegistroHoja, ...] = ()
    filas_curriculares: tuple[str, ...] = ()
    avisos: tuple[str, ...] = ()


class AgrupacionCurricular(ContratoCurricular):
    """Agrupación por asignatura declarada en la malla, sin clasificación heredada."""

    grado: int
    asignatura_malla: str
    unidad: str
    filas: tuple[str, ...]


class Curriculo(ContratoCurricular):
    """Resultado trazable de ingesta; no activa una versión ni aprueba su contenido."""

    version: str
    estado: Literal["ingerido_verificado"] = "ingerido_verificado"
    huella: str = Field(pattern=r"^[a-f0-9]{64}$")
    fuentes: tuple[FuenteCurricular, ...]
    filas: tuple[FilaCurricular, ...]
    hojas: tuple[HojaCurricular, ...]
    agrupaciones: tuple[AgrupacionCurricular, ...]
    avisos: tuple[str, ...] = ()
