"""Validación de los lotes de subagentes (harness de agentes: .claude/agents y .claude/hooks/validar_lotes.py).

Cada tarea de IA del proyecto sigue el mismo circuito: un comando «preparar» escribe `lote_<x>.json`, un subagente
escribe `salida_<x>.json` en la misma carpeta y un comando «unir» valida y consolida. Este módulo reúne, por tipo de
lote, la función que valida UNA salida contra su lote, la misma que usa la unión correspondiente. Así un subagente
del proyecto no puede terminar con una salida que la unión rechazaría: el hook SubagentStop corre
`gskg lotes validar --agente <nombre>` y, si hay errores, lo devuelve a corregirlos.

Las salidas que todavía no existen no son error (otro subagente puede estar trabajando en ellas).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from goes_science_kg.config import relativa, ruta


@dataclass(frozen=True)
class TipoLote:
    carpeta: str                                   # donde viven lote_*.json y salida_*.json
    validar: Callable[[object, list[dict]], list[str]]
    unir: str                                      # comando que consolida (para el mensaje al subagente)


def _tipos() -> dict[str, list[TipoLote]]:
    from goes_science_kg import alineacion, comunidades, conceptos, panel, prerrequisitos, propuesta
    from goes_science_kg.aprendizaje import pedagogia

    return {
        "alineacion": [TipoLote("data/interim/alineaciones/lotes", alineacion.errores_lote,
                                "gskg alinear unir-bachillerato | unir-temas")],
        "etiquetado": [TipoLote("data/interim/conceptos/lotes", conceptos.errores_lote_temas,
                                "gskg conceptos unir-etiquetado"),
                       TipoLote("data/interim/conceptos/lotes_paises", conceptos.errores_lote_paises,
                                "gskg conceptos unir-paises")],
        "prerrequisitos": [TipoLote("data/interim/prerrequisitos/lotes",
                                    lambda _lote, salida: prerrequisitos.errores_salida(salida),
                                    "gskg conceptos unir-prerrequisitos")],
        "bloques": [TipoLote("data/interim/comunidades", comunidades.errores_resumenes, "gskg grados resumenes")],
        "adopcion": [TipoLote("data/interim/propuestas", propuesta.errores_adopcion,
                              "gskg propuesta unir-adopcion")],
        "pedagogia": [TipoLote("data/pedagogia/lotes", pedagogia.errores_lote, "gskg tutor unir-actividades")],
        "panel": [TipoLote("data/interim/panel/lotes", panel.errores_lote, "gskg panel consolidar --ronda <n>")],
    }


# Subagente del proyecto (.claude/agents/<nombre>.md) → tipo de lote que produce.
AGENTES = {
    "alineador-marcos": "alineacion",
    "etiquetador-conceptos": "etiquetado",
    "ordenador-prerrequisitos": "prerrequisitos",
    "redactor-bloques": "bloques",
    "conciliador-propuestas": "adopcion",
    "redactor-actividades": "pedagogia",
    "experto-biologia": "panel",
    "experto-fisica": "panel",
    "experto-quimica": "panel",
    "experto-tierra-espacio": "panel",
    "psicopedagogo": "panel",
}


def validar_par(tipo: TipoLote, p_lote: Path) -> list[str] | None:
    """Errores de la salida de un lote; None si la salida aún no existe."""
    p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
    if not p_sal.exists():
        return None
    try:
        salida = json.loads(p_sal.read_text(encoding="utf-8"))
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON inválido: {e}"]
    if not isinstance(salida, list):
        return ["la salida debe ser un arreglo JSON (un objeto por ítem)"]
    return tipo.validar(lote, salida)


def validar(nombre: str | None = None, base: Path | None = None) -> dict[str, list[str]]:
    """Errores por archivo de salida (ruta relativa → errores) de un tipo de lote, o de todos si `nombre` es None.
    Solo incluye las salidas con errores. `base` reemplaza la raíz del repo (pruebas)."""
    tipos = _tipos()
    if nombre is not None and nombre not in tipos:
        raise ValueError(f"Tipo de lote desconocido {nombre!r}; opciones: {', '.join(tipos)}")
    errores: dict[str, list[str]] = {}
    for clave in [nombre] if nombre else sorted(tipos):
        for tipo in tipos[clave]:
            carpeta = (base / tipo.carpeta) if base else ruta(tipo.carpeta)
            for p_lote in sorted(carpeta.glob("lote_*.json")):
                if errs := validar_par(tipo, p_lote):
                    sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
                    errores[relativa(sal) if base is None else sal.relative_to(base).as_posix()] = errs
    return errores


def tipo_de_agente(agente: str) -> str | None:
    """Tipo de lote que valida el hook al terminar ese subagente (None: no es un subagente de lotes)."""
    return AGENTES.get(agente)


def comando_union(nombre: str) -> str:
    """Los comandos que consolidan ese tipo de lote."""
    return " · ".join(t.unir for t in _tipos()[nombre])
