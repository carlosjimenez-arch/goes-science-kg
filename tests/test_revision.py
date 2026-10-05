import csv
import json

import pytest

from goes_science_kg import revision_humana as rh


def _csv(p, encabezado, filas):
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(encabezado)
        w.writerows(filas)


@pytest.fixture
def raiz(tmp_path, monkeypatch):
    monkeypatch.setattr(rh, "ruta", lambda rel: tmp_path / rel)
    return tmp_path


def test_importar_prerrequisitos_rechazados(raiz):
    _csv(raiz / "a/b/revision/x.csv", ["prerrequisito_id", "concepto_id", *rh.COLUMNAS_DECISION],
         [["CON:a", "CON:b", "rechazar", "", "no aplica", "Equipo de Ciencias"],
          ["CON:c", "CON:d", "aceptar", "", "", "Equipo de Ciencias"],
          ["CON:e", "CON:f", "", "", "", ""]])  # sin decisión: se ignora
    assert rh.importar("a/b/revision/x.csv") == {"prerrequisitos_rechazados": 1, "aceptados": 1}
    rech = json.loads((raiz / rh.RECHAZADOS).read_text())
    assert (rech[0]["origen"], rech[0]["destino"]) == ("CON:a", "CON:b")


def test_csv_sin_decisiones_no_escribe_nada(raiz):
    _csv(raiz / "a/b/revision/y.csv", ["prerrequisito_id", "concepto_id", *rh.COLUMNAS_DECISION],
         [["CON:a", "CON:b", "", "", "", ""]])
    assert rh.importar("a/b/revision/y.csv") == {"decisiones": 0}
    assert not (raiz / "data/interim/revisiones").exists()


def test_importar_rechaza_conceptos_inexistentes_y_sin_revisor(raiz):
    _csv(raiz / "a/biologia/revision/z.csv", ["id", *rh.COLUMNAS_DECISION],
         [["G02-CIE-U1-1.1", "cambiar", "CON:biologia/no-existe", "", "Equipo"],
          ["G02-CIE-U1-1.2", "aceptar", "", "", ""]])
    with pytest.raises(ValueError, match="no-existe|revisado_por"):
        rh.importar("a/biologia/revision/z.csv")
