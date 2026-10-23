"""Treat incorrect answers as hypotheses to verify through diagnostic probes."""

# Historical implementation notes:
# Reglas:
# 1. La respuesta solo actualiza lo que la actividad evalúa (estudiante.Perfil.observar). Las bases relacionadas no
#    cambian: se abren hipótesis «quizá le falta X», a lo sumo `max_hipotesis_abiertas`.
# 2. Puntaje de una base B: (1 − P(B)) × peso de la confianza de la arista × peso del distractor (si la opción elegida
#    delata una dificultad de B). P(B) es la previa del estudiante, no la que dejó el error.
# 3. Orden: primero las bases (si falta una base, reforzar el concepto no sirve); la hipótesis «en el concepto»
#    (la dificultad está en el concepto evaluado: el del objetivo, o la base cuya comprobación falló)
#    va al final, salvo que el distractor la señale (entonces va primero).
# 4. Confirmar exige `evidencias_para_confirmar` observaciones y P < umbral_brecha; un sondeo correcto con P ≥
#    umbral_descartar la descarta. Lo que no se alcanza a comprobar queda «sin_comprobar», nunca «brecha».

from __future__ import annotations

from collections.abc import Callable

from goes_science_kg.aprendizaje.estudiante import Evidencia, Hipotesis, Perfil
from goes_science_kg.aprendizaje.pedagogia import Pedagogia
from goes_science_kg.aprendizaje.relaciones import Navegador, antes_en_la_malla, confianza
from goes_science_kg.config import cargar


def config() -> dict:
    """Load the configured diagnostic thresholds and probe limits."""

    return cargar("aprendizaje")


def previa(nav: Navegador, objetivo: str, cid: str) -> tuple[float, str]:
    """Derive the initial mastery probability from curriculum position alone."""
    d = config()["dominio"]
    if cid.startswith("TEMA:") or cid in nav.conceptos_de_tema(objetivo, ("principal",)):
        return d["inicial_en_curso"], "objetivo en curso"
    primero = nav.primer_tema(cid)
    if primero and antes_en_la_malla(primero, objetivo):
        return d["inicial_visto"], f"la malla lo trabaja antes ({primero.removeprefix('TEMA:')})"
    return d["inicial_no_visto"], "la malla no lo trabaja antes del objetivo"


def abrir(
    perfil: Perfil,
    nav: Navegador,
    ped: Pedagogia,
    objetivo: str,
    actividad: dict,
    ev: Evidencia,
    previas: dict[str, tuple[float, str]],
) -> list[Hipotesis]:
    """Open ordered diagnostic hypotheses after an incorrect answer."""
    cfg = config()["diagnostico"]
    dif = ped.dificultades.get(ev.dificultad or "")
    dif_conceptos = nav.equivalentes(dif["concepto"]) if dif else set()
    evaluados = [c for c in actividad["evalua"] if c.startswith("CON:")]
    candidatas: dict[str, Hipotesis] = {}
    for c in evaluados:
        for a in nav.requiere(c, cfg["confianza_minima_prerrequisito"]):
            b = a.origen
            if b in candidatas or b in evaluados:
                continue
            pb = perfil.conceptos[b].p if b in perfil.conceptos else previa(nav, objetivo, b)[0]
            peso = cfg["peso_confianza"][confianza(a)] * (cfg["peso_distractor"] if b in dif_conceptos else 1.0)
            candidatas[b] = Hipotesis(
                f"H{len(perfil.hipotesis) + len(candidatas) + 1}", objetivo, b, "base", ev.id, round((1 - pb) * peso, 3)
            )
    bases = sorted(candidatas.values(), key=lambda h: (-h.puntaje, h.concepto))
    abiertas, resto = bases[: cfg["max_hipotesis_abiertas"]], bases[cfg["max_hipotesis_abiertas"] :]
    for h in resto:
        h.estado = "sin_comprobar"
    dentro = []
    for c in evaluados:
        p_antes = previas.get(c, previa(nav, objetivo, c))[0]
        senalado = bool(dif_conceptos & nav.equivalentes(c))
        dentro.append(
            Hipotesis(
                f"H{len(perfil.hipotesis) + len(candidatas) + len(dentro) + 1}",
                objetivo,
                c,
                "en_el_concepto",
                ev.id,
                round((1 - p_antes) * (cfg["peso_distractor"] if senalado else 1.0), 3),
                evidencias=[ev.id],
            )
        )
    primero = [
        h
        for h in dentro
        if h.puntaje > max((b.puntaje for b in abiertas), default=0) and dif_conceptos & nav.equivalentes(h.concepto)
    ]
    orden = primero + abiertas + [h for h in dentro if h not in primero]
    perfil.hipotesis += orden + resto
    return orden


def resolver(h: Hipotesis, perfil: Perfil) -> str:
    """Confirm, reject, or retain a hypothesis using accumulated evidence."""
    cfg, d = config()["diagnostico"], config()["dominio"]
    e = perfil.conceptos.get(h.concepto)
    if not e:
        return h.estado
    ultima = next((x for x in reversed(perfil.evidencias) if x.id == (h.evidencias or [""])[-1]), None)
    if ultima and ultima.correcta and e.p >= cfg["umbral_descartar"]:
        h.estado = "descartada"
    elif len(h.evidencias) >= cfg["evidencias_para_confirmar"] and e.p < d["umbral_brecha"]:
        h.estado = "confirmada"
    return h.estado


def comprobar(
    hipotesis: list[Hipotesis],
    perfil: Perfil,
    ped: Pedagogia,
    grado: int,
    responder: Callable[[dict], Evidencia],
    usadas: set[str],
) -> Hipotesis | None:
    """Probe hypotheses in order under the configured diagnostic limit."""

    # Implementation notes:
    # `responder` presenta una actividad al estudiante y devuelve la evidencia ya registrada en el perfil.
    restantes = config()["diagnostico"]["max_sondeos_por_intento"]
    for h in hipotesis:
        while h.estado == "abierta" and restantes > 0:
            sondeo = next(iter(ped.es_evaluado_por(h.concepto, rol="sondeo", grado=grado, excluir=tuple(usadas))), None)
            if sondeo is None:
                h.estado = "sin_comprobar"  # no hay con qué comprobarla: no se concluye nada
                break
            usadas.add(sondeo["id"])
            restantes -= 1
            ev = responder(sondeo)
            h.evidencias.append(ev.id)
            resolver(h, perfil)
        if h.estado == "confirmada":
            break
    for h in hipotesis:
        if h.estado == "abierta":
            h.estado = "sin_comprobar"
    return next((h for h in hipotesis if h.estado == "confirmada"), None)
