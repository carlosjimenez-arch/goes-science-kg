"""Expose the catalogo command group for the science curriculum pipeline."""

from __future__ import annotations

import typer

app = typer.Typer(help="Catálogos de marcos pivote", no_args_is_help=True)


@app.command("acara")
def catalogo_acara() -> None:
    """Build the Australian senior-secondary reference catalog for biology and chemistry."""
    from goes_science_kg.ingesta.acara import SALIDA, escribir_catalogo

    typer.echo(f"{escribir_catalogo()} objetivos → {SALIDA}")
