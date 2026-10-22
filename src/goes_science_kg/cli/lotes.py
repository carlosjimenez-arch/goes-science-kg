"""Comandos del grupo `lotes`."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(help="Lotes de subagentes: validación de sus salidas (harness de agentes)", no_args_is_help=True)


@app.command("validar")
def lotes_validar(
    tipo: str = typer.Option(None, help="alineacion | etiquetado | prerrequisitos | bloques | adopcion"),
    agente: str = typer.Option(None, help="Nombre de un subagente de .claude/agents (usa su tipo de lote)"),
    base: str = typer.Option(None, hidden=True, help="Raíz alternativa donde buscar los lotes (pruebas)"),
) -> None:
    """Valida cada salida_*.json contra su lote con las reglas de la unión. Sale con 1 si hay errores."""

    from goes_science_kg.lotes import comando_union, tipo_de_agente, validar

    if agente is not None:
        tipo = tipo_de_agente(agente)
        if tipo is None:
            typer.echo(f"{agente} no produce lotes: nada que validar.")
            return
    errores = validar(tipo, Path(base) if base else None)
    for archivo, errs in errores.items():
        typer.echo(f"✗ {archivo}: {len(errs)} errores")
        for e in errs[:10]:
            typer.echo(f"    - {e}")
    if errores:
        raise typer.Exit(1)
    typer.echo(
        f"✓ salidas válidas ({tipo or 'todos los tipos'}); se consolidan con: "
        f"{comando_union(tipo) if tipo else 'el «unir» de cada tipo'}"
    )


@app.command("vertex")
def lotes_vertex(
    lotes: Annotated[list[str], typer.Argument(help="Rutas de lote_*.json")],
    agente: Annotated[str, typer.Option(help="redactor-actividades, experto-<asignatura> o psicopedagogo")],
    modelo: Annotated[str, typer.Option(help="Modelo de Vertex")] = "gemini-4-argon",
    confirmar: Annotated[
        bool, typer.Option("--confirmar", help="Pagar las llamadas a Vertex que no están en caché")
    ] = False,
) -> None:
    """Corre lotes de un agente en Vertex (Gemini) con las mismas validaciones del hook; sin --confirmar solo estima."""

    from goes_science_kg import agentes_vertex
    from goes_science_kg.internacional import vertex

    rutas = [Path(x) for x in lotes]
    typer.echo(json.dumps(agentes_vertex.estimar(rutas, agente, modelo), ensure_ascii=False))
    if not confirmar:
        typer.echo("Sin --confirmar no se gasta. Agrega --confirmar para correr.")
        return
    vertex.verificar_cuenta()
    fallidos = 0
    for p in rutas:
        errores = agentes_vertex.correr(p, agente, modelo)
        fallidos += bool(errores)
        typer.echo(f"{'✓' if not errores else '✗'} {p.name}" + (f": {len(errores)} errores" if errores else ""))
        for e in errores[:5]:
            typer.echo(f"    - {e}")
    typer.echo(f"Llamadas pagadas: {vertex.llamadas()}; lotes fallidos: {fallidos}")
