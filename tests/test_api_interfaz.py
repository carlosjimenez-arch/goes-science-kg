"""Test repository-backed application filters, evidence, abstention, and zero model calls."""

from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from test_mejoras_curriculares import caso as caso
from test_mejoras_entrega import entrega as entrega

from goes_science_kg.api_interfaz import crear_router_interfaz, registrar_interfaz
from goes_science_kg.curriculo.contratos import CeldaCurricular
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.motor.registro import Registro


@pytest.fixture
def aplicacion(entrega, tmp_path):
    curriculo, archivo = entrega
    fila = curriculo.filas[0]
    celda = CeldaCurricular(
        coordenada="C3",
        fila=3,
        columna="C",
        campo="procedimental",
        valor=fila.procedimental,
        valor_original=fila.procedimental,
        tipo_excel="s",
    )
    curriculo = SimpleNamespace(filas=(fila.model_copy(update={"celdas": (celda,)}),))
    fuente = SimpleNamespace(
        catalogo={"fuente1": {"sha256": "a" * 64, "version_curriculo": "V4"}},
        bloqueos_efectivos={"fila1": "Errata documentada: el original sigue vetado."},
        hidratar_celdas=lambda d: (SimpleNamespace(id="prueba-verificada"),),
    )
    nodos = (
        Nodo(id="fila1", tipo=TipoNodo.TEMA, etiqueta=curriculo.filas[0].procedimental, grado=3),
        Nodo(id="unidad1", tipo=TipoNodo.UNIDAD, etiqueta="Materia", grado=3),
        Nodo(id="DOC:fuente1", tipo=TipoNodo.DOCUMENTO, etiqueta="Fuente sintética"),
    )
    producto = SimpleNamespace(
        curriculo=curriculo,
        mejoras=archivo,
        manifest=SimpleNamespace(snapshot_id="d" * 64, sha256={"mejoras.json": "a" * 64}),
        catalogo=SimpleNamespace(
            filas=(SimpleNamespace(fila_id="fila1", disciplinas=("fisica",), estado="coincidencia"),)
        ),
        nodos=nodos,
        aristas=(
            Arista(origen="fila1", destino="unidad1", tipo=TipoArista.EN_UNIDAD),
            Arista(origen="fila1", destino="DOC:fuente1", tipo=TipoArista.FUENTE),
        ),
    )
    runtime = SimpleNamespace(producto=producto, fuentes=fuente)
    lecturas = []

    def leer():
        lecturas.append(True)
        return runtime

    app = FastAPI()
    app.include_router(crear_router_interfaz(leer, tmp_path), prefix="/api/v4")
    registrar_interfaz(app)
    return SimpleNamespace(cliente=TestClient(app), runtime=runtime, app=app, lecturas=lecturas, base=tmp_path)


def test_inicio_usa_assets_locales_sin_semilla_ni_dependencias_remotas(aplicacion):
    c = aplicacion.cliente
    r = c.get("/", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/app/"
    html = c.get("/app/")
    assert html.status_code == 200
    assert 'id="seed"' not in html.text and "Matemática" not in html.text
    assert "fonts.googleapis.com" not in html.text and "cdnjs.cloudflare.com" not in html.text
    assert "script-src 'self'" in html.headers["content-security-policy"]
    assert html.headers["cache-control"] == "private, no-store"
    for nombre in ("producto.js", "cliente.js", "grafo.js", "iconos.js", "producto.css", "ciencias.css"):
        assert c.get("/app/" + nombre).status_code == 200
    assert c.get("/app/inter-latin.woff2").content[:4] == b"wOF2"
    assert c.get("/app/OFL-Inter.txt").status_code == 200
    assert c.get("/app/..%2F..%2F.env").status_code == 404


def test_resumen_no_inventa_metricas_nacionales_y_conserva_denominador(aplicacion):
    d = aplicacion.cliente.get("/api/v4/interfaz/resumen").json()
    assert d["snapshot_id"] == "d" * 64 and d["cobertura"]["filas"] == 1
    assert d["nodos"] == 3 and d["aristas"] == 2 and d["alertas_originales"] == 1
    assert d["grados"] == [{"grado": 3, "filas": 1, "unidades": 1, "propuestas_ciencias": 1, "alertas_originales": 1}]
    assert d["integraciones"]["lxp"]["escuelas"] is None
    assert d["integraciones"]["territorio"]["departamentos"] is None
    assert d["integraciones"]["aprobacion_institucional"]["estado"] == "no_acreditada"


@pytest.mark.parametrize(
    "consulta,total",
    [
        ("", 1),
        ("?grado=3&disciplina=fisica", 1),
        ("?q=MATERÍA", 1),
        ("?grado=4", 0),
        ("?disciplina=quimica", 0),
        ("?q=no-existe", 0),
        ("?solo_alertas=true", 1),
        ("?offset=1", 1),
    ],
)
def test_filtros_y_paginacion_se_aplican_al_mismo_snapshot(aplicacion, consulta, total):
    d = aplicacion.cliente.get("/api/v4/interfaz/filas" + consulta).json()
    assert d["total"] == total and d["snapshot_id"] == "d" * 64
    if "offset=1" in consulta:
        assert not d["filas"]


@pytest.mark.parametrize("consulta", ["?grado=1", "?limite=10000", "?offset=-1", "?disciplina=matematica"])
def test_filtros_invalidos_no_se_convierten_en_resultados(aplicacion, consulta):
    assert aplicacion.cliente.get("/api/v4/interfaz/filas" + consulta).status_code == 422


def test_detalle_y_brief_conservan_alerta_y_texto_sin_nuevos_votos(aplicacion):
    c = aplicacion.cliente
    antes = deepcopy(aplicacion.runtime.producto.mejoras.unidades)
    respuesta = c.get("/api/v4/interfaz/filas/fila1")
    assert respuesta.status_code == 200
    detalle = respuesta.json()
    assert detalle["alerta_original"] and detalle["propuesta"]["objetivo_propuesto"]
    assert len(detalle["revisiones"]["dictamenes"]) == 4
    r = c.post("/api/v4/interfaz/briefs", json={"filas_ids": ["fila1"], "formato": "cinco_fases"})
    assert r.status_code == 200
    brief = r.json()["briefs"][0]
    assert brief["llamadas_modelos"] == 0 and r.json()["llamadas_modelos"] == 0
    assert detalle["propuesta"]["objetivo_propuesto"] in brief["markdown"]
    assert "Ausente en el insumo" in brief["markdown"] and "d" * 64 in brief["markdown"]
    assert aplicacion.runtime.producto.mejoras.unidades == antes


def test_fuente_modificada_impide_detalle_y_compilar_brief(aplicacion):
    c = aplicacion.cliente
    assert c.get("/api/v4/interfaz/resumen").status_code == 200

    def cambiada(_):
        raise ValueError("La fuente cambió")

    aplicacion.runtime.fuentes.hidratar_celdas = cambiada
    assert c.get("/api/v4/interfaz/filas/fila1").status_code == 503
    assert c.get("/api/v4/interfaz/nodos/fila1").status_code == 503
    assert c.post("/api/v4/interfaz/briefs", json={"filas_ids": ["fila1"]}).status_code == 503


def test_grafo_devuelve_solo_relaciones_reales_con_extremos_presentes(aplicacion):
    c = aplicacion.cliente
    d = c.get("/api/v4/interfaz/grafo?grado=3").json()
    ids = {n["id"] for n in d["nodos"]}
    assert len(ids) == 3 and len(d["aristas"]) == 2
    assert all(a["origen"] in ids and a["destino"] in ids for a in d["aristas"])
    assert {a["tipo"] for a in d["aristas"]} == {"EN_UNIDAD", "FUENTE"}
    assert c.get("/api/v4/interfaz/grafo?grado=4").json()["nodos"] == []
    assert c.get("/api/v4/interfaz/nodos/no-existe").status_code == 404


def test_corpus_no_convierte_url_de_contenido_en_javascript(aplicacion):
    aplicacion.runtime.fuentes.catalogo["fuente1"]["url"] = "javascript:alert('x')"
    d = aplicacion.cliente.get("/api/v4/interfaz/documentos?tipo=curriculo").json()
    assert d["total"] == 1 and d["documentos"][0]["url"] is None


@pytest.mark.parametrize(
    "solicitud,estado",
    [
        ({"filas_ids": ["otra"]}, 404),
        ({"filas_ids": ["fila1", "fila1"]}, 422),
        ({"filas_ids": []}, 422),
        ({"filas_ids": ["fila1"] * 21}, 422),
        ({"filas_ids": ["fila1"], "formato": "inventar"}, 422),
    ],
)
def test_briefs_rechaza_identidades_y_formatos_ajenos(aplicacion, solicitud, estado):
    assert aplicacion.cliente.post("/api/v4/interfaz/briefs", json=solicitud).status_code == estado


def test_administracion_no_crea_usuarios_ni_toma_reserva_por_factura(aplicacion):
    d = aplicacion.cliente.get("/api/v4/interfaz/administracion").json()
    assert d["usuarios"] is None and d["actividad_vertex"] is None
    assert not d["permisos"]["gestion_usuarios"] and not d["permisos"]["generacion_modelos"]
    # El ledger existe, pero consultar sólo debe leer sus bytes.
    ledger = aplicacion.base / "data/operaciones/registro.sqlite"
    Registro(ledger)
    antes = ledger.read_bytes()
    d = aplicacion.cliente.get("/api/v4/interfaz/administracion").json()
    assert d["actividad_vertex"]["llamadas"] == 0
    assert d["actividad_vertex"]["importe_facturado"] is None
    assert ledger.read_bytes() == antes


def test_cada_consulta_revalida_lector_aunque_proyeccion_este_cacheada(aplicacion):
    c = aplicacion.cliente
    assert c.get("/api/v4/interfaz/resumen").status_code == 200
    assert c.get("/api/v4/interfaz/documentos").status_code == 200
    assert len(aplicacion.lecturas) == 2


def test_publicacion_invalida_no_ofrece_semilla_o_datos_de_matematicas(tmp_path):
    def leer():
        raise HTTPException(503, "Publicación invalidada")

    app = FastAPI()
    app.include_router(crear_router_interfaz(leer, tmp_path), prefix="/api/v4")
    assert TestClient(app).get("/api/v4/interfaz/resumen").status_code == 503


def test_static_no_distribuye_el_seed_original():
    raiz = Path(__file__).parents[1] / "src/goes_science_kg/interfaz/estaticos"
    scripts = "".join(p.read_text() for p in raiz.glob("*.js"))
    assert "const SEED" not in scripts and "Math.random" not in scripts and "function motor(" not in scripts


def test_identidad_de_concepto_con_barra_se_resuelve_sin_ruta_de_archivo(aplicacion):
    """Encoded concept IDs must remain addressable after ASGI URL decoding."""
    from urllib.parse import quote

    id_ = "CON:fisica/sistema-internacional-unidades"
    nodo = Nodo(id=id_, tipo=TipoNodo.CONCEPTO, etiqueta="Sistema Internacional de Unidades", grado=3)
    producto = aplicacion.runtime.producto
    producto.nodos = (*producto.nodos, nodo)
    respuesta = aplicacion.cliente.get("/api/v4/interfaz/nodos/" + quote(id_, safe=""))
    assert respuesta.status_code == 200
    assert respuesta.json()["nodo"]["id"] == id_
    assert respuesta.json()["relaciones"] == []


def test_campana_sin_registros_no_acredita_reserva_cero(aplicacion):
    """An existing empty ledger must not imply measured zero spending."""
    Registro(aplicacion.base / "data/operaciones/registro.sqlite")
    actividad = aplicacion.cliente.get("/api/v4/interfaz/administracion").json()["actividad_vertex"]
    assert actividad["estado"] == "sin_datos"
    assert actividad["reserva_usd"] is None
    assert actividad["importe_facturado"] is None


def test_url_documental_malformada_no_rompe_el_corpus(aplicacion):
    """Reject invalid URL authorities instead of raising an internal server error."""
    aplicacion.runtime.fuentes.catalogo["fuente1"]["url"] = "https://[host-invalido"
    respuesta = aplicacion.cliente.get("/api/v4/interfaz/documentos")
    assert respuesta.status_code == 200
    assert respuesta.json()["documentos"][0]["url"] is None


def test_openapi_describe_respuestas_publicas_tipadas(aplicacion):
    """Expose stable schemas for the application integration boundary."""
    esquema = aplicacion.cliente.get("/openapi.json").json()
    assert "PaginaFilas" in esquema["components"]["schemas"]
    respuesta = esquema["paths"]["/api/v4/interfaz/filas"]["get"]["responses"]["200"]
    assert respuesta["content"]["application/json"]["schema"]["$ref"].endswith("PaginaFilas")


def _progresion(aplicacion, snapshot_id):
    import json

    from goes_science_kg.producto import progresion_v4 as p4

    fila = aplicacion.runtime.producto.curriculo.filas[0]
    etiquetado = {
        "snapshot_id": snapshot_id,
        "etiquetas": [
            {"fila_id": fila.id, "origen": "original", "conceptos": ["CON:fisica/fuerza"], "practicas": ["PRAC:medir"]}
        ],
    }
    voc = {"CON:fisica/fuerza": {"nombre": "Fuerza", "asignatura": "fisica", "nivel": "primaria"}}
    filas = {fila.id: {"grado": fila.grado, "dominios_timss": ("conocer",)}}
    doc = p4.construir(filas, etiquetado, voc, [], etiquetas_v3={}, pares_v3_v4=[], procedencia={"prueba": True})
    archivo = aplicacion.base / "data/producto/progresion_v4/progresion.json"
    archivo.parent.mkdir(parents=True, exist_ok=True)
    archivo.write_text(json.dumps(doc), encoding="utf-8")
    return fila


def test_progresion_sin_artefacto_declara_que_no_hay_datos(aplicacion):
    r = aplicacion.cliente.get("/api/v4/interfaz/progresion")
    assert r.status_code == 503 and "No hay datos disponibles" in r.json()["detail"]


def test_progresion_de_otra_publicacion_no_se_sirve(aplicacion):
    _progresion(aplicacion, "e" * 64)
    assert aplicacion.cliente.get("/api/v4/interfaz/progresion/conceptos").status_code == 503


def test_progresion_filtra_y_devuelve_las_filas_de_cada_grado(aplicacion):
    fila = _progresion(aplicacion, "d" * 64)
    c = aplicacion.cliente
    resumen = c.get("/api/v4/interfaz/progresion").json()
    assert resumen["conceptos_presentes"] == 1 and resumen["patrones"]["aislado"] == 1
    assert c.get("/api/v4/interfaz/progresion/conceptos", params={"disciplina": "fisica"}).json()["total"] == 1
    assert c.get("/api/v4/interfaz/progresion/conceptos", params={"disciplina": "quimica"}).json()["total"] == 0
    assert c.get("/api/v4/interfaz/progresion/conceptos", params={"patron": "otro"}).status_code == 422
    detalle = c.get("/api/v4/interfaz/progresion/conceptos/CON:fisica/fuerza").json()["concepto"]
    assert detalle["filas"][str(fila.grado)][0]["procedimental"] == fila.procedimental
    assert c.get("/api/v4/interfaz/progresion/conceptos/CON:fisica/otro").status_code == 404
