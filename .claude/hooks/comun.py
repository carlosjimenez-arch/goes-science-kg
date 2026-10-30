"""Share standard-library-only utilities across repository editor hooks."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def config() -> dict:
    """Load the configured identity and protected source roots."""
    return json.loads((RAIZ / ".claude" / "harness.json").read_text(encoding="utf-8"))


def entrada() -> dict:
    """Parse the JSON tool event received on standard input."""
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def decidir(decision: str, motivo: str) -> None:
    """Return a structured hook decision with the user-visible reason."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": motivo,
                }
            },
            ensure_ascii=False,
        )
    )
    sys.exit(0)


def relativa(ruta: str) -> str:
    """Resolve a repository-relative path while preserving external paths for display."""
    p = Path(ruta)
    try:
        return p.resolve().relative_to(RAIZ.resolve()).as_posix() if p.is_absolute() else p.as_posix().lstrip("./")
    except ValueError:
        return p.as_posix()
