"""Comandos del grupo `catalogo`."""

from __future__ import annotations

import typer

app = typer.Typer(help="Catálogos de marcos pivote", no_args_is_help=True)


@app.command("acara")
def catalogo_acara() -> None:
    """ACARA Senior Secondary (Biología, Química) → data/referencia/catalogo_acara_senior.json."""
    from goes_science_kg.ingesta.acara import SALIDA, escribir_catalogo

    typer.echo(f"{escribir_catalogo()} objetivos → {SALIDA}")
