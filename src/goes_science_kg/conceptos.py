"""Capa de conceptos y prácticas (fase 3; skill grafo-conceptos).

Un CONCEPTO es una idea científica enseñable y evaluable («fotosíntesis», «modelo de partículas»,
«circuito en serie»). Una PRÁCTICA es una práctica científica transversal («controlar variables»,
«construir explicaciones con evidencia»). Ninguno es un tema ni una actividad.

Flujo (cada paso de IA lo hace un subagente; los pasos deterministas, este módulo):
1. preparar_vocabulario()  → data/interim/conceptos/insumos/<asignatura>.json  (objetivos de los marcos)
   subagente               → data/interim/conceptos/vocabulario_<asignatura>.json y practicas.json
2. preparar_etiquetado()   → data/interim/conceptos/lotes/lote_<asig>_G<grado>.json (temas + vocabulario)
   subagente               → salida_<asig>_G<grado>.json
                             [{id, conceptos[], practicas[], nuevos[], confianza, justificacion}]
3. unir_etiquetado()       → data/interim/conceptos/etiquetado_temas.json (validado: ids y códigos)

El grafo (grafo/construir.py) lee el vocabulario y el etiquetado consolidados.
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from functools import cache
from pathlib import Path

from goes_science_kg.config import cargar, ruta

DIR = "data/interim/conceptos"
VERSION_VOCABULARIO = "conceptos-v1"
VERSION_ETIQUETADO = "etiquetado-v1"
CONFIANZAS = {"alta", "media", "baja"}


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def _escribir(rel: str, datos) -> Path:
    p = ruta(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def _leer(rel: str):
    return json.loads(ruta(rel).read_text(encoding="utf-8"))


# -- 1. vocabulario -----------------------------------------------------------------------------
def preparar_vocabulario(nodos) -> list[str]:
    """Un insumo por asignatura con todos sus objetivos de marco (texto + subítems) y las unidades SV."""
    from goes_science_kg.modelos import TipoNodo

    escritos = []
    for asig in cargar("asignaturas")["asignaturas"]:
        objs = [n for n in nodos if n.tipo == TipoNodo.OBJETIVO_MARCO and n.asignatura == asig
                and n.props.get("marco") != "T23"]
        temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura == asig]
        unidades = Counter((t.grado, t.props.get("unidad")) for t in temas)
        insumo = {
            "asignatura": asig,
            "objetivos_marco": [{
                "codigo": o.id.removeprefix("OBJ:"), "marco": o.props["marco"], "texto": o.etiqueta,
                "area": o.props.get("area") or o.props.get("tema") or o.props.get("grupo"),
                "eje": o.props.get("eje"),
                "subitems": [s["texto"] for s in o.props.get("subitems", [])],
            } for o in sorted(objs, key=lambda x: x.id)],
            "unidades_malla_sv": [{"grado": g, "unidad": u, "temas": k} for (g, u), k in sorted(unidades.items())],
        }
        escritos.append(str(_escribir(f"{DIR}/insumos/{asig}.json", insumo).relative_to(ruta("."))))
    return escritos


@cache
def vocabulario() -> dict[str, dict]:
    """Conceptos consolidados (id → concepto), más los conceptos nuevos del triaje. Vacío si aún no existe."""
    p = ruta(f"{DIR}/vocabulario.json")
    voc = {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    for c in conceptos_del_triaje():
        voc.setdefault(c["id"], c)
    return voc


# -- Triaje de conceptos propuestos (capa sobre el etiquetado, como las revisiones) ----------------
# data/interim/conceptos/triaje_propuestos.json decide qué hacer con cada nombre que el etiquetado propuso:
# «nuevo» (entra al vocabulario), «sinonimo» (ya existe: concepto_id) o «descartar» (si es un detalle de un concepto,
# trae concepto_id). Se aplica al cargar, así que sobrevive a volver a correr unir-etiquetado. Las decisiones de
# confianza baja no se aplican (quedan para revisión humana).
VERSION_TRIAJE = "triaje-v1"


@cache
def triaje() -> list[dict]:
    p = ruta(f"{DIR}/triaje_propuestos.json")
    return [t for t in json.loads(p.read_text(encoding="utf-8")) if t.get("confianza") != "baja"] if p.exists() else []


def _id_triaje(t: dict) -> str | None:
    if t["decision"] == "nuevo":
        return f"CON:{t['asignatura']}/{slug(t['nombre'])}"
    return t.get("concepto_id")


@cache
def conceptos_del_triaje() -> tuple[dict, ...]:
    nuevos: dict[str, dict] = {}
    for t in triaje():
        if t["decision"] != "nuevo":
            continue
        c = nuevos.setdefault(_id_triaje(t), {
            "id": _id_triaje(t), "nombre": t["nombre"], "definicion": t["definicion"], "sinonimos": [],
            "objetivos_marco": [], "origen": "triaje", "nivel": None, "asignatura": t["asignatura"],
            "version": VERSION_TRIAJE, "prerrequisitos_sugeridos": []})
        c["sinonimos"] = sorted({*c["sinonimos"], *(x for x in t.get("agrupa", [t["propuesto"]]) if x != t["nombre"])})
        c["prerrequisitos_sugeridos"] = sorted({*c["prerrequisitos_sugeridos"], *t.get("prerrequisitos_sugeridos", [])})
    return tuple(nuevos[k] for k in sorted(nuevos))


def mapa_triaje() -> dict[str, str]:
    """Nombre propuesto → id de concepto (nuevo, sinónimo o concepto del que es un detalle)."""
    return {t["propuesto"]: cid for t in triaje() if (cid := _id_triaje(t))}


@cache
def equivalencias() -> list[dict]:
    """Pares de conceptos equivalentes entre asignaturas (misma idea en dos vocabularios)."""
    p = ruta(f"{DIR}/equivalencias.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


@cache
def practicas() -> dict[str, dict]:
    p = ruta(f"{DIR}/practicas.json")
    return {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def consolidar_vocabulario() -> dict:
    """Une vocabulario_<asig>.json en vocabulario.json, validando ids, asignaturas y códigos de marco."""
    from goes_science_kg.ingesta import legado

    codigos = ({o["codigo"] for o in legado.catalogo_timss2027()}
               | {o["codigo"] for o in legado.catalogo_timss_v1() if o["marco"] == "TA"}
               | {e["codigo"] for e in legado.catalogo_pisa2025()["elementos"]}
               | {o["codigo"] for o in legado.catalogo_acara_senior()})
    todos, errores = [], []
    for asig in cargar("asignaturas")["asignaturas"]:
        for c in _leer(f"{DIR}/vocabulario_{asig}.json"):
            if not c["id"].startswith(f"CON:{asig}/"):
                errores.append(f"{c['id']}: prefijo distinto de CON:{asig}/")
            if malos := [x for x in c.get("objetivos_marco", []) if x not in codigos]:
                errores.append(f"{c['id']}: códigos de marco inexistentes {malos}")
            if len(c.get("definicion", "").split()) > 30:
                errores.append(f"{c['id']}: definición de más de 30 palabras")
            todos.append({**c, "asignatura": asig, "version": VERSION_VOCABULARIO})
    if dup := [i for i, k in Counter(c["id"] for c in todos).items() if k > 1]:
        errores.append(f"ids duplicados: {dup[:10]}")
    for p in _leer(f"{DIR}/practicas.json"):
        if not p["id"].startswith("PRAC:"):
            errores.append(f"{p['id']}: práctica sin prefijo PRAC:")
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    _escribir(f"{DIR}/vocabulario.json", sorted(todos, key=lambda c: c["id"]))
    vocabulario.cache_clear()
    return dict(Counter(c["asignatura"] for c in todos))


# -- 2. etiquetado ------------------------------------------------------------------------------
def preparar_etiquetado(nodos) -> list[str]:
    """Un lote por asignatura y grado con los temas y el vocabulario de ESA asignatura + prácticas."""
    from goes_science_kg.modelos import TipoNodo

    voc, prac = vocabulario(), practicas()
    escritos = []
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura]
    for asig, grado in sorted({(t.asignatura, t.grado) for t in temas}):
        lote = {
            "lote": f"{asig}_G{grado:02d}", "version": VERSION_ETIQUETADO,
            "instrucciones": "prompts/etiquetar_conceptos.md",
            "vocabulario": [{k: c[k] for k in ("id", "nombre", "definicion")} for c in voc.values()
                            if c["asignatura"] == asig],
            "practicas": [{k: p[k] for k in ("id", "nombre")} for p in prac.values()],
            "items": [{"id": t.id.removeprefix("TEMA:"), "unidad": t.props.get("unidad"),
                       "contenido": t.props.get("contenido"), "procedimental": t.etiqueta,
                       "indicador": t.props.get("indicador")}
                      for t in sorted(temas, key=lambda x: x.id) if t.asignatura == asig and t.grado == grado],
        }
        escritos.append(str(_escribir(f"{DIR}/lotes/lote_{lote['lote']}.json", lote).relative_to(ruta("."))))
    return escritos


def unir_etiquetado() -> dict:
    voc, prac = vocabulario(), practicas()
    filas, errores, nuevos = [], [], Counter()
    for p_lote in sorted(ruta(f"{DIR}/lotes").glob("lote_*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        salida = {s["id"]: s for s in json.loads(p_sal.read_text(encoding="utf-8"))}
        if faltan := {i["id"] for i in lote["items"]} - salida.keys():
            errores.append(f"{p_sal.name}: faltan {sorted(faltan)[:3]}")
        for item in lote["items"]:
            s = salida.get(item["id"])
            if not s:
                continue
            if malos := [c for c in s.get("conceptos", []) if c not in voc]:
                errores.append(f"{item['id']}: conceptos inexistentes {malos}")
            if malos := [c for c in s.get("practicas", []) if c not in prac]:
                errores.append(f"{item['id']}: prácticas inexistentes {malos}")
            if not s.get("conceptos") and not s.get("practicas"):
                errores.append(f"{item['id']}: sin conceptos ni prácticas")
            if s.get("confianza") not in CONFIANZAS:
                errores.append(f"{item['id']}: confianza inválida")
            for n in s.get("nuevos", []):
                nuevos[n] += 1
            filas.append({"id": item["id"], "conceptos": s.get("conceptos", []), "practicas": s.get("practicas", []),
                          "nuevos": s.get("nuevos", []), "confianza": s.get("confianza"),
                          "justificacion": s.get("justificacion"), "version": lote["version"]})
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    _escribir(f"{DIR}/etiquetado_temas.json", sorted(filas, key=lambda f: f["id"]))
    _escribir(f"{DIR}/conceptos_propuestos.json", sorted(nuevos.items(), key=lambda x: (-x[1], x[0])))
    return {"temas": len(filas), "confianza": dict(Counter(f["confianza"] for f in filas)),
            "conceptos_propuestos": len(nuevos)}


@cache
def etiquetado() -> dict[str, dict]:
    """Etiquetado de temas; los nombres «nuevos» resueltos por el triaje se suman como conceptos secundarios."""
    p = ruta(f"{DIR}/etiquetado_temas.json")
    filas = {f["id"]: f for f in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    mapa, voc = mapa_triaje(), vocabulario()
    for f in filas.values():
        extra = [c for n in f.get("nuevos", []) if (c := mapa.get(n)) in voc and c not in f["conceptos"]]
        if extra:
            f["conceptos"] = f["conceptos"] + sorted(set(extra), key=extra.index)
            f["conceptos_triaje"] = sorted(set(extra))
    return filas


# -- 2-bis. etiquetado directo de objetivos de países --------------------------------------------
# Más preciso que heredar conceptos vía el objetivo de marco (spec 09, «Limitaciones»).
def preparar_etiquetado_paises(nodos, por_lote: int = 70, solo_pendientes: bool = True) -> list[str]:
    """Lotes por país. Con solo_pendientes, únicamente los objetivos aún sin etiquetar (p. ej. un país nuevo)."""
    from goes_science_kg.modelos import TipoNodo

    voc, prac = vocabulario(), practicas()
    hechos = set(etiquetado_paises()) if solo_pendientes else set()
    ops = sorted((n for n in nodos if n.tipo == TipoNodo.OBJETIVO_PAIS and n.id.removeprefix("OP:") not in hechos),
                 key=lambda n: n.id)
    escritos = []
    for pais in sorted({n.props["pais"] for n in ops}):
        items = [n for n in ops if n.props["pais"] == pais]
        # La numeración sigue tras los lotes existentes: reutilizar un número dejaría su salida_ desalineada.
        previos = [int(p.stem.rsplit("_", 1)[1]) for p in ruta(f"{DIR}/lotes_paises").glob(f"lote_PAIS_{pais}_*.json")]
        base = max(previos, default=0) if solo_pendientes else 0
        for i in range(0, len(items), por_lote):
            lote = {
                "lote": f"PAIS_{pais}_{base + i // por_lote + 1}", "version": "etiquetado-paises-v1",
                "instrucciones": "prompts/etiquetar_conceptos.md (los ítems son objetivos de un país, no temas)",
                "vocabulario": [{k: c[k] for k in ("id", "nombre", "definicion")} | {"asignatura": c["asignatura"]}
                                for c in voc.values()],
                "practicas": [{k: p[k] for k in ("id", "nombre")} for p in prac.values()],
                "items": [{"id": n.id.removeprefix("OP:"), "texto": n.etiqueta, "eje": n.props.get("eje"),
                           "grado_o_tramo": n.props.get("grado_o_tramo"), "asignatura_estimada": n.asignatura}
                          for n in items[i:i + por_lote]],
            }
            escritos.append(str(_escribir(f"{DIR}/lotes_paises/lote_{lote['lote']}.json", lote).relative_to(ruta("."))))
    return escritos


def unir_etiquetado_paises() -> dict:
    voc, prac = vocabulario(), practicas()
    filas, errores = [], []
    for p_lote in sorted(ruta(f"{DIR}/lotes_paises").glob("lote_*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        salida = {s["id"]: s for s in json.loads(p_sal.read_text(encoding="utf-8"))}
        for item in lote["items"]:
            s = salida.get(item["id"])
            if not s:
                errores.append(f"{p_sal.name}: falta {item['id']}")
                continue
            if malos := [c for c in s.get("conceptos", []) + s.get("practicas", []) if c not in voc and c not in prac]:
                errores.append(f"{item['id']}: ids inexistentes {malos}")
            if s.get("confianza") not in CONFIANZAS:
                errores.append(f"{item['id']}: confianza inválida")
            filas.append({"id": item["id"], "conceptos": s.get("conceptos", []), "practicas": s.get("practicas", []),
                          "confianza": s.get("confianza"), "justificacion": s.get("justificacion"),
                          "version": lote["version"]})
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    _escribir(f"{DIR}/etiquetado_paises.json", sorted(filas, key=lambda f: f["id"]))
    return {"objetivos": len(filas), "confianza": dict(Counter(f["confianza"] for f in filas)),
            "sin_concepto": sum(not f["conceptos"] for f in filas)}


@cache
def etiquetado_paises() -> dict[str, dict]:
    """Etiquetado de objetivos de países, más los conceptos del triaje (etiquetado_paises_triaje.json)."""
    p = ruta(f"{DIR}/etiquetado_paises.json")
    filas = {f["id"]: f for f in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    pt, voc = ruta(f"{DIR}/etiquetado_paises_triaje.json"), vocabulario()
    for r in json.loads(pt.read_text(encoding="utf-8")) if pt.exists() else []:
        f = filas.get(r["id"])
        extra = [c for c in r["conceptos"] if c in voc and f and c not in f["conceptos"]]
        if extra:
            f["conceptos"] = f["conceptos"] + extra
            f["conceptos_triaje"] = sorted(extra)
    return filas
