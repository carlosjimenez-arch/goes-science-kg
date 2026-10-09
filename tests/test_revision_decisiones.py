"""Circuito de confirmación de decisiones con el MINED: exportar y volver a importar (sobre copias temporales)."""

from __future__ import annotations

import csv
import json
import shutil

import pytest

from goes_science_kg import revision_decisiones as rd
from goes_science_kg.config import ruta


@pytest.fixture
def copias(tmp_path, monkeypatch):
    """Las capas de decisión copiadas a tmp_path; el módulo lee y escribe ahí."""
    for rel in rd.ARCHIVOS.values():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ruta(rel), tmp_path / rel)
    monkeypatch.setattr(rd, "ruta", lambda rel: tmp_path / rel if str(rel) in {*rd.ARCHIVOS.values(), rd.DIR}
                        or str(rel).startswith(rd.DIR) else ruta(rel))
    yield tmp_path
    from goes_science_kg import conceptos

    conceptos.divisiones.cache_clear()
    conceptos.vocabulario.cache_clear()


def _csv(p, filas: list[tuple[str, dict]]) -> str:
    with open(p, encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        campos, originales = lector.fieldnames, {r["clave"]: r for r in lector}
    with open(p, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for clave, cambios in filas:
            w.writerow({**originales[clave], **cambios})
    return str(p)


def test_exportar_lista_todas_las_decisiones(copias):
    decisiones, asignaciones = rd.exportar_decisiones("2026-01-01")
    filas = list(csv.DictReader(open(decisiones, encoding="utf-8-sig")))
    tipos = {r["tipo"] for r in filas}
    assert tipos == set(rd.ARCHIVOS) and all(r["estado"] == "pendiente de confirmar" for r in filas)
    assert len(list(csv.DictReader(open(asignaciones, encoding="utf-8-sig")))) == 85


def test_importar_aceptar_rechazar_y_cambiar(copias):
    decisiones, asignaciones = rd.exportar_decisiones("2026-01-01")
    filas = list(csv.DictReader(open(decisiones, encoding="utf-8-sig")))
    acepta, rechaza = filas[0]["clave"], filas[1]["clave"]
    d = rd.COLUMNAS_DECISION
    r = rd.importar_decisiones(_csv(decisiones, [
        (acepta, {d[0]: "aceptar", d[3]: "Equipo de Ciencias MINED"}),
        (rechaza, {d[0]: "rechazar", d[2]: "Revisar con el programa de 10.°", d[3]: "Equipo de Ciencias MINED"})]))
    assert r["aceptar"] == 1 and r["rechazar"] == 1 and r["observadas_piden_nueva_decision"] == [rechaza]
    estados = {f["clave"]: f["estado"] for f in csv.DictReader(open(rd.exportar_decisiones("2026-01-02")[0],
                                                                    encoding="utf-8-sig"))}
    assert estados[acepta] == "confirmada" and estados[rechaza].startswith("observada")

    clave = next(f["clave"] for f in csv.DictReader(open(asignaciones, encoding="utf-8-sig"))
                 if f["elemento"] == "G05-CIE-U3-3.11" and f["conjunto"] == "malla_v1")
    concepto = clave.split("::")[0]
    rd.importar_decisiones(_csv(asignaciones, [(clave, {d[0]: "cambiar", d[1]: concepto, d[3]: "MINED"})]))
    division = json.loads((copias / rd.ARCHIVOS["division"]).read_text())["divisiones"][0]
    assert division["asignaciones"]["malla_v1"]["G05-CIE-U3-3.11"] == [concepto]


@pytest.mark.parametrize("cambios, error", [
    ({"decision (aceptar|cambiar|rechazar)": "aceptar"}, "falta revisado_por"),
    ({"decision (aceptar|cambiar|rechazar)": "cambiar", "nuevos_conceptos (ids; separados por ;)": "CON:inventado",
      "revisado_por": "MINED"}, "admite solo"),
])
def test_importar_valida_antes_de_escribir(copias, cambios, error):
    _, asignaciones = rd.exportar_decisiones("2026-01-01")
    clave = next(csv.DictReader(open(asignaciones, encoding="utf-8-sig")))["clave"]
    antes = (copias / rd.ARCHIVOS["division"]).read_text()
    with pytest.raises(ValueError, match=error):
        rd.importar_decisiones(_csv(asignaciones, [(clave, cambios)]))
    assert (copias / rd.ARCHIVOS["division"]).read_text() == antes
