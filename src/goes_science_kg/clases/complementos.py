"""Añade extractos primarios fijados sin alterar el corpus CNXML ni sus ejecuciones."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from goes_science_kg.clases.fuentes import CorpusClases
from goes_science_kg.motor.contratos import Evidencia, huella


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


class CorpusAmpliado(CorpusClases):
    """Las selecciones son bytes literales; cada omisión se muestra con un marcador."""

    def __init__(self, raiz: Path, complemento: Path):
        super().__init__(raiz)
        anterior = self.huella
        self.complemento = complemento
        if complemento.is_symlink() or any(p.is_symlink() for p in complemento.parents):
            raise ValueError("El manifiesto complementario requiere un archivo propio")
        raw = complemento.read_bytes()
        self.adicional = json.loads(raw)
        if self.adicional["version"] != "complemento-fuentes-clases-1":
            raise ValueError("Versión de complemento no admitida")
        if self.adicional["extractor_sha256"] != _sha(Path(__file__).read_bytes()):
            raise ValueError("El extractor del complemento cambió")
        if self.adicional["corpus_base_sha256"] != anterior:
            raise ValueError("El complemento pertenece a otro corpus base")
        self.huella = huella({"base": anterior, "complemento_sha256": _sha(raw)})
        self.huellas_compatibles = {anterior, self.huella}
        self._originales = {complemento.name: raw}
        self._complementarias = {}
        for documento in self.adicional["documentos"]:
            contenido = self._leer_adicional(documento["archivo"])
            self._leer_adicional(documento["licencia_archivo"])
            for extracto in documento["extractos"]:
                texto = self._extraer(contenido, extracto["selecciones"])
                fuente = {
                    **documento["fuente"],
                    "documento": documento["id"],
                    "tipo": "documental",
                    "fuente_primaria": True,
                    "sha256": documento["archivo"]["sha256"],
                    "licencia_sha256": documento["licencia_archivo"]["sha256"],
                    "localizador": {"formato": "extractos_bytes_utf8", "selecciones": extracto["selecciones"]},
                    "verificacion": "contenido_fuente",
                }
                evidencia = Evidencia.crear(documento["id"] + "#" + extracto["id"], texto, fuente, "referencia")
                if evidencia.id in self.evidencias:
                    raise ValueError("Identidad de evidencia complementaria repetida")
                self.evidencias[evidencia.id] = evidencia
                self._complementarias[evidencia.id] = (documento["archivo"], evidencia)

    def _leer_adicional(self, ref):
        nombre = ref["ruta"]
        p = self.complemento.parent / nombre
        if (
            p.is_symlink()
            or any(t.is_symlink() for t in p.parents)
            or not p.resolve().is_relative_to(self.complemento.parent.resolve())
            or not p.is_file()
            or p.stat().st_size > 2 * 1024**2
        ):
            raise ValueError("Fuente complementaria fuera de límites")
        raw = p.read_bytes()
        if len(raw) != ref["bytes"] or _sha(raw) != ref["sha256"]:
            raise ValueError("La fuente complementaria cambió")
        self._originales[nombre] = raw
        return raw

    @staticmethod
    def _extraer(raw, selecciones):
        if not 1 <= len(selecciones) <= 8:
            raise ValueError("Selecciones complementarias fuera de límites")
        partes, ultimo = [], 0
        for inicio, fin in selecciones:
            if type(inicio) is not int or type(fin) is not int or not ultimo <= inicio < fin <= len(raw):
                raise ValueError("Localizador de bytes inválido")
            partes.append(raw[inicio:fin].decode("utf-8"))
            ultimo = fin
        texto = "\n[…]\n".join(partes)
        if not 50 <= len(texto) <= 12000:
            raise ValueError("Extracto complementario fuera de límites")
        return texto

    def verificar(self, evidencia):
        ref = self._complementarias.get(evidencia.id)
        if ref is None:
            original = self.evidencias.get(evidencia.id)
            if original is None or original.model_dump() != evidencia.model_dump():
                raise ValueError("La evidencia CNXML no coincide con el registro primario")
            return super().verificar(evidencia)
        archivo, esperada = ref
        raw = self._leer_adicional(archivo)
        texto = self._extraer(raw, esperada.fuente["localizador"]["selecciones"])
        if texto != evidencia.texto or evidencia.model_dump() != esperada.model_dump():
            raise ValueError("La evidencia complementaria no coincide con sus bytes originales")

    def originales_adicionales(self):
        # Revalida en el momento de compilar, no confía sólo en lo leído al construir el objeto.
        if self.complemento.is_symlink() or self.complemento.read_bytes() != self._originales[self.complemento.name]:
            raise ValueError("El manifiesto complementario cambió")
        for documento in self.adicional["documentos"]:
            self._leer_adicional(documento["archivo"])
            self._leer_adicional(documento["licencia_archivo"])
        return {"data/referencias_complementarias_clases/" + k: v for k, v in self._originales.items()}


def cargar_corpus(base: Path, huella_solicitada=None):
    complemento = base / "data/referencias_complementarias_clases/manifest.json"
    raiz = base / "data/referencias_clases_2026"
    original = CorpusClases(raiz)
    if huella_solicitada == original.huella:
        return original
    corpus = CorpusAmpliado(raiz, complemento) if complemento.is_file() else original
    if huella_solicitada is not None and huella_solicitada != corpus.huella:
        raise ValueError("El corpus solicitado no está disponible")
    return corpus
