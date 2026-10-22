"""Propuestas curriculares V4: identidad por fila, fuentes y cuatro revisiones de la salida exacta."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, create_model, model_validator

from goes_science_kg.curriculo.catalogacion import AsignaturaCiencia
from goes_science_kg.motor.contratos import Contrato, Evidencia
from goes_science_kg.motor.fragmentos import Fragmento

ROLES_MEJORA = ("revision_ciencia", "revision_curriculo", "revision_psicopedagogia", "revision_adversarial")
CRITERIOS_MEJORA = {
    "revision_ciencia": ("correccion_cientifica", "significado_original_conservado", "evidencia_pertinente"),
    "revision_curriculo": (
        "objetivos_observables",
        "evaluacion_coherente",
        "referentes_sin_equivalencias",
        "conservacion_del_alcance",
    ),
    "revision_psicopedagogia": ("adecuacion_al_grado", "andamiaje", "carga_cognitiva", "accesibilidad"),
    "revision_adversarial": (
        "sin_contradicciones",
        "fuentes_implican_justificacion",
        "seguridad",
        "sin_datos_inventados",
    ),
}
Valor = Literal["si", "no", "insuficiente"]
MAX_BYTES_BORRADOR = 120000
LIMITE_MEJORAS = (
    "Propuesta curricular revisada automáticamente, condicionada a sus filas y escenario; "
    "no modifica originales, acredita eficacia, homologa grados ni constituye aprobación del MINED"
)


class SolicitudMejora(Contrato):
    grado: int = Field(ge=2, le=11)
    asignatura_malla: str
    unidad: str


class MejoraFila(Contrato):
    fila_id: str
    accion: Literal["mantener_objetivo", "precisar_objetivo", "fuera_alcance"]
    disciplinas_propuestas: tuple[AsignaturaCiencia, ...] = Field(max_length=4)
    objetivo_propuesto: str = Field(min_length=10, max_length=1800)
    indicador_observable: str = Field(min_length=10, max_length=800)
    producto_evaluable: str = Field(min_length=10, max_length=800)
    criterio_evaluacion: str = Field(min_length=10, max_length=800)
    orientacion_didactica: str = Field(min_length=10, max_length=1000)
    recursos_condicionales: tuple[str, ...] = Field(max_length=8)
    seguridad: str = Field(min_length=10, max_length=500)
    andamiaje: str = Field(min_length=10, max_length=700)
    contexto_salvador: str = Field(min_length=10, max_length=700)
    justificacion: str = Field(min_length=15, max_length=700)
    fragmentos_ids: tuple[str, ...] = Field(min_length=2, max_length=6)

    @model_validator(mode="after")
    def _disciplinas(self):
        if len(self.disciplinas_propuestas) != len(set(self.disciplinas_propuestas)):
            raise ValueError("No se repiten disciplinas propuestas")
        if bool(self.disciplinas_propuestas) != (self.accion != "fuera_alcance"):
            raise ValueError("Sólo las propuestas de Ciencias llevan disciplinas")
        return self


class BorradorMejora(Contrato):
    filas: tuple[MejoraFila, ...] = Field(min_length=1, max_length=30)
    enmiendas_aceptadas: tuple[str, ...] = Field(max_length=3)
    sintesis: str = Field(min_length=20, max_length=1200)
    limites: tuple[str, ...] = Field(min_length=1, max_length=12)

    @model_validator(mode="after")
    def _presupuesto_salida(self):
        if len(self.model_dump_json().encode()) > MAX_BYTES_BORRADOR:
            raise ValueError("La propuesta completa excede ciento veinte mil bytes UTF-8; requiere concisión")
        return self


class PreparacionMejora(Contrato):
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    solicitud: SolicitudMejora
    huella_curriculo: str
    huella_catalogo: str
    filas_originales: tuple[dict, ...]
    clasificaciones_originales: dict[str, dict]
    alertas: dict[str, str]
    correcciones_requeridas: tuple[dict, ...] = ()
    evidencias: tuple[Evidencia, ...]
    fragmentos: tuple[Fragmento, ...]
    grupos: dict[str, tuple[str, ...]]
    contexto_aula: dict
    limites: tuple[str, ...]


class LecturaMejora(Contrato):
    criterios: dict[str, Valor]
    fragmentos_ids: tuple[str, ...] = Field(min_length=1, max_length=60)
    hallazgos: tuple[str, ...] = Field(max_length=12)
    limites: tuple[str, ...] = Field(min_length=1, max_length=8)


def esquema_revision(rol: str) -> type[Contrato]:
    criterios = create_model("Criterios_" + rol, __base__=Contrato, **{c: (Valor, ...) for c in CRITERIOS_MEJORA[rol]})
    return create_model(
        "Lectura_" + rol,
        __base__=Contrato,
        criterios=(criterios, ...),
        fragmentos_ids=(tuple[str, ...], Field(min_length=1, max_length=60)),
        hallazgos=(tuple[str, ...], Field(max_length=12)),
        limites=(tuple[str, ...], Field(min_length=1, max_length=8)),
    )


class DictamenMejora(Contrato):
    rol: str
    modelo: str
    huella_preparacion: str
    huella_borrador: str
    lectura: LecturaMejora | None
    error: str | None = None


class RondaMejora(Contrato):
    borrador: BorradorMejora | None
    errores_estructura: tuple[str, ...]
    dictamenes: tuple[DictamenMejora, ...]
    error_generacion: str | None = None
    respuesta_rechazada: str | None = Field(default=None, max_length=1000000)
    errores_generacion: tuple[str, ...] = ()


class ResultadoMejora(Contrato):
    solicitud: SolicitudMejora
    ejecucion_id: str
    preparacion_id: str
    estado: Literal["respaldado_automaticamente", "no_respaldado", "abstencion"]
    propuesta: BorradorMejora | None
    rondas: tuple[RondaMejora, ...] = Field(min_length=1, max_length=2)
    motivos: tuple[str, ...]
    limite: Literal[LIMITE_MEJORAS] = LIMITE_MEJORAS
