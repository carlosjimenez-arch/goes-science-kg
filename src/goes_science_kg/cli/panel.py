"""Expose the panel command group for the science curriculum pipeline."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Panel de expertos IA: revisión técnica interina (spec 14)", no_args_is_help=True)


@app.command("preparar")
def panel_preparar(
    ronda: int = typer.Option(...),
    tipos: str = typer.Option(None, help="separados por coma"),
    serie: str = typer.Option("", help="lotes aparte para un grupo de tipos"),
    prefijo: str = typer.Option("", help="solo expedientes cuyo id empieza así (p. ej. PED:)"),
) -> None:
    """Prepare one panel round's batches for every required reviewer role."""
    from goes_science_kg import panel

    lista = tipos.split(",") if tipos else None
    if ronda == 1:
        typer.echo(f"{panel.iniciar(lista)} expedientes nuevos en el estado")
    for p in panel.preparar(ronda, lista, serie, prefijo):
        typer.echo(f"→ {p}")


@app.command("consolidar")
def panel_consolidar(ronda: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Validate round outputs and advance dossiers under the panel resolution rules."""
    from goes_science_kg import panel

    typer.echo(panel.consolidar(ronda, serie))
    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))


@app.command("aplicar")
def panel_aplicar() -> None:
    """Apply resolved decisions and pedagogical changes with their recorded provenance."""
    from goes_science_kg import panel

    typer.echo(panel.aplicar())


@app.command("informe")
def panel_informe() -> None:
    """Write the panel report with resolved and unresolved dossiers."""
    from goes_science_kg import panel

    typer.echo(f"→ {panel.informe()}")


@app.command("resumen")
def panel_resumen() -> None:
    """Summarize panel dossiers by type and state."""
    from goes_science_kg import panel

    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))
