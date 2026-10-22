"""Comandos del grupo `refuerzo`."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Refuerzo de cada tema de la malla V3 con evidencia (spec 15)", no_args_is_help=True)


@app.command("errores")
def refuerzo_errores() -> None:
    """Qué errores y problemas de progresión registrados siguen literales en la malla vigente."""
    from goes_science_kg.refuerzo import errores_en_vigente

    for e in errores_en_vigente():
        typer.echo(f"{e['id']}  {e['estado']:16}  {', '.join(e['temas_v3'])}")


@app.command("candidatos")
def refuerzo_candidatos() -> None:
    """Catálogo de candidatos a refuerzo → data/interim/refuerzo_v3/candidatos.json."""
    from goes_science_kg.refuerzo import escribir_candidatos

    typer.echo(json.dumps(escribir_candidatos(), ensure_ascii=False, indent=1))


@app.command("preparar")
def refuerzo_preparar(
    serie: str = typer.Option("a"),
    asignaturas: str = typer.Option(None, help="separadas por coma (vacío = todas)"),
    tramo: str = typer.Option(None, help="2_8 o 9_11 (vacío = los dos)"),
) -> None:
    """Lotes del subagente redactor-refuerzos → data/interim/refuerzo_v3/lotes/ (sin reescribir los existentes)."""
    from goes_science_kg.refuerzo import preparar_lotes

    for p in preparar_lotes(serie, tuple(asignaturas.split(",")) if asignaturas else None, tramo):
        typer.echo(f"→ {p}")


@app.command("snapshot")
def refuerzo_snapshot(
    asignaturas: str = typer.Option("fisica,quimica", help="separadas por coma"),
    grados: str = typer.Option("9-11", help="rango, p. ej. 9-11"),
    etapa: str = typer.Option(..., help="qué corte es (fecha y estado)"),
) -> None:
    """Estado del refuerzo de esas asignaturas y grados → entregas/mallas_v3_reforzadas/SNAPSHOT_*.md."""
    from goes_science_kg.refuerzo import escribir_snapshot

    g0, g1 = (int(x) for x in grados.split("-"))
    typer.echo(f"→ {escribir_snapshot(tuple(asignaturas.split(',')), tuple(range(g0, g1 + 1)), etapa)}")


@app.command("unir")
def refuerzo_unir() -> None:
    """Valida las salidas del redactor y escribe data/interim/refuerzo_v3/refuerzos.json."""
    from goes_science_kg.refuerzo import unir

    typer.echo(json.dumps(unir(), ensure_ascii=False, indent=1))
