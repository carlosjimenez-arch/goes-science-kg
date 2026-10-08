"""Rutas del repositorio y lectura de la configuración (config/*.yaml).

Todas las rutas de config/ son relativas a la raíz del repo, así que el paquete funciona
igual sin importar desde qué carpeta se ejecute.
"""

from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any

import yaml


def raiz() -> Path:
    """Raíz del repo: GSKG_RAIZ si existe; si no, el primer ancestro con pyproject.toml."""
    if env := os.environ.get("GSKG_RAIZ"):
        return Path(env).resolve()
    for p in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:
        if (p / "pyproject.toml").exists() and (p / "config").is_dir():
            return p
    raise FileNotFoundError("No encuentro la raíz del repo (pyproject.toml + config/).")


def ruta(rel: str | Path) -> Path:
    """Ruta dentro del repo (una ruta absoluta se respeta tal cual)."""
    return raiz() / rel


def relativa(p: Path) -> str:
    """`p` relativa a la raíz del repo para mostrarla; si queda fuera (p. ej. una carpeta temporal), absoluta."""
    try:
        return str(p.resolve().relative_to(raiz()))
    except ValueError:
        return str(p)


@cache
def cargar(nombre: str) -> dict[str, Any]:
    """Lee config/<nombre>.yaml."""
    with open(ruta(f"config/{nombre}.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


DIR_FUENTES = "data/fuentes"
DIR_EXTERNOS = "data/fuentes/externos"
DIR_INTERIM = "data/interim"
DIR_GRAFO = "data/grafo"
