"""Fuse rankings and expand graph context under explicit work budgets."""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from collections.abc import Iterable, Sequence

from goes_science_kg.recuperacion.embeddings import IndiceEmbeddings
from goes_science_kg.recuperacion.lexico import IndiceLexico, normalizar
from goes_science_kg.recuperacion.modelos import Documento, Enlace, Resultado, huella_corpus, ordenar_documentos

LOGGER = logging.getLogger(__name__)
VERSION_REFERENCIA = "referencia"


class Buscador:
    """Retrieve locally with BM25, optional cosine similarity, rank fusion, and bounded adjacency."""

    def __init__(
        self,
        documentos: Iterable[Documento],
        *,
        indice_embeddings: IndiceEmbeddings | None = None,
        aristas: Iterable[Enlace] = (),
        constante_rrf: int = 60,
        max_candidatos: int = 100,
        max_vecinos: int = 20,
    ):
        if constante_rrf < 1 or max_candidatos < 1 or max_vecinos < 1:
            raise ValueError("Los límites de recuperación deben ser positivos")
        corpus = ordenar_documentos(documentos)
        self.documentos = {d.id: d for d in corpus}
        self.versiones = {d.version for d in corpus if d.version != VERSION_REFERENCIA}
        self._ids = set(self.documentos)
        self._por_version: dict[str, set[str]] = defaultdict(set)
        self._por_grado: dict[int | None, set[str]] = defaultdict(set)
        self._por_asignatura: dict[tuple[str, ...] | None, set[str]] = defaultdict(set)
        for documento in corpus:
            self._por_version[documento.version].add(documento.id)
            self._por_grado[documento.grado].add(documento.id)
            materia = tuple(normalizar(documento.asignatura.replace("_", " "))) if documento.asignatura else None
            self._por_asignatura[materia].add(documento.id)
        self.lexico = IndiceLexico(corpus)
        self.indice_embeddings = indice_embeddings
        if indice_embeddings is not None:
            indice_embeddings.validar_corpus(corpus)
        self.constante_rrf = constante_rrf
        self.max_candidatos = max_candidatos
        self.max_vecinos = max_vecinos
        self.vecinos: dict[str, list[Enlace]] = defaultdict(list)
        unicas = {(a.origen, a.destino, a.tipo): a for a in aristas}
        for arista in sorted(unicas.values(), key=lambda a: (a.origen, a.destino, a.tipo)):
            if arista.origen in self.documentos and arista.destino in self.documentos:
                self.vecinos[arista.origen].append(arista)
        identidad = {
            "corpus": huella_corpus(corpus),
            "aristas": [a.model_dump() for a in sorted(unicas.values(), key=lambda a: (a.origen, a.destino, a.tipo))],
            "algoritmo": "hibrido-v1",
            "rrf": constante_rrf,
            "max_candidatos": max_candidatos,
            "max_vecinos": max_vecinos,
            "modelo_embeddings": indice_embeddings.modelo if indice_embeddings else None,
            "dimensiones_embeddings": indice_embeddings.dimensiones if indice_embeddings else None,
            "vectores": indice_embeddings.huella_vectores if indice_embeddings else None,
        }
        self.huella = hashlib.sha256(json.dumps(identidad, sort_keys=True).encode("utf-8")).hexdigest()
        LOGGER.info("Índice listo: %d documentos; versiones=%s", len(corpus), sorted(self.versiones))

    def _permitidos(self, version: str | None, grado: int | None, asignatura: str | None) -> set[str]:
        if version is None and len(self.versiones) > 1:
            raise ValueError("El corpus contiene varias mallas: se debe seleccionar una versión")
        if version is not None and version not in self.versiones and version != VERSION_REFERENCIA:
            raise ValueError(f"El corpus no contiene la versión curricular {version}")
        if grado is not None and (not isinstance(grado, int) or not 1 <= grado <= 13):
            raise ValueError("El grado debe estar entre 1 y 13")
        permitidos = self._ids.copy()
        if version is not None:
            permitidos.intersection_update(
                self._por_version.get(version, set()) | self._por_version.get(VERSION_REFERENCIA, set()),
            )
        if grado is not None:
            permitidos.intersection_update(self._por_grado.get(grado, set()) | self._por_grado.get(None, set()))
        if asignatura:
            materia = tuple(normalizar(asignatura.replace("_", " ")))
            permitidos.intersection_update(
                self._por_asignatura.get(materia, set()) | self._por_asignatura.get(None, set()),
            )
        return permitidos

    def buscar(
        self,
        consulta: str,
        *,
        version: str | None = None,
        grado: int | None = None,
        asignatura: str | None = None,
        k: int = 10,
        vector_consulta: Sequence[float] | None = None,
        modelo_embeddings: str | None = None,
        saltos_grafo: int = 1,
    ) -> list[Resultado]:
        """Filter before ranking without silently mixing models or curriculum versions."""

        # Implementation notes:
        # Sin vector usa BM25. Si se solicita búsqueda densa, el modelo y las dimensiones deben
        # coincidir con el índice. Una versión ausente es un error, no una consulta de otra malla.
        if not 0 <= saltos_grafo <= 2:
            raise ValueError("La expansión admite entre cero y dos saltos")
        if k < 1 or k > self.max_candidatos:
            raise ValueError(f"k debe estar entre 1 y {self.max_candidatos}")
        permitidos = self._permitidos(version, grado, asignatura)
        if vector_consulta is not None and (self.indice_embeddings is None or not modelo_embeddings):
            raise ValueError("La búsqueda densa requiere índice y modelo de embeddings explícitos")
        if modelo_embeddings is not None and vector_consulta is None:
            raise ValueError("Falta el vector de consulta para el modelo de embeddings")
        if not consulta.strip() or not permitidos:
            return []
        limite = min(self.max_candidatos, max(k * 3, 20))
        rankings = {"bm25": self.lexico.buscar(consulta, permitidos=permitidos, limite=limite)}
        if vector_consulta is not None and self.indice_embeddings is not None:
            rankings["denso"] = self.indice_embeddings.buscar(
                vector_consulta,
                modelo=modelo_embeddings,
                permitidos=permitidos,
                limite=limite,
            )
        puntos: dict[str, float] = defaultdict(float)
        canales: dict[str, set[str]] = defaultdict(set)
        for canal, ranking in rankings.items():
            for posicion, (documento_id, _) in enumerate(ranking, 1):
                puntos[documento_id] += 1 / (self.constante_rrf + posicion)
                canales[documento_id].add(canal)
        if len(puntos) > self.max_candidatos:
            mejores = sorted(puntos, key=lambda documento_id: (-puntos[documento_id], documento_id))
            puntos = {documento_id: puntos[documento_id] for documento_id in mejores[: self.max_candidatos]}
        self._expandir(puntos, canales, permitidos, saltos_grafo)
        elegidos = sorted(puntos, key=lambda documento_id: (-puntos[documento_id], documento_id))[:k]
        LOGGER.debug(
            "Recuperación: permitidos=%d, candidatos=%d, resultados=%d, saltos=%d",
            len(permitidos),
            len(puntos),
            len(elegidos),
            saltos_grafo,
        )
        return [
            Resultado(
                documento=self.documentos[documento_id].model_copy(deep=True),
                puntaje=puntos[documento_id],
                canales=tuple(sorted(canales[documento_id])),
            )
            for documento_id in elegidos
        ]

    def _expandir(
        self,
        puntos: dict[str, float],
        canales: dict[str, set[str]],
        permitidos: set[str],
        saltos: int,
    ) -> None:
        frontera = dict(sorted(puntos.items(), key=lambda par: (-par[1], par[0]))[:8])
        visitados = set(puntos)
        incorporados = 0
        for _ in range(saltos):
            candidatos: dict[str, float] = {}
            for documento_id, puntaje in frontera.items():
                aristas = sorted(self.vecinos.get(documento_id, ()), key=lambda a: (-a.peso, a.destino))
                for arista in aristas[: self.max_vecinos]:
                    vecino = arista.destino
                    if vecino not in permitidos or vecino in visitados:
                        continue
                    candidatos[vecino] = max(candidatos.get(vecino, 0.0), puntaje * arista.peso * 0.65)
            cupo = min(self.max_vecinos - incorporados, self.max_candidatos - len(puntos))
            if cupo <= 0:
                return
            frontera = dict(sorted(candidatos.items(), key=lambda par: (-par[1], par[0]))[:cupo])
            if not frontera:
                return
            for documento_id, puntaje in frontera.items():
                puntos[documento_id] = puntaje
                canales[documento_id].add("grafo")
            visitados.update(frontera)
            incorporados += len(frontera)
