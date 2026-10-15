"""Contrato ejecutable de GOES Science Content. Los estados originales no son permisos de publicación."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from goes_science_kg.modelos import Arista, Nodo

Texto = Annotated[str, StringConstraints(min_length=1)]
SHA = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]
SemVer = Annotated[str, StringConstraints(pattern=r"^\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?$")]


class Registro(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Ubicacion(Registro):
    archivo: Texto
    hoja: Texto
    fila: int = Field(ge=3)
    fila_fin: int = Field(ge=3)
    sha256: SHA

    @model_validator(mode="after")
    def rango(self):
        if self.fila_fin < self.fila:
            raise ValueError("fila_fin anterior a fila")
        return self


class Identidad(Registro):
    id_analisis: Texto
    tema_id: Texto
    fuente: Ubicacion
    sha256_columnas: SHA


class Tema(Registro):
    id: Texto
    version_malla: Literal["V3"] = "V3"
    aliases: list[Texto] = Field(min_length=1)
    grado: int = Field(ge=2, le=11)
    asignatura: str | None
    asignatura_malla: Texto
    en_alcance_ciencias: bool
    orden: int = Field(ge=1)
    fuente: Ubicacion
    # Columnas de la V3, normalizadas solo en espacios y con los bloques combinados conservados.
    columnas: dict[str, str]
    extraccion_grafo: dict[str, Any]
    diferencias_extraccion: list[str]


class Relacion(Arista):
    id: str


class Analisis(Registro):
    id: Texto
    tema_id: Texto
    tipo: Literal["TIMSS", "PISA", "ACARA"]
    marco: Texto
    procedencia: Literal["analisis_nuevas_mallas"] = "analisis_nuevas_mallas"
    resultado: dict[str, Any]


class Calidad(Registro):
    estado_original: str
    estado_panel: str | None
    solidez: str | None
    revisado_por: str | None
    estado_datos: Literal["pendiente", "no_evaluado", "verificado", "no_requiere"]
    datos_por_localizar: list[dict[str, Any]] = Field(default_factory=list)


class Usos(Registro):
    consulta: Literal[True] = True
    autoria: bool
    # Esta entrega inicial nunca habilita aula; requiere el hito de verificación docente de la spec 16.
    aula: Literal[False] = False
    motivos_autoria: list[str]
    pendientes_aula: list[str]


class Componente(Registro):
    id: Texto
    tipo: Literal["actividad", "experimento", "dificultad", "microtema", "refuerzo"]
    contenido: dict[str, Any]
    nodos_referidos: list[Texto]
    componentes_requeridos: list[Texto]
    calidad: Calidad
    usos: Usos


class Referencia(Registro):
    id: Texto
    conceptos: list[Texto]
    dato: Texto
    valor: Any
    unidad: str
    condiciones: Texto
    documento: Texto
    pagina: int | None = Field(default=None, ge=1)
    localizador: str | None = None
    sha256: SHA

    @model_validator(mode="after")
    def localizada(self):
        if not self.pagina and not self.localizador:
            raise ValueError("referencia sin página ni localizador")
        return self


class Paquete(Registro):
    id: Texto
    tema_id: Texto
    componentes: dict[str, list[Texto]]
    conceptos: list[Texto]
    bases: list[dict[str, Any]]
    fuentes: dict[str, Any]
    datos_referencia: dict[str, Any]
    completitud_origen: dict[str, str]
    # Un reemplazo elegido por una persona no se convierte en alias de identidad.
    reemplazo_elegido: dict[str, Any] | None = None


class FichaArchivo(Registro):
    sha256: SHA
    bytes: int = Field(ge=0)
    registros: int | None = Field(default=None, ge=0)


class Manifiesto(Registro):
    formato: Literal["GOES Science Content"] = "GOES Science Content"
    version_contrato: Literal["1.0.0"] = "1.0.0"
    version_contenido: SemVer
    fecha_corte: Annotated[str, StringConstraints(pattern=r"^\d{4}-\d{2}-\d{2}$")]
    malla: Literal["V3"] = "V3"
    perfiles: list[Literal["consulta", "autoria"]]
    commit_base: Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{40}$")]
    insumos: dict[str, SHA]
    archivos: dict[str, FichaArchivo]
    metricas: dict[str, int]
    advertencias: list[str]
    id_entrega: SHA


MODELOS = {"temas": Tema, "puente": Identidad, "nodos": Nodo, "relaciones": Relacion,
           "analisis": Analisis, "componentes": Componente, "paquetes": Paquete, "referencias": Referencia}
ARCHIVOS = {f"{n}.jsonl" for n in MODELOS} | {"catalogos.json", "esquemas.json", "LEEME.md"}


class Manifiesto11(Manifiesto):
    version_contrato: Literal['1.1.0'] = '1.1.0'


def clase_manifiesto(version: str):
    if version == '1.0.0':
        return Manifiesto
    if version == '1.1.0':
        return Manifiesto11
    raise ValueError('versión de contrato no implementada')


def modelos_para(version: str) -> dict:
    clase_manifiesto(version)
    if version == '1.0.0':
        return MODELOS
    from goes_science_kg.secuencias_ia import Secuencia

    return {**MODELOS, 'secuencias': Secuencia}


def archivos_para(version: str) -> set[str]:
    return {f'{n}.jsonl' for n in modelos_para(version)} | {'catalogos.json', 'esquemas.json', 'LEEME.md'}


def esquemas(version: str = '1.0.0') -> dict:
    return {**{n: m.model_json_schema() for n, m in modelos_para(version).items()},
            'manifiesto': clase_manifiesto(version).model_json_schema()}
