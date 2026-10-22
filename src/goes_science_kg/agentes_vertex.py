"""Execute validated batch agents through the Vertex AI adapter."""

# Historical implementation notes:
# Corre un lote de `redactor-actividades` o del panel (expertos y psicopedagogo) con un modelo de Vertex. El subagente
# de
# Claude lee archivos y corre comandos; aquí todo eso va empaquetado de antemano en el mensaje:
# - instrucción del agente (`.claude/agents/<agente>.md`) y los prompts que cita;
# - el lote completo;
# - el texto de la fila vigente de la malla de cada tema del lote (lo que daría `gskg bucle fuente`);
# - para el redactor, las ideas previas que ya existen de los conceptos del lote y los títulos de los experimentos de la
#   misma unidad (para no repetirlos), y un ejemplo de cada tipo de elemento ya revisado por el panel.
#
# La salida pasa por el MISMO validador que el hook de los subagentes (`lotes.validar_par`). Si falla, se le devuelven
# los errores al modelo y se reintenta. Solo se escribe `salida_*.json` si es válida; si no, queda en
# `salida_*.vertex_fallida.json` para revisarla. Cada llamada cuenta para el tope `VERTEX_MAX_CALLS` y queda en caché.

from __future__ import annotations

import json
import re
from pathlib import Path

from goes_science_kg.config import ruta

PROMPTS = {
    "redactor-actividades": ["prompts/redactar_actividades.md"],
    "experto-fisica": ["prompts/panel_dictaminar.md"],
    "experto-quimica": ["prompts/panel_dictaminar.md"],
    "experto-biologia": ["prompts/panel_dictaminar.md"],
    "experto-tierra-espacio": ["prompts/panel_dictaminar.md"],
    "psicopedagogo": ["prompts/panel_dictaminar.md"],
}
MAX_FUENTE = 7000
INSTRUCCION_SALIDA = (
    "\n\n## Cómo respondes aquí\nNo tienes herramientas: no puedes leer archivos ni correr comandos. Todo lo que "
    "necesitas (lote, filas de la malla, capa existente) va en el mensaje; donde la instrucción dice que leas o corras "
    "algo, usa lo que viene en el mensaje. Responde SOLO con el JSON que escribirías en el archivo de salida: un "
    "arreglo con un objeto por ranura o por expediente, sin texto alrededor. "
    "Recalcula cada número antes de escribirlo."
)


def _sin_encabezado(texto: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n", "", texto, flags=re.S)


def sistema(agente: str) -> str:
    """Load the registered system instructions for a batch-agent role."""

    partes = [_sin_encabezado(ruta(f".claude/agents/{agente}.md").read_text(encoding="utf-8"))]
    partes += [f"\n\n# {p}\n\n" + ruta(p).read_text(encoding="utf-8") for p in PROMPTS[agente]]
    return "".join(partes) + INSTRUCCION_SALIDA


def _temas(texto: str) -> list[str]:
    return sorted(set(re.findall(r"TEMA:G\d\d-[A-Z]+-U\d+-\d+\.\d+(?:-v3)?", texto)))


def _fuentes(lote: dict) -> str:
    from goes_science_kg import bucle

    salida = []
    for t in _temas(json.dumps(lote, ensure_ascii=False)):
        textos = bucle.textos_de_fuente(t)
        if textos:
            donde, texto = textos[0]  # la primera es la fila vigente
            salida.append(f"── {t} · {donde}\n{texto[:MAX_FUENTE]}")
    return "\n\n".join(salida)


def _capa_para_redactor(lote: dict) -> str:
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia

    ped = Pedagogia.cargar()
    texto = json.dumps(lote, ensure_ascii=False)
    conceptos = sorted(set(re.findall(r"CON:([a-z\-]+/[a-z0-9\-]+)", texto)))
    difs = [
        f"- {i}: {d.get('descripcion', '')[:200]}"
        for i, d in sorted(ped.dificultades.items())
        if any(i.startswith(f"DIF:{c}/") for c in conceptos)
    ]
    unidad = re.match(r"(G\d\d-[A-Z]+-U\d+)-", lote["objetivo"]["id"].removeprefix("TEMA:"))
    exps = [
        f"- {x['id']}: {x.get('titulo', '')}"
        for x in ped.experimentos.values()
        if unidad and x["id"].startswith(f"EXP:{unidad.group(1)}-")
    ]
    ejemplos = []
    for coleccion in (ped.actividades, ped.dificultades, ped.experimentos):
        revisado = next((x for x in coleccion.values() if x.get("estado") == "revisado_panel"), None)
        if revisado:
            ejemplos.append(
                json.dumps({k: v for k, v in revisado.items() if k not in ("revision_panel",)}, ensure_ascii=False)
            )
    return (
        "## Ideas previas que ya existen de estos conceptos (puedes enlazarlas en `distractores`)\n"
        + ("\n".join(difs) or "(ninguna)")
        + "\n\n## Experimentos que ya existen en la misma unidad (no los repitas)\n"
        + ("\n".join(exps) or "(ninguno)")
        + "\n\n## Ejemplo del formato de cada tipo de elemento (ya revisado por el panel; no lo copies)\n"
        + "\n".join(ejemplos)
    )


def mensaje(p_lote: Path, agente: str) -> str:
    """Build a batch message from its input and verified source context."""

    lote = json.loads(p_lote.read_text(encoding="utf-8"))
    partes = [
        f"# Lote `{p_lote.name}`\n```json\n{json.dumps(lote, ensure_ascii=False, indent=1)}\n```",
        "# Filas vigentes de la malla (lo que mostraría `gskg bucle fuente`)\n" + _fuentes(lote),
    ]
    if agente == "redactor-actividades":
        partes.append(_capa_para_redactor(lote))
    return "\n\n".join(partes)


def _tipo(agente: str):
    from goes_science_kg import lotes

    return lotes._tipos()[lotes.AGENTES[agente]][0]


def _desenvolver(respuesta) -> list:
    if isinstance(respuesta, dict):
        for k in ("salida", "dictamenes", "elementos", "items"):
            if isinstance(respuesta.get(k), list):
                return respuesta[k]
        return [respuesta]
    return respuesta


def correr(p_lote: Path, agente: str, modelo: str, reintentos: int = 2) -> list[str]:
    """Execute a Vertex batch and return any final validation errors."""
    from goes_science_kg.internacional import vertex

    tipo = _tipo(agente)
    lote = json.loads(p_lote.read_text(encoding="utf-8"))
    base, sis = mensaje(p_lote, agente), sistema(agente)
    texto, errores, salida = base, [], []
    for _ in range(reintentos + 1):
        salida = _desenvolver(vertex.generar_json(texto, modelo=modelo, sistema=sis, max_tokens=65536))
        errores = tipo.validar(lote, salida)
        if not errores:
            p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1)).write_text(
                json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
            )
            return []
        texto = (
            base + "\n\n# Tu respuesta anterior no pasó la validación\nCorrige estos errores y devuelve la salida "
            "COMPLETA otra vez:\n"
            + "\n".join(f"- {e}" for e in errores[:40])
            + f"\n\nTu respuesta anterior:\n```json\n{json.dumps(salida, ensure_ascii=False)}\n```"
        )
    p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1).replace(".json", ".vertex_fallida.json")).write_text(
        json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    return errores


def estimar(lotes: list[Path], agente: str, modelo: str) -> dict:
    """Estimate batch counts, cache hits, and message sizes without invoking models."""
    from goes_science_kg.internacional import vertex

    sis = sistema(agente)
    tam = [len(sis) + len(mensaje(p, agente)) for p in lotes]
    en_cache = sum(vertex.en_cache(mensaje(p, agente), modelo=modelo, sistema=sis) for p in lotes)
    return {
        "lotes": len(lotes),
        "en_cache": en_cache,
        "llamadas_minimas": len(lotes) - en_cache,
        "llamadas_maximas": (len(lotes) - en_cache) * 3,
        "caracteres_por_mensaje": max(tam) if tam else 0,
    }
