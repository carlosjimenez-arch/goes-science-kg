"""Inventory sources and run explicit experiments with separate preparation and spending."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from uuid import uuid4

import typer

from goes_science_kg.cli.referencias import app as referencias_app
from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Inventarios y experimentos reproducibles", no_args_is_help=True)
app.add_typer(referencias_app, name="referencias")


@app.command("inventariar")
def inventariar(directorio: Path, salida: Annotated[Path, typer.Option()], version: str = typer.Option("V4")) -> None:
    """Inspect workbooks without modifying them or activating a curriculum version."""
    from goes_science_kg.ingesta.inventario import inventariar as inspeccionar

    origen = directorio.resolve()
    destino = salida.resolve()
    if destino.is_relative_to(origen) or destino.is_relative_to(ruta("data/fuentes").resolve()):
        raise typer.BadParameter("El manifiesto debe guardarse fuera del directorio de fuentes")
    inventario = inspeccionar(origen, version)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(inventario.model_dump_json(indent=2), encoding="utf-8")
    typer.echo(
        json.dumps(
            {
                "version": version,
                "estado": inventario.estado,
                "libros": len(inventario.archivos),
                "huella": inventario.huella_contenido,
                "salida": str(destino),
            },
            ensure_ascii=False,
        )
    )


@app.command("recuperacion")
def recuperacion(
    salida: Annotated[Path, typer.Option()] = Path("docs/investigacion/recuperacion_local.json"),
    repeticiones: int = typer.Option(3, min=1, max=10),
) -> None:
    """Compare local retrieval candidates without cloud calls."""
    from goes_science_kg.recuperacion.evaluacion import comparar_recuperacion, escribir_comparacion

    datos = comparar_recuperacion(repeticiones=repeticiones)
    escribir_comparacion(datos, salida_json=salida, salida_md=salida.with_suffix(".md"))
    typer.echo(str(salida))


@app.command("jueces")
def jueces(
    dataset: Path,
    salida: Annotated[Path, typer.Option()],
    ejecutar: bool = typer.Option(False, "--ejecutar"),
    max_usd: float = typer.Option(10.0, min=0.01, max=100),
    ejecucion: str = typer.Option(None),
) -> None:
    """Prepare or execute the configured reviewer experiment without claiming learning efficacy."""
    from goes_science_kg.motor.experimentos import VARIANTES, comparar_jueces
    from goes_science_kg.motor.registro import Registro
    from goes_science_kg.motor.vertex import ConfiguracionVertex

    datos = json.loads(dataset.read_text(encoding="utf-8"))
    modelos = ("gemini-3.8-flash", "gemini-4-argon")
    n = len(datos["casos"]) * len(modelos) * len(VARIANTES)
    if not ejecutar:
        typer.echo(
            json.dumps(
                {
                    "casos": len(datos["casos"]),
                    "modelos": modelos,
                    "variantes": list(VARIANTES),
                    "solicitudes_previstas": n,
                    "max_reserva_usd": max_usd,
                    "llamadas": 0,
                }
            )
        )
        return
    cfg = ConfiguracionVertex.model_validate(cargar("motor")["vertex"]).model_copy(
        update={"max_llamadas": n, "max_usd": max_usd, "max_salida_tokens": 2048, "reintentos": 0}
    )
    registro = Registro(ruta("data/operaciones/registro.sqlite"))
    resultado = comparar_jueces(
        dataset, configuracion=cfg, registro=registro, ejecucion_id=ejecucion or uuid4().hex, modelos=modelos
    )
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(json.dumps(resultado["resumen"], ensure_ascii=False, indent=2))
