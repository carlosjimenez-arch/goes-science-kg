"""CLI `gskg`. Cada comando es una etapa del pipeline (specs/04_pipeline.md)."""

from __future__ import annotations

import json

import typer

from goes_science_kg.config import DIR_INTERIM, ruta

app = typer.Typer(help="Grafo de conocimiento de Ciencias · El Salvador", no_args_is_help=True)
grafo_app = typer.Typer(help="Construir, validar y exportar el grafo", no_args_is_help=True)
app.add_typer(grafo_app, name="grafo")


@app.command()
def temas() -> None:
    """Extrae los temas de las mallas → data/interim/temas.json."""
    from goes_science_kg.ingesta.mallas import extraer

    ts = extraer()
    out = ruta(DIR_INTERIM) / "temas.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([t.dict() for t in ts], ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"{len(ts)} temas → {out.relative_to(ruta('.'))}")


@grafo_app.command("construir")
def grafo_construir() -> None:
    """Construye el grafo desde las fuentes y lo guarda en data/grafo/."""
    from goes_science_kg.grafo.almacen import guardar
    from goes_science_kg.grafo.construir import VERSION_GRAFO, construir
    from goes_science_kg.grafo.validar import validar

    nodos, aristas = construir()
    rep = validar(nodos, aristas)
    for e in rep.errores[:20]:
        typer.echo(f"ERROR {e}", err=True)
    if not rep.ok:
        raise typer.Exit(1)
    m = guardar(nodos, aristas, VERSION_GRAFO)
    typer.echo(json.dumps({"nodos": m["nodos"], "aristas": m["aristas"]}, ensure_ascii=False, indent=1))


@grafo_app.command("validar")
def grafo_validar() -> None:
    """Revisa los invariantes del grafo guardado (sale con código 1 si hay errores)."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.grafo.validar import validar

    rep = validar(*cargar())
    for e in rep.errores:
        typer.echo(f"ERROR {e}", err=True)
    for a in rep.avisos:
        typer.echo(f"AVISO {a}")
    typer.echo(json.dumps(rep.metricas, ensure_ascii=False, indent=1))
    raise typer.Exit(0 if rep.ok else 1)


@grafo_app.command("exportar")
def grafo_exportar(formato: str = typer.Option("graphml", help="graphml")) -> None:
    """Exporta el grafo guardado (data/grafo/export/)."""
    import networkx as nx

    from goes_science_kg.grafo.almacen import a_networkx, cargar

    g = a_networkx(*cargar())
    out = ruta("data/grafo/export")
    out.mkdir(parents=True, exist_ok=True)
    if formato != "graphml":
        raise typer.BadParameter("Por ahora solo graphml")
    plano = nx.MultiDiGraph()
    for n, d in g.nodes(data=True):
        plano.add_node(n, **{k: json.dumps(v, ensure_ascii=False) if isinstance(v, dict | list) else v
                             for k, v in d.items() if v is not None})
    for u, v, k, d in g.edges(keys=True, data=True):
        plano.add_edge(u, v, key=k, **{x: json.dumps(y, ensure_ascii=False) if isinstance(y, dict | list) else y
                                       for x, y in d.items() if y is not None})
    nx.write_graphml(plano, out / "grafo.graphml")
    typer.echo(f"→ {(out / 'grafo.graphml').relative_to(ruta('.'))}")


@app.command()
def fichas() -> None:
    """Genera asignaturas/<asignatura>/ficha.md desde el grafo guardado."""
    import json as _json

    from goes_science_kg.fichas import escribir_fichas
    from goes_science_kg.grafo.almacen import cargar

    version = _json.loads(ruta("data/grafo/manifest.json").read_text(encoding="utf-8"))["version"]
    for p in escribir_fichas(*cargar(), version):
        typer.echo(f"→ {p}")


if __name__ == "__main__":
    app()
