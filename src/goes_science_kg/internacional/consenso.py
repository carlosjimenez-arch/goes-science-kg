"""Grafos por país y grafo de consenso internacional por asignatura, para 9.°–11.° (spec 11).

Regla de presencia, la misma del grafo principal: un objetivo ENSEÑA un concepto si lo tiene como principal, o como
secundario con confianza alta o media.

Grado de un objetivo = punto medio de su rango SV (p. ej. «Sec 3–4» = 9,5).

Antecedente: los objetivos de grados ≤ 8 de Inglaterra, Australia y Japón, que ya están en el grafo principal
(data/interim/paises + etiquetado_paises), solo sirven para fechar la primera aparición de un concepto. Así, algo
que esos países enseñan en 7.° no aparece como «nuevo en 10.°». Los demás países no tienen antecedente cargado y
eso se declara en el informe.
"""

from __future__ import annotations

import json
import statistics
from collections import Counter, defaultdict
from functools import cache
from pathlib import Path

from goes_science_kg import conceptos
from goes_science_kg.config import cargar, ruta
from goes_science_kg.ingesta import legado
from goes_science_kg.internacional import etiquetar
from goes_science_kg.internacional.extraer import DIR_SALIDA
from goes_science_kg.prerrequisitos import cargar_prerrequisitos

DIR_GRAFO = "data/grafo/internacional"
VERSION = "grafo-internacional-v1"
GRADOS = (9, 10, 11)
ANTECEDENTE = {"ENG": "inglaterra", "AU": "australia", "JP": "japon"}
ASIG_SV = {"fisica": "fisica", "quimica": "quimica", "biologia": "biologia",
           "ciencias_tierra_espacio": "tierra_espacio"}


def paises() -> list[str]:
    """Códigos de los países del estudio internacional (config/internacional.yaml), en orden alfabético."""
    return sorted(cargar("internacional")["paises"])


@cache
def objetivos() -> tuple[dict, ...]:
    """Objetivos extraídos de todos los países (DIR_SALIDA/<país>.json), ordenados por id; con caché."""
    filas = []
    for p in paises():
        f = ruta(DIR_SALIDA) / f"{p}.json"
        if f.exists():
            filas += json.loads(f.read_text(encoding="utf-8"))
    return tuple(sorted(filas, key=lambda o: o["id"]))


def etiquetar_paises(solo: list[str] | None = None) -> list[dict]:
    """Etiqueta los objetivos de cada país (ver grupos_paises)."""
    return [etiquetar.etiquetar(*g) for g in grupos_paises(solo)]


def grupos_paises(solo: list[str] | None = None) -> list[etiquetar.Grupo]:
    """Grupos de etiquetado: objetivos de cada país agrupados por asignatura (los importados sin asignatura van con
    todo el vocabulario)."""
    # Los documentos de antecedente (secundaria baja) van en grupos aparte: así no cambian los lotes ya etiquetados.
    antecedente = {d["id"] for d in cargar("internacional")["documentos"] if d.get("antecedente")}
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
    """Registro de fuentes (manifest.csv) indexado por nombre de archivo y por id, para enlazar cada objetivo con el
    mismo nodo Documento que usa el grafo principal."""
    filas = legado.manifiesto_fuentes()
    return {**{Path(r["archivo_local"]).name: r for r in filas if r.get("archivo_local")},
            **{r["id"]: r for r in filas}}


def ensenados(e: dict) -> list[str]:
    """Conceptos que el enunciado enseña según la regla de presencia."""
    sec = e["secundarios"] if e["confianza"] in ("alta", "media") else []
    return sorted({*e["principales"], *sec})


def con_equivalentes(ids: list[str]) -> list[str]:
    """Agrega los conceptos equivalentes entre asignaturas (conceptos.equivalencias(), revisadas por una persona): la
    misma idea puede estar en Física en un currículo y en Tierra y Espacio en otro (p. ej. el Big Bang)."""
    eq = _equivalencias()
    return sorted({*ids, *(y for x in ids for y in eq.get(x, ()))})


@cache
def _equivalencias() -> dict[str, frozenset[str]]:
    """Concepto → conceptos equivalentes. Se arma una vez: con_equivalentes se llama ~20 000 veces por corrida."""
    eq: dict[str, set[str]] = defaultdict(set)
    for e in conceptos.equivalencias():
        eq[e["a"]].add(e["b"])
        eq[e["b"]].add(e["a"])
    return {k: frozenset(v) for k, v in eq.items()}


def _grado(o: dict) -> float:
    return (o["grado_sv_min"] + o["grado_sv_max"]) / 2


def _antecedente() -> list[dict]:
    """(pais, concepto, grado) de los objetivos de grados ≤ 8 ya etiquetados en el grafo principal."""
    etq = conceptos.etiquetado_paises()
    filas = []
    for codigo, archivo in ANTECEDENTE.items():
        for o in json.loads(ruta(f"data/interim/paises/{archivo}.json").read_text(encoding="utf-8")):
            g = (o["grado_min"] + o["grado_max"]) / 2
            if g > 8.5 or o["id"] not in etq:
                continue
            filas.extend({"pais": codigo, "concepto": c, "grado": g, "objetivo": o["id"]}
                         for c in etq[o["id"]]["conceptos"])
    return filas


def construir() -> dict:
    """Escribe data/grafo/internacional/: grafo (nodos, aristas) y consenso por concepto."""
    voc, prac = conceptos.vocabulario(), conceptos.practicas()
    etq = etiquetar.cargar_etiquetas("pais_")
    objs = [o for o in objetivos() if o["id"] in etq]
    nodos, aristas = [], []
    cursos = sorted({(o["pais"], o["curso"], o["nivel"]) for o in objs})
    for p in paises():
        info = cargar("internacional")["paises"][p]
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
        nodos.append({**{k: o[k] for k in (
            "id", "pais", "documento", "archivo", "pagina", "curso", "nivel", "asignatura", "grado_sv_min",
            "grado_sv_max", "eje", "demanda", "texto")}, "tipo": "ObjetivoPais", "tipo_objetivo": o["tipo"],
            "validacion": o["validacion"]["veredicto"], "version": o["version"],
            "documento_registro": doc["id"] if doc else None})
        aristas.append({"origen": f"CURSO:{o['pais']}/{o['curso']}", "destino": o["id"], "tipo": "CONTIENE"})
        if doc:   # mismo id que el nodo Documento del grafo principal: se navega documento ↔ objetivos
            documentos[doc["id"]] = doc
            aristas.append({"origen": o["id"], "destino": f"DOC:{doc['id']}", "tipo": "FUENTE",
                            **({"pagina": o["pagina"]} if o.get("pagina") else {})})
        for c in e["principales"]:
            aristas.append({"origen": o["id"], "destino": c, "tipo": "ENSEÑA", "peso": "principal",
                            "confianza": e["confianza"], "justificacion": e["justificacion"], "version": e["version"]})
            usados.add(c)
        for c in e["secundarios"]:
            aristas.append({"origen": o["id"], "destino": c, "tipo": "ENSEÑA", "peso": "secundario",
                            "confianza": e["confianza"], "justificacion": e["justificacion"], "version": e["version"]})
            usados.add(c)
        for pr in e["practicas"]:
            aristas.append({"origen": o["id"], "destino": pr, "tipo": "PRACTICA", "confianza": e["confianza"]})
            usados.add(pr)
    for d in documentos.values():
        nodos.append({"id": f"DOC:{d['id']}", "tipo": "Documento", "nombre": d["titulo"],
                      **{k: d.get(k) for k in ("organismo", "anio", "url", "archivo_local", "sha256")}})
    for c in sorted(usados):
        x = voc.get(c) or prac.get(c)
        nodos.append({"id": c, "tipo": "Concepto" if c in voc else "Practica", "nombre": x["nombre"],
                      "asignatura": x.get("asignatura"), "definicion": x.get("definicion")})

    aristas.extend({"origen": a["origen"], "destino": a["destino"], "tipo": "PRERREQUISITO",
                    "confianza": a.get("confianza"), "tipo_evidencia": a.get("tipo_evidencia")}
                   for a in cargar_prerrequisitos() if a["origen"] in usados and a["destino"] in usados)

    consenso = _consenso(objs, etq, voc)
    base = ruta(DIR_GRAFO)
    base.mkdir(parents=True, exist_ok=True)
    nodos.sort(key=lambda n: n["id"])
    aristas.sort(key=lambda a: (a["tipo"], a["origen"], a["destino"], a.get("peso", "")))
    for nombre, filas in (("nodos", nodos), ("aristas", aristas)):
        (base / f"{nombre}.jsonl").write_text("".join(json.dumps(f, ensure_ascii=False) + "\n" for f in filas),
                                               encoding="utf-8")
    (base / "consenso.json").write_text(json.dumps(consenso, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    manifest = {"version": VERSION, "paises": paises(), "objetivos": len(objs),
                "objetivos_sin_documento_registrado": sum(n.get("documento_registro") is None
                                                          for n in nodos if n["tipo"] == "ObjetivoPais"),
                "nodos": len(nodos), "aristas": len(aristas), "conceptos_en_consenso": len(consenso["conceptos"]),
                "paises_con_nucleo_por_grado": consenso["paises_con_nucleo_por_grado"]}
    (base / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return manifest


def _consenso(objs: list[dict], etq: dict, voc: dict) -> dict:
    # Denominador del consenso: países con un núcleo común (para todos) que llega hasta el grado g o antes.
    # Pregunta: ¿qué proporción de los currículos comunes ya enseñó el concepto a esa edad? Hong Kong, sin núcleo
    # en S4–S6, no entra en el denominador (sí en la especialización).
    con_nucleo = {g: sorted({o["pais"] for o in objs if o["nivel"] == "nucleo" and o["grado_sv_min"] <= g})
                  for g in GRADOS}
    por: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"nucleo": [], "especializacion": []}))
    # Evidencia del núcleo por país: 2 puntos por objetivo con el concepto como principal, 1 como secundario.
    # Con ≥ 2 puntos el núcleo «lo enseña» de forma sólida (un principal, o al menos dos secundarios).
    foco: dict[str, Counter] = defaultdict(Counter)
    for o in objs:
        principales = set(con_equivalentes(etq[o["id"]]["principales"]))
        for c in con_equivalentes(ensenados(etq[o["id"]])):
            por[c][o["pais"]][o["nivel"]].append((_grado(o), o["id"], o["grado_sv_max"]))
            if o["nivel"] == "nucleo":
                foco[c][o["pais"]] += 2 if c in principales else 1
    previo: dict[str, dict[str, float]] = defaultdict(dict)
    for a in _antecedente():
        g = previo[a["concepto"]].get(a["pais"])
        previo[a["concepto"]][a["pais"]] = a["grado"] if g is None else min(g, a["grado"])
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
            # El núcleo de 9.°–11.° solo cuenta objetivos extraídos cuyo rango llega a 9.° (no el antecedente).
            nucleo_9_11 = any(gmax >= GRADOS[0] for _, _, gmax in d["nucleo"])
            # Evidencia: primero los objetivos del núcleo, después los de especialización.
            ids = sorted({i for _, i, _ in d["nucleo"]}) + sorted({i for _, i, _ in d["especializacion"]})
            filas[p] = {"primer_grado_nucleo": primero_nucleo, "primer_grado": primero,
                        "antes_de_9": ga is not None, "en_especializacion": bool(ge), "nucleo_9_11": nucleo_9_11,
                        "objetivos": list(dict.fromkeys(ids))[:12]}
            if primero_nucleo is not None:
                primeros_nucleo.append(primero_nucleo)
            primeros.append(primero)
        if not filas:
            continue
        nucleo_hasta = {g: sorted(p for p, f in filas.items()
                                  if f["primer_grado_nucleo"] is not None and f["primer_grado_nucleo"] <= g + 0.5)
                        for g in GRADOS}
        salida.append({
            "concepto": c, "nombre": voc[c]["nombre"], "asignatura": ASIG_SV.get(voc[c]["asignatura"]),
            "paises": filas, "n_paises": len(filas),
            "n_nucleo": len(primeros_nucleo),
            "n_nucleo_9_11": sum(f["nucleo_9_11"] for f in filas.values()),
            "n_nucleo_foco": sum(v >= 2 for v in foco[c].values()),
            "n_solo_especializacion": sum(f["primer_grado_nucleo"] is None for f in filas.values()),
            "mediana_primer_grado_nucleo": statistics.median(primeros_nucleo) if primeros_nucleo else None,
            "mediana_primer_grado": statistics.median(primeros),
            "nucleo_hasta_grado": nucleo_hasta,
            "proporcion_nucleo_hasta_grado": {g: round(len(nucleo_hasta[g]) / max(1, len(con_nucleo[g])), 3)
                                              for g in GRADOS},
        })
    return {"version": VERSION, "paises_con_nucleo_por_grado": con_nucleo, "conceptos": salida}
