"""Read protected historical coverage artifacts without modifying them."""

# Historical implementation notes:
# Catálogos de marcos (TIMSS 2027/2023/Advanced, PISA 2025), clasificaciones de los temas
# y objetivos de países con su alineación a TIMSS 2027. Ver config/marcos.yaml.

from __future__ import annotations

import csv
import json
from functools import cache
from pathlib import Path
from typing import Any

from goes_science_kg.config import DIR_EXTERNOS, cargar, ruta


def _json(rel: str) -> Any:
    with open(ruta(rel), encoding="utf-8") as f:
        return json.load(f)


@cache
def catalogo_timss2027() -> list[dict]:
    """Load the TIMSS 2027 grade-four and grade-eight objectives."""
    return _json(cargar("marcos")["marcos"]["T4_27"]["catalogo"])


@cache
def catalogo_timss_v1() -> list[dict]:
    """Load historical TIMSS 2023 and TIMSS Advanced physics catalogs."""
    return _json(cargar("marcos")["marcos"]["T23"]["catalogo"])


@cache
def catalogo_pisa2025() -> dict:
    """Load the original PISA 2025 catalog and its registered elements."""
    return _json(cargar("marcos")["marcos"]["PISA25"]["catalogo"])


def equivalencias_timss() -> list[dict]:
    """Read the explicit TIMSS 2023 to TIMSS 2027 objective correspondence."""
    with open(ruta(cargar("marcos")["marcos"]["T23"]["equivalencias"]), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _por_llave(filas: list[dict]) -> dict[tuple[str, str, int], dict]:
    """Index topic identities by their original workbook, sheet, and row coordinates."""

    # Implementation notes:
    # nombre del libro en la V1 (`legado`), que se traduce al de la versión que fija las llaves. Con la V3 vigente es
    # la V2 (`anterior` en config/mallas.yaml): sus temas idénticos o parecidos heredan la llave de la V2 y los nuevos
    # llevan una propia («V3/<archivo>»).
    cfg = cargar("mallas")
    vigente = {i["legado"]: i["archivo"] for i in cargar(cfg.get("anterior", "mallas"))["archivos"] if "legado" in i}
    return {(vigente.get(c["archivo"], c["archivo"]), c["hoja"], int(c["fila"])): c for c in filas}


def _con_capa(clave: str) -> list[dict]:
    """Combine prior classifications with the explicit new-topic alignment layer."""
    clasif = cargar("marcos")["clasificaciones"]
    p = ruta(clasif[f"{clave}_temas_nuevos"])
    return _json(clasif[clave]) + (json.loads(p.read_text(encoding="utf-8")) if p.exists() else [])


@cache
def clasificacion_timss() -> dict[tuple[str, str, int], dict]:
    """Index historical TIMSS classifications by original physical row location."""
    return _por_llave(_con_capa("timss2027"))


@cache
def clasificacion_pisa() -> dict[tuple[str, str, int], dict]:
    """Index PISA 2025 classifications for grades seven through nine."""
    return _por_llave(_con_capa("pisa2025"))


@cache
def alineacion_paises() -> list[dict]:
    """Load Uruguay, Colombia, and Singapore objective alignments to TIMSS 2027."""
    return _json(cargar("marcos")["clasificaciones"]["paises_alineacion"])


@cache
def catalogo_acara_senior() -> list[dict]:
    """Load the senior-secondary biology and chemistry reference or an empty catalog."""
    p = ruta(cargar("marcos")["marcos"]["AUSS"]["catalogo"])
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


@cache
def clasificacion_auss() -> dict[tuple[str, str, int], dict]:
    """Load senior-secondary Australian alignments when explicitly available."""
    p = ruta(cargar("marcos")["clasificaciones"]["auss"])
    return _por_llave(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else {}


def paises_nuevos() -> list[dict]:
    """Load country objectives extracted in this repository and their source metadata."""

    # Implementation notes:
    # con su alineación a TIMSS 2027 si existe (data/interim/alineaciones/paises_<pais>.json).
    d = ruta("data/interim/paises")
    salida = []
    if not d.exists():
        return salida
    for p in sorted(d.glob("*.json")):
        objs = json.loads(p.read_text(encoding="utf-8"))
        a = ruta(f"data/interim/alineaciones/paises_{p.stem}.json")
        alin = {x["id"]: x for x in json.loads(a.read_text(encoding="utf-8"))} if a.exists() else {}
        salida += [o | {k: v for k, v in alin.get(o["id"], {}).items() if k not in o} for o in objs]
    return salida


def manifiesto_fuentes() -> list[dict]:
    """Read registered source identities, URLs, paths, and byte fingerprints."""
    base = ruta(DIR_EXTERNOS)
    with open(base / "manifest.csv", encoding="utf-8") as f:
        filas = {r["id"]: r for r in csv.DictReader(f)}
    with open(base / "estado.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id"] in filas:
                filas[r["id"]].update(ok=r["ok"] == "True", sha256=r["sha256"], bytes=r["bytes"])
    return list(filas.values())


def documento_por_archivo() -> dict[str, str]:
    """Map PDF filenames to registered document identities."""
    return {Path(r["archivo_local"]).name: r["id"] for r in manifiesto_fuentes()}
