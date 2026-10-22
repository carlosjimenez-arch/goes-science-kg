"""Expose the alinear command group for the science curriculum pipeline."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Lotes de alineación con subagentes", no_args_is_help=True)


@app.command("preparar-bachillerato")
def alinear_preparar(
    version: str = "auss-v1",
    todos: bool = typer.Option(False, "--todos", help="Rehace todos (si no, solo los pendientes)"),
) -> None:
    """Prepare Australian-reference batches for biology and chemistry in grades 10 and 11."""
    from goes_science_kg.alineacion import preparar_bachillerato
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    for p in preparar_bachillerato(catalogo_acara_senior(), version, solo_pendientes=not todos):
        typer.echo(f"→ {p}")


@app.command("unir-bachillerato")
def alinear_unir() -> None:
    """Validate and merge the senior-secondary alignment batch outputs."""
    from goes_science_kg.alineacion import unir
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    typer.echo(json.dumps(unir("AUSS_", "bachillerato_auss", catalogo_acara_senior()), ensure_ascii=False))


@app.command("preparar-temas")
def alinear_preparar_temas() -> None:
    """Prepare TIMSS and PISA batches for previously unclassified topics in grades 2 to 9."""
    from goes_science_kg.alineacion import preparar_temas_nuevos

    escritos = preparar_temas_nuevos()
    for p in escritos:
        typer.echo(f"→ {p}")
    if not escritos:
        typer.echo("No hay temas sin clasificación.")


@app.command("unir-temas")
def alinear_unir_temas() -> None:
    """Validate new-topic alignment outputs and write their configured artifacts."""
    from goes_science_kg.alineacion import unir_temas_nuevos

    typer.echo(json.dumps(unir_temas_nuevos(), ensure_ascii=False))
