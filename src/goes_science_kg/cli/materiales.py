"""Preparación, distribución y verificación de materiales docentes reales."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Biblioteca docente V4 y material histórico con versiones explícitas", no_args_is_help=True)


def _almacen():
    from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen

    cfg = dict(cargar("almacen_ciencias"))
    if os.environ.get("CLOUDSDK_PYTHON"):
        cfg["python_gcloud"] = os.environ["CLOUDSDK_PYTHON"]
    return AlmacenGCS(ConfiguracionAlmacen.model_validate(cfg))


@app.command("construir")
def construir(destino: Annotated[Path | None, typer.Option()] = None):
    """Compila los contenidos existentes; cero invocaciones a modelos y ninguna escritura en GCS."""
    from goes_science_kg.api_producto import _LecturaProducto
    from goes_science_kg.materiales.almacen import construir as guardar
    from goes_science_kg.materiales.compilacion import (
        compilar_historicos,
        compilar_v4,
        recoger_originales,
        sha,
    )

    base = ruta(".")
    runtime = _LecturaProducto(base, base / "data/producto/V4").leer()
    originales = recoger_originales(base)
    ledger = base / "data/operaciones/registro.sqlite"
    ledger_sha = sha(ledger.read_bytes())
    registros = compilar_v4(runtime) + compilar_historicos(originales)
    manifest = guardar(
        registros,
        originales,
        destino or base / "data/materiales",
        procedencia={
            "snapshot_id": runtime.producto.manifest.snapshot_id,
            "archivos_snapshot": runtime.producto.manifest.sha256,
            "corpus": json.loads((base / "config/datos_ciencias.lock.json").read_bytes())["paquete"],
            "ledger_sha256": ledger_sha,
            "metodo": "compilacion_determinista_sin_generacion_ni_reevaluacion",
        },
    )
    if sha(ledger.read_bytes()) != ledger_sha:
        raise ValueError("El ledger cambió durante la compilación")
    typer.echo(json.dumps({k: manifest[k] for k in ("id", "materiales", "por_tipo", "por_version")}))


@app.command("validar")
def validar(directorio: Annotated[Path | None, typer.Option()] = None):
    from goes_science_kg.materiales.almacen import Biblioteca

    manifest = Biblioteca(directorio or ruta("data/materiales")).validar()
    typer.echo(json.dumps({"estado": "verificado", "id": manifest["id"], "materiales": manifest["materiales"]}))


@app.command("publicar")
def publicar(
    recibo: Annotated[Path, typer.Option(help="Archivo propio de progreso y recibo final")],
    directorio: Annotated[Path | None, typer.Option()] = None,
):
    """Crea objetos privados nuevos y relee cada generación. Nunca modifica permisos."""
    from goes_science_kg.materiales.publicacion import publicar as subir

    resultado = subir(directorio or ruta("data/materiales"), _almacen(), recibo)
    typer.echo(json.dumps({"biblioteca_id": resultado["biblioteca_id"], "objetos": len(resultado["objetos"])}))


@app.command("restaurar")
def restaurar(
    recibo: Annotated[Path | None, typer.Option()] = None,
    destino: Annotated[Path | None, typer.Option()] = None,
):
    """Recupera sólo los materiales; no necesita restaurar las 7.580 fuentes y entregas del corpus."""
    from goes_science_kg.materiales.publicacion import restaurar as descargar

    ref = json.loads((recibo or ruta("config/materiales_ciencias.lock.json")).read_bytes())
    manifest = descargar(ref, destino or ruta("data/materiales"), _almacen())
    typer.echo(
        json.dumps({"estado": "verificado", "biblioteca_id": manifest["id"], "materiales": manifest["materiales"]})
    )
