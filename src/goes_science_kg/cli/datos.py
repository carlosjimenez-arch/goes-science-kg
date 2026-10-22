"""Migrate and restore the external corpus through verified manifests."""

from __future__ import annotations

import json
import tempfile
import zipfile
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import cargar, ruta
from goes_science_kg.operacion import datos_externos as datos
from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen

app = typer.Typer(help="Corpus y entregables en GCS; recuperación con SHA y generación fijados", no_args_is_help=True)
RECIBO = "config/datos_ciencias.lock.json"


def _almacen() -> AlmacenGCS:
    return AlmacenGCS(ConfiguracionAlmacen.model_validate(cargar("almacen_ciencias")))


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
    salida = recibo or ruta(RECIBO)
    if salida.exists() or salida.is_symlink():
        raise typer.BadParameter("El recibo ya existe; use otro nombre para una nueva versión")
    preparado = _leer(plan)
    if preparado.get("version") != datos.VERSION:
        raise typer.BadParameter("Plan incompatible")
    local = preparado["paquete_local"]
    archivo = Path(local["archivo"])
    if datos.digest(archivo) != local["sha256"]:
        raise typer.BadParameter("El paquete cambió después de prepararse")
    almacen = _almacen()
    objeto = almacen.crear(archivo, f"repositorio/objetos/{local['sha256']}.zip")
    with tempfile.TemporaryDirectory(prefix="goes-datos-manifest-") as temporal:
        inventario = Path(temporal) / "inventario.json"
        with zipfile.ZipFile(archivo) as zip_:
            inventario.write_bytes(zip_.read("MANIFEST_RESPALDO.json"))
        manifest = json.loads(inventario.read_bytes())
        comprobante = {
            "version": datos.VERSION,
            "paquete": objeto,
            "inventario": almacen.crear(inventario, f"repositorio/inventarios/{local['sha256']}.json"),
            "huella_inventario": local["huella_inventario"],
            "archivos": local["archivos"],
            "bytes_originales": manifest["bytes_sin_comprimir"],
            "montajes": preparado["montajes"],
            "enlaces": preparado["enlaces"],
            "identidad_ledger": preparado["identidad_ledger"],
        }
        descriptor = Path(temporal) / "recibo.json"
        _guardar(descriptor, comprobante)
        comprobante["descriptor"] = almacen.crear(descriptor, f"repositorio/recibos/{local['sha256']}.json")
    _guardar(salida, comprobante)
    typer.echo(json.dumps({"recibo": str(salida), "uri": objeto["uri"], "archivos": local["archivos"]}))


def _descargar_restaurar(comprobante: dict, destino: Path) -> dict:
    with tempfile.TemporaryDirectory(prefix="goes-datos-gcs-") as temporal:
        archivo = Path(temporal) / "datos.zip"
        _almacen().descargar(comprobante["paquete"], archivo)
        return datos.restaurar(archivo, destino, comprobante)


@app.command("restaurar")
def restaurar(
    destino: Annotated[Path | None, typer.Option()] = None,
    en_repo: Annotated[bool, typer.Option(help="Repone las rutas originales, ignoradas por Git")] = False,
    recibo: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Restore an exact generation only after verifying every file."""
    if en_repo == (destino is not None):
        raise typer.BadParameter("Indique --destino vacío o --en-repo")
    comprobante = _leer(recibo)
    if en_repo:
        with tempfile.TemporaryDirectory(prefix="goes-datos-restaurados-") as temporal:
            restaurado = Path(temporal) / "corpus"
            resultado = _descargar_restaurar(comprobante, restaurado)
            datos.incorporar(restaurado, ruta("."), comprobante["montajes"])
            from goes_science_kg.operacion.presupuestos_restaurados import migrar_presupuestos

            resultado["presupuestos"] = migrar_presupuestos(ruta("."), comprobante, resultado["sqlite_verificados"])
    else:
        resultado = _descargar_restaurar(comprobante, destino.resolve())
    typer.echo(json.dumps(resultado))


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
    comprobante = _leer(recibo)
    with tempfile.TemporaryDirectory(prefix="goes-datos-verificados-") as temporal:
        verificacion = _descargar_restaurar(comprobante, Path(temporal) / "corpus")
        resultado = datos.retirar(ruta("."), _leer(plan), comprobante, cargar("datos_externos"))
    typer.echo(json.dumps(resultado | {"restauracion_verificada": verificacion}))
