"""La edición final conserva procedencia, incidencias y límites sin heredar votos."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

import pytest
import yaml
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_curriculo_v4 import _mutar_config, _mutar_libro
from test_curriculo_v4 import configuracion as configuracion
from test_materiales import AlmacenDePrueba

from goes_science_kg.api_materiales import crear_router_materiales
from goes_science_kg.curriculo.ingesta import cargar_curriculo
from goes_science_kg.materiales.almacen import Biblioteca, construir
from goes_science_kg.materiales.compilacion import markdown, serializar, sha
from goes_science_kg.produccion.compilacion import compilar, exportar


@pytest.fixture
def versiones(configuracion):
    anterior = cargar_curriculo(configuracion)
    _mutar_libro(configuracion, lambda w: w["Unidad exacta "].__setitem__("O3", "Texto sin fase"))
    final = cargar_curriculo(configuracion)
    fuente = final.fuentes[0]
    antecedentes = [
        {
            "id": "errata",
            "estado_verificacion": "confirmada",
            "ancla_original": "Tabla de datos",
            "explicacion": "Hallazgo histórico que requiere contraste de esta edición.",
            "fuente": {"archivo": fuente.archivo, "hoja": final.filas[0].hoja},
        }
    ]
    return anterior, final, antecedentes


def test_no_reutiliza_ids_votos_ni_aprobacion_para_misma_procedimental(versiones):
    anterior, final, alertas = versiones
    registros, informe = compilar(final, anterior, alertas, biblioteca_anterior="a" * 64)
    assert informe["objetivos_identicos"] == 2
    assert informe["filas_sin_paquete"] == []
    assert informe["revisiones_anteriores_heredadas"] == 0
    assert informe["llamadas_vertex"] == 0
    assert {f.id for f in final.filas}.isdisjoint(f.id for f in anterior.filas)
    assert len(registros) == 3
    for r in registros:
        d = r["documento"]
        assert d["revisiones"] == [] and d["propuesta"] is None
        assert d["estado_revision"] == "pendiente_revision_nueva_edicion"
        assert not d["guion_cronometrado"]
        assert "pendiente" in markdown(r).lower()
    primero = registros[0]["documento"]
    assert primero["original"] == final.filas[0].model_dump(mode="json")
    assert any(c["valor"] == "Texto sin fase" for c in primero["celdas_sin_rol"])
    assert any(a["codigo"] == "ANTECEDENTE_CIENTIFICO_PERSISTENTE:errata" for a in primero["alertas"])


def test_ancla_cientifica_requiere_mismo_archivo_hoja_y_literal(versiones):
    anterior, final, alertas = versiones
    alteradas = deepcopy(alertas)
    alteradas[0]["fuente"]["archivo"] = "otro.xlsx"
    registros, _ = compilar(final, anterior, alteradas, biblioteca_anterior="a" * 64)
    assert not any(a["codigo"].startswith("ANTECEDENTE") for a in registros[0]["documento"]["alertas"])


def test_cuatro_fases_con_ordinales_nuevos_sin_inventar_aproximar(configuracion):
    def cambiar(w):
        h = w["Unidad exacta "]
        for celda, valor in {"H2": "1. Explorar", "I2": "2. Explicar", "J2": "3. Indagar", "K2": "4. Reforzar"}.items():
            h[celda] = valor

    _mutar_libro(configuracion, cambiar)

    def aliases(cfg):
        for i, f in enumerate(("explorar", "explicar", "indagar", "reforzar"), 1):
            cfg["alias_campos"]["fase_" + f] = [f"{i}. {f.title()}"]

    _mutar_config(configuracion, aliases)
    f = cargar_curriculo(configuracion).filas[0]
    assert not f.fases["aproximar"].presente_en_hoja
    assert f.fases["explorar"].texto == "E1, PR2.1 y EP3"
    assert f.fases["explicar"].texto == "D2"
    assert f.fases["indagar"].texto == "I10"
    assert f.fases["reforzar"].texto == "EP2"


def test_zip_reproducible_preserva_todo_y_verifica_shas(versiones, tmp_path):
    anterior, final, alertas = versiones
    registros, informe = compilar(final, anterior, alertas, biblioteca_anterior="a" * 64)
    originales = {s.archivo_local: b"original de prueba" for s in final.fuentes}
    a = exportar(registros, originales, informe, tmp_path / "a")
    b = exportar(list(reversed(registros)), originales, informe, tmp_path / "b")
    assert a == b
    for archivo in a:
        with ZipFile(tmp_path / "a" / archivo["archivo"]) as z:
            m = json.loads(z.read("manifest.json"))
            assert m["paquetes"] == 3
            assert len([n for n in z.namelist() if n.endswith(".md")]) == 3
            for nombre, esperado in m["archivos"].items():
                raw = z.read(nombre)
                assert (len(raw), sha(raw)) == (esperado["bytes"], esperado["sha256"])
    with pytest.raises(ValueError, match="nuevo"):
        exportar(registros, originales, informe, tmp_path / "a")


def test_rutas_finales_independientes_sin_sustituir_biblioteca_previa(versiones, tmp_path):
    anterior, final, alertas = versiones
    registros, informe = compilar(final, anterior, alertas, biblioteca_anterior="a" * 64)
    nueva = tmp_path / "data/materiales_produccion_v4"
    construir(registros, {"informe.json": serializar(informe)}, nueva, procedencia={"snapshot_id": final.huella})
    app = FastAPI()
    app.include_router(crear_router_materiales(tmp_path))
    app.include_router(
        crear_router_materiales(
            tmp_path, directorio="data/materiales_produccion_v4", prefijo="/api/v4/produccion/materiales"
        )
    )
    c = TestClient(app)
    assert c.get("/api/v4/materiales/salud").status_code == 503
    prefix = "/api/v4/produccion/materiales"
    assert c.get(prefix + "/salud").json()["materiales"] == 3
    id_ = registros[0]["id"]
    assert c.get(prefix + "/detalle/" + id_).json()["material"]["documento"]["revisiones"] == []
    assert "pendiente" in c.get(prefix + "/descarga/" + id_ + "?formato=md").text.lower()
    with (nueva / "biblioteca.sqlite").open("ab") as f:
        f.write(b"alteracion")
    assert c.get(prefix + "/salud").status_code == 503


def test_configuracion_produccion_no_activa_ni_altera_edicion_anterior():
    base = Path(__file__).resolve().parents[1]
    nueva = yaml.safe_load((base / "config/mallas_v4_produccion.yaml").read_text())
    previa = yaml.safe_load((base / "config/mallas_v4.yaml").read_text())
    for fuente in nueva["fuentes"]:
        for hoja in fuente["hojas"]:
            if hoja["tratamiento"] == "curricular":
                assert hoja.pop("expandir_fases_combinadas") is True
    assert nueva["fuentes"] == previa["fuentes"]
    assert nueva["directorio"] != previa["directorio"]
    assert nueva["procedencia"] != previa["procedencia"]
    assert nueva["alias_campos"]["fase_explorar"] == ["1. Explorar", "2. Explorar"]


def test_encabezado_combinado_incorpora_ambas_columnas_sin_duplicar_ancla(configuracion):
    from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
    from goes_science_kg.producto.unidades import _verificar_fila

    _mutar_libro(configuracion, lambda w: w["Unidad exacta "].merge_cells("H2:I2"))
    _mutar_config(configuracion, lambda c: c["fuentes"][0]["hojas"][0].update(expandir_fases_combinadas=True))
    c = cargar_curriculo(configuracion)
    fase = c.filas[0].fases["explorar"]
    assert fase.coordenadas == ("H3", "I3")
    assert fase.texto == "E1, PR2.1 y EP3\nD2"
    fuentes = fuentes_del_curriculo(c, raiz_v4=configuracion.parent / "insumos")
    assert _verificar_fila(c.filas[0], fuentes) is not None
    _mutar_libro(configuracion, lambda w: w["Unidad exacta "].merge_cells("H3:I3"))
    c = cargar_curriculo(configuracion)
    assert c.filas[0].fases["explorar"].texto == "E1, PR2.1 y EP3"
    fuentes = fuentes_del_curriculo(c, raiz_v4=configuracion.parent / "insumos")
    assert _verificar_fila(c.filas[0], fuentes) is not None


def test_no_confunde_dos_encabezados_separados_con_uno_combinado(configuracion):
    _mutar_libro(configuracion, lambda w: w["Unidad exacta "].__setitem__("I2", "2. Explorar"))
    _mutar_config(configuracion, lambda c: c["fuentes"][0]["hojas"][0].update(expandir_fases_combinadas=True))
    with pytest.raises(ValueError, match="duplicado"):
        cargar_curriculo(configuracion)


def test_publicacion_zip_reanuda_y_restaura_con_recibo_exacto(versiones, tmp_path):
    from goes_science_kg.produccion.publicacion import descargar, publicar

    anterior, final, alertas = versiones
    registros, informe = compilar(final, anterior, alertas, biblioteca_anterior="a" * 64)
    originales = {s.archivo_local: b"original" for s in final.fuentes}
    carpeta = tmp_path / "exportaciones"
    exportar(registros, originales, informe, carpeta)
    for p in carpeta.iterdir():
        originales["paquetes/" + p.name] = p.read_bytes()
    destino = tmp_path / "biblioteca"
    construir(
        registros,
        originales,
        destino,
        procedencia={"snapshot_id": final.huella, "edicion": "produccion-final-20261026"},
    )
    b = Biblioteca(destino)
    almacen = AlmacenDePrueba(tmp_path / "bucket_prueba")
    recibo = tmp_path / "recibo.json"
    ref = publicar(carpeta, b, almacen, recibo)
    assert len(almacen.creaciones) == 2
    assert publicar(carpeta, b, almacen, recibo) == ref
    assert len(almacen.creaciones) == 2
    restaurada = tmp_path / "descargada"
    descargar(ref, restaurada, almacen)
    for p in carpeta.iterdir():
        assert p.read_bytes() == (restaurada / p.name).read_bytes()
    adulterado = deepcopy(ref)
    adulterado["objetos"]["indice.json"]["uri"] = "gs://otro/indice.json"
    with pytest.raises(ValueError, match="pertenece"):
        descargar(adulterado, tmp_path / "mal", almacen)
    assert not (tmp_path / "mal").exists()
    with pytest.raises(ValueError, match="nuevo"):
        descargar(ref, restaurada, almacen)
    zip_ = next(carpeta.glob("*.zip"))
    zip_.write_bytes(b"alteracion")
    with pytest.raises(ValueError, match="biblioteca"):
        publicar(carpeta, b, almacen, recibo)
    assert len(almacen.creaciones) == 2
