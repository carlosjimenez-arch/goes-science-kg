"""Reject agent completion when its batch output fails the registered consolidation contract."""

# Historical test notes:
# Al terminar uno de los subagentes de .claude/agents que escriben `salida_*.json` (alineador-marcos,
# etiquetador-conceptos, ordenador-prerrequisitos, redactor-bloques, conciliador-propuestas), corre
# `uv run gskg lotes validar --agente <nombre>`, que aplica las mismas reglas que el «unir» de cada tipo de lote.
#
# - Salidas válidas: sin salida; el subagente termina.
# - Errores: {"decision": "block", "reason": ...}; el subagente sigue trabajando y ve qué corregir.
# - Tras MAX_INTENTOS bloqueos del mismo subagente lo deja terminar y avisa al usuario (systemMessage), para no entrar
#   en un ciclo. Si la validación no puede correr (uv ausente, error inesperado), avisa y no bloquea.
#
# GSKG_LOTES_BASE (solo pruebas) cambia la raíz donde se buscan los lotes.

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from comun import RAIZ, entrada  # noqa: E402

MAX_INTENTOS = 3


def _contador(agente_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"gskg-validar-lotes-{agente_id or 'sin-id'}.txt"


def _intentos(agente_id: str, reiniciar: bool = False) -> int:
    p = _contador(agente_id)
    if reiniciar:
        p.unlink(missing_ok=True)
        return 0
    n = (int(p.read_text()) if p.exists() and p.read_text().strip().isdigit() else 0) + 1
    p.write_text(str(n))
    return n


def _responder(datos: dict) -> None:
    print(json.dumps(datos, ensure_ascii=False))


def _comando(agente: str) -> list[str]:
    """Reuse the installed validation environment without package resolution or network access."""
    ejecutable = RAIZ / ".venv" / ("Scripts/gskg.exe" if os.name == "nt" else "bin/gskg")
    prefijo = (
        [str(ejecutable)]
        if ejecutable.is_file() and os.access(ejecutable, os.X_OK)
        else ["uv", "run", "--frozen", "-q", "gskg"]
    )
    return [*prefijo, "lotes", "validar", "--agente", agente]


def main() -> None:
    datos = entrada()
    agente, agente_id = datos.get("agent_type") or "", datos.get("agent_id") or datos.get("session_id") or ""
    if not agente:
        return
    comando = _comando(agente)
    if base := os.environ.get("GSKG_LOTES_BASE"):
        comando += ["--base", base]
    try:
        r = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.SubprocessError) as e:
        _responder(
            {
                "systemMessage": f"No se pudo validar la salida de {agente} ({e}). "
                f"Corre `uv run gskg lotes validar --agente {agente}` antes de unir."
            }
        )
        return
    if r.returncode == 0:
        _intentos(agente_id, reiniciar=True)
        return
    detalle = "\n".join((r.stdout + r.stderr).strip().splitlines()[-40:])
    if r.returncode != 1:  # la validación falló por otra razón: no se culpa al subagente
        _responder({"systemMessage": f"La validación de {agente} no pudo completarse:\n{detalle}"})
        return
    n = _intentos(agente_id)
    if n > MAX_INTENTOS:
        _intentos(agente_id, reiniciar=True)
        _responder(
            {
                "systemMessage": f"{agente} terminó con salidas inválidas tras {MAX_INTENTOS} intentos de "
                f"corrección; no las unas sin revisarlas:\n{detalle}"
            }
        )
        return
    _responder(
        {
            "decision": "block",
            "reason": f"Tu salida no pasa la validación del proyecto (intento {n} de {MAX_INTENTOS}). Corrige "
            f"estos errores en tus salida_*.json y vuelve a validar con "
            f"`uv run gskg lotes validar --agente {agente}` antes de terminar. No corras la unión:\n"
            f"{detalle}",
        }
    )


if __name__ == "__main__":
    main()
