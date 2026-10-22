"""Expose the revision command group for the science curriculum pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from goes_science_kg.config import relativa

app = typer.Typer(help="Revisión humana con el equipo de Ciencias del MINED", no_args_is_help=True)


@app.command("exportar")
def revision_exportar() -> None:
    """Export low-confidence labels and evidence-backed prerequisites for subject review."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.revision_humana import exportar

    for p in exportar(*cargar()):
        typer.echo(f"→ {p}")


@app.command("exportar-decisiones")
def revision_exportar_decisiones() -> None:
    """Export curriculum-content decisions for institutional review."""
    from goes_science_kg.revision_decisiones import exportar_decisiones

    for p in exportar_decisiones():
        typer.echo(f"→ {relativa(Path(p))}")


@app.command("importar-decisiones")
def revision_importar_decisiones(archivo: str) -> None:
    """Record institutional acceptance, changes, or rejection before rebuilding derivatives."""
    from goes_science_kg.revision_decisiones import importar_decisiones

    typer.echo(json.dumps(importar_decisiones(archivo), ensure_ascii=False))


@app.command("importar")
def revision_importar(archivo: str) -> None:
    """Import a reviewed CSV as explicit decisions before rebuilding the graph."""
    from goes_science_kg.revision_humana import importar

    typer.echo(json.dumps(importar(archivo), ensure_ascii=False))
