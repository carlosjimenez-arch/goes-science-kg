"""Contraste de la malla V2 (9.°–11.°) con el consenso internacional (spec 11).

Clasificación de cada concepto de la asignatura. Consenso: ≥ 50 % de los países con núcleo común y al menos
5 países (spec 11: «≥ 5 de 9»; Hong Kong no tiene núcleo, así que son 5 de 8: una mayoría, no un empate).
- faltante: el consenso lo tiene en el núcleo hasta el grado g y El Salvador no lo enseña en 2.°–11.°.
- no_retomado: El Salvador solo lo enseña antes de 9.° y al menos 5 países lo enseñan en su núcleo de 9.°–11.°
  (hueco de profundización en Bachillerato).
- tardio: El Salvador lo introduce en 9.°–11.°, ≥ 2 grados después de g.
- solo_especializacion: El Salvador lo introduce en 9.°–11.° (obligatorio), pero en los países solo aparece en
  cursos electivos: a lo sumo 1 país lo enseña de forma sólida en su núcleo (como principal en un objetivo o como
  secundario en dos, contando la secundaria baja) y al menos 3 lo tienen en especialización. Una etiqueta secundaria
  suelta no basta (revisión manual: 3 de 5 casos así eran falsos); exigir que sea principal tampoco, porque el
  etiquetado suele elegir un concepto vecino más general (p. ej. inmunidad adaptativa en JP 生物基礎).
- adelantado: El Salvador lo introduce en 9.°–11.°, ≥ 1,5 grados antes que la mediana del núcleo de los países.
- alineado: El Salvador lo introduce en 9.°–11.° y el momento coincide (± 1,5 grados).
- retomado: El Salvador lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.°.
- previo: El Salvador solo lo enseña antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°.
- sin_referente: El Salvador lo enseña en 9.°–11.° y ningún país de los 9 lo tiene en 9.°–11. ni antes.
El momento (adelantado, tardío) solo se juzga para lo que El Salvador introduce en 9.°–11.°: los datos de los
países son de 9.°–11.° (más el antecedente de ENG, AU y JP), así que no permiten fechar la primaria salvadoreña.
Secuencia: prerrequisito p → c donde El Salvador enseña p después que c.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.internacional import etiquetar
from goes_science_kg.internacional.consenso import DIR_GRAFO, GRADOS, con_equivalentes, ensenados, paises

UMBRAL = 0.5
MIN_PAISES = 5
MIN_ESPECIALIZACION = 3
TOLERANCIA = 1.5
ASIGNATURAS = ("fisica", "quimica", "biologia", "tierra_espacio")


def _sv() -> tuple[dict[str, list[tuple[int, str]]], dict[str, dict]]:
    """Concepto → [(grado, id de tema)] de la malla V2, de 2.° a 11.°, y la ficha de cada tema.

    Unión de todos los etiquetados de la V2 (vocabulario de la asignatura y completo) más las equivalencias entre
    asignaturas: un tema enseña c si algún etiquetado lo encuentra."""
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t.dict() for t in extraer("mallas_v2")}
    por: dict[str, set[tuple[int, str]]] = defaultdict(set)
    for f in sorted(ruta(etiquetar.DIR).glob("malla_v2_*.json")):
        for tid, e in json.loads(f.read_text(encoding="utf-8")).items():
            if tid in temas:
                for c in con_equivalentes(ensenados(e)):
                    por[c].add((temas[tid]["grado"], tid))
    return {c: sorted(v) for c, v in por.items()}, temas


def clase_de(sv_primer: int | None, sv_9_11: int | None, g_cons: int | None, n_nucleo_9_11: int,
             mediana_nucleo: float | None, n_nucleo_foco: int, n_esp: int) -> str:
    """Regla del docstring del módulo. `g_cons`: primer grado en que el núcleo alcanza el consenso;
    `sv_9_11`: primer grado de la V2 dentro de 9.°–11.° (None si no está en esos grados)."""
    if sv_primer is None:
        return "faltante" if g_cons is not None else "no_aplica"
    if sv_9_11 is None:
        return "no_retomado" if n_nucleo_9_11 >= MIN_PAISES else "previo"
    if sv_primer < GRADOS[0]:
        return "retomado"
    if g_cons is not None and sv_primer >= g_cons + 2:
        return "tardio"
    if n_nucleo_foco <= 1 and n_esp >= MIN_ESPECIALIZACION:
        return "solo_especializacion"
    if mediana_nucleo is not None and sv_primer <= mediana_nucleo - TOLERANCIA:
        return "adelantado"
    return "alineado"


def clasificar() -> dict:
    voc = conceptos.vocabulario()
    cons = json.loads((ruta(DIR_GRAFO) / "consenso.json").read_text(encoding="utf-8"))
    sv, temas = _sv()
    filas = []
    en_consenso = set()
    for c in cons["conceptos"]:
        en_consenso.add(c["concepto"])
        if c["asignatura"] not in ASIGNATURAS:
            continue
        grados_sv = sv.get(c["concepto"], [])
        sv_primer = grados_sv[0][0] if grados_sv else None
        sv_9_11 = next((g for g, _ in grados_sv if g >= GRADOS[0]), None)
        g_cons = next((g for g in GRADOS if c["proporcion_nucleo_hasta_grado"][str(g)] >= UMBRAL
                       and len(c["nucleo_hasta_grado"][str(g)]) >= MIN_PAISES), None)
        med = c["mediana_primer_grado_nucleo"]
        n_esp = sum(f["en_especializacion"] for f in c["paises"].values())
        clase = clase_de(sv_primer, sv_9_11, g_cons, c["n_nucleo_9_11"], med, c["n_nucleo_foco"], n_esp)
        filas.append({**{k: c[k] for k in ("concepto", "nombre", "asignatura", "n_paises", "n_nucleo",
                                           "n_solo_especializacion", "n_nucleo_9_11", "n_nucleo_foco",
                                           "mediana_primer_grado_nucleo")},
                      "n_especializacion": n_esp, "grado_consenso": g_cons,
                      "proporcion_nucleo": c["proporcion_nucleo_hasta_grado"],
                      "sv_primer_grado": sv_primer, "sv_9_11": sv_9_11,
                      "sv_temas": [t for _, t in grados_sv][:8],
                      "paises": c["paises"], "clase": clase})
    # Lo que El Salvador enseña en 9.°–11.° sin ningún referente.
    for c, gs in sorted(sv.items()):
        if c in en_consenso or c not in voc or not any(g >= 9 for g, _ in gs):
            continue
        asig = {"ciencias_tierra_espacio": "tierra_espacio"}.get(voc[c]["asignatura"], voc[c]["asignatura"])
        filas.append({"concepto": c, "nombre": voc[c]["nombre"], "asignatura": asig, "n_paises": 0, "n_nucleo": 0,
                      "n_solo_especializacion": 0, "n_nucleo_9_11": 0, "n_nucleo_foco": 0,
                      "mediana_primer_grado_nucleo": None,
                      "n_especializacion": 0, "sv_9_11": min(g for g, _ in gs if g >= GRADOS[0]),
                      "grado_consenso": None, "proporcion_nucleo": {}, "sv_primer_grado": gs[0][0],
                      "sv_temas": [t for _, t in gs][:8], "paises": {}, "clase": "sin_referente"})
    revisiones = revisiones_expertas()
    for f in filas:
        if rv := revisiones.get(f["concepto"]):
            f["clase_ia"], f["clase"] = f["clase"], rv["clase"]
            f["revision"] = {"justificacion": rv["justificacion"], "revisado_por": rv["revisado_por"]}
    secuencia = _secuencia(sv, voc)
    return {"filas": sorted(filas, key=lambda f: (f["asignatura"], f["clase"], f["concepto"])),
            "secuencia": secuencia, "temas": temas, "paises_con_nucleo": cons["paises_con_nucleo_por_grado"]}


def revisiones_expertas() -> dict[str, dict]:
    """Clases decididas en revisión experta (data/interim/internacional/revisiones.json). Ganan sobre la regla
    automática, como las decisiones humanas del grafo principal; cada una trae su evidencia y quién la revisó."""
    p = ruta("data/interim/internacional/revisiones.json")
    return {r["concepto"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def _secuencia(sv: dict, voc: dict) -> list[dict]:
    from goes_science_kg.prerrequisitos import cargar_prerrequisitos

    salida = []
    for a in cargar_prerrequisitos():
        p, c = a["origen"], a["destino"]
        if p in sv and c in sv and sv[c][0][0] >= 9 and sv[p][0][0] > sv[c][0][0]:
            salida.append({"prerrequisito": p, "nombre_prerrequisito": voc[p]["nombre"], "concepto": c,
                           "nombre_concepto": voc[c]["nombre"], "grado_prerrequisito": sv[p][0][0],
                           "grado_concepto": sv[c][0][0], "confianza": a.get("confianza"),
                           "tema_concepto": sv[c][0][1], "tema_prerrequisito": sv[p][0][1]})
    return sorted(salida, key=lambda s: (s["grado_concepto"], s["concepto"]))


def resumen(r: dict) -> dict:
    return {a: dict(Counter(f["clase"] for f in r["filas"] if f["asignatura"] == a)) for a in ASIGNATURAS}


def evidencia_paises(fila: dict, max_paises: int = 9) -> str:
    partes = []
    for p in paises():
        f = fila["paises"].get(p)
        if not f:
            continue
        g = f["primer_grado_nucleo"]
        partes.append(f"{p} {g:g}" if g is not None else f"{p} esp.")
    return ", ".join(partes[:max_paises])
