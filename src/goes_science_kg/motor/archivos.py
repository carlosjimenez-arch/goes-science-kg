"""Serialización canónica y destinos protegidos de la entrega; sin redes ni llamadas a modelos."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from goes_science_kg.config import ruta


def canonico(dato: object) -> str:
    return json.dumps(dato, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def firma(dato: object) -> str:
    return hashlib.sha256(canonico(dato).encode()).hexdigest()


def _pares(pares):
    resultado = {}
    for k, v in pares:
        if k in resultado:
            raise ValueError(f"clave JSON repetida: {k}")
        resultado[k] = v
    return resultado


def _constante(valor):
    raise ValueError(f"constante JSON inválida: {valor}")


def decodificar(texto: str):
    return json.loads(texto, object_pairs_hook=_pares, parse_constant=_constante)


def leer(p: Path):
    return decodificar(p.read_text(encoding="utf-8"))


def escribir(p: Path, dato: object) -> None:
    p.write_text(canonico(dato) + "\n", encoding="utf-8")


def destino_seguro(p: Path) -> Path:
    destino = p.resolve()
    try:
        ruta(".")
    except FileNotFoundError:
        # Consumidor instalado sin el repositorio productor: no requiere config ni fuentes locales.
        return destino
    for protegido in ("data/fuentes", "reportes", "data/grafo", ".git"):
        base = ruta(protegido).resolve()
        if destino == base or destino.is_relative_to(base) or base.is_relative_to(destino):
            raise ValueError(f"destino protegido o demasiado amplio: {p}")
    return destino


def id_manifiesto(dato: dict) -> str:
    return firma({k: v for k, v in dato.items() if k != "id_entrega"})
