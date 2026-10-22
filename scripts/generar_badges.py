"""Generate honest local quality badges from JUnit and coverage XML reports."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from xml.etree import ElementTree


def badge(etiqueta: str, valor: str, color: str) -> str:
    """Render a small accessible SVG badge without an external service."""
    izquierda, derecha = max(70, len(etiqueta) * 7 + 18), max(65, len(valor) * 7 + 18)
    ancho = izquierda + derecha
    titulo = escape(f"{etiqueta}: {valor}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{ancho}" height="24" role="img" aria-label="{titulo}">'
        f"<title>{titulo}</title>"
        f'<rect width="{ancho}" height="24" rx="5" fill="#1c1e4d"/>'
        f'<path d="M{izquierda} 0h{derecha - 5}q5 0 5 5v14q0 5-5 5h-{derecha - 5}z" fill="{color}"/>'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,DejaVu Sans,sans-serif" font-size="11">'
        f'<text x="{izquierda / 2}" y="16">{escape(etiqueta)}</text>'
        f'<text x="{izquierda + derecha / 2}" y="16">{escape(valor)}</text></g></svg>\n'
    )


def huella_codigo(raiz: Path) -> str:
    """Hash measured source, test, script, and dependency files deterministically."""
    digest = hashlib.sha256()
    archivos = sorted(
        [
            p
            for carpeta in ("src", "tests", "scripts", ".claude/hooks")
            for p in (raiz / carpeta).rglob("*")
            if p.suffix in {".py", ".js", ".cjs", ".css", ".html"}
        ]
        + [raiz / "pyproject.toml", raiz / "uv.lock"]
    )
    for archivo in archivos:
        digest.update(archivo.relative_to(raiz).as_posix().encode() + b"\0" + archivo.read_bytes() + b"\0")
    return digest.hexdigest()


def generar(junit: Path, cobertura: Path, destino: Path, raiz: Path) -> dict:
    """Generate badges and preserve their measured denominator, date, and code hash."""
    suites = ElementTree.parse(junit).getroot()
    if suites.tag == "testsuite":
        suites = [suites]
    else:
        suites = list(suites.findall("testsuite"))
    if not suites:
        raise ValueError("El informe JUnit no contiene suites")
    totales = {k: sum(int(s.get(k, "0")) for s in suites) for k in ("tests", "failures", "errors", "skipped")}
    ejecutadas = totales["tests"] - totales["skipped"]
    aprobadas = ejecutadas - totales["failures"] - totales["errors"]
    if ejecutadas <= 0 or aprobadas < 0:
        raise ValueError("El informe no contiene un denominador válido de pruebas ejecutadas")
    porcentaje = aprobadas * 100 / ejecutadas
    medicion = ElementTree.parse(cobertura).getroot()
    cubiertas = int(medicion.attrib["lines-covered"])
    lineas = int(medicion.attrib["lines-valid"])
    if not 0 <= cubiertas <= lineas or lineas == 0:
        raise ValueError("El informe no contiene un denominador válido de cobertura")
    cobertura_pct = cubiertas * 100 / lineas
    informe = {
        "fecha_utc": datetime.now(UTC).isoformat(),
        "commit_base": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=raiz, text=True).strip(),
        "huella_codigo_sha256": huella_codigo(raiz),
        "pruebas": totales | {"aprobadas": aprobadas, "ejecutadas": ejecutadas, "porcentaje_aprobado": porcentaje},
        "cobertura": {"lineas_cubiertas": cubiertas, "lineas_totales": lineas, "porcentaje": cobertura_pct},
        "alcance": "Medición local completa con corpus restaurado; no acredita resultados de CI ni eficacia educativa.",
    }
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, etiqueta, valor, color in (
        ("tests", "tests locales", f"{aprobadas}/{ejecutadas}", "#14855b" if porcentaje == 100 else "#b42318"),
        ("pass-rate", "aprobación", f"{porcentaje:.2f}%", "#14855b" if porcentaje == 100 else "#b42318"),
        ("coverage", "cobertura", f"{cobertura_pct:.2f}%", "#3565fc"),
    ):
        (destino / f"{nombre}.svg").write_text(badge(etiqueta, valor, color), encoding="utf-8")
    (destino / "medicion.json").write_text(json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return informe


def main() -> None:
    """Build badges only from existing measurement reports."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--junit", type=Path, required=True)
    parser.add_argument("--cobertura", type=Path, required=True)
    parser.add_argument("--salida", type=Path, default=Path("docs/badges"))
    args = parser.parse_args()
    print(json.dumps(generar(args.junit, args.cobertura, args.salida, Path(__file__).resolve().parents[1])))


if __name__ == "__main__":
    main()
