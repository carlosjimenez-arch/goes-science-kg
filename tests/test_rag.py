from goes_science_kg.modelos import TipoNodo
from goes_science_kg.rag import BM25, GraphRAG, normalizar


def test_normalizar_quita_tildes_y_vacias():
    assert normalizar("La fotosíntesis de las plantas") == ["fotosintesis", "plantas"]


def test_bm25_prefiere_el_documento_pertinente():
    idx = BM25({"a": normalizar("circuito eléctrico en serie"), "b": normalizar("ciclo del agua y evaporación")})
    q = normalizar("circuito en serie")
    assert idx.puntaje(q, "a") > idx.puntaje(q, "b") == 0


def test_recuperacion_por_grado(grafo):
    rag = GraphRAG(*grafo)
    ctx = rag.recuperar("fotosíntesis y respiración celular", grado=6, k_final=15)
    temas = [n for n, _ in ctx.nodos if n.tipo == TipoNodo.TEMA]
    assert temas and all(t.grado == 6 for t in temas[:3])
    assert all(n.props.get("marco") != "T23" for n, _ in ctx.nodos)
    # Cada nodo del contexto es citable.
    assert "fuente:" in ctx.como_texto()


def test_recuperacion_por_asignatura(grafo):
    ctx = GraphRAG(*grafo).recuperar("enlace covalente y fuerzas intermoleculares", asignatura="quimica", k_final=10)
    assert ctx.nodos and all(n.asignatura in (None, "quimica") for n, _ in ctx.nodos)


def test_determinista(grafo):
    rag = GraphRAG(*grafo)
    a = [n.id for n, _ in rag.recuperar("ecosistemas y cadenas tróficas", grado=7).nodos]
    b = [n.id for n, _ in rag.recuperar("ecosistemas y cadenas tróficas", grado=7).nodos]
    assert a == b


def test_intencion_pais_reconoce_paises_y_gentilicios():
    from goes_science_kg.rag import INTENCION_PAISES, PAIS_NOMBRADO, _sin_tildes

    for consulta, codigo in [("¿Cómo enseña Japón las fases de la Luna?", "JP"),
                             ("¿Qué aprenden los estudiantes japoneses sobre solubilidad?", "JP"),
                             ("Currículo de Inglaterra en KS3", "ENG"), ("¿Y en Australia?", "AU")]:
        plano = _sin_tildes(consulta)
        assert INTENCION_PAISES.search(plano), consulta
        assert codigo in {c for p, c in PAIS_NOMBRADO.items() if p in plano}, consulta
