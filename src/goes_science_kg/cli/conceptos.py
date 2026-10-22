"""Comandos del grupo `conceptos`."""

from __future__ import annotations

import json

import typer

app = typer.Typer(help="Capa de conceptos y prácticas (fase 3)", no_args_is_help=True)


@app.command("preparar-vocabulario")
def conceptos_preparar_vocabulario() -> None:
    """Insumos por asignatura para que un subagente construya el vocabulario."""
    from goes_science_kg.conceptos import preparar_vocabulario
    from goes_science_kg.grafo.almacen import cargar

    for p in preparar_vocabulario(cargar()[0]):
        typer.echo(f"→ {p}")


@app.command("consolidar")
def conceptos_consolidar() -> None:
    """Valida y une vocabulario_<asignatura>.json → vocabulario.json."""
    from goes_science_kg.conceptos import consolidar_vocabulario

    typer.echo(json.dumps(consolidar_vocabulario(), ensure_ascii=False))


@app.command("preparar-etiquetado")
def conceptos_preparar_etiquetado(
    todos: bool = typer.Option(False, "--todos", help="Rehace todos los lotes (si no, solo los temas pendientes)"),
    v3: bool = typer.Option(False, "--v3", help="Re-etiqueta los temas nuevos, parecidos y ampliados de la V3"),
) -> None:
    """Lotes por asignatura y grado para etiquetar temas con conceptos y prácticas."""
    from goes_science_kg.conceptos import preparar_etiquetado
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.ingesta.mallas import extraer

    reetiquetar = (
        frozenset(t.id for t in extraer() if t.origen in ("nuevo", "parecido", "ampliado")) if v3 else frozenset()
    )
    escritos = preparar_etiquetado(cargar()[0], solo_pendientes=not todos, reetiquetar=reetiquetar)
    for p in escritos:
        typer.echo(f"→ {p}")
    if not escritos:
        typer.echo("No hay temas pendientes de etiquetar.")


@app.command("unir-etiquetado")
def conceptos_unir_etiquetado() -> None:
    """Valida y une las salidas de los subagentes → etiquetado_temas.json."""
    from goes_science_kg.conceptos import unir_etiquetado

    typer.echo(json.dumps(unir_etiquetado(), ensure_ascii=False))


@app.command("preparar-paises")
def conceptos_preparar_paises() -> None:
    """Lotes para etiquetar los objetivos de países directamente con conceptos."""
    from goes_science_kg.conceptos import preparar_etiquetado_paises
    from goes_science_kg.grafo.almacen import cargar

    for p in preparar_etiquetado_paises(cargar()[0]):
        typer.echo(f"→ {p}")


@app.command("unir-paises")
def conceptos_unir_paises() -> None:
    """Valida y une las salidas → etiquetado_paises.json."""
    from goes_science_kg.conceptos import unir_etiquetado_paises

    typer.echo(json.dumps(unir_etiquetado_paises(), ensure_ascii=False))


@app.command("preparar-prerrequisitos")
def conceptos_preparar_prerrequisitos() -> None:
    """Lotes por asignatura con la evidencia de orden (SV, países, marcos) para el subagente."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.prerrequisitos import preparar

    for p in preparar(*cargar()):
        typer.echo(f"→ {p}")


@app.command("unir-prerrequisitos")
def conceptos_unir_prerrequisitos() -> None:
    """Valida, rompe ciclos y quita redundancias transitivas → prerrequisitos.json."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.prerrequisitos import unir

    typer.echo(json.dumps(unir(cargar()[0]), ensure_ascii=False))
