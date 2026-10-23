"""Expose the tutor command group for the science curriculum pipeline."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from goes_science_kg.config import relativa

app = typer.Typer(help="Apoyo al aprendizaje sobre el grafo (spec 13, prototipo)", no_args_is_help=True)


def _nav():
    """Load the shared curriculum navigator only when needed by a command."""
    from goes_science_kg.aprendizaje.pedagogia import navegador_compartido

    return navegador_compartido()


@app.command("bases")
def tutor_bases(tema: str, profundidad: int = 2) -> None:
    """Traverse an objective's prerequisite concepts."""
    nav = _nav()
    tema = tema if tema.startswith("TEMA:") else f"TEMA:{tema}"
    for b in nav.bases(tema, profundidad):
        typer.echo(
            f"{'  ' * (b.profundidad - 1)}{b.profundidad} {nav.por_id[b.concepto].etiqueta} [{b.concepto}] "
            f"conf {b.confianza} · {'antes' if b.antes_del_objetivo else 'NO antes'} en la malla "
            f"({(b.primer_tema or '—').removeprefix('TEMA:')}) · {b.estado_relacion}"
        )


@app.command("apoya")
def tutor_apoya(concepto: str, grado: int = typer.Option(None), alcance: int = 2) -> None:
    """Find objectives supported by reinforcing a prerequisite concept."""
    for f in _nav().apoya(concepto, grado, alcance=alcance):
        typer.echo(
            f"distancia {f['distancia']} · {f['grado']}.° {f['tema'].removeprefix('TEMA:')} "
            f"({f['concepto_nombre']}): {f['tema_texto'][:90]}"
        )


@app.command("alinear")
def tutor_alinear(texto: str, grado: int = typer.Option(...), asignatura: str = typer.Option(None)) -> None:
    """Identify candidate curriculum objectives for learner or teacher text."""
    from goes_science_kg.aprendizaje.contexto import alinear

    typer.echo(json.dumps(alinear(texto, grado, _nav(), asignatura), ensure_ascii=False, indent=1))


@app.command("contexto")
def tutor_contexto(tema: str, grado: int = typer.Option(...), concepto: str = typer.Option(None)) -> None:
    """Build tutor context for a new learner without observed evidence."""
    from goes_science_kg.aprendizaje.contexto import paquete
    from goes_science_kg.aprendizaje.estudiante import Perfil
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    tema = tema if tema.startswith("TEMA:") else f"TEMA:{tema}"
    typer.echo(
        json.dumps(
            paquete(Perfil("nuevo", grado), _nav(), Pedagogia.cargar(), tema, concepto), ensure_ascii=False, indent=1
        )
    )


def _modelo_llm(rol: str, confirmar: bool):
    """Create the role model only after explicit confirmation and account verification."""
    if not confirmar:
        return None
    from goes_science_kg.aprendizaje.llm import de_config
    from goes_science_kg.internacional import vertex

    vertex.verificar_cuenta()
    return de_config(rol)


@app.command("turno")
def tutor_turno(
    tema: str,
    grado: int = typer.Option(...),
    concepto: str = typer.Option(None),
    confirmar: bool = typer.Option(False, "--confirmar", help="Llama al modelo (Vertex: se paga)."),
) -> None:
    """Prepare a reinforcement tutor turn for a new learner."""

    # Implementation notes:
    # Sin --confirmar muestra el respaldo determinista y cuántas llamadas costaría; con --confirmar llama a Vertex.
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
        typer.echo(
            f"Sin --confirmar: respaldo determinista. Con --confirmar costaría {por_intento} llamadas por "
            f"intento (tutor{' y verificador de fidelidad' if por_intento == 2 else ''}), hasta "
            f"{config_llm()['intentos_tutor']} intentos."
        )
    else:
        from goes_science_kg.aprendizaje.fidelidad import Verificador

        verificador = (
            Verificador(_modelo_llm("fidelidad", confirmar)) if config_llm()["fidelidad"]["obligatoria"] else None
        )
        t = Tutor(modelo, verificador=verificador).turno("introducir", paq, mt, practica)
    typer.echo(
        json.dumps(
            {
                "origen": t.origen,
                "mensaje": t.mensaje,
                "pregunta": t.pregunta,
                "fuentes": t.fuentes,
                "errores_descartados": t.errores,
                "actividad": practica["enunciado"],
            },
            ensure_ascii=False,
            indent=1,
        )
    )


@app.command("evaluar")
def tutor_evaluar(
    actividad: str,
    respuesta: str,
    confirmar: bool = typer.Option(False, "--confirmar", help="Llama al evaluador (Vertex: se paga)."),
) -> None:
    """Assess an open response only when a model invocation was explicitly confirmed."""

    # Implementation notes:
    # iría a revisión docente (se muestra la rúbrica); con --confirmar llama a Vertex (1 llamada).
    from dataclasses import asdict

    from goes_science_kg.aprendizaje.evaluador import Evaluador
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    act = Pedagogia.cargar().actividades.get(actividad)
    if not act or act["formato"] != "abierta":
        raise typer.BadParameter(f"{actividad} no es una actividad abierta de la capa pedagógica")
    modelo = _modelo_llm("evaluador", confirmar)
    if modelo is None:
        typer.echo(
            "Sin --confirmar: sin evaluador, la respuesta va a revisión docente. Con --confirmar costaría 1 llamada."
        )
        typer.echo("Rúbrica: " + json.dumps(act["rubrica"], ensure_ascii=False, indent=1))
        return
    typer.echo(json.dumps(asdict(Evaluador(modelo).evaluar(act, respuesta)), ensure_ascii=False, indent=1))


@app.command("paquete")
def tutor_paquete(temas: Annotated[list[str], typer.Argument(help="ids de tema (TEMA:… o sin prefijo)")]) -> None:
    """Build topic-specific lesson packages with raw sources and completeness information."""

    # Implementation notes:
    # entregas/paquetes_clase/.
    from goes_science_kg.aprendizaje.paquete import escribir

    for p in escribir(temas):
        typer.echo(f"→ {relativa(p)}")


@app.command("preparar-actividades")
def tutor_preparar_actividades(
    temas: list[str],
    ideas_previas: int = typer.Option(1, help="ideas previas del concepto principal"),
    ligero: bool = typer.Option(
        False, help="solo el objetivo, el experimento y las ideas previas (paquete de clase ligero)"
    ),
) -> None:
    """Prepare one activity-writing batch per curriculum objective."""
    from goes_science_kg.aprendizaje.pedagogia import preparar_lote

    for p in preparar_lote(
        [t if t.startswith("TEMA:") else f"TEMA:{t}" for t in temas], _nav(), ideas_previas=ideas_previas, ligero=ligero
    ):
        typer.echo(f"→ {p}")


@app.command("unir-actividades")
def tutor_unir_actividades(
    prefijo: Annotated[list[str] | None, typer.Option(help="Solo los lotes que empiezan así (G09-CIE-U1-)")] = None,
) -> None:
    """Validate and append proposed activities to the pedagogical layer."""
    from goes_science_kg.aprendizaje.pedagogia import unir

    typer.echo(json.dumps(unir(prefijos=prefijo or None), ensure_ascii=False))


@app.command("validar")
def tutor_validar() -> None:
    """Validate pedagogical links and the consistency of inverse relationships."""
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia, errores_capa
    from goes_science_kg.aprendizaje.recorridos import errores_inversas

    nav = _nav()
    errores = errores_capa(Pedagogia.cargar(), nav) + errores_inversas(nav)
    for e in errores[:30]:
        typer.echo(f"✗ {e}")
    if errores:
        raise typer.Exit(1)
    typer.echo("✓ capa pedagógica e inversas coherentes")


@app.command("recorridos")
def tutor_recorridos() -> None:
    """Run three reproducible journeys with explicitly simulated learners."""
    from goes_science_kg.aprendizaje.recorridos import escribir_recorridos

    for p in escribir_recorridos():
        typer.echo(f"→ {p}")
