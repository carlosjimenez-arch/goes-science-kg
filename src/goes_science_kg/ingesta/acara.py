"""Catálogo del pivote de Bachillerato para Biología y Química: Australian Curriculum,
Senior Secondary (v8.4), cursos Biology y Chemistry, unidades 1–4 (ACARA, licencia CC BY 4.0).

Por qué este pivote: specs/03_fuentes_y_referentes.md («Pivote de Bachillerato»).

Fuente: páginas HTML oficiales guardadas en data/fuentes/externos/bachillerato/ (ACARA no publica
un PDF por curso; el HTML guardado con su sha256 es el documento). No hay páginas: el localizador
de cada objetivo es su código oficial de descripción de contenido (ACSBL001, ACSCH001…).

Dos pasos:
1. `parsear()` lee el HTML → objetivos en inglés (data/interim/acara/<asignatura>_en.json).
2. `catalogo()` une esos objetivos con la paráfrasis en español
   (data/referencia/acara_senior_es.json, la escribe un subagente) → data/referencia/catalogo_acara_senior.json.
"""

from __future__ import annotations

import html
import json
import re

from goes_science_kg.config import ruta

DIR = "data/fuentes/externos/bachillerato"
CURSOS = {
    "biologia": {"prefijo": "ACSBL", "archivos": ["AU_SeniorSecondary_Biology_v8.4_U1-3.html",
                                                  "AU_SeniorSecondary_Biology_v8.4_U4.html"]},
    "quimica": {"prefijo": "ACSCH", "archivos": ["AU_SeniorSecondary_Chemistry_v8.4_U1-3.html",
                                                 "AU_SeniorSecondary_Chemistry_v8.4_U4.html"]},
}
ES = "data/referencia/acara_senior_es.json"
SALIDA = "data/referencia/catalogo_acara_senior.json"

_TOKENS = re.compile(
    r'<h3 id="ContentDescriptions[^"]*">(?P<h3>.*?)</h3>'
    r'|<h4>(?P<h4>.*?)</h4>'
    r'|<section id="(?P<cod>ACS(?:BL|CH)\d+)"[^>]*>(?P<sec>.*?)</section>',
    re.S,
)


def _texto(fragmento: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", fragmento))).strip()


def _unidades(h: str) -> dict[int, str]:
    return {int(n): t.strip() for n, t in re.findall(r"Unit ([1-4]): ([^<]+?) Content Descriptions", h)}


def parsear(asignatura: str) -> list[dict]:
    """Objetivos en inglés de `asignatura` leídos del HTML de ACARA (unidad, eje, tema, texto y código), ordenados
    por código. No escribe nada."""
    curso = CURSOS[asignatura]
    objetivos: dict[str, dict] = {}
    for archivo in curso["archivos"]:
        h = (ruta(DIR) / archivo).read_text(encoding="utf-8")
        titulos = _unidades(h)
        unidad, eje, tema = None, None, None
        for m in _TOKENS.finditer(h):
            if m["h3"]:
                unidad = int(re.search(r"Unit (\d)", m["h3"]).group(1))
            elif m["h4"]:
                t = _texto(m["h4"])
                if u := re.search(r"Science Inquiry Skills \(\w+ Unit (\d)\)", t):
                    unidad, eje, tema = int(u.group(1)), "indagacion", None
                elif t.startswith("Science as a Human Endeavour"):
                    eje, tema = "naturaleza_ciencia", None
                elif t == "Science Understanding":
                    eje, tema = "contenido", None
                else:
                    tema = t
            elif m["cod"] and m["cod"].startswith(curso["prefijo"]):
                texto = re.sub(r"\s*\(" + m["cod"] + r"\)\s*$", "", _texto(m["sec"]))
                objetivos.setdefault(m["cod"], {
                    "codigo": m["cod"], "marco": "AUSS", "asignatura": asignatura, "unidad": unidad,
                    "unidad_titulo_en": titulos.get(unidad), "eje": eje, "tema_en": tema,
                    "texto_en": texto, "documento": archivo, "localizador": m["cod"],
                })
    return sorted(objetivos.values(), key=lambda o: o["codigo"])


def catalogo() -> list[dict]:
    """Une el inglés con la paráfrasis en español. Falla si falta alguna traducción."""
    es = json.loads(ruta(ES).read_text(encoding="utf-8"))
    salida, faltan = [], []
    for asignatura in CURSOS:
        for o in parsear(asignatura):
            t = es.get(o["codigo"])
            if not t:
                faltan.append(o["codigo"])
                continue
            salida.append({**o, "objetivo": t["objetivo"], "tema": t.get("tema"),
                           "unidad_titulo": t.get("unidad_titulo")})
    if faltan:
        raise ValueError(f"Faltan {len(faltan)} paráfrasis en {ES}: {faltan[:5]}…")
    return salida


def escribir_catalogo() -> int:
    """Escribe el catálogo bilingüe en data/referencia/catalogo_acara_senior.json. Devuelve cuántos objetivos tiene."""
    cat = catalogo()
    ruta(SALIDA).parent.mkdir(parents=True, exist_ok=True)
    ruta(SALIDA).write_text(json.dumps(cat, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return len(cat)
