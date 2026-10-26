"""Versioned files must not depend on, or disclose, paths of a particular workstation."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

from goes_science_kg.motor.ejecuciones import identidad_ledger

RAIZ = Path(__file__).resolve().parents[1]
RUTA_LOCAL = re.compile(r"/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+/|/private/(?:tmp|var)/|[A-Z]:\\Users\\")


def _versionados() -> list[str]:
    try:
        salida = subprocess.run(["git", "ls-files", "-z"], cwd=RAIZ, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("Requiere un checkout de Git")
    # reportes/ conserva originales históricos que no se modifican.
    return [n for n in salida.decode().split("\0") if n and not n.startswith("reportes/")]


def test_ningun_archivo_versionado_contiene_rutas_de_una_estacion():
    hallazgos = []
    for nombre in _versionados():
        archivo = RAIZ / nombre
        if not archivo.is_file() or archivo.stat().st_size > 5 * 1024**2:
            continue
        try:
            texto = archivo.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        hallazgos += [f"{nombre}:{n}" for n, linea in enumerate(texto.splitlines(), 1) if RUTA_LOCAL.search(linea)]
    assert hallazgos == []


def test_la_identidad_del_ledger_no_incluye_rutas(tmp_path):
    ledger = tmp_path / "registro.sqlite"
    ledger.write_bytes(b"")
    identidad = identidad_ledger(ledger)
    assert set(identidad) == {"nombre", "dispositivo", "inodo"} and str(tmp_path) not in json.dumps(identidad)
    assert identidad_ledger(tmp_path / "ausente.sqlite") is None
