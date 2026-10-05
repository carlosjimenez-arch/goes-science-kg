"""Ayudantes comunes: las pestañas del libro 2027 tienen nombres visibles (scripts/hojas.py) distintos de los internos."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from hojas import NOMBRES  # noqa: E402


def hoja(wb, interno):
    """Hoja por nombre interno; acepta libros viejos (nombre interno) y nuevos (nombre visible)."""
    return wb[NOMBRES[interno]] if NOMBRES.get(interno) in wb.sheetnames else wb[interno]


def tiene(wb, interno):
    return interno in wb.sheetnames or NOMBRES.get(interno) in wb.sheetnames
