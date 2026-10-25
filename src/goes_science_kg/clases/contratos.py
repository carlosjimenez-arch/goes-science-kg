"""Contrato de clase: actividades ejecutables, evaluación con soluciones y tiempos explícitos."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, create_model, model_validator

from goes_science_kg.motor.contratos import Contrato

FASES = ("aproximar", "explorar", "explicar", "indagar", "reforzar")
ROLES = ("clases_ciencia", "clases_curriculo", "clases_psicopedagogia", "clases_adversarial")
CRITERIOS = {
    "clases_ciencia": ("ciencia_correcta", "afirmaciones_sustentadas", "soluciones_correctas"),
    "clases_curriculo": ("objetivo_conservado", "evaluacion_alineada", "guion_completo"),
    "clases_psicopedagogia": ("adecuacion_al_grado", "tiempos_realistas", "andamiaje_y_accesibilidad"),
    "clases_adversarial": ("seguridad", "sin_datos_ni_fuentes_inventadas", "recursos_factibles"),
}
MAX_BYTES_BORRADOR = 120000
MAX_CONTEXTO_BYTES = 96000
MAX_HALLAZGOS_BYTES = 48000


class Bloque(Contrato):
    fase: Literal["aproximar", "explorar", "explicar", "indagar", "reforzar"]
    minutos: int = Field(ge=1, le=60)
    docente: str = Field(min_length=30, max_length=1200)
    estudiantes: str = Field(min_length=30, max_length=1000)
    evidencia_observable: str = Field(min_length=20, max_length=600)


class Sesion(Contrato):
    numero: int = Field(ge=1, le=3)
    titulo: str = Field(min_length=5, max_length=150)
    bloques: tuple[Bloque, ...] = Field(min_length=2, max_length=8)

    @model_validator(mode="after")
    def _tiempo(self):
        if sum(b.minutos for b in self.bloques) != 60:
            raise ValueError("Cada sesión propuesta debe sumar exactamente 60 minutos")
        return self


class AfirmacionClase(Contrato):
    texto: str = Field(min_length=20, max_length=600)
    fuentes_ids: tuple[str, ...] = Field(min_length=1, max_length=4)


class CriterioRubrica(Contrato):
    criterio: str = Field(min_length=15, max_length=400)
    logrado: str = Field(min_length=15, max_length=400)
    en_proceso: str = Field(min_length=15, max_length=400)
    requiere_apoyo: str = Field(min_length=15, max_length=400)


class ComprobacionCalculo(Contrato):
    expresion: str = Field(min_length=1, max_length=160)
    resultado: float = Field(allow_inf_nan=False)
    tolerancia: float = Field(default=0, ge=0, le=0.01)
    tolerancia_relativa: float = Field(default=0.000001, ge=0, le=0.01)
    unidad: str = Field(min_length=1, max_length=50)


class TareaEstudiante(Contrato):
    enunciado: str = Field(min_length=30, max_length=1600, description="Tarea completa: 30–1600 caracteres.")
    respuesta_esperada: str = Field(min_length=20, max_length=2000, description="Solución docente: 20–2000 caracteres.")
    explicacion_solucion: str = Field(min_length=20, max_length=2000, description="Explicación: 20–2000 caracteres.")
    rubrica: tuple[CriterioRubrica, ...] = Field(min_length=2, max_length=4)
    calculos: tuple[ComprobacionCalculo, ...] = Field(max_length=6)
    datos_simulados: bool


class GuionClase(Contrato):
    fila_id: str = Field(min_length=1, max_length=200)
    titulo: str = Field(min_length=8, max_length=200)
    objetivo: str = Field(min_length=20, max_length=1800)
    conocimientos_a_activar: tuple[str, ...] = Field(min_length=1, max_length=5)
    explicacion_docente: tuple[AfirmacionClase, ...] = Field(min_length=2, max_length=6)
    sesiones: tuple[Sesion, ...] = Field(min_length=1, max_length=3)
    tareas: tuple[TareaEstudiante, ...] = Field(min_length=2, max_length=3)
    recursos: tuple[str, ...] = Field(min_length=2, max_length=12)
    alternativa_sin_recursos: str = Field(min_length=40, max_length=1000)
    apoyos: tuple[str, ...] = Field(min_length=2, max_length=5)
    dificultad_previsible: str = Field(min_length=20, max_length=500)
    retroalimentacion: str = Field(min_length=30, max_length=700)
    seguridad: str = Field(min_length=30, max_length=700)
    implementacion_condicionada: str = Field(min_length=30, max_length=700)

    @model_validator(mode="after")
    def _sesiones(self):
        if [s.numero for s in self.sesiones] != list(range(1, len(self.sesiones) + 1)):
            raise ValueError("Las sesiones deben numerarse consecutivamente")
        if set(FASES) - {b.fase for s in self.sesiones for b in s.bloques}:
            raise ValueError("El guion debe incluir las cinco fases a lo largo de sus sesiones")
        return self


class BorradorClases(Contrato):
    guiones: tuple[GuionClase, ...] = Field(min_length=1, max_length=4)

    @model_validator(mode="after")
    def _tamano(self):
        if len(self.model_dump_json().encode()) > MAX_BYTES_BORRADOR:
            raise ValueError("El lote supera el tamaño máximo de salida")
        if len({g.fila_id for g in self.guiones}) != len(self.guiones):
            raise ValueError("Los guiones no pueden repetir filas")
        return self


class JuicioFila(Contrato):
    fila_id: str
    criterios: dict[str, Literal["si", "no", "insuficiente"]]
    hallazgos: tuple[str, ...] = Field(max_length=8)
    fuentes_ids: tuple[str, ...] = Field(min_length=1, max_length=12)


class LecturaClases(Contrato):
    filas: tuple[JuicioFila, ...] = Field(min_length=1, max_length=4)


def esquema_lectura(rol):
    criterios = create_model(
        "CriteriosClase_" + rol,
        __base__=Contrato,
        **{c: (Literal["si", "no", "insuficiente"], ...) for c in CRITERIOS[rol]},
    )
    fila = create_model(
        "JuicioClase_" + rol,
        __base__=Contrato,
        fila_id=(str, ...),
        criterios=(criterios, ...),
        hallazgos=(tuple[str, ...], Field(max_length=8)),
        fuentes_ids=(tuple[str, ...], Field(min_length=1, max_length=12)),
    )
    return create_model(
        "LecturaClases_" + rol, __base__=Contrato, filas=(tuple[fila, ...], Field(min_length=1, max_length=4))
    )


def esquema_transporte(esquema):
    """Vertex recibe forma y tipos compactos; Pydantic conserva todas las cotas al validar la respuesta.

    Las múltiples cotas anidadas del guion excedieron la complejidad admitida por el proveedor.
    No se retira ningún validador de contenido, identidades, tiempos o tamaños en el proceso local.
    """

    class Transporte(esquema):
        @classmethod
        def model_json_schema(cls, *args, **kwargs):
            original = super().model_json_schema(*args, **kwargs)
            omitir = {"minLength", "maxLength", "minItems", "maxItems", "minimum", "maximum", "default", "title"}

            def limpiar(valor):
                if isinstance(valor, dict):
                    return {k: limpiar(v) for k, v in valor.items() if k not in omitir}
                if isinstance(valor, list):
                    return [limpiar(v) for v in valor]
                return valor

            return limpiar(original)

    return Transporte
