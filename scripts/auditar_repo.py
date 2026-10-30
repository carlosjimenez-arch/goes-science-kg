"""Inventory Python dependencies and documentation without deleting artifacts."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from urllib.parse import unquote


class AuditorRepositorio:
    """Inspect tracked source files and distinguish private assets from broken links."""

    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz.resolve()
        nombres = subprocess.check_output(["git", "ls-files", "-z"], cwd=self.raiz).decode().split("\0")
        nuevos = (
            subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "-z"], cwd=self.raiz)
            .decode()
            .split("\0")
        )
        self.rutas = sorted({n for n in (*nombres, *nuevos) if n and (self.raiz / n).is_file()})
        self.versionadas = set(nombres)

    def inspeccionar(self) -> dict:
        """Return deterministic counts, import consumers, and unresolved local links.

        Missing static consumers are review candidates, not proof of dead code:
        CLI entry points, package exports, templates, and dynamic imports matter.
        """
        modulos, consumidores, documentacion = {}, {}, []
        conteos: Counter = Counter()
        for nombre in self.rutas:
            archivo = self.raiz / nombre
            if archivo.suffix == ".py":
                arbol = ast.parse(archivo.read_text(encoding="utf-8"), filename=nombre)
                for nodo in ast.walk(arbol):
                    if isinstance(nodo, ast.ImportFrom) and nodo.module:
                        for modulo in (nodo.module, *(nodo.module + "." + a.name for a in nodo.names)):
                            consumidores.setdefault(modulo, set()).add(nombre)
                    elif isinstance(nodo, ast.Import):
                        for alias in nodo.names:
                            consumidores.setdefault(alias.name, set()).add(nombre)
                if nombre.startswith("src/"):
                    modulo = nombre[4:-3].replace("/", ".").removesuffix(".__init__")
                    modulos[modulo] = nombre
                    conteos["modulos_python"] += 1
                    conteos["lineas_python"] += len(archivo.read_text().splitlines())
                    for nodo in ast.walk(arbol):
                        if isinstance(nodo, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                            tipo = type(nodo).__name__
                            conteos[tipo] += 1
                            if ast.get_docstring(nodo):
                                conteos[tipo + "_documentados"] += 1
            elif archivo.suffix == ".md":
                enlaces = []
                for destino in re.findall(r"\[[^\]]*\]\(([^)]+)\)", archivo.read_text(encoding="utf-8")):
                    ruta = unquote(destino.strip("<>").split("#", 1)[0])
                    if not ruta or re.match(r"^[a-zA-Z][\w+.-]*:", ruta):
                        continue
                    objetivo = (archivo.parent / ruta).resolve()
                    if not objetivo.is_relative_to(self.raiz):
                        estado = "fuera_del_repositorio"
                    elif objetivo.exists():
                        relativa = objetivo.relative_to(self.raiz).as_posix()
                        if relativa in self.versionadas:
                            estado = "versionado"
                        elif objetivo.is_dir() and any(n.startswith(relativa + "/") for n in self.versionadas):
                            estado = "directorio_versionado"
                        else:
                            estado = "activo_local"
                    else:
                        estado = "ausente"
                    enlaces.append({"destino": ruta, "estado": estado})
                documentacion.append({"archivo": nombre, "enlaces": enlaces})
        dependencias = {
            nombre: sorted(
                {c for m, cs in consumidores.items() if m == modulo or m.startswith(modulo + ".") for c in cs}
            )
            for modulo, nombre in sorted(modulos.items())
        }
        return {
            "archivos_inspeccionados": len(self.rutas),
            "conteos": dict(sorted(conteos.items())),
            "consumidores_estaticos": dependencias,
            "candidatos_sin_consumidor_estatico": [p for p, consumidores in dependencias.items() if not consumidores],
            "documentacion": documentacion,
            "criterio": (
                "La ausencia de imports no autoriza una eliminación; comprobar entradas públicas y uso dinámico."
            ),
        }


def main() -> None:
    """Write the requested audit report without modifying inspected source files."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raiz", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    informe = AuditorRepositorio(args.raiz).inspeccionar()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(informe["conteos"], ensure_ascii=False))


if __name__ == "__main__":
    main()
