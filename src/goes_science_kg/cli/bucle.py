"""Expose the bucle command group for the science curriculum pipeline."""

from __future__ import annotations

import json

import typer

app = typer.Typer(
    help="Bucle de fortalecimiento de los dictámenes del panel (spec 14, sección 7)", no_args_is_help=True
)


def _tipos_opcion(tipos: str | None) -> list[str] | None:
    """Convert an optional CLI filter to the use-case contract."""
    return tipos.split(",") if tipos else None


@app.command("anclar")
def bucle_anclar(tipos: str = typer.Option(None, help="separados por coma")) -> None:
    """Check primary-source anchors for panel reviews without invoking AI."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.anclar(_tipos_opcion(tipos)), ensure_ascii=False, indent=1))


@app.command("impugnar")
def bucle_impugnar(
    vuelta: int = typer.Option(...),
    tipos: str = typer.Option(None, help="separados por coma"),
    serie: str = typer.Option("", help="corrida aparte sobre expedientes nuevos (p. ej. inc9)"),
) -> None:
    """Prepare adversarial challenge batches for the selected review cycle."""
    from goes_science_kg import bucle

    for p in bucle.impugnar(vuelta, _tipos_opcion(tipos), serie):
        typer.echo(f"→ {p}")


@app.command("sonda")
def bucle_sonda(
    vuelta: int = typer.Option(...),
    n: int = typer.Option(None),
    semilla: int = typer.Option(None),
    tipos: str = typer.Option(None, help="separados por coma"),
) -> None:
    """Prepare blind repeat readings without exposing the previous resolution."""
    from goes_science_kg import bucle

    for p in bucle.sonda(vuelta, n, semilla, _tipos_opcion(tipos)):
        typer.echo(f"→ {p}")


@app.command("cerrar-impugnacion")
def bucle_cerrar_impugnacion(vuelta: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Verify literal quotations and determine which challenges require a response."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_impugnacion(vuelta, serie), ensure_ascii=False, indent=1))


@app.command("replicar")
def bucle_replicar(vuelta: int = typer.Option(...), paso: int = typer.Option(1), serie: str = typer.Option("")) -> None:
    """Prepare response batches for challenged expert-panel dossiers."""
    from goes_science_kg import bucle

    for p in bucle.replicar(vuelta, paso, serie):
        typer.echo(f"→ {p}")


@app.command("cerrar-replica")
def bucle_cerrar_replica(
    vuelta: int = typer.Option(...), paso: int = typer.Option(1), serie: str = typer.Option("")
) -> None:
    """Resolve challenged decisions under unanimity, deliberation, or no-consensus rules."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_replica(vuelta, paso, serie), ensure_ascii=False, indent=1))


@app.command("solidez")
def bucle_solidez() -> None:
    """Recompute review strength and display the cycle metrics."""
    from goes_science_kg import bucle

    typer.echo(json.dumps({"solidez": bucle.solidez(), "metricas": bucle.metricas()}, ensure_ascii=False, indent=1))


@app.command("snapshot")
def bucle_snapshot(etapa: str = typer.Option(..., help="p. ej. «vuelta 2, réplica en curso»")) -> None:
    """Write subject-specific snapshots of the panel strengthening process."""
    from goes_science_kg import bucle

    for p in bucle.snapshot(etapa):
        typer.echo(f"→ {p}")


@app.command("cita")
def bucle_cita(fuente: str, cita: str) -> None:
    """Check whether a literal quotation occurs in the registered source."""
    from goes_science_kg import bucle

    r = bucle.verificar(fuente, cita)
    marca = "✓" if r["estado"] == "anclada" else "✗"
    typer.echo(
        f"{marca} {r['tipo']} · {r['estado']} · {r['donde'] or ''}"
        + (f" · no existen: {', '.join(r['inexistentes'])}" if r["inexistentes"] else "")
    )
    raise typer.Exit(0 if r["estado"] == "anclada" else 1)


@app.command("fuente")
def bucle_fuente(fuente: str, caracteres: int = typer.Option(8000, help="0 = sin límite")) -> None:
    """Display the exact source text used by deterministic quotation checks."""

    # Implementation notes:
    # Avisa si recorta: en una fila de la malla, las microhabilidades y el indicador avanzado van al final.
    from goes_science_kg import bucle

    for donde, texto in bucle.textos_de_fuente(fuente):
        recorte = caracteres and len(texto) > caracteres
        aviso = f"[… recortado: {len(texto) - caracteres} caracteres más; usa --caracteres 0]\n" if recorte else ""
        typer.echo(f"── {donde}\n{texto[:caracteres] if recorte else texto}\n{aviso}")
