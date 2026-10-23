"""Resolve repository paths and load the YAML configuration."""

# Historical implementation notes:
# Todas las rutas de config/ son relativas a la raíz del repo, así que el paquete funciona
# igual sin importar desde qué carpeta se ejecute.

from __future__ import annotations

import os
from functools import cache
from pathlib import Path
from typing import Any

import yaml


def raiz() -> Path:
    """Resolve the repository root from GSKG_RAIZ or a matching project ancestor."""
    if env := os.environ.get("GSKG_RAIZ"):
        return Path(env).resolve()
    for p in [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]:
        if (p / "pyproject.toml").exists() and (p / "config").is_dir():
            return p
    raise FileNotFoundError("No encuentro la raíz del repo (pyproject.toml + config/).")


def ruta(rel: str | Path) -> Path:
    """Resolve a repository-relative path while respecting explicit absolute paths."""
    return raiz() / rel


def relativa(p: Path) -> str:
    """Display a repository-relative path or retain an external absolute path."""
    try:
        return str(p.resolve().relative_to(raiz()))
    except ValueError:
        return str(p)


@cache
def cargar(nombre: str) -> dict[str, Any]:
    """Load the named YAML configuration from the repository config directory."""
    with open(ruta(f"config/{nombre}.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


DIR_FUENTES = "data/fuentes"
DIR_EXTERNOS = "data/fuentes/externos"
DIR_INTERIM = "data/interim"
DIR_GRAFO = "data/grafo"
