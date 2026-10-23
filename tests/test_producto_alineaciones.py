"""Test real product-3 alignment, mandatory context, and source-audited API queries."""

from __future__ import annotations

import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from test_alineacion import LectorSimulado, ejecutar, pdf_sintetico
from test_producto_v4 import catalogo as catalogo
from test_producto_v4 import curriculo as curriculo

from goes_science_kg.api import crear_app
from goes_science_kg.config import ruta
from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.ingesta.referencias import FuentePublica, RepositorioReferencias
from goes_science_kg.ingesta.referentes_operativos import ReferenteOperativo
from goes_science_kg.motor.alineacion import ROLES_ALINEACION, MotorAlineacion, SolicitudAlineacion
from goes_science_kg.motor.contexto import construir_contexto, grupos_obligatorios
from goes_science_kg.motor.contratos import Solicitud, huella
from goes_science_kg.motor.flujo import Motor
from goes_science_kg.producto import cargar_producto, construir_producto
from goes_science_kg.producto.alineaciones import coleccionar_alineaciones
from goes_science_kg.producto.runtime import cargar_runtime


@pytest.fixture(scope="module")
def publicado(tmp_path_factory, curriculo, catalogo):
    base = tmp_path_factory.mktemp("producto-alineado")
    shutil.copytree(ruta("insumos/v4"), base / "insumos/v4")
    alertas = base / "docs/investigacion/alertas_v4.json"
    alertas.parent.mkdir(parents=True)
    shutil.copyfile(ruta("docs/investigacion/alertas_v4.json"), alertas)
    contenido = pdf_sintetico(
        "Evaluate a scientific experiment. Compare conditions and justify conclusions with evidence."
    )
    repo = RepositorioReferencias(base / "data/referencias_2026")
    with pytest.MonkeyPatch.context() as m:
        m.setattr("goes_science_kg.ingesta.referencias.descargar_pdf", lambda f: (contenido, f.url_documento))
        registro = repo.incorporar(
            [
                FuentePublica(
                    id="marco_sintetico",
                    titulo="Fuente sintética de prueba",
                    institucion="Prueba",
                    version_documental="prueba-2026",
                    url_catalogo="https://www.oecd.org/prueba",
                    url_documento="https://www.oecd.org/prueba.pdf",
                    estado_publicacion="publicado_final",
                )
            ],
            descargar=True,
        ).referencias["marco_sintetico"]
    ref = ReferenteOperativo(
        id="LOCAL:experimento",
        marco="Marco sintético",
        ciclo="2026",
        version_documental=registro.version_documental,
        fuente=registro.id,
        sha256=registro.sha256,
        paginas_pdf=(1,),
        ancla="Compare conditions",
        descripcion="Valorar un experimento con evidencia.",
        eje="practica",
        tipo="competencia",
        alcance="Sólo una prueba técnica sintética.",
    )
    filas = [f for f in curriculo.filas if f.grado == 10 and f.asignatura_malla == "Física"][:2]
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=base / "insumos/v4")
    modelo = LectorSimulado()
    motor = MotorAlineacion(curriculo, {ref.id: ref}, fuentes, repo, modelo)
    estado = ejecutar(motor, SolicitudAlineacion(fila_id=filas[0].id, referente_id=ref.id))
    estado["huella_entorno"] = motor.huella_entorno
    modelos = {r: modelo.nombre_modelo(r) for r in ROLES_ALINEACION}
    archivo = coleccionar_alineaciones([estado], curriculo, {ref.id: ref}, modelos, fuentes, repo)
    informe = construir_producto(
        curriculo,
        catalogo,
        destino=base / "data/producto/V4",
        raiz_v4=base / "insumos/v4",
        archivo_alertas=alertas,
        alineaciones=archivo,
        modelos_alineacion=modelos,
        paginas_alineacion=repo,
    )
    return SimpleNamespace(base=base, informe=informe, filas=filas, archivo=archivo, registro=registro)


def runtime(publicado):
    return cargar_runtime(
        publicado.base / "data/producto/V4",
        raiz_v4=publicado.base / "insumos/v4",
        raiz_referencias=publicado.base / "data/referencias_2026",
        archivo_alertas=publicado.base / "docs/investigacion/alertas_v4.json",
    )


def test_producto3_nueve_archivos_carga_y_relacion_con_fila_exacta(publicado):
    p = cargar_producto(publicado.base / "data/producto/V4")
    assert p.manifest.version == "producto-3" and len(p.manifest.sha256) == 9
    assert p.alineaciones == publicado.archivo
    assert sum(a.tipo.value == "DECLARADA_EN" for a in p.aristas) == 1
    assert not any(a.tipo.value == "CUBRE" for a in p.aristas)
    r = runtime(publicado)
    consultadas = [r.buscador.buscar_fila(f.id, version="V4", grado=10, asignatura="fisica") for f in publicado.filas]
    assert any(x.documento.version == "referencia" for x in consultadas[0])
    assert all(x.documento.version == "V4" for x in consultadas[1])
    with pytest.raises(ValueError, match="límite"):
        r.buscador.buscar_fila(publicado.filas[0].id, version="V4", grado=10, asignatura="fisica", k=1)


def test_motor_conserva_pagina_inglesa_y_abstiene_si_no_cabe(publicado):
    r = runtime(publicado)
    s = Solicitud(
        consulta="Explica el objetivo curricular local",
        grado=10,
        asignatura="fisica",
        version_curriculo="V4",
        fila_id=publicado.filas[0].id,
    )
    m = Motor(r.buscador, LectorSimulado(), fuentes=r.fuentes)
    e = m._contexto({"solicitud": s.model_dump()})
    assert not e["errores"]
    refs = {x["id"] for x in e["evidencias"] if x["version"] == "referencia"}
    assert refs and refs.issubset(f["evidencia_id"] for f in e["fragmentos"])
    corto = Motor(r.buscador, LectorSimulado(), fuentes=r.fuentes, max_caracteres=1000)
    cerrado = corto._contexto({"solicitud": s.model_dump()})
    assert cerrado["errores"] and not cerrado.get("fragmentos")
    resultados = r.buscador.buscar_fila(publicado.filas[0].id, version="V4", grado=10, asignatura="fisica")
    evidencias = construir_contexto(resultados, version="V4", fuentes=r.fuentes)
    with pytest.raises(ValueError, match="obligatoria"):
        grupos_obligatorios(resultados, [e for e in evidencias if e.version == "V4"])


def test_api_lista_audita_y_rechaza_caso_ajeno(publicado):
    c = TestClient(crear_app(publicado.base))
    lista = c.get("/api/v4/alineaciones")
    assert lista.status_code == 200 and len(lista.json()["casos"]) == 1
    id_ = huella(publicado.archivo.casos[0].solicitud)
    respuesta = c.get(f"/api/v4/alineaciones/{id_}")
    assert respuesta.status_code == 200
    assert respuesta.json()["caso"]["resultado"]["estado"] == "respaldo_documental_automatico"
    assert c.get("/api/v4/alineaciones/inventada").status_code == 404
    assert c.get("/api/v4/alineaciones", params={"fila_id": "otra"}).status_code == 404


def test_noveno_archivo_alterado_invalida_instancia(publicado):
    c = TestClient(crear_app(publicado.base))
    assert c.get("/api/v4/salud").status_code == 200
    p = Path(publicado.informe["ruta_grafo"]) / "alineaciones.json"
    original = p.read_bytes()
    try:
        p.write_bytes(original + b" ")
        assert c.get("/api/v4/salud").status_code == 503
    finally:
        p.write_bytes(original)
    assert c.get("/api/v4/salud").status_code == 503


def test_pdf_cambiado_impide_auditar_aunque_el_snapshot_no_cambie(publicado):
    c = TestClient(crear_app(publicado.base))
    id_ = huella(publicado.archivo.casos[0].solicitud)
    assert c.get(f"/api/v4/alineaciones/{id_}").status_code == 200
    p = publicado.base / "data/referencias_2026" / publicado.registro.archivo_pdf
    original = p.read_bytes()
    try:
        p.write_bytes(original + b" cambio")
        assert c.get(f"/api/v4/alineaciones/{id_}").status_code == 503
    finally:
        p.write_bytes(original)
