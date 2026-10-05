"""Lectura (solo lectura) de los productos del trabajo previo en reportes/cobertura_curricular.

Catálogos de marcos (TIMSS 2027/2023/Advanced, PISA 2025), clasificaciones de los temas
y objetivos de países con su alineación a TIMSS 2027. Ver config/marcos.yaml.
"""

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
    return _json(cargar("marcos")["marcos"]["T4_27"]["catalogo"])


@cache
def catalogo_timss_v1() -> list[dict]:
    """TIMSS 2023 (T4, T8) y TIMSS Advanced 2015 Física (TA)."""
    return _json(cargar("marcos")["marcos"]["T23"]["catalogo"])


@cache
def catalogo_pisa2025() -> dict:
    return _json(cargar("marcos")["marcos"]["PISA25"]["catalogo"])


def equivalencias_timss() -> list[dict]:
    with open(ruta(cargar("marcos")["marcos"]["T23"]["equivalencias"]), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _por_llave(filas: list[dict]) -> dict[tuple[str, str, int], dict]:
    return {(c["archivo"], c["hoja"], int(c["fila"])): c for c in filas}


@cache
def clasificacion_timss() -> dict[tuple[str, str, int], dict]:
    """Clasificación TIMSS 2027 (2.°–9.°) y TIMSS Advanced (Física 10.°–11.°), por (archivo, hoja, fila)."""
    return _por_llave(_json(cargar("marcos")["clasificaciones"]["timss2027"]))


@cache
def clasificacion_pisa() -> dict[tuple[str, str, int], dict]:
    """Clasificación PISA 2025 (7.°–9.°), por (archivo, hoja, fila)."""
    return _por_llave(_json(cargar("marcos")["clasificaciones"]["pisa2025"]))


@cache
def alineacion_paises() -> list[dict]:
    """Objetivos de Uruguay, Colombia y Singapur con obj1/obj2 en TIMSS 2027."""
    return _json(cargar("marcos")["clasificaciones"]["paises_alineacion"])


@cache
def catalogo_acara_senior() -> list[dict]:
    """Pivote AUSS de Biología y Química 10.°–11.° (vacío si aún no se construyó)."""
    p = ruta(cargar("marcos")["marcos"]["AUSS"]["catalogo"])
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


@cache
def clasificacion_auss() -> dict[tuple[str, str, int], dict]:
    """Alineación de Biología y Química 10.°–11.° con AUSS (vacía si aún no existe)."""
    p = ruta(cargar("marcos")["clasificaciones"]["auss"])
    return _por_llave(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else {}


def paises_nuevos() -> list[dict]:
    """Objetivos de países extraídos en este repo (data/interim/paises/<pais>.json; skill pais-extraer-objetivos),
    con su alineación a TIMSS 2027 si existe (data/interim/alineaciones/paises_<pais>.json)."""
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
    """manifest.csv + estado.csv de data/fuentes/externos (id, título, url, archivo, sha256)."""
    base = ruta(DIR_EXTERNOS)
    with open(base / "manifest.csv", encoding="utf-8") as f:
        filas = {r["id"]: r for r in csv.DictReader(f)}
    with open(base / "estado.csv", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["id"] in filas:
                filas[r["id"]].update(ok=r["ok"] == "True", sha256=r["sha256"], bytes=r["bytes"])
    return list(filas.values())


def documento_por_archivo() -> dict[str, str]:
    """Nombre de archivo PDF → id del manifiesto (para enlazar objetivos de países con su documento)."""
    return {Path(r["archivo_local"]).name: r["id"] for r in manifiesto_fuentes()}
