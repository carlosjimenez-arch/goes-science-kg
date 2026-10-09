"""PreToolUse (Edit, Write, MultiEdit, NotebookEdit): archivos que no se editan a mano.

- deny: .env; data/fuentes/ y reportes/ (solo lectura); PDF; salidas generadas (data/grafo/, caché de Vertex), que se
  regeneran con gskg: hay que cambiar el código o la capa de decisión, no el resultado.
Las reglas permissions.deny de .claude/settings.json cubren lo mismo para .env y las fuentes; este hook además explica
el motivo y cubre las salidas generadas.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from comun import config, decidir, entrada, relativa  # noqa: E402


def revisar(ruta: str) -> None:
    cfg, rel = config(), relativa(ruta)
    nombre = rel.rsplit("/", 1)[-1]
    if nombre == ".env" or nombre.startswith(".env."):
        decidir("deny", "El .env no se edita ni se lee desde la sesión: lo administra el usuario.")
    if rel.lower().endswith(".pdf"):
        decidir("deny", "Los PDF son fuentes oficiales: no se modifican (CLAUDE.md).")
    for prefijo in cfg["rutas_solo_lectura"]:
        if rel.startswith(prefijo):
            decidir("deny", f"{prefijo} es de solo lectura (CLAUDE.md): no se modifica.")
    for prefijo in cfg["rutas_generadas"]:
        if rel.startswith(prefijo):
            decidir("deny", f"{prefijo} se genera con gskg (salidas deterministas): cambia el código o la capa de "
                            "decisión y regenera, en lugar de editar el resultado.")


if __name__ == "__main__":
    datos = entrada()
    entrada_herramienta = datos.get("tool_input", {})
    ruta = entrada_herramienta.get("file_path") or entrada_herramienta.get("notebook_path")
    if ruta:
        revisar(ruta)
