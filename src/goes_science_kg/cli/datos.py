"""Migrate and restore the external corpus through verified manifests."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import cargar, ruta
from goes_science_kg.operacion import datos_externos as datos
from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen

app = typer.Typer(help="Corpus y entregables en GCS; recuperación con SHA y generación fijados", no_args_is_help=True)
RECIBO = "config/datos_ciencias.lock.json"


def _almacen() -> AlmacenGCS:
    cfg = dict(cargar("almacen_ciencias"))
    if os.environ.get("CLOUDSDK_PYTHON"):
        cfg["python_gcloud"] = os.environ["CLOUDSDK_PYTHON"]
    return AlmacenGCS(
        ConfiguracionAlmacen.model_validate(cfg),
        max_bytes_objeto=datos.limite_bytes(cargar("datos_externos").get("max_bytes_sin_comprimir")),
    )


def _leer(recibo: Path | None) -> dict:
    return json.loads((recibo or ruta(RECIBO)).read_bytes())


def _guardar(destino: Path, contenido: dict) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(contenido, ensure_ascii=False, indent=2) + "\n")


@app.command("preparar")
def preparar(destino: Annotated[Path, typer.Option()]) -> None:
    """Package the corpus without uploading code or credentials."""
    if destino.with_suffix(".json").exists():
        raise typer.BadParameter("El plan ya existe; elija otro destino")
    plan = datos.preparar(ruta("."), cargar("datos_externos"), destino.resolve())
    _guardar(destino.with_suffix(".json"), plan)
    typer.echo(json.dumps(plan["paquete_local"], ensure_ascii=False))


@app.command("subir")
def subir(plan: Path, recibo: Annotated[Path | None, typer.Option()] = None) -> None:
    """Upload new protected objects and verify downloaded bytes."""
    from goes_science_kg.operacion.sincronizacion import subir_paquete

    salida = recibo or ruta(RECIBO)
    if salida.exists() or salida.is_symlink():
        raise typer.BadParameter("El recibo ya existe; use otro nombre para una nueva versión")
    try:
        comprobante = subir_paquete(_almacen(), _leer(plan))
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    _guardar(salida, comprobante)
    typer.echo(
        json.dumps({"recibo": str(salida), "uri": comprobante["paquete"]["uri"], "archivos": comprobante["archivos"]})
    )


@app.command("restaurar")
def restaurar(
    destino: Annotated[Path | None, typer.Option()] = None,
    en_repo: Annotated[bool, typer.Option(help="Repone las rutas originales, ignoradas por Git")] = False,
    recibo: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Restore an exact generation only after verifying every file."""
    from goes_science_kg.operacion.sincronizacion import descargar_corpus, restaurar_en_repo

    if en_repo == (destino is not None):
        raise typer.BadParameter("Indique --destino vacío o --en-repo")
    comprobante = _leer(recibo)
    if en_repo:
        resultado = restaurar_en_repo(_almacen(), comprobante, ruta("."))
    else:
        resultado = descargar_corpus(_almacen(), comprobante, destino.resolve())
    typer.echo(json.dumps(resultado))


def _sincronizador():
    from goes_science_kg.operacion.sincronizacion import Sincronizador

    return Sincronizador(ruta("."), _almacen())


@app.command("estado")
def estado() -> None:
    """Compare local corpus, teacher library, and class delivery with their receipts, without downloading."""
    typer.echo(json.dumps(_sincronizador().estado(), ensure_ascii=False, indent=2))


@app.command("verificar")
def verificar() -> None:
    """Hash the local corpus against the remote inventory of the pinned generation."""
    resultado = _sincronizador().verificar_corpus()
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2))
    if resultado["total_distintos"] or resultado["total_faltan"]:
        raise typer.Exit(1)


@app.command("sincronizar")
def sincronizar() -> None:
    """Download from GCS every pinned component that is missing locally; never overwrite existing data."""
    try:
        resultado = _sincronizador().sincronizar()
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2))


@app.command("publicar")
def publicar(
    trabajo: Annotated[Path, typer.Option(help="Carpeta nueva fuera del repositorio para el paquete")],
) -> None:
    """Package, upload, restore-verify, and adopt a new corpus receipt in one fail-closed step."""
    if trabajo.resolve().is_relative_to(ruta(".").resolve()):
        raise typer.BadParameter("La carpeta de trabajo debe estar fuera del repositorio")
    try:
        resultado = _sincronizador().publicar_corpus(cargar("datos_externos"), trabajo.resolve())
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2))


@app.command("inventario")
def inventario(recibo: Annotated[Path | None, typer.Option()] = None) -> None:
    """Read the remote path, size, and SHA inventory without downloading the corpus."""
    comprobante = _leer(recibo)
    with tempfile.TemporaryDirectory(prefix="goes-datos-inventario-") as temporal:
        archivo = Path(temporal) / "inventario.json"
        _almacen().descargar(comprobante["inventario"], archivo)
        typer.echo(archivo.read_text(encoding="utf-8"))


@app.command("retirar")
def retirar(plan: Path, recibo: Annotated[Path | None, typer.Option()] = None) -> None:
    """Verify remote restoration and retire only originals unchanged since the plan."""
    from goes_science_kg.operacion.sincronizacion import descargar_corpus

    comprobante = _leer(recibo)
    with tempfile.TemporaryDirectory(prefix="goes-datos-verificados-") as temporal:
        verificacion = descargar_corpus(_almacen(), comprobante, Path(temporal) / "corpus")
        resultado = datos.retirar(ruta("."), _leer(plan), comprobante, cargar("datos_externos"))
    typer.echo(json.dumps(resultado | {"restauracion_verificada": verificacion}))
