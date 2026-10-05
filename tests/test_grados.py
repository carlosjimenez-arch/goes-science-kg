import json

from goes_science_kg.config import ruta
from goes_science_kg.grados import GRADOS, subgrafo
from goes_science_kg.modelos import TipoNodo
from goes_science_kg.prerrequisitos import evidencia_orden


def test_subgrafo_del_grado_contiene_solo_sus_temas(grafo):
    nodos, aristas = grafo
    ev = evidencia_orden(nodos, aristas)
    sn, sa, d = subgrafo(7, nodos, aristas, ev)
    temas = [n for n in sn if n.tipo == TipoNodo.TEMA]
    assert temas and all(t.grado == 7 for t in temas)
    ids = {n.id for n in sn}
    assert all(a.origen in ids and a.destino in ids for a in sa)
    assert d["temas"] == len(temas)
    assert d["conceptos_nuevos"] + d["conceptos_retomados"] + d["conceptos_anticipados"] == d["conceptos"]


def test_estados_de_anclaje_validos(grafo):
    nodos, aristas = grafo
    ev = evidencia_orden(nodos, aristas)
    for g in (5, 8, 10):
        _, _, d = subgrafo(g, nodos, aristas, ev)
        assert all(a["estado"] in {"previo", "mismo_grado", "posterior", "ausente"} for a in d["anclajes"])


def test_salidas_por_grado_existen():
    for g in GRADOS:
        assert (ruta(f"grados/G{g:02d}") / "ficha.md").exists()
        assert (ruta(f"grados/G{g:02d}") / "grafo.html").exists()
        m = json.loads((ruta(f"data/grafo/grados/G{g:02d}") / "manifest.json").read_text(encoding="utf-8"))
        assert m["nodos"]["Tema"] > 0


def test_primer_grado_no_tiene_retomados(grafo):
    nodos, aristas = grafo
    _, _, d = subgrafo(2, nodos, aristas, evidencia_orden(nodos, aristas))
    assert d["conceptos_retomados"] == 0


def test_resumen_se_empareja_por_conceptos_aunque_cambie_el_id(monkeypatch):
    from goes_science_kg import comunidades as com

    falso = {"COM:G05-01": {"id": "COM:G05-01", "conceptos": ["a", "b", "c", "d"], "titulo": "T", "resumen_ia": "R"}}
    monkeypatch.setattr(com, "resumenes", lambda: falso)
    assert com.resumen_para(5, ["a", "b", "c", "d"])["titulo"] == "T"   # mismo bloque, otro id posible
    assert com.resumen_para(5, ["a", "b", "x", "y"]) is None              # Jaccard 0,33
    assert com.resumen_para(6, ["a", "b", "c", "d"]) is None              # otro grado
