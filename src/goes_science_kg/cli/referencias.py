"""Manage public references without activating or rebuilding the curriculum."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Literal

import typer

from goes_science_kg.archivos import destino_generado, escribir_texto_generado
from goes_science_kg.config import cargar, ruta

app = typer.Typer(help="Fuentes PDF oficiales con SHA y evidencia por página", no_args_is_help=True)
Coleccion = Literal["evaluacion", "paises", "cientificas", "progresiones"]
COLECCIONES = {
    "evaluacion": ("referentes_2026", "data/referencias_2026"),
    "paises": ("curriculos_paises_2026", "data/referencias_paises_2026"),
    "cientificas": ("fuentes_cientificas_2026", "data/referencias_cientificas_2026"),
    "progresiones": ("progresiones_2026", "data/referencias_progresiones_2026"),
}


def _repositorio():
    from goes_science_kg.ingesta.referencias import RepositorioReferencias

    return RepositorioReferencias(ruta("data/referencias_2026"))


def _coleccion(nombre: Coleccion):
    if nombre == "evaluacion":
        return _repositorio()
    if nombre not in COLECCIONES:
        raise ValueError("Colección documental desconocida")
    from goes_science_kg.ingesta.referencias import RepositorioReferencias

    return RepositorioReferencias(ruta(COLECCIONES[nombre][1]))


def _destino_evidencia(salida: Path, *, repositorio: Path | None = None) -> Path:
    """Validate an evidence output path while preserving custom read-only stores."""
    destino = destino_generado(salida, extension=".json", raiz=ruta("."))
    if repositorio is not None and destino.is_relative_to(repositorio.resolve()):
        raise ValueError("Guarde la evidencia fuera del almacén de referencias")
    return destino


@app.command("estado")
def estado(coleccion: Annotated[Coleccion, typer.Option()] = "evaluacion") -> None:
    """Read the local reference manifest without network requests."""
    typer.echo(_coleccion(coleccion).manifiesto().model_dump_json(indent=2))


@app.command("ingerir")
def ingerir(
    fuentes: Annotated[list[str], typer.Argument(help="IDs del catálogo de la colección seleccionada")],
    descargar: bool = typer.Option(False, "--descargar", help="Descargar solo los PDF seleccionados"),
    coleccion: Annotated[Coleccion, typer.Option()] = "evaluacion",
) -> None:
    """Verify local objects or explicitly download and fingerprint public sources."""
    from goes_science_kg.ingesta.referencias import fuentes_del_catalogo

    try:
        catalogo = COLECCIONES[coleccion][0]
        datos_catalogo = cargar(catalogo)
        seleccion = fuentes_del_catalogo(datos_catalogo, fuentes)
        esperadas = {
            fuente.id: datos_catalogo["fuentes"][fuente.id]["sha256_verificado"]
            for fuente in seleccion
            if "sha256_verificado" in datos_catalogo["fuentes"][fuente.id]
        }
        repositorio = _coleccion(coleccion)
        resultado = (
            repositorio.incorporar(seleccion, descargar=descargar, sha256_esperados=esperadas)
            if esperadas
            else repositorio.incorporar(seleccion, descargar=descargar)
        )
    except (KeyError, ValueError, OSError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(resultado.model_dump_json(indent=2))


@app.command("buscar")
def buscar(
    consulta: str,
    fuente: str = typer.Option(None),
    k: int = typer.Option(5, min=1, max=20),
    coleccion: Annotated[Coleccion, typer.Option()] = "evaluacion",
) -> None:
    """Locate reference pages with BM25 without asserting curriculum alignment."""
    from goes_science_kg.recuperacion import Buscador

    documentos = _coleccion(coleccion).documentos([fuente] if fuente else None)
    buscador = Buscador(documentos)
    for resultado in buscador.buscar(consulta, version="referencia", k=k, saltos_grafo=0):
        documento = resultado.documento
        typer.echo(
            f"{documento.id}\t{resultado.puntaje:.6f}\t{documento.metadata['titulo']}\tPDF {documento.fuente['pagina']}"
        )


@app.command("pagina")
def pagina(
    fuente: str,
    numero: Annotated[int, typer.Argument(min=1)],
    salida: Annotated[Path | None, typer.Option(help="Evidencia JSON, fuera del almacén de fuentes")] = None,
    coleccion: Annotated[Coleccion, typer.Option()] = "evaluacion",
) -> None:
    """Re-extract an original PDF page after verifying its SHA fingerprint."""
    try:
        if salida is not None:
            _destino_evidencia(salida)
        repositorio = _coleccion(coleccion)
        if salida is not None:
            _destino_evidencia(salida, repositorio=repositorio.raiz)
        evidencia = repositorio.pagina(fuente, numero)
        texto = evidencia.model_dump_json(indent=2)
        if salida is not None:
            destino = _destino_evidencia(salida, repositorio=repositorio.raiz)
            escribir_texto_generado(destino, texto + "\n", extension=".json", raiz=ruta("."))
            typer.echo(str(destino))
        else:
            typer.echo(texto)
    except (KeyError, OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error


@app.command("validar-dimensiones")
def validar_dimensiones() -> None:
    """Verify dimension anchors in primary pages without remote models."""
    import json

    from goes_science_kg.ingesta.dimensiones import CatalogoDimensiones
    from goes_science_kg.ingesta.dimensiones import validar_dimensiones as validar

    catalogo = CatalogoDimensiones.model_validate(cargar("dimensiones_evaluativas_2026"))
    resultado = validar(catalogo, _repositorio())
    typer.echo(json.dumps(resultado, ensure_ascii=False, indent=2))
