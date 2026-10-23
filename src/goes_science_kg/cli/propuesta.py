"""Expose the propuesta command group for the science curriculum pipeline."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Propuesta curricular por asignatura y ciclo (fase 5)", no_args_is_help=True)


@app.command("candidatos")
def propuesta_candidatos(asignatura: str, desde: int, hasta: int, marco: str | None = None) -> None:
    """Prepare evidence-backed curriculum change candidates for a subject and cycle."""

    # Implementation notes:
    # Sin --marco se usa el marco del ciclo: TIMSS 4.° (T4_27) hasta 4.°, TIMSS 8.° (T8_27) hasta 9.° y, en
    # Bachillerato, TIMSS Advanced (TA15) para Física y ACARA Senior Secondary (AUSS) para Biología y Química.
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import escribir_candidatos

    if marco is None:
        marco = "T4_27" if hasta <= 4 else "T8_27" if hasta <= 9 else "TA15" if asignatura == "fisica" else "AUSS"

    typer.echo(f"→ {escribir_candidatos(asignatura, desde, hasta, marco, *cargar())}")


@app.command("simular")
def propuesta_simular(asignatura: str, desde: int, hasta: int) -> None:
    """Simulate a proposal in memory and record its graph impact."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import escribir_simulacion

    r = escribir_simulacion(asignatura, desde, hasta, *cargar())
    typer.echo(
        json.dumps(
            {
                "antes": r["antes"],
                "despues": r["despues"],
                "secuencia_alta_pendiente": len(r["secuencia_alta_pendiente"]),
                "conceptos_no_resueltos": r["conceptos_no_resueltos"],
            },
            ensure_ascii=False,
        )
    )


@app.command("preparar-adopcion")
def propuesta_preparar_adopcion() -> None:
    """Prepare reconciliation of proposed additions with topics adopted in V2."""
    from goes_science_kg.propuesta import preparar_adopcion_v2

    typer.echo(f"→ {preparar_adopcion_v2()}")


@app.command("unir-adopcion")
def propuesta_unir_adopcion() -> None:
    """Validate the specialist's V2 adoption reconciliation output."""
    from goes_science_kg.propuesta import unir_adopcion_v2

    typer.echo(json.dumps(unir_adopcion_v2(), ensure_ascii=False))


@app.command("resumen")
def propuesta_resumen() -> None:
    """Write the proposal summary table with simulation results."""
    from goes_science_kg.propuesta import escribir_resumen

    typer.echo(f"→ {escribir_resumen()}")


@app.command("excel")
def propuesta_excel(asignatura: str, desde: int, hasta: int) -> None:
    """Export the specialist's curriculum proposal to an Excel workbook."""
    from goes_science_kg.propuesta import escribir_excel

    typer.echo(f"→ {escribir_excel(asignatura, desde, hasta)}")
