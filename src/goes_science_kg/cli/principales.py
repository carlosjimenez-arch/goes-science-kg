"""Comandos principales del pipeline curricular."""

from __future__ import annotations

import json

import typer

from goes_science_kg.config import DIR_INTERIM, relativa, ruta

app = typer.Typer(help="Grafo de conocimiento de Ciencias · El Salvador", no_args_is_help=True)


@app.command()
def temas() -> None:
    """Extrae los temas de las mallas → data/interim/temas.json."""
    from goes_science_kg.ingesta.mallas import extraer

    ts = extraer()
    out = ruta(DIR_INTERIM) / "temas.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps([t.dict() for t in ts], ensure_ascii=False, indent=1), encoding="utf-8")
    typer.echo(f"{len(ts)} temas → {relativa(out)}")


@app.command("malla-correspondencia")
def malla_correspondencia() -> None:
    """Empareja la malla vigente (V3) con la anterior (V2) → data/interim/mallas/v2_a_v3.json (spec 15)."""
    from goes_science_kg.ingesta.mallas import escribir_correspondencia

    typer.echo(json.dumps(escribir_correspondencia(), ensure_ascii=False, indent=1))


@app.command()
def rag(
    consulta: str,
    grado: int = typer.Option(None, help="Filtra los temas a un grado (2–11)"),
    asignatura: str = typer.Option(None, help="biologia | fisica | quimica | ciencias_tierra_espacio"),
    k: int = typer.Option(25, help="Nodos en el contexto"),
    responder_con_claude: bool = typer.Option(False, "--responder", help="Genera la respuesta con Claude"),
    global_: bool = typer.Option(False, "--global", help="Búsqueda global: bloques temáticos del grado"),
) -> None:
    """GraphRAG: recupera evidencia del grafo (y opcionalmente responde con Claude)."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.rag import GraphRAG, busqueda_global, responder

    if global_:
        if not grado:
            raise typer.BadParameter("--global requiere --grado")
        for c in busqueda_global(consulta, grado):
            typer.echo(
                f"[{c['id']}] {c.get('titulo') or c['nombre']} (puntaje {c['puntaje']})\n"
                f"    {c.get('resumen_ia') or c['resumen']}"
            )
        return

    ctx = GraphRAG(*cargar()).recuperar(consulta, grado=grado, asignatura=asignatura, k_final=k)
    typer.echo(responder(ctx) if responder_con_claude else ctx.como_texto())


@app.command("evaluar-rag")
def evaluar_rag(
    conjunto: str = typer.Option(
        "data/evaluacion/rag_preguntas.json",
        help="Archivo de preguntas (p. ej. el de prueba, que no se usa para ajustar)",
    ),
) -> None:
    """Mide la recuperación de GraphRAG con un conjunto de preguntas (recall@k, MRR)."""
    from goes_science_kg.evaluacion import evaluar
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.rag import GraphRAG

    typer.echo(json.dumps(evaluar(GraphRAG(*cargar()), conjunto=conjunto), ensure_ascii=False, indent=1))


@app.command()
def brechas() -> None:
    """Análisis de brechas por asignatura → asignaturas/<x>/brechas/."""
    from goes_science_kg.brechas import escribir_brechas
    from goes_science_kg.grafo.almacen import cargar

    for r in escribir_brechas(*cargar()):
        typer.echo(json.dumps(r, ensure_ascii=False))


@app.command()
def progresion() -> None:
    """Mapa de progresión de conceptos por asignatura → asignaturas/<x>/progresion.html."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.progresion import escribir_todas

    for p in escribir_todas(*cargar()):
        typer.echo(f"→ {p}")


@app.command()
def servir(puerto: int = 8010, host: str = "127.0.0.1") -> None:
    """API de lectura (FastAPI) en http://127.0.0.1:<puerto>/docs. Requiere `uv sync --extra api`."""
    import uvicorn

    uvicorn.run("goes_science_kg.api:app", host=host, port=puerto)


@app.command()
def fichas() -> None:
    """Genera asignaturas/<asignatura>/ficha.md desde el grafo guardado."""
    import json as _json

    from goes_science_kg.fichas import escribir_fichas
    from goes_science_kg.grafo.almacen import cargar

    version = _json.loads(ruta("data/grafo/manifest.json").read_text(encoding="utf-8"))["version"]
    for p in escribir_fichas(*cargar(), version):
        typer.echo(f"→ {p}")
