"""Utilidades compartidas por los hooks del proyecto (solo biblioteca estándar: corren con el python3 del sistema)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def config() -> dict:
    """Identidad y rutas protegidas (.claude/harness.json)."""
    return json.loads((RAIZ / ".claude" / "harness.json").read_text(encoding="utf-8"))


def entrada() -> dict:
    """El JSON que Claude Code manda por stdin a cada hook."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def decidir(decision: str, motivo: str) -> None:
    """Responde a PreToolUse con deny (bloquea, el motivo lo ve Claude) o ask (lo decide el usuario)."""
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision,
                                             "permissionDecisionReason": motivo}}, ensure_ascii=False))
    sys.exit(0)


def relativa(ruta: str) -> str:
    """Ruta relativa a la raíz del repo (o tal cual si queda fuera)."""
    p = Path(ruta)
    try:
        return p.resolve().relative_to(RAIZ.resolve()).as_posix() if p.is_absolute() else p.as_posix().lstrip("./")
    except ValueError:
        return p.as_posix()
