"""Expose the refuerzo command group for the science curriculum pipeline."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Refuerzo de cada tema de la malla V3 con evidencia (spec 15)", no_args_is_help=True)


@app.command("errores")
def refuerzo_errores() -> None:
    """List documented errors and sequencing issues still present in the current curriculum."""
    from goes_science_kg.refuerzo import errores_en_vigente

    for e in errores_en_vigente():
        typer.echo(f"{e['id']}  {e['estado']:16}  {', '.join(e['temas_v3'])}")


@app.command("candidatos")
def refuerzo_candidatos() -> None:
    """Write the historical V3 reinforcement candidate catalog."""
    from goes_science_kg.refuerzo import escribir_candidatos

    typer.echo(json.dumps(escribir_candidatos(), ensure_ascii=False, indent=1))


@app.command("preparar")
def refuerzo_preparar(
    serie: str = typer.Option("a"),
    asignaturas: str = typer.Option(None, help="separadas por coma (vacío = todas)"),
    tramo: str = typer.Option(None, help="2_8 o 9_11 (vacío = los dos)"),
) -> None:
    """Prepare reinforcement-writing batches without overwriting existing outputs."""
    from goes_science_kg.refuerzo import preparar_lotes

    for p in preparar_lotes(serie, tuple(asignaturas.split(",")) if asignaturas else None, tramo):
        typer.echo(f"→ {p}")


@app.command("snapshot")
def refuerzo_snapshot(
    asignaturas: str = typer.Option("fisica,quimica", help="separadas por coma"),
    grados: str = typer.Option("9-11", help="rango, p. ej. 9-11"),
    etapa: str = typer.Option(..., help="qué corte es (fecha y estado)"),
) -> None:
    """Write a subject- and grade-specific reinforcement snapshot."""
    from goes_science_kg.refuerzo import escribir_snapshot

    g0, g1 = (int(x) for x in grados.split("-"))
    typer.echo(f"→ {escribir_snapshot(tuple(asignaturas.split(',')), tuple(range(g0, g1 + 1)), etapa)}")


@app.command("unir")
def refuerzo_unir() -> None:
    """Validate writer outputs and consolidate the reinforcement artifact."""
    from goes_science_kg.refuerzo import unir

    typer.echo(json.dumps(unir(), ensure_ascii=False, indent=1))
