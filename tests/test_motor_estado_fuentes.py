"""Revalidate resumed and terminal workflows against original physical sources."""

from __future__ import annotations

import copy
import hashlib
import json
import sqlite3
from contextlib import closing
from types import SimpleNamespace

import openpyxl
import pytest
from langgraph.checkpoint.sqlite import SqliteSaver
from test_conocimiento_v4 import _pdf
from test_fuentes_estructuradas import _docx, _fila, _html

from goes_science_kg.motor.calidad import CRITERIOS
from goes_science_kg.motor.ejecuciones import ejecutar_durable
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.recuperacion import Documento, Resultado

OBJETIVO = "Compara los procesos de las plantas con observaciones y representaciones en papel."
CIENCIA = "Plants transform light into chemical energy through photosynthesis."


class BuscadorContado:
    def __init__(self, documentos):
        self.documentos = documentos
        self.llamadas = []

    def buscar(self, consulta, **filtros):
        self.llamadas.append((consulta, filtros))
        return [Resultado(documento=d, puntaje=1, canales=("fixture",)) for d in self.documentos]

    def buscar_fila(self, fila_id, **filtros):
        assert fila_id == "fila-local"
        self.llamadas.append((fila_id, filtros))
        return [Resultado(documento=d, puntaje=1, canales=("fila_fixture",)) for d in self.documentos]


class ModeloContado:
    def __init__(self, modo="respaldo"):
        self.modo = modo
        self.llamadas = []

    def nombre_modelo(self, rol):
        return "simulado-" + rol

    def generar(self, *, rol, sistema, mensaje, esquema):
        self.llamadas.append(rol)
        datos = json.loads(mensaje)["datos_no_confiables"]
        if rol == "redactor":
            reparando = self.llamadas.count("redactor") > 1
            if self.modo == "redactor_falla" or (reparando and self.modo == "reparacion_falla"):
                raise TimeoutError("Redacción simulada no disponible")
            local = next(f for f in datos["fragmentos"] if datos["fuentes"][f["evidencia_id"]]["version"] == "V4")
            referencia = next(
                f for f in datos["fragmentos"] if datos["fuentes"][f["evidencia_id"]]["version"] == "referencia"
            )
            return esquema.model_validate(
                {
                    "afirmaciones": [{"texto": referencia["literal"], "fragmentos_ids": [referencia["id"]]}],
                    "anclaje_curricular": [local["id"]],
                    "actividad": {
                        "objetivo": "Representa los procesos mediante un modelo en papel",
                        "pasos": ["Compara dos representaciones y explica sus diferencias"],
                        "comprobacion": "Justifica una observación mediante el modelo representado",
                        "minutos": 60 if reparando and self.modo == "reparacion_anclaje" else 20,
                        "recursos": ["papel"],
                        "adaptacion_salvador": "Actividad disponible sin conexión con materiales de papel",
                    },
                    "limites": ["Respuesta sintética que no acredita eficacia educativa"],
                }
            )
        rechaza = self.modo in {"rechaza", "reparacion_falla", "reparacion_anclaje"} and rol == "adversarial"
        return esquema.model_validate(
            {
                "aprobado": not rechaza,
                "errores": ["Revisión negativa sintética"] if rechaza else [],
                "criterios": dict.fromkeys(CRITERIOS[rol], True),
                "evidencia_ids": list(datos["fuentes"]),
            }
        )


def _xlsx(archivo, texto):
    libro = openpyxl.Workbook()
    libro.active.title = "Unidad"
    libro.active.append(["Objetivo"])
    libro.active.append([texto])
    libro.save(archivo)
    libro.close()


def _entrada(tmp_path, formato="xlsx", *, modo="respaldo", reparaciones=0):
    local = tmp_path / "malla.xlsx"
    _xlsx(local, OBJETIVO)
    referencia = tmp_path / f"referencia.{formato}"
    if formato == "xlsx":
        _xlsx(referencia, CIENCIA)
        localizador = {"hoja": "Unidad", "fila": 2}
    elif formato == "pdf":
        referencia.write_bytes(_pdf(CIENCIA))
        localizador = {"pagina": 1}
    elif formato == "docx":
        referencia.write_bytes(_docx("<w:tbl>" + _fila(texto=CIENCIA) + "</w:tbl>"))
        localizador = {"localizador": "AC9S3U01"}
    else:
        referencia.write_bytes(_html(f"<p>{CIENCIA} (ACSBL001)</p>"))
        localizador = {"localizador": "ACSBL001"}
    catalogo = {
        i: {"archivo_local": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
        for i, p in (("malla", local), ("guia", referencia))
    }
    fuentes = FuentesVerificadas(catalogo, raiz_fuentes=tmp_path)
    documentos = [
        Documento(
            id="fila-local",
            texto="Texto no autorizado de metadata",
            version="V4",
            grado=7,
            asignatura="biologia",
            fuente={"documento": "malla", "hoja": "Unidad", "fila": 2, "celdas": ["A2"]},
        ),
        Documento(
            id="referencia",
            texto="Texto no autorizado de metadata",
            version="referencia",
            fuente={"documento": "guia", **localizador},
        ),
    ]
    modelo = ModeloContado(modo)
    buscador = BuscadorContado(documentos)
    motor = Motor(buscador, modelo, fuentes=fuentes, max_reparaciones=reparaciones)
    solicitud = {
        "consulta": "Compara los procesos de las plantas con un modelo",
        "version_curriculo": "V4",
        "grado": 7,
        "asignatura": "biologia",
        "fila_id": "fila-local",
    }
    inicial = {"solicitud": solicitud, "ejecucion_id": "presupuesto", "huella_entorno": "entorno-fijo"}
    return SimpleNamespace(**locals())


@pytest.mark.parametrize("formato", ["xlsx", "pdf", "docx", "html"])
@pytest.mark.parametrize("terminal", [False, True])
def test_fuentes_se_rehidratan_en_parcial_y_terminal_sin_buscar_ni_generar(tmp_path, formato, terminal):
    e = _entrada(tmp_path, formato)
    estado = e.motor.compilar().invoke(e.inicial) if terminal else e.inicial | e.motor._contexto(e.inicial)
    if terminal:
        assert estado["resultado"]["estado"] == "respaldado_automaticamente"
    antes = (len(e.buscador.llamadas), len(e.modelo.llamadas))
    e.motor.validar_estado(estado)
    assert (len(e.buscador.llamadas), len(e.modelo.llamadas)) == antes
    e.referencia.write_bytes(b"Fuente sustituida despues del checkpoint")
    with pytest.raises(ValueError, match="rehidratar"):
        e.motor.validar_estado(estado)
    assert (len(e.buscador.llamadas), len(e.modelo.llamadas)) == antes


def test_cambio_xlsx_local_o_bloqueo_actual_invalida_terminal(tmp_path):
    e = _entrada(tmp_path)
    estado = e.motor.compilar().invoke(e.inicial)
    e.fuentes.bloqueos_curriculares["fila-local"] = "Alerta científica confirmada"
    with pytest.raises(ValueError, match="bloqueos actuales"):
        e.motor.validar_estado(estado)
    e.fuentes.bloqueos_curriculares.clear()
    e.local.write_bytes(b"Malla sustituida")
    with pytest.raises(ValueError, match="rehidratar"):
        e.motor.validar_estado(estado)


@pytest.mark.parametrize(
    "alteracion", ["estado", "propuesta", "iteraciones", "ejecucion_id", "version", "juez", "huella"]
)
def test_terminal_no_confia_en_bandera_dictamenes_o_identidad_persistidos(tmp_path, alteracion):
    e = _entrada(tmp_path)
    estado = e.motor.compilar().invoke(e.inicial)
    if alteracion == "estado":
        estado["resultado"]["estado"] = "abstencion"
    elif alteracion == "propuesta":
        estado["resultado"]["propuesta"]["actividad"]["minutos"] = 21
    elif alteracion == "version":
        estado["resultado"]["version_curriculo"] = "V3"
    elif alteracion == "juez":
        estado["cientifico"]["modelo"] = "modelo-ajeno"
    elif alteracion == "huella":
        estado["cientifico"]["huella_propuesta"] = "f" * 64
    else:
        estado["resultado"][alteracion] = "otra-ejecucion" if alteracion == "ejecucion_id" else 9
    antes = (len(e.buscador.llamadas), len(e.modelo.llamadas))
    with pytest.raises(ValueError, match="terminal|modelo"):
        e.motor.validar_estado(estado)
    assert (len(e.buscador.llamadas), len(e.modelo.llamadas)) == antes


@pytest.mark.parametrize("campo", ["texto", "fuente", "fragmento", "duplicada"])
def test_contexto_parcial_no_acepta_texto_procedencia_o_fragmentos_suplantados(tmp_path, campo):
    e = _entrada(tmp_path)
    estado = e.inicial | e.motor._contexto(e.inicial)
    if campo == "texto":
        estado["evidencias"][0]["texto"] = "Contenido inventado que no procede de la fuente física"
    elif campo == "fuente":
        estado["evidencias"][0]["fuente"]["sha256"] = "0" * 64
    elif campo == "fragmento":
        estado["fragmentos"][0]["literal"] = "Un fragmento inventado sin respaldo en la fuente física"
    else:
        estado["evidencias"].append(copy.deepcopy(estado["evidencias"][0]))
    with pytest.raises(ValueError):
        e.motor.validar_estado(estado)
    assert e.modelo.llamadas == []


@pytest.mark.parametrize("modo", ["rechaza", "redactor_falla", "reparacion_falla", "reparacion_anclaje"])
def test_abstenciones_validas_y_dictamenes_previos_se_conservan_tras_reparar(tmp_path, modo):
    e = _entrada(tmp_path, modo=modo, reparaciones=1)
    estado = e.motor.compilar().invoke(e.inicial)
    assert estado["resultado"]["estado"] == "abstencion"
    if modo in {"reparacion_falla", "reparacion_anclaje"}:
        assert estado["cientifico"] is not None
        if modo == "reparacion_falla":
            assert estado["propuesta"] is None
        else:
            assert estado["propuesta"]["actividad"]["minutos"] == 60
    antes = copy.deepcopy(estado)
    llamadas = list(e.modelo.llamadas)
    e.motor.validar_estado(estado)
    assert estado == antes and e.modelo.llamadas == llamadas


def test_helper_durable_no_devuelve_terminal_stale_ni_repite_modelos(tmp_path):
    e = _entrada(tmp_path, "docx")
    argumentos = dict(
        archivo=tmp_path / "checkpoint.sqlite",
        solicitud=e.solicitud,
        thread_id="sesion",
        ejecucion_id="presupuesto",
        huella_entorno="entorno-fijo",
    )
    uno = ejecutar_durable(e.motor, **argumentos)
    assert ejecutar_durable(e.motor, **argumentos) == uno
    llamadas = list(e.modelo.llamadas)
    e.referencia.write_bytes(b"DOCX cambiado")
    with pytest.raises(ValueError, match="rehidratar"):
        ejecutar_durable(e.motor, **argumentos)
    assert e.modelo.llamadas == llamadas


def test_reanudar_parcial_con_instancia_nueva_verifica_sha_antes_de_modelos(tmp_path):
    e = _entrada(tmp_path, "pdf")
    archivo = tmp_path / "checkpoint.sqlite"
    opciones = {"configurable": {"thread_id": "sesion"}}
    with closing(sqlite3.connect(archivo, check_same_thread=False)) as db, db:
        flujo = e.motor.compilar(checkpointer=SqliteSaver(db))
        flujo.invoke(e.inicial, opciones, interrupt_after=["contexto"], durability="sync")
    assert e.modelo.llamadas == []
    consultas = list(e.buscador.llamadas)
    e.referencia.write_bytes(b"PDF sustituido entre contexto y redaccion")
    e.motor.fuentes = FuentesVerificadas(e.catalogo, raiz_fuentes=tmp_path)
    with pytest.raises(ValueError, match="rehidratar"):
        ejecutar_durable(
            e.motor,
            archivo=archivo,
            solicitud=e.solicitud,
            thread_id="sesion",
            ejecucion_id="presupuesto",
            huella_entorno="entorno-fijo",
        )
    assert e.modelo.llamadas == [] and e.buscador.llamadas == consultas
