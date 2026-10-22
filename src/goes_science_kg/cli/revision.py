"""Comandos del grupo `revision`."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from goes_science_kg.config import relativa

app = typer.Typer(help="Revisión humana con el equipo de Ciencias del MINED", no_args_is_help=True)


@app.command("exportar")
def revision_exportar() -> None:
    """CSV por asignatura: etiquetas de confianza baja y prerrequisitos que sostienen hallazgos."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.revision_humana import exportar

    for p in exportar(*cargar()):
        typer.echo(f"→ {p}")


@app.command("exportar-decisiones")
def revision_exportar_decisiones() -> None:
    """CSV de las decisiones de contenido (equivalencias, prerrequisitos, divisiones, clases) para el MINED."""
    from goes_science_kg.revision_decisiones import exportar_decisiones

    for p in exportar_decisiones():
        typer.echo(f"→ {relativa(Path(p))}")


@app.command("importar-decisiones")
def revision_importar_decisiones(archivo: str) -> None:
    """Registra el veredicto del MINED (aceptar | cambiar | rechazar). Luego: make todo."""
    from goes_science_kg.revision_decisiones import importar_decisiones

    typer.echo(json.dumps(importar_decisiones(archivo), ensure_ascii=False))


@app.command("importar")
def revision_importar(archivo: str) -> None:
    """Convierte un CSV revisado en revisiones (data/interim/revisiones/). Luego: gskg grafo construir."""
    from goes_science_kg.revision_humana import importar

    typer.echo(json.dumps(importar(archivo), ensure_ascii=False))
