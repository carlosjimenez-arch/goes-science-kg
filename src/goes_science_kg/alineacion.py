"""Lotes de alineación de temas de la malla contra un catálogo pivote (skill alinear-objetivos).

preparar → data/interim/alineaciones/lotes/lote_<nombre>.json   (lo lee un subagente)
           el subagente escribe salida_<nombre>.json: [{id, obj1, obj2, confianza, justificacion}]
unir     → data/interim/alineaciones/<destino>.json            (validado: códigos, ids, confianza)

Se usa para Biología y Química de 10.°–11.° contra ACARA Senior Secondary (marco AUSS) y para los temas de
2.°–9.° que aún no tienen clasificación TIMSS 2027 o PISA 2025 (los 47 que agregó la V2), con los mismos prompts
del trabajo previo (`reportes/cobertura_curricular/prompts/clasificar_lote.md` y `clasificar_lote_pisa.md`).
"""

from __future__ import annotations

import json
from collections import Counter

from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.ingesta import legado
from goes_science_kg.ingesta.mallas import TemaMalla, extraer, por_id_con_anteriores

DIR = "data/interim/alineaciones"
CONFIANZAS = {"alta", "media", "baja"}
CAMPOS_TEMA = ("id", "unidad", "contenido", "subcontenido", "procedimental", "indicador")
CAMPOS_TEMA_NUEVO = ("id", "archivo", "hoja", "fila", "grado", *CAMPOS_TEMA[1:], "evidencia")
VERSION_TIMSS_NUEVOS = "v2-2027-temas-nuevos"
VERSION_PISA_NUEVOS = "pisa2025-temas-nuevos"
PROMPTS = {"T": "reportes/cobertura_curricular/prompts/clasificar_lote.md",
           "PISA": "reportes/cobertura_curricular/prompts/clasificar_lote_pisa.md"}
CONOCIMIENTOS = {"Contenido", "Procedimental", "Epistémico"}
CONTEXTOS = {"Personal", "Local/nacional", "Global", "Sin contexto"}
AREAS = {"Salud y enfermedad", "Recursos naturales", "Impactos ambientales y cambio climático", "Riesgos",
         "Avances y desafíos científicos y tecnológicos", ""}
DEMANDAS = {"Baja", "Media", "Alta"}


def _nombre_libre(d, base: str) -> str:
    """El nombre del lote: el base, o «<base>_V3» (la versión de la malla vigente) si el base ya tiene salida, para no
    reescribir un lote ya unido (spec 15)."""
    if not (d / f"salida_{base}.json").exists():
        return base
    return f"{base}_{cargar('mallas').get('version', 'nueva')}"


def preparar_bachillerato(catalogo: list[dict], version: str, solo_pendientes: bool = True) -> list[str]:
    """Un lote por asignatura y grado (Biología y Química de 10.° y 11.°). Con solo_pendientes, únicamente los temas
    sin clasificación ACARA (p. ej. los nuevos de la V3), en lotes que no reescriben los ya unidos."""
    from goes_science_kg.ingesta.legado import clasificacion_auss

    d = ruta(DIR) / "lotes"
    d.mkdir(parents=True, exist_ok=True)
    escritos = []
    temas = [t for t in extraer() if t.asignatura in ("biologia", "quimica")]
    if solo_pendientes:
        hechas = clasificacion_auss()
        temas = [t for t in temas if t.llave not in hechas]
    for (asig, grado) in sorted({(t.asignatura, t.grado) for t in temas}):
        objs = [{k: o[k] for k in ("codigo", "unidad", "eje", "tema", "objetivo")}
                for o in catalogo if o["asignatura"] == asig]
        lote = {
            "lote": _nombre_libre(d, f"AUSS_{asig}_G{grado}") if solo_pendientes else f"AUSS_{asig}_G{grado}",
            "version": version, "marco": "AUSS",
            "instrucciones": "prompts/alinear_bachillerato_auss.md",
            "catalogo": objs,
            "items": [{k: getattr(t, k) for k in CAMPOS_TEMA} for t in temas
                      if t.asignatura == asig and t.grado == grado],
        }
        p = d / f"lote_{lote['lote']}.json"
        p.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
        escritos.append(relativa(p))
    return escritos


def unir(prefijo_lote: str, destino: str, catalogo: list[dict]) -> dict:
    """Valida y une las salidas de los subagentes. Lanza ValueError ante cualquier problema. Los códigos válidos son
    los del catálogo de cada lote (`catalogo` se conserva por compatibilidad de la CLI)."""
    d = ruta(DIR) / "lotes"
    por_tema: dict[str, TemaMalla] = por_id_con_anteriores()   # lotes ya unidos citan temas de la V2 (spec 15)
    filas, errores = [], []
    for p_lote in sorted(d.glob(f"lote_{prefijo_lote}*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        lista = json.loads(p_sal.read_text(encoding="utf-8"))
        errores += [f"{p_sal.name}: {e}" for e in errores_lote(lote, lista)]
        salida = {s["id"]: s for s in lista}
        for i in sorted({i["id"] for i in lote["items"]} & salida.keys()):
            s = salida[i]
            obj1, obj2 = s.get("obj1") or "", s.get("obj2") or ""
            t = por_tema[i]
            filas.append({"id": i, "archivo": t.llave[0], "hoja": t.llave[1], "fila": t.llave[2],
                          "procedimental": t.procedimental, "obj1": obj1,
                          "obj2": "" if obj2 == "FUERA" else obj2, "confianza": s.get("confianza"),
                          "justificacion": s.get("justificacion"), "version": lote["version"],
                          "revisado_por": ""})
    if errores:
        raise ValueError(f"{len(errores)} errores al unir: " + "; ".join(errores[:15]))
    salida = ruta(DIR) / f"{destino}.json"
    salida.write_text(json.dumps(filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"temas": len(filas), "confianza": dict(Counter(f["confianza"] for f in filas)),
            "fuera": sum(f["obj1"] == "FUERA" for f in filas)}


# -- temas de 2.°–9.° sin clasificación previa (los que agregó la V2) ---------------------------------------------
def _llave(t: TemaMalla) -> tuple[str, str, int]:
    return t.llave


def pendientes() -> dict[str, list[TemaMalla]]:
    """Temas de 2.°–9.° sin clasificación TIMSS 2027, de Física de Bachillerato sin TIMSS Advanced y de 7.°–9.° sin
    clasificación PISA 2025."""
    ct, cp = legado.clasificacion_timss(), legado.clasificacion_pisa()
    temas = [t for t in extraer() if t.asignatura in ("ciencias", "fisica")]
    return {"timss": [t for t in temas if _llave(t) not in ct],
            "pisa": [t for t in temas if t.asignatura == "ciencias" and 7 <= t.grado <= 9 and _llave(t) not in cp]}


def _catalogo_timss(marco: str) -> list[dict]:
    return [{"codigo": o["codigo"], "dominio": o["dominio"], "area": o["area"], "objetivo": o["objetivo"],
             "es_investigacion": o.get("es_investigacion", False),
             "subitems": [s["texto"] if isinstance(s, dict) else s for s in o.get("subitems", [])]}
            for o in legado.catalogo_timss2027() if o["marco"] == marco]


def _catalogo_ta() -> list[dict]:
    """TIMSS Advanced 2015 Física (la clasificación previa de Física de Bachillerato)."""
    return [{"codigo": o["codigo"], "dominio": o["dominio"], "area": o["area"], "objetivo": o["objetivo"]}
            for o in legado.catalogo_timss_v1() if o["marco"] == "TA"]


def _catalogo_pisa() -> list[dict]:
    return [{k: e.get(k) for k in ("codigo", "tipo", "grupo", "texto")}
            for e in legado.catalogo_pisa2025()["elementos"] if e["tipo"] != "subcompetencia"]


def preparar_temas_nuevos() -> list[str]:
    """Lotes para los temas sin clasificación previa: TIMSS 4.° (2.°–4.°), TIMSS 8.° (5.°–9.°) y PISA (7.°–9.°).
    Sin pendientes no escribe nada; volver a correrlo antes de unir reescribe los mismos lotes."""
    d = ruta(DIR) / "lotes"
    d.mkdir(parents=True, exist_ok=True)
    pend = pendientes()
    grupos = (("TN_T4_27", "T4_27", VERSION_TIMSS_NUEVOS, [t for t in pend["timss"] if t.grado <= 4],
               _catalogo_timss("T4_27"), PROMPTS["T"]),
              ("TN_T8_27", "T8_27", VERSION_TIMSS_NUEVOS,
               [t for t in pend["timss"] if 5 <= t.grado <= 9 and t.asignatura == "ciencias"],
               _catalogo_timss("T8_27"), PROMPTS["T"]),
              ("TN_TA15", "TA15", VERSION_TIMSS_NUEVOS, [t for t in pend["timss"] if t.asignatura == "fisica"],
               _catalogo_ta(), PROMPTS["T"]),
              ("TN_PISA25", "PISA25", VERSION_PISA_NUEVOS, pend["pisa"], _catalogo_pisa(), PROMPTS["PISA"]))
    escritos = []
    for base, marco, version, temas, catalogo, prompt in grupos:
        if not temas:
            continue
        nombre = _nombre_libre(d, base)
        lote = {"lote": nombre, "marco": marco, "version": version, "instrucciones": prompt,
                "salida": f"salida_{nombre}.json: un objeto por tema, con su «id» y los campos que pide el prompt",
                "catalogo": catalogo,
                "temas": [{k: getattr(t, k) for k in CAMPOS_TEMA_NUEVO}
                          | {"competencia_pisa": t.competencia_pisa, "microhabilidades": t.micro_pisa}
                          for t in sorted(temas, key=lambda t: t.id)]}
        p = d / f"lote_{nombre}.json"
        p.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        escritos.append(relativa(p))
    return escritos


def _comunes(s: dict) -> list[str]:
    errores = []
    if s.get("confianza") not in CONFIANZAS:
        errores.append(f"confianza inválida {s.get('confianza')!r}")
    if not s.get("justificacion") or len(s["justificacion"].split()) > 15:
        errores.append("justificación vacía o de más de 15 palabras")
    return errores


def _validar_timss(s: dict, codigos: set[str]) -> list[str]:
    obj1, obj2 = s.get("obj1") or "", s.get("obj2") or ""
    errores = _comunes(s)
    if obj1 != "FUERA" and obj1 not in codigos:
        errores.append(f"obj1 inválido {obj1!r}")
    if obj2 and (obj2 not in codigos or obj2 == obj1):
        errores.append(f"obj2 inválido {obj2!r}")
    return errores


def _validar_pisa(s: dict, catalogo: list[dict]) -> list[str]:
    de_tipo = {tipo: {e["codigo"] for e in catalogo if e["tipo"] == tipo}
               for tipo in ("contenido", "procedimental", "epistemico")}
    cont1, cont2 = s.get("cont1") or "", s.get("cont2") or ""
    errores = _comunes(s)
    if cont1 != "FUERA" and cont1 not in de_tipo["contenido"]:
        errores.append(f"cont1 inválido {cont1!r}")
    if cont2 and (cont2 not in de_tipo["contenido"] or cont2 == cont1):
        errores.append(f"cont2 inválido {cont2!r}")
    for campo, tipo in (("proc", "procedimental"), ("epis", "epistemico")):
        valores = s.get(campo)
        if not isinstance(valores, list) or len(valores) > 2 or set(valores) - de_tipo[tipo]:
            errores.append(f"{campo} inválido {valores!r}")
    for campo, validos in (("conocimiento", CONOCIMIENTOS), ("contexto", CONTEXTOS), ("area", AREAS),
                           ("demanda", DEMANDAS)):
        if s.get(campo) not in validos:
            errores.append(f"{campo} inválido {s.get(campo)!r}")
    return errores


def _validar_auss(s: dict, codigos: set[str]) -> list[str]:
    """Como _validar_timss, pero la justificación solo se exige no vacía (así se unió el lote de 2026-10-05)."""
    obj1, obj2 = s.get("obj1") or "", s.get("obj2") or ""
    errores = [] if s.get("confianza") in CONFIANZAS else [f"confianza inválida {s.get('confianza')!r}"]
    if not s.get("justificacion"):
        errores.append("sin justificación")
    if obj1 != "FUERA" and obj1 not in codigos:
        errores.append(f"obj1 inválido {obj1!r}")
    if obj2 and (obj2 not in codigos or obj2 == obj1):
        errores.append(f"obj2 inválido {obj2!r}")
    return errores


def errores_lote(lote: dict, salida: list[dict]) -> list[str]:
    """Errores de la salida de un lote de alineación (AUSS_*, TN_T*, TN_PISA*): los mismos que hacen fallar la unión
    (y que revisa `gskg lotes validar` al terminar el subagente alineador-marcos)."""
    por_id = {s.get("id"): s for s in salida}
    items = lote.get("items") or lote.get("temas") or []
    faltan = {i["id"] for i in items} - por_id.keys()
    errores = [f"faltan {len(faltan)} ids, p. ej. {sorted(faltan)[:3]}"] if faltan else []
    codigos = {o["codigo"] for o in lote["catalogo"]}
    for item in items:
        if not (s := por_id.get(item["id"])):
            continue
        if lote["lote"].startswith("TN_PISA"):
            malos = _validar_pisa(s, lote["catalogo"])
        elif lote["lote"].startswith("TN_"):
            malos = _validar_timss(s, codigos)
        else:
            malos = _validar_auss(s, codigos)
        errores += [f"{item['id']}: {e}" for e in malos]
    return errores


def unir_temas_nuevos() -> dict:
    """Valida las salidas de los lotes TN_* y escribe las capas de config/marcos.yaml
    (`timss2027_temas_nuevos`, `pisa2025_temas_nuevos`) con la forma de las clasificaciones previas.
    Lanza ValueError ante cualquier problema; devuelve los conteos."""
    d = ruta(DIR) / "lotes"
    por_tema = por_id_con_anteriores()   # los lotes de la V2 citan temas que la V3 ya no tiene (spec 15)
    clasif = cargar("marcos")["clasificaciones"]
    errores, capas = [], {}
    for prefijo, destino, campos in (("TN_T", "timss2027_temas_nuevos", ("obj1", "obj2")),
                                     ("TN_PISA", "pisa2025_temas_nuevos",
                                      ("cont1", "cont2", "conocimiento", "proc", "epis", "contexto", "area",
                                       "demanda"))):
        filas = []
        for p_lote in sorted(d.glob(f"lote_{prefijo}*.json")):
            lote = json.loads(p_lote.read_text(encoding="utf-8"))
            p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
            if not p_sal.exists():
                errores.append(f"falta {p_sal.name}")
                continue
            lista = json.loads(p_sal.read_text(encoding="utf-8"))
            errores += [f"{p_sal.name}: {e}" for e in errores_lote(lote, lista)]
            salida = {s.get("id"): s for s in lista}
            for item in lote["temas"]:
                if not (s := salida.get(item["id"])):
                    continue
                t = por_tema[item["id"]]
                filas.append({"id": t.id, "archivo": t.llave[0], "hoja": t.llave[1], "fila": t.llave[2],
                              "procedimental": t.procedimental, **{c: s.get(c, "") for c in campos},
                              "confianza": s.get("confianza"), "justificacion": s.get("justificacion"),
                              "version": lote["version"], "revisado_por": ""})
        capas[destino] = sorted(filas, key=lambda f: f["id"])
    if errores:
        raise ValueError(f"{len(errores)} errores al unir: " + "; ".join(errores[:15]))
    resumen = {}
    for destino, filas in capas.items():
        p = ruta(clasif[destino])
        p.write_text(json.dumps(filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        primero = "obj1" if destino.startswith("timss") else "cont1"
        resumen[destino] = {"temas": len(filas), "confianza": dict(Counter(f["confianza"] for f in filas)),
                            "fuera": sum(f[primero] == "FUERA" for f in filas)}
    legado.clasificacion_timss.cache_clear()
    legado.clasificacion_pisa.cache_clear()
    return resumen
