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
