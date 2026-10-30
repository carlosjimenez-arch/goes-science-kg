"""Build country and international consensus graphs by subject and grade band."""

# Historical implementation notes:
# Regla de presencia, la misma del grafo principal: un objetivo ENSEÑA un concepto si lo tiene como principal, o como
# secundario con confianza alta o media.
#
# Grado de un objetivo = punto medio de su rango SV (p. ej. «Sec 3–4» = 9,5).
#
# Doble lectura (tramos con `lectura_doble`, spec 12): además del primer grado de cada país con la regla de presencia
# (lectura amplia), se calcula el primer grado con presencia SÓLIDA en el núcleo (lectura estricta): 2 puntos por
# objetivo con el concepto como principal y 1 como secundario, acumulados por grado hasta llegar a 2. Ahí también se
# aplican las relaciones «parte de» (conceptos.partes()), además de las equivalencias.
#
# Antecedente: los objetivos de grados ≤ 8 solo sirven para fechar la primera aparición de un concepto. Así, algo que
# un país enseña en 7.° no aparece como «nuevo en 10.°». Son los de Inglaterra, Australia y Japón del grafo principal
# (data/interim/paises + etiquetado_paises) y, desde el 2026-10-13, los del núcleo de los demás países en el tramo
# 2.°–8.° (spec 12), ya extraídos y etiquetados: primaria y secundaria baja de HK, SG y EE, y primaria de KR, TW y ON
# (su secundaria baja ya está en el tramo 9.°–11.° como documento de antecedente).

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from functools import cache
from pathlib import Path

from goes_science_kg import conceptos
from goes_science_kg.config import cargar, ruta
from goes_science_kg.ingesta import legado
from goes_science_kg.internacional import etiquetar, tramo
from goes_science_kg.prerrequisitos import cargar_prerrequisitos

VERSION = "grafo-internacional-v1"
ANTECEDENTE = {"ENG": "inglaterra", "AU": "australia", "JP": "japon"}
# Países cuyo antecedente sale del tramo 2.°–8.° (ENG, AU y JP ya lo traen del grafo principal).
ANTECEDENTE_2_8 = ("EE", "HK", "KR", "ON", "SG", "TW")
ASIG_SV = {
    "fisica": "fisica",
    "quimica": "quimica",
    "biologia": "biologia",
    "ciencias_tierra_espacio": "tierra_espacio",
}


def paises() -> list[str]:
    """Return the active grade band's configured country codes in alphabetical order."""
    return sorted(cargar(tramo.actual().config)["paises"])


def objetivos() -> tuple[dict, ...]:
    """Load and cache the active band's country objectives in identity order."""
    return _objetivos(tramo.actual().clave)


@cache
def _objetivos(clave: str) -> tuple[dict, ...]:
    filas = []
    for p in paises():
        f = ruta(tramo.TRAMOS[clave].objetivos) / f"{p}.json"
        if f.exists():
            filas += json.loads(f.read_text(encoding="utf-8"))
    return tuple(sorted(filas, key=lambda o: o["id"]))


def grupos_paises(solo: list[str] | None = None) -> list[etiquetar.Grupo]:
    """Group country objectives by their explicit subject metadata."""

    # Implementation notes:
    # todo el vocabulario).
    # Los documentos de antecedente (secundaria baja) van en grupos aparte: así no cambian los lotes ya etiquetados.
    antecedente = {d["id"] for d in cargar(tramo.actual().config)["documentos"] if d.get("antecedente")}
    resumen = []
    for p in paises():
        if solo and p not in solo:
            continue
        grupos: dict[str, list[dict]] = defaultdict(list)
        for o in objetivos():
            if o["pais"] == p:
                sufijo = "_antecedente" if o["documento"] in antecedente else ""
                grupos[(o["asignatura"] or "ciencias") + sufijo].append({"id": o["id"], "texto": o["texto"]})
        for grupo, items in sorted(grupos.items()):
            resumen.append((items, grupo.removesuffix("_antecedente"), f"pais_{p}_{grupo}"))
    return resumen


def _registro_de_documentos() -> dict[str, dict]:
    """Index registered document metadata by filename and source identity."""

    # Implementation notes:
    # mismo nodo Documento que usa el grafo principal.
    filas = legado.manifiesto_fuentes()
    return {
        **{Path(r["archivo_local"]).name: r for r in filas if r.get("archivo_local")},
        **{r["id"]: r for r in filas},
    }


def ensenados(e: dict) -> list[str]:
    """Return concepts taught by a statement under the configured presence rule."""
    sec = e["secundarios"] if e["confianza"] in ("alta", "media") else []
    return sorted({*e["principales"], *sec})


def con_equivalentes(ids: list[str]) -> list[str]:
    """Expand explicit, human-reviewed equivalences across subject vocabularies."""

    # Implementation notes:
    # misma idea puede estar en Física en un currículo y en Tierra y Espacio en otro (p. ej. el Big Bang).
    eq = _equivalencias()
    return sorted({*ids, *(y for x in ids for y in eq.get(x, ()))})


def ampliar(ids: list[str]) -> list[str]:
    """Expand part-of concepts and their explicitly reviewed equivalents."""

    # Implementation notes:
    # conservación de la energía mecánica, también enseña la conservación de la energía. Solo con doble lectura.
    base = con_equivalentes(ids)
    todos = _partes()
    return con_equivalentes(sorted({*base, *(t for x in base for t in todos.get(x, ()))}))


def expandir(ids: list[str]) -> list[str]:
    """Apply the expansion policy selected for the active contrast method."""
    return ampliar(ids) if tramo.actual().lectura_doble else con_equivalentes(ids)


@cache
def _partes() -> dict[str, frozenset[str]]:
    """Map each part to the wholes that explicitly contain it."""
    todos: dict[str, set[str]] = defaultdict(set)
    for r in conceptos.partes():
        todos[r["parte"]].add(r["todo"])
    return {k: frozenset(v) for k, v in todos.items()}


def primer_grado_solido(puntos: list[tuple[float, int]], minimo: int = 2) -> float | None:
    """Find the first grade reaching the required accumulated concept-presence score."""

    # Implementation notes:
    # secundarios (1 + 1).
    acumulado = 0
    for g, p in sorted(puntos):
        acumulado += p
        if acumulado >= minimo:
            return g
    return None


@cache
def _equivalencias() -> dict[str, frozenset[str]]:
    """Cache concept equivalences for repeated international comparisons."""
    eq: dict[str, set[str]] = defaultdict(set)
    for e in conceptos.equivalencias():
        eq[e["a"]].add(e["b"])
        eq[e["b"]].add(e["a"])
    return {k: frozenset(v) for k, v in eq.items()}


def _grado(o: dict) -> float:
    return (o["grado_sv_min"] + o["grado_sv_max"]) / 2


def _antecedente() -> list[dict]:
    """Collect earlier country-objective evidence from the principal graph."""

    # Implementation notes:
    # concepto de cada objetivo es el principal (2 puntos) y los demás, secundarios (1).
    etq = conceptos.etiquetado_paises()
    filas = []
    for codigo, archivo in ANTECEDENTE.items():
        for o in json.loads(ruta(f"data/interim/paises/{archivo}.json").read_text(encoding="utf-8")):
            g = (o["grado_min"] + o["grado_max"]) / 2
            if g > tramo.actual().grados[0] - 0.5 or o["id"] not in etq:  # solo lo anterior al tramo
                continue
            filas.extend(
                {"pais": codigo, "concepto": c, "grado": g, "objetivo": o["id"], "puntos": 2 if i == 0 else 1}
                for i, c in enumerate(etq[o["id"]]["conceptos"])
            )
    return filas + _antecedente_2_8()


def _antecedente_2_8() -> list[dict]:
    """Collect earlier core objectives from other countries' grade-two-to-eight band."""

    # Implementation notes:
    # HK ni otra especialización), salvo los documentos que el tramo activo ya tiene (kr_jung, tw_jh, on_snc1w). Lo
    # encontró el bucle el 2026-10-13: la reflexión interna total, núcleo de HK S1–3 (p. 74), salía como especialización
    # porque la secundaria baja de HK no contaba.
    t28 = tramo.TRAMOS["2_8"]
    if tramo.actual().clave == t28.clave:
        return []
    etq = dict(kv for _, e in etiquetar._leer_etiquetados("pais_", t28.etiquetado) for kv in e.items())
    propios = {o["documento"] for o in objetivos()}
    limite = tramo.actual().grados[0] - 0.5
    filas = []
    for p in ANTECEDENTE_2_8:
        archivo = ruta(t28.objetivos) / f"{p}.json"
        for o in json.loads(archivo.read_text(encoding="utf-8")) if archivo.exists() else []:
            e = etq.get(o["id"])
            if not e or o["nivel"] != "nucleo" or o["documento"] in propios or _grado(o) > limite:
                continue
            filas.extend(
                {
                    "pais": p,
                    "concepto": c,
                    "grado": _grado(o),
                    "objetivo": o["id"],
                    "puntos": 2 if c in e["principales"] else 1,
                }
                for c in ensenados(e)
            )
    return filas


def construir() -> dict:
    """Write the active band's country graphs and concept-level consensus."""
    voc, prac = conceptos.vocabulario(), conceptos.practicas()
    etq = etiquetar.cargar_etiquetas("pais_")
    objs = [o for o in objetivos() if o["id"] in etq]
    nodos, aristas = [], []
    cursos = sorted({(o["pais"], o["curso"], o["nivel"]) for o in objs})
    for p in paises():
        info = cargar(tramo.actual().config)["paises"][p]
        nodos.append({"id": f"PAIS:{p}", "tipo": "Pais", "nombre": info["nombre"], "nota": info.get("nota")})
    for p, curso, nivel in cursos:
        cid = f"CURSO:{p}/{curso}"
        nodos.append({"id": cid, "tipo": "Curso", "pais": p, "nombre": curso, "nivel": nivel})
        aristas.append({"origen": f"PAIS:{p}", "destino": cid, "tipo": "OFRECE"})
    usados: set[str] = set()
    registro = _registro_de_documentos()
    documentos: dict[str, dict] = {}
    for o in objs:
        e = etq[o["id"]]
        doc = registro.get(Path(o["archivo"]).name) or registro.get(o["documento"])
        nodos.append(
            {
                **{
                    k: o[k]
                    for k in (
                        "id",
                        "pais",
                        "documento",
                        "archivo",
                        "pagina",
                        "curso",
                        "nivel",
                        "asignatura",
                        "grado_sv_min",
                        "grado_sv_max",
                        "eje",
                        "demanda",
                        "texto",
                    )
                },
                "tipo": "ObjetivoPais",
                "tipo_objetivo": o["tipo"],
                "validacion": o["validacion"]["veredicto"],
                "version": o["version"],
                "documento_registro": doc["id"] if doc else None,
            }
        )
        aristas.append({"origen": f"CURSO:{o['pais']}/{o['curso']}", "destino": o["id"], "tipo": "CONTIENE"})
        if doc:  # mismo id que el nodo Documento del grafo principal: se navega documento ↔ objetivos
            documentos[doc["id"]] = doc
            aristas.append(
                {
                    "origen": o["id"],
                    "destino": f"DOC:{doc['id']}",
                    "tipo": "FUENTE",
                    **({"pagina": o["pagina"]} if o.get("pagina") else {}),
                }
            )
        for c in e["principales"]:
            aristas.append(
                {
                    "origen": o["id"],
                    "destino": c,
                    "tipo": "ENSEÑA",
                    "peso": "principal",
                    "confianza": e["confianza"],
                    "justificacion": e["justificacion"],
                    "version": e["version"],
                }
            )
            usados.add(c)
        for c in e["secundarios"]:
            aristas.append(
                {
                    "origen": o["id"],
                    "destino": c,
                    "tipo": "ENSEÑA",
                    "peso": "secundario",
                    "confianza": e["confianza"],
                    "justificacion": e["justificacion"],
                    "version": e["version"],
                }
            )
            usados.add(c)
        for pr in e["practicas"]:
            aristas.append({"origen": o["id"], "destino": pr, "tipo": "PRACTICA", "confianza": e["confianza"]})
            usados.add(pr)
    for d in documentos.values():
        nodos.append(
            {
                "id": f"DOC:{d['id']}",
                "tipo": "Documento",
                "nombre": d["titulo"],
                **{k: d.get(k) for k in ("organismo", "anio", "url", "archivo_local", "sha256")},
            }
        )
    for c in sorted(usados):
        x = voc.get(c) or prac.get(c)
        nodos.append(
            {
                "id": c,
                "tipo": "Concepto" if c in voc else "Practica",
                "nombre": x["nombre"],
                "asignatura": x.get("asignatura"),
                "definicion": x.get("definicion"),
            }
        )

    aristas.extend(
        {
            "origen": a["origen"],
            "destino": a["destino"],
            "tipo": "PRERREQUISITO",
            "confianza": a.get("confianza"),
            "tipo_evidencia": a.get("tipo_evidencia"),
        }
        for a in cargar_prerrequisitos()
        if a["origen"] in usados and a["destino"] in usados
    )

    consenso = _consenso(objs, etq, voc)
    base = ruta(tramo.actual().grafo)
    base.mkdir(parents=True, exist_ok=True)
    nodos.sort(key=lambda n: n["id"])
    aristas.sort(key=lambda a: (a["tipo"], a["origen"], a["destino"], a.get("peso", "")))
    for nombre, filas in (("nodos", nodos), ("aristas", aristas)):
        (base / f"{nombre}.jsonl").write_text(
            "".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas), encoding="utf-8"
        )
    (base / "consenso.json").write_text(json.dumps(consenso, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    manifest = {
        "version": VERSION,
        "paises": paises(),
        "objetivos": len(objs),
        "objetivos_sin_documento_registrado": sum(
            n.get("documento_registro") is None for n in nodos if n["tipo"] == "ObjetivoPais"
        ),
        "nodos": len(nodos),
        "aristas": len(aristas),
        "conceptos_en_consenso": len(consenso["conceptos"]),
        "paises_con_nucleo_por_grado": consenso["paises_con_nucleo_por_grado"],
    }
    (base / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


NIVELES_NUCLEO = ("nucleo", "nucleo_parcial")


def _consenso(objs: list[dict], etq: dict, voc: dict) -> dict:
    grados, doble = tramo.actual().grados, tramo.actual().lectura_doble
    # Denominador del consenso: países con un núcleo común (para todos) que llega hasta el grado g o antes.
    # Pregunta: ¿qué proporción de los currículos comunes ya enseñó el concepto a esa edad? Hong Kong, sin núcleo
    # en S4–S6, no entra en el denominador (sí en la especialización).
    # «nucleo_parcial» (lo cursa la mayoría, no todos: SG Combined, JP 基礎) cuenta como núcleo en la presencia laxa de
    # los países y como especialización en la sólida (los puntos solo suman con el núcleo pleno).
    con_nucleo = {
        g: sorted({o["pais"] for o in objs if o["nivel"] in NIVELES_NUCLEO and o["grado_sv_min"] <= g}) for g in grados
    }
    por: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"nucleo": [], "especializacion": []}))
    # Evidencia del núcleo por país: 2 puntos por objetivo con el concepto como principal, 1 como secundario.
    # Con ≥ 2 puntos el núcleo «lo enseña» de forma sólida (un principal, o al menos dos secundarios).
    foco: dict[str, Counter] = defaultdict(Counter)
    puntos: dict[str, dict[str, list[tuple[float, int]]]] = defaultdict(lambda: defaultdict(list))
    for o in objs:
        principales = set(expandir(etq[o["id"]]["principales"]))
        for c in expandir(ensenados(etq[o["id"]])):
            nivel = "nucleo" if o["nivel"] in NIVELES_NUCLEO else o["nivel"]
            por[c][o["pais"]][nivel].append((_grado(o), o["id"], o["grado_sv_max"]))
            if o["nivel"] == "nucleo":
                foco[c][o["pais"]] += 2 if c in principales else 1
                puntos[c][o["pais"]].append((_grado(o), 2 if c in principales else 1))
    previo: dict[str, dict[str, float]] = defaultdict(dict)
    for a in _antecedente():
        for c in expandir([a["concepto"]]) if doble else [a["concepto"]]:
            g = previo[c].get(a["pais"])
            previo[c][a["pais"]] = a["grado"] if g is None else min(g, a["grado"])
            puntos[c][a["pais"]].append((a["grado"], a["puntos"]))
            # El núcleo sólido (n_nucleo_foco) cuenta la secundaria baja, como dice la regla de «solo especialización»
            # (contraste.py). Antes no la sumaba (lo encontró el panel el 2026-10-13: la pila de Daniell de JP 中3).
            foco[c][a["pais"]] += a["puntos"]
    salida = []
    for c in sorted(set(por) | set(previo)):
        if c not in voc:
            continue
        filas, primeros_nucleo, primeros = {}, [], []
        for p in paises():
            d = por[c].get(p) or {"nucleo": [], "especializacion": []}
            gn = [g for g, _, _ in d["nucleo"]]
            ge = [g for g, _, _ in d["especializacion"]]
            ga = previo[c].get(p)
            primero_nucleo = min([*gn, *([ga] if ga is not None else [])], default=None)
            primero = min([*gn, *ge, *([ga] if ga is not None else [])], default=None)
            if primero is None:
                continue
            # El núcleo del tramo solo cuenta objetivos extraídos cuyo rango llega al tramo (no el antecedente).
            nucleo_en_tramo = any(gmax >= grados[0] for _, _, gmax in d["nucleo"])
            # Evidencia: primero los objetivos del núcleo, después los de especialización.
            ids = sorted({i for _, i, _ in d["nucleo"]}) + sorted({i for _, i, _ in d["especializacion"]})
            filas[p] = {
                "primer_grado_nucleo": primero_nucleo,
                "primer_grado": primero,
                "antes_del_tramo": ga is not None,
                "en_especializacion": bool(ge),
                "nucleo_en_tramo": nucleo_en_tramo,
                "objetivos": list(dict.fromkeys(ids))[:12],
            }
            if doble:
                filas[p]["primer_grado_nucleo_solido"] = primer_grado_solido(puntos[c][p])
            if primero_nucleo is not None:
                primeros_nucleo.append(primero_nucleo)
            primeros.append(primero)
        if not filas:
            continue
        nucleo_hasta = {
            g: sorted(
                p
                for p, f in filas.items()
                if f["primer_grado_nucleo"] is not None and f["primer_grado_nucleo"] <= g + 0.5
            )
            for g in grados
        }
        extra = {}
        if doble:
            solidos = [
                f["primer_grado_nucleo_solido"] for f in filas.values() if f["primer_grado_nucleo_solido"] is not None
            ]
            hasta = {
                g: sorted(
                    p
                    for p, f in filas.items()
                    if f["primer_grado_nucleo_solido"] is not None and f["primer_grado_nucleo_solido"] <= g + 0.5
                )
                for g in grados
            }
            extra = {
                "n_nucleo_solido": len(solidos),
                "mediana_primer_grado_nucleo_solido": statistics.median(solidos) if solidos else None,
                "nucleo_solido_hasta_grado": hasta,
                "proporcion_nucleo_solido_hasta_grado": {
                    g: round(len(hasta[g]) / max(1, len(con_nucleo[g])), 3) for g in grados
                },
            }
        salida.append(
            {
                "concepto": c,
                "nombre": voc[c]["nombre"],
                "asignatura": ASIG_SV.get(voc[c]["asignatura"]),
                "paises": filas,
                "n_paises": len(filas),
                "n_nucleo": len(primeros_nucleo),
                "n_nucleo_en_tramo": sum(f["nucleo_en_tramo"] for f in filas.values()),
                "n_nucleo_foco": sum(v >= 2 for v in foco[c].values()),
                "n_solo_especializacion": sum(f["primer_grado_nucleo"] is None for f in filas.values()),
                "mediana_primer_grado_nucleo": statistics.median(primeros_nucleo) if primeros_nucleo else None,
                "mediana_primer_grado": statistics.median(primeros),
                "nucleo_hasta_grado": nucleo_hasta,
                "proporcion_nucleo_hasta_grado": {
                    g: round(len(nucleo_hasta[g]) / max(1, len(con_nucleo[g])), 3) for g in grados
                },
                **extra,
            }
        )
    return {"version": VERSION, "paises_con_nucleo_por_grado": con_nucleo, "conceptos": salida}
