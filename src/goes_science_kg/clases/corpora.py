"""Registro de versiones de fuentes: conserva las usadas y permite añadir evidencia sin reescribirlas."""

from __future__ import annotations

import json

from goes_science_kg.clases.complementos import CorpusAmpliado
from goes_science_kg.clases.complementos import cargar_corpus as cargar_anterior
from goes_science_kg.clases.fuentes import CorpusClases
from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.recuperacion.lexico import IndiceLexico
from goes_science_kg.recuperacion.modelos import Documento


def _indexar(corpus):
    corpus.indice = IndiceLexico(
        Documento(id=e.id, texto=e.fuente["titulo"] + " " + e.texto, fuente=e.fuente, version=e.version)
        for e in corpus.evidencias.values()
    )
    return corpus


class ColeccionCorpora:
    def __init__(self, corpora, actual, registro, registro_raw):
        self.corpora = corpora
        self.actual = actual
        self.huella = actual.huella
        self.huellas_compatibles = {h for c in corpora for h in c.huellas_compatibles}
        self.manifest, self.manifest_bytes = actual.manifest, actual.manifest_bytes
        self._registro, self._registro_raw = registro, registro_raw
        self._propietarios = {}
        for c in corpora:
            for id_, e in c.evidencias.items():
                anterior = self._propietarios.get(id_)
                if anterior and anterior.evidencias[id_].model_dump() != e.model_dump():
                    raise ValueError("Dos versiones atribuyen contenido diferente a la misma identidad de fuente")
                self._propietarios[id_] = c

    def verificar(self, evidencia):
        c = self._propietarios.get(evidencia.id)
        if c is None:
            raise ValueError("La evidencia no pertenece a las versiones registradas")
        c.verificar(evidencia)

    def _leer(self, ref):
        return self.actual._leer(ref)

    def originales_adicionales(self):
        if self._registro.read_bytes() != self._registro_raw:
            raise ValueError("El registro de fuentes cambió durante la compilación")
        salida = {"data/referencias_complementarias_clases/registro.json": self._registro_raw}
        for c in self.corpora:
            for nombre, raw in c.originales_adicionales().items():
                if nombre in salida and salida[nombre] != raw:
                    raise ValueError("Dos versiones intentan reemplazar el mismo original científico")
                salida[nombre] = raw
        return salida


def cargar_corpus(base, huella_solicitada=None, *, todos=False):
    from goes_science_kg.clases.compilacion import leer_propio

    archivo = base / "data/referencias_complementarias_clases/registro.json"
    if not archivo.is_file():
        return cargar_anterior(base, huella_solicitada)
    raw = leer_propio(base, archivo.relative_to(base).as_posix()).read_bytes()
    cfg = json.loads(raw)
    if cfg["version"] != "registro-corpora-clases-1":
        raise ValueError("Registro de corpus incompatible")
    refs = cfg["manifiestos"]
    hashes = [r["corpus_sha256"] for r in refs]
    if len(hashes) != len(set(hashes)) or cfg["vigente"] not in hashes:
        raise ValueError("Versiones de corpus repetidas o falta la versión vigente")
    if huella_solicitada and huella_solicitada not in hashes:
        c = CorpusClases(base / "data/referencias_clases_2026")
        if c.huella != huella_solicitada:
            raise ValueError("El corpus solicitado no está registrado")
        return c
    objetivo = huella_solicitada or cfg["vigente"]
    corpora, actual = [], None
    for ref in refs:
        if not todos and ref["corpus_sha256"] != objetivo:
            continue
        p = leer_propio(base, ref["ruta"])
        if sha(p.read_bytes()) != ref["sha256"]:
            raise ValueError("El manifest científico registrado cambió")
        c = CorpusAmpliado(base / "data/referencias_clases_2026", p)
        if c.huella != ref["corpus_sha256"]:
            raise ValueError("La versión científica no corresponde al registro")
        corpora.append(c)
        if c.huella == objetivo:
            actual = c
    if actual is None:
        raise ValueError("No se pudo cargar el corpus requerido")
    return ColeccionCorpora(corpora, actual, archivo, raw) if todos else _indexar(actual)
