"""Paquetes individuales por indicador, sin generación ni nuevas revisiones."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import ruta

app = typer.Typer(help="Paquetes por indicador de las mallas finales", no_args_is_help=True)


@app.command("construir")
def construir(
    origen: Annotated[Path, typer.Option()] = Path("data/materiales_produccion_v4"),
    destino: Annotated[Path, typer.Option()] = Path("data/materiales_indicadores_v4"),
    exportaciones: Annotated[Path, typer.Option()] = Path("data/indicadores_v4/paquetes"),
):
    from goes_science_kg.materiales.compilacion import sha
    from goes_science_kg.observabilidad import configurar_logging
    from goes_science_kg.produccion.indicadores.exportacion import guardar

    configurar_logging()
    ledger = ruta("data/operaciones/registro.sqlite")
    antes = sha(ledger.read_bytes()) if ledger.exists() else None
    m, r = guardar(ruta(origen), ruta(destino), ruta(exportaciones))
    despues = sha(ledger.read_bytes()) if ledger.exists() else None
    if despues != antes:
        raise ValueError("El ledger cambió durante la compilación")
    typer.echo(
        json.dumps(
            {
                "biblioteca_id": m["id"],
                "indicadores": m["materiales"],
                "filas_cubiertas": r["filas_cubiertas"],
                "llamadas_modelos": 0,
            },
            ensure_ascii=False,
        )
    )


@app.command("publicar")
def publicar(
    directorio: Annotated[Path, typer.Option()] = Path("data/materiales_indicadores_v4"),
    exportaciones: Annotated[Path, typer.Option()] = Path("data/indicadores_v4/paquetes"),
    recibo_biblioteca: Annotated[Path, typer.Option()] = Path("config/materiales_indicadores_ciencias.lock.json"),
    recibo_paquetes: Annotated[Path, typer.Option()] = Path("config/paquetes_indicadores_ciencias.lock.json"),
):
    from goes_science_kg.cli.materiales import _almacen
    from goes_science_kg.materiales.almacen import Biblioteca
    from goes_science_kg.materiales.publicacion import publicar as subir_biblioteca
    from goes_science_kg.produccion.publicacion import publicar as subir_paquetes

    almacen = _almacen()
    b = subir_biblioteca(ruta(directorio), almacen, ruta(recibo_biblioteca))
    p = subir_paquetes(ruta(exportaciones), Biblioteca(ruta(directorio)), almacen, ruta(recibo_paquetes))
    typer.echo(json.dumps({"biblioteca_id": b["biblioteca_id"], "objetos": len(b["objetos"]) + len(p["objetos"])}))


@app.command("descargar")
def descargar(
    destino: Annotated[Path, typer.Option()],
    recibo: Annotated[Path, typer.Option()] = Path("config/paquetes_indicadores_ciencias.lock.json"),
):
    from goes_science_kg.cli.materiales import _almacen
    from goes_science_kg.produccion.publicacion import descargar as recuperar

    r = recuperar(json.loads(ruta(recibo).read_bytes()), ruta(destino), _almacen())
    typer.echo(
        json.dumps({"colecciones": len(r["paquetes"]), "indicadores": sum(p["paquetes"] for p in r["paquetes"])})
    )
