"""Define new authoring contracts and SDK-compatible transport without weakening local validation."""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, create_model, model_validator

from goes_science_kg.aprendizaje.cierre_recorridos import RecorridoFinal, RubricaRecorrido, validar_recorrido
from goes_science_kg.clases.complementaria import AnexoClase, EvaluacionUnidad
from goes_science_kg.clases.contratos import ComprobacionCalculo, GuionClase
from goes_science_kg.clases.contratos import esquema_transporte as compactar_esquema_historico

T = TypeVar("T", bound=BaseModel)
PERFIL_DIRECTO = "contrato_directo_v1"
PERFIL_MAPA = "recorrido_mapa_v1"
PERFIL_LISTA = "recorrido_soluciones_lista_v1"
VERSION_ADAPTADOR = "lista-soluciones-a-mapa-sin-redaccion-1"


def canonico(valor: Any) -> bytes:
    """Serialize campaign identities with explicit stable UTF-8 bytes."""
    return (
        json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha256(valor: bytes) -> str:
    """Identify the exact bytes of a prompt, context, schema, or received response."""
    return hashlib.sha256(valor).hexdigest()


def esquema_transporte(esquema: type[T]) -> type[T]:
    """Compact the remote schema while preserving all original Pydantic constraints locally."""

    class Transporte(compactar_esquema_historico(esquema)):
        @classmethod
        def model_json_schema(cls, *args, **kwargs):
            original = copy.deepcopy(super().model_json_schema(*args, **kwargs))

            def adaptar(valor):
                if isinstance(valor, dict):
                    # google-genai 2.28 rejects non-string Literal constants in response_schema.
                    if valor.get("type") == "boolean":
                        valor.pop("const", None)
                    for contenido in valor.values():
                        adaptar(contenido)
                elif isinstance(valor, list):
                    for contenido in valor:
                        adaptar(contenido)

            adaptar(original)
            if esquema is RecorridoAutorLista:
                # Keep only this supported bound: there is at least one item in each pupil phase.
                original["properties"]["soluciones_docente"]["minItems"] = 3
            return original

    Transporte.__name__ = esquema.__name__ + "TransporteVertex"
    return Transporte


def plazas_disponibles(componente: dict) -> int:
    """Bound each component to its explicitly remaining one or two paid attempts."""
    plazas = componente.get("plazas_disponibles", 2)
    if type(plazas) is not int or plazas not in (1, 2):
        raise ValueError("Cada componente debe fijar una o dos plazas disponibles")
    return plazas


class ContratoAutor(BaseModel):
    """Reject fields outside an explicitly described authoring component."""

    model_config = ConfigDict(extra="forbid")


class ObjetivoPendiente(ContratoAutor):
    """Keep every missing unit objective visible with its reason."""

    fila_id: str = Field(min_length=1)
    motivo: str = Field(min_length=20)


class GuiaUnidad(ContratoAutor):
    """Describe a unit's actual coverage rather than inferring completeness from a pilot."""

    unidad_id: str = Field(min_length=1)
    titulo: str = Field(min_length=8)
    objetivos_cubiertos: list[str] = Field(min_length=1)
    objetivos_pendientes: list[ObjetivoPendiente]
    completa: bool
    orientaciones_docente: list[str] = Field(min_length=1)
    secuencia_componentes: list[str] = Field(min_length=1)
    fuentes_ids: list[str] = Field(min_length=1)
    carga_cognitiva_no_medida: Literal[True]

    @model_validator(mode="after")
    def _alcance(self):
        cubiertos = self.objetivos_cubiertos
        pendientes = [p.fila_id for p in self.objetivos_pendientes]
        if len(cubiertos + pendientes) != len(set(cubiertos + pendientes)):
            raise ValueError("Los objetivos cubiertos y pendientes deben ser únicos y disjuntos")
        if self.completa != (not pendientes):
            raise ValueError("La completitud debe coincidir con la ausencia de objetivos pendientes")
        return self


# Provenance and source metadata are supplied locally from pinned evidence, never authored by the model.
RecorridoAutor = create_model(
    "RecorridoAutor",
    __base__=ContratoAutor,
    **{
        nombre: (campo.annotation, campo)
        for nombre, campo in RecorridoFinal.model_fields.items()
        if nombre not in {"origen", "fuentes"}
    },
    fuentes_ids=(list[str], Field(min_length=1)),
)


class SolucionItemAutor(ContratoAutor):
    """Expose each named solution as an explicit remote object instead of a dynamic map."""

    item_id: str = Field(min_length=1)
    respuesta: str = Field(min_length=10)
    explicacion: str = Field(min_length=10)
    rubrica: list[RubricaRecorrido] = Field(min_length=1)
    calculos: list[ComprobacionCalculo]


RecorridoAutorLista = create_model(
    "RecorridoAutorLista",
    __base__=ContratoAutor,
    **{
        nombre: (campo.annotation, campo)
        for nombre, campo in RecorridoAutor.model_fields.items()
        if nombre != "soluciones_docente"
    },
    soluciones_docente=(list[SolucionItemAutor], Field(min_length=3)),
)


ESQUEMAS = {
    "guion_sucesor": GuionClase,
    "anexo_implementacion": AnexoClase,
    "recorrido_cerrado": RecorridoAutor,
    "evaluacion_unidad": EvaluacionUnidad,
    "guia_sintesis_unidad": GuiaUnidad,
}


def contrato_autor_api(tipo: str, perfil: str | None = None) -> type[BaseModel]:
    """Select a versioned remote DTO while leaving every business contract unchanged."""
    if tipo not in ESQUEMAS:
        raise ValueError("Tipo de autoría no reconocido")
    perfil = perfil or (PERFIL_LISTA if tipo == "recorrido_cerrado" else PERFIL_DIRECTO)
    if tipo == "recorrido_cerrado":
        if perfil == PERFIL_LISTA:
            return RecorridoAutorLista
        if perfil == PERFIL_MAPA:
            return RecorridoAutor
    elif perfil == PERFIL_DIRECTO:
        return ESQUEMAS[tipo]
    raise ValueError("Perfil de transporte no reconocido para el tipo solicitado")


def perfil_transporte_plan(plan: dict, tipo: str) -> str:
    """Resolve an explicit profile or an exactly pinned legacy schema, never by inspecting output."""
    perfil = plan.get("perfiles_transporte", {}).get(tipo)
    if perfil is None and tipo == "recorrido_cerrado":
        expected = plan["esquemas_sha256"].get(tipo)
        candidates = [
            candidate
            for candidate in (PERFIL_MAPA, PERFIL_LISTA)
            if sha256(canonico(esquema_transporte(contrato_autor_api(tipo, candidate)).model_json_schema())) == expected
        ]
        if len(candidates) != 1:
            raise ValueError("El SHA del esquema no determina un perfil de recorrido único")
        perfil = candidates[0]
    perfil = perfil or PERFIL_DIRECTO
    contrato_autor_api(tipo, perfil)
    return perfil


def leer_objeto_autor(raw: bytes | str) -> dict:
    """Parse exact received JSON without silently dropping duplicate fields or non-finite numbers."""

    def pares_unicos(pares):
        resultado = {}
        for key, value in pares:
            if key in resultado:
                raise ValueError("Campo JSON repetido en la respuesta de autoría")
            resultado[key] = value
        return resultado

    def no_constante(value):
        raise ValueError(f"Constante JSON no finita: {value}")

    contenido = json.loads(raw, object_pairs_hook=pares_unicos, parse_constant=no_constante)
    if not isinstance(contenido, dict):
        raise ValueError("La respuesta de autoría debe ser un objeto JSON")
    return contenido


def normalizar_autoria(tipo: str, contenido: dict, *, perfil: str | None = None) -> dict:
    """Rekey typed remote solutions bijectively; never write, invent, coerce or discard their content."""
    perfil = perfil or (PERFIL_LISTA if tipo == "recorrido_cerrado" else PERFIL_DIRECTO)
    api = contrato_autor_api(tipo, perfil)
    if not isinstance(contenido, dict):
        raise ValueError("La autoría requiere un objeto JSON")
    if tipo != "recorrido_cerrado":
        return copy.deepcopy(contenido)
    api.model_validate(contenido, strict=perfil == PERFIL_LISTA)
    resultado = copy.deepcopy(contenido)
    if perfil == PERFIL_LISTA:
        soluciones = {}
        for item in contenido["soluciones_docente"]:
            item_id = item["item_id"]
            if item_id in soluciones:
                raise ValueError("item_id duplicado: no se puede perder una solución al formar el mapa")
            for calculo in item["calculos"]:
                for nombre in ("resultado", "tolerancia", "tolerancia_relativa"):
                    if nombre in calculo and (
                        type(calculo[nombre]) not in (int, float) or not math.isfinite(calculo[nombre])
                    ):
                        raise ValueError("El cálculo requiere números finitos originales, sin coerción")
            soluciones[item_id] = {key: copy.deepcopy(value) for key, value in item.items() if key != "item_id"}
        resultado["soluciones_docente"] = soluciones
    negocio = RecorridoAutor.model_validate(resultado)
    items = (
        list(negocio.diagnostico.items)
        + list(negocio.refuerzo.practica_guiada.items)
        + list(negocio.comprobacion_independiente.items)
    )
    ids = [item.id for item in items]
    if len(ids + [negocio.refuerzo.ejemplo_trabajado.id]) != len(set(ids + [negocio.refuerzo.ejemplo_trabajado.id])):
        raise ValueError("Las identidades de ítems y ejemplo deben ser distintas")
    if set(resultado["soluciones_docente"]) != set(ids):
        raise ValueError("El solucionario debe cubrir exactamente diagnóstico, práctica y comprobación")
    return resultado


def equivalencia_raw_normalizado(raw: bytes | str, tipo: str, *, perfil: str | None = None) -> dict:
    """Return a traceable normalized author object and prove a structural round trip without adding text."""
    raw_bytes = raw.encode() if isinstance(raw, str) else raw
    original = leer_objeto_autor(raw_bytes)
    perfil = perfil or (PERFIL_LISTA if tipo == "recorrido_cerrado" else PERFIL_DIRECTO)
    normalizado = normalizar_autoria(tipo, original, perfil=perfil)
    inverso = copy.deepcopy(normalizado)
    orden = []
    if tipo == "recorrido_cerrado" and perfil == PERFIL_LISTA:
        orden = [item["item_id"] for item in original["soluciones_docente"]]
        inverso["soluciones_docente"] = [
            {"item_id": item_id, **copy.deepcopy(normalizado["soluciones_docente"][item_id])} for item_id in orden
        ]
    if canonico(inverso) != canonico(original):
        raise ValueError("La normalización no tiene una inversa estructural exacta")
    return {
        "autor_normalizado": normalizado,
        "raw_sha256": sha256(raw_bytes),
        "normalizado_sha256": sha256(canonico(normalizado)),
        "perfil_transporte": perfil,
        "adapter_version": VERSION_ADAPTADOR,
        "adapter_codigo_sha256": sha256(Path(__file__).read_bytes()),
        "orden_soluciones_raw": orden,
        "conversion_biyectiva": True,
        "limite": "Conversión estructural; no corrige ni añade ciencia, texto, cálculos o aprobación.",
    }


def completar_recorrido(autor: BaseModel | dict, *, origen: dict, fuentes: list[dict]) -> dict:
    """Join authored material to exact local provenance and validate the complete learning cycle."""
    contenido = RecorridoAutor.model_validate(autor).model_dump(mode="json")
    ids = contenido.pop("fuentes_ids")
    registradas = {f["id"]: f for f in fuentes}
    if len(ids) != len(set(ids)) or set(ids) - registradas.keys():
        raise ValueError("El recorrido cita fuentes repetidas o ajenas al contexto fijado")
    resultado = contenido | {"origen": copy.deepcopy(origen), "fuentes": [registradas[i] for i in ids]}
    errores = validar_recorrido(resultado)
    if errores:
        raise ValueError("; ".join(errores))
    return resultado


def validar_alcance_unidad(guia: GuiaUnidad | dict, objetivos_unidad: list[str]) -> GuiaUnidad:
    """Check the complete curricular denominator independently of the guide's own declaration."""
    resultado = GuiaUnidad.model_validate(guia)
    if len(objetivos_unidad) != len(set(objetivos_unidad)) or not objetivos_unidad:
        raise ValueError("El denominador curricular requiere objetivos únicos y no vacíos")
    declarados = set(resultado.objetivos_cubiertos) | {p.fila_id for p in resultado.objetivos_pendientes}
    if declarados != set(objetivos_unidad):
        raise ValueError("La guía debe declarar cada objetivo curricular como cubierto o pendiente")
    return resultado
