"""PreToolUse (Bash): reglas del proyecto que antes dependían de recordarlas (CLAUDE.md y specs 07, 11, 12).

- deny: leer o copiar .env; escribir en data/fuentes/ o reportes/ desde la terminal; commit con una cuenta que no es la
  de GOES; commit con pruebas o lint en rojo; push forzado a main o a un remoto que no es el alias de GOES.
- ask: cualquier comando que gaste en Vertex (--confirmar, congelar-catalogo, make internacional-ia CONFIRMAR=…).
- sin salida: todo lo demás sigue el flujo normal de permisos.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from comun import RAIZ, config, decidir, entrada  # noqa: E402

LECTORES = (r"(cat|less|more|head|tail|grep|rg|egrep|sed|awk|bat|strings|xxd|od|cp|mv|scp|rsync|source|base64|tee|"
            r"curl|nl)")
ENV = r"(?<![\w.-])(\./)?\.env(?![\w.-])"


def _salida(cmd: list[str], segundos: int) -> tuple[int, str]:
    r = subprocess.run(cmd, cwd=RAIZ, capture_output=True, text=True, timeout=segundos)
    return r.returncode, (r.stdout + r.stderr).strip()


def revisar(comando: str) -> None:
    cfg = config()
    # 1. Secretos: el .env no se lee ni se imprime; el código lo carga solo.
    if re.search(ENV, comando) and (re.search(rf"\b{LECTORES}\b", comando) or re.search(r"(^|[;&|]\s*)\.\s", comando)
                                    or re.search(r"open\(|read_text|read_bytes|dotenv_values", comando)):
        decidir("deny", "El .env no se lee ni se imprime (CLAUDE.md y pedido del usuario): el código lo carga solo.")
    # 2. Fuentes y trabajo previo: solo lectura.
    for ruta in cfg["rutas_solo_lectura"]:
        r = re.escape(ruta)
        if (re.search(rf"\b(rm|mv|truncate|tee|sed\s+-i\S*|perl\s+-\S*i)\b[^;&|]*{r}", comando)
                or re.search(rf">>?\s*\S*{r}", comando)):
            decidir("deny", f"{ruta} es de solo lectura (CLAUDE.md): no se modifica.")
    # 3. Gasto en Vertex: lo aprueba el usuario.
    if (re.search(r"gskg\s+internacional\b.*\b(extraer|etiquetar)\b.*--confirmar", comando)
            or re.search(r"gskg\s+internacional\b.*\bcongelar-catalogo\b", comando)
            or re.search(r"make\s+internacional-ia\b.*CONFIRMAR=\S+", comando)):
        decidir("ask", "Este comando gasta llamadas a Vertex (proyecto GOES). Antes corre sin --confirmar para ver "
                       "el costo.")
    # 4. Commit: cuenta GOES y pruebas en verde.
    if re.search(r"\bgit\b(\s+-\S+(\s+\S+)?)*\s+commit\b", comando):
        _, correo = _salida(["git", "config", "user.email"], 10)
        if correo != cfg["correo_git"]:
            decidir("deny", f"git usa la cuenta {correo or '(vacía)'}; este repo exige {cfg['correo_git']} (GOES).")
        if os.environ.get("GSKG_HARNESS_SIN_PRUEBAS") != "1":   # solo para las pruebas del propio harness
            lint = ["uv", "run", "ruff", "check", "src", "tests", ".claude/hooks"]
            for nombre, cmd, segundos in (("ruff", lint, 120),
                                          ("pytest", ["uv", "run", "pytest", "-q", "-x"], 600)):
                codigo, texto = _salida(cmd, segundos)
                if codigo != 0:
                    ultimas = "\n".join(texto.splitlines()[-15:])
                    decidir("deny", f"{nombre} en rojo: no se hace commit (CLAUDE.md).\n{ultimas}")
    # 5. Push: solo al remoto de GOES y nunca forzado sobre main.
    if re.search(r"\bgit\b(\s+-\S+(\s+\S+)?)*\s+push\b", comando):
        if re.search(r"(\s-f\b|--force\b|--force-with-lease\b)", comando) and re.search(r"\b(main|master)\b", comando):
            decidir("deny", "No se fuerza un push sobre main.")
        _, url = _salida(["git", "remote", "get-url", "origin"], 10)
        if cfg["alias_remoto"] not in url:
            decidir("deny", f"El remoto origin ({url}) no usa el alias SSH {cfg['alias_remoto']} de la cuenta GOES.")


if __name__ == "__main__":
    datos = entrada()
    if datos.get("tool_name") == "Bash":
        revisar(datos.get("tool_input", {}).get("command", ""))
