"""Apply explicit reviewed decisions ahead of automatic or AI classification."""

# Historical implementation notes:
# Cada archivo data/interim/revisiones/<nombre>.json (excepto los lote_*.json) es una lista de registros por tema:
# {"id": "<id del tema sin TEMA:>", "asignatura": "...", "conceptos": [...], "practicas": [...],
#  "confianza": "...", "justificacion": "...", "version": "...", "revisado_por": "..."}
# Los campos ausentes no se tocan. Si dos archivos revisan el mismo tema, gana el último en orden alfabético
# (por eso conviene nombrarlos con fecha: 2026-10-05_<tema>.json). La revisión humana del MINED (skill
# revision-humana) escribe en el mismo formato.

from __future__ import annotations

import json
from functools import cache

from goes_science_kg.config import ruta

DIR = "data/interim/revisiones"


@cache
def revisiones_temas() -> dict[str, dict]:
    """Merge topic reviews alphabetically with the documented field-level precedence."""

    # Implementation notes:
    # último).
    #
    # Cada registro lleva `archivo_revision` con el último archivo que lo tocó. Resultado en caché.
    d = ruta(DIR)
    out: dict[str, dict] = {}
    if not d.exists():
        return out
    for p in sorted(d.glob("*.json")):
        if p.name.startswith("lote_"):
            continue
        for r in json.loads(p.read_text(encoding="utf-8")):
            if "id" not in r:  # solo registros por tema; otros archivos no pertenecen a esta capa
                continue
            out[r["id"]] = {**out.get(r["id"], {}), **r, "archivo_revision": p.name}
    return out
