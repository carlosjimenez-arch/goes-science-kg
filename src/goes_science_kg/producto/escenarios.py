"""Restricciones de aula sobre una unidad íntegra; no simula aprendizaje ni valida tiempos."""

from __future__ import annotations

import unicodedata

from pydantic import Field, field_validator

from goes_science_kg.motor.contratos import Contrato, huella
from goes_science_kg.producto.unidades import ContextoAula, PaqueteUnidad


class RequisitoSesion(Contrato):
    fila_id: str = Field(min_length=1, max_length=200)
    bloques_propuestos: int = Field(ge=1, le=12)
    recursos_necesarios: tuple[str, ...] = Field(max_length=32)
    justificacion_propuesta: str = Field(min_length=20, max_length=1000)

    @field_validator("recursos_necesarios")
    @classmethod
    def _recursos(cls, valores):
        if any(not v.strip() or len(v) > 300 for v in valores):
            raise ValueError("Los recursos deben ser nombres no vacíos de hasta 300 caracteres")
        return valores


class EscenarioUnidad(Contrato):
    nombre: str = Field(min_length=1, max_length=120)
    paquete_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    aula_declarada: ContextoAula
    minutos_disponibles: int = Field(ge=0, le=50000)
    requisitos: tuple[RequisitoSesion, ...] = Field(min_length=1, max_length=200)


def _recurso(texto: str) -> str:
    # Normaliza escritura y acentos, sin suponer equivalencias entre instrumentos diferentes.
    return " ".join(
        "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).casefold().split()
    )


def evaluar_escenario(paquete: PaqueteUnidad, escenario: EscenarioUnidad) -> dict:
    """Comprueba cobertura, tiempo y recursos explícitos; no mueve ni elimina objetivos."""
    if paquete.id != huella(paquete.model_dump(mode="json", exclude={"id"})) or escenario.paquete_id != paquete.id:
        raise ValueError("El escenario necesita la identidad íntegra de su paquete")
    filas = {f.id for f in paquete.filas}
    requisitos = {r.fila_id: r for r in escenario.requisitos}
    if len(requisitos) != len(escenario.requisitos) or requisitos.keys() != filas:
        raise ValueError("Declare cada fila exactamente una vez; el escenario no omite ni agrega objetivos")
    disponibles = {_recurso(r) for r in escenario.aula_declarada.recursos}
    sesiones = []
    for sesion in paquete.sesiones:
        requisito = requisitos[sesion.fila_id]
        sesiones.append(
            {
                "fila_id": sesion.fila_id,
                "bloques_propuestos": requisito.bloques_propuestos,
                "minutos_propuestos": requisito.bloques_propuestos * escenario.aula_declarada.minutos_por_sesion,
                "recursos_faltantes": [r for r in requisito.recursos_necesarios if _recurso(r) not in disponibles],
                "justificacion_propuesta": requisito.justificacion_propuesta,
            }
        )
    minutos = sum(s["minutos_propuestos"] for s in sesiones)
    faltan_recursos = any(s["recursos_faltantes"] for s in sesiones)
    deficit = max(0, minutos - escenario.minutos_disponibles)
    return {
        "nombre": escenario.nombre,
        "paquete_id": paquete.id,
        "huella_escenario": huella(escenario),
        "estado": "restricciones_incumplidas" if faltan_recursos or deficit else "restricciones_declaradas_satisfechas",
        "filas_conservadas": len(filas),
        "minutos_propuestos": minutos,
        "minutos_disponibles": escenario.minutos_disponibles,
        "deficit_minutos": deficit,
        "sesiones": sesiones,
        "llamadas_modelos": 0,
        "limites": [
            "Recursos y capacidad son declaraciones del escenario, no una constatación en una escuela",
            "Bloques y requisitos son propuestas; su suficiencia pedagógica no está validada",
            "Satisfacer las restricciones no acredita calidad pedagógica, aprendizaje ni aprobación oficial",
            "No se reordenan objetivos ni se atribuyen prerrequisitos que no tengan evidencia",
        ],
    }
