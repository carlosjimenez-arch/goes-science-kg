"""Back up private artifacts without publishing data to GitHub or changing IAM."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Respaldo privado y restauración verificable de Ciencias", no_args_is_help=True)


@app.command("preparar")
def preparar(destino: Annotated[Path, typer.Option()]) -> None:
    """Create a local package with a SHA inventory and consistent SQLite backups."""
    from goes_science_kg.operacion.respaldo import crear_paquete, seleccionar_artefactos
    from goes_science_kg.producto.almacen import cargar_producto

    try:
        destino = destino_generado(destino, extension=".zip", raiz=ruta("."))
        recibo = destino_generado(destino.with_suffix(".json"), extension=".json", raiz=ruta("."))
        if recibo.exists():
            raise ValueError("El plan de respaldo debe tener un nombre nuevo")
        snapshot = cargar_producto(ruta("data/producto/V4")).manifest.snapshot_id
        datos = crear_paquete(ruta("."), seleccionar_artefactos(ruta(".")), destino)
        if cargar_producto(ruta("data/producto/V4")).manifest.snapshot_id != snapshot:
            raise ValueError("La publicación cambió durante el respaldo")
        datos["snapshot_id"] = snapshot
        escribir_texto_generado(recibo, json.dumps(datos, ensure_ascii=False, indent=2) + "\n", raiz=ruta("."))
    except (ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(datos | {"plan": str(recibo)}, ensure_ascii=False))


@app.command("subir")
def subir(plan: Path, salida: Annotated[Path, typer.Option()]) -> None:
    """Upload new objects and verify storage protections and exact generations."""
    from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen

    try:
        salida = destino_generado(salida, extension=".json", raiz=ruta("."))
        if salida.exists():
            raise ValueError("El recibo debe guardarse en un archivo nuevo")
        datos = json.loads(plan.read_bytes())
        archivo = Path(datos["archivo"])
        if archivo.suffix != ".zip" or hashlib.sha256(archivo.read_bytes()).hexdigest() != datos["sha256"]:
            raise ValueError("El paquete cambió después de prepararse")
        cfg = ConfiguracionAlmacen.model_validate(cargar("almacen_ciencias"))
        almacen = AlmacenGCS(cfg)
        objeto = almacen.crear(archivo, f"objetos/{datos['sha256']}.zip")
        recibo = {
            "version": "entrega-privada-ciencias-1",
            "paquete": objeto,
            "snapshot_id": datos["snapshot_id"],
            "archivos": datos["archivos"],
            "huella_inventario": datos["huella_inventario"],
        }
        descriptor = archivo.with_name(f"descriptor-{datos['sha256']}.json")
        if descriptor.exists():
            raise ValueError("No se sobrescriben descriptores de otra ejecución")
        descriptor.write_text(json.dumps(recibo, ensure_ascii=False, indent=2) + "\n")
        recibo["descriptor"] = almacen.crear(descriptor, f"entregas/{datos['sha256']}.json")
        escribir_texto_generado(salida, json.dumps(recibo, ensure_ascii=False, indent=2) + "\n", raiz=ruta("."))
    except (ValueError, KeyError, OSError, RuntimeError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(recibo, ensure_ascii=False, indent=2))


@app.command("restaurar")
def restaurar(recibo: Path, destino: Annotated[Path, typer.Option()]) -> None:
    """Download a pinned generation and restore it into an empty directory."""
    import tempfile

    from goes_science_kg.operacion.almacen_gcs import AlmacenGCS, ConfiguracionAlmacen
    from goes_science_kg.operacion.respaldo import restaurar_paquete

    try:
        destino_generado(destino / "MANIFEST_RESTAURADO.json", raiz=ruta("."))
        if destino.is_symlink() or (destino.exists() and any(destino.iterdir())):
            raise ValueError("La restauración requiere un directorio nuevo y vacío")
        datos = json.loads(recibo.read_bytes())
        if datos.get("version") != "entrega-privada-ciencias-1":
            raise ValueError("Recibo incompatible")
        almacen = AlmacenGCS(ConfiguracionAlmacen.model_validate(cargar("almacen_ciencias")))
        with tempfile.TemporaryDirectory(prefix="goes-ciencias-restaurar-") as temporal:
            archivo = Path(temporal) / "paquete.zip"
            almacen.descargar(datos["paquete"], archivo)
            resultado = restaurar_paquete(archivo, destino, sha256=datos["paquete"]["sha256"])
    except (ValueError, KeyError, OSError, RuntimeError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(json.dumps(resultado, ensure_ascii=False))
