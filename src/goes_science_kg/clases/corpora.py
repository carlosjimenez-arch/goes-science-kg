"""Registro de versiones de fuentes: conserva las usadas y permite añadir evidencia sin reescribirlas."""

from __future__ import annotations

import json

from goes_science_kg.clases.complementos import CorpusAmpliado
from goes_science_kg.clases.complementos import cargar_corpus as cargar_anterior
from goes_science_kg.clases.fuentes import CorpusClases
from goes_science_kg.materiales.compilacion import sha
from goes_science_kg.motor.contratos import huella
from goes_science_kg.recuperacion.lexico import IndiceLexico
from goes_science_kg.recuperacion.modelos import Documento


def _indexar(corpus):
    corpus.indice = IndiceLexico(
        Documento(id=e.id, texto=e.fuente["titulo"] + " " + e.texto, fuente=e.fuente, version=e.version)
        for e in corpus.evidencias.values()
    )
    return corpus


class ColeccionCorpora:
    def __init__(self, corpora, actual, registro, registro_raw, *, manifiestos=None, compatibles=()):
        self.corpora = corpora
        self.actual = actual
        self.huella = actual.huella
        self.huellas_compatibles = {h for c in corpora for h in c.huellas_compatibles} | set(compatibles)
        self.manifest, self.manifest_bytes = actual.manifest, actual.manifest_bytes
        self._registro, self._registro_raw = registro, registro_raw
        self._manifiestos = manifiestos or {}
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
        for archivo, raw in self._manifiestos.items():
            if archivo.is_symlink() or any(p.is_symlink() for p in archivo.parents) or archivo.read_bytes() != raw:
                raise ValueError("El manifest científico registrado cambió durante la compilación")
            salida["data/referencias_complementarias_clases/" + archivo.name] = raw
        for c in self.corpora:
            for nombre, raw in c.originales_adicionales().items():
                if nombre in salida and salida[nombre] != raw:
                    raise ValueError("Dos versiones intentan reemplazar el mismo original científico")
                salida[nombre] = raw
        return salida


def _incluido(anterior, actual):
    """Una ampliación sólo comparte objetos cuando conserva metadatos y rangos exactos."""
    documentos = {d["id"]: d for d in actual["documentos"]}
    if len(documentos) != len(actual["documentos"]):
        return False
    vistos = set()
    for d in anterior["documentos"]:
        if d["id"] in vistos:
            return False
        vistos.add(d["id"])
        presente = documentos.get(d["id"])
        if presente is None or {k: v for k, v in d.items() if k != "extractos"} != {
            k: v for k, v in presente.items() if k != "extractos"
        }:
            return False
        extractos = {e["id"]: e for e in presente["extractos"]}
        if len(extractos) != len(presente["extractos"]) or len({e["id"] for e in d["extractos"]}) != len(
            d["extractos"]
        ):
            return False
        if any(extractos.get(e["id"]) != e for e in d["extractos"]):
            return False
    return True


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
    if todos:
        manifiestos, datos = {}, {}
        for ref in refs:
            p = leer_propio(base, ref["ruta"])
            contenido = p.read_bytes()
            if sha(contenido) != ref["sha256"]:
                raise ValueError("El manifest científico registrado cambió")
            manifiestos[p], datos[ref["corpus_sha256"]] = contenido, json.loads(contenido)
        actual_ref = next(r for r in refs if r["corpus_sha256"] == objetivo)
        actual = CorpusAmpliado(base / "data/referencias_clases_2026", leer_propio(base, actual_ref["ruta"]))
        for ref in refs:
            m = datos[ref["corpus_sha256"]]
            if (
                m["version"] != actual.adicional["version"]
                or m["extractor_sha256"] != actual.adicional["extractor_sha256"]
                or m["corpus_base_sha256"] != actual.adicional["corpus_base_sha256"]
                or huella({"base": m["corpus_base_sha256"], "complemento_sha256": ref["sha256"]})
                != ref["corpus_sha256"]
            ):
                raise ValueError("La versión científica no corresponde al registro")
        if all(_incluido(m, actual.adicional) for m in datos.values()):
            return ColeccionCorpora([actual], actual, archivo, raw, manifiestos=manifiestos, compatibles=hashes)
        # Si una versión no es una ampliación literal, mantiene la reunión completa y sus conflictos.
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
