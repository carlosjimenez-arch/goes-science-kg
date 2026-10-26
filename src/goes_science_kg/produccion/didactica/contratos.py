"""Contratos de diseño didáctico: origen documental separado de observaciones y revisiones."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContratoDidactico(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Localizador(ContratoDidactico):
    fuente_id: str
    archivo: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    hoja: str
    celdas: tuple[str, ...] = Field(min_length=1)


class DefinicionLocal(ContratoDidactico):
    codigo: str = Field(pattern=r"^[EDI][1-9]$")
    macro_id: Literal["explicacion_modelizacion", "indagacion_datos", "informacion_argumentacion_decisiones"]
    nombre: str
    contextualizacion_original: str
    competencia_declarada: str
    origen: Localizador
    autoridad: Literal["codigo_local_de_la_malla"] = "codigo_local_de_la_malla"


class TareaHabilidad(ContratoDidactico):
    id: str
    fase: str
    codigo: str
    actividad_literal: str
    origen: Localizador
    definicion: DefinicionLocal | None
    estado_alineacion: Literal["declarada_no_verificada"] = "declarada_no_verificada"


class CriterioHabilidad(ContratoDidactico):
    codigo: str
    tarea_ids: tuple[str, ...] = Field(min_length=1)
    evidencia_propuesta: str
    criterios_observables: tuple[str, ...] = Field(min_length=1)
    retroalimentacion: str
    error_a_indagar: str
    apoyo: str
    retirada_del_apoyo: str
    transferencia: str
    respuesta_observada: None = None
    logro_observado: None = None


class DisenoDidactico(ContratoDidactico):
    version: Literal["diseno-didactico-ciencias-1"] = "diseno-didactico-ciencias-1"
    fila_id: str
    catalogo_sha256: str
    objetivo_original: str
    indicador_original: str
    producto_original: str
    perfil_apoyo: dict
    transposicion: dict
    tareas: tuple[TareaHabilidad, ...]
    criterios: tuple[CriterioHabilidad, ...]
    macrohabilidades: tuple[str, ...]
    aplicacion: dict
    recuperacion: dict
    contexto_y_factibilidad: dict
    controles_cientificos: tuple[dict, ...]
    caso_resuelto: dict | None = None
    incidencias: tuple[dict, ...]
    estado_revision: Literal["propuesta_didactica_pendiente_revision"] = "propuesta_didactica_pendiente_revision"
    eficacia_observada: None = None
    alineacion_internacional_acreditada: Literal[False] = False

    @model_validator(mode="after")
    def identidad_y_cobertura(self):
        ids = {t.id for t in self.tareas}
        if len(ids) != len(self.tareas):
            raise ValueError("Las tareas didácticas tienen que ser únicas")
        conocidas = {t.id for t in self.tareas if t.definicion is not None}
        cubiertas = [id_ for c in self.criterios for id_ in c.tarea_ids]
        if len({c.codigo for c in self.criterios}) != len(self.criterios):
            raise ValueError("Se requiere un criterio integrado por código local")
        if set(cubiertas) != conocidas or len(cubiertas) != len(set(cubiertas)):
            raise ValueError("Cada tarea con definición requiere exactamente un criterio de habilidad")
        if any(t.codigo != t.definicion.codigo for t in self.tareas if t.definicion):
            raise ValueError("Una tarea está asociada a otra definición local")
        if set(self.macrohabilidades) != {t.definicion.macro_id for t in self.tareas if t.definicion}:
            raise ValueError("Las macrohabilidades deben proceder de las tareas documentadas")
        for criterio in self.criterios:
            if any(t.codigo != criterio.codigo for t in self.tareas if t.id in criterio.tarea_ids):
                raise ValueError("El criterio no corresponde a los códigos de sus tareas")
        return self
