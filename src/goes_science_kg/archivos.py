"""Write derived artifacts outside protected sources, code, configuration, and evaluations."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from goes_science_kg.config import raiz as raiz_proyecto

PROTEGIDAS = (
    "insumos",
    "data/fuentes",
    "data/grafo",
    "reportes",
    "data/referencias_2026",
    "data/referencias_paises_2026",
    "data/referencias_cientificas_2026",
    "data/referencias_progresiones_2026",
    "data/referencias_web_cientificas_2026",
    "data/evaluacion",
    "src",
    "config",
    ".claude",
    ".codex",
    ".agents",
    ".git",
)


def destino_generado(salida: Path, *, extension: str | None = None, raiz: Path | None = None) -> Path:
    """Validate an output destination outside protected source and evaluation paths."""

    if salida.is_symlink():
        raise ValueError("La salida debe ser un archivo propio, no un enlace simbólico")
    destino = salida.resolve()
    base = (raiz or raiz_proyecto()).resolve()
    if extension is not None and destino.suffix.lower() != extension:
        raise ValueError(f"La salida requiere extensión {extension}")
    if destino.name in {".env", ".envrc", "pyproject.toml", "uv.lock"} or any(
        destino.is_relative_to((base / p).resolve()) for p in PROTEGIDAS
    ):
        raise ValueError("El resultado debe guardarse fuera de originales, código, configuración y evaluación")
    if destino.exists() and not destino.is_file():
        raise ValueError("La salida debe identificar un archivo, no un directorio")
    return destino


def escribir_texto_generado(
    salida: Path, texto: str, *, extension: str | None = None, raiz: Path | None = None
) -> Path:
    """Write derived text only after validating its destination."""

    destino = destino_generado(salida, extension=extension, raiz=raiz)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_name(f".{destino.name}.{uuid4().hex}.tmp")
    try:
        temporal.write_text(texto, encoding="utf-8")
        temporal.replace(destino)
    finally:
        temporal.unlink(missing_ok=True)
    return destino
