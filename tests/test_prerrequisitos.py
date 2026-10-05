import json

import pytest

from goes_science_kg import prerrequisitos as pr
from goes_science_kg.modelos import Nodo, TipoNodo


def _nodos(*ids):
    return [Nodo(id=i, tipo=TipoNodo.CONCEPTO, etiqueta=i) for i in ids]


def _salida(tmp_path, monkeypatch, aristas):
    monkeypatch.setattr(pr, "ruta", lambda rel: tmp_path / rel)
    d = tmp_path / pr.DIR / "lotes"
    d.mkdir(parents=True)
    (d / "salida_x.json").write_text(json.dumps(aristas), encoding="utf-8")


def _a(o, d, conf="media", tipo="logica"):
    return {"origen": o, "destino": d, "tipo_evidencia": tipo, "confianza": conf, "justificacion": "x"}


def test_rompe_ciclos_por_menor_confianza(tmp_path, monkeypatch):
    _salida(tmp_path, monkeypatch, [_a("CON:a", "CON:b", "alta"), _a("CON:b", "CON:a", "baja")])
    r = pr.unir(_nodos("CON:a", "CON:b"))
    assert r["aristas"] == 1 and r["rotas_por_ciclo"] == 1
    final = json.loads((tmp_path / pr.DIR / "prerrequisitos.json").read_text())
    assert (final[0]["origen"], final[0]["destino"]) == ("CON:a", "CON:b")


def test_quita_transitivas_no_declaradas(tmp_path, monkeypatch):
    _salida(tmp_path, monkeypatch, [_a("CON:a", "CON:b"), _a("CON:b", "CON:c"), _a("CON:a", "CON:c")])
    r = pr.unir(_nodos("CON:a", "CON:b", "CON:c"))
    assert r["aristas"] == 2 and r["transitivas_quitadas"] == 1


def test_rechaza_ids_inexistentes(tmp_path, monkeypatch):
    _salida(tmp_path, monkeypatch, [_a("CON:a", "CON:zzz")])
    with pytest.raises(ValueError):
        pr.unir(_nodos("CON:a"))
