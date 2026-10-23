"""Los extractos adicionales se atan a bytes, licencia, código y corpus anterior."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from goes_science_kg.clases import complementos
from goes_science_kg.clases.complementos import CorpusAmpliado, cargar_corpus


@pytest.fixture
def complemento(tmp_path, monkeypatch):
    def inicializar(self, raiz):
        self.raiz = raiz
        self.huella = "b" * 64
        self.evidencias = {}
        self.manifest = {}
        self.manifest_bytes = b"{}"

    monkeypatch.setattr(complementos.CorpusClases, "__init__", inicializar)
    d = tmp_path / "data/referencias_complementarias_clases"
    d.mkdir(parents=True)
    raw = (
        b"gtsd:Paleogene\n    time:hasBeginning [ gtsd:inMYA 66.00 ; ] ;\n    time:hasEnd [ gtsd:inMYA 23.04 ; ] ;\n.\n"
    )
    licencia = b"Creative Commons Attribution 4.0 International"

    def ref(nombre, contenido):
        (d / nombre).write_bytes(contenido)
        return {"ruta": nombre, "bytes": len(contenido), "sha256": hashlib.sha256(contenido).hexdigest()}

    manifest = {
        "version": "complemento-fuentes-clases-1",
        "extractor_sha256": hashlib.sha256(Path(complementos.__file__).read_bytes()).hexdigest(),
        "corpus_base_sha256": "b" * 64,
        "documentos": [
            {
                "id": "ICS:revision",
                "archivo": ref("chart.ttl", raw),
                "licencia_archivo": ref("LICENSE", licencia),
                "fuente": {"titulo": "ICS chart", "licencia": "CC BY 4.0", "institucion": "ICS"},
                "extractos": [{"id": "Paleogene", "selecciones": [[0, len(raw)]]}],
            }
        ],
    }
    p = d / "manifest.json"
    p.write_text(json.dumps(manifest))
    return tmp_path, p, manifest


def test_complemento_preserva_huella_original_y_verifica_extractos(complemento):
    base, p, _ = complemento
    c = CorpusAmpliado(base / "data/referencias_clases_2026", p)
    e = next(iter(c.evidencias.values()))
    c.verificar(e)
    assert "66.00" in e.texto and e.fuente["localizador"]["formato"] == "extractos_bytes_utf8"
    assert c.huella != "b" * 64 and c.huellas_compatibles == {"b" * 64, c.huella}
    assert len(c.originales_adicionales()) == 3
    assert cargar_corpus(base, "b" * 64).huella == "b" * 64
    assert cargar_corpus(base, c.huella).huella == c.huella
    with pytest.raises(ValueError, match="no está disponible"):
        cargar_corpus(base, "c" * 64)


@pytest.mark.parametrize("archivo", ["chart.ttl", "LICENSE", "manifest.json"])
def test_rechaza_modificaciones_posteriores(complemento, archivo):
    base, p, _ = complemento
    c = CorpusAmpliado(base / "data/referencias_clases_2026", p)
    f = p.parent / archivo
    f.write_bytes(f.read_bytes() + b"alterado")
    with pytest.raises(ValueError, match="cambi"):
        c.originales_adicionales()


def test_rechaza_evidencia_con_metadatos_adulterados(complemento):
    base, p, _ = complemento
    c = CorpusAmpliado(base / "data/referencias_clases_2026", p)
    e = next(iter(c.evidencias.values()))
    fuente = deepcopy(e.fuente)
    fuente["licencia"] = "otra"
    with pytest.raises(ValueError, match="no coincide"):
        c.verificar(e.model_copy(update={"fuente": fuente}))


@pytest.mark.parametrize("clave", ["extractor_sha256", "corpus_base_sha256"])
def test_rechaza_cambios_de_codigo_o_de_corpus(complemento, clave):
    base, p, manifest = complemento
    manifest[clave] = "c" * 64
    p.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        CorpusAmpliado(base / "data/referencias_clases_2026", p)


@pytest.mark.parametrize("rangos", [[[3, 2]], [[-1, 20]], [[0, 1000]], [[0, 90], [50, 100]], [[True, 80]]])
def test_rechaza_localizadores_imposibles_o_solapados(rangos):
    with pytest.raises(ValueError):
        CorpusAmpliado._extraer(b"a" * 100, rangos)


def test_selecciones_muestran_omision_sin_fabricar_texto():
    raw = b"a" * 70 + b" OMITIDO " + b"b" * 70
    texto = CorpusAmpliado._extraer(raw, [[0, 70], [79, len(raw)]])
    assert texto == "a" * 70 + "\n[…]\n" + "b" * 70


def _registrar_versiones(base, archivo, manifest):
    from goes_science_kg.materiales.compilacion import serializar, sha

    segundo = deepcopy(manifest)
    segundo["documentos"].append(deepcopy(manifest["documentos"][0]))
    segundo["documentos"][-1]["id"] = "ICS:version_adicional"
    segundo_archivo = archivo.with_name("manifest_r2.json")
    segundo_archivo.write_bytes(serializar(segundo))
    versiones = [CorpusAmpliado(base / "data/referencias_clases_2026", p) for p in (archivo, segundo_archivo)]
    registro = {
        "version": "registro-corpora-clases-1",
        "vigente": versiones[-1].huella,
        "manifiestos": [
            {"ruta": p.relative_to(base).as_posix(), "sha256": sha(p.read_bytes()), "corpus_sha256": c.huella}
            for p, c in zip((archivo, segundo_archivo), versiones, strict=True)
        ],
    }
    archivo.with_name("registro.json").write_bytes(serializar(registro))
    return versiones, registro


def test_registro_carga_version_anterior_sin_reescribir_y_reune_originales(complemento):
    from goes_science_kg.clases.corpora import cargar_corpus as cargar_version

    base, p, manifest = complemento
    versiones, _ = _registrar_versiones(base, p, manifest)
    assert cargar_version(base).huella == versiones[-1].huella
    assert cargar_version(base, versiones[0].huella).huella == versiones[0].huella
    assert cargar_version(base, "b" * 64).huella == "b" * 64
    reunion = cargar_version(base, todos=True)
    for version in versiones:
        for evidencia in version.evidencias.values():
            reunion.verificar(evidencia)
    originales = reunion.originales_adicionales()
    assert len(originales) == 5
    p.with_name("registro.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="registro de fuentes cambió"):
        reunion.originales_adicionales()


def test_registro_rechaza_version_adulterada_aunque_sea_la_seleccionada(complemento):
    from goes_science_kg.clases.corpora import cargar_corpus as cargar_version

    base, p, manifest = complemento
    _registrar_versiones(base, p, manifest)
    segundo = p.with_name("manifest_r2.json")
    segundo.write_bytes(segundo.read_bytes() + b" ")
    with pytest.raises(ValueError, match="manifest científico registrado cambió"):
        cargar_version(base)


def test_ampliaciones_literales_comparten_una_sola_instancia_y_revalidan_manifests(complemento, monkeypatch):
    from goes_science_kg.clases import corpora

    base, archivo, manifest = complemento
    versiones, _ = _registrar_versiones(base, archivo, manifest)
    original, cargas = corpora.CorpusAmpliado, []

    def contar(*args):
        cargas.append(args[1])
        return original(*args)

    monkeypatch.setattr(corpora, "CorpusAmpliado", contar)
    reunion = corpora.cargar_corpus(base, todos=True)
    assert len(cargas) == 1
    for version in versiones:
        assert version.huella in reunion.huellas_compatibles
        for evidencia in version.evidencias.values():
            reunion.verificar(evidencia)
    archivo.write_bytes(archivo.read_bytes() + b" ")
    with pytest.raises(ValueError, match="manifest científico registrado cambió"):
        reunion.originales_adicionales()
