"""Contraste de la malla V2 con el consenso internacional, por tramo de grados T (specs 11 y 12).

Clasificación de cada concepto de la asignatura. Consenso: ≥ 50 % de los países con núcleo común y al menos
5 países (spec 11: «≥ 5 de 9»; Hong Kong no tiene núcleo en 9.°–11.°, así que son 5 de 8: una mayoría, no un empate).
- faltante: el consenso lo tiene en el núcleo hasta el grado g y El Salvador no lo enseña en 2.°–11.°.
- tardio: El Salvador lo introduce ≥ 2 grados después de g, dentro de T o después de T.
- posterior: El Salvador lo enseña solo después de T y el núcleo internacional no lo exige dentro de T.
- no_retomado: El Salvador solo lo enseña antes de T y al menos 5 países lo enseñan en su núcleo dentro de T
  (hueco de profundización).
- solo_especializacion: El Salvador lo introduce en T (obligatorio), pero en los países solo aparece en cursos
  electivos: a lo sumo 1 país lo enseña de forma sólida en su núcleo (como principal en un objetivo o como
  secundario en dos, contando la secundaria baja) y al menos 3 lo tienen en especialización. Una etiqueta secundaria
  suelta no basta (revisión manual: 3 de 5 casos así eran falsos); exigir que sea principal tampoco, porque el
  etiquetado suele elegir un concepto vecino más general (p. ej. inmunidad adaptativa en JP 生物基礎).
- adelantado: El Salvador lo introduce en T, ≥ 1,5 grados antes que la mediana del núcleo de los países.
- alineado: El Salvador lo introduce en T y el momento coincide (± 1,5 grados).
- retomado: El Salvador lo introduce antes de T y lo vuelve a trabajar en T.
- previo: El Salvador solo lo enseña antes de T y el núcleo internacional no lo exige en T.
- sin_referente: El Salvador lo enseña en T y ningún país lo tiene en T ni antes.
El momento (adelantado, tardío) solo se juzga para lo que El Salvador introduce en T: los datos de los países son
del tramo (más su antecedente), así que no permiten fechar lo que El Salvador enseña antes. En 2.°–8.° no hay nada
antes del tramo ni cursos electivos: «retomado», «previo», «no_retomado» y «solo_especializacion» no aparecen.
Secuencia: prerrequisito p → c donde El Salvador enseña p después que c (c introducido en T).

Doble lectura (tramos con `lectura_doble`: 2.°–8.°, spec 12). La verificación de 2.°–8.° encontró 46 % de falsos,
casi todos por etiquetas sueltas de la V2 o de los países. Por eso la regla se aplica dos veces:
- lectura amplia: la V2 enseña c en un tema si CUALQUIER etiquetado lo encuentra (los de Vertex con cualquier
  confianza y el del grafo principal) o si el texto de CUALQUIER columna de su fila lo nombra (evidencia, habilidad
  TIMSS, microhabilidades, indicador avanzado: la verificación encontró ahí la fricción de 3.° y la conservación de la
  masa de 7.°); los países, solo con presencia sólida (principal en un objetivo o secundario en dos). Es la lectura
  más favorable a la V2.
- lectura estricta: la V2 solo con presencia sólida (2 puntos acumulados: principal en algún etiquetado, o dos
  etiquetados que coinciden, o secundario en dos temas); los países con la regla de presencia. La más desfavorable.
Una clase se afirma si las dos lecturas dan la misma; si no, el concepto queda «incierto» y va a revisión con las
dos clases. Además: la mediana de «adelantado» exige ≥ 3 países (con menos, «sin referente»); las relaciones «parte
de» cuentan en los dos lados; una secuencia exige el concepto como principal en un tema (no secundarias sueltas) y el
prerrequisito ausente también del texto; un «tardío» trae una alerta si los objetivos de los países que fechan el
consenso también enseñan un concepto vecino que la V2 da antes.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.ingesta.mallas import extraer, textos_completos
from goes_science_kg.internacional import etiquetar, tramo
from goes_science_kg.internacional.consenso import (
    ampliar,
    con_equivalentes,
    ensenados,
    objetivos,
    paises,
    primer_grado_solido,
)
from goes_science_kg.prerrequisitos import cargar_prerrequisitos

UMBRAL = 0.5
MIN_PAISES = 5
MIN_ESPECIALIZACION = 3
TOLERANCIA = 1.5
MIN_PAISES_MOMENTO = 3   # doble lectura: con menos países en el núcleo, la mediana no fecha nada
ASIGNATURAS = ("fisica", "quimica", "biologia", "tierra_espacio")


def _sv() -> tuple[dict[str, list[tuple[int, str]]], dict[str, dict]]:
    """Concepto → [(grado, id de tema)] de la malla V2, de 2.° a 11.°, y la ficha de cada tema.

    Unión de todos los etiquetados de la V2 (vocabulario de la asignatura y completo) más las equivalencias entre
    asignaturas: un tema enseña c si algún etiquetado lo encuentra."""

    temas = {t.id: t.dict() for t in extraer()}
    por: dict[str, set[tuple[int, str]]] = defaultdict(set)
    for _, etiquetas in etiquetar.leer_etiquetados("malla_v2_"):
        for tid, e in etiquetas.items():
            if tid in temas:
                for c in con_equivalentes(ensenados(e)):
                    por[c].add((temas[tid]["grado"], tid))
    return {c: sorted(v) for c, v in por.items()}, temas


CLASES_DE_AUSENCIA = ("no_retomado", "faltante")
# Clases que no afirman un desajuste. Si las dos lecturas difieren pero ambas están aquí, la diferencia es descriptiva
# (dónde empieza la V2) y no hay hallazgo que proteger: gana la lectura estricta, que es donde la V2 lo enseña con
# presencia sólida (2026-10-13, al pasar 9.°–11.° a la doble lectura). Si una lectura afirma un desajuste, «incierto».
SIN_DESAJUSTE = frozenset({"alineado", "retomado", "previo", "posterior", "no_aplica"})


def ausencias_con_texto(filas: list[dict], voc: dict, temas: dict[str, dict], grados: tuple[int, ...]) -> list[str]:
    """Salvaguarda del método v1 (revisión crítica del bucle, 2026-10-13): una clase de ausencia («no retomado»:
    la V2 no lo retoma en el tramo; «faltante»: no lo enseña) solo se afirma si el concepto tampoco aparece como frase
    en el texto completo de la fila (microhabilidades, valores, indicador avanzado). Si aparece, la clase pasa a
    «incierto» con la alerta de los temas donde aparece, para revisión. Las 4 «no retomado» de 9.°–11.° eran falsas o
    parciales por eso. Modifica `filas` y devuelve los conceptos afectados."""
    if not any(f["clase"] in CLASES_DE_AUSENCIA for f in filas):
        return []
    texto = presencia_por_texto(voc, textos_completos())
    afectados = []
    for f in filas:
        if f["clase"] not in CLASES_DE_AUSENCIA:
            continue
        donde = sorted(tid for tid in texto.get(f["concepto"], ()) if tid in temas
                       and (f["clase"] == "faltante" or temas[tid]["grado"] in grados))
        if donde:
            f["clase_v1"], f["clase"] = f["clase"], "incierto"
            f.setdefault("alertas", {})["ausencia_con_texto"] = donde[:6]
            afectados.append(f["concepto"])
    return afectados


def clase_de(sv_primer: int | None, sv_en_tramo: int | None, g_cons: int | None, n_nucleo_en_tramo: int,
             mediana_nucleo: float | None, n_nucleo_foco: int, n_esp: int,
             grados: tuple[int, ...] | None = None, n_mediana: int | None = None) -> str:
    """Regla del docstring del módulo. `g_cons`: primer grado en que el núcleo alcanza el consenso;
    `sv_en_tramo`: primer grado de la V2 dentro del tramo (None si no está en él); `grados`: los del tramo
    (por defecto, el activo); `n_mediana`: países detrás de la mediana (con doble lectura; < 3 → sin referente)."""
    grados = grados or tramo.actual().grados
    if sv_primer is None:
        return "faltante" if g_cons is not None else "no_aplica"
    if sv_en_tramo is None:
        if sv_primer > grados[-1]:          # la V2 lo enseña solo después del tramo
            if g_cons is None:
                return "posterior"
            # «tardío» exige ≥ 2 grados también aquí (docstring y spec 12); a menos distancia el momento coincide.
            return "tardio" if sv_primer >= g_cons + 2 else "alineado"
        return "no_retomado" if n_nucleo_en_tramo >= MIN_PAISES else "previo"
    if sv_primer < grados[0]:
        return "retomado"
    if g_cons is not None and sv_primer >= g_cons + 2:
        return "tardio"
    if n_nucleo_foco <= 1 and n_esp >= MIN_ESPECIALIZACION:
        return "solo_especializacion"
    if n_mediana is not None and n_mediana < MIN_PAISES_MOMENTO:
        return "sin_referente"
    if mediana_nucleo is not None and sv_primer <= mediana_nucleo - TOLERANCIA:
        return "adelantado"
    return "alineado"


def clasificar() -> dict:
    """Clasifica cada concepto del consenso del tramo activo (y lo que la V2 enseña en el tramo sin referente) con la
    regla del módulo; las revisiones expertas ganan. Devuelve filas, secuencia, temas y núcleo por grado."""
    if tramo.actual().lectura_doble:
        return _clasificar_doble()
    voc, t = conceptos.vocabulario(), tramo.actual()
    cons = json.loads((ruta(t.grafo) / "consenso.json").read_text(encoding="utf-8"))
    sv, temas = _sv()
    filas = []
    en_consenso = set()
    for c in cons["conceptos"]:
        en_consenso.add(c["concepto"])
        if c["asignatura"] not in ASIGNATURAS:
            continue
        grados_sv = sv.get(c["concepto"], [])
        sv_primer = grados_sv[0][0] if grados_sv else None
        sv_en_tramo = next((g for g, _ in grados_sv if g in t.grados), None)
        g_cons = next((g for g in t.grados if c["proporcion_nucleo_hasta_grado"][str(g)] >= UMBRAL
                       and len(c["nucleo_hasta_grado"][str(g)]) >= MIN_PAISES), None)
        med = c["mediana_primer_grado_nucleo"]
        n_esp = sum(f["en_especializacion"] for f in c["paises"].values())
        clase = clase_de(sv_primer, sv_en_tramo, g_cons, c["n_nucleo_en_tramo"], med, c["n_nucleo_foco"], n_esp,
                         t.grados)
        filas.append({**{k: c[k] for k in ("concepto", "nombre", "asignatura", "n_paises", "n_nucleo",
                                           "n_solo_especializacion", "n_nucleo_en_tramo", "n_nucleo_foco",
                                           "mediana_primer_grado_nucleo")},
                      "n_especializacion": n_esp, "grado_consenso": g_cons,
                      "proporcion_nucleo": c["proporcion_nucleo_hasta_grado"],
                      "sv_primer_grado": sv_primer, "sv_en_tramo": sv_en_tramo,
                      "sv_temas": [t for _, t in grados_sv][:8],
                      "paises": c["paises"], "clase": clase})
    # Lo que El Salvador enseña en el tramo sin ningún referente.
    for c, gs in sorted(sv.items()):
        if c in en_consenso or c not in voc or not any(g in t.grados for g, _ in gs):
            continue
        asig = {"ciencias_tierra_espacio": "tierra_espacio"}.get(voc[c]["asignatura"], voc[c]["asignatura"])
        filas.append({"concepto": c, "nombre": voc[c]["nombre"], "asignatura": asig, "n_paises": 0, "n_nucleo": 0,
                      "n_solo_especializacion": 0, "n_nucleo_en_tramo": 0, "n_nucleo_foco": 0,
                      "mediana_primer_grado_nucleo": None,
                      "n_especializacion": 0, "sv_en_tramo": min(g for g, _ in gs if g in t.grados),
                      "grado_consenso": None, "proporcion_nucleo": {}, "sv_primer_grado": gs[0][0],
                      "sv_temas": [t for _, t in gs][:8], "paises": {}, "clase": "sin_referente"})
    ausencias_con_texto(filas, voc, temas, t.grados)
    revisiones = revisiones_expertas()
    for f in filas:
        if rv := revisiones.get(f["concepto"]):
            f["clase_ia"], f["clase"] = f["clase"], rv["clase"]
            f["revision"] = {"justificacion": rv["justificacion"], "revisado_por": rv["revisado_por"]}
    secuencia = _secuencia(sv, voc, t.grados)
    return {"filas": sorted(filas, key=lambda f: (f["asignatura"], f["clase"], f["concepto"])),
            "secuencia": secuencia, "temas": temas, "paises_con_nucleo": cons["paises_con_nucleo_por_grado"]}


# -- Doble lectura (spec 12) ---------------------------------------------------------------------------------------
def puntos_sv(temas: dict[str, dict]) -> dict[str, dict[str, int]]:
    """Concepto → {tema de la V2: puntos}, con TODOS los etiquetados de la V2: los de Vertex (malla_v2_*, cualquier
    confianza) y el del grafo principal (subagentes; su primer concepto es el principal). 2 puntos si algún etiquetado
    lo trae como principal o si lo encuentran dos etiquetados; 1 si solo uno lo trae como secundario. Con
    equivalencias y relaciones «parte de»."""
    lecturas: dict[str, list[tuple[list[str], list[str]]]] = defaultdict(list)
    for _, etiquetas in etiquetar.leer_etiquetados("malla_v2_"):
        for tid, e in etiquetas.items():
            if tid in temas:
                lecturas[tid].append((e["principales"], e["secundarios"]))
    from goes_science_kg.revisiones import revisiones_temas

    revisadas = revisiones_temas()   # el grafo principal con sus revisiones (panel, decisiones delegadas, MINED)
    for tid, e in conceptos.etiquetado().items():
        cs = revisadas.get(tid, {}).get("conceptos", e["conceptos"])
        if tid in temas and cs:
            lecturas[tid].append((cs[:1], cs[1:]))
    puntos: dict[str, dict[str, int]] = defaultdict(dict)
    for tid, ls in sorted(lecturas.items()):
        vistos = [(set(ampliar(pr)), set(ampliar([*pr, *sec]))) for pr, sec in ls]
        for c in sorted(set().union(*(todos for _, todos in vistos))):
            principal = any(c in pr for pr, _ in vistos)
            puntos[c][tid] = 2 if principal or sum(c in todos for _, todos in vistos) >= 2 else 1
    return puntos


def presencia_sv(puntos: dict[str, int], temas: dict[str, dict], grados: tuple[int, ...],
                 por_texto: set[str] | frozenset[str] = frozenset()) -> dict:
    """Primer grado de la V2 en las dos lecturas: amplia (cualquier etiqueta o el texto de la fila) y estricta (2 puntos
    acumulados), en total y dentro del tramo; `principal`: primer grado con un tema de 2 puntos. `temas`: los
    etiquetados, en orden de grado y, dentro del grado, primero los de 2 puntos."""
    orden = sorted((temas[t]["grado"], -puntos[t], t) for t in puntos)
    amplios = sorted({*((g, t) for g, _, t in orden), *((temas[t]["grado"], t) for t in por_texto)})
    en_t = [(g, t) for g, _, t in orden if g in grados]
    estricto = primer_grado_solido([(g, -p) for g, p, _ in orden])
    principal = next((g for g, p, _ in orden if p == -2), None)
    amplio_en_t = [g for g, _ in amplios if g in grados]
    return {"amplio": amplios[0][0] if amplios else None, "estricto": estricto, "principal": principal,
            "amplio_en_tramo": amplio_en_t[0] if amplio_en_t else None,
            "estricto_en_tramo": primer_grado_solido([(g, puntos[t]) for g, t in en_t]),
            "temas": [t for _, _, t in orden],
            "temas_texto": [t for _, t in amplios if t in por_texto and t not in puntos][:5],
            "temas_principal": [t for g, p, t in orden if g == principal and p == -2]}


_VACIAS = {"de", "del", "la", "las", "los", "el", "y", "e", "en", "sus", "su", "un", "una", "por", "para", "con", "al",
           "o", "que", "se", "lo", "como", "entre", "sobre"}


def _raices(texto: str) -> list[str]:
    s = "".join(ch for ch in unicodedata.normalize("NFKD", texto.lower()) if not unicodedata.combining(ch))
    return [w[:6] if len(w) > 6 else w.rstrip("s")
            for w in re.findall(r"[a-z0-9]+", s) if w not in _VACIAS and len(w) > 2]


def frases(concepto: dict) -> list[tuple[str, ...]]:
    """Frases de búsqueda de un concepto: la cabeza de su nombre (lo que va antes de «:» o «(») y cada sinónimo, como
    raíces de sus palabras («Sustancias puras: elementos y compuestos» → (sustan, pura)). Solo frases de dos raíces o
    más (de 3 letras o más): una palabra suelta («pila», «suelo») es una mención, no la enseñanza del concepto."""
    cabeza = re.split(r"[:(]", concepto["nombre"])[0]
    salida = []
    for f in [cabeza, *(concepto.get("sinonimos") or [])]:
        r = tuple(x for x in _raices(f) if len(x) >= 3)
        if len(r) >= 2 and r not in salida:
            salida.append(r)
    return salida


VENTANA = 3   # palabras (sin vacías) que puede haber entre dos raíces seguidas de una frase


def _frase_en(f: tuple[str, ...], palabras: list[str]) -> bool:
    """Si las raíces de la frase inician palabras del texto en orden, cada una a ≤ VENTANA de la anterior."""
    def desde(i: int, k: int) -> bool:
        if k == len(f):
            return True
        return any(palabras[j].startswith(f[k]) and desde(j + 1, k + 1)
                   for j in range(i, min(len(palabras), i + VENTANA + 1)))
    return any(w.startswith(f[0]) and desde(i + 1, 1) for i, w in enumerate(palabras))


def aparece(frases_c: list[tuple[str, ...]], texto: str) -> bool:
    """Si alguna frase del concepto aparece en el texto (ver _frase_en)."""
    palabras = _raices(texto)
    return any(_frase_en(f, palabras) for f in frases_c)


def presencia_por_texto(voc: dict, textos: dict[str, str]) -> dict[str, set[str]]:
    """Concepto → temas de la V2 cuyo texto completo (todas las columnas de la fila) nombra el concepto o un sinónimo
    como frase; con equivalencias y relaciones «parte de»."""
    palabras = {tid: _raices(tx) for tid, tx in textos.items()}
    iniciales = {tid: {w[:k] for w in ps for k in range(3, len(w) + 1)} for tid, ps in palabras.items()}
    por_tema: dict[str, set[str]] = defaultdict(set)
    for c, x in voc.items():
        fr = frases(x)
        for tid, ps in palabras.items():
            if any(all(r in iniciales[tid] for r in f) and _frase_en(f, ps) for f in fr):
                por_tema[tid].add(c)
    salida: dict[str, set[str]] = defaultdict(set)
    for tid, cs in por_tema.items():
        for c in ampliar(sorted(cs)):
            salida[c].add(tid)
    return dict(salida)


def _indice_paises() -> dict[str, list[tuple[float, str, frozenset[str]]]]:
    """Concepto → [(grado, objetivo, conceptos del objetivo)] del núcleo de los países, con la regla de presencia."""
    etq = etiquetar.cargar_etiquetas("pais_")
    indice: dict[str, list] = defaultdict(list)
    for o in objetivos():
        if o["nivel"] != "nucleo" or o["id"] not in etq:
            continue
        cs = frozenset(ampliar(ensenados(etq[o["id"]])))
        for c in cs:
            indice[c].append(((o["grado_sv_min"] + o["grado_sv_max"]) / 2, o["id"], cs))
    return indice


def alerta_vecinos(c: str, g_cons: float, sv_c: int, indice: dict, pres: dict) -> list[str]:
    """Conceptos vecinos que la V2 enseña antes que c y que aparecen en al menos la mitad (y ≥ 2) de los objetivos de
    los países que fechan el consenso de c (grado ≤ g_cons + 0,5): quizá los países enseñan el vecino y no c."""
    tempranos = [cs for g, _, cs in indice.get(c, []) if g <= g_cons + 0.5]
    propios = set(con_equivalentes([c]))
    cuenta = Counter(d for cs in tempranos for d in cs - propios)
    umbral = max(2, len(tempranos) / 2)
    return sorted(d for d, n in cuenta.items()
                  if n >= umbral and d in pres and pres[d]["amplio"] is not None and pres[d]["amplio"] < sv_c)


def _g_cons(c: dict, grados: tuple[int, ...], solido: bool) -> int | None:
    sufijo = "_solido" if solido else ""
    return next((g for g in grados if c[f"proporcion_nucleo{sufijo}_hasta_grado"][str(g)] >= UMBRAL
                 and len(c[f"nucleo{sufijo}_hasta_grado"][str(g)]) >= MIN_PAISES), None)


def clase_doble(p: dict, c: dict | None, grados: tuple[int, ...]) -> tuple[str, dict[str, str]]:
    """(clase, {amplia, estricta}) de un concepto con la presencia `p` de la V2 y la fila `c` del consenso (None si
    ningún país lo tiene). La clase es la de las dos lecturas si coinciden; si no, «incierto»."""
    if c is None:   # ningún país: «sin referente» si la V2 lo enseña en el tramo
        def sin_pais(primer: int | None, en_tramo: int | None) -> str:
            if primer is None:
                return "no_aplica"
            return "sin_referente" if en_tramo is not None else ("posterior" if primer > grados[-1] else "previo")
        lect = {"amplia": sin_pais(p["amplio"], p["amplio_en_tramo"]),
                "estricta": sin_pais(p["estricto"], p["estricto_en_tramo"])}
    else:
        n_esp = sum(f["en_especializacion"] for f in c["paises"].values())
        lect = {
            "amplia": clase_de(p["amplio"], p["amplio_en_tramo"], _g_cons(c, grados, True), c["n_nucleo_en_tramo"],
                               c["mediana_primer_grado_nucleo_solido"], c["n_nucleo_foco"], n_esp, grados,
                               n_mediana=c["n_nucleo_solido"]),
            "estricta": clase_de(p["estricto"], p["estricto_en_tramo"], _g_cons(c, grados, False),
                                 c["n_nucleo_en_tramo"], c["mediana_primer_grado_nucleo"], c["n_nucleo_foco"], n_esp,
                                 grados, n_mediana=c["n_nucleo"]),
        }
    if lect["amplia"] == lect["estricta"]:
        return lect["amplia"], lect
    if set(lect.values()) <= SIN_DESAJUSTE:   # ninguna lectura afirma un desajuste: no hay hallazgo que proteger
        return lect["estricta"], {**lect, "sin_desajuste": True}
    return "incierto", lect


def _clasificar_doble() -> dict:
    """clasificar() con doble lectura (docstring del módulo)."""
    voc, t = conceptos.vocabulario(), tramo.actual()
    cons = {c["concepto"]: c for c in json.loads((ruta(t.grafo) / "consenso.json").read_text(encoding="utf-8"))[
        "conceptos"]}
    temas = {x.id: x.dict() for x in extraer()}
    puntos = puntos_sv(temas)
    texto = presencia_por_texto(voc, textos_completos())
    pres = {c: presencia_sv(puntos.get(c, {}), temas, t.grados, frozenset(texto.get(c, ())))
            for c in sorted(set(puntos) | set(texto))}
    vacia = presencia_sv({}, temas, t.grados)
    indice = _indice_paises()
    filas = []
    for cid in sorted(set(cons) | {c for c in pres if c in voc}):
        c, p = cons.get(cid), pres.get(cid, vacia)
        asig = c["asignatura"] if c else {"ciencias_tierra_espacio": "tierra_espacio"}.get(voc[cid]["asignatura"],
                                                                                           voc[cid]["asignatura"])
        if asig not in ASIGNATURAS:
            continue
        clase, lect = clase_doble(p, c, t.grados)
        if c is None and "sin_referente" not in lect.values():
            continue   # ni los países ni la V2 en el tramo: fuera del contraste, como con la regla simple
        g_laxo = _g_cons(c, t.grados, False) if c else None
        g_sol = _g_cons(c, t.grados, True) if c else None
        alertas = {}
        if "tardio" in lect.values() and p["amplio"] is not None:
            alertas["vecinos"] = alerta_vecinos(cid, g_sol if g_sol is not None else g_laxo, p["amplio"], indice,
                                                pres)
        vacio = {"n_paises": 0, "n_nucleo": 0, "n_solo_especializacion": 0, "n_nucleo_en_tramo": 0,
                 "n_nucleo_foco": 0, "mediana_primer_grado_nucleo": None, "n_nucleo_solido": 0,
                 "mediana_primer_grado_nucleo_solido": None, "proporcion_nucleo_hasta_grado": {}, "paises": {}}
        c = c or {**vacio, "concepto": cid, "nombre": voc[cid]["nombre"]}
        filas.append({**{k: c[k] for k in ("concepto", "nombre", "n_paises", "n_nucleo", "n_solo_especializacion",
                                           "n_nucleo_en_tramo", "n_nucleo_foco", "mediana_primer_grado_nucleo",
                                           "n_nucleo_solido", "mediana_primer_grado_nucleo_solido")},
                      "asignatura": asig,
                      "n_especializacion": sum(f["en_especializacion"] for f in c["paises"].values()),
                      "grado_consenso": g_laxo, "grado_consenso_solido": g_sol,
                      "proporcion_nucleo": c["proporcion_nucleo_hasta_grado"],
                      "sv_primer_grado": p["amplio"], "sv_en_tramo": p["amplio_en_tramo"],
                      "sv_primer_grado_solido": p["estricto"], "sv_en_tramo_solido": p["estricto_en_tramo"],
                      "sv_temas": p["temas"][:8], "sv_temas_texto": p["temas_texto"], "paises": c["paises"],
                      "clase": clase, "lecturas": lect,
                      **({"alertas": {k: v for k, v in alertas.items() if v}} if any(alertas.values()) else {})})
    revisiones = revisiones_expertas()
    for f in filas:
        if rv := revisiones.get(f["concepto"]):
            f["clase_ia"], f["clase"] = f["clase"], rv["clase"]
            f["revision"] = {"justificacion": rv["justificacion"], "revisado_por": rv["revisado_por"]}
    secuencia = _secuencia_doble(pres, voc, t.grados)
    return {"filas": sorted(filas, key=lambda f: (f["asignatura"], f["clase"], f["concepto"])),
            "secuencia": secuencia, "temas": temas,
            "paises_con_nucleo": json.loads((ruta(t.grafo) / "consenso.json").read_text(encoding="utf-8"))[
                "paises_con_nucleo_por_grado"]}


def _secuencia_doble(pres: dict, voc: dict, grados: tuple[int, ...]) -> list[dict]:
    """Prerrequisito p → c con la lectura prudente: c como principal en un tema del tramo (la verificación encontró
    secuencias falsas apoyadas en secundarias sueltas) y p sin ninguna etiqueta ni mención en el texto hasta después."""
    salida = []
    for a in cargar_prerrequisitos():
        p, c = a["origen"], a["destino"]
        if p not in pres or c not in pres or p not in voc or c not in voc:
            continue
        gc, gp = pres[c]["principal"], pres[p]["amplio"]
        if gc is None or gp is None or gc not in grados or gp <= gc:
            continue
        salida.append({"prerrequisito": p, "nombre_prerrequisito": voc[p]["nombre"], "concepto": c,
                       "nombre_concepto": voc[c]["nombre"], "grado_prerrequisito": gp, "grado_concepto": gc,
                       "confianza": a.get("confianza"), "tema_concepto": pres[c]["temas_principal"][0],
                       "tema_prerrequisito": (pres[p]["temas"] or pres[p]["temas_texto"])[0]})
    return sorted(salida, key=lambda s: (s["grado_concepto"], s["concepto"]))


def revisiones_expertas() -> dict[str, dict]:
    """Clases decididas en revisión experta (revisiones.json del tramo activo). Ganan sobre la regla automática, como
    las decisiones humanas del grafo principal; cada una trae su evidencia y quién la revisó."""
    p = ruta(tramo.actual().revisiones)
    return {r["concepto"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def _secuencia(sv: dict, voc: dict, grados: tuple[int, ...]) -> list[dict]:

    salida = []
    for a in cargar_prerrequisitos():
        p, c = a["origen"], a["destino"]
        if p in sv and c in sv and sv[c][0][0] in grados and sv[p][0][0] > sv[c][0][0]:
            salida.append({"prerrequisito": p, "nombre_prerrequisito": voc[p]["nombre"], "concepto": c,
                           "nombre_concepto": voc[c]["nombre"], "grado_prerrequisito": sv[p][0][0],
                           "grado_concepto": sv[c][0][0], "confianza": a.get("confianza"),
                           "tema_concepto": sv[c][0][1], "tema_prerrequisito": sv[p][0][1]})
    return sorted(salida, key=lambda s: (s["grado_concepto"], s["concepto"]))


def resumen(r: dict) -> dict:
    """Conceptos por clase en cada asignatura."""
    return {a: dict(Counter(f["clase"] for f in r["filas"] if f["asignatura"] == a)) for a in ASIGNATURAS}


def evidencia_paises(fila: dict, max_paises: int = 9) -> str:
    """«PAÍS grado» con el primer grado de núcleo de cada país que tiene el concepto («PAÍS esp.» si no lo tiene en el
    núcleo), hasta `max_paises` países."""
    partes = []
    for p in paises():
        f = fila["paises"].get(p)
        if not f:
            continue
        g = f["primer_grado_nucleo"]
        partes.append(f"{p} {g:g}" if g is not None else f"{p} esp.")
    return ", ".join(partes[:max_paises])
