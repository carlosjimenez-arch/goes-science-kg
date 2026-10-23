from goes_science_kg.brechas import analizar
from goes_science_kg.modelos import TipoArista
from goes_science_kg.prerrequisitos import evidencia_orden


def test_brechas_biologia(grafo):
    nodos, aristas = grafo
    r = analizar("biologia", nodos, aristas, evidencia_orden(nodos, aristas))
    # En la V1 (y en el trabajo previo) TIMSS 4.° dejaba sin cobertura «Herencia y estrategias de reproducción»
    # (T4_27-B2.2); la V2 la cubría con el tema de rasgos heredados de 3.° (5.14) y la V3 con el de estrategias de
    # supervivencia de la descendencia (5.11), que ya no compara rasgos heredados y no heredados.
    assert r["cobertura"]["T4_27"]["sin_cobertura"] == []
    assert any(
        a.origen == "TEMA:G03-CIE-U5-5.11-v3" and a.destino == "OBJ:T4_27-B2.2"
        for a in aristas
        if a.tipo == TipoArista.CUBRE
    )
    # La V3 movió la resistencia bacteriana de 7.° a 9.° (spec 15): el ciclo 5.°–8.° se queda sin tema para «causas,
    # transmisión, prevención y resistencia a enfermedades». Es un candidato a refuerzo, no un error del grafo.
    assert [o["objetivo"] for o in r["cobertura"]["T8_27"]["sin_cobertura"]] == ["T8_27-B6.1"]
    for f in r["llega_tarde"]:
        assert f["oportunidad"] >= 2 and len(f["paises"]) >= 2
    for s in r["secuencia"]:
        assert s["grado_prerrequisito"] is None or s["grado_prerrequisito"] > s["grado_concepto"]
