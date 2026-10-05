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


catalogo_app = typer.Typer(help="Catálogos de marcos pivote", no_args_is_help=True)
app.add_typer(catalogo_app, name="catalogo")
alinear_app = typer.Typer(help="Lotes de alineación con subagentes", no_args_is_help=True)
app.add_typer(alinear_app, name="alinear")


@catalogo_app.command("acara")
def catalogo_acara() -> None:
    """ACARA Senior Secondary (Biología, Química) → data/referencia/catalogo_acara_senior.json."""
    from goes_science_kg.ingesta.acara import SALIDA, escribir_catalogo

    typer.echo(f"{escribir_catalogo()} objetivos → {SALIDA}")


@alinear_app.command("preparar-bachillerato")
def alinear_preparar(version: str = "auss-v1") -> None:
    """Lotes de Biología y Química 10.°–11.° contra AUSS (uno por asignatura y grado)."""
    from goes_science_kg.alineacion import preparar_bachillerato
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    for p in preparar_bachillerato(catalogo_acara_senior(), version):
        typer.echo(f"→ {p}")


@alinear_app.command("unir-bachillerato")
def alinear_unir() -> None:
    """Valida y une las salidas de los subagentes → data/interim/alineaciones/bachillerato_auss.json."""
    from goes_science_kg.alineacion import unir
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    typer.echo(json.dumps(unir("AUSS_", "bachillerato_auss", catalogo_acara_senior()), ensure_ascii=False))


conceptos_app = typer.Typer(help="Capa de conceptos y prácticas (fase 3)", no_args_is_help=True)
app.add_typer(conceptos_app, name="conceptos")


@conceptos_app.command("preparar-vocabulario")
def conceptos_preparar_vocabulario() -> None:
    """Insumos por asignatura para que un subagente construya el vocabulario."""
    from goes_science_kg.conceptos import preparar_vocabulario
    from goes_science_kg.grafo.almacen import cargar

    for p in preparar_vocabulario(cargar()[0]):
        typer.echo(f"→ {p}")


@conceptos_app.command("consolidar")
def conceptos_consolidar() -> None:
    """Valida y une vocabulario_<asignatura>.json → vocabulario.json."""
    from goes_science_kg.conceptos import consolidar_vocabulario

    typer.echo(json.dumps(consolidar_vocabulario(), ensure_ascii=False))


@conceptos_app.command("preparar-etiquetado")
def conceptos_preparar_etiquetado() -> None:
    """Lotes por asignatura y grado para etiquetar temas con conceptos y prácticas."""
    from goes_science_kg.conceptos import preparar_etiquetado
    from goes_science_kg.grafo.almacen import cargar

    for p in preparar_etiquetado(cargar()[0]):
        typer.echo(f"→ {p}")


@conceptos_app.command("unir-etiquetado")
def conceptos_unir_etiquetado() -> None:
    """Valida y une las salidas de los subagentes → etiquetado_temas.json."""
    from goes_science_kg.conceptos import unir_etiquetado

    typer.echo(json.dumps(unir_etiquetado(), ensure_ascii=False))


@conceptos_app.command("preparar-paises")
def conceptos_preparar_paises() -> None:
    """Lotes para etiquetar los objetivos de países directamente con conceptos."""
    from goes_science_kg.conceptos import preparar_etiquetado_paises
    from goes_science_kg.grafo.almacen import cargar

    for p in preparar_etiquetado_paises(cargar()[0]):
        typer.echo(f"→ {p}")


@conceptos_app.command("unir-paises")
def conceptos_unir_paises() -> None:
    """Valida y une las salidas → etiquetado_paises.json."""
    from goes_science_kg.conceptos import unir_etiquetado_paises

    typer.echo(json.dumps(unir_etiquetado_paises(), ensure_ascii=False))


@conceptos_app.command("preparar-prerrequisitos")
def conceptos_preparar_prerrequisitos() -> None:
    """Lotes por asignatura con la evidencia de orden (SV, países, marcos) para el subagente."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.prerrequisitos import preparar

    for p in preparar(*cargar()):
        typer.echo(f"→ {p}")


@conceptos_app.command("unir-prerrequisitos")
def conceptos_unir_prerrequisitos() -> None:
    """Valida, rompe ciclos y quita redundancias transitivas → prerrequisitos.json."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.prerrequisitos import unir

    typer.echo(json.dumps(unir(cargar()[0]), ensure_ascii=False))


grados_app = typer.Typer(help="Grafos por grado (2.° a 11.°)", no_args_is_help=True)
app.add_typer(grados_app, name="grados")


@grados_app.command("construir")
def grados_construir() -> None:
    """Subgrafo y diagnóstico de cada grado → data/grafo/grados/ y grados/G<gg>/ficha.md."""
    from goes_science_kg.grados import construir_grados
    from goes_science_kg.grafo.almacen import cargar

    version = json.loads(ruta("data/grafo/manifest.json").read_text(encoding="utf-8"))["version"]
    for r in construir_grados(*cargar(), version):
        typer.echo(json.dumps(r, ensure_ascii=False))


@grados_app.command("resumenes")
def grados_resumenes() -> None:
    """Une los títulos y resúmenes de bloques (subagentes) → data/interim/comunidades/resumenes.json."""
    from goes_science_kg.comunidades import consolidar_resumenes

    typer.echo(json.dumps(consolidar_resumenes(), ensure_ascii=False))


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
            typer.echo(f"[{c['id']}] {c.get('titulo') or c['nombre']} (puntaje {c['puntaje']})\n"
                       f"    {c.get('resumen_ia') or c['resumen']}")
        return

    ctx = GraphRAG(*cargar()).recuperar(consulta, grado=grado, asignatura=asignatura, k_final=k)
    typer.echo(responder(ctx) if responder_con_claude else ctx.como_texto())


@app.command("evaluar-rag")
def evaluar_rag() -> None:
    """Mide la recuperación de GraphRAG con data/evaluacion/rag_preguntas.json (recall@k, MRR)."""
    from goes_science_kg.evaluacion import evaluar
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.rag import GraphRAG

    typer.echo(json.dumps(evaluar(GraphRAG(*cargar())), ensure_ascii=False, indent=1))


propuesta_app = typer.Typer(help="Propuesta curricular por asignatura y ciclo (fase 5)", no_args_is_help=True)
app.add_typer(propuesta_app, name="propuesta")


@propuesta_app.command("candidatos")
def propuesta_candidatos(asignatura: str, desde: int, hasta: int, marco: str = "T8_27") -> None:
    """Candidatos de cambio con evidencia → asignaturas/<x>/propuesta/candidatos_G..-G...json."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import escribir_candidatos

    typer.echo(f"→ {escribir_candidatos(asignatura, desde, hasta, marco, *cargar())}")


@propuesta_app.command("simular")
def propuesta_simular(asignatura: str, desde: int, hasta: int) -> None:
    """Aplica la propuesta al grafo en memoria y mide el impacto → simulacion_G..-G...json."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import simular

    r = simular(asignatura, desde, hasta, *cargar())
    p = ruta(f"asignaturas/{asignatura}/propuesta/simulacion_G{desde:02d}-G{hasta:02d}.json")
    p.write_text(json.dumps(r, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    typer.echo(json.dumps({"antes": r["antes"], "despues": r["despues"],
                           "secuencia_alta_pendiente": len(r["secuencia_alta_pendiente"]),
                           "conceptos_no_resueltos": r["conceptos_no_resueltos"]}, ensure_ascii=False))


@propuesta_app.command("resumen")
def propuesta_resumen() -> None:
    """Tabla de todas las propuestas con su simulación → asignaturas/PROPUESTAS.md."""
    from goes_science_kg.propuesta import escribir_resumen

    typer.echo(f"→ {escribir_resumen()}")


@propuesta_app.command("excel")
def propuesta_excel(asignatura: str, desde: int, hasta: int) -> None:
    """Libro Excel de la propuesta (después de que el especialista escribe propuesta_G..-G...json)."""
    from goes_science_kg.propuesta import escribir_excel

    typer.echo(f"→ {escribir_excel(asignatura, desde, hasta)}")


revision_app = typer.Typer(help="Revisión humana con el equipo de Ciencias del MINED", no_args_is_help=True)
app.add_typer(revision_app, name="revision")


@revision_app.command("exportar")
def revision_exportar() -> None:
    """CSV por asignatura: etiquetas de confianza baja y prerrequisitos que sostienen hallazgos."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.revision_humana import exportar

    for p in exportar(*cargar()):
        typer.echo(f"→ {p}")


@revision_app.command("importar")
def revision_importar(archivo: str) -> None:
    """Convierte un CSV revisado en revisiones (data/interim/revisiones/). Luego: gskg grafo construir."""
    from goes_science_kg.revision_humana import importar

    typer.echo(json.dumps(importar(archivo), ensure_ascii=False))


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


if __name__ == "__main__":
    app()
