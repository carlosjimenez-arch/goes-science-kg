"""Test durability, source anchoring, and safe writes independently of cloud services."""

from __future__ import annotations

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier, Event
from types import SimpleNamespace
from typing import TypedDict

import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from test_alineacion import ejecutar
from test_alineacion import entrada as entrada

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.ingesta.extraccion import CatalogoPerfilesPDF, PaginasConPerfil, PerfilPaginaPDF, RegionPDF
from goes_science_kg.motor.ejecuciones import ejecutar_durable


class EstadoPrueba(TypedDict, total=False):
    solicitud: dict
    ejecucion_id: str
    huella_entorno: str
    resultado: dict


class MotorBloqueable:
    def __init__(self):
        self.inicio = Event()
        self.continuar = Event()
        self.llamadas = 0

    def compilar(self, *, checkpointer=None):
        def trabajo(estado):
            self.llamadas += 1
            self.inicio.set()
            assert self.continuar.wait(timeout=5)
            return {"resultado": {"estado": "terminal", "presupuesto": estado["ejecucion_id"]}}

        grafo = StateGraph(EstadoPrueba)
        grafo.add_node("trabajo", trabajo)
        grafo.add_edge(START, "trabajo")
        grafo.add_edge("trabajo", END)
        return grafo.compile(checkpointer=checkpointer)


def test_mismo_checkpoint_no_ejecuta_dos_veces_concurrentemente(tmp_path):
    archivo = tmp_path / "checkpoints.sqlite"
    with closing(sqlite3.connect(archivo)) as db, db:
        SqliteSaver(db).setup()
    motor = MotorBloqueable()
    opciones = dict(
        archivo=archivo,
        solicitud={"consulta": "sintética"},
        thread_id="mismo-thread",
        ejecucion_id="mismo-presupuesto",
        huella_entorno="mismo-entorno",
    )
    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        primera = ejecutor.submit(ejecutar_durable, motor, **opciones)
        assert motor.inicio.wait(timeout=5)
        try:
            with pytest.raises(ValueError, match="curso"):
                ejecutar_durable(motor, **opciones)
        finally:
            motor.continuar.set()
        resultado = primera.result(timeout=5)
    assert motor.llamadas == 1
    assert ejecutar_durable(motor, **opciones)["resultado"] == resultado["resultado"]
    assert motor.llamadas == 1


def test_checkpoint_no_sigue_enlace_sqlite_ni_modifica_original(tmp_path):
    original = tmp_path / "original.sqlite"
    with closing(sqlite3.connect(original)) as db, db:
        db.execute("CREATE TABLE original (id TEXT)")
    antes = original.read_bytes()
    enlace = tmp_path / "checkpoint.sqlite"
    enlace.symlink_to(original)
    motor = MotorBloqueable()
    motor.continuar.set()
    with pytest.raises(ValueError, match="enlace"):
        ejecutar_durable(motor, archivo=enlace, solicitud={}, thread_id="x", ejecucion_id="x", huella_entorno="x")
    assert original.read_bytes() == antes and motor.llamadas == 0


def test_threads_distintos_no_serializan_trabajo_sobre_la_misma_base(tmp_path):
    barrera = Barrier(2)

    class MotorParalelo:
        def compilar(self, *, checkpointer=None):
            def trabajo(estado):
                barrera.wait(timeout=5)
                return {"resultado": {"consulta": estado["solicitud"]["consulta"]}}

            grafo = StateGraph(EstadoPrueba)
            grafo.add_node("trabajo", trabajo)
            grafo.add_edge(START, "trabajo")
            grafo.add_edge("trabajo", END)
            return grafo.compile(checkpointer=checkpointer)

    with ThreadPoolExecutor(max_workers=2) as ejecutor:
        futuros = [
            ejecutor.submit(
                ejecutar_durable,
                MotorParalelo(),
                archivo=tmp_path / "checkpoints.sqlite",
                solicitud={"consulta": i},
                thread_id=str(i),
                ejecucion_id="unidad",
                huella_entorno="entorno",
            )
            for i in range(2)
        ]
        assert {f.result(timeout=6)["resultado"]["consulta"] for f in futuros} == {0, 1}


def test_checkpoint_no_reasigna_el_ledger_aunque_se_conserve_id(tmp_path):
    motor = MotorBloqueable()
    motor.continuar.set()
    motor.modelo = SimpleNamespace(ejecucion_id="unidad", registro=SimpleNamespace(archivo=tmp_path / "ledger.sqlite"))
    opciones = dict(
        archivo=tmp_path / "checkpoints.sqlite",
        solicitud={},
        thread_id="objetivo-1",
        ejecucion_id="unidad",
        huella_entorno="entorno",
    )
    ejecutar_durable(motor, **opciones)
    motor.modelo.registro.archivo = tmp_path / "ledger-vacio.sqlite"
    with pytest.raises(ValueError, match="ledger"):
        ejecutar_durable(motor, **opciones)
    # Un thread nuevo tampoco permite dividir el presupuesto existente entre dos registros.
    with pytest.raises(ValueError, match="ledger"):
        ejecutar_durable(motor, **(opciones | {"thread_id": "objetivo-2"}))
    assert motor.llamadas == 1


def test_ejecucion_exige_el_id_real_del_proveedor_antes_de_escribir(tmp_path):
    motor = MotorBloqueable()
    motor.continuar.set()
    motor.modelo = SimpleNamespace(ejecucion_id="otro-presupuesto")
    with pytest.raises(ValueError, match="proveedor"):
        ejecutar_durable(
            motor,
            archivo=tmp_path / "checkpoints.sqlite",
            solicitud={},
            thread_id="x",
            ejecucion_id="unidad",
            huella_entorno="entorno",
        )
    assert motor.llamadas == 0
    assert list(tmp_path.iterdir()) == []


def test_no_se_reanuda_con_ledger_vacio_sustituido_en_la_misma_ruta(tmp_path):
    ledger = tmp_path / "ledger.sqlite"
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute("CREATE TABLE reservas (id TEXT)")
    motor = MotorBloqueable()
    motor.continuar.set()
    motor.modelo = SimpleNamespace(ejecucion_id="unidad", registro=SimpleNamespace(archivo=ledger))
    opciones = dict(
        archivo=tmp_path / "checkpoints.sqlite",
        solicitud={},
        thread_id="objetivo",
        ejecucion_id="unidad",
        huella_entorno="entorno",
    )
    ejecutar_durable(motor, **opciones)
    ledger.rename(tmp_path / "ledger-anterior.sqlite")
    with closing(sqlite3.connect(ledger)) as db, db:
        db.execute("CREATE TABLE reservas (id TEXT)")
    with pytest.raises(ValueError, match="ledger"):
        ejecutar_durable(motor, **opciones)
    assert motor.llamadas == 1


@pytest.mark.parametrize("campo,nuevo", [("fila_id", "fila-ajena"), ("referente_id", "LOCAL:criterio_ajeno")])
def test_cierre_no_atribuye_dictamenes_a_solicitud_distinta(entrada, campo, nuevo):
    motor = entrada.crear()
    estado = ejecutar(motor, entrada.solicitud)
    estado["solicitud"][campo] = nuevo
    resultado = motor._cerrar(estado)["resultado"]
    assert resultado["estado"] == "abstencion"
    assert any("solicitud" in motivo for motivo in resultado["motivos"])


@pytest.mark.parametrize("origen", ["xlsx", "pdf"])
def test_cierre_rehidrata_fuentes_y_no_respalda_preparacion_stale(entrada, origen):
    motor = entrada.crear()
    estado = ejecutar(motor, entrada.solicitud)
    if origen == "xlsx":
        entrada.archivo.write_bytes(b"XLSX cambiado despues de las lecturas")
    else:
        registro = entrada.repositorio.manifiesto().referencias[entrada.referente.fuente]
        (entrada.repositorio.raiz / registro.archivo_pdf).write_bytes(b"PDF cambiado despues de las lecturas")
    resultado = motor._cerrar(estado)["resultado"]
    assert resultado["estado"] == "abstencion"
    assert any("rehidratar" in motivo for motivo in resultado["motivos"])


def test_terminal_durable_revalida_fuente_antes_de_mostrar_respaldo(entrada, tmp_path):
    motor = entrada.crear()
    opciones = dict(
        archivo=tmp_path / "checkpoint.sqlite",
        solicitud=entrada.solicitud.model_dump(),
        thread_id="par",
        ejecucion_id="presupuesto",
        huella_entorno=motor.huella_entorno,
    )
    assert ejecutar_durable(motor, **opciones)["resultado"]["estado"] == "respaldo_documental_automatico"
    llamadas = len(motor.modelo.llamadas)
    entrada.archivo.write_bytes(b"Fuente cambiada entre ejecuciones")
    with pytest.raises(ValueError, match="rehidratar"):
        ejecutar_durable(motor, **opciones)
    assert len(motor.modelo.llamadas) == llamadas


def test_reanudar_parcial_rehidrata_antes_de_consumir_modelos(entrada, tmp_path):
    motor = entrada.crear()
    archivo = tmp_path / "checkpoint.sqlite"
    entorno = motor.huella_entorno
    datos = {"solicitud": entrada.solicitud.model_dump(), "ejecucion_id": "presupuesto", "huella_entorno": entorno}
    with closing(sqlite3.connect(archivo, check_same_thread=False)) as db, db:
        flujo = motor.compilar(checkpointer=SqliteSaver(db))
        flujo.invoke(datos, {"configurable": {"thread_id": "par"}}, interrupt_after=["contexto"], durability="sync")
    assert motor.modelo.llamadas == []
    entrada.archivo.write_bytes(b"Fuente cambiada entre contexto y revisiones")
    with pytest.raises(ValueError, match="rehidratar"):
        ejecutar_durable(
            motor,
            archivo=archivo,
            solicitud=entrada.solicitud.model_dump(),
            thread_id="par",
            ejecucion_id="presupuesto",
            huella_entorno=entorno,
        )
    assert motor.modelo.llamadas == []


@pytest.mark.parametrize("pagina", [True, 1.0, "1"])
def test_perfil_no_acepta_alias_booleano_o_decimal_de_pagina(entrada, pagina):
    referente = entrada.referente
    perfil = PerfilPaginaPDF(
        id="LOCAL:pagina",
        fuente=referente.fuente,
        sha256=referente.sha256,
        pagina_pdf=1,
        extractor="pdfplumber",
        version="1",
        regiones=(RegionPDF(id="LOCAL:region", bbox=(0, 0, 600, 800)),),
    )
    paginas = PaginasConPerfil(entrada.repositorio, CatalogoPerfilesPDF(schema_version="1.0", perfiles=(perfil,)))
    with pytest.raises(ValueError, match="entero"):
        paginas.pagina(referente.fuente, pagina)


def test_escritura_atomica_conserva_destino_si_falla_codificacion(tmp_path):
    salida = tmp_path / "resultado.json"
    salida.write_text("anterior")
    with pytest.raises(UnicodeEncodeError):
        escribir_texto_generado(salida, "\ud800", extension=".json", raiz=tmp_path / "repo")
    assert salida.read_text() == "anterior"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_destino_resuelve_ancestro_enlazado_y_protege_datos(tmp_path):
    protegida = tmp_path / "repo" / "data" / "evaluacion"
    protegida.mkdir(parents=True)
    enlace = tmp_path / "salidas"
    enlace.symlink_to(protegida, target_is_directory=True)
    with pytest.raises(ValueError, match="evaluación"):
        destino_generado(enlace / "gold.json", extension=".json", raiz=tmp_path / "repo")
    assert not (protegida / "gold.json").exists()
