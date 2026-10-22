"""Resolve selected quotation identifiers to literals from verified evidence."""

# Historical implementation notes:
# Esto elimina la invención del texto literal por el modelo. No demuestra que una cita implique
# una afirmación: las revisiones semánticas y el gate de versión/fuentes siguen siendo necesarios.

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence

from pydantic import Field, field_validator

from goes_science_kg.motor.contratos import (
    Actividad,
    Afirmacion,
    Cita,
    Contrato,
    Evidencia,
    Propuesta,
)
from goes_science_kg.recuperacion.lexico import normalizar


class Fragmento(Contrato):
    """Represent an immutable evidence quotation selected by its registered identity."""

    id: str = Field(min_length=1, max_length=100)
    evidencia_id: str = Field(min_length=1)
    literal: str = Field(min_length=12, max_length=280)

    @field_validator("id", "evidencia_id")
    @classmethod
    def _id_no_vacio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("El identificador no puede estar vacío")
        return valor

    @field_validator("literal")
    @classmethod
    def _literal_citable(cls, texto: str) -> str:
        literal = " ".join(texto.split())
        if len(literal) < 12 or len(literal.split()) > 20:
            raise ValueError("Un fragmento necesita al menos doce caracteres y como máximo veinte palabras")
        return literal


class AfirmacionBorrador(Contrato):
    """Represent a draft factual statement using registered quotation identities."""

    texto: str = Field(min_length=10, max_length=1500)
    fragmentos_ids: list[str] = Field(min_length=1, max_length=5)

    @field_validator("texto")
    @classmethod
    def _texto_no_vacio(cls, texto: str) -> str:
        if not texto.strip():
            raise ValueError("La afirmación no puede estar vacía")
        return texto


class Borrador(Contrato):
    """Represent a draft using registered references rather than free-form quotations."""

    afirmaciones: list[AfirmacionBorrador] = Field(min_length=1, max_length=8)
    anclaje_curricular: list[str] = Field(min_length=1, max_length=5)
    actividad: Actividad
    limites: list[str] = Field(min_length=1)

    @field_validator("limites")
    @classmethod
    def _limites_no_vacios(cls, limites: list[str]) -> list[str]:
        if any(not limite.strip() for limite in limites):
            raise ValueError("Las limitaciones no pueden ser cadenas vacías")
        return limites


def _evidencias_verificadas(evidencias: Sequence[Evidencia]) -> dict[str, Evidencia]:
    por_id: dict[str, Evidencia] = {}
    for evidencia in evidencias:
        if not evidencia.id.strip() or not evidencia.texto.strip():
            raise ValueError("La evidencia necesita identificador y texto")
        if hashlib.sha256(evidencia.texto.encode("utf-8")).hexdigest() != evidencia.huella:
            raise ValueError(f"La evidencia {evidencia.id} no conserva su huella de texto")
        fuente = evidencia.fuente
        if not fuente.get("documento") or fuente.get("tipo") == "derivada" or fuente.get("fuente_primaria") is False:
            raise ValueError(f"La evidencia {evidencia.id} carece de procedencia primaria")
        if evidencia.id in por_id and por_id[evidencia.id] != evidencia:
            raise ValueError(f"La evidencia {evidencia.id} está definida de forma ambigua")
        por_id[evidencia.id] = evidencia
    return por_id


def _ventanas(texto: str, *, palabras: int, solape: int) -> list[str]:
    normalizado = " ".join(texto.split())
    literales = []
    for frase in re.split(r"(?<=[.!?;])\s+", normalizado):
        tokens = frase.split()
        inicio = 0
        while inicio < len(tokens):
            fin = min(len(tokens), inicio + palabras)
            while fin > inicio and len(" ".join(tokens[inicio:fin])) > 280:
                fin -= 1
            if fin == inicio:
                # No partir URLs o palabras enormes para aparentar evidencia útil.
                inicio += 1
                continue
            literal = " ".join(tokens[inicio:fin])
            if len(literal) >= 12:
                if literal not in normalizado:
                    raise ValueError("La segmentación alteró el texto original")
                literales.append(literal)
            if fin == len(tokens):
                break
            inicio = max(inicio + 1, fin - solape)
    return list(dict.fromkeys(literales))


def datos_fragmentos(
    fragmentos: Sequence[Fragmento], evidencias: Sequence[Evidencia], *, lectura_completa: bool = False
) -> dict:
    """Build a budgeted quotation payload with optional complete source readings."""
    por_id = {e.id: e for e in evidencias}
    seleccionados = sorted({f.evidencia_id for f in fragmentos})
    if not set(seleccionados).issubset(por_id):
        raise ValueError("Hay fragmentos de evidencias que no forman parte del contexto")
    datos = {
        "fragmentos": [f.model_dump() for f in fragmentos],
        "fuentes": {
            evidencia_id: {
                "fuente": por_id[evidencia_id].fuente,
                "version": por_id[evidencia_id].version,
                "huella": por_id[evidencia_id].huella,
            }
            for evidencia_id in seleccionados
        },
    }
    if lectura_completa:
        if any(marca in por_id[id_].texto for id_ in seleccionados for marca in ("(cid:", "\ufffd")):
            raise ValueError("La extracción primaria contiene glifos sin resolver")
        datos["lectura_primaria"] = {id_: por_id[id_].texto for id_ in seleccionados}
    return datos


def _anclajes_por_grupo(
    candidatos: list[tuple[Fragmento, int]],
    grupos: Sequence[Sequence[str]],
    cabe: Callable[[list[Fragmento]], bool],
    max_fragmentos: int,
) -> list[Fragmento]:
    """Reserve explicit group coverage before filling remaining context lexically."""

    # Implementation notes:
    # La selección voraz es determinista; no pretende resolver el empaquetado óptimo.
    # Un fragmento puede cubrir varios grupos superpuestos sin duplicarse.
    mascaras: dict[str, int] = {}
    for posicion, ids in enumerate(grupos):
        for evidencia_id in ids:
            mascaras[evidencia_id] = mascaras.get(evidencia_id, 0) | (1 << posicion)
    pendientes = (1 << len(grupos)) - 1
    salida: list[Fragmento] = []
    while pendientes and len(salida) < max_fragmentos:
        opciones = sorted(
            (
                (fragmento, mascaras.get(fragmento.evidencia_id, 0) & pendientes)
                for fragmento, _ in candidatos
                if mascaras.get(fragmento.evidencia_id, 0) & pendientes
            ),
            key=lambda par: -par[1].bit_count(),
        )
        elegido = next(((f, mascara) for f, mascara in opciones if cabe(salida + [f])), None)
        if elegido is None:
            break
        fragmento, mascara = elegido
        salida.append(fragmento)
        pendientes &= ~mascara
    if pendientes:
        raise ValueError("El presupuesto no conserva un fragmento de cada grupo obligatorio")
    return salida


def preparar_fragmentos(
    evidencias: Sequence[Evidencia],
    consulta: str,
    max_caracteres: int = 18000,
    *,
    max_fragmentos: int = 48,
    max_palabras: int = 20,
    solape: int = 4,
    grupos_obligatorios: Mapping[str, Sequence[str]] | None = None,
    lectura_completa: bool = False,
) -> list[Fragmento]:
    """Select citable windows while retaining evidence from the current local curriculum."""

    # Implementation notes:
    # La única versión distinta de ``referencia`` identifica el currículo actual del contexto;
    # mezclar versiones o un presupuesto sin espacio para su anclaje produce un error explícito.
    # El límite comprende el JSON de ``datos_fragmentos`` con fuente, versión y huella.
    # Con ``lectura_completa`` cuenta también el texto íntegro de las fuentes seleccionadas.
    # Si se declaran grupos, reserva primero al menos una fuente de cada uno; no convierte
    # esa cobertura estructural en respaldo semántico.
    if max_caracteres <= 0 or max_fragmentos < 1 or not 1 <= max_palabras <= 20 or not 0 <= solape < max_palabras:
        raise ValueError("Presupuesto, cantidad de fragmentos o ventanas inválidos")
    por_id = _evidencias_verificadas(evidencias)
    if grupos_obligatorios is not None:
        for nombre, ids in grupos_obligatorios.items():
            if (
                not nombre.strip()
                or isinstance(ids, str)
                or not ids
                or len(set(ids)) != len(ids)
                or not set(ids).issubset(por_id)
            ):
                raise ValueError("Cada grupo obligatorio requiere un nombre e IDs de evidencias conocidas sin repetir")
    versiones = {e.version for e in por_id.values() if e.version != "referencia"}
    if len(versiones) != 1:
        raise ValueError("Se requiere exactamente una versión de currículo local vigente")
    version = next(iter(versiones))
    terminos = set(normalizar(consulta))
    candidatos = []
    for evidencia in por_id.values():
        for literal in _ventanas(evidencia.texto, palabras=max_palabras, solape=solape):
            identidad = json.dumps(
                [evidencia.id, evidencia.version, evidencia.huella, evidencia.fuente, literal],
                ensure_ascii=False,
                sort_keys=True,
            )
            fragmento = Fragmento(
                id="F:" + hashlib.sha256(identidad.encode("utf-8")).hexdigest()[:24],
                evidencia_id=evidencia.id,
                literal=literal,
            )
            coincidencias = len(terminos.intersection(normalizar(literal)))
            candidatos.append((fragmento, coincidencias))
    candidatos.sort(key=lambda par: (-par[1], par[0].evidencia_id, par[0].id))
    locales = [f for f, _ in candidatos if por_id[f.evidencia_id].version == version]
    if not locales:
        raise ValueError("El currículo vigente no contiene un fragmento citable")

    def cabe(fragmentos: list[Fragmento]) -> bool:
        return (
            len(
                json.dumps(
                    datos_fragmentos(fragmentos, evidencias, lectura_completa=lectura_completa), ensure_ascii=False
                )
            )
            <= max_caracteres
        )

    if grupos_obligatorios is None:
        anclaje = next((fragmento for fragmento in locales if cabe([fragmento])), None)
        if anclaje is None:
            raise ValueError("El presupuesto no permite incluir un fragmento del currículo vigente y sus metadatos")
        salida = [anclaje]
    else:
        grupos = [tuple(e.id for e in por_id.values() if e.version == version), *grupos_obligatorios.values()]
        salida = _anclajes_por_grupo(candidatos, grupos, cabe, max_fragmentos)
    vistos = {f.id for f in salida}
    primera_por_fuente = []
    restantes = []
    fuentes_vistas = {f.evidencia_id for f in salida}
    for fragmento, _ in candidatos:
        if fragmento.id in vistos:
            continue
        if fragmento.evidencia_id not in fuentes_vistas:
            primera_por_fuente.append(fragmento)
            fuentes_vistas.add(fragmento.evidencia_id)
        else:
            restantes.append(fragmento)
    for fragmento in primera_por_fuente + restantes:
        if len(salida) >= max_fragmentos:
            break
        if fragmento.id not in vistos and cabe(salida + [fragmento]):
            salida.append(fragmento)
            vistos.add(fragmento.id)
    return salida


def resolver_borrador(borrador: Borrador, fragmentos: Sequence[Fragmento]) -> Propuesta:
    """Resolve known fragment identities to source literals without trusting model-written quotations."""
    registro = {f.id: f for f in fragmentos}
    if not registro or len(registro) != len(fragmentos):
        raise ValueError("El registro de fragmentos está vacío o contiene identificadores duplicados")

    def citas(ids: list[str]) -> list[Cita]:
        if not ids:
            raise ValueError("Cada afirmación o anclaje requiere fragmentos")
        if any(fragmento_id not in registro for fragmento_id in ids):
            raise ValueError("El borrador selecciona un identificador de fragmento desconocido")
        return [Cita(evidencia_id=registro[i].evidencia_id, literal=registro[i].literal) for i in dict.fromkeys(ids)]

    return Propuesta(
        afirmaciones=[Afirmacion(texto=a.texto, citas=citas(a.fragmentos_ids)) for a in borrador.afirmaciones],
        anclaje_curricular=citas(borrador.anclaje_curricular),
        actividad=borrador.actividad,
        limites=borrador.limites,
    )
