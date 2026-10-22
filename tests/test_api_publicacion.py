"""Reject mixed graph generations using regenerated derivatives in a temporary repository."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from goes_science_kg.api import crear_app  # noqa: E402
from goes_science_kg.grafo.almacen import guardar  # noqa: E402
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo  # noqa: E402


@pytest.fixture
def publicado(tmp_path, monkeypatch):
    from goes_science_kg import comunidades, grados
    from goes_science_kg.config import cargar

    # Las reglas se leen del repo real antes de cambiar exclusivamente el destino.
    cargar("asignaturas")
    cargar("referentes")
    nodos = [
        Nodo(id="ASIG:biologia", tipo=TipoNodo.ASIGNATURA, etiqueta="Biología"),
        Nodo(id="CON:biologia/fotosintesis", tipo=TipoNodo.CONCEPTO, etiqueta="Fotosíntesis", asignatura="biologia"),
    ]
    aristas = []
    for g in range(2, 12):
        tema = f"TEMA:G{g:02d}-CIE-U1-1.1"
        nodos.extend(
            [
                Nodo(id=f"GRADO:{g:02d}", tipo=TipoNodo.GRADO, etiqueta=f"Grado {g}", grado=g),
                Nodo(
                    id=tema,
                    tipo=TipoNodo.TEMA,
                    etiqueta="Fotosíntesis de las plantas",
                    grado=g,
                    asignatura="biologia",
                    props={"unidad": "Plantas"},
                ),
            ]
        )
        aristas.extend(
            [
                Arista(origen=tema, destino="CON:biologia/fotosintesis", tipo=TipoArista.TRABAJA, rol="principal"),
                Arista(origen=tema, destino="ASIG:biologia", tipo=TipoArista.DE_ASIGNATURA),
            ]
        )
    monkeypatch.setenv("GSKG_RAIZ", str(tmp_path))
    guardar(nodos, aristas, "prueba", directorio=str(tmp_path / "data/grafo"))
    comunidades.resumenes.cache_clear()
    try:
        grados.construir_grados(nodos, aristas, "prueba")
        yield SimpleNamespace(base=tmp_path, nodos=nodos, aristas=aristas, cliente=TestClient(crear_app(tmp_path)))
    finally:
        comunidades.resumenes.cache_clear()


def _simulacion(valor):
    return {
        "antes": {"secuencia_en_ciclo": valor},
        "despues": {"secuencia_en_ciclo": 0},
        "secuencia_alta_pendiente": [],
        "conceptos_no_resueltos": [],
    }


def _publicar_propuesta(publicado, monkeypatch, g0=5, g1=8, valor=4):
    from goes_science_kg import propuesta

    monkeypatch.setattr(propuesta, "simular", lambda *args: _simulacion(valor))
    return propuesta.escribir_simulacion("biologia", g0, g1, publicado.nodos, publicado.aristas)


def test_contratos_200_con_grados_realmente_regenerados(publicado):
    c = publicado.cliente
    assert c.get("/api/salud").json()["alcance"] == "grafo"
    grados = c.get("/api/grados")
    assert grados.status_code == 200 and [g["grado"] for g in grados.json()] == list(range(2, 12))
    assert "X-Articulos-No-Disponibles" not in grados.headers
    assert c.get("/api/grados/7").json()["diagnostico"]["grado"] == 7
    global_ = c.get("/api/rag/global", params={"q": "fotosíntesis", "grado": 7})
    assert global_.status_code == 200 and global_.json()[0]["grado"] == 7


@pytest.mark.parametrize("archivo", ["manifest.json", "nodos.jsonl", "aristas.jsonl"])
def test_mutar_grafo_o_manifiesto_tras_carga_bloquea_la_lectura_hasta_reiniciar(publicado, archivo):
    c = publicado.cliente
    assert c.get("/api/conceptos/biologia/fotosintesis").status_code == 200
    ruta = publicado.base / "data/grafo" / archivo
    original = ruta.read_bytes()
    ruta.write_bytes(original + b" ")
    assert c.get("/api/salud").status_code == 503
    assert c.get("/api/rag", params={"q": "fotosíntesis"}).status_code == 503
    ruta.write_bytes(original)
    assert c.get("/api/salud").status_code == 503
    assert TestClient(crear_app(publicado.base)).get("/api/salud").status_code == 200


@pytest.mark.parametrize("archivo", ["diagnostico.json", "comunidades.json"])
def test_mutacion_de_un_grado_no_mezcla_json_ni_bloquea_otros_articulos(publicado, archivo):
    c = publicado.cliente
    assert c.get("/api/grados/7").status_code == 200
    ruta = publicado.base / "data/grafo/grados/G07" / archivo
    ruta.write_bytes(ruta.read_bytes() + b" ")
    assert c.get("/api/grados/7").status_code == 503
    assert c.get("/api/rag/global", params={"q": "fotosíntesis", "grado": 7}).status_code == 503
    assert c.get("/api/grados/6").status_code == 200
    assert c.get("/api/conceptos/biologia/fotosintesis").status_code == 200
    parcial = c.get("/api/grados")
    assert parcial.status_code == 200 and len(parcial.json()) == 9
    assert parcial.headers["X-Articulos-No-Disponibles"] == "grado-G07"


def test_regeneracion_completa_de_grafo_no_se_recarga_implicitamente(publicado):
    c = publicado.cliente
    assert c.get("/api/salud").status_code == 200
    guardar(publicado.nodos, publicado.aristas, "segunda-generacion", directorio=str(publicado.base / "data/grafo"))
    assert c.get("/api/salud").status_code == 503
    nuevo = TestClient(crear_app(publicado.base))
    assert nuevo.get("/api/salud").json()["manifest"]["version"] == "segunda-generacion"


def test_legacy_sin_procedencia_no_se_adopta_por_coexistir_con_el_grafo(publicado):
    for archivo in (publicado.base / "data/grafo/publicaciones_api").glob("*.json"):
        archivo.unlink()
    c = publicado.cliente
    assert c.get("/api/grados/7").status_code == 503
    assert c.get("/api/salud").status_code == 200
    assert c.get("/api/conceptos/biologia/fotosintesis").status_code == 200


def test_publicacion_inicial_con_derivado_distinto_se_rechaza(publicado):
    ruta = publicado.base / "data/grafo/grados/G07/diagnostico.json"
    d = json.loads(ruta.read_text())
    d["temas"] = 999
    ruta.write_text(json.dumps(d))
    assert publicado.cliente.get("/api/grados/7").status_code == 503
    assert publicado.cliente.get("/api/grados/6").status_code == 200


def test_un_articulo_no_puede_atribuirse_a_otro_grafo(publicado):
    ruta = publicado.base / "data/grafo/publicaciones_api/grado-G07.json"
    d = json.loads(ruta.read_text())
    d["grafo"]["nodos.jsonl"] = "a" * 64
    ruta.write_text(json.dumps(d))
    assert publicado.cliente.get("/api/grados/7").status_code == 503


def test_simulacion_legacy_se_recalcula_antes_de_publicar(publicado, monkeypatch):
    ruta = publicado.base / "asignaturas/biologia/propuesta/simulacion_G05-G08.json"
    ruta.parent.mkdir(parents=True)
    ruta.write_text(json.dumps(_simulacion(999)))
    c = publicado.cliente
    assert c.get("/api/propuestas").status_code == 503
    _publicar_propuesta(publicado, monkeypatch, valor=4)
    r = c.get("/api/propuestas")
    assert r.status_code == 200 and r.json()[0]["antes"]["secuencia_en_ciclo"] == 4


def test_propuesta_mutada_o_borrada_no_bloquea_otra_publicada(publicado, monkeypatch):
    _publicar_propuesta(publicado, monkeypatch, 5, 8)
    _publicar_propuesta(publicado, monkeypatch, 2, 4)
    c = publicado.cliente
    assert len(c.get("/api/propuestas").json()) == 2
    ruta = publicado.base / "asignaturas/biologia/propuesta/simulacion_G05-G08.json"
    ruta.write_text(json.dumps(_simulacion(666)))
    r = c.get("/api/propuestas")
    assert r.status_code == 200 and [p["ciclo"] for p in r.json()] == ["G02-G04"]
    assert r.headers["X-Articulos-No-Disponibles"] == "propuesta-biologia-G05-G08"
    ruta.unlink()
    (publicado.base / "data/grafo/publicaciones_api/propuesta-biologia-G05-G08.json").unlink()
    assert c.get("/api/propuestas").headers["X-Articulos-No-Disponibles"] == "propuesta-biologia-G05-G08"
    assert c.get("/api/salud").status_code == 200


def test_generador_rechaza_modelos_ajenos_antes_de_escribir(publicado):
    from goes_science_kg.grados import construir_grados

    nodos = [n.model_copy(update={"etiqueta": "Entrada modificada"}) for n in publicado.nodos]
    ruta = publicado.base / "data/grafo/grados/G07/diagnostico.json"
    antes = ruta.read_bytes()
    with pytest.raises(ValueError, match="no coinciden"):
        construir_grados(nodos, publicado.aristas, "prueba")
    assert ruta.read_bytes() == antes


def test_no_se_publica_si_el_grafo_cambia_durante_la_generacion(publicado, monkeypatch):
    from goes_science_kg import propuesta

    def cambiar_grafo(*args):
        modificados = [n.model_copy(update={"etiqueta": "Nueva entrada"}) for n in publicado.nodos]
        guardar(modificados, publicado.aristas, "nuevo", directorio=str(publicado.base / "data/grafo"))
        return _simulacion(4)

    monkeypatch.setattr(propuesta, "simular", cambiar_grafo)
    with pytest.raises(ValueError, match="cambió"):
        propuesta.escribir_simulacion("biologia", 5, 8, publicado.nodos, publicado.aristas)
    assert not (publicado.base / "data/grafo/publicaciones_api/propuesta-biologia-G05-G08.json").exists()


def test_inicializacion_concurrente_captura_una_sola_instancia(publicado, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from time import sleep

    from goes_science_kg import api

    original = api.LecturaPublicada
    llamadas = []

    class LecturaLenta(original):
        def __init__(self, base):
            llamadas.append(base)
            # Amplía la ventana en la que un cache sin exclusión duplicaría carga.
            sleep(0.03)
            super().__init__(base)

    monkeypatch.setattr(api, "LecturaPublicada", LecturaLenta)
    aplicacion = api.crear_app(publicado.base)
    barrera = Barrier(4)

    def consultar(_):
        barrera.wait(timeout=5)
        return TestClient(aplicacion).get("/api/salud")

    with ThreadPoolExecutor(max_workers=4) as pool:
        respuestas = list(pool.map(consultar, range(4)))
    assert all(r.status_code == 200 for r in respuestas)
    assert len(llamadas) == 1


@pytest.mark.parametrize("enlace", ["directorio", "archivo"])
def test_publicacion_no_escribe_a_traves_de_enlaces_fuera_del_repo(publicado, enlace):
    from goes_science_kg.publicacion_api import comprobar_entrada, publicar_articulo

    externo = publicado.base.parent / f"externo-{publicado.base.name}"
    externo.mkdir()
    publicaciones = publicado.base / "data/grafo/publicaciones_api"
    if enlace == "directorio":
        publicaciones.rename(publicado.base / "publicaciones_originales")
        publicaciones.symlink_to(externo, target_is_directory=True)
    else:
        destino = externo / "no-tocar.json"
        destino.write_text("Conservar")
        (publicaciones / "grado-G07.json").unlink()
        (publicaciones / "grado-G07.json").symlink_to(destino)
    antes = {p.name: p.read_bytes() for p in externo.iterdir()}
    huellas = comprobar_entrada(publicado.nodos, publicado.aristas, base=publicado.base)
    with pytest.raises(ValueError, match="fuera del repositorio"):
        publicar_articulo(
            "grado-G07",
            ["data/grafo/grados/G07/diagnostico.json", "data/grafo/grados/G07/comunidades.json"],
            huellas,
            generador="prueba",
            base=publicado.base,
        )
    assert {p.name: p.read_bytes() for p in externo.iterdir()} == antes
    assert publicado.cliente.get("/api/grados/7").status_code == 503
    assert publicado.cliente.get("/api/salud").status_code == 200
