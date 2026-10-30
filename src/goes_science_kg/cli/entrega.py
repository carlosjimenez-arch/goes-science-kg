"""Expose isolated successor builds without changing publication receipts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import ruta

app = typer.Typer(help="Edición didáctica sucesora local, sin modelos ni publicación GCS", no_args_is_help=True)


@app.command("compilar")
def compilar(
    archivo_base: Path,
    destino: Annotated[Path, typer.Option(help="Carpeta nueva; conserva la entrega publicada")],
    ciencias: Annotated[Path | None, typer.Option(help="Correcciones científicas con catálogo y anclajes SHA")] = None,
    recorridos: Annotated[Path | None, typer.Option(help="Recorridos con materiales finales separados")] = None,
    revisiones: Annotated[Path | None, typer.Option(help="Dictámenes documentales anclados a los JSON finales")] = None,
    archivo_zip: Annotated[Path | None, typer.Option(help="ZIP nuevo fuera de la carpeta de edición")] = None,
) -> None:
    """Create a standalone local edition and verify its exact inventory and internal links."""
    from goes_science_kg.entrega.compilacion import compilar as construir

    try:
        manifest = construir(
            ruta("."),
            archivo_base,
            destino,
            ciencias=ciencias,
            recorridos=recorridos,
            revisiones=revisiones,
            archivo_zip=archivo_zip,
        )
    except (OSError, ValueError, KeyError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {"id": manifest["id"], "resumen": manifest["resumen"], "mediciones": manifest["mediciones"]},
            ensure_ascii=False,
        )
    )


@app.command("validar")
def validar(destino: Path) -> None:
    """Check the local edition without altering its files or making network calls."""
    from goes_science_kg.entrega.compilacion import validar as comprobar

    try:
        manifest = comprobar(destino)
    except (OSError, ValueError, KeyError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {"id": manifest["id"], "archivos": len(manifest["archivos"]), "resumen": manifest["resumen"]},
            ensure_ascii=False,
        )
    )


@app.command("despachar")
def despachar(
    edicion: Path,
    archivo_zip: Annotated[Path, typer.Option(help="ZIP final que corresponde exactamente a la edición")],
    auditoria: Annotated[Path, typer.Option(help="Resultado JSON de la auditoría independiente del ZIP")],
    destino: Annotated[Path | None, typer.Option(help="Carpeta nueva; por defecto en el Escritorio")] = None,
    medicion: Annotated[
        Path | None, typer.Option(help="Medición completa y vigente de pruebas del repositorio")
    ] = None,
    evidencia: Annotated[list[Path] | None, typer.Option(help="Evidencia adicional; admite repetir la opción")] = None,
) -> None:
    """Deliver only reviewed, fully verified packages and verify their Desktop copies."""
    from goes_science_kg.entrega.despacho import despachar as copiar_verificado

    try:
        if destino is None:
            identidad = json.loads((edicion / "manifest.json").read_bytes()).get("id", "")
            if not isinstance(identidad, str) or not re.fullmatch(r"[0-9a-f]{64}", identidad):
                raise ValueError("La edición requiere una identidad SHA-256 válida")
            destino = Path.home() / "Desktop" / f"Ciencias_V4_Entrega_{identidad[:12]}"
        recibo = copiar_verificado(
            ruta("."),
            edicion,
            archivo_zip,
            auditoria,
            medicion or ruta("docs/badges/medicion.json"),
            destino,
            evidencias_extra=evidencia or (),
        )
    except (OSError, ValueError, KeyError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(
        json.dumps(
            {
                "recibo_id": recibo["id"],
                "edicion_id": recibo["edicion_id"],
                "zip": recibo["zip"],
                "archivos": len(recibo["archivos"]),
                "destino": str(destino),
            },
            ensure_ascii=False,
        )
    )
