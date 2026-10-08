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
    import re

    from goes_science_kg.rag import INTENCION_PAISES, PAIS_NOMBRADO, _sin_tildes

    def nombrados(plano):
        return {c for p, c in PAIS_NOMBRADO.items() if re.search(rf"\b(?:{p})\b", plano)}

    for consulta, codigo in [("¿Cómo enseña Japón las fases de la Luna?", "JP"),
                             ("¿Qué aprenden los estudiantes japoneses sobre solubilidad?", "JP"),
                             ("Currículo de Inglaterra en KS3", "ENG"), ("¿Y en Australia?", "AU")]:
        plano = _sin_tildes(consulta)
        assert INTENCION_PAISES.search(plano), consulta
        assert codigo in nombrados(plano), consulta
    # palabras comunes que no son intención de país (revisión de código 2026-10-05)
    for consulta in ["compartimentos celulares", "un paisaje volcánico", "el texto en inglés"]:
        plano = _sin_tildes(consulta)
        assert not INTENCION_PAISES.search(plano) and not nombrados(plano), consulta


def test_curriculo_australiano_es_marco_no_pais(grafo):
    """«currículo australiano» apunta al marco ACARA: no debe reforzar los objetivos de Australia como país."""
    from goes_science_kg.rag import GraphRAG

    nodos, aristas = grafo
    ctx = GraphRAG(nodos, aristas).recuperar("¿Qué descriptores del currículo australiano cubren la selección natural?")
    primeros = [n.id for n, _ in ctx.nodos[:10]]
    assert not primeros[0].startswith("OP:"), primeros
    assert any(i.startswith("OBJ:") for i in primeros), primeros


def test_intencion_prerrequisito_con_redaccion_variada():
    from goes_science_kg.rag import INTENCION_PRERREQ, _sin_tildes

    for consulta in ["¿Sobre qué conceptos se apoya la conservación de la energía?",
                     "¿Qué base conceptual necesita un estudiante para calcular el pH?",
                     "¿Qué tendría que haberse trabajado antes de la meiosis?"]:
        # Hueco conocido: «¿de qué depende…?» (orden invertido) no se reconoce;
        # se mide antes de ampliar (resultados.md).
        assert INTENCION_PRERREQ.search(_sin_tildes(consulta)), consulta
    for consulta in ["¿En qué país se enseña antes la fotosíntesis?", "¿Qué se ve en 7.° sobre el clima?"]:
        assert not INTENCION_PRERREQ.search(_sin_tildes(consulta)), consulta
