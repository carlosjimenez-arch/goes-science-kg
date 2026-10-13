"""Refuerzo de cada tema de la malla vigente (V3) con lo que el repo ya sabe (spec 15).

Cuatro fuentes, solo con evidencia y sin quitar nada:
- errores de la malla (`data/interim/refuerzo_v3/errores_malla.json`, curado): se buscan LITERALES en la vigente;
- recomendaciones del panel con solidez «sólido» o «respaldado»;
- hallazgos del contraste internacional;
- lo que la V3 dejó de cubrir y los países o los marcos enseñan en el núcleo.

Este módulo arma los candidatos (código, sin IA). La redacción de las filas propuestas y su revisión van después.
"""

from __future__ import annotations

import json
import unicodedata
from functools import cache

from goes_science_kg.config import ruta

DIR = "data/interim/refuerzo_v3"


def _plano(texto: str) -> str:
    """Minúsculas, sin tildes y con los espacios normalizados: para buscar un fragmento literal."""
    t = unicodedata.normalize("NFKD", texto.lower())
    return " ".join("".join(c for c in t if not unicodedata.combining(c)).split())


@cache
def errores_malla() -> tuple[dict, ...]:
    """Los errores y problemas de progresión curados, con su fragmento literal."""
    return tuple(json.loads(ruta(f"{DIR}/errores_malla.json").read_text(encoding="utf-8")))


def errores_en_vigente() -> list[dict]:
    """Cada error con los temas de la malla vigente donde su fragmento sigue literal (en toda la fila). Sin temas, la
    V3 lo corrigió o lo quitó: no se inyecta y se registra como «corregido_en_v3»."""
    from goes_science_kg.ingesta.mallas import textos_completos

    textos = {i: _plano(t) for i, t in textos_completos().items()}
    salida = []
    for e in errores_malla():
        frag = _plano(e["cita_literal"])
        temas = sorted(i for i, t in textos.items() if frag in t)
        salida.append({**e, "temas_v3": temas, "estado": "sigue" if temas else "corregido_en_v3"})
    return salida


# -- catálogo de candidatos (15.4) ------------------------------------------------------------------------------------
VERSION = "refuerzo-v3-1"
SOLIDEZ_INYECTABLE = ("solido", "respaldado")   # lo frágil, sin consenso o sin bucle no se inyecta
ID_TEMA = r"G\d\d-[A-Z]{3}-U\d+-\d+(?:\.\d+)+(?:-f\d+|-v3)?"
# Clase del contraste (con revisión) → tipo de refuerzo. «alineado», «retomado», «sin_referente» y «no_aplica» no
# generan refuerzo: no afirman un desajuste.
TIPO_POR_CLASE = {
    "2_8": {"tardio": "adelantar", "posterior": "agregar_precursor", "adelantado": "acotar", "faltante": "agregar"},
    "9_11": {"previo": "adelantar", "solo_especializacion": "acotar", "faltante": "agregar", "no_retomado": "retomar",
             "tardio": "adelantar", "adelantado": "acotar"},
}


@cache
def _movidos() -> dict[str, str]:
    from goes_science_kg.config import cargar

    p = ruta(cargar("mallas")["correspondencia"])
    return {x["id"]: x["movido_a"] for x in json.loads(p.read_text(encoding="utf-8"))["sin_par"] if x["movido_a"]}


def ubicacion_vigente(id_tema: str) -> str | None:
    """El tema de la malla vigente donde está hoy el contenido de un tema citado: el mismo, el que lo absorbió o
    aquel al que se movió de grado."""
    from goes_science_kg.ingesta.mallas import vigente_de

    i = id_tema.removeprefix("TEMA:")
    return vigente_de(i) or _movidos().get(i)


def _temas_citados(*textos: object) -> list[str]:
    import re

    ids = re.findall(ID_TEMA, " ".join(json.dumps(t, ensure_ascii=False) for t in textos))
    return list(dict.fromkeys(v for i in ids if (v := ubicacion_vigente(i))))


def _grados_en(texto: str) -> list[int]:
    """Grados nombrados en un texto («en 5.°–6.°», «7.°», «10.°»)."""
    import re

    salida: set[int] = set()
    for a, b in re.findall(r"(\d{1,2})\.°(?:\s*[–-]\s*(\d{1,2})\.°)?", texto or ""):
        g0, g1 = int(a), int(b or a)
        salida.update(g for g in range(g0, g1 + 1) if 2 <= g <= 11)
    return sorted(salida)


def _texto_final(x: dict) -> str:
    """El texto con que el panel matizó o adaptó (el del experto de la disciplina, si lo hay)."""
    from goes_science_kg import bucle

    finales = [d for d in bucle._finales(x) if d["decision"] == x["resolucion"]["decision"] and d.get("texto")]
    finales.sort(key=lambda d: not d["rol"].startswith("experto-"))
    return finales[0]["texto"] if finales else ""


def _candidatos_errores() -> list[dict]:
    salida = []
    for e in errores_en_vigente():
        if e["estado"] != "sigue":
            continue
        salida.append({"origen": "error_malla", "tipo": "corregir" if e["tipo"] == "error_cientifico" else "precisar",
                       "temas_v3": e["temas_v3"], "grados": [], "conceptos": [], "texto_base": e["correccion"],
                       "problema": e["problema"],
                       "evidencia": [{"fuente": f"TEMA:{t}", "cita_literal": e["cita_literal"]} for t in e["temas_v3"]],
                       "solidez": "solido", "referencia": e["id"]})
    return salida


def _candidatos_panel() -> list[dict]:
    """Hallazgos respaldados o matizados y propuestas adoptadas o adaptadas por el panel, con solidez inyectable."""
    from goes_science_kg import conceptos, panel

    voc = conceptos.vocabulario()
    por_nombre = {c["nombre"].lower(): i for i, c in voc.items()}
    salida = []
    for i, x in sorted(panel.cargar_estado().items()):
        s = (x.get("bucle") or {}).get("solidez")
        if x["estado"] != "resuelta" or s not in SOLIDEZ_INYECTABLE:
            continue
        d, dec = x["datos"], x["resolucion"]["decision"]
        if x["tipo"] == "hallazgo" and dec in ("respaldar", "matizar"):
            texto = _texto_final(x) or d.get("recomendacion", "")
            salida.append({"origen": "panel_hallazgo", "tipo": "precisar", "asignatura": d.get("asignatura"),
                           "temas_v3": _temas_citados(d.get("evidencia"), d.get("recomendacion"), texto),
                           "grados": _grados_en(f"{d.get('recomendacion', '')} {texto}"), "conceptos": [],
                           "texto_base": texto, "problema": d.get("titulo", ""),
                           "evidencia": [{"fuente": d.get("fuente", ""), "cita": d.get("evidencia", "")}],
                           "solidez": s, "referencia": i})
        elif x["tipo"] == "propuesta" and dec in ("adoptar", "adaptar"):
            nombres = d.get("conceptos") or []
            if isinstance(nombres, str):
                nombres = [n.strip(" '\"") for n in nombres.strip("[]").split("',")]
            ids = [c for n in nombres if (c := por_nombre.get(n.strip(" '\"").lower()))]
            texto = _texto_final(x) if dec == "adaptar" else d.get("tema_propuesto", "")
            salida.append({"origen": "panel_propuesta", "tipo": "agregar", "asignatura": d.get("asignatura"),
                           "temas_v3": _temas_citados(d.get("unidad_propuesta"), d.get("justificacion")),
                           "grados": [int(d["grado_propuesto"])] if str(d.get("grado_propuesto", "")).isdigit() else [],
                           "conceptos": ids, "texto_base": texto or d.get("tema_propuesto", ""),
                           "problema": d.get("justificacion", ""),
                           "propuesta_original": {k: d.get(k) for k in ("unidad_propuesta", "tema_propuesto",
                                                                        "indicador_logro")},
                           "evidencia": [{"fuente": "propuesta curricular (spec 06)", "cita": d.get("evidencia", "")}],
                           "solidez": s, "referencia": i})
    return salida


def _candidatos_contraste() -> list[dict]:
    """Clases del contraste que afirman un desajuste y tienen revisión (panel, delegada o humana): las automáticas
    sin verificar no se inyectan (spec 12: 25 % de falsos)."""
    from goes_science_kg import panel
    from goes_science_kg import revision_decisiones as rd

    salida = []
    for tramo, tipos in TIPO_POR_CLASE.items():
        revs = {r["concepto"]: r for r in rd._leer("clase_internacional_2_8" if tramo == "2_8" else
                                                    "clase_internacional")}
        for c, f in sorted(panel._contraste(tramo).items()):
            if f["clase"] not in tipos or not f.get("revision") or c not in revs:
                continue
            r = revs[c]
            temas = list(dict.fromkeys([*f.get("sv_temas", []), *f.get("sv_temas_texto", [])]))[:6]
            if not temas and tipos[f["clase"]] == "acotar":
                continue   # la malla vigente ya no lo enseña: no hay nada que acotar
            salida.append({"origen": "contraste", "tipo": tipos[f["clase"]], "tramo": tramo, "clase": f["clase"],
                           "asignatura": f.get("asignatura"), "conceptos": [c], "temas_v3": temas,
                           "grados": sorted({g for g in (f.get("grado_consenso"), f.get("grado_consenso_solido"),
                                                         f.get("sv_primer_grado")) if g}),
                           "texto_base": r.get("justificacion", ""), "problema": f"{f['nombre']}: {f['clase']}",
                           "evidencia": r.get("evidencia") or [{"fuente": f"revisión ({r.get('revisado_por', '')})",
                                                                "cita": r.get("justificacion", "")}],
                           "solidez": "revisada",
                           "referencia": f"{tramo}:{c}"})
    return salida


def _cobertura(version: str) -> dict[str, set[int]]:
    """Concepto → grados en que lo enseña la malla `version` (etiquetado del grafo principal, con lo absorbido). Una
    parte cubre a su todo (conceptos.partes()): «enlace iónico» enseña «enlace químico»."""
    from goes_science_kg import conceptos
    from goes_science_kg.ingesta.mallas import extraer

    todos: dict[str, set[str]] = {}
    for r in conceptos.partes():
        todos.setdefault(r["parte"], set()).add(r["todo"])
    etq, salida = conceptos.etiquetado(), {}
    for t in extraer(version):
        for c in (etq.get(t.id) or {}).get("conceptos", []):
            for x in (c, *todos.get(c, ())):
                salida.setdefault(x, set()).add(t.grado)
    return salida


def _candidatos_quitado() -> list[dict]:
    """Conceptos que la V2 enseñaba en un tramo y la V3 ya no enseña ahí (ni por etiqueta ni por el texto de la fila),
    con núcleo sólido en ≥ 3 países, cuando los países los enseñan a esa edad:
    - 2.°–8.°: la V3 ya no lo enseña o lo movió después de 8.°, y la mediana del núcleo es ≤ 8.°;
    - 9.°–11.°: la V3 ya no lo enseña o lo dejó solo antes de 9.°, y la mediana del núcleo es ≥ 9.°.
    Lo que la V3 dejó en un grado anterior y los países también enseñan antes no es una pérdida."""
    from goes_science_kg import panel
    from goes_science_kg.ingesta.mallas import extraer

    antes, ahora = _cobertura("mallas_v2"), _cobertura("mallas")
    grado = {t.id: t.grado for t in extraer()}
    salida = []
    for tramo, (g0, g1) in (("2_8", (2, 8)), ("9_11", (9, 11))):
        con = panel._contraste(tramo)
        for c in sorted(antes):
            grados_v2 = sorted(g for g in antes[c] if g0 <= g <= g1)
            if not grados_v2 or any(g0 <= g <= g1 for g in ahora.get(c, ())):
                continue
            f = con.get(c)
            if not f or (f.get("n_nucleo_solido") or 0) < 3:
                continue
            if any(g0 <= grado.get(t, 0) <= g1 for t in f.get("sv_temas_texto", [])):
                continue   # el texto de una fila del tramo lo enseña: falta la etiqueta, no el contenido
            mediana = f.get("mediana_primer_grado_nucleo_solido") or f.get("mediana_primer_grado_nucleo")
            if ahora.get(c) and mediana is not None and (mediana > g1 if tramo == "2_8" else mediana < g0):
                continue   # la V3 lo enseña en otro grado y los países no lo esperan en este tramo
            salida.append({"origen": "quitado_v3", "tipo": "recuperar", "tramo": tramo,
                           "asignatura": f.get("asignatura"), "conceptos": [c], "temas_v3": [],
                           "grados": grados_v2, "texto_base": "",
                           "problema": f"{f['nombre']}: la V2 lo enseñaba en {', '.join(f'{g}.°' for g in grados_v2)}"
                                       f" y la V3 ya no lo enseña en {g0}.°–{g1}.°"
                                       + (f" (ahora en {', '.join(f'{g}.°' for g in sorted(ahora[c]))})"
                                          if ahora.get(c) else " (en ningún grado)"),
                           "evidencia": [{"fuente": f"contraste {tramo}",
                                          "cita": f"núcleo sólido en {f['n_nucleo_solido']} países; mediana del "
                                                  f"primer grado {mediana}"}],
                           "solidez": "calculada", "referencia": f"{tramo}:{c}"})
    return salida


def candidatos() -> list[dict]:
    """Todos los candidatos a refuerzo, con id estable («REF:<origen>:<referencia>»: no cambia al regenerar el
    catálogo) y orden determinista."""
    filas = [*_candidatos_errores(), *_candidatos_panel(), *_candidatos_contraste(), *_candidatos_quitado()]
    filas.sort(key=lambda f: (f["origen"], f["referencia"]))
    return [{"id": f"REF:{f['origen']}:{f['referencia']}", "version": VERSION, **f} for f in filas]


def escribir_candidatos() -> dict:
    from collections import Counter

    filas = candidatos()
    p = ruta(f"{DIR}/candidatos.json")
    p.write_text(json.dumps(filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"candidatos": len(filas), "por_origen": dict(Counter(f["origen"] for f in filas)),
            "por_tipo": dict(Counter(f["tipo"] for f in filas)),
            "sin_ubicacion": sum(1 for f in filas if not f["temas_v3"] and not f["grados"])}


def grados_destino(f: dict, grado_de: dict[str, int]) -> list[int]:
    """Dónde va el refuerzo de un candidato: lo que se adelanta, agrega o retoma va al grado que dicen los países (o el
    panel); lo que se acota o corrige, donde la malla lo enseña hoy; lo que se recupera, donde lo tenía la V2."""
    anclas = sorted({grado_de[t] for t in f["temas_v3"] if t in grado_de})
    if f["origen"] == "contraste":
        g0, g1 = (2, 8) if f.get("tramo") == "2_8" else (9, 11)
        if f["tipo"] in ("adelantar", "agregar_precursor", "agregar", "retomar"):
            propios = [g for g in f["grados"] if g <= g1]
            return sorted(set(propios)) or [g for g in anclas if g0 <= g <= g1]
        return [g for g in anclas if g0 <= g <= g1] or anclas
    if f["origen"] in ("panel_propuesta", "quitado_v3"):
        return f["grados"] or anclas
    return sorted({*f["grados"], *anclas})


# -- lotes del redactor (15.5) ----------------------------------------------------------------------------------------
TAMANO_LOTE = 20
FORMAS = ("nota_en_tema", "fila_nueva")
TIPOS_CON_FILA = ("agregar", "agregar_precursor", "recuperar")
CAMPOS_FILA = ("contenido", "procedimental", "indicador", "evidencia_aprendizaje")


def _asignatura_de_temas() -> dict[str, str]:
    """Id del tema → asignatura (disciplina) en el grafo: en 2.°–9.° la malla es «ciencias» y la disciplina sale de la
    clasificación o de la revisión."""
    from goes_science_kg.grafo.almacen import cargar

    return {n.id.removeprefix("TEMA:"): n.asignatura for n in cargar()[0] if n.tipo.value == "Tema" and n.asignatura}


def _conceptos_en_re_decision() -> set[str]:
    """Conceptos con un expediente de la serie v3 del panel todavía sin resolver: su clase puede cambiar."""
    from goes_science_kg import panel

    ids = {e["id"] for p in sorted(ruta(f"{panel.DIR}/lotes").glob("lote_r1-v3_*.json"))
           for e in json.loads(p.read_text(encoding="utf-8"))["expedientes"]}
    estado = panel.cargar_estado()
    return {estado[i]["datos"]["concepto"]["id"] for i in ids if i in estado and estado[i]["estado"] != "resuelta"}


def preparar_lotes(serie: str = "a", asignaturas: tuple[str, ...] | None = None,
                   tramo: str | None = None) -> list[str]:
    """Lotes por asignatura y tramo con los candidatos (candidatos.json), sus temas ancla y los temas de cada grado
    destino, en una serie («lote_<asig>_<tramo>_<serie>»). No reescribe lotes: deja fuera los candidatos que ya están
    en un lote y los del contraste cuyo concepto el panel todavía re-decide (serie v3)."""
    from goes_science_kg.config import relativa
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t for t in extraer()}
    asig_de = _asignatura_de_temas()
    d = ruta(f"{DIR}/lotes")
    d.mkdir(parents=True, exist_ok=True)
    ya = {c["id"] for p in d.glob("lote_*.json") for c in json.loads(p.read_text(encoding="utf-8"))["candidatos"]}
    pendientes = _conceptos_en_re_decision()
    filas = [f for f in json.loads(ruta(f"{DIR}/candidatos.json").read_text(encoding="utf-8"))
             if f["id"] not in ya and not (f["origen"] in ("contraste", "quitado_v3") and set(f["conceptos"]) &
                                           pendientes)]
    grupos: dict[tuple[str, str], list[dict]] = {}
    for f in filas:
        anclas = [t for t in f["temas_v3"] if t in temas]
        asig = f.get("asignatura") or next((asig_de[t] for t in anclas if t in asig_de), None) or "ciencias"
        asig = {"tierra_espacio": "ciencias_tierra_espacio"}.get(asig, asig)
        grados = grados_destino(f, {i: t.grado for i, t in temas.items()})
        su_tramo = "2_8" if grados and min(grados) <= 8 else "9_11"
        if (asignaturas and asig not in asignaturas) or (tramo and su_tramo != tramo):
            continue
        f = {**f, "asignatura": asig, "grados_destino": grados,
             "temas_ancla": [{"id": t, "grado": temas[t].grado, "unidad": temas[t].unidad,
                              "contenido": temas[t].contenido, "procedimental": temas[t].procedimental,
                              "indicador": temas[t].indicador} for t in anclas[:4]]}
        grupos.setdefault((asig, su_tramo), []).append(f)
    escritos = []
    for (asig, su_tramo), cands in sorted(grupos.items()):
        partes = [cands[i:i + TAMANO_LOTE] for i in range(0, len(cands), TAMANO_LOTE)]
        for k, parte in enumerate(partes, start=1):
            nombre = f"{asig}_{su_tramo}_{serie}" + (f"_{k}" if len(partes) > 1 else "")
            claves = sorted({(g, asig) for c in parte for g in c["grados_destino"]})
            del_grado = {f"{g}:{a}": [f"{t.id} | {t.procedimental[:110]}" for t in temas.values()
                                       if t.grado == g and (asig_de.get(t.id) == a or t.asignatura == a)]
                         for g, a in claves}
            lote = {"lote": nombre, "version": VERSION, "instrucciones": "prompts/redactar_refuerzos.md",
                    "candidatos": parte, "temas_del_grado": del_grado}
            p = d / f"lote_{nombre}.json"
            p.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            escritos.append(relativa(p))
    return escritos


def errores_lote(lote: dict, salida: list[dict]) -> list[str]:
    """Errores de la salida del redactor-refuerzos: los mismos que hacen fallar unir() (y que revisa
    `gskg lotes validar` al terminar el subagente)."""
    from goes_science_kg.ingesta.mallas import extraer

    ids_malla = {t.id for t in extraer()}
    cands = {c["id"]: c for c in lote["candidatos"]}
    por_id: dict[str, dict] = {}
    errores = []
    for s in salida:
        if s.get("id") in por_id:
            errores.append(f"{s.get('id')}: repetido")
        por_id[s.get("id")] = s
    if faltan := sorted(cands.keys() - por_id.keys()):
        errores.append(f"faltan {faltan[:5]}")
    if sobran := sorted(por_id.keys() - cands.keys(), key=str):
        errores.append(f"ids fuera del lote {sobran[:5]}")
    for i, s in por_id.items():
        if i not in cands:
            continue
        e = []
        if s.get("decision") not in ("inyectar", "descartar"):
            e.append(f"decision inválida {s.get('decision')!r}")
        elif s["decision"] == "descartar":
            if not s.get("motivo") or len(s["motivo"].split()) > 40:
                e.append("un descarte exige motivo (40 palabras como máximo)")
        else:
            if s.get("forma") not in FORMAS:
                e.append(f"forma inválida {s.get('forma')!r}")
            if s.get("tema_ancla") not in ids_malla:
                e.append(f"tema_ancla {s.get('tema_ancla')!r} no está en la malla vigente")
            if not s.get("refuerzo") or len(s["refuerzo"].split()) > 60:
                e.append("refuerzo vacío o de más de 60 palabras")
            if s.get("forma") == "fila_nueva":
                if cands[i]["tipo"] not in TIPOS_CON_FILA:
                    e.append(f"una fila nueva solo para {', '.join(TIPOS_CON_FILA)} "
                             f"(el candidato es {cands[i]['tipo']})")
                fila = s.get("fila") or {}
                if faltan_campos := [c for c in CAMPOS_FILA if not fila.get(c)]:
                    e.append(f"fila sin {faltan_campos}")
            if not s.get("evidencia"):
                e.append("sin evidencia")
        if s.get("confianza") not in ("alta", "media", "baja"):
            e.append(f"confianza inválida {s.get('confianza')!r}")
        errores += [f"{i}: {x}" for x in e]
    return errores


def unir() -> dict:
    """Valida todas las salidas (todo o nada) y escribe refuerzos.json: cada decisión del redactor con su candidato,
    «propuesta_pendiente» hasta que la revise el panel."""
    from collections import Counter

    d, filas, errores = ruta(f"{DIR}/lotes"), [], []
    for p_lote in sorted(d.glob("lote_*.json")):
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        lote, salida = (json.loads(x.read_text(encoding="utf-8")) for x in (p_lote, p_sal))
        errores += [f"{p_sal.name}: {e}" for e in errores_lote(lote, salida)]
        cands = {c["id"]: c for c in lote["candidatos"]}
        filas += [{**cands[s["id"]], **s, "estado": "propuesta_pendiente", "origen_redaccion":
                   f"redactor-refuerzos ({lote['lote']})", "version_redaccion": lote["version"]}
                  for s in salida if s.get("id") in cands]
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    # Lo que ya revisó el panel no se pisa: volver a unir solo agrega o actualiza lo que sigue pendiente.
    p = ruta(f"{DIR}/refuerzos.json")
    previos = {r["id"]: r for r in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    filas = [previos[f["id"]] if previos.get(f["id"], {}).get("estado", "propuesta_pendiente") != "propuesta_pendiente"
             else f for f in filas]
    filas.sort(key=lambda f: f["id"])
    p.write_text(json.dumps(filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"refuerzos": len(filas), "decision": dict(Counter(f["decision"] for f in filas)),
            "forma": dict(Counter(f.get("forma") for f in filas if f["decision"] == "inyectar"))}


# -- snapshot por asignatura y grados ---------------------------------------------------------------------------------
NOMBRE_ASIG = {"fisica": "Física", "quimica": "Química", "biologia": "Biología",
               "ciencias_tierra_espacio": "Ciencias de la Tierra y del Espacio"}


def _disciplina_v2() -> dict[str, str]:
    """Disciplina de los temas de la V2: la del grafo vigente si el tema sigue; si no, la de su concepto principal."""
    from goes_science_kg import conceptos

    asig, voc, etq = _asignatura_de_temas(), conceptos.vocabulario(), conceptos.etiquetado()
    salida = {}
    from goes_science_kg.ingesta.mallas import extraer

    for t in extraer("mallas_v2"):
        if t.id in asig:
            salida[t.id] = asig[t.id]
        elif (cs := (etq.get(t.id) or {}).get("conceptos")) and cs[0] in voc:
            salida[t.id] = voc[cs[0]]["asignatura"]
        elif t.asignatura != "ciencias":
            salida[t.id] = t.asignatura
    return salida


def snapshot(asignaturas: tuple[str, ...], grados: tuple[int, ...], etapa: str) -> str:
    """Markdown con el estado del refuerzo de esas asignaturas y grados (de mayor a menor grado)."""
    from collections import Counter

    from goes_science_kg import panel
    from goes_science_kg.config import cargar
    from goes_science_kg.ingesta.mallas import extraer

    v3 = {t.id: t for t in extraer()}
    asig3 = _asignatura_de_temas()
    asig2 = _disciplina_v2()
    corr = json.loads(ruta(cargar("mallas")["correspondencia"]).read_text(encoding="utf-8"))
    sin_par = {x["id"]: x for x in corr["sin_par"]}
    v2 = {t.id: t for t in extraer("mallas_v2")}
    nombres = " y ".join(NOMBRE_ASIG[a] for a in asignaturas)
    rango = f"{max(grados)}.° a {min(grados)}.°"
    md = [f"# Refuerzo de la malla V3: {nombres}, {rango}", "",
          f"> **Corte: {etapa}.** Lo generó `gskg refuerzo snapshot`. Son propuestas del equipo GOES con evidencia, no "
          "decisiones del MINED. El texto oficial no se modifica.", ""]
    # 1. qué cambió
    md += ["## 1. Qué cambió la V3", "",
           "| Grado | Asignatura | Temas V2 | Temas V3 | Idénticos | Parecidos | Ampliados | Nuevos | V2 absorbidos | "
           "V2 movidos | V2 sin rastro |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for g in sorted(grados, reverse=True):
        for a in asignaturas:
            t3 = [t for t in v3.values() if t.grado == g and asig3.get(t.id) == a]
            t2 = [t for t in v2.values() if t.grado == g and asig2.get(t.id) == a]
            o = Counter(t.origen for t in t3)
            sp = [sin_par[t.id] for t in t2 if t.id in sin_par]
            md.append(f"| {g}.° | {NOMBRE_ASIG[a]} | {len(t2)} | {len(t3)} | {o['identico']} | {o['parecido']} | "
                      f"{o['ampliado']} | {o['nuevo']} | {sum(bool(x['absorbido_por']) for x in sp)} | "
                      f"{sum(bool(x['movido_a']) for x in sp)} | "
                      f"{sum(not x['absorbido_por'] and not x['movido_a'] for x in sp)} |")
    md += ["", "*Ampliado: el tema de la V3 contiene casi entero uno de la V2 y conserva su id. Absorbido: el tema "
           "de la V2 está dentro de otro tema de la V3. Sin rastro: no aparece en el texto de la V3; se juzga por "
           "concepto.*", ""]
    # 2. errores
    errores = [e for e in errores_en_vigente() if any(asig3.get(t) in asignaturas and v3[t].grado in grados
                                                     for t in e["temas_v3"]) or
               (e["estado"] != "sigue" and v2.get(e["tema_v2"]) and v2[e["tema_v2"]].grado in grados
                and asig2.get(e["tema_v2"]) in asignaturas)]
    md += ["## 2. Errores y problemas de progresión de la malla", ""]
    for e in errores:
        donde = ", ".join(e["temas_v3"]) or "—"
        md.append(f"- **{e['id']}** ({'sigue en la V3' if e['estado'] == 'sigue' else 'corregido en la V3'}; "
                  f"{donde}): {e['problema']} *Propuesta:* {e['correccion']}")
    if not errores:
        md.append("- Ninguno registrado en estas asignaturas y grados.")
    md.append("")
    # 3. candidatos
    filas = [f for f in candidatos() if f.get("asignatura") in (*asignaturas, None) or f["origen"] == "error_malla"]
    por_grado: dict[int, list[dict]] = {}
    for f in filas:
        anclas = [t for t in f["temas_v3"] if t in v3]
        a = f.get("asignatura") or next((asig3.get(t) for t in anclas if asig3.get(t)), None)
        if a not in asignaturas:
            continue
        gs = sorted(set(grados_destino(f, {i: t.grado for i, t in v3.items()})) & set(grados))
        if not gs:
            continue
        por_grado.setdefault(max(gs), []).append({**f, "asignatura": a, "anclas": anclas})
    md += ["## 3. Candidatos a refuerzo, por grado", "",
           "Cada candidato trae su evidencia y la solidez de lo que lo respalda. Todavía no está redactado como fila "
           "de la malla (etapa 15.5).", ""]
    for g in sorted(por_grado, reverse=True):
        md += [f"### {g}.°", "", "| Id | Asignatura | Tipo | Origen | Tema de la V3 | Qué se propone | Evidencia | "
               "Solidez |", "|---|---|---|---|---|---|---|---|"]
        for f in sorted(por_grado[g], key=lambda f: (f["asignatura"], f["id"])):
            tema = "; ".join(f"{t} {v3[t].procedimental[:70]}" for t in f["anclas"] if v3[t].grado == g)[:160] or "—"
            que = (f.get("texto_base") or f.get("problema") or "").replace("|", "/").replace("\n", " ")
            ev = " / ".join(str(e.get("cita_literal") or e.get("cita") or e.get("fuente", ""))[:90]
                            for e in f["evidencia"][:2]).replace("|", "/").replace("\n", " ")
            md.append(f"| {f['id']} | {NOMBRE_ASIG[f['asignatura']]} | {f['tipo']} | {f['origen']} | {tema} | "
                      f"{que[:260]} | {ev} | {f['solidez']} |")
        md.append("")
    # 4. re-decisiones del panel
    estado = panel.cargar_estado()
    ids_v3 = {e["id"] for p in sorted(ruta(f"{panel.DIR}/lotes").glob("lote_r1-v3_*.json"))
              for e in json.loads(p.read_text(encoding="utf-8"))["expedientes"]}
    serie = {i: x for i, x in estado.items() if i in ids_v3
             and x["datos"]["concepto"]["id"].split(":")[1].split("/")[0] in asignaturas
             and (x["datos"].get("tramo", "2_8") == "9_11" if min(grados) >= 9 else True)}
    pend = {i: x for i, x in serie.items() if x["estado"] != "resuelta"}
    md += ["## 4. Clases del contraste que el panel re-decide con la V3 (serie v3)", "",
           f"{len(serie)} expedientes; {len(pend)} todavía sin resolver.", ""]
    for i, x in sorted(serie.items()):
        res = x.get("resolucion", {}).get("decision") if x["estado"] == "resuelta" else x["estado"]
        ant = (x["datos"].get("decision_anterior") or {}).get("clase")
        md.append(f"- `{i}`: {x['titulo']}" + (f" (antes: {ant})" if ant else "") + f" → **{res}**")
    md += ["", "## 5. Qué falta para la versión final", "",
           "1. Cerrar la serie v3 del panel y pasarla por el bucle de fortalecimiento.",
           "2. Regenerar los candidatos con las clases nuevas.",
           "3. Redactar cada refuerzo como nota o como fila de la malla (subagente `redactor-refuerzos`).",
           "4. Revisión del panel (experto y psicopedagogo) de cada redacción, y bucle.",
           "5. Copias anotadas de sus Excel en `entregas/mallas_v3_reforzadas/`.", ""]
    return "\n".join(md)


def escribir_snapshot(asignaturas: tuple[str, ...], grados: tuple[int, ...], etapa: str):
    """Escribe el snapshot en entregas/mallas_v3_reforzadas/ y devuelve su ruta."""
    nombre = "_".join(asignaturas) + f"_{min(grados)}-{max(grados)}"
    p = ruta(f"entregas/mallas_v3_reforzadas/SNAPSHOT_{nombre}.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(snapshot(asignaturas, grados, etapa), encoding="utf-8")
    return p
