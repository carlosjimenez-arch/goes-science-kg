"""Harness de Claude Code (.claude/hooks): cada guarda decide lo esperado con la entrada que manda Claude Code."""

from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

from goes_science_kg.config import ruta

HOOKS = ruta(".claude/hooks")


def _correr(script: str, datos: dict, **env: str) -> dict | None:
    r = subprocess.run([sys.executable, str(HOOKS / script)], input=json.dumps(datos), capture_output=True, text=True,
                       env={**os.environ, "CLAUDE_PROJECT_DIR": str(ruta(".")), "GSKG_HARNESS_SIN_PRUEBAS": "1", **env},
                       timeout=60, check=True)
    return json.loads(r.stdout) if r.stdout.strip() else None


def _bash(comando: str, **env: str) -> str | None:
    salida = _correr("guardia_bash.py", {"tool_name": "Bash", "tool_input": {"command": comando}}, **env)
    return salida and salida["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize("comando, esperado", [
    ("cat .env", "deny"),
    ("grep GOOGLE ./.env", "deny"),
    ("python3 -c \"print(open('.env').read())\"", "deny"),
    ("git check-ignore -v .env", None),                      # mencionarlo no es leerlo
    ("cat .env.example", None),
    ("rm -rf data/fuentes/mined", "deny"),
    ("echo x > reportes/cobertura_curricular/a.md", "deny"),
    ("ls data/fuentes/mined && cp data/fuentes/a.pdf /tmp/x", None),
    ("uv run gskg internacional --tramo 2_8 extraer", None),  # sin --confirmar solo estima
    ("uv run gskg internacional --tramo 2_8 extraer --confirmar", "ask"),
    ("uv run gskg internacional etiquetar --confirmar", "ask"),
    ("uv run gskg internacional congelar-catalogo v2", "ask"),
    ("make internacional-ia CONFIRMAR=--confirmar", "ask"),
    ("git push --force origin main", "deny"),
    ("git status", None),
])
def test_guardia_bash(comando, esperado):
    assert _bash(comando) == esperado


def test_commit_exige_la_cuenta_de_goes():
    otra = {"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "user.email", "GIT_CONFIG_VALUE_0": "otra@ejemplo.com"}
    assert _bash('git commit -m "x"', **otra) == "deny"
    assert _bash('git commit -m "x"') is None   # cuenta GOES (pruebas desactivadas solo en este test)


@pytest.mark.parametrize("ruta_archivo, esperado", [
    ("data/fuentes/mined/x.xlsx", "deny"),
    ("reportes/cobertura_curricular/CLAUDE.md", "deny"),
    ("data/grafo/nodos.jsonl", "deny"),
    ("data/interim/internacional/cache/ab/x.json", "deny"),
    (".env", "deny"),
    ("informe.pdf", "deny"),
    ("src/goes_science_kg/rag.py", None),
    ("data/interim/conceptos/divisiones.json", None),   # las capas de decisión sí se editan
])
def test_guardia_archivos(ruta_archivo, esperado):
    salida = _correr("guardia_archivos.py", {"tool_name": "Edit", "tool_input": {"file_path": str(ruta(ruta_archivo))}})
    assert (salida and salida["hookSpecificOutput"]["permissionDecision"]) == esperado


def test_contexto_de_sesion():
    salida = _correr("contexto_sesion.py", {"hook_event_name": "SessionStart", "source": "startup"})
    texto = salida["hookSpecificOutput"]["additionalContext"]
    assert "Rama:" in texto and "Decisiones de contenido" in texto and "2.°–8.°" in texto


def test_settings_conecta_los_hooks():
    s = json.loads(ruta(".claude/settings.json").read_text(encoding="utf-8"))
    comandos = [h["command"] for grupo in s["hooks"].values() for m in grupo for h in m["hooks"]]
    for script in ("contexto_sesion.py", "guardia_bash.py", "guardia_archivos.py"):
        assert any(script in c for c in comandos) and (HOOKS / script).is_file()
    assert "Read(./.env)" in s["permissions"]["deny"]
