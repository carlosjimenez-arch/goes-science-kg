"""Contratos de subida y descarga de todo el producto desde GCS, con un almacén simulado en memoria."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from goes_science_kg.clases.complementaria_publicacion import RECIBO as RECIBO_COMPLEMENTOS
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.operacion.sincronizacion import RECIBO_CORPUS, Sincronizador

CONFIGURACION = {"rutas": ["data", "insumos"], "patrones": [], "max_bytes_sin_comprimir": 2 * 1024**3}


class AlmacenMemoria:
    """Imita AlmacenGCS: crea generaciones nuevas y verifica SHA y tamaño al descargar."""

    def __init__(self):
        self.objetos = {}
        self.configuracion = SimpleNamespace(ruta=lambda nombre: f"gs://prueba/ciencias/v4/{nombre}")

    def crear(self, archivo: Path, nombre: str) -> dict:
        uri = self.configuracion.ruta(nombre)
        if uri in self.objetos:
            raise ValueError("El objeto ya existe")
        contenido = archivo.read_bytes()
        self.objetos[uri] = contenido
        return {
            "uri": uri,
            "generacion": str(len(self.objetos)),
            "sha256": hashlib.sha256(contenido).hexdigest(),
            "bytes": len(contenido),
        }

    def descargar(self, ref: dict, destino: Path) -> None:
        contenido = self.objetos[ref["uri"]]
        if hashlib.sha256(contenido).hexdigest() != ref["sha256"] or len(contenido) != ref["bytes"]:
            raise ValueError("El objeto no corresponde al recibo")
        destino.write_bytes(contenido)


def _repo(raiz: Path) -> Path:
    (raiz / "data/producto").mkdir(parents=True)
    (raiz / "data/producto/actual.json").write_text('{"snapshot_id": "s"}')
    (raiz / "insumos").mkdir()
    (raiz / "insumos/malla.txt").write_text("fila original")
    (raiz / "config").mkdir()
    return raiz


def test_publicar_adopta_el_recibo_solo_tras_restaurar_y_un_consumidor_nuevo_lo_recupera(tmp_path):
    almacen = AlmacenMemoria()
    origen = _repo(tmp_path / "origen")
    resultado = Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "trabajo")
    assert resultado["restauracion_verificada"] and resultado["archivos"] == 2
    recibo = json.loads((origen / RECIBO_CORPUS).read_bytes())
    assert recibo["paquete"]["sha256"] == resultado["paquete"]

    consumidor = tmp_path / "consumidor"
    (consumidor / "config").mkdir(parents=True)
    (consumidor / RECIBO_CORPUS).write_bytes((origen / RECIBO_CORPUS).read_bytes())
    sincronizador = Sincronizador(consumidor, almacen)
    assert sincronizador.estado()["corpus"]["estado"] == "ausente"
    acciones = sincronizador.sincronizar()
    assert "corpus" in acciones["acciones"] and acciones["estado"]["corpus"]["estado"] == "completo"
    assert (consumidor / "insumos/malla.txt").read_text() == "fila original"
    assert sincronizador.verificar_corpus()["identicos"] == 2
    assert sincronizador.sincronizar()["acciones"] == {}


def test_una_segunda_publicacion_conserva_el_recibo_anterior_en_el_trabajo(tmp_path):
    almacen = AlmacenMemoria()
    origen = _repo(tmp_path / "origen")
    primero = Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "t1")
    (origen / "data/producto/nuevo.json").write_text("{}")
    segundo = Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "t2")
    assert segundo["recibo_anterior"] == primero["paquete"] != segundo["paquete"]
    assert json.loads((tmp_path / "t2/recibo_anterior.json").read_bytes())["paquete"]["sha256"] == primero["paquete"]


def test_estado_parcial_o_divergente_no_se_sobrescribe(tmp_path):
    almacen = AlmacenMemoria()
    origen = _repo(tmp_path / "origen")
    Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "trabajo")
    consumidor = tmp_path / "consumidor"
    (consumidor / "config").mkdir(parents=True)
    (consumidor / RECIBO_CORPUS).write_bytes((origen / RECIBO_CORPUS).read_bytes())
    (consumidor / "insumos").mkdir()
    with pytest.raises(ValueError, match="incompleto"):
        Sincronizador(consumidor, almacen).sincronizar()


def test_verificacion_detecta_archivos_alterados(tmp_path):
    almacen = AlmacenMemoria()
    origen = _repo(tmp_path / "origen")
    Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "trabajo")
    (origen / "insumos/malla.txt").write_text("fila alterada")
    resultado = Sincronizador(origen, almacen).verificar_corpus()
    assert resultado["total_distintos"] == 1 and resultado["distintos"] == ["insumos/malla.txt"]


def test_publicar_exige_una_carpeta_de_trabajo_nueva(tmp_path):
    origen = _repo(tmp_path / "origen")
    trabajo = tmp_path / "trabajo"
    trabajo.mkdir()
    (trabajo / "otro.zip").write_text("x")
    with pytest.raises(ValueError, match="nueva o estar vacía"):
        Sincronizador(origen, AlmacenMemoria()).publicar_corpus(CONFIGURACION, trabajo)


def test_recupera_complementos_faltantes_en_un_consumidor_con_corpus_existente(tmp_path):
    almacen = AlmacenMemoria()
    origen = _repo(tmp_path / "origen")
    doc = {"version": "complementos-ciencias-1", "clases": {}, "unidades": {}, "retenidos": []}
    doc["id"] = sha(serializar(doc))
    rel = "data/clases_v4/complementaria/publicacion/complementos-prueba.json"
    archivo = origen / rel
    archivo.parent.mkdir(parents=True)
    archivo.write_bytes(serializar(doc))
    recibo = {"ruta": rel, "sha256": sha(archivo.read_bytes()), "id": doc["id"]}
    (origen / RECIBO_COMPLEMENTOS).write_text(json.dumps(recibo))
    Sincronizador(origen, almacen).publicar_corpus(CONFIGURACION, tmp_path / "trabajo")

    consumidor = _repo(tmp_path / "consumidor")
    for recibo_rel in (RECIBO_CORPUS, RECIBO_COMPLEMENTOS):
        (consumidor / recibo_rel).write_bytes((origen / recibo_rel).read_bytes())
    local = consumidor / "data/producto/actual.json"
    local.write_text('{"snapshot_id": "conservar-local"}')
    sync = Sincronizador(consumidor, almacen)
    assert sync.estado()["corpus"]["estado"] == "completo"
    assert sync.estado()["complementos"]["estado"] == "ausente"
    resultado = sync.sincronizar()
    assert resultado["acciones"]["complementos"]["id"] == doc["id"]
    assert resultado["estado"]["complementos"]["estado"] == "vigente"
    assert local.read_text() == '{"snapshot_id": "conservar-local"}'
    (consumidor / rel).write_text("alterado")
    assert sync.estado()["complementos"]["estado"] == "distinto"
    with pytest.raises(ValueError, match="complementos locales"):
        sync.sincronizar()
    assert (consumidor / rel).read_text() == "alterado"
