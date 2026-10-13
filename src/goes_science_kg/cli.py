"""CLI `gskg`. Cada comando es una etapa del pipeline (specs/04_pipeline.md)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from goes_science_kg.config import DIR_INTERIM, relativa, ruta

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
    typer.echo(f"{len(ts)} temas → {relativa(out)}")


@app.command("malla-correspondencia")
def malla_correspondencia() -> None:
    """Empareja la malla vigente (V3) con la anterior (V2) → data/interim/mallas/v2_a_v3.json (spec 15)."""
    from goes_science_kg.ingesta.mallas import escribir_correspondencia

    typer.echo(json.dumps(escribir_correspondencia(), ensure_ascii=False, indent=1))


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
    typer.echo(f"→ {relativa(out / 'grafo.graphml')}")


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
def alinear_preparar(version: str = "auss-v1",
                     todos: bool = typer.Option(False, "--todos", help="Rehace todos (si no, solo los pendientes)")
                     ) -> None:
    """Lotes de Biología y Química 10.°–11.° contra AUSS (uno por asignatura y grado)."""
    from goes_science_kg.alineacion import preparar_bachillerato
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    for p in preparar_bachillerato(catalogo_acara_senior(), version, solo_pendientes=not todos):
        typer.echo(f"→ {p}")


@alinear_app.command("unir-bachillerato")
def alinear_unir() -> None:
    """Valida y une las salidas de los subagentes → data/interim/alineaciones/bachillerato_auss.json."""
    from goes_science_kg.alineacion import unir
    from goes_science_kg.ingesta.legado import catalogo_acara_senior

    typer.echo(json.dumps(unir("AUSS_", "bachillerato_auss", catalogo_acara_senior()), ensure_ascii=False))


@alinear_app.command("preparar-temas")
def alinear_preparar_temas() -> None:
    """Lotes TIMSS 2027 y PISA 2025 para los temas de 2.°–9.° sin clasificación previa (los nuevos de la V2)."""
    from goes_science_kg.alineacion import preparar_temas_nuevos

    escritos = preparar_temas_nuevos()
    for p in escritos:
        typer.echo(f"→ {p}")
    if not escritos:
        typer.echo("No hay temas sin clasificación.")


@alinear_app.command("unir-temas")
def alinear_unir_temas() -> None:
    """Valida y une las salidas → data/interim/alineaciones/temas_nuevos_{timss2027,pisa2025}.json."""
    from goes_science_kg.alineacion import unir_temas_nuevos

    typer.echo(json.dumps(unir_temas_nuevos(), ensure_ascii=False))


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
def conceptos_preparar_etiquetado(
        todos: bool = typer.Option(False, "--todos", help="Rehace todos los lotes (si no, solo los temas pendientes)"),
        v3: bool = typer.Option(False, "--v3", help="Re-etiqueta los temas nuevos, parecidos y ampliados de la V3"),
) -> None:
    """Lotes por asignatura y grado para etiquetar temas con conceptos y prácticas."""
    from goes_science_kg.conceptos import preparar_etiquetado
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.ingesta.mallas import extraer

    reetiquetar = frozenset(t.id for t in extraer() if t.origen in ("nuevo", "parecido", "ampliado")) if v3 else \
        frozenset()
    escritos = preparar_etiquetado(cargar()[0], solo_pendientes=not todos, reetiquetar=reetiquetar)
    for p in escritos:
        typer.echo(f"→ {p}")
    if not escritos:
        typer.echo("No hay temas pendientes de etiquetar.")


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
def evaluar_rag(
    conjunto: str = typer.Option("data/evaluacion/rag_preguntas.json",
                                 help="Archivo de preguntas (p. ej. el de prueba, que no se usa para ajustar)"),
) -> None:
    """Mide la recuperación de GraphRAG con un conjunto de preguntas (recall@k, MRR)."""
    from goes_science_kg.evaluacion import evaluar
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.rag import GraphRAG

    typer.echo(json.dumps(evaluar(GraphRAG(*cargar()), conjunto=conjunto), ensure_ascii=False, indent=1))


propuesta_app = typer.Typer(help="Propuesta curricular por asignatura y ciclo (fase 5)", no_args_is_help=True)
app.add_typer(propuesta_app, name="propuesta")


@propuesta_app.command("candidatos")
def propuesta_candidatos(asignatura: str, desde: int, hasta: int, marco: str | None = None) -> None:
    """Candidatos de cambio con evidencia → asignaturas/<x>/propuesta/candidatos_G..-G...json.

    Sin --marco se usa el marco del ciclo: TIMSS 4.° (T4_27) hasta 4.°, TIMSS 8.° (T8_27) hasta 9.° y, en
    Bachillerato, TIMSS Advanced (TA15) para Física y ACARA Senior Secondary (AUSS) para Biología y Química.
    """
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.propuesta import escribir_candidatos

    if marco is None:
        marco = "T4_27" if hasta <= 4 else "T8_27" if hasta <= 9 else "TA15" if asignatura == "fisica" else "AUSS"

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


@propuesta_app.command("preparar-adopcion")
def propuesta_preparar_adopcion() -> None:
    """Lote para conciliar las acciones «nuevo» con los temas que agregó la V2 → data/interim/propuestas/."""
    from goes_science_kg.propuesta import preparar_adopcion_v2

    typer.echo(f"→ {preparar_adopcion_v2()}")


@propuesta_app.command("unir-adopcion")
def propuesta_unir_adopcion() -> None:
    """Valida la salida del especialista → data/interim/propuestas/adopcion_v2.json."""
    from goes_science_kg.propuesta import unir_adopcion_v2

    typer.echo(json.dumps(unir_adopcion_v2(), ensure_ascii=False))


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


tutor_app = typer.Typer(help="Apoyo al aprendizaje sobre el grafo (spec 13, prototipo)", no_args_is_help=True)
app.add_typer(tutor_app, name="tutor")


def _nav():
    from goes_science_kg.aprendizaje.pedagogia import navegador_compartido

    return navegador_compartido()


@tutor_app.command("bases")
def tutor_bases(tema: str, profundidad: int = 2) -> None:
    """Desde un objetivo hacia sus bases: «¿qué necesita comprender?»."""
    nav = _nav()
    tema = tema if tema.startswith("TEMA:") else f"TEMA:{tema}"
    for b in nav.bases(tema, profundidad):
        typer.echo(f"{'  ' * (b.profundidad - 1)}{b.profundidad} {nav.por_id[b.concepto].etiqueta} [{b.concepto}] "
                   f"conf {b.confianza} · {'antes' if b.antes_del_objetivo else 'NO antes'} en la malla "
                   f"({(b.primer_tema or '—').removeprefix('TEMA:')}) · {b.estado_relacion}")


@tutor_app.command("apoya")
def tutor_apoya(concepto: str, grado: int = typer.Option(None), alcance: int = 2) -> None:
    """Desde una base hacia lo que apoya: «¿dónde ayudará reforzar esto?»."""
    for f in _nav().apoya(concepto, grado, alcance=alcance):
        typer.echo(f"distancia {f['distancia']} · {f['grado']}.° {f['tema'].removeprefix('TEMA:')} "
                   f"({f['concepto_nombre']}): {f['tema_texto'][:90]}")


@tutor_app.command("alinear")
def tutor_alinear(texto: str, grado: int = typer.Option(...), asignatura: str = typer.Option(None)) -> None:
    """Identifica el objetivo de la malla para un texto del estudiante o del docente."""
    from goes_science_kg.aprendizaje.contexto import alinear

    typer.echo(json.dumps(alinear(texto, grado, _nav(), asignatura), ensure_ascii=False, indent=1))


@tutor_app.command("contexto")
def tutor_contexto(tema: str, grado: int = typer.Option(...), concepto: str = typer.Option(None)) -> None:
    """El contexto que se inyecta al agente tutor para un objetivo (estudiante nuevo, sin evidencia)."""
    from goes_science_kg.aprendizaje.contexto import paquete
    from goes_science_kg.aprendizaje.estudiante import Perfil
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    tema = tema if tema.startswith("TEMA:") else f"TEMA:{tema}"
    typer.echo(json.dumps(paquete(Perfil("nuevo", grado), _nav(), Pedagogia.cargar(), tema, concepto),
                          ensure_ascii=False, indent=1))


def _modelo_llm(rol: str, confirmar: bool):
    """El modelo de Vertex del rol si hay --confirmar (tras verificar la cuenta GOES); si no, None (no se gasta)."""
    if not confirmar:
        return None
    from goes_science_kg.aprendizaje.llm import de_config
    from goes_science_kg.internacional import vertex

    vertex.verificar_cuenta()
    return de_config(rol)


@tutor_app.command("turno")
def tutor_turno(tema: str, grado: int = typer.Option(...), concepto: str = typer.Option(None),
                confirmar: bool = typer.Option(False, "--confirmar", help="Llama al modelo (Vertex: se paga)."),
                ) -> None:
    """Un turno del agente tutor que presenta el refuerzo de un concepto del objetivo (estudiante nuevo, sin evidencia).
    Sin --confirmar muestra el respaldo determinista y cuántas llamadas costaría; con --confirmar llama a Vertex."""
    from goes_science_kg.aprendizaje.contexto import paquete
    from goes_science_kg.aprendizaje.estudiante import Perfil
    from goes_science_kg.aprendizaje.llm import config as config_llm
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia
    from goes_science_kg.aprendizaje.tutor import Tutor, fuentes

    nav, ped = _nav(), Pedagogia.cargar()
    tid = tema if tema.startswith("TEMA:") else f"TEMA:{tema}"
    paq = paquete(Perfil("cli", grado), nav, ped, tid, concepto)
    mt = ped.microtemas.get(paq["foco"]["microtema"] or "")
    if not mt:
        raise typer.BadParameter(f"No hay microtema de {paq['foco']['concepto']} para {grado}.°")
    practica = ped.actividades[mt["practica"]]
    modelo = _modelo_llm("tutor", confirmar)
    if modelo is None:
        t = Tutor.respaldo("introducir", mt, fuentes(paq, mt), [])
        por_intento = 2 if config_llm()["fidelidad"]["obligatoria"] else 1
        typer.echo(f"Sin --confirmar: respaldo determinista. Con --confirmar costaría {por_intento} llamadas por "
                   f"intento (tutor{' y verificador de fidelidad' if por_intento == 2 else ''}), hasta "
                   f"{config_llm()['intentos_tutor']} intentos.")
    else:
        from goes_science_kg.aprendizaje.fidelidad import Verificador

        verificador = Verificador(_modelo_llm("fidelidad", confirmar)) if config_llm()["fidelidad"]["obligatoria"] \
            else None
        t = Tutor(modelo, verificador=verificador).turno("introducir", paq, mt, practica)
    typer.echo(json.dumps({"origen": t.origen, "mensaje": t.mensaje, "pregunta": t.pregunta, "fuentes": t.fuentes,
                           "errores_descartados": t.errores, "actividad": practica["enunciado"]},
                          ensure_ascii=False, indent=1))


@tutor_app.command("evaluar")
def tutor_evaluar(actividad: str, respuesta: str,
                  confirmar: bool = typer.Option(False, "--confirmar", help="Llama al evaluador (Vertex: se paga).")
                  ) -> None:
    """Califica una respuesta abierta con la rúbrica de la actividad. Sin --confirmar no hay evaluador: la respuesta
    iría a revisión docente (se muestra la rúbrica); con --confirmar llama a Vertex (1 llamada)."""
    from dataclasses import asdict

    from goes_science_kg.aprendizaje.evaluador import Evaluador
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    act = Pedagogia.cargar().actividades.get(actividad)
    if not act or act["formato"] != "abierta":
        raise typer.BadParameter(f"{actividad} no es una actividad abierta de la capa pedagógica")
    modelo = _modelo_llm("evaluador", confirmar)
    if modelo is None:
        typer.echo("Sin --confirmar: sin evaluador, la respuesta va a revisión docente. Con --confirmar costaría 1 "
                   "llamada.")
        typer.echo("Rúbrica: " + json.dumps(act["rubrica"], ensure_ascii=False, indent=1))
        return
    typer.echo(json.dumps(asdict(Evaluador(modelo).evaluar(act, respuesta)), ensure_ascii=False, indent=1))


@tutor_app.command("preparar-actividades")
def tutor_preparar_actividades(temas: list[str]) -> None:
    """Lotes para el subagente redactor-actividades (uno por objetivo) → data/pedagogia/lotes/."""
    from goes_science_kg.aprendizaje.pedagogia import preparar_lote

    for p in preparar_lote([t if t.startswith("TEMA:") else f"TEMA:{t}" for t in temas], _nav()):
        typer.echo(f"→ {p}")


@tutor_app.command("unir-actividades")
def tutor_unir_actividades() -> None:
    """Valida las salidas de redactor-actividades y las agrega a data/pedagogia/ (nacen «propuesta_pendiente»)."""
    from goes_science_kg.aprendizaje.pedagogia import unir

    typer.echo(json.dumps(unir(), ensure_ascii=False))


@tutor_app.command("validar")
def tutor_validar() -> None:
    """Integridad de la capa pedagógica (vínculos a objetivos e ids) y coherencia de las relaciones inversas."""
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia, errores_capa
    from goes_science_kg.aprendizaje.recorridos import errores_inversas

    nav = _nav()
    errores = errores_capa(Pedagogia.cargar(), nav) + errores_inversas(nav)
    for e in errores[:30]:
        typer.echo(f"✗ {e}")
    if errores:
        raise typer.Exit(1)
    typer.echo("✓ capa pedagógica e inversas coherentes")


@tutor_app.command("recorridos")
def tutor_recorridos() -> None:
    """Corre los tres recorridos de ejemplo (estudiantes simulados) → aprendizaje/recorridos/."""
    from goes_science_kg.aprendizaje.recorridos import escribir_recorridos

    for p in escribir_recorridos():
        typer.echo(f"→ {p}")


lotes_app = typer.Typer(help="Lotes de subagentes: validación de sus salidas (harness de agentes)",
                        no_args_is_help=True)
app.add_typer(lotes_app, name="lotes")


@lotes_app.command("validar")
def lotes_validar(
        tipo: str = typer.Option(None, help="alineacion | etiquetado | prerrequisitos | bloques | adopcion"),
        agente: str = typer.Option(None, help="Nombre de un subagente de .claude/agents (usa su tipo de lote)"),
        base: str = typer.Option(None, hidden=True, help="Raíz alternativa donde buscar los lotes (pruebas)"),
) -> None:
    """Valida cada salida_*.json contra su lote con las reglas de la unión. Sale con 1 si hay errores."""
    from pathlib import Path

    from goes_science_kg.lotes import comando_union, tipo_de_agente, validar

    if agente is not None:
        tipo = tipo_de_agente(agente)
        if tipo is None:
            typer.echo(f"{agente} no produce lotes: nada que validar.")
            return
    errores = validar(tipo, Path(base) if base else None)
    for archivo, errs in errores.items():
        typer.echo(f"✗ {archivo}: {len(errs)} errores")
        for e in errs[:10]:
            typer.echo(f"    - {e}")
    if errores:
        raise typer.Exit(1)
    typer.echo(f"✓ salidas válidas ({tipo or 'todos los tipos'}); se consolidan con: "
               f"{comando_union(tipo) if tipo else 'el «unir» de cada tipo'}")


revision_app = typer.Typer(help="Revisión humana con el equipo de Ciencias del MINED", no_args_is_help=True)
app.add_typer(revision_app, name="revision")


@revision_app.command("exportar")
def revision_exportar() -> None:
    """CSV por asignatura: etiquetas de confianza baja y prerrequisitos que sostienen hallazgos."""
    from goes_science_kg.grafo.almacen import cargar
    from goes_science_kg.revision_humana import exportar

    for p in exportar(*cargar()):
        typer.echo(f"→ {p}")


@revision_app.command("exportar-decisiones")
def revision_exportar_decisiones() -> None:
    """CSV de las decisiones de contenido (equivalencias, prerrequisitos, divisiones, clases) para el MINED."""
    from goes_science_kg.revision_decisiones import exportar_decisiones

    for p in exportar_decisiones():
        typer.echo(f"→ {relativa(Path(p))}")


@revision_app.command("importar-decisiones")
def revision_importar_decisiones(archivo: str) -> None:
    """Registra el veredicto del MINED (aceptar | cambiar | rechazar). Luego: make todo."""
    from goes_science_kg.revision_decisiones import importar_decisiones

    typer.echo(json.dumps(importar_decisiones(archivo), ensure_ascii=False))


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


panel_app = typer.Typer(help="Panel de expertos IA: revisión técnica interina (spec 14)", no_args_is_help=True)
app.add_typer(panel_app, name="panel")


@panel_app.command("preparar")
def panel_preparar(ronda: int = typer.Option(...), tipos: str = typer.Option(None, help="separados por coma"),
                   serie: str = typer.Option("", help="lotes aparte para un grupo de tipos")) -> None:
    """Lotes de la ronda para cada rol del panel → data/interim/panel/lotes/."""
    from goes_science_kg import panel

    lista = tipos.split(",") if tipos else None
    if ronda == 1:
        typer.echo(f"{panel.iniciar(lista)} expedientes nuevos en el estado")
    for p in panel.preparar(ronda, lista, serie):
        typer.echo(f"→ {p}")


@panel_app.command("consolidar")
def panel_consolidar(ronda: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Valida las salidas de la ronda y avanza cada expediente (unanimidad, deliberación o secuencia)."""
    from goes_science_kg import panel

    typer.echo(panel.consolidar(ronda, serie))
    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))


@panel_app.command("aplicar")
def panel_aplicar() -> None:
    """Escribe lo resuelto en las capas (decisiones, asignaciones, capa pedagógica) con su procedencia."""
    from goes_science_kg import panel

    typer.echo(panel.aplicar())


@panel_app.command("informe")
def panel_informe() -> None:
    """panel/DICTAMEN.md con lo resuelto, lo que quedó sin consenso y la asesoría del piloto."""
    from goes_science_kg import panel

    typer.echo(f"→ {panel.informe()}")


@panel_app.command("resumen")
def panel_resumen() -> None:
    """Expedientes por tipo y estado."""
    from goes_science_kg import panel

    typer.echo(json.dumps(panel.resumen(), ensure_ascii=False, indent=1))


bucle_app = typer.Typer(help="Bucle de fortalecimiento de los dictámenes del panel (spec 14, sección 7)",
                        no_args_is_help=True)
app.add_typer(bucle_app, name="bucle")


def _tipos_opcion(tipos: str | None) -> list[str] | None:
    return tipos.split(",") if tipos else None


@bucle_app.command("anclar")
def bucle_anclar(tipos: str = typer.Option(None, help="separados por coma")) -> None:
    """Mide, sin IA, si la evidencia de cada dictamen está anclada en una fuente primaria."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.anclar(_tipos_opcion(tipos)), ensure_ascii=False, indent=1))


@bucle_app.command("impugnar")
def bucle_impugnar(vuelta: int = typer.Option(...), tipos: str = typer.Option(None, help="separados por coma"),
                   serie: str = typer.Option("", help="corrida aparte sobre expedientes nuevos (p. ej. inc9)")) -> None:
    """Lotes del refutador (revisor adversarial) → data/interim/panel/bucle/lotes/."""
    from goes_science_kg import bucle

    for p in bucle.impugnar(vuelta, _tipos_opcion(tipos), serie):
        typer.echo(f"→ {p}")


@bucle_app.command("sonda")
def bucle_sonda(vuelta: int = typer.Option(...), n: int = typer.Option(None), semilla: int = typer.Option(None),
                tipos: str = typer.Option(None, help="separados por coma")) -> None:
    """Muestra ciega: los roles del panel dictaminan otra vez sin ver la resolución (lotes c<k>)."""
    from goes_science_kg import bucle

    for p in bucle.sonda(vuelta, n, semilla, _tipos_opcion(tipos)):
        typer.echo(f"→ {p}")


@bucle_app.command("cerrar-impugnacion")
def bucle_cerrar_impugnacion(vuelta: int = typer.Option(...), serie: str = typer.Option("")) -> None:
    """Verifica las citas por código y decide qué se sostiene y qué va a la réplica."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_impugnacion(vuelta, serie), ensure_ascii=False, indent=1))


@bucle_app.command("replicar")
def bucle_replicar(vuelta: int = typer.Option(...), paso: int = typer.Option(1), serie: str = typer.Option("")) -> None:
    """Lotes de la réplica para los roles del panel (ronda 10·vuelta + paso)."""
    from goes_science_kg import bucle

    for p in bucle.replicar(vuelta, paso, serie):
        typer.echo(f"→ {p}")


@bucle_app.command("cerrar-replica")
def bucle_cerrar_replica(vuelta: int = typer.Option(...), paso: int = typer.Option(1),
                         serie: str = typer.Option("")) -> None:
    """Mantiene o cambia cada resolución impugnada (unanimidad, deliberación o «sin consenso»)."""
    from goes_science_kg import bucle

    typer.echo(json.dumps(bucle.cerrar_replica(vuelta, paso, serie), ensure_ascii=False, indent=1))


@bucle_app.command("solidez")
def bucle_solidez() -> None:
    """Recalcula la solidez (sólido, respaldado, frágil, sin consenso) y muestra las métricas del bucle."""
    from goes_science_kg import bucle

    typer.echo(json.dumps({"solidez": bucle.solidez(), "metricas": bucle.metricas()}, ensure_ascii=False, indent=1))


@bucle_app.command("snapshot")
def bucle_snapshot(etapa: str = typer.Option(..., help="p. ej. «vuelta 2, réplica en curso»")) -> None:
    """panel/bucle/<ciencia>.md y RESUMEN.md: el estado del reforzamiento por ciencia (se versiona en cada etapa)."""
    from goes_science_kg import bucle

    for p in bucle.snapshot(etapa):
        typer.echo(f"→ {p}")


@bucle_app.command("cita")
def bucle_cita(fuente: str, cita: str) -> None:
    """¿Está la cita, literal, en esa fuente? (lo mismo que verifica el código al cerrar la impugnación)."""
    from goes_science_kg import bucle

    r = bucle.verificar(fuente, cita)
    marca = "✓" if r["estado"] == "anclada" else "✗"
    typer.echo(f"{marca} {r['tipo']} · {r['estado']} · {r['donde'] or ''}"
               + (f" · no existen: {', '.join(r['inexistentes'])}" if r["inexistentes"] else ""))
    raise typer.Exit(0 if r["estado"] == "anclada" else 1)


@bucle_app.command("fuente")
def bucle_fuente(fuente: str, caracteres: int = typer.Option(8000, help="0 = sin límite")) -> None:
    """Muestra el texto en que el código busca las citas de esa fuente (fila completa de la malla, objetivo o página).
    Avisa si recorta: en una fila de la malla, las microhabilidades y el indicador avanzado van al final."""
    from goes_science_kg import bucle

    for donde, texto in bucle.textos_de_fuente(fuente):
        recorte = caracteres and len(texto) > caracteres
        aviso = f"[… recortado: {len(texto) - caracteres} caracteres más; usa --caracteres 0]\n" if recorte else ""
        typer.echo(f"── {donde}\n{texto[:caracteres] if recorte else texto}\n{aviso}")


internacional_app = typer.Typer(help="Grafos internacionales de 9.°–11.° y contraste con la malla V2 (spec 11)",
                                no_args_is_help=True)
app.add_typer(internacional_app, name="internacional")


@internacional_app.callback()
def internacional_opciones(tramo: Annotated[str, typer.Option(help="Tramo de grados: 9_11 (spec 11) o 2_8 (spec 12)")]
                           = "9_11") -> None:
    """Grafos internacionales y contraste con la malla V2, por tramo de grados."""
    from goes_science_kg.internacional import tramo as tramos

    tramos.usar(tramo)


CONFIRMAR = Annotated[bool, typer.Option("--confirmar", help="Pagar las llamadas a Vertex que no están en caché.")]


def _frenar_si_hay_costo(pendientes: int, confirmar: bool) -> None:
    """Sin --confirmar, no se gasta: informa cuántas llamadas pagaría y sale con código 1. La cifra es una cota
    inferior (los reintentos y la validación de completitud suman: Ontario 1–2 estimó 24 y usó 29)."""
    techo = pendientes + -(-pendientes // 4)   # +25 %, redondeado hacia arriba
    typer.echo(f"Llamadas a Vertex fuera de la caché: {pendientes} (al menos; pide aprobación para unas {techo})"
               if pendientes else "Llamadas a Vertex fuera de la caché: 0")
    if pendientes and not confirmar:
        typer.echo("No se llamó a Vertex. Repite con --confirmar para pagarlas.", err=True)
        raise typer.Exit(1)
    if pendientes:   # se va a gastar: solo con la cuenta GOES
        from goes_science_kg.internacional import vertex

        try:
            vertex.verificar_cuenta()
        except RuntimeError as e:
            typer.echo(str(e), err=True)
            raise typer.Exit(1) from e


@internacional_app.command("extraer")
def internacional_extraer(paises: Annotated[list[str] | None, typer.Argument(help="SG, JP…")] = None,
                          confirmar: CONFIRMAR = False) -> None:
    """Extrae y valida con Vertex los objetivos de los países (config/internacional.yaml)."""
    from goes_science_kg.internacional import consenso, extraer

    elegidos = paises or consenso.paises()
    _frenar_si_hay_costo(sum(extraer.llamadas_pendientes(p) for p in elegidos), confirmar)
    for p in elegidos:
        typer.echo(extraer.extraer_pais(p))
    # La extracción reescribe los objetivos desde la caché: sin esto se pierden las correcciones de metadatos (grados,
    # Extension Part en cursiva, sugerencias opcionales al docente). Pasó el 2026-10-13 con HK S1–3.
    typer.echo(f"metadatos corregidos: {extraer.corregir_metadatos()}")


@internacional_app.command("etiquetar")
def internacional_etiquetar(paises: Annotated[list[str] | None, typer.Argument(help="vacío = todos")] = None,
                            confirmar: CONFIRMAR = False) -> None:
    """Etiqueta con conceptos los objetivos de los países y la malla V2 (2.°–11.°)."""
    from goes_science_kg.internacional import consenso, etiquetar

    grupos = [*consenso.grupos_paises(paises or None), *etiquetar.grupos_malla_v2()]
    _frenar_si_hay_costo(etiquetar.pendientes(grupos), confirmar)
    for g in grupos:
        typer.echo(etiquetar.etiquetar(*g))


@internacional_app.command("congelar-catalogo")
def internacional_congelar_catalogo(version: str) -> None:
    """Congela el catálogo de etiquetado con el vocabulario vivo. Invalida la caché: re-etiquetar se paga completo."""
    from goes_science_kg.internacional import etiquetar

    typer.echo(etiquetar.congelar_catalogo(version))


@internacional_app.command("corregir-metadatos")
def internacional_corregir_metadatos() -> None:
    """Corrige grados y nivel (Extension Part en cursiva) de los objetivos ya extraídos, sin Vertex (spec 12)."""
    from goes_science_kg.internacional import extraer

    typer.echo(extraer.corregir_metadatos())


@internacional_app.command("construir")
def internacional_construir() -> None:
    """Arma data/grafo/internacional/ (grafo por país + consenso) y los informes de internacional/."""
    from goes_science_kg.internacional import consenso, informe

    typer.echo(consenso.construir())
    typer.echo(informe.escribir())


if __name__ == "__main__":
    app()
