import json

from goes_science_kg import propuesta as pr
from goes_science_kg.grafo.almacen import cargar


def test_dividir_mueve_conceptos_al_tema_nuevo(tmp_path, monkeypatch):
    """Regresión: al dividir, los conceptos de la acción salen del tema original y van al tema nuevo."""
    nodos, aristas = cargar()
    tema = next(n for n in nodos if n.id == "TEMA:G02-CIE-U2-2.5")
    conceptos = [a.destino for a in aristas if a.origen == tema.id and a.destino.startswith("CON:")]
    nombre = next(n.etiqueta for n in nodos if n.id == conceptos[0])
    d = tmp_path / "asignaturas/fisica/propuesta"
    d.mkdir(parents=True)
    (d / "propuesta_G02-G04.json").write_text(json.dumps({"version": "t", "acciones": [
        {"n": 1, "accion": "dividir", "temas_afectados": ["G02-CIE-U2-2.5"], "grado_propuesto": 4,
         "conceptos": [nombre]}]}), encoding="utf-8")
    original = pr.ruta
    monkeypatch.setattr(pr, "ruta", lambda rel: tmp_path / rel if str(rel).startswith("asignaturas") else original(rel))
    r = pr.simular("fisica", 2, 4, nodos, aristas)
    assert r["conceptos_no_resueltos"] == []


def test_quitar_conceptos_retira_la_etiqueta(tmp_path, monkeypatch):
    """Una acción con quitar_conceptos retira la arista TRABAJA del tema a ese concepto."""
    import json

    from goes_science_kg import propuesta as pr
    from goes_science_kg.conceptos import vocabulario
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.modelos import TipoArista

    nodos, aristas = cargar()
    t, c = next((a.origen, a.destino) for a in aristas if a.tipo == TipoArista.TRABAJA
                and a.origen.startswith("TEMA:G06-") and a.destino.startswith("CON:biologia/"))
    nombre = vocabulario()[c]["nombre"]
    d = tmp_path / "asignaturas" / "biologia" / "propuesta"
    d.mkdir(parents=True)
    (d / "propuesta_G05-G08.json").write_text(json.dumps({"version": "prueba", "acciones": [
        {"n": 1, "accion": "revisar", "temas_afectados": [t.removeprefix("TEMA:")], "quitar_conceptos": [nombre]}]}),
        encoding="utf-8")
    real = pr.ruta
    monkeypatch.setattr(pr, "ruta", lambda rel: tmp_path / rel if rel.startswith("asignaturas") else real(rel))
    r = pr.simular("biologia", 5, 8, nodos, aristas)
    assert r["conceptos_no_resueltos"] == []
    assert r["etiquetas_retiradas"] >= 1


def test_quitas_de_otra_asignatura_no_contaminan_el_reporte(tmp_path, monkeypatch):
    """Revisión de código: un nombre con errata en otra asignatura no aparece como no resuelto en esta."""
    import json

    from goes_science_kg import propuesta as pr
    from goes_science_kg.grafo.almacen import cargar

    for asig, acciones in [("quimica", []), ("biologia", [{"n": 1, "accion": "revisar", "temas_afectados": [],
                                                           "quitar_conceptos": ["Concepto con errata"]}])]:
        d = tmp_path / "asignaturas" / asig / "propuesta"
        d.mkdir(parents=True)
        (d / "propuesta_G10-G11.json").write_text(json.dumps({"version": "prueba", "acciones": acciones}),
                                                  encoding="utf-8")
    real = pr.ruta
    monkeypatch.setattr(pr, "ruta", lambda rel: tmp_path / rel if rel.startswith("asignaturas") else real(rel))
    r = pr.simular("quimica", 10, 11, *cargar())
    assert r["conceptos_no_resueltos"] == [] and r["quitas_de_otras_asignaturas"] == []
