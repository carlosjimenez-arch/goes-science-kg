"""Require deterministic output bytes and a versioned graph consistent with original sources."""

from __future__ import annotations

import json
import os
import subprocess
import sys

from goes_science_kg.config import ruta


def test_excel_identico_al_guardar_dos_veces(tmp_path):
    from openpyxl import Workbook

    from goes_science_kg.excel import guardar

    wb = Workbook()
    wb.active.append(["Concepto", "=1+1"])
    a, b = guardar(wb, tmp_path / "a.xlsx"), guardar(wb, tmp_path / "b.xlsx")
    assert a.read_bytes() == b.read_bytes()


def test_grafo_versionado_al_dia(tmp_path):
    """Detect sources added without rebuilding the persisted graph."""
    from goes_science_kg.grafo.almacen import guardar
    from goes_science_kg.grafo.construir import VERSION_GRAFO, construir

    nuevo = guardar(*construir(), VERSION_GRAFO, directorio=str(tmp_path))
    versionado = json.loads(ruta("data/grafo/manifest.json").read_text(encoding="utf-8"))
    assert nuevo["sha256"] == versionado["sha256"], "data/grafo/ está desactualizado: corre `gskg grafo construir`"


def test_evidencia_orden_no_depende_de_la_semilla_de_hash():
    """Keep ordering evidence independent of the process hash seed."""
    codigo = (
        "import hashlib, json; from goes_science_kg.grafo.almacen import cargar; "
        "from goes_science_kg.prerrequisitos import evidencia_orden; "
        "print(hashlib.sha256(json.dumps(evidencia_orden(*cargar()), ensure_ascii=False).encode()).hexdigest())"
    )
    salidas = {
        subprocess.run(
            [sys.executable, "-c", codigo],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": s},
        ).stdout
        for s in ("1", "2")
    }
    assert len(salidas) == 1
