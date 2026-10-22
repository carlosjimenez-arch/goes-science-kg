"""Compute optional vector similarity with corpus, model, and dimension validation."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from goes_science_kg.recuperacion.modelos import Documento, huella_corpus, ordenar_documentos

if TYPE_CHECKING:
    import numpy as np


def _numpy():
    try:
        import numpy as np
    except ImportError as error:
        raise RuntimeError("La búsqueda densa requiere numpy; la búsqueda léxica funciona sin él") from error
    return np


class IndiceEmbeddings:
    """Index vectors in source order without mixing embedding models or corpora."""

    def __init__(self, documentos: Iterable[Documento], vectores: Sequence[Sequence[float]], *, modelo: str):
        np = _numpy()
        originales = tuple(documentos)
        ordenar_documentos(originales)
        if not modelo.strip():
            raise ValueError("El modelo de embeddings debe identificarse")
        matriz = np.asarray(vectores, dtype=np.float32)
        if matriz.ndim != 2 or matriz.shape[0] != len(originales) or not len(originales) or not matriz.shape[1]:
            raise ValueError("La matriz debe tener una fila por documento y al menos una dimensión")
        if not np.isfinite(matriz).all():
            raise ValueError("Los embeddings contienen valores no finitos")
        normas = np.linalg.norm(matriz.astype(np.float64), axis=1)
        if (normas == 0).any():
            raise ValueError("Un embedding de norma cero no permite calcular coseno")
        self.ids = tuple(d.id for d in originales)
        self.modelo = modelo
        self.dimensiones = matriz.shape[1]
        self.huella = huella_corpus(originales)
        self.matriz: np.ndarray = (matriz / normas[:, None]).astype(np.float32)
        self.matriz.setflags(write=False)
        self._posiciones = {documento_id: i for i, documento_id in enumerate(self.ids)}
        posiciones = [self._posiciones[i] for i in sorted(self.ids)]
        self.huella_vectores = hashlib.sha256(self.matriz[posiciones].tobytes()).hexdigest()

    def validar_corpus(self, documentos: Iterable[Documento]) -> None:
        """Reject stale vectors even when document identifiers remain unchanged."""
        if huella_corpus(documentos) != self.huella:
            raise ValueError("El corpus cambió: se deben regenerar los embeddings")

    def buscar(
        self,
        vector: Sequence[float],
        *,
        modelo: str,
        permitidos: set[str],
        limite: int,
    ) -> list[tuple[str, float]]:
        """Compute cosine scores in one matrix operation over the permitted subset."""
        np = _numpy()
        if modelo != self.modelo:
            raise ValueError("El vector de consulta pertenece a otro modelo de embeddings")
        consulta = np.asarray(vector, dtype=np.float64)
        if consulta.ndim != 1 or consulta.shape[0] != self.dimensiones:
            raise ValueError("Dimensión incorrecta del vector de consulta")
        if not np.isfinite(consulta).all():
            raise ValueError("El vector de consulta contiene valores no finitos")
        norma = np.linalg.norm(consulta)
        if not np.isfinite(norma) or norma == 0:
            raise ValueError("El vector de consulta debe tener norma finita y positiva")
        posiciones = [self._posiciones[i] for i in sorted(permitidos) if i in self._posiciones]
        if not posiciones or limite <= 0:
            return []
        puntajes = self.matriz[posiciones] @ (consulta / norma).astype(np.float32)
        orden = np.argsort(-puntajes, kind="stable")[:limite]
        return [(self.ids[posiciones[int(i)]], float(puntajes[i])) for i in orden]

    def guardar(self, archivo: str | Path) -> None:
        """Persist arrays and simple metadata without serializing executable objects."""
        np = _numpy()
        with Path(archivo).open("wb") as salida:
            np.savez_compressed(
                salida,
                ids=np.asarray(self.ids),
                matriz=self.matriz,
                modelo=np.asarray(self.modelo),
                huella=np.asarray(self.huella),
            )

    @classmethod
    def cargar(cls, archivo: str | Path, documentos: Iterable[Documento], *, modelo: str) -> IndiceEmbeddings:
        """Reject embedding artifacts from another model or corpus version."""
        np = _numpy()
        corpus = ordenar_documentos(documentos)
        with np.load(archivo, allow_pickle=False) as datos:
            if str(datos["modelo"].item()) != modelo:
                raise ValueError("El archivo usa otro modelo de embeddings")
            if str(datos["huella"].item()) != huella_corpus(corpus):
                raise ValueError("El archivo de embeddings corresponde a otro corpus")
            por_id = {d.id: d for d in corpus}
            ids = datos["ids"].tolist()
            if len(ids) != len(por_id) or len(set(ids)) != len(ids) or set(ids) != set(por_id):
                raise ValueError("Los ids del archivo no corresponden al corpus")
            return cls([por_id[i] for i in ids], datos["matriz"], modelo=modelo)
