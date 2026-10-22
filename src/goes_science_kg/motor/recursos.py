"""Define explicit material equivalences without assuming classroom availability."""

import re

ALIAS = {
    "papel": {"papel", "hoja de papel", "hojas de papel"},
    "lapiz": {"lapiz", "lápiz", "lapices", "lápices", "lápiz de grafito", "lápices de grafito"},
    "agua": {"agua"},
    "regla": {"regla", "regla graduada"},
    "tijeras": {"tijera", "tijeras"},
}


def _normalizar(recurso: str) -> str:
    return re.sub(r"\s+", " ", recurso).strip().casefold()


POR_ALIAS = {_normalizar(alias): id_recurso for id_recurso, nombres in ALIAS.items() for alias in nombres}


def canonico(recurso: str) -> str:
    """Resolve an explicitly registered resource synonym to its canonical name."""

    limpio = _normalizar(recurso)
    return POR_ALIAS.get(limpio, limpio)
