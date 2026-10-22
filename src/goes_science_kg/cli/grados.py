"""Comandos del grupo `grados`."""

from __future__ import annotations

import json

import typer

from goes_science_kg.config import ruta

app = typer.Typer(help="Grafos por grado (2.° a 11.°)", no_args_is_help=True)


@app.command("construir")
def grados_construir() -> None:
    """Subgrafo y diagnóstico de cada grado → data/grafo/grados/ y grados/G<gg>/ficha.md."""
    from goes_science_kg.grados import construir_grados
    from goes_science_kg.grafo.almacen import cargar

    version = json.loads(ruta("data/grafo/manifest.json").read_text(encoding="utf-8"))["version"]
    for r in construir_grados(*cargar(), version):
        typer.echo(json.dumps(r, ensure_ascii=False))


@app.command("resumenes")
def grados_resumenes() -> None:
    """Une los títulos y resúmenes de bloques (subagentes) → data/interim/comunidades/resumenes.json."""
    from goes_science_kg.comunidades import consolidar_resumenes

    typer.echo(json.dumps(consolidar_resumenes(), ensure_ascii=False))
