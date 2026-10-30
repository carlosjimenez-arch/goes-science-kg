"""Test simulated reviews and published evidence conditioned on actual V4 rows."""

from __future__ import annotations

import copy
import hashlib
import json
import shutil
from io import BytesIO
from types import SimpleNamespace

import pytest
from pypdf import PdfReader, PdfWriter
from test_conocimiento_v4 import _concepto, _pais, _pdf, _referencia
from test_juicios_conocimiento import LectoresSimulados
from test_producto_v4 import catalogo as catalogo
from test_producto_v4 import curriculo as curriculo

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.modelos import TipoArista, TipoNodo
from goes_science_kg.motor.conocimiento import MotorConocimiento
from goes_science_kg.motor.contratos import huella
from goes_science_kg.producto import almacen, cargar_producto, construir_producto
from goes_science_kg.producto._juicios_contratos import SolicitudConocimiento
from goes_science_kg.producto.conocimiento import EdicionEsperada, PoliticaConocimiento, generar_candidatos_conocimiento
from goes_science_kg.producto.conocimiento_publicado import (
    ArchivoConocimiento,
    crear_archivo_conocimiento,
    validar_archivo_conocimiento,
)
from goes_science_kg.producto.consulta_conocimiento import fuentes_del_archivo, rehidratar_evidencias
from goes_science_kg.producto.juicios import PreparadorConocimiento
from goes_science_kg.producto.runtime import cargar_runtime


@pytest.fixture(scope="module")
def preparado(tmp_path_factory, curriculo, catalogo):
    base = tmp_path_factory.mktemp("fuentes-juicio-producto")
    documento, objetivo, _ = _pais(base)
    escritor = PdfWriter()
    for texto in (
        "Water and temperature, first synthetic objective.",
        "Water and measurement, second synthetic objective.",
    ):
        escritor.add_page(PdfReader(BytesIO(_pdf(texto))).pages[0])
    contenido = BytesIO()
    escritor.write(contenido)
    (base / "referencia.pdf").write_bytes(contenido.getvalue())
    digest = hashlib.sha256(contenido.getvalue()).hexdigest()
    documento.props["sha256"] = digest
    a = objetivo.model_copy(deep=True, update={"id": "objetivo-extranjero-uno"})
    b = objetivo.model_copy(deep=True, update={"id": "objetivo-extranjero-dos"})
    b.fuente.pagina = 2
    referencia = _referencia(_concepto(), documento, a, b)
    informe = generar_candidatos_conocimiento(
        curriculo,
        referencia,
        raiz_v4=ruta("insumos/v4"),
        raiz_historica=base,
        politica=PoliticaConocimiento(
            ediciones_por_documento={
                "documento-pais": EdicionEsperada(sha256=digest, version_documental="2013"),
            }
        ),
    )
    fuentes = fuentes_del_curriculo(
        curriculo,
        raiz_v4=ruta("insumos/v4"),
        raiz_historica=base,
        catalogo_historico={"documento-pais": documento.props},
    )
    motor = MotorConocimiento(
        PreparadorConocimiento(curriculo, informe, referencia, fuentes, max_caracteres=40000), LectoresSimulados()
    )
    decisiones = {f.fila_id: f for f in catalogo.filas}
    filas = {f.id: f for f in curriculo.filas}
    candidatos = []
    for grado, objetivo_id in ((6, a.id), (7, b.id)):
        candidatos.append(
            next(
                c
                for c in informe.candidatos
                if c.tipo == "contraste_pais"
                and c.destino == objetivo_id
                and filas[c.fila_id].grado == grado
                and decisiones[c.fila_id].disciplinas == ("fisica",)
            )
        )
    estados = [
        motor.compilar().invoke(
            {"solicitud": SolicitudConocimiento(candidato_id=c.id).model_dump(), "ejecucion_id": "sintetica-" + str(i)}
        )
        for i, c in enumerate(candidatos)
    ]
    assert all(e["resultado"]["estado"] == "respaldado" for e in estados)
    archivo = crear_archivo_conocimiento(motor, estados)
    destino = base / "producto"
    construir_producto(
        curriculo,
        catalogo,
        destino=destino,
        conocimiento=archivo,
        modelos_conocimiento=archivo.modelos,
        raiz_v4=ruta("insumos/v4"),
        raiz_historica=base,
    )
    return SimpleNamespace(**locals())


def modificar(archivo, funcion):
    datos = archivo.model_dump(mode="json")
    funcion(datos)
    datos["huella_archivo"] = huella({k: v for k, v in datos.items() if k != "huella_archivo"})
    return ArchivoConocimiento.model_validate(datos)


def test_snapshot_producto2_conoce_evidencia_y_relaciones_reificadas(preparado):
    p = cargar_producto(preparado.destino)
    assert p.conocimiento == preparado.archivo
    assert p.manifest.version == "producto-2" and "conocimiento.json" in p.manifest.sha256
    relaciones = [n for n in p.nodos if n.tipo == TipoNodo.RELACION_CURRICULAR]
    assert len(relaciones) == 2
    assert all(n.props["ambito"] == "fila_curricular" and n.props["no_es_fuente_primaria"] for n in relaciones)
    assert sum(a.tipo == TipoArista.EN_CONTEXTO for a in p.aristas) == 2
    assert not any(a.tipo in {TipoArista.TRABAJA, TipoArista.PRERREQUISITO_DE, TipoArista.CUBRE} for a in p.aristas)
    assert len(preparado.motor.modelo.llamadas) == 8  # Sólo llamadas al puerto sintético de la prueba.
    assert p.diagnostico["conocimiento"]["filas_con_juicio"] == 2
    assert p.diagnostico["conocimiento"]["filas_sin_juicio"] == 1018


def test_evidencia_deduplicada_se_resuelve_sin_json_dentro_de_cada_expediente(preparado):
    archivo = preparado.archivo
    assert all("evidencias" not in e.preparacion for e in archivo.expedientes.values())
    assert len(archivo.evidencias) == len({i for e in archivo.expedientes.values() for i in e.evidencias_ids})
    validar_archivo_conocimiento(
        ArchivoConocimiento.model_validate_json(archivo.model_dump_json()),
        preparado.curriculo,
        catalogo=preparado.catalogo,
        modelos_esperados=archivo.modelos,
    )


def test_consulta_exacta_no_mezcla_filas_grados_ni_paginas(preparado):
    runtime = cargar_runtime(preparado.destino, raiz_historica=preparado.base)
    for i, candidato in enumerate(preparado.candidatos):
        fila = preparado.filas[candidato.fila_id]
        resultados = runtime.buscador.buscar_fila(fila.id, version="V4", grado=fila.grado, asignatura="fisica")
        assert resultados[0].documento.id == fila.id
        externos = [r.documento for r in resultados[1:]]
        assert externos and {d.fuente["pagina"] for d in externos} == {i + 1}
        assert all(d.version == "referencia" and d.grado is None for d in externos)
        assert all(d.metadata["fila_contexto"] == fila.id for d in externos)
    otra = next(
        f
        for f in preparado.curriculo.filas
        if f.grado == 6
        and f.id not in {c.fila_id for c in preparado.candidatos}
        and preparado.decisiones[f.id].disciplinas == ("fisica",)
    )
    assert len(runtime.buscador.buscar_fila(otra.id, version="V4", grado=6, asignatura="fisica")) == 1


@pytest.mark.parametrize("version,grado,asignatura", [("V3", 6, "fisica"), ("V4", 10, "fisica"), ("V4", 6, "biologia")])
def test_filtros_contradictorios_no_autorizan_contexto(preparado, version, grado, asignatura):
    r = cargar_runtime(preparado.destino, raiz_historica=preparado.base)
    with pytest.raises(ValueError):
        r.buscador.buscar_fila(preparado.candidatos[0].fila_id, version=version, grado=grado, asignatura=asignatura)


@pytest.mark.parametrize(
    "alteracion",
    ["modelo", "criterio", "grado", "solicitud", "literal", "tipo_extremo", "grupo", "evidencia_huerfana", "admision"],
)
def test_archivo_rehasheado_no_autoriza_juicios_incoherentes(preparado, alteracion):
    def cambiar(datos):
        id_ = next(iter(datos["expedientes"]))
        registro = datos["expedientes"][id_]
        resultado = next(r for r in datos["coleccion"]["resultados"] if r["solicitud"]["candidato_id"] == id_)
        if alteracion == "modelo":
            resultado["dictamenes"][0]["modelo"] = "modelo-ajeno"
        elif alteracion == "criterio":
            resultado["dictamenes"][0]["criterios"]["fuentes_implican_relacion"] = "no"
        elif alteracion == "grado":
            registro["preparacion"]["grado"] = 11
        elif alteracion == "solicitud":
            resultado["solicitud"]["candidato_id"] = "CANDIDATO_V4:" + "a" * 64
        elif alteracion == "literal":
            registro["preparacion"]["fragmentos"][0]["literal"] = "Un literal ajeno que no existe en la fuente"
        elif alteracion == "tipo_extremo":
            datos["nodos_referencia"][0]["tipo"] = "Concepto"
        elif alteracion == "grupo":
            registro["preparacion"]["grupos"].pop("objetivo_local")
        elif alteracion == "evidencia_huerfana":
            evidencia = copy.deepcopy(next(iter(datos["evidencias"].values())))
            evidencia["id"] = "evidencia-huerfana"
            datos["evidencias"][evidencia["id"]] = evidencia
        else:
            datos["coleccion"]["relaciones_admisibles"] = []

    with pytest.raises((ValueError, KeyError)):
        validar_archivo_conocimiento(
            modificar(preparado.archivo, cambiar), preparado.curriculo, catalogo=preparado.catalogo
        )


def test_fuente_modificada_no_se_sustituye_por_metadatos(preparado, tmp_path):
    copia = tmp_path / "copia"
    copia.mkdir()
    (copia / "referencia.pdf").write_bytes(b"El archivo ya no es el original")
    fuentes = fuentes_del_archivo(
        preparado.archivo, preparado.curriculo, raiz_v4=ruta("insumos/v4"), raiz_historica=copia
    )
    with pytest.raises(ValueError, match="bytes originales"):
        rehidratar_evidencias(preparado.archivo, fuentes, preparado.archivo.evidencias)


def test_bloqueo_cientifico_inhibe_fila_antes_de_recuperar(preparado):
    runtime = cargar_runtime(preparado.destino, raiz_historica=preparado.base)
    candidato = preparado.candidatos[0]
    runtime.fuentes.bloqueos_curriculares[candidato.fila_id] = "Error científico confirmado"
    with pytest.raises(ValueError, match="bloqueante"):
        runtime.buscador.buscar_fila(candidato.fila_id, version="V4", grado=6, asignatura="fisica")


@pytest.mark.parametrize("tipo", ["trabaja_concepto", "practica_declarada", "prerrequisito_necesario"])
def test_archivo_de_otros_tipos_reconstruye_extremos_y_soportes_sinteticos(tmp_path, tipo):
    from test_juicios_conocimiento import ejecutar, entrada

    traduccion = {
        "trabaja_concepto": "fila_concepto",
        "practica_declarada": "fila_practica",
        "prerrequisito_necesario": "prerrequisito",
    }
    e = entrada(tmp_path, tipo=traduccion[tipo], soportes=True)
    motor, _, estado = ejecutar(e)
    archivo = crear_archivo_conocimiento(motor, [estado])
    validar_archivo_conocimiento(archivo, e.curriculo)
    assert archivo.coleccion.relaciones_admisibles[0].tipo == tipo


@pytest.mark.parametrize("cambio", ["nodo_relacion", "destino", "tipo", "fuente"])
def test_grafo_no_puede_alterar_papeles_o_fuentes_de_la_relacion(preparado, cambio):
    p = cargar_producto(preparado.destino)
    nodos = [n.model_copy(deep=True) for n in p.nodos]
    aristas = [a.model_copy(deep=True) for a in p.aristas]
    if cambio == "nodo_relacion":
        next(n for n in nodos if n.tipo == TipoNodo.RELACION_CURRICULAR).props["grado_sv"] = 11
    elif cambio == "fuente":
        next(n for n in nodos if n.id == "DOC:documento-pais").props["sha256"] = "0" * 64
    else:
        arista = next(a for a in aristas if a.tipo == TipoArista.DESTINO_RELACION)
        if cambio == "destino":
            arista.destino = preparado.candidatos[1].fila_id
        else:
            arista.tipo = TipoArista.TRABAJA
    with pytest.raises(ValueError):
        almacen._verificar_grafo(p.curriculo, p.catalogo, tuple(nodos), tuple(aristas), p.conocimiento)


@pytest.mark.parametrize("cambio", ["omitir", "alterar"])
def test_snapshot_sin_conocimiento_o_con_bytes_distintos_falla_sin_fallback(preparado, tmp_path, cambio):
    copia = tmp_path / "copia"
    shutil.copytree(preparado.destino, copia)
    puntero = json.loads((copia / "actual.json").read_bytes())
    archivo = copia / "snapshots" / puntero["snapshot_id"] / "conocimiento.json"
    if cambio == "omitir":
        archivo.unlink()
        error = (FileNotFoundError, ValueError)
    else:
        archivo.write_bytes(archivo.read_bytes() + b"alterado")
        error = ValueError
    with pytest.raises(error):
        cargar_producto(copia)


def test_motor_recupera_fuentes_de_la_fila_explicita_y_conserva_versiones(preparado):
    from goes_science_kg.motor.contratos import Solicitud
    from goes_science_kg.motor.flujo import Motor

    runtime = cargar_runtime(preparado.destino, raiz_historica=preparado.base)
    fila = preparado.filas[preparado.candidatos[0].fila_id]
    motor = Motor(runtime.buscador, None, fuentes=runtime.fuentes, max_caracteres=40000)
    solicitud = Solicitud(
        consulta="Prepara una actividad para este objetivo.",
        version_curriculo="V4",
        grado=6,
        asignatura="fisica",
        fila_id=fila.id,
    )
    contexto = motor._contexto({"solicitud": solicitud.model_dump()})
    assert contexto["evidencias"]
    locales = [e for e in contexto["evidencias"] if e["version"] == "V4"]
    referencias = [e for e in contexto["evidencias"] if e["version"] == "referencia"]
    assert locales and all(e["id"].startswith(fila.id + "#CELDA:") for e in locales)
    assert referencias and {e["fuente"]["pagina"] for e in referencias} == {1}


def test_motor_no_inventa_buscador_de_fila_ni_recurre_a_busqueda_general():
    from goes_science_kg.motor.contratos import Solicitud
    from goes_science_kg.motor.flujo import Motor

    class General:
        def buscar(self, *args, **kwargs):
            raise AssertionError("Un fallo de ámbito no habilita otra búsqueda")

    solicitud = Solicitud(
        consulta="Prepara una actividad para el agua.",
        version_curriculo="V4",
        grado=6,
        asignatura="fisica",
        fila_id="identidad-opaca",
    )
    contexto = Motor(General(), None, fuentes=object())._contexto({"solicitud": solicitud.model_dump()})
    assert contexto["evidencias"] == [] and "fila explícita" in contexto["errores"][0]
