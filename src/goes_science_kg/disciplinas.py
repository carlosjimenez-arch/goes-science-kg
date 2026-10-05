"""Asigna cada tema y cada objetivo a una de las cuatro asignaturas del grafo.

Reglas (specs/05_asignaturas.md, config/asignaturas.yaml):
1. Bachillerato: la asignatura de la malla.                         metodo = «malla»
2. 2.°–9.°: el dominio del objetivo TIMSS 2027 principal (obj1);    metodo = «timss»
   en TIMSS 4.° «Ciencias físicas» decide el área (P1 → química, resto → física).
3. Si obj1 es FUERA: el contenido PISA principal (7.°–9.°).         metodo = «pisa»
4. Si nada aplica: None («por asignar»; lo resuelve la skill grafo-asignar-disciplina).
"""

from __future__ import annotations

from functools import cache

from goes_science_kg.config import cargar
from goes_science_kg.ingesta import legado


@cache
def _dominio_a_asignatura() -> dict[str, str]:
    m = {}
    for asig, a in cargar("asignaturas")["asignaturas"].items():
        for d in a["timss_dominios"]:
            m[d] = asig
    return m


@cache
def _objetivos_timss() -> dict[str, dict]:
    return {o["codigo"]: o for o in legado.catalogo_timss2027()}


def asignatura_de_objetivo(codigo: str) -> str | None:
    """Asignatura de un objetivo TIMSS 2027, TIMSS Advanced o PISA (None si es transversal)."""
    reglas = cargar("asignaturas")["asignacion"]
    if codigo.startswith("TA-"):
        return "fisica"
    if codigo.startswith("PISA-"):
        if codigo.startswith("PISA-F"):
            return reglas["pisa_sistemas_fisicos"].get(codigo, reglas["pisa_sistemas_fisicos_resto"])
        if codigo.startswith("PISA-V"):
            return "biologia"
        if codigo.startswith("PISA-T"):
            return "ciencias_tierra_espacio"
        return None  # procedimental / epistémico: transversal
    o = _objetivos_timss().get(codigo)
    if not o:
        return None
    if o["dominio"] == "Ciencias físicas":
        return reglas["timss4_ciencias_fisicas"].get(o["area_codigo"])
    return _dominio_a_asignatura().get(o["dominio"])


def asignatura_de_tema(asignatura_malla: str, timss: dict | None, pisa: dict | None) -> tuple[str | None, str]:
    """Devuelve (asignatura, metodo)."""
    if asignatura_malla != "ciencias":
        return asignatura_malla, "malla"
    obj1 = (timss or {}).get("obj1", "")
    if obj1 and obj1 not in ("FUERA", "PENDIENTE"):
        if a := asignatura_de_objetivo(obj1):
            return a, "timss"
    cont1 = (pisa or {}).get("cont1", "")
    if cont1 and (a := asignatura_de_objetivo(cont1)):
        return a, "pisa"
    return None, "pendiente"
