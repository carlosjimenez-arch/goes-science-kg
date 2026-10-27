"""Respuestas de revisión verificables; una cobertura incompleta nunca equivale a aprobación."""

from __future__ import annotations

import html
from typing import Literal

from pydantic import Field

from goes_science_kg.motor.contratos import Contrato

ROLES = ("revision_ciencia", "revision_curriculo", "revision_psicopedagogia", "revision_adversarial")
Veredicto = Literal["aprobar", "vetar", "abstener"]


def normal(texto):
    return " ".join(html.unescape(texto).split())


class Respaldo(Contrato):
    fuente_id: str
    cita: str = Field(min_length=12, max_length=400)


class Hallazgo(Contrato):
    ruta: str
    ancla: str
    problema: str = Field(min_length=20)
    reemplazo: str
    respaldo: list[Respaldo] = Field(max_length=3)


class LecturaItem(Contrato):
    id: str
    veredicto: Veredicto
    comprobacion: str = Field(min_length=30, max_length=1200)
    respaldos: list[Respaldo] = Field(max_length=3)
    hallazgos: list[Hallazgo] = Field(max_length=8)


class DictamenLote(Contrato):
    items: list[LecturaItem] = Field(min_length=1, max_length=230)
    observaciones: str = Field(max_length=2000)


def leer_ruta(documento, ruta):
    """Acceso exclusivamente a campos derivados; no permite alterar IDs, orígenes o el original."""
    partes = ruta.split("/")
    permitidos = {
        "indicador",
        "producto",
        "explicacion",
        "seguridad",
        "actividades",
        "criterios",
        "perfil_apoyo",
        "aplicacion",
        "recuperacion",
        "factibilidad",
        "rubrica",
        "caso_resuelto",
        "articulacion",
        "progresion",
        "regla",
    }
    protegidos = {
        "id",
        "origen_tarea_id",
        "fuentes",
        "fila_id",
        "huella_curriculo",
        "destino",
        "referencias",
        "estado_revision",
        "respuesta_observada",
        "logro_observado",
    }
    if not partes or partes[0] not in permitidos or protegidos.intersection(partes):
        raise ValueError("La ruta no es un campo editorial permitido")
    valor = documento
    for parte in partes:
        if isinstance(valor, list) and parte.isascii() and parte.isdecimal():
            valor = valor[int(parte)]
        elif isinstance(valor, dict):
            valor = valor[parte]
        else:
            raise ValueError("La ruta editorial no identifica un valor")
    if not isinstance(valor, str):
        raise ValueError("Sólo se reemplazan valores textuales completos")
    return valor


def validar_dictamen(dictamen, solicitud):
    items = {i["id"]: i for i in solicitud["items"]}
    ids = [i.id for i in dictamen.items]
    if len(ids) != len(set(ids)) or set(ids) != set(items):
        raise ValueError("El dictamen omite, repite o inventa elementos")
    fuentes = {s["id"]: s.get("texto", "".join(s.get("fragmentos", []))) for s in solicitud["fuentes"]}
    for item in dictamen.items:
        if item.veredicto == "aprobar" and item.hallazgos:
            raise ValueError("No se aprueba con hallazgos materiales")
        if item.veredicto == "aprobar" and not item.respaldos:
            raise ValueError("La aprobación requiere un respaldo visible")
        if item.veredicto != "aprobar" and not item.hallazgos:
            raise ValueError("Un veto o abstención debe localizar qué falta")
        for h in item.hallazgos:
            valor = leer_ruta(items[item.id]["edicion"], h.ruta)
            if normal(h.ancla) not in normal(valor) or (not h.ancla and valor):
                raise ValueError("El hallazgo no ancla el contenido exacto")
        for respaldo in [*item.respaldos, *(r for h in item.hallazgos for r in h.respaldo)]:
            if respaldo.fuente_id not in fuentes or normal(respaldo.cita) not in normal(fuentes[respaldo.fuente_id]):
                raise ValueError("La cita del revisor no existe en el contexto visible")
    return dictamen
