"""Contrato docente: versiones, estados, originales, recuperación y consultas adversarias."""

from __future__ import annotations

import shutil
from copy import deepcopy
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from test_api_interfaz import aplicacion as aplicacion
from test_mejoras_curriculares import caso as caso
from test_mejoras_entrega import entrega as entrega

from goes_science_kg.api_materiales import crear_router_materiales
from goes_science_kg.materiales import compilacion
from goes_science_kg.materiales.almacen import Biblioteca, construir
from goes_science_kg.materiales.compilacion import compilar_historicos, compilar_v4, recoger_originales, serializar, sha
from goes_science_kg.materiales.publicacion import publicar, restaurar


def registro(id_, version="V4", tipo="paquete_objetivo", grados=(3,), estado="propuesta_pendiente"):
    return {
        "id": id_,
        "version_curriculo": version,
        "tipo": tipo,
        "titulo": "Medición y materia",
        "grados": list(grados),
        "asignatura": "Ciencias",
        "unidad": "Materia",
        "fila_id": id_,
        "estado": estado,
        "documento": {"texto": "Contenido sintético de prueba", "estado": estado},
    }


@pytest.fixture
def biblioteca(tmp_path):
    registros = [
        registro("fila-v4"),
        registro("ACT:historica/obj-1", "historico", "actividad", (3, 5)),
        registro("V3:tema", "V3", "paquete_historico", (9,), "revision_incompleta"),
    ]
    archivos = {"entregas/paquete.md": b"# Original\n\nSin alterar.\n", "data/pedagogia.json": b'[{"id":"x"}]\n'}
    destino = tmp_path / "data/materiales"
    manifest = construir(registros, archivos, destino, procedencia={"snapshot_id": "a" * 64})
    return SimpleNamespace(base=tmp_path, destino=destino, registros=registros, archivos=archivos, manifest=manifest)


@pytest.fixture
def cliente(biblioteca):
    app = FastAPI()
    app.include_router(crear_router_materiales(biblioteca.base))
    return TestClient(app)


def test_originales_y_conteos_se_reconstruyen_sin_promover_pendientes(biblioteca):
    b = Biblioteca(biblioteca.destino)
    assert b.validar() == biblioteca.manifest
    assert b.listar()["total"] == 1
    assert b.listar(version="historico", grado=5)["materiales"][0]["estado"] == "propuesta_pendiente"
    assert b.listar(version="V3")["materiales"][0]["estado"] == "revision_incompleta"
    for ruta, raw in biblioteca.archivos.items():
        assert b.archivo(sha(raw)) == (raw, [ruta])


def test_compilacion_determinista_aunque_cambie_el_orden(biblioteca, tmp_path):
    segundo = tmp_path / "segunda"
    m = construir(
        list(reversed(biblioteca.registros)),
        dict(reversed(list(biblioteca.archivos.items()))),
        segundo,
        procedencia={"snapshot_id": "a" * 64},
    )
    assert m == biblioteca.manifest
    for nombre in ("biblioteca.sqlite", "manifest.json"):
        assert (segundo / nombre).read_bytes() == (biblioteca.destino / nombre).read_bytes()


def test_no_sobrescribe_y_rechaza_ids_duplicados(biblioteca, tmp_path):
    with pytest.raises(ValueError, match="nuevo"):
        construir(biblioteca.registros, {}, biblioteca.destino, procedencia={})
    with pytest.raises(ValueError, match="únicas"):
        construir(biblioteca.registros * 2, {}, tmp_path / "otra", procedencia={})
    assert not (tmp_path / "otra").exists()


@pytest.mark.parametrize(
    "consulta,total",
    [
        ("", 1),
        ("?version=V3", 1),
        ("?version=historico&grado=5", 1),
        ("?version=historico&grado=2", 0),
        ("?q=MEDICIÓN", 1),
        ("?q=%25", 0),
        ("?q=' OR 1=1 --", 0),
        ("?fila_id=fila-v4", 1),
        ("?tipo=actividad", 0),
        ("?asignatura=Física", 0),
        ("?offset=1", 1),
    ],
)
def test_api_filtra_version_grado_y_no_interpreta_sql(cliente, consulta, total):
    r = cliente.get("/api/v4/materiales" + consulta)
    assert r.status_code == 200 and r.json()["total"] == total
    if "offset=1" in consulta:
        assert not r.json()["materiales"]


@pytest.mark.parametrize(
    "consulta", ["?version=V2", "?grado=1", "?limite=1000", "?offset=-1", "?tipo=inventado", "?q=" + "a" * 201]
)
def test_api_acota_entradas(cliente, consulta):
    assert cliente.get("/api/v4/materiales" + consulta).status_code == 422


def test_detalle_con_slash_y_archivos_por_sha_sin_acceso_a_rutas(cliente, biblioteca):
    r = cliente.get("/api/v4/materiales/detalle/ACT:historica/obj-1")
    assert r.status_code == 200 and r.json()["material"]["estado"] == "propuesta_pendiente"
    assert cliente.get("/api/v4/materiales/detalle/desconocido").status_code == 404
    raw = biblioteca.archivos["entregas/paquete.md"]
    r = cliente.get("/api/v4/materiales/archivos/" + sha(raw))
    assert r.content == raw and r.headers["etag"] == '"' + sha(raw) + '"'
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "attachment" in r.headers["content-disposition"]
    assert cliente.get("/api/v4/materiales/archivos/" + "a" * 64).status_code == 404
    assert cliente.get("/api/v4/materiales/archivos/.env").status_code == 422
    assert cliente.get("/api/v4/materiales/archivos/..%2f..%2f.env").status_code == 404
    assert cliente.get("/api/v4/materiales/descarga/V3:tema?formato=md").status_code == 200
    r = cliente.get("/api/v4/materiales/descarga/ACT:historica/obj-1")
    assert r.status_code == 200 and r.json()["documento"]["estado"] == "propuesta_pendiente"


def test_api_falla_cerrada_si_no_se_restauro_o_si_cambia_la_biblioteca(biblioteca, cliente, tmp_path):
    assert cliente.get("/api/v4/materiales/salud").status_code == 200
    p = biblioteca.destino / "biblioteca.sqlite"
    with p.open("ab") as f:
        f.write(b"alteracion")
    assert cliente.get("/api/v4/materiales/salud").status_code == 503
    assert cliente.get("/api/v4/materiales").status_code == 503
    app = FastAPI()
    app.include_router(crear_router_materiales(tmp_path / "sin_datos"))
    assert TestClient(app).get("/api/v4/materiales/salud").status_code == 503


def test_manifest_y_sqlite_alterados_se_rechazan(biblioteca):
    p = biblioteca.destino / "manifest.json"
    raw = p.read_bytes()
    p.write_bytes(raw.replace(b'"materiales":3', b'"materiales":4'))
    with pytest.raises(ValueError, match="Manifest"):
        Biblioteca(biblioteca.destino)
    p.write_bytes(raw)
    with (biblioteca.destino / "biblioteca.sqlite").open("ab") as f:
        f.write(b"alterado")
    with pytest.raises(ValueError, match="manifest"):
        Biblioteca(biblioteca.destino)


def test_paquete_v4_copia_textos_y_votos_sin_generar_ni_migrar(aplicacion, monkeypatch):
    # Fuentes sintéticas de la fixture: la prueba real de celdas está en test_unidades.
    monkeypatch.setattr(compilacion, "_verificar_fila", lambda f, fuentes: SimpleNamespace(fuente={"sha256": "a" * 64}))
    paquetes = compilar_v4(aplicacion.runtime)
    objetivo, unidad = paquetes
    original = aplicacion.runtime.producto.mejoras.unidades[0].resultado.propuesta.filas[0]
    assert objetivo["documento"]["propuesta"] == original.model_dump(mode="json")
    assert objetivo["documento"]["duracion_minutos"] is None
    assert not objetivo["documento"]["guion_cronometrado"]
    assert not objetivo["documento"]["material_historico_trasladado"]
    assert len(objetivo["documento"]["revisiones"]["dictamenes"]) == 4
    assert objetivo["documento"]["alerta_original"]
    assert unidad["documento"]["filas_ids"] == ["fila1"]
    texto = compilacion.markdown(objetivo)
    assert original.orientacion_didactica in texto and original.seguridad in texto
    assert "Criterios de evaluación" in texto


def historicos_de_prueba():
    archivos = {
        "entregas/paquetes_clase/G09-CIE-X.json": serializar(
            {
                "tema": {
                    "id": "G09-CIE-X",
                    "grado": 9,
                    "asignatura": "Ciencias",
                    "unidad": "Materia",
                    "procedimental": "Comparar materiales",
                },
                "completitud": {"revision_del_panel": "incompleta"},
            }
        ),
        "aprendizaje/recorridos/recorridos.json": serializar({"R1": {"estado": "demostracion"}}),
        "data/producto/unidades/fisica-10-entrega-experimental/unidad.json": serializar(
            {
                "paquete_origen_id": "origen",
                "snapshot_id": "b" * 64,
                "grado": 10,
                "asignatura": "Física",
                "unidad": "Física como ciencia",
                "estado": "experimental",
            }
        ),
    }
    for banco, tipo in compilacion.BANCOS.items():
        archivos[f"data/pedagogia/{banco}.json"] = serializar(
            [{"id": tipo + ":prueba", "grados": [9], "estado": "propuesta_pendiente", "version": "pedagogia-v1"}]
        )
    return archivos


def test_historicos_mantienen_pendientes_y_experimental_no_adopta_snapshot_actual():
    archivos = historicos_de_prueba()
    antes = deepcopy(archivos)
    registros = compilar_historicos(archivos)
    assert archivos == antes
    assert len(registros) == 7
    assert all(r["estado"] == "propuesta_pendiente" for r in registros[1:5])
    assert registros[0]["documento"]["migrado_a_v4"] is False
    experimental = registros[-1]["documento"]
    assert experimental["snapshot_id_origen"] == "b" * 64
    assert experimental["adopcion_snapshot_actual"] is False


def test_seleccion_de_originales_rechaza_enlaces(tmp_path):
    archivos = historicos_de_prueba()
    for nombre, contenido in archivos.items():
        p = tmp_path / nombre
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(contenido)
    for nombre in (
        "data/pedagogia/REVISION_PENDIENTE.md",
        "data/interim/revisiones/2026-10-13_paquetes_clase.json",
        "data/producto/unidades/fisica-10-entrega-experimental/unidad.md",
    ):
        p = tmp_path / nombre
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("original")
    originales = recoger_originales(tmp_path)
    assert len(originales) == 10
    (tmp_path / "data/pedagogia/actividades.json").unlink()
    (tmp_path / "data/pedagogia/actividades.json").symlink_to(tmp_path / "data/pedagogia/experimentos.json")
    with pytest.raises(ValueError, match="propios"):
        recoger_originales(tmp_path)


class AlmacenDePrueba:
    def __init__(self, base):
        self.base = base
        self.base.mkdir()
        self.configuracion = SimpleNamespace(ruta=lambda n: "gs://aprobado/ciencias/v4/" + n)
        self.creaciones = []

    def crear(self, archivo, nombre):
        self.creaciones.append(nombre)
        p = self.base / sha(nombre.encode())
        with p.open("xb") as f:
            f.write(archivo.read_bytes())
        return {
            "uri": self.configuracion.ruta(nombre),
            "generacion": "123",
            "sha256": sha(p.read_bytes()),
            "bytes": p.stat().st_size,
        }

    def verificar(self, uri, generacion, digest, tamano):
        p = self.base / sha(uri.removeprefix("gs://aprobado/ciencias/v4/").encode())
        assert generacion == "123" and sha(p.read_bytes()) == digest and p.stat().st_size == tamano

    def descargar(self, ref, destino):
        self.verificar(ref["uri"], ref["generacion"], ref["sha256"], ref["bytes"])
        p = self.base / sha(ref["uri"].removeprefix("gs://aprobado/ciencias/v4/").encode())
        shutil.copyfile(p, destino)


def test_publicacion_reanuda_sin_sobrescribir_y_restauracion_verifica_todo(biblioteca, tmp_path):
    almacen = AlmacenDePrueba(tmp_path / "bucket_prueba")
    recibo = tmp_path / "recibo.json"
    ref = publicar(biblioteca.destino, almacen, recibo)
    assert len(almacen.creaciones) == 2
    assert publicar(biblioteca.destino, almacen, recibo) == ref
    assert len(almacen.creaciones) == 2
    assert restaurar(ref, tmp_path / "recuperada", almacen) == biblioteca.manifest
    assert Biblioteca(tmp_path / "recuperada").detalle("fila-v4")["estado"] == "propuesta_pendiente"
    with pytest.raises(ValueError, match="nuevo"):
        restaurar(ref, tmp_path / "recuperada", almacen)
    alterado = deepcopy(ref)
    alterado["objetos"]["biblioteca.sqlite"]["uri"] = "gs://otro/biblioteca.sqlite"
    with pytest.raises(ValueError, match="pertenece"):
        restaurar(alterado, tmp_path / "otra", almacen)
    assert not (tmp_path / "otra").exists()
