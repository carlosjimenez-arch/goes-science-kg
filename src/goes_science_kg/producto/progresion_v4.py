"""Measure how V4 concepts and practices are introduced and reinforced from grade 2 to grade 11."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from statistics import mean

VERSION = "progresion-v4-1"
ARCHIVO = "data/producto/progresion_v4/progresion.json"
GRADOS = tuple(range(2, 12))
BACHILLERATO = (10, 11)
DOMINIOS = ("conocer", "aplicar", "razonar")
PATRONES = ("aislado", "concentrado", "espiral", "intermitente")
LIMITE = (
    "Trayectorias derivadas de etiquetas de concepto validadas por reglas (vocabulario y evidencia literal) y de "
    "prerrequisitos históricos V3. Describen presencia documental en la malla, no secuencia oficial, carga horaria "
    "ni aprendizaje observado; no constituyen aprobación del MINED."
)


def dominios_timss(texto: str) -> tuple[str, ...]:
    """Return the TIMSS cognitive domains named in a row annotation, in canonical order."""
    encontrados = {m.casefold() for m in re.findall(r"\b(Conocer|Aplicar|Razonar)\b", texto or "", re.IGNORECASE)}
    return tuple(d for d in DOMINIOS if d in encontrados)


def plano(texto: str) -> str:
    """Return accent-free, lower-case alphanumeric text padded with spaces for whole-word lookups."""
    sin_acentos = "".join(
        c for c in unicodedata.normalize("NFKD", texto or "") if not unicodedata.combining(c)
    ).casefold()
    return " " + re.sub(r"[^a-z0-9]+", " ", sin_acentos).strip() + " "


VACIAS = frozenset("a al con de del e el en la las lo los o para por se sin sobre su sus u un una y no".split())
PREFIJO_SIGLA = "SIGLA:"


def _contenido(clave: str) -> int:
    return sum(1 for p in clave.split() if p not in VACIAS)


def claves_lexicas(vocabulario: dict[str, dict], *, min_palabra: int = 8) -> dict[str, list[str]]:
    """Derive whole-word lookup keys per concept that a single concept owns.

    A full name or synonym qualifies when no other concept declares it and it is not part of two or more other
    names (then it is generic). A fragment
    obtained by splitting a name on connectors needs two or more content words and must not appear anywhere
    else in the vocabulary, so generic phrases ("seres vivos", "características") never count as a mention.
    Upper-case acronyms (ATP) are kept with a marker and matched case-sensitively against the original text.
    """
    completos_por: dict[str, set[str]] = {}
    fragmentos_por: dict[str, set[str]] = {}
    siglas_por: dict[str, set[str]] = {}
    for ident, c in vocabulario.items():
        textos = [c.get("nombre", ""), *(c.get("sinonimos") or [])]
        completos_por[ident] = {k for t in textos if (k := plano(t).strip())}
        fragmentos_por[ident] = {
            k for t in textos for p in re.split(r",|:|;|\(|\)| y | e | o ", t) if (k := plano(p).strip())
        } - completos_por[ident]
        siglas_por[ident] = {PREFIJO_SIGLA + s for t in textos for s in re.findall(r"\b[A-Z]{3,5}\b", t)}
    usos_completos = Counter(k for ks in completos_por.values() for k in ks)
    usos_fragmentos = Counter(k for ks in fragmentos_por.values() for k in ks)
    usos_todos = usos_completos + usos_fragmentos
    usos_siglas = Counter(k for ks in siglas_por.values() for k in ks)
    claves = {}
    for ident in vocabulario:
        nombres = {
            k
            for k in completos_por[ident]
            if len(k) >= min_palabra
            and (" " in k or _contenido(k) == 1)
            and usos_completos[k] == 1
            and usos_fragmentos[k] < 2
        }
        partes = {
            k for k in fragmentos_por[ident] if _contenido(k) >= 2 and len(k) >= min_palabra and usos_todos[k] == 1
        }
        siglas = {k for k in siglas_por[ident] if usos_siglas[k] == 1}
        claves[ident] = sorted(nombres | partes | siglas)
    return claves


def menciones(textos: dict[str, tuple], claves: dict[str, list[str]]) -> dict[str, list[int]]:
    """Return the grades whose row text mentions each concept by any key, allowing simple plurals.

    `textos` maps a row to `(grado, plano(texto))` or `(grado, plano(texto), texto)`; acronyms need the
    original text and are ignored without it.
    """
    resultado = {}
    for ident, ks in claves.items():
        palabras = [k for k in ks if not k.startswith(PREFIJO_SIGLA)]
        siglas = [re.compile(rf"\b{re.escape(k.removeprefix(PREFIJO_SIGLA))}\b") for k in ks if k not in palabras]
        grados = set()
        for grado, texto, *original in textos.values():
            if any(f" {k} " in texto or f" {k}s " in texto or f" {k}es " in texto for k in palabras) or (
                original and any(r.search(original[0]) for r in siglas)
            ):
                grados.add(grado)
        if grados:
            resultado[ident] = sorted(grados)
    return resultado


def patron(grados: list[int]) -> str:
    """Classify a grade trajectory as isolated, concentrated, spiral, or intermittent."""
    if len(grados) == 1:
        return "aislado"
    huecos = [b - a - 1 for a, b in zip(grados, grados[1:], strict=False)]
    if max(huecos) >= 2:
        return "intermitente"
    return "espiral" if len(grados) >= 3 else "concentrado"


def asignaciones(etiquetas: list[dict], vista: str) -> dict[str, dict]:
    """Return the effective label per row: originals, or refined proposals replacing their originals."""
    if vista not in ("original", "propuesta"):
        raise ValueError("La vista debe ser original o propuesta")
    por_fila = {e["fila_id"]: e for e in etiquetas if e["origen"] == "original"}
    if vista == "propuesta":
        por_fila |= {e["fila_id"]: e for e in etiquetas if e["origen"] == "propuesta"}
    return por_fila


def trayectorias(filas: dict[str, dict], etiquetas: dict[str, dict], clave: str) -> dict[str, dict]:
    """Group tagged rows by concept or practice id and grade, keeping row-level provenance."""
    if clave not in ("conceptos", "practicas"):
        raise ValueError("Clave de etiqueta desconocida")
    por_id: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for fila_id, etiqueta in sorted(etiquetas.items()):
        fila = filas[fila_id]
        for posicion, ident in enumerate(etiqueta[clave]):
            por_id[ident][fila["grado"]].append({"fila_id": fila_id, "principal": posicion == 0})
    resultado = {}
    for ident, por_grado in sorted(por_id.items()):
        grados = sorted(por_grado)
        resultado[ident] = {
            "grados": grados,
            "primera": grados[0],
            "ultima": grados[-1],
            "patron": patron(grados),
            "max_hueco": max((b - a - 1 for a, b in zip(grados, grados[1:], strict=False)), default=0),
            "filas_por_grado": {str(g): len(por_grado[g]) for g in grados},
            "principal_por_grado": {str(g): sum(r["principal"] for r in por_grado[g]) for g in grados},
            "filas": {str(g): [r["fila_id"] for r in por_grado[g]] for g in grados},
        }
    return resultado


def clase_tardia(nivel_concepto: str | None, desfase: int, confianza: str | None) -> str:
    """Separate qualitative early introductions from late prerequisites that deserve expert priority."""
    if nivel_concepto == "primaria":
        return "introduccion_cualitativa"
    return "prioritaria" if desfase >= 2 and confianza == "alta" else "revisar"


def coherencia_prerrequisitos(
    conceptos: dict[str, dict],
    aristas: list[tuple[str, str]],
    confianzas: dict | None = None,
    primera_mencion: dict[str, int] | None = None,
) -> dict:
    """Check prerequisite order: a prerequisite should not first appear after the concept that needs it.

    A prerequisite counts from its first tagged row or, if earlier, its first lexical mention; the dependent
    concept counts from its first tagged row, where it is actually taught.
    """
    confianzas = confianzas or {}
    primera_mencion = primera_mencion or {}
    tardios, ausentes, simultaneos, ordenados = [], [], [], 0
    for previo, posterior in sorted(set(aristas)):
        if posterior not in conceptos:
            continue
        candidatos = [g for g in (conceptos.get(previo, {}).get("primera"), primera_mencion.get(previo)) if g]
        if not candidatos:
            ausentes.append({"prerrequisito": previo, "concepto": posterior, "grado": conceptos[posterior]["primera"]})
            continue
        a, b = min(candidatos), conceptos[posterior]["primera"]
        registro = {"prerrequisito": previo, "concepto": posterior, "grado_prerrequisito": a, "grado_concepto": b}
        if a > b:
            confianza = confianzas.get((previo, posterior))
            clase = clase_tardia(conceptos[posterior].get("nivel"), a - b, confianza)
            tardios.append(registro | {"desfase": a - b, "confianza_arista": confianza, "clase": clase})
        elif a == b:
            simultaneos.append(registro)
        else:
            ordenados += 1
    evaluables = ordenados + len(tardios) + len(simultaneos)
    return {
        "aristas_evaluables": evaluables,
        "ordenadas": ordenados,
        "simultaneas": len(simultaneos),
        "tardias": sorted(tardios, key=lambda r: (-r["desfase"], r["concepto"])),
        "ausentes": sorted(ausentes, key=lambda r: (r["grado"], r["concepto"])),
        "proporcion_ordenada": round(ordenados / evaluables, 4) if evaluables else None,
        "tardias_por_clase": dict(sorted(Counter(t["clase"] for t in tardios).items())),
    }


def construccion(conceptos: dict[str, dict], aristas: list[tuple[str, str]]) -> dict[str, list[int]]:
    """Return, per concept, the later grades where concepts that depend on it are introduced."""
    sucesores = defaultdict(set)
    for previo, posterior in aristas:
        sucesores[previo].add(posterior)
    resultado = {}
    for ident, datos in conceptos.items():
        grados = {
            conceptos[s]["primera"]
            for s in sucesores.get(ident, ())
            if s in conceptos and conceptos[s]["primera"] > datos["primera"]
        }
        resultado[ident] = sorted(grados)
    return resultado


def _asignaturas(ident: str, datos: dict, vocabulario: dict[str, dict]) -> list[str]:
    return datos.get("asignaturas") or [vocabulario.get(ident, {}).get("asignatura")]


def transicion_bachillerato(conceptos: dict[str, dict], vocabulario: dict[str, dict]) -> dict:
    """Measure whether grade 10–11 concepts of each discipline had prior exposure in grades 2–9."""
    resultado = {}
    for disciplina in ("biologia", "fisica", "quimica", "ciencias_tierra_espacio"):
        en_bach = [
            c for c, d in conceptos.items() if disciplina in _asignaturas(c, d, vocabulario) and d["ultima"] >= 10
        ]
        con_antecedente = [c for c in en_bach if conceptos[c]["primera"] <= 9]
        previos = [
            c for c, d in conceptos.items() if disciplina in _asignaturas(c, d, vocabulario) and d["primera"] <= 9
        ]
        continuados = [c for c in previos if conceptos[c]["ultima"] >= 10]
        resultado[disciplina] = {
            "conceptos_en_bachillerato": len(en_bach),
            "con_antecedente_2_9": len(con_antecedente),
            "nuevos_en_bachillerato": sorted(set(en_bach) - set(con_antecedente)),
            "conceptos_2_9": len(previos),
            "continuados_en_bachillerato": len(continuados),
        }
    return resultado


def resumen_grados(conceptos: dict[str, dict], practicas: dict[str, dict], filas: dict[str, dict]) -> list[dict]:
    """Summarize introduced and reinforced concepts, practices, and TIMSS annotations per grade."""
    resumen = []
    for g in GRADOS:
        presentes = [c for c, d in conceptos.items() if g in d["grados"]]
        nuevos = [c for c in presentes if conceptos[c]["primera"] == g]
        filas_g = [f for f in filas.values() if f["grado"] == g]
        dominios = Counter(len(f["dominios_timss"]) for f in filas_g)
        resumen.append(
            {
                "grado": g,
                "filas": len(filas_g),
                "conceptos": len(presentes),
                "introducidos": len(nuevos),
                "reforzados": len(presentes) - len(nuevos),
                "practicas": sorted(p for p, d in practicas.items() if g in d["grados"]),
                "filas_con_razonar": sum("razonar" in f["dominios_timss"] for f in filas_g),
                "filas_por_numero_de_dominios": {str(k): v for k, v in sorted(dominios.items())},
            }
        )
    return resumen


def canonicos(equivalencias: list[tuple[str, str]]) -> dict[str, str]:
    """Map every concept in an equivalence class to its smallest identifier (union-find)."""
    padre: dict[str, str] = {}

    def raiz(x: str) -> str:
        while padre.setdefault(x, x) != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, b in equivalencias:
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[max(ra, rb)] = min(ra, rb)
    return {x: raiz(x) for x in list(padre)}


def _canonizar(etiquetas: dict[str, dict], mapa: dict[str, str]) -> dict[str, dict]:
    salida = {}
    for fila_id, e in etiquetas.items():
        conceptos = list(dict.fromkeys(mapa.get(c, c) for c in e["conceptos"]))
        salida[fila_id] = e | {"conceptos": conceptos}
    return salida


def _nombrar(prer: dict, vocabulario: dict[str, dict], conceptos: dict[str, dict]) -> dict:
    for registro in (*prer["tardias"], *prer["ausentes"]):
        for clave in ("prerrequisito", "concepto"):
            ident = registro[clave]
            registro["nombre_" + clave] = vocabulario.get(ident, {}).get("nombre", ident)
        registro["prerrequisito_solo_mencion"] = registro["prerrequisito"] not in conceptos
    return prer


def analizar(
    filas: dict[str, dict],
    etiquetas: list[dict],
    vocabulario: dict[str, dict],
    aristas,
    *,
    vista: str,
    equivalencias: list[tuple[str, str]] = (),
    confianzas: dict | None = None,
):
    """Build the full progression analysis for one view, merging equivalent concepts across disciplines."""
    mapa = canonicos(list(equivalencias))
    campo = "texto_propuesta" if vista == "propuesta" else "texto"
    textos = {
        f: (
            d["grado"],
            d.get(campo) or d.get("texto") or " ",
            d.get(campo + "_original") or d.get("texto_original") or "",
        )
        for f, d in filas.items()
    }
    por_mencion: dict[str, set[int]] = defaultdict(set)
    for ident, grados in menciones(textos, claves_lexicas(vocabulario)).items():
        por_mencion[mapa.get(ident, ident)].update(grados)
    primera_mencion = {c: min(g) for c, g in por_mencion.items()}
    efectivas = _canonizar(asignaciones(etiquetas, vista), mapa)
    rango = {"baja": 0, "media": 1, "alta": 2}
    canon_conf: dict[tuple[str, str], str] = {}
    for (a, b), conf in (confianzas or {}).items():
        par = (mapa.get(a, a), mapa.get(b, b))
        if rango.get(conf, -1) > rango.get(canon_conf.get(par), -1):
            canon_conf[par] = conf
    aristas = sorted({(mapa.get(a, a), mapa.get(b, b)) for a, b in aristas})
    aristas = [(a, b) for a, b in aristas if a != b]
    agrupa = defaultdict(list)
    for c, r in mapa.items():
        agrupa[r].append(c)
    conceptos = trayectorias(filas, efectivas, "conceptos")
    practicas = trayectorias(filas, efectivas, "practicas")
    construido = construccion(conceptos, aristas)
    for ident, datos in conceptos.items():
        v = vocabulario.get(ident, {})
        datos |= {"nombre": v.get("nombre", ident), "asignatura": v.get("asignatura"), "nivel": v.get("nivel")}
        miembros = agrupa.get(ident, [ident])
        datos["asignaturas"] = sorted({a for m in miembros if (a := vocabulario.get(m, {}).get("asignatura"))})
        datos["construido_en"] = construido[ident]
        datos["agrupa"] = sorted(agrupa.get(ident, [ident]))
        datos["grados_mencion"] = sorted(por_mencion.get(ident, ()))
        datos["patron_con_menciones"] = patron(sorted(set(datos["grados"]) | por_mencion.get(ident, set())))
    patrones = Counter(d["patron"] for d in conceptos.values())
    return {
        "vista": vista,
        "filas_etiquetadas": len(efectivas),
        "conceptos_presentes": len(conceptos),
        "conceptos_vocabulario": len(vocabulario),
        "clases_equivalencia": sum(len(v) > 1 for v in agrupa.values()),
        "patrones": {p: patrones.get(p, 0) for p in PATRONES},
        "grados_promedio_por_concepto": round(mean(len(d["grados"]) for d in conceptos.values()), 3)
        if conceptos
        else 0,
        "patrones_con_menciones": {
            p: sum(d["patron_con_menciones"] == p for d in conceptos.values()) for p in PATRONES
        },
        "prerrequisitos_solo_etiquetas": {
            k: v
            for k, v in coherencia_prerrequisitos(conceptos, aristas, canon_conf).items()
            if k in ("aristas_evaluables", "ordenadas", "simultaneas", "proporcion_ordenada", "tardias_por_clase")
        },
        "prerrequisitos": _nombrar(
            coherencia_prerrequisitos(conceptos, aristas, canon_conf, primera_mencion), vocabulario, conceptos
        ),
        "aislados_por_tramo": {
            "2_9_sin_retomar": sum(d["patron"] == "aislado" and d["primera"] <= 9 for d in conceptos.values()),
            "10_11": sum(d["patron"] == "aislado" and d["primera"] >= 10 for d in conceptos.values()),
        },
        "transicion_bachillerato": transicion_bachillerato(conceptos, vocabulario),
        "grados": resumen_grados(conceptos, practicas, filas),
        "conceptos": conceptos,
        "practicas": practicas,
    }


def acuerdo(etiquetas_v4: dict[str, dict], etiquetas_v3: dict[str, dict], pares: list[tuple[str, str]]) -> dict:
    """Compare blind V4 labels with historical V3 labels on rows whose objective matches one to one."""
    jaccard, principal, tp, fp, fn, evaluados = [], 0, 0, 0, 0, 0
    for v3, v4 in pares:
        if v3 not in etiquetas_v3 or v4 not in etiquetas_v4:
            continue
        a, b = set(etiquetas_v3[v3]["conceptos"]), set(etiquetas_v4[v4]["conceptos"])
        if not a and not b:
            continue
        evaluados += 1
        jaccard.append(len(a & b) / len(a | b))
        principal += bool(etiquetas_v3[v3]["conceptos"][:1] == etiquetas_v4[v4]["conceptos"][:1] != [])
        tp, fp, fn = tp + len(a & b), fp + len(b - a), fn + len(a - b)
    precision = tp / (tp + fp) if tp + fp else 0.0
    exhaustividad = tp / (tp + fn) if tp + fn else 0.0
    return {
        "pares_evaluados": evaluados,
        "jaccard_promedio": round(mean(jaccard), 4) if jaccard else None,
        "principal_coincide": round(principal / evaluados, 4) if evaluados else None,
        "precision_vs_v3": round(precision, 4),
        "exhaustividad_vs_v3": round(exhaustividad, 4),
        "f1_vs_v3": round(2 * precision * exhaustividad / (precision + exhaustividad), 4) if tp else 0.0,
        "nota": "V3 es otra pasada de etiquetado, no una verdad de referencia; mide consistencia entre pasadas.",
    }


def construir(
    filas: dict[str, dict],
    etiquetado: dict,
    vocabulario: dict[str, dict],
    aristas: list[tuple[str, str]],
    *,
    etiquetas_v3: dict[str, dict],
    pares_v3_v4: list[tuple[str, str]],
    procedencia: dict,
    equivalencias: list[tuple[str, str]] = (),
    confianzas: dict | None = None,
) -> dict:
    """Assemble the deterministic progression document for both curriculum views."""
    mapa = canonicos(list(equivalencias))
    originales = _canonizar(asignaciones(etiquetado["etiquetas"], "original"), mapa)
    previas = _canonizar(etiquetas_v3, mapa)
    return {
        "version": VERSION,
        "snapshot_id": etiquetado["snapshot_id"],
        "procedencia": procedencia,
        "limite": LIMITE,
        "vistas": {
            v: analizar(
                filas,
                etiquetado["etiquetas"],
                vocabulario,
                aristas,
                vista=v,
                equivalencias=equivalencias,
                confianzas=confianzas,
            )
            for v in ("original", "propuesta")
        },
        "acuerdo_v3": acuerdo(originales, previas, pares_v3_v4),
    }
