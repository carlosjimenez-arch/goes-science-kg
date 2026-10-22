"""Comandos del grupo `bucle`."""

from __future__ import annotations

import json

import typer

app = typer.Typer(
    help="Bucle de fortalecimiento de los dictámenes del panel (spec 14, sección 7)", no_args_is_help=True
)


def _tipos_opcion(tipos: str | None) -> list[str] | None:
    """Convierte el filtro opcional de terminal al contrato de los casos de uso."""
    return tipos.split(",") if tipos else None


@app.command("anclar")
def bucle_anclar(tipos: str = typer.Option(None, help="separados por coma")) -> None:
    """Mide, sin IA, si la evidencia de cada dictamen está anclada en una fuente primaria."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.anclar(_tipos_opcion(tipos)), ensure_ascii=False, indent=1))


@app.command("impugnar")
def bucle_impugnar(
    vuelta: int = typer.Option(...),
    tipos: str = typer.Option(None, help="separados por coma"),
    serie: str = typer.Option("", help="corrida aparte sobre expedientes nuevos (p. ej. inc9)"),
) -> None:
    """Lotes del refutador (revisor adversarial) → data/interim/panel/bucle/lotes/."""
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
    """Muestra ciega: los roles del panel dictaminan otra vez sin ver la resolución (lotes c<k>)."""
    from goes_science_kg import bucle

    for p in bucle.sonda(vuelta, n, semilla, _tipos_opcion(tipos)):
        typer.echo(f"→ {p}")


@app.command("cerrar-impugnacion")
def bucle_cerrar_impugnacion(vuelta: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Verifica las citas por código y decide qué se sostiene y qué va a la réplica."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_impugnacion(vuelta, serie), ensure_ascii=False, indent=1))


@app.command("replicar")
def bucle_replicar(vuelta: int = typer.Option(...), paso: int = typer.Option(1), serie: str = typer.Option("")) -> None:
    """Lotes de la réplica para los roles del panel (ronda 10·vuelta + paso)."""
    from goes_science_kg import bucle

    for p in bucle.replicar(vuelta, paso, serie):
        typer.echo(f"→ {p}")


@app.command("cerrar-replica")
def bucle_cerrar_replica(
    vuelta: int = typer.Option(...), paso: int = typer.Option(1), serie: str = typer.Option("")
) -> None:
    """Mantiene o cambia cada resolución impugnada (unanimidad, deliberación o «sin consenso»)."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_replica(vuelta, paso, serie), ensure_ascii=False, indent=1))


@app.command("solidez")
def bucle_solidez() -> None:
    """Recalcula la solidez (sólido, respaldado, frágil, sin consenso) y muestra las métricas del bucle."""
    from goes_science_kg import bucle

    typer.echo(json.dumps({"solidez": bucle.solidez(), "metricas": bucle.metricas()}, ensure_ascii=False, indent=1))


@app.command("snapshot")
def bucle_snapshot(etapa: str = typer.Option(..., help="p. ej. «vuelta 2, réplica en curso»")) -> None:
    """panel/bucle/<ciencia>.md y RESUMEN.md: el estado del reforzamiento por ciencia (se versiona en cada etapa)."""
    from goes_science_kg import bucle

    for p in bucle.snapshot(etapa):
        typer.echo(f"→ {p}")


@app.command("cita")
def bucle_cita(fuente: str, cita: str) -> None:
    """¿Está la cita, literal, en esa fuente? (lo mismo que verifica el código al cerrar la impugnación)."""
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
    """Muestra el texto en que el código busca las citas de esa fuente (fila completa de la malla, objetivo o página).
    Avisa si recorta: en una fila de la malla, las microhabilidades y el indicador avanzado van al final."""
    from goes_science_kg import bucle

    for donde, texto in bucle.textos_de_fuente(fuente):
        recorte = caracteres and len(texto) > caracteres
        aviso = f"[… recortado: {len(texto) - caracteres} caracteres más; usa --caracteres 0]\n" if recorte else ""
        typer.echo(f"── {donde}\n{texto[:caracteres] if recorte else texto}\n{aviso}")
