"""Test retrieval relevance and curriculum-version isolation."""

from __future__ import annotations

import json

import pytest

from goes_science_kg.modelos import Arista, Fuente, Nodo, TipoArista, TipoNodo
from goes_science_kg.recuperacion import (
    Buscador,
    Documento,
    Enlace,
    IndiceEmbeddings,
    aristas_del_grafo,
    cargar_buscador_grafo,
    cargar_documentos_grafo,
    documentos_del_grafo,
    huella_corpus,
)
from goes_science_kg.recuperacion.lexico import normalizar


def _documento(documento_id: str, texto: str, **campos) -> Documento:
    return Documento(
        id=documento_id,
        texto=texto,
        fuente={"documento": "curriculo.pdf", "pagina": 3},
        version=campos.pop("version", "V4"),
        **campos,
    )


@pytest.fixture
def corpus():
    return [
        _documento("agua", "El ciclo del agua y la evaporación", grado=5, asignatura="fisica"),
        _documento("plantas", "Fotosíntesis: plantas transforman luz solar en energía", grado=5, asignatura="biologia"),
        _documento("enlaces", "Enlaces químicos y moléculas de agua", grado=9, asignatura="quimica"),
        _documento("marco", "Las plantas requieren energía de la luz", version="referencia", asignatura="biologia"),
    ]


def test_recupera_relevancia_sin_completar_con_documentos_ajenos(corpus):
    resultados = Buscador(corpus).buscar("FOTOSINTESIS", k=3, saltos_grafo=0)
    assert [r.documento.id for r in resultados] == ["plantas"]
    assert resultados[0].canales == ("bm25",)
    assert Buscador(corpus).buscar("tectónica", k=3) == []


def test_normalizacion_espanol_y_formula_unicode():
    assert normalizar("¿QUÍMICA? H₂O — presión") == ["quimica", "h2o", "presion"]


def test_filtra_grado_asignatura_y_conserva_referencias(corpus):
    resultados = Buscador(corpus).buscar("plantas energía agua", version="V4", grado=5, asignatura="BIOLOGÍA")
    assert {r.documento.id for r in resultados} == {"plantas", "marco"}
    assert Buscador(corpus).buscar("enlaces", grado=5) == []


def test_no_sustituye_una_version_inexistente(corpus):
    with pytest.raises(ValueError, match="versión curricular V5"):
        Buscador(corpus).buscar("energía", version="V5")


def test_varias_mallas_exigen_filtro_explicito():
    documentos = [_documento("viejo", "energía", version="V3"), _documento("nuevo", "energía")]
    buscador = Buscador(documentos)
    with pytest.raises(ValueError, match="varias mallas"):
        buscador.buscar("energía")
    assert [r.documento.id for r in buscador.buscar("energía", version="V4")] == ["nuevo"]


def test_rechaza_duplicados_y_devuelve_copias(corpus):
    with pytest.raises(ValueError, match="duplicados"):
        Buscador([corpus[0], corpus[0]])
    buscador = Buscador(corpus)
    resultado = buscador.buscar("fotosintesis")[0]
    resultado.documento.fuente["pagina"] = 100
    assert buscador.buscar("fotosintesis")[0].documento.fuente["pagina"] == 3


def test_expansion_dirigida_con_cupo_y_sin_cruzar_filtros():
    documentos = [_documento("inicio", "fotosíntesis", grado=5)] + [
        _documento(f"base{i}", "conocimiento previo", grado=5) for i in range(20)
    ]
    documentos.append(_documento("otro_grado", "conocimiento previo", grado=9))
    enlaces = [Enlace(origen="inicio", destino=d.id, tipo="requiere") for d in documentos[1:]]
    buscador = Buscador(documentos, aristas=enlaces, max_vecinos=3)
    resultado = buscador.buscar("fotosintesis", grado=5, k=10)
    assert len(resultado) == 4
    assert "otro_grado" not in {r.documento.id for r in resultado}
    assert all(r.canales == ("grafo",) for r in resultado[1:])
    assert buscador.buscar("conocimiento", k=30, saltos_grafo=1)[-1].documento.id != "inicio"


def test_direccion_prerrequisito_y_cubre():
    enlaces = aristas_del_grafo(
        [
            Arista(origen="base", destino="avanzado", tipo=TipoArista.PRERREQUISITO_DE),
            Arista(origen="tema", destino="marco", tipo=TipoArista.CUBRE),
            Arista(origen="tema", destino="grado", tipo=TipoArista.EN_GRADO),
        ]
    )
    assert {(a.origen, a.destino) for a in enlaces} == {("avanzado", "base"), ("tema", "marco")}


def test_corpus_cambia_con_texto_fuente_y_version_pero_no_orden(corpus):
    assert huella_corpus(corpus) == huella_corpus(reversed(corpus))
    for cambios in ({"texto": "nuevo texto"}, {"fuente": {"documento": "otro.pdf"}}, {"version": "V3"}):
        nuevo = [corpus[0].model_copy(update=cambios), *corpus[1:]]
        assert huella_corpus(nuevo) != huella_corpus(corpus)


def test_embeddings_rrf_resuelve_sinonimo_y_combina_canales():
    pytest.importorskip("numpy")
    documentos = [_documento("cambio", "Transición entre líquido y vapor"), _documento("solar", "Energía solar")]
    indice = IndiceEmbeddings(documentos, [[1, 0], [0, 1]], modelo="modelo-a")
    buscador = Buscador(documentos, indice_embeddings=indice)
    assert buscador.buscar("evaporación") == []
    resultado = buscador.buscar("evaporación", vector_consulta=[1, 0], modelo_embeddings="modelo-a", k=1)
    assert resultado[0].documento.id == "cambio"
    resultado = buscador.buscar("solar", vector_consulta=[0, 1], modelo_embeddings="modelo-a", k=1)
    assert resultado[0].documento.id == "solar"
    assert resultado[0].canales == ("bm25", "denso")


def test_embeddings_preserva_correspondencia_vectores_en_orden_original():
    pytest.importorskip("numpy")
    documentos = [_documento("z", "vapor"), _documento("a", "plantas")]
    indice = IndiceEmbeddings(documentos, [[1, 0], [0, 1]], modelo="a")
    resultado = Buscador(documentos, indice_embeddings=indice).buscar(
        "sinónimo",
        vector_consulta=[1, 0],
        modelo_embeddings="a",
        k=1,
    )
    assert resultado[0].documento.id == "z"


def test_embeddings_rechaza_corpus_modelo_dimensiones_y_nan(corpus):
    pytest.importorskip("numpy")
    documentos = corpus[:2]
    indice = IndiceEmbeddings(documentos, [[1, 0], [0, 1]], modelo="a")
    with pytest.raises(ValueError, match="corpus cambió"):
        Buscador([documentos[0].model_copy(update={"texto": "cambió"}), documentos[1]], indice_embeddings=indice)
    for vector, modelo, mensaje in [
        ([1, 0], "b", "otro modelo"),
        ([1], "a", "Dimensión"),
        ([float("nan"), 0], "a", "no finitos"),
        ([0, 0], "a", "norma"),
    ]:
        with pytest.raises(ValueError, match=mensaje):
            indice.buscar(vector, modelo=modelo, permitidos={d.id for d in documentos}, limite=2)


@pytest.mark.parametrize("vectores", [[[0, 0]], [[float("nan"), 1]], [[1, 0], [0, 1]], [1, 2]])
def test_matriz_embedding_invalida(vectores):
    pytest.importorskip("numpy")
    with pytest.raises(ValueError):
        IndiceEmbeddings([_documento("a", "energía")], vectores, modelo="a")


def test_persistencia_embedding_valida_hash_y_modelo(tmp_path, corpus):
    pytest.importorskip("numpy")
    documentos = corpus[:2]
    archivo = tmp_path / "indice.npz"
    IndiceEmbeddings(documentos, [[1, 0], [0, 1]], modelo="a").guardar(archivo)
    indice = IndiceEmbeddings.cargar(archivo, reversed(documentos), modelo="a")
    assert indice.buscar([1, 0], modelo="a", permitidos={"agua", "plantas"}, limite=1)[0][0] == "agua"
    with pytest.raises(ValueError, match="otro modelo"):
        IndiceEmbeddings.cargar(archivo, documentos, modelo="b")
    with pytest.raises(ValueError, match="otro corpus"):
        IndiceEmbeddings.cargar(archivo, documentos[:1], modelo="a")


def test_adaptador_grafo_etiqueta_derivacion_y_preserva_fuente():
    nodos = [
        Nodo(
            id="tema",
            tipo=TipoNodo.TEMA,
            etiqueta="La célula",
            grado=5,
            fuente=Fuente(documento="malla.xlsx", hoja="Unidad 1", fila=3),
            props={"version_curriculo": "V4"},
        ),
        Nodo(id="concepto", tipo=TipoNodo.CONCEPTO, etiqueta="Célula"),
    ]
    tema, concepto = documentos_del_grafo(nodos, version="V4")
    assert tema.version == "V4" and tema.fuente["fila"] == 3
    assert concepto.version == "referencia" and concepto.fuente["tipo"] == "derivada"
    assert concepto.metadata["fuente_primaria"] is False
    with pytest.raises(ValueError, match="No se puede etiquetar"):
        documentos_del_grafo(nodos, version="V5")


def test_manifiesto_formato_no_cambia_version_curricular(tmp_path, monkeypatch):

    (tmp_path / "nodos.jsonl").write_text(Nodo(id="tema", tipo=TipoNodo.TEMA, etiqueta="Célula").model_dump_json())
    (tmp_path / "aristas.jsonl").write_text("")
    import hashlib

    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "version": "v1",
                "version_curriculo": "V3",
                "sha256": {
                    n: hashlib.sha256((tmp_path / n).read_bytes()).hexdigest() for n in ("nodos.jsonl", "aristas.jsonl")
                },
            }
        )
    )
    assert cargar_documentos_grafo(tmp_path)[0].version == "V3"
    with pytest.raises(ValueError, match="contiene V3"):
        cargar_documentos_grafo(tmp_path, version="V4")
    buscador = cargar_buscador_grafo(tmp_path)
    assert buscador.buscar("célula", version="V3")[0].documento.id == "tema"


def test_huella_buscador_cambia_con_aristas_y_parametros(corpus):
    base = Buscador(corpus)
    enlace = Enlace(origen="agua", destino="plantas", tipo="TRABAJA")
    assert Buscador(corpus, aristas=[enlace]).huella != base.huella
    assert Buscador(corpus, constante_rrf=61).huella != base.huella
    assert Buscador(reversed(corpus)).huella == base.huella


def test_metricas_no_ocultan_ids_relevantes_ausentes():
    from goes_science_kg.recuperacion.evaluacion import metricas_recuperacion

    preguntas = [{"id": "q", "relevantes": ["presente", "ausente"]}]
    resultado = metricas_recuperacion(preguntas, [["presente"]], ks=(1, 10))
    assert resultado["recall@10"] == 0.5
    assert resultado["mrr"] == 1.0
    with pytest.raises(ValueError, match="carece de relevantes"):
        metricas_recuperacion([{"id": "q", "relevantes": []}], [[]])


def test_adaptador_baseline_preserva_ranking_historico():
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.rag import GraphRAG
    from goes_science_kg.recuperacion import cargar_buscador_baseline

    nodos, aristas = cargar()
    baseline = GraphRAG(nodos, aristas)
    adaptado = cargar_buscador_baseline()
    consulta = "¿Qué debe aprenderse antes de la fotosíntesis?"
    esperado = baseline.recuperar(consulta, grado=7, asignatura="biologia", k_final=10)
    real = adaptado.buscar(consulta, grado=7, asignatura="biologia", k=10)
    assert [(r.documento.id, r.puntaje) for r in real] == [(n.id, p) for n, p in esperado.nodos]


def test_vertex_embedding_cache_task_presupuesto_y_ledger(tmp_path):
    pytest.importorskip("google.genai")
    from types import SimpleNamespace

    from goes_science_kg.recuperacion.vertex_embeddings import PresupuestoEmbeddingsAgotado, VertexEmbeddings

    llamadas = []

    def generar(**campos):
        llamadas.append(campos)
        return SimpleNamespace(
            embeddings=[
                SimpleNamespace(
                    values=[1.0] * 768,
                    statistics=SimpleNamespace(token_count=4, truncated=False),
                )
            ]
        )

    configuracion = {
        "proyecto": "proyecto-prueba",
        "directorio_cache": tmp_path / "cache",
        "ledger": tmp_path / "ledger.jsonl",
        "max_requests": 1,
        "cliente": SimpleNamespace(models=SimpleNamespace(embed_content=generar)),
    }
    proveedor = VertexEmbeddings(**configuracion)
    primero = proveedor.vectorizar_texto("texto público", tarea="RETRIEVAL_DOCUMENT")
    segundo = proveedor.vectorizar_texto("texto público", tarea="RETRIEVAL_DOCUMENT")
    assert primero.tolist() == segundo.tolist()
    assert len(llamadas) == 1
    assert llamadas[0]["config"].auto_truncate is False
    assert llamadas[0]["config"].task_type == "RETRIEVAL_DOCUMENT"
    assert proveedor.resumen()["cache_hits"] == 1
    assert "texto público" not in (tmp_path / "ledger.jsonl").read_text()
    with pytest.raises(PresupuestoEmbeddingsAgotado):
        proveedor.vectorizar_texto("texto público", tarea="RETRIEVAL_QUERY")
    restaurado = VertexEmbeddings(**configuracion)
    assert restaurado.resumen()["requests_reservadas"] == 1
    assert restaurado.resumen()["tokens_reportados"] == 4


def test_vertex_no_cachea_respuesta_truncada(tmp_path):
    pytest.importorskip("google.genai")
    from types import SimpleNamespace

    from goes_science_kg.recuperacion.vertex_embeddings import VertexEmbeddings

    respuesta = SimpleNamespace(
        embeddings=[
            SimpleNamespace(
                values=[1.0] * 768,
                statistics=SimpleNamespace(token_count=4, truncated=True),
            )
        ]
    )
    cliente = SimpleNamespace(models=SimpleNamespace(embed_content=lambda **campos: respuesta))
    proveedor = VertexEmbeddings(
        proyecto="prueba",
        directorio_cache=tmp_path / "cache",
        ledger=tmp_path / "ledger",
        cliente=cliente,
    )
    with pytest.raises(ValueError, match="truncamiento"):
        proveedor.vectorizar_texto("texto", tarea="RETRIEVAL_QUERY")
    assert not list((tmp_path / "cache").rglob("*.npz"))
    assert proveedor.resumen()["errores"] == 1


def test_experimento_no_amplia_el_numero_de_preguntas_autorizado():
    from goes_science_kg.recuperacion.experimento_vertex import ejecutar_experimento

    with pytest.raises(ValueError):
        ejecutar_experimento(proyecto="prueba", max_preguntas_autorizadas=100)


def test_cancelacion_embedding_interrumpe_pendientes(tmp_path, monkeypatch):
    from goes_science_kg.recuperacion.vertex_embeddings import VertexEmbeddings

    proveedor = VertexEmbeddings(proyecto="prueba", directorio_cache=tmp_path / "cache", ledger=tmp_path / "ledger")

    def interrumpir(texto, *, tarea):
        raise KeyboardInterrupt

    monkeypatch.setattr(proveedor, "vectorizar_texto", interrumpir)
    with pytest.raises(KeyboardInterrupt):
        proveedor.vectorizar(["uno", "dos", "tres"], tarea="RETRIEVAL_DOCUMENT")
    assert proveedor._abortar.is_set()
