"""Recuperación documental por disciplina, con diversidad y descarte de preguntas solas."""

from __future__ import annotations

import re
from collections import Counter

from goes_science_kg.recuperacion.lexico import normalizar

VACIAS_INGLES = frozenset("of the and or for with in to from by as on at an is are be using".split())

LIBROS = {
    "biologia": {"biology-2e"},
    "quimica": {"chemistry-2e"},
    "fisica": {"college-physics-2e", "astronomy-2e", "university-physics-volume-2"},
    "ciencias_tierra_espacio": {"biology-2e", "chemistry-2e", "college-physics-2e", "astronomy-2e"},
}


def es_expositivo(texto):
    """Un pasaje disponible no es evidencia si sólo pregunta o depende de opciones omitidas."""
    normal = texto.strip()
    return not (
        normal.endswith(("?", ":"))
        or re.match(
            r"^(?:which|what|why|how|calculate|determine|explain|describe|indicate|complete|balance|classify)\b",
            normal,
            re.I,
        )
        or re.search(r"\b(?:explain why|complete and balance)\b", normal, re.I)
        or re.search(r"(?:following (?:questions|statements|scenarios)|which of the following)", normal, re.I)
    )


def buscar_fuentes(corpus, fila, *, k=6, max_caracteres=10000):
    disciplinas = fila["propuesta"].get("disciplinas_propuestas", [])
    libros = set().union(*(LIBROS.get(d, set()) for d in disciplinas))
    permitidos = {
        e.id
        for e in corpus.evidencias.values()
        if (not libros or e.fuente.get("libro") in libros) and es_expositivo(e.texto)
    }
    consulta = fila.get("consulta_recuperacion", "").strip()
    if not consulta:
        raise ValueError("La recuperación específica requiere la consulta bilingüe congelada")
    # La cola larga de una consulta no debe ocultar su concepto principal.
    palabras = [p for p in normalizar(consulta) if p not in VACIAS_INGLES]
    ancla = " ".join(palabras[:3])
    posiciones = Counter()
    for texto, peso in ((consulta, 1.0), (ancla, 1.5)):
        for posicion, (id_, _) in enumerate(corpus.indice.buscar(texto, permitidos=permitidos, limite=150), 1):
            posiciones[id_] += peso / (30 + posicion)
    candidatos = sorted(posiciones.items(), key=lambda p: (-p[1], p[0]))
    salida, por_documento, usados = [], Counter(), 0
    for id_, _ in candidatos:
        e = corpus.evidencias[id_]
        doc = e.fuente["documento"]
        if usados + len(e.texto) > max_caracteres or por_documento[doc] >= 3:
            continue
        corpus.verificar(e)
        salida.append(e)
        por_documento[doc] += 1
        usados += len(e.texto)
        if len(salida) == k:
            break
    if len(salida) < 2:
        raise ValueError("No hay evidencia expositiva suficiente en la disciplina asignada")
    return tuple(salida)
