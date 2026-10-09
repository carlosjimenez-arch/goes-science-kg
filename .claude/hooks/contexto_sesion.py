"""SessionStart: estado del proyecto al iniciar o retomar una sesión (hechos, no instrucciones).

Rama y cambios sin commit, cuenta de git frente a la de GOES, decisiones de contenido pendientes de confirmar con el
MINED y el estado de las etapas del estudio internacional. Todo local y rápido: sin red ni llamadas a Vertex.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from comun import RAIZ, config  # noqa: E402

DECISIONES = {
    "equivalencias retiradas": "data/interim/conceptos/equivalencias_retiradas.json",
    "prerrequisitos rechazados": "data/interim/prerrequisitos/rechazados.json",
    "divisiones de conceptos": "data/interim/conceptos/divisiones.json",
    "clases corregidas (9.°–11.°)": "data/interim/internacional/revisiones.json",
}


def _git(*args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def _gcloud() -> str | None:
    try:
        r = subprocess.run(["gcloud", "config", "get-value", "account"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _decisiones() -> list[str]:
    lineas = []
    for nombre, rel in DECISIONES.items():
        p = RAIZ / rel
        if not p.exists():
            continue
        datos = json.loads(p.read_text(encoding="utf-8"))
        registros = datos["divisiones"] if isinstance(datos, dict) else datos
        pendientes = sum(not r.get("confirmaciones") and not r.get("observaciones") for r in registros)
        observadas = sum(bool(r.get("observaciones")) for r in registros)
        lineas.append(f"  - {nombre}: {len(registros)} ({pendientes} sin confirmar con el MINED, "
                      f"{observadas} observadas)")
    return lineas


def _etapas() -> list[str]:
    def hay(rel: str) -> bool:
        return (RAIZ / rel).exists()
    pendiente = "lista para ejecutar; espera aprobación del gasto en Vertex"
    return [
        f"  - 9.°–11.° (spec 11): {'construido' if hay('data/grafo/internacional/consenso.json') else 'sin construir'}",
        f"  - 2.°–8.° (spec 12): {'construido' if hay('data/grafo/internacional_2_8/consenso.json') else pendiente}",
    ]


def main() -> None:
    cfg = config()
    correo, rama, gcloud = _git("config", "user.email"), _git("branch", "--show-current"), _gcloud()
    sin_commit = [linea for linea in _git("status", "--short").splitlines() if "Mallas sugeridas" not in linea]
    texto = "\n".join([
        "Estado del proyecto goes-science-kg (hook SessionStart):",
        f"- Rama: {rama or '?'}; archivos con cambios sin commit: {len(sin_commit)}.",
        f"- Cuenta de git: {correo or '(vacía)'} "
        f"({'es la de GOES' if correo == cfg['correo_git'] else 'NO es la de GOES: ' + cfg['correo_git']}).",
        f"- Proyecto de GCP esperado: {cfg['proyecto_gcp']} (credenciales por defecto de gcloud; el .env no se lee).",
        f"- Cuenta activa de gcloud: {gcloud or '(no disponible)'}"
        f"{'' if gcloud in (None, cfg['correo_git']) else ' — NO es la de GOES; Vertex se detendrá antes de gastar'}.",
        "- Decisiones de contenido (capas que ganan sobre la IA):", *_decisiones(),
        "- Estudio internacional:", *_etapas(),
        "- Guardas activas (.claude/hooks): .env y fuentes protegidos, gasto en Vertex con aprobación del usuario,"
        " commit solo con cuenta GOES y pruebas en verde.",
    ])
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": texto}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
