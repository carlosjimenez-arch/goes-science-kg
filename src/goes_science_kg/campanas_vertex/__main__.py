"""Expose a strictly offline preflight entry point for prepared campaign plans."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from goes_science_kg.campanas_vertex.proveedor import preflight


def main():
    """Read pinned local inputs and print their finite call/reservation bound without inference."""
    parser = argparse.ArgumentParser(description="Preflight offline; este comando nunca llama a Vertex.")
    parser.add_argument("operacion", choices=["preflight"])
    parser.add_argument("plan", type=Path)
    parser.add_argument("--solicitudes", required=True, type=Path)
    parser.add_argument("--prompts", required=True, type=Path)
    argumentos = parser.parse_args()
    resultado = preflight(
        json.loads(argumentos.plan.read_bytes()),
        json.loads(argumentos.solicitudes.read_bytes()),
        json.loads(argumentos.prompts.read_bytes()),
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
