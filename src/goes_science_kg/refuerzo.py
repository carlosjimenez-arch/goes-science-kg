"""Refuerzo de cada tema de la malla vigente (V3) con lo que el repo ya sabe (spec 15).

Cuatro fuentes, solo con evidencia y sin quitar nada:
- errores de la malla (`data/interim/refuerzo_v3/errores_malla.json`, curado): se buscan LITERALES en la vigente;
- recomendaciones del panel con solidez «sólido» o «respaldado»;
- hallazgos del contraste internacional;
- lo que la V3 dejó de cubrir y los países o los marcos enseñan en el núcleo.

Este módulo arma los candidatos (código, sin IA). La redacción de las filas propuestas y su revisión van después.
"""

from __future__ import annotations

import json
import unicodedata
from functools import cache

from goes_science_kg.config import ruta

DIR = "data/interim/refuerzo_v3"


def _plano(texto: str) -> str:
    """Minúsculas, sin tildes y con los espacios normalizados: para buscar un fragmento literal."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).split())


@cache
def errores_malla() -> tuple[dict, ...]:
    """Los errores y problemas de progresión curados, con su fragmento literal."""
    return tuple(json.loads(ruta(f"{DIR}/errores_malla.json").read_text(encoding="utf-8")))


def errores_en_vigente() -> list[dict]:
    """Cada error con los temas de la malla vigente donde su fragmento sigue literal (en toda la fila). Sin temas, la
    V3 lo corrigió o lo quitó: no se inyecta y se registra como «corregido_en_v3»."""
    from goes_science_kg.ingesta.mallas import textos_completos

    textos = {i: _plano(t) for i, t in textos_completos().items()}
    salida = []
    for e in errores_malla():
        frag = _plano(e["cita_literal"])
        temas = sorted(i for i, t in textos.items() if frag in t)
        salida.append({**e, "temas_v3": temas, "estado": "sigue" if temas else "corregido_en_v3"})
    return salida
