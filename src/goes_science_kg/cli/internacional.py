"""Expose the internacional command group for the science curriculum pipeline."""

from __future__ import annotations

from typing import Annotated

import typer

app = typer.Typer(help="Grafos internacionales de 9.°–11.° y contraste con la malla V2 (spec 11)", no_args_is_help=True)

CONFIRMAR = Annotated[bool, typer.Option("--confirmar", help="Pagar las llamadas a Vertex que no están en caché.")]


@app.callback()
def internacional_opciones(
    tramo: Annotated[str, typer.Option(help="Tramo de grados: 9_11 (spec 11) o 2_8 (spec 12)")] = "9_11",
) -> None:
    """Select the grade band for international graph construction and comparison."""
    from goes_science_kg.internacional import tramo as tramos

    tramos.usar(tramo)


def _frenar_si_hay_costo(pendientes: int, confirmar: bool) -> None:
    """Report estimated paid calls and stop unless spending was explicitly confirmed."""

    # Implementation notes:
    # inferior (los reintentos y la validación de completitud suman: Ontario 1–2 estimó 24 y usó 29).
    techo = pendientes + -(-pendientes // 4)  # +25 %, redondeado hacia arriba
    typer.echo(
        f"Llamadas a Vertex fuera de la caché: {pendientes} (al menos; pide aprobación para unas {techo})"
        if pendientes
        else "Llamadas a Vertex fuera de la caché: 0"
    )
    if pendientes and not confirmar:
        typer.echo("No se llamó a Vertex. Repite con --confirmar para pagarlas.", err=True)
        raise typer.Exit(1)
    if pendientes:  # se va a gastar: solo con la cuenta GOES
        from goes_science_kg.internacional import vertex

        try:
            vertex.verificar_cuenta()
        except RuntimeError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1) from e


@app.command("extraer")
def internacional_extraer(
    paises: Annotated[list[str] | None, typer.Argument(help="SG, JP…")] = None, confirmar: CONFIRMAR = False
) -> None:
    """Extract and validate country curriculum objectives through Vertex AI."""
    from goes_science_kg.internacional import consenso, extraer

    elegidos = paises or consenso.paises()
    _frenar_si_hay_costo(sum(extraer.llamadas_pendientes(p) for p in elegidos), confirmar)
    for p in elegidos:
        typer.echo(extraer.extraer_pais(p))
    # La extracción reescribe los objetivos desde la caché: sin esto se pierden las correcciones de metadatos (grados,
    # Extension Part en cursiva, sugerencias opcionales al docente). Pasó el 2026-10-13 con HK S1–3.
    typer.echo(f"metadatos corregidos: {extraer.corregir_metadatos()}")


@app.command("etiquetar")
def internacional_etiquetar(
    paises: Annotated[list[str] | None, typer.Argument(help="vacío = todos")] = None, confirmar: CONFIRMAR = False
) -> None:
    """Tag country objectives and V2 curriculum topics with registered concepts."""
    from goes_science_kg.internacional import consenso, etiquetar

    grupos = [*consenso.grupos_paises(paises or None), *etiquetar.grupos_malla_v2()]
    _frenar_si_hay_costo(etiquetar.pendientes(grupos), confirmar)
    for g in grupos:
        typer.echo(etiquetar.etiquetar(*g))


@app.command("congelar-catalogo")
def internacional_congelar_catalogo(version: str) -> None:
    """Freeze the current vocabulary for tagging and explicitly invalidate the prior cache."""
    from goes_science_kg.internacional import etiquetar

    typer.echo(etiquetar.congelar_catalogo(version))


@app.command("corregir-metadatos")
def internacional_corregir_metadatos() -> None:
    """Correct extracted grade metadata without invoking Vertex AI."""
    from goes_science_kg.internacional import extraer

    typer.echo(extraer.corregir_metadatos())


@app.command("construir")
def internacional_construir() -> None:
    """Build country graphs, international consensus, and comparison reports."""
    from goes_science_kg.internacional import consenso, informe

    typer.echo(consenso.construir())
    typer.echo(informe.escribir())
