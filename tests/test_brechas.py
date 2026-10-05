from goes_science_kg.brechas import analizar
from goes_science_kg.prerrequisitos import evidencia_orden


def test_brechas_biologia(grafo):
    nodos, aristas = grafo
    r = analizar("biologia", nodos, aristas, evidencia_orden(nodos, aristas))
    # Regresión con el trabajo previo: TIMSS 4.° deja sin cobertura «Herencia y estrategias de reproducción».
    assert [f["objetivo"] for f in r["cobertura"]["T4_27"]["sin_cobertura"]] == ["T4_27-B2.2"]
    assert r["cobertura"]["T8_27"]["cubiertos"] == r["cobertura"]["T8_27"]["objetivos"]
    for f in r["llega_tarde"]:
        assert f["oportunidad"] >= 2 and len(f["paises"]) >= 2
    for s in r["secuencia"]:
        assert s["grado_prerrequisito"] is None or s["grado_prerrequisito"] > s["grado_concepto"]
