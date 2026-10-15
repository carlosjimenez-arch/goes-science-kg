"""Pruebas de aceptación con datos reales y ataques que recalculan SHA: integridad no basta para validez."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from goes_science_kg.cli import app
from goes_science_kg.motor import archivos, consumidor
from goes_science_kg.motor.archivos import canonico, decodificar, escribir, id_manifiesto, leer, sha
from goes_science_kg.motor.construccion import exportar
from goes_science_kg.motor.identidades import columnas_vigentes, comprobar_identidades
from goes_science_kg.motor.politicas import calidad, propagar_dependencias
from goes_science_kg.motor.validacion import cargar_entrega, validar


@pytest.fixture(scope="module")
def entrega(tmp_path_factory):
    d = tmp_path_factory.mktemp("motor") / "v1"
    exportar(d, "0.1.0-prueba", "a" * 40)
    return d


@pytest.fixture(scope="module")
def datos(entrega):
    return cargar_entrega(entrega)[1]


def copiar(entrega, tmp_path):
    d = tmp_path / "copia"
    shutil.copytree(entrega, d)
    return d


def resignar(d, archivo=None):
    """Simula alteración consistente de huellas para exigir comprobaciones semánticas."""
    m = leer(d / "manifiesto.json")
    if archivo:
        p = d / archivo
        m["archivos"][archivo].update(sha256=sha(p), bytes=p.stat().st_size)
        if archivo.endswith(".jsonl"):
            m["archivos"][archivo]["registros"] = len(p.read_text().splitlines())
    m["id_entrega"] = id_manifiesto(m)
    escribir(d / "manifiesto.json", m)
    return m["id_entrega"]


def alterar(d, nombre, funcion):
    p = d / (nombre + ".jsonl")
    rs = [decodificar(linea) for linea in p.read_text().splitlines()]
    funcion(rs)
    p.write_text("".join(canonico(r) + "\n" for r in rs), encoding="utf-8")
    resignar(d, p.name)


def test_aceptacion_catalogo_fuentes_y_permisos(entrega, datos):
    rep = validar(entrega)
    assert rep["metricas"]["temas"] == rep["metricas"]["puente"] == 935
    assert rep["metricas"]["temas_en_alcance"] == 920
    assert rep["metricas"]["paquetes"] == 230
    assert rep["metricas"]["analisis"] == 1123
    assert rep["metricas"]["referencias"] == rep["metricas"]["componentes_aula"] == 0
    assert len({t.fuente.archivo for t in datos["temas"]}) == 11
    assert all(not c.usos.aula and c.calidad.revisado_por is None for c in datos["componentes"])
    assert any(c.usos.autoria for c in datos["componentes"])
    assert any(not c.usos.autoria for c in datos["componentes"])


def test_columnas_completas_y_orden_real(datos):
    columnas = columnas_vigentes()
    temas = sorted(datos["temas"], key=lambda t: t.orden)
    assert [(t.fuente.archivo, t.fuente.hoja, t.fuente.fila) for t in temas] == list(columnas)
    for t in temas:
        assert t.columnas == columnas[(t.fuente.archivo, t.fuente.hoja, t.fuente.fila)][0]
    assert sum(bool(t.diferencias_extraccion) for t in temas) == 9
    t = next(t for t in temas if t.id == "TEMA:G05-CIE-U3-3.3")
    assert len(t.columnas["Evidencia de aprendizaje"]) > len(t.extraccion_grafo["evidencia"])


def test_puente_incompleto_y_alias_repetido_se_rechazan():
    base = Path("data/interim/motor/analisis_v3")
    ids = leer(base / "identidades.json")
    fuentes = leer(base / "fuentes_mallas.json")
    columnas = columnas_vigentes()
    with pytest.raises(ValueError, match="todos los temas"):
        comprobar_identidades(ids[:-1], fuentes, columnas)
    ids[1]["id"] = ids[0]["id"]
    with pytest.raises(ValueError, match="repetida"):
        comprobar_identidades(ids, fuentes, columnas)


def test_ningun_marcador_no_certifica_ausencia_de_datos():
    c = calidad({"id": "ACT:prueba", "enunciado": "Explica el cambio observado."}, None)
    assert c.estado_datos == "no_evaluado"
    c = calidad({"id": "ACT:prueba", "enunciado": "Consulta la tabla de referencia."}, None)
    assert c.estado_datos == "pendiente"


def test_dependencias_bloqueadas_se_propagan(datos):
    elegible = next(c for c in datos["componentes"] if c.usos.autoria)
    a, b, c = [elegible.model_copy(deep=True) for _ in range(3)]
    a.id, b.id, c.id = "a", "b", "c"
    a.componentes_requeridos, b.componentes_requeridos, c.componentes_requeridos = ["b"], ["c"], []
    c.usos.autoria = False
    propagar_dependencias({"a": a, "b": b, "c": c})
    assert not a.usos.autoria and not b.usos.autoria


@pytest.mark.parametrize("ataque,patron", [
    ("duplicado", "repetido"), ("alias", "identidad ambigua"), ("orden", "orden de temas"),
    ("fuente", "fila oficial"), ("aula", "aula"), ("permiso", "permisos"),
    ("codigo", "código de marco desconocido"), ("pisa", "no es contenido"),
    ("dependencia", "requerido inexistente"), ("grupo", "tipo o identidad"),
    ("clave", "clave de actividad inválida"), ("sha_fuente", "sin respaldo"),
    ("concepto", "concepto de paquete inexistente"),
])
def test_rechaza_corrupcion_semantica_aun_con_sha_nuevos(entrega, tmp_path, ataque, patron):
    d = copiar(entrega, tmp_path)
    if ataque == "duplicado":
        alterar(d, "temas", lambda rs: rs.append(rs[0]))
    elif ataque == "alias":
        alterar(d, "temas", lambda rs: rs[0]["aliases"].append("NM26:inventado"))
    elif ataque == "orden":
        alterar(d, "temas", lambda rs: rs[0].update(orden=rs[1]["orden"]))
    elif ataque == "fuente":
        def cambiar(rs):
            rs[0]["fuente"]["archivo"] = "otra_malla.xlsx"
        alterar(d, "temas", cambiar)
        alterar(d, "puente", cambiar)
    elif ataque in ("aula", "permiso"):
        def cambiar(rs):
            c = next(r for r in rs if not r["usos"]["autoria"])
            c["usos"]["aula" if ataque == "aula" else "autoria"] = True
        alterar(d, "componentes", cambiar)
    elif ataque in ("codigo", "pisa"):
        def cambiar(rs):
            c = next(r for r in rs if r["tipo"] == ("PISA" if ataque == "pisa" else "TIMSS"))
            c["resultado"]["cont1" if ataque == "pisa" else "obj1"] = (
                "PISA-PR1" if ataque == "pisa" else "T8_27-INVENTADO")
        alterar(d, "analisis", cambiar)
    elif ataque == "dependencia":
        alterar(d, "componentes", lambda rs: rs[0]["componentes_requeridos"].append("ACT:inexistente"))
    elif ataque == "grupo":
        def cambiar(rs):
            rs[0]["componentes"]["experimentos"].append(rs[0]["componentes"]["actividades"][0])
        alterar(d, "paquetes", cambiar)
    elif ataque == "sha_fuente":
        def cambiar(rs):
            rs[0]["fuente"]["sha256"] = "0" * 64
        alterar(d, "temas", cambiar)
        alterar(d, "puente", cambiar)
    elif ataque == "concepto":
        alterar(d, "paquetes", lambda rs: rs[0]["conceptos"].append(rs[0]["tema_id"]))
    else:
        def cambiar(rs):
            next(r for r in rs if r["contenido"].get("formato") == "opcion_multiple")["contenido"]["correcta"] = "Z"
        alterar(d, "componentes", cambiar)
    with pytest.raises(ValueError, match=patron):
        validar(d)


@pytest.mark.parametrize("ataque", ["bytes", "extra", "simbolico", "rutas", "json_repetido", "nan"])
def test_rechaza_archivos_no_integros(entrega, tmp_path, ataque):
    d = copiar(entrega, tmp_path)
    if ataque == "bytes":
        with (d / "LEEME.md").open("a") as f:
            f.write("alteración")
    elif ataque == "extra":
        (d / "ajeno.json").write_text("{}")
    elif ataque == "simbolico":
        (d / "LEEME.md").unlink()
        (d / "LEEME.md").symlink_to(entrega / "LEEME.md")
    elif ataque == "rutas":
        m = leer(d / "manifiesto.json")
        m["archivos"]["../ajeno"] = m["archivos"].pop("LEEME.md")
        m["id_entrega"] = id_manifiesto(m)
        escribir(d / "manifiesto.json", m)
    else:
        (d / "catalogos.json").write_text('{"a":1,"a":2}' if ataque == "json_repetido" else '{"a":NaN}')
        resignar(d, "catalogos.json")
    with pytest.raises(ValueError):
        validar(d)


def test_ciclo_de_componentes_se_rechaza_aunque_las_referencias_existan(entrega, tmp_path):
    d = copiar(entrega, tmp_path)
    def crear_ciclo(rs):
        c = next(r for r in rs if r["tipo"] == "microtema")
        c["contenido"]["practica"] = c["id"]
        c["componentes_requeridos"] = sorted({c["contenido"]["comprobacion"], c["id"]})
    alterar(d, "componentes", crear_ciclo)
    with pytest.raises(ValueError, match="con ciclos"):
        validar(d)


def test_archivo_de_versiones_simbolico_se_rechaza(entrega, tmp_path):
    almacen = tmp_path / "almacen"
    rep = consumidor.importar(entrega, almacen)
    (almacen / "otra").mkdir()
    shutil.move(almacen / "entregas", almacen / "otra" / "entregas")
    (almacen / "entregas").symlink_to(almacen / "otra" / "entregas", target_is_directory=True)
    with pytest.raises(ValueError, match="simbólico"):
        consumidor.consultar(almacen, "G10-FIS-U7-7.5")
    with pytest.raises(ValueError, match="simbólico"):
        consumidor.activar(almacen, rep["id_entrega"])


def test_importacion_idempotente_consulta_y_alias_exactos(entrega, tmp_path, datos):
    almacen = tmp_path / "almacen"
    assert consumidor.importar(entrega, almacen)["creada"]
    assert not consumidor.importar(entrega, almacen)["creada"]
    t = next(t for t in datos["temas"] if t.id == "TEMA:G10-FIS-U4-4.1")
    a = consumidor.consultar(almacen, t.id, "autoria")
    b = consumidor.consultar(almacen, t.aliases[0], "autoria")
    assert a == b
    assert all(c["usos"]["autoria"] and not c["usos"]["aula"] for c in a["componentes"])
    assert all(c["tipo"] != "refuerzo" for c in a["componentes"])
    assert a["paquete"]
    with pytest.raises(ValueError, match="perfil no habilitado"):
        consumidor.consultar(almacen, t.id, "aula")
    with pytest.raises(ValueError, match="inexistente"):
        consumidor.consultar(almacen, "TEMA:inventado")


def test_reemplazos_no_se_convierten_en_aliases(datos):
    aliases = {a for t in datos["temas"] for a in t.aliases}
    ids = {t.id for t in datos["temas"]}
    for p in datos["paquetes"]:
        if p.reemplazo_elegido:
            assert p.reemplazo_elegido["pedido"] not in aliases
            assert "TEMA:" + p.reemplazo_elegido["pedido"] not in ids
            assert p.tema_id == "TEMA:" + p.reemplazo_elegido["tema_usado"]
    assert sum(p.reemplazo_elegido is not None for p in datos["paquetes"]) == 2


def test_casos_pendientes_y_refuerzo_fragil_no_pasan_a_autoria(datos):
    bloqueados = [c for c in datos["componentes"] if not c.usos.autoria]
    assert any(c.calidad.estado_panel == "sin_consenso" for c in bloqueados)
    assert any(c.tipo == "refuerzo" and c.calidad.solidez == "fragil" for c in bloqueados)
    assert all(not c.usos.autoria for c in datos["componentes"] if c.calidad.estado_panel == "sin_consenso")


def test_activar_otra_version_y_retroceder_sin_duplicar(entrega, tmp_path):
    almacen = tmp_path / "almacen"
    rep = consumidor.importar(entrega, almacen)
    copia = copiar(entrega, tmp_path)
    m = leer(copia / "manifiesto.json")
    m["version_contenido"] = "0.2.0-prueba"
    escribir(copia / "manifiesto.json", m)
    nuevo = resignar(copia)
    consumidor.importar(copia, almacen, False)
    assert leer(almacen / "activo.json")["id_entrega"] == rep["id_entrega"]
    consumidor.activar(almacen, nuevo)
    assert leer(almacen / "activo.json")["id_entrega"] == nuevo
    consumidor.activar(almacen, rep["id_entrega"])
    assert len(list((almacen / "entregas").iterdir())) == 2
    (copia / "LEEME.md").write_text("corrupto")
    with pytest.raises(ValueError):
        consumidor.importar(copia, almacen)
    assert leer(almacen / "activo.json")["id_entrega"] == rep["id_entrega"]


def test_fallo_de_activacion_preserva_puntero(entrega, tmp_path, monkeypatch):
    almacen = tmp_path / "almacen"
    consumidor.importar(entrega, almacen)
    antes = (almacen / "activo.json").read_bytes()
    copia = copiar(entrega, tmp_path)
    m = leer(copia / "manifiesto.json")
    m["version_contenido"] = "0.8.0-prueba"
    escribir(copia / "manifiesto.json", m)
    nuevo = resignar(copia)
    consumidor.importar(copia, almacen, False)
    def fallar(*args):
        raise OSError("disco no disponible")
    monkeypatch.setattr(consumidor.os, "replace", fallar)
    with pytest.raises(OSError, match="disco"):
        consumidor.activar(almacen, nuevo)
    assert (almacen / "activo.json").read_bytes() == antes
    assert not list(almacen.glob(".activo-*"))


def test_cambio_de_entrega_durante_copia_se_rechaza(entrega, tmp_path, monkeypatch):
    original = consumidor.shutil.copytree
    def copiar_y_cambiar(origen, destino):
        original(origen, destino)
        m = leer(destino / "manifiesto.json")
        m["version_contenido"] = "0.9.0-prueba"
        escribir(destino / "manifiesto.json", m)
        resignar(destino)
    monkeypatch.setattr(consumidor.shutil, "copytree", copiar_y_cambiar)
    almacen = tmp_path / "almacen"
    with pytest.raises(ValueError, match="cambió durante"):
        consumidor.importar(entrega, almacen)
    assert not (almacen / "activo.json").exists()
    assert not list((almacen / "entregas").iterdir())


def test_validador_portatil_y_destinos_protegidos(entrega, tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="protegido"):
        archivos.destino_seguro(Path("data/fuentes/prueba"))
    def sin_repositorio(*args):
        raise FileNotFoundError("sin repositorio productor")
    monkeypatch.setattr(archivos, "ruta", sin_repositorio)
    assert validar(entrega)["resultado"] == "valido"
    assert consumidor.importar(entrega, tmp_path / "instalado")["creada"]


def test_determinismo_inmutabilidad_y_cli(entrega, tmp_path):
    copia = exportar(tmp_path / "otra", "0.1.0-prueba", "a" * 40)
    assert leer(copia / "manifiesto.json") == leer(entrega / "manifiesto.json")
    assert exportar(copia, "0.1.0-prueba", "a" * 40) == copia
    with pytest.raises(ValueError, match="otra entrega"):
        exportar(copia, "0.2.0-prueba", "a" * 40)
    resultado = CliRunner().invoke(app, ["motor", "validar", str(entrega)])
    assert resultado.exit_code == 0 and '"resultado": "valido"' in resultado.output
