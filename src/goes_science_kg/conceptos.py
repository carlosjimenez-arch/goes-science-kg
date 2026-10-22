"""Manage curriculum concepts and scientific practices."""

# Historical implementation notes:
# Un CONCEPTO es una idea científica enseñable y evaluable («fotosíntesis», «modelo de partículas»,
# «circuito en serie»). Una PRÁCTICA es una práctica científica transversal («controlar variables»,
# «construir explicaciones con evidencia»). Ninguno es un tema ni una actividad.
#
# Flujo (cada paso de IA lo hace un subagente; los pasos deterministas, este módulo):
# 1. preparar_vocabulario()  → data/interim/conceptos/insumos/<asignatura>.json  (objetivos de los marcos)
#    subagente               → data/interim/conceptos/vocabulario_<asignatura>.json y practicas.json
# 2. preparar_etiquetado()   → data/interim/conceptos/lotes/lote_<asig>_G<grado>.json (temas + vocabulario)
#    subagente               → salida_<asig>_G<grado>.json
#                              [{id, conceptos[], practicas[], nuevos[], confianza, justificacion}]
# 3. unir_etiquetado()       → data/interim/conceptos/etiquetado_temas.json (validado: ids y códigos)
#
# El grafo (grafo/construir.py) lee el vocabulario y el etiquetado consolidados.

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from functools import cache
from pathlib import Path

from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.ingesta import legado
from goes_science_kg.modelos import Nodo, TipoNodo

DIR = "data/interim/conceptos"
VERSION_VOCABULARIO = "conceptos-v1"
VERSION_ETIQUETADO = "etiquetado-v1"
CONFIANZAS = {"alta", "media", "baja"}


def slug(texto: str) -> str:
    """Create a bounded lowercase ASCII slug using hyphen-separated tokens."""
    t = unicodedata.normalize("NFKD", texto.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")[:60]


def _escribir(rel: str, datos: object) -> Path:
    p = ruta(rel)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return p


def _leer(rel: str):
    return json.loads(ruta(rel).read_text(encoding="utf-8"))


# -- 1. vocabulario -----------------------------------------------------------------------------
def preparar_vocabulario(nodos: list[Nodo]) -> list[str]:
    """Prepare each subject's framework objectives and local units for vocabulary design."""

    escritos = []
    for asig in cargar("asignaturas")["asignaturas"]:
        objs = [
            n
            for n in nodos
            if n.tipo == TipoNodo.OBJETIVO_MARCO and n.asignatura == asig and n.props.get("marco") != "T23"
        ]
        temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura == asig]
        unidades = Counter((t.grado, t.props.get("unidad")) for t in temas)
        insumo = {
            "asignatura": asig,
            "objetivos_marco": [
                {
                    "codigo": o.id.removeprefix("OBJ:"),
                    "marco": o.props["marco"],
                    "texto": o.etiqueta,
                    "area": o.props.get("area") or o.props.get("tema") or o.props.get("grupo"),
                    "eje": o.props.get("eje"),
                    "subitems": [s["texto"] for s in o.props.get("subitems", [])],
                }
                for o in sorted(objs, key=lambda x: x.id)
            ],
            "unidades_malla_sv": [{"grado": g, "unidad": u, "temas": k} for (g, u), k in sorted(unidades.items())],
        }
        escritos.append(relativa(_escribir(f"{DIR}/insumos/{asig}.json", insumo)))
    return escritos


@cache
def vocabulario() -> dict[str, dict]:
    """Load consolidated vocabulary and explicitly admitted triage concepts."""
    p = ruta(f"{DIR}/vocabulario.json")
    voc = {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    for c in conceptos_del_triaje():
        voc.setdefault(c["id"], c)
    for d in divisiones():
        if d["concepto"] in voc:
            voc[d["concepto"]] = {**voc[d["concepto"]], **d["redefinir"]}
            voc.setdefault(
                d["nuevo"]["id"],
                {
                    "sinonimos": [],
                    "objetivos_marco": [],
                    "origen": "division",
                    "version": VERSION_DIVISION,
                    **d["nuevo"],
                },
            )
    return voc


# -- Divisiones de conceptos (capa de decisión, como el triaje) ------------------------------------
# data/interim/conceptos/divisiones.json parte un concepto que mezclaba dos ideas: redefine el original, crea el nuevo,
# reasigna cada elemento etiquetado con el original (asignaciones explícitas por conjunto) y ajusta sus prerrequisitos.
# Se aplica al cargar, así que sobrevive a volver a correr el etiquetado.
VERSION_DIVISION = "division-v1"


@cache
def divisiones() -> tuple[dict, ...]:
    """Load cached concept-splitting decisions or return an empty collection."""
    p = ruta(f"{DIR}/divisiones.json")
    return tuple(json.loads(p.read_text(encoding="utf-8"))["divisiones"]) if p.exists() else ()


def aplicar_divisiones(conjunto: str, item: str, ids: list[str]) -> list[str]:
    """Replace split concepts using the explicit item-specific allocation decision."""

    # Implementation notes:
    # (malla_v1, objetivos_pais, internacional o malla_v2), en la misma posición. Sin asignación, no cambia nada.
    for d in divisiones():
        if d["concepto"] in ids and (nuevos := d["asignaciones"].get(conjunto, {}).get(item)):
            i = ids.index(d["concepto"])
            ids = list(dict.fromkeys([*ids[:i], *nuevos, *ids[i + 1 :]]))
    return ids


# -- Triaje de conceptos propuestos (capa sobre el etiquetado, como las revisiones) ----------------
# data/interim/conceptos/triaje_propuestos.json decide qué hacer con cada nombre que el etiquetado propuso:
# «nuevo» (entra al vocabulario), «sinonimo» (ya existe: concepto_id) o «descartar» (si es un detalle de un concepto,
# trae concepto_id). Se aplica al cargar, así que sobrevive a volver a correr unir-etiquetado. Las decisiones de
# confianza baja no se aplican (quedan para revisión humana).
VERSION_TRIAJE = "triaje-v1"


@cache
def triaje() -> list[dict]:
    """Load concept-triage decisions while excluding low-confidence proposals."""
    p = ruta(f"{DIR}/triaje_propuestos.json")
    return [t for t in json.loads(p.read_text(encoding="utf-8")) if t.get("confianza") != "baja"] if p.exists() else []


def _id_triaje(t: dict) -> str | None:
    if t["decision"] == "nuevo":
        return f"CON:{t['asignatura']}/{slug(t['nombre'])}"
    return t.get("concepto_id")


@cache
def conceptos_del_triaje() -> tuple[dict, ...]:
    """Return triage-approved new concepts with synonyms and suggested prerequisites."""

    # Implementation notes:
    # acumulados; ordenados por id y con caché.
    nuevos: dict[str, dict] = {}
    for t in triaje():
        if t["decision"] != "nuevo":
            continue
        c = nuevos.setdefault(
            _id_triaje(t),
            {
                "id": _id_triaje(t),
                "nombre": t["nombre"],
                "definicion": t["definicion"],
                "sinonimos": [],
                "objetivos_marco": [],
                "origen": "triaje",
                "nivel": None,
                "asignatura": t["asignatura"],
                "version": VERSION_TRIAJE,
                "prerrequisitos_sugeridos": [],
            },
        )
        c["sinonimos"] = sorted({*c["sinonimos"], *(x for x in t.get("agrupa", [t["propuesto"]]) if x != t["nombre"])})
        c["prerrequisitos_sugeridos"] = sorted({*c["prerrequisitos_sugeridos"], *t.get("prerrequisitos_sugeridos", [])})
    return tuple(nuevos[k] for k in sorted(nuevos))


def mapa_triaje() -> dict[str, str]:
    """Map proposed names to their resolved concept identities."""
    return {t["propuesto"]: cid for t in triaje() if (cid := _id_triaje(t))}


@cache
def equivalencias() -> list[dict]:
    """Load explicit cross-subject concept equivalence pairs."""
    p = ruta(f"{DIR}/equivalencias.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def partes() -> list[dict]:
    """Load directional part-of decisions used by the historical international contrast."""

    # Implementation notes:
    # enseñar el todo, no al revés (la conservación de la energía mecánica es parte de la conservación de la energía).
    # Solo las usa el contraste internacional con doble lectura (spec 12).
    p = ruta(f"{DIR}/partes.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


@cache
def practicas() -> dict[str, dict]:
    """Load cached scientific practices or return an empty collection."""
    p = ruta(f"{DIR}/practicas.json")
    return {c["id"]: c for c in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def consolidar_vocabulario() -> dict:
    """Validate and merge subject vocabularies and framework codes."""

    codigos = (
        {o["codigo"] for o in legado.catalogo_timss2027()}
        | {o["codigo"] for o in legado.catalogo_timss_v1() if o["marco"] == "TA"}
        | {e["codigo"] for e in legado.catalogo_pisa2025()["elementos"]}
        | {o["codigo"] for o in legado.catalogo_acara_senior()}
    )
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
    errores.extend(
        f"{p['id']}: práctica sin prefijo PRAC:"
        for p in _leer(f"{DIR}/practicas.json")
        if not p["id"].startswith("PRAC:")
    )
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    _escribir(f"{DIR}/vocabulario.json", sorted(todos, key=lambda c: c["id"]))
    vocabulario.cache_clear()
    etiquetado.cache_clear()  # filtran contra el vocabulario
    etiquetado_paises.cache_clear()
    return dict(Counter(c["asignatura"] for c in todos))


# -- 2. etiquetado ------------------------------------------------------------------------------
def preparar_etiquetado(
    nodos: list[Nodo], solo_pendientes: bool = True, reetiquetar: frozenset[str] = frozenset()
) -> list[str]:
    """Prepare grade-specific topic tagging without overwriting completed batches."""

    # Implementation notes:
    # Con solo_pendientes, únicamente los temas sin etiquetar que tampoco están ya en un lote (p. ej. los que agregó
    # la V2), en lotes `<asig>_G<gg>_<n>` numerados tras los existentes; así no se reescriben lotes que ya tienen
    # salida y correrlo dos veces es seguro. Sin él, se rehacen los lotes base `<asig>_G<gg>`.
    #
    # `reetiquetar` (spec 15): ids que se vuelven a etiquetar aunque ya tengan etiqueta (los temas de la V3 que
    # cambiaron), en lotes `<asig>_G<gg>_V3[_<n>]`; como se unen después de los anteriores, su etiqueta gana.

    voc, prac = vocabulario(), practicas()
    escritos = []
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.asignatura]
    existentes = sorted(ruta(f"{DIR}/lotes").glob("lote_*.json"))
    if solo_pendientes:
        en_lote = {p.stem: {i["id"] for i in json.loads(p.read_text(encoding="utf-8"))["items"]} for p in existentes}
        hechos = set(etiquetado()) | set().union(*en_lote.values())
        en_v3 = set().union(*(ids for n, ids in en_lote.items() if "_V3" in n))
        temas = [
            t for t in temas if (i := t.id.removeprefix("TEMA:")) not in hechos or (i in reetiquetar and i not in en_v3)
        ]
    for asig, grado in sorted({(t.asignatura, t.grado) for t in temas}):
        nombre = f"{asig}_G{grado:02d}"
        if solo_pendientes and reetiquetar:
            previos = sum(1 for p in existentes if p.stem.startswith(f"lote_{nombre}_V3"))
            nombre += "_V3" + (f"_{previos + 1}" if previos else "")
        elif solo_pendientes:
            nombre += f"_{sum(1 for p in existentes if p.stem.startswith(f'lote_{nombre}')) + 1}"
        lote = {
            "lote": nombre,
            "version": VERSION_ETIQUETADO,
            "instrucciones": "prompts/etiquetar_conceptos.md",
            "vocabulario": [
                {k: c[k] for k in ("id", "nombre", "definicion")} for c in voc.values() if c["asignatura"] == asig
            ],
            "practicas": [{k: p[k] for k in ("id", "nombre")} for p in prac.values()],
            "items": [
                {
                    "id": t.id.removeprefix("TEMA:"),
                    "unidad": t.props.get("unidad"),
                    "contenido": t.props.get("contenido"),
                    "subcontenido": t.props.get("subcontenido"),
                    "procedimental": t.etiqueta,
                    "indicador": t.props.get("indicador"),
                }
                for t in sorted(temas, key=lambda x: x.id)
                if t.asignatura == asig and t.grado == grado
            ],
        }
        escritos.append(relativa(_escribir(f"{DIR}/lotes/lote_{lote['lote']}.json", lote)))
    return escritos


def errores_lote_temas(lote: dict, salida: list[dict]) -> list[str]:
    """Return topic-batch errors under the same rules used by consolidation."""

    # Implementation notes:
    # `gskg lotes validar` al terminar el subagente etiquetador-conceptos).
    voc, prac = vocabulario(), practicas()
    por_id = {s.get("id"): s for s in salida}
    faltan = {i["id"] for i in lote["items"]} - por_id.keys()
    errores = [f"faltan {sorted(faltan)[:3]}"] if faltan else []
    for item in lote["items"]:
        if not (s := por_id.get(item["id"])):
            continue
        if malos := [c for c in s.get("conceptos", []) if c not in voc]:
            errores.append(f"{item['id']}: conceptos inexistentes {malos}")
        if malos := [c for c in s.get("practicas", []) if c not in prac]:
            errores.append(f"{item['id']}: prácticas inexistentes {malos}")
        if not s.get("conceptos") and not s.get("practicas"):
            errores.append(f"{item['id']}: sin conceptos ni prácticas")
        if s.get("confianza") not in CONFIANZAS:
            errores.append(f"{item['id']}: confianza inválida")
    return errores


def unir_etiquetado() -> dict:
    """Validate topic-tagging outputs and write labels and proposed concepts."""

    # Implementation notes:
    # (nombres nuevos por frecuencia). Lanza ValueError si hay errores; devuelve los conteos.
    filas: dict[str, dict] = {}  # un id etiquetado en varios lotes: gana el último (los «_V3» van después)
    errores, nuevos = [], Counter()
    for p_lote in sorted(ruta(f"{DIR}/lotes").glob("lote_*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        lista = json.loads(p_sal.read_text(encoding="utf-8"))
        errores += [f"{p_sal.name}: {e}" for e in errores_lote_temas(lote, lista)]
        salida = {s["id"]: s for s in lista}
        for item in lote["items"]:
            s = salida.get(item["id"])
            if not s:
                continue
            for n in s.get("nuevos", []):
                nuevos[n] += 1
            filas[item["id"]] = {
                "id": item["id"],
                "conceptos": s.get("conceptos", []),
                "practicas": s.get("practicas", []),
                "nuevos": s.get("nuevos", []),
                "confianza": s.get("confianza"),
                "justificacion": s.get("justificacion"),
                "version": lote["version"],
            }
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    _escribir(f"{DIR}/etiquetado_temas.json", sorted(filas.values(), key=lambda f: f["id"]))
    _escribir(f"{DIR}/conceptos_propuestos.json", sorted(nuevos.items(), key=lambda x: (-x[1], x[0])))
    etiquetado.cache_clear()
    return {
        "temas": len(filas),
        "confianza": dict(Counter(f["confianza"] for f in filas.values())),
        "conceptos_propuestos": len(nuevos),
    }


@cache
def etiquetado() -> dict[str, dict]:
    """Load topic labels and add triage-resolved concepts as secondary labels."""
    p = ruta(f"{DIR}/etiquetado_temas.json")
    filas = {f["id"]: f for f in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    mapa, voc = mapa_triaje(), vocabulario()
    for f in filas.values():
        f["conceptos"] = aplicar_divisiones("malla_v1", f["id"], f["conceptos"])
        extra = [c for n in f.get("nuevos", []) if (c := mapa.get(n)) in voc and c not in f["conceptos"]]
        if extra:
            f["conceptos"] = f["conceptos"] + sorted(set(extra), key=extra.index)
            f["conceptos_triaje"] = sorted(set(extra))
    # Spec 15: un tema de la V2 que la V3 fusionó en otro le suma sus conceptos, como secundarios, al que lo contiene.
    from goes_science_kg.ingesta.mallas import absorbidos

    for previo, absorbe in sorted(absorbidos().items()):
        if previo in filas and absorbe in filas:
            f = filas[absorbe]
            if extra := [c for c in filas[previo]["conceptos"] if c not in f["conceptos"]]:
                f["conceptos"] = f["conceptos"] + extra
                f["conceptos_absorbidos"] = sorted({*f.get("conceptos_absorbidos", []), *extra})
    return filas


# -- 2-bis. etiquetado directo de objetivos de países --------------------------------------------
# Más preciso que heredar conceptos vía el objetivo de marco (spec 09, «Limitaciones»).
def preparar_etiquetado_paises(nodos: list[Nodo], por_lote: int = 70, solo_pendientes: bool = True) -> list[str]:
    """Prepare country tagging batches, optionally limited to untagged objectives."""

    voc, prac = vocabulario(), practicas()
    hechos = set(etiquetado_paises()) if solo_pendientes else set()
    ops = sorted(
        (n for n in nodos if n.tipo == TipoNodo.OBJETIVO_PAIS and n.id.removeprefix("OP:") not in hechos),
        key=lambda n: n.id,
    )
    escritos = []
    for pais in sorted({n.props["pais"] for n in ops}):
        items = [n for n in ops if n.props["pais"] == pais]
        d = ruta(f"{DIR}/lotes_paises")
        existentes = sorted(d.glob(f"lote_PAIS_{pais}_*.json"))
        if solo_pendientes:
            # La numeración sigue tras los lotes existentes (reutilizar un número dejaría su salida_ desalineada) y
            # no se repiten objetivos que ya están en un lote aunque aún no tengan salida (correr dos veces es seguro).
            en_lotes = {i["id"] for p in existentes for i in json.loads(p.read_text(encoding="utf-8"))["items"]}
            items = [n for n in items if n.id.removeprefix("OP:") not in en_lotes]
            base = max((int(m.group(1)) for p in existentes if (m := re.search(r"_(\d+)$", p.stem))), default=0)
        else:
            # Regeneración completa: se borran los lotes y salidas del país para no mezclar con los nuevos.
            for p in existentes + sorted(d.glob(f"salida_PAIS_{pais}_*.json")):
                p.unlink()
            base = 0
        for i in range(0, len(items), por_lote):
            lote = {
                "lote": f"PAIS_{pais}_{base + i // por_lote + 1}",
                "version": "etiquetado-paises-v1",
                "instrucciones": "prompts/etiquetar_conceptos.md (los ítems son objetivos de un país, no temas)",
                "vocabulario": [
                    {k: c[k] for k in ("id", "nombre", "definicion")} | {"asignatura": c["asignatura"]}
                    for c in voc.values()
                ],
                "practicas": [{k: p[k] for k in ("id", "nombre")} for p in prac.values()],
                "items": [
                    {
                        "id": n.id.removeprefix("OP:"),
                        "texto": n.etiqueta,
                        "eje": n.props.get("eje"),
                        "grado_o_tramo": n.props.get("grado_o_tramo"),
                        "asignatura_estimada": n.asignatura,
                    }
                    for n in items[i : i + por_lote]
                ],
            }
            escritos.append(relativa(_escribir(f"{DIR}/lotes_paises/lote_{lote['lote']}.json", lote)))
    return escritos


def errores_lote_paises(lote: dict, salida: list[dict]) -> list[str]:
    """Return country-objective batch errors under the consolidation contract."""
    voc, prac = vocabulario(), practicas()
    por_id = {s.get("id"): s for s in salida}
    errores = []
    for item in lote["items"]:
        if not (s := por_id.get(item["id"])):
            errores.append(f"falta {item['id']}")
            continue
        if malos := [c for c in s.get("conceptos", []) + s.get("practicas", []) if c not in voc and c not in prac]:
            errores.append(f"{item['id']}: ids inexistentes {malos}")
        if s.get("confianza") not in CONFIANZAS:
            errores.append(f"{item['id']}: confianza inválida")
    return errores


def unir_etiquetado_paises() -> dict:
    """Validate and merge country labels under the documented duplicate-resolution rule."""

    # Implementation notes:
    # Lanza ValueError si hay errores; devuelve los conteos.
    filas, errores = [], []
    for p_lote in sorted(ruta(f"{DIR}/lotes_paises").glob("lote_*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        lista = json.loads(p_sal.read_text(encoding="utf-8"))
        errores += [f"{p_sal.name}: {e}" for e in errores_lote_paises(lote, lista)]
        salida = {s["id"]: s for s in lista}
        for item in lote["items"]:
            if not (s := salida.get(item["id"])):
                continue
            filas.append(
                {
                    "id": item["id"],
                    "conceptos": s.get("conceptos", []),
                    "practicas": s.get("practicas", []),
                    "confianza": s.get("confianza"),
                    "justificacion": s.get("justificacion"),
                    "version": lote["version"],
                }
            )
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    filas = list({f["id"]: f for f in filas}.values())  # un id repetido entre lotes: gana el último
    _escribir(f"{DIR}/etiquetado_paises.json", sorted(filas, key=lambda f: f["id"]))
    etiquetado_paises.cache_clear()
    return {
        "objetivos": len(filas),
        "confianza": dict(Counter(f["confianza"] for f in filas)),
        "sin_concepto": sum(not f["conceptos"] for f in filas),
    }


@cache
def etiquetado_paises() -> dict[str, dict]:
    """Load country-objective labels and explicit triage additions."""
    p = ruta(f"{DIR}/etiquetado_paises.json")
    filas = {f["id"]: f for f in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}
    for f in filas.values():
        f["conceptos"] = aplicar_divisiones("objetivos_pais", f["id"], f["conceptos"])
    pt, voc = ruta(f"{DIR}/etiquetado_paises_triaje.json"), vocabulario()
    for r in json.loads(pt.read_text(encoding="utf-8")) if pt.exists() else []:
        f = filas.get(r["id"])
        extra = [c for c in r["conceptos"] if c in voc and f and c not in f["conceptos"]]
        if extra:
            f["conceptos"] = f["conceptos"] + extra
            f["conceptos_triaje"] = sorted(extra)
    return filas
