"""Comandos del grupo `panel`."""

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
    """Lotes de la ronda para cada rol del panel → data/interim/panel/lotes/."""
    from goes_science_kg import panel

    lista = tipos.split(",") if tipos else None
    if ronda == 1:
        typer.echo(f"{panel.iniciar(lista)} expedientes nuevos en el estado")
    for p in panel.preparar(ronda, lista, serie, prefijo):
        typer.echo(f"→ {p}")


@app.command("consolidar")
def panel_consolidar(ronda: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Valida las salidas de la ronda y avanza cada expediente (unanimidad, deliberación o secuencia)."""
    from goes_science_kg import panel

    typer.echo(panel.consolidar(ronda, serie))
    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))


@app.command("aplicar")
def panel_aplicar() -> None:
    """Escribe lo resuelto en las capas (decisiones, asignaciones, capa pedagógica) con su procedencia."""
    from goes_science_kg import panel

    typer.echo(panel.aplicar())


@app.command("informe")
def panel_informe() -> None:
    """panel/DICTAMEN.md con lo resuelto, lo que quedó sin consenso y la asesoría del piloto."""
    from goes_science_kg import panel

    typer.echo(f"→ {panel.informe()}")


@app.command("resumen")
def panel_resumen() -> None:
    """Expedientes por tipo y estado."""
    from goes_science_kg import panel

    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))
