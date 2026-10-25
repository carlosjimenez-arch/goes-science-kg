"""Localiza párrafos literales sin consumir el siguiente tras una etiqueta vacía."""

from __future__ import annotations

import re

PARRAFO = re.compile(rb"<(?P<etiqueta>p|para)\b(?![^>]*?/\s*>)[^>]*>.*?</(?P=etiqueta)\s*>", re.S | re.I)
APERTURA = re.compile(rb"<(?:p|para)\b(?![^>]*?/\s*>)[^>]*>", re.I)


def parrafos_literales(raw: bytes, *, minimo=50, maximo=6000):
    """Devuelve rangos de bytes UTF-8 completos; no traduce ni sintetiza texto."""
    if not 1 <= minimo <= maximo <= 12000:
        raise ValueError("Cotas de párrafo inválidas")
    salida = []
    for coincidencia in PARRAFO.finditer(raw):
        fragmento = coincidencia.group()
        if len(APERTURA.findall(fragmento)) != 1:
            continue
        if minimo <= len(fragmento.decode("utf-8")) <= maximo:
            salida.append([coincidencia.start(), coincidencia.end()])
    return salida
