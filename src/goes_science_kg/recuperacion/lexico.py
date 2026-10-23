"""Score BM25 through inverted postings for documents sharing query terms."""

from __future__ import annotations

import heapq
import math
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Iterable

from goes_science_kg.recuperacion.modelos import Documento

VACIAS = frozenset("a al con de del el en es la las lo los o para por que se su un una unos unas y".split())


def normalizar(texto: str) -> list[str]:
    """Normalize case and diacritics while preserving Unicode scientific terms."""
    base = unicodedata.normalize("NFKD", texto.casefold())
    base = "".join(c for c in base if not unicodedata.combining(c))
    return [t for t in re.findall(r"[^\W_]+", base) if len(t) > 1 and t not in VACIAS]


class IndiceLexico:
    """Index BM25 postings with deterministic identifier-based tie breaking."""

    def __init__(self, documentos: Iterable[Documento], *, k1: float = 1.4, b: float = 0.75):
        if not math.isfinite(k1) or k1 <= 0 or not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("Parámetros BM25 inválidos")
        self.k1 = k1
        self.b = b
        self.longitudes: dict[str, int] = {}
        self.invertido: dict[str, list[tuple[str, int]]] = defaultdict(list)
        for documento in documentos:
            tokens = normalizar(documento.texto)
            self.longitudes[documento.id] = len(tokens)
            for termino, frecuencia in Counter(tokens).items():
                self.invertido[termino].append((documento.id, frecuencia))
        self.n = len(self.longitudes)
        self.promedio = sum(self.longitudes.values()) / max(1, self.n)

    def buscar(self, consulta: str, *, permitidos: set[str], limite: int) -> list[tuple[str, float]]:
        """Return permitted documents with positive scores without filling results with noise."""
        if not self.n or not self.promedio or not permitidos or limite <= 0:
            return []
        puntajes: dict[str, float] = defaultdict(float)
        for termino in set(normalizar(consulta)):
            lista = self.invertido.get(termino, ())
            idf = math.log1p((self.n - len(lista) + 0.5) / (len(lista) + 0.5))
            for documento_id, frecuencia in lista:
                if documento_id not in permitidos:
                    continue
                norma = self.k1 * (1 - self.b + self.b * self.longitudes[documento_id] / self.promedio)
                puntajes[documento_id] += idf * frecuencia * (self.k1 + 1) / (frecuencia + norma)
        return heapq.nsmallest(limite, puntajes.items(), key=lambda item: (-item[1], item[0]))
