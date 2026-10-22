"""Coincidencias de frases completas, sin stemming ni equivalencia de conceptos."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass

from goes_science_kg.modelos import Nodo

_PALABRA = re.compile(r"[^\W_]+", re.UNICODE)


def _clave(token: str) -> str:
    # CO/Co, ADN/ADn, pH/PH, etc. no se colapsan; tampoco se eliminan tildes.
    return token if len(token) <= 3 else token.casefold()


@dataclass(frozen=True)
class CoincidenciaAlias:
    nodo_id: str
    alias: str
    literal: str
    inicio: int
    fin: int
    alternativas: tuple[str, ...]


class IndiceAlias:
    """Índice por primer término para evitar comparar cada alias con todas las celdas."""

    def __init__(self, nodos: list[Nodo]):
        por_clave = defaultdict(list)
        self.avisos = []
        for nodo in sorted(nodos, key=lambda n: n.id):
            sinonimos = nodo.props.get("sinonimos", [])
            if not isinstance(sinonimos, (list, tuple)) or any(not isinstance(a, str) for a in sinonimos):
                self.avisos.append(f"{nodo.id}: sinonimos con formato inválido; solo se indexa la etiqueta")
                sinonimos = []
            for alias in sorted(set([nodo.etiqueta, *sinonimos])):
                texto = unicodedata.normalize("NFKC", alias)
                tokens = tuple(_clave(m.group()) for m in _PALABRA.finditer(texto))
                if tokens:
                    por_clave[tokens].append((nodo.id, alias))
        self._indice = defaultdict(list)
        for tokens, entradas in sorted(por_clave.items()):
            alternativas = tuple(sorted({id_nodo for id_nodo, _ in entradas}))
            self._indice[tokens[0]].append((tokens, tuple(sorted(set(entradas))), alternativas))

    def buscar(self, texto: str) -> list[CoincidenciaAlias]:
        """Los offsets corresponden a NFKC; se conserva también el texto fuente en la evidencia."""
        normalizado = unicodedata.normalize("NFKC", texto)
        palabras = list(_PALABRA.finditer(normalizado))
        claves = tuple(_clave(m.group()) for m in palabras)
        resultado = []
        for posicion, token in enumerate(claves):
            for alias, entradas, alternativas in self._indice.get(token, ()):
                if claves[posicion : posicion + len(alias)] != alias:
                    continue
                inicio, fin = palabras[posicion].start(), palabras[posicion + len(alias) - 1].end()
                for identidad, etiqueta in entradas:
                    resultado.append(
                        CoincidenciaAlias(
                            identidad,
                            etiqueta,
                            normalizado[inicio:fin],
                            inicio,
                            fin,
                            alternativas,
                        )
                    )
        return sorted(set(resultado), key=lambda m: (m.inicio, m.fin, m.nodo_id, m.alias))
