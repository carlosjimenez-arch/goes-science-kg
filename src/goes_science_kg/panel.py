"""Panel de expertos IA (spec 14): revisión técnica interina de las decisiones que esperaban al MINED.

Cinco roles (config/panel.yaml): un experto en la didáctica de cada ciencia y un psicopedagogo. Dictaminan
«expedientes»: las decisiones de contenido pendientes, las asignaciones de una división de concepto, los cambios de
asignatura, la capa pedagógica, los hallazgos verificados, las acciones de las propuestas que la V2 no adoptó y las
decisiones del piloto. Sus dictámenes NO son confirmaciones del MINED: quedan registrados como «dictamen del panel»,
con su evidencia, y el MINED o el responsable del proyecto pueden confirmarlos o revertirlos.

Circuito (el de todos los lotes del proyecto):
  preparar(ronda) → data/interim/panel/lotes/lote_r<n>_<rol>[_<k>].json: lo que ese rol dictamina en esa ronda
  subagente <rol> → salida_r<n>_<rol>[_<k>].json: un dictamen por expediente (validado por el hook SubagentStop)
  consolidar(ronda) → data/interim/panel/estado.json: dictámenes, etapa y estado de cada expediente
  aplicar() → escribe lo resuelto en las capas, con su procedencia; informe() → panel/DICTAMEN.md

Regla de consolidación (determinista):
- Expedientes en paralelo (todos menos «contenido»): se resuelven con unanimidad de los roles requeridos y confianza
  media o alta. Si no, una ronda de deliberación en la que cada rol ve los dictámenes de los demás; si sigue sin
  unanimidad, «sin consenso»: queda para una decisión humana.
- Contenido (capa pedagógica), en secuencia: el experto de la disciplina revisa la exactitud científica; el
  psicopedagogo revisa la versión resultante (edad, lenguaje, carga cognitiva, evaluación); si el psicopedagogo la
  corrige, el experto da el visto bueno final a la exactitud. Una confianza baja deja el elemento sin consenso.
- Piloto: el panel asesora; decide el responsable del proyecto (aprendizaje/PILOTO.md).
"""

from __future__ import annotations

import copy
import json
import re
from collections import Counter, defaultdict
from datetime import date
from functools import cache
from pathlib import Path

from goes_science_kg import conceptos
from goes_science_kg.config import cargar, relativa, ruta

DIR = "data/interim/panel"
VERSION = "panel-v1"
PESO_MAX_LOTE = 36   # carga de un lote; un expediente pesa según cuánto hay que leer y verificar
PESO = {"asignacion": 0.3, "cambio_asignatura": 0.5, "decision": 1, "hallazgo": 1, "propuesta": 1, "piloto": 2,
        "contenido": 1.2}
CONFIANZAS = ("alta", "media", "baja")
REQUIERE_TEXTO = {"rechazar": "alternativa", "matizar": "texto", "no_respaldar": "alternativa", "adaptar": "texto",
                  "recomendar": "recomendacion"}
ROL_DE = {"biologia": "experto-biologia", "fisica": "experto-fisica", "quimica": "experto-quimica",
          "ciencias_tierra_espacio": "experto-tierra-espacio", "tierra_espacio": "experto-tierra-espacio"}


def config() -> dict:
    return cargar("panel")


def _palabras(s: str | None) -> int:
    return len((s or "").split())


def _asig(cid: str) -> str:
    voc = conceptos.vocabulario()
    return voc.get(cid, {}).get("asignatura") or cid.removeprefix("CON:").split("/")[0]


def _rol(cid_o_asig: str) -> str:
    a = _asig(cid_o_asig) if cid_o_asig.startswith("CON:") else cid_o_asig
    return ROL_DE.get(a, "experto-quimica")


def _concepto(cid: str) -> dict:
    c = conceptos.vocabulario().get(cid, {})
    return {"id": cid, "nombre": c.get("nombre", cid), "definicion": c.get("definicion"),
            "asignatura": c.get("asignatura")}


# -- expedientes ----------------------------------------------------------------------------------------------------
def _contraste(tramo: str) -> dict[str, dict]:
    p = ruta("internacional/2_8/contraste.json" if tramo == "2_8" else "internacional/contraste.json")
    filas = json.loads(p.read_text(encoding="utf-8"))["filas"] if p.exists() else []
    return {f["concepto"]: f for f in filas}


def _resumen_contraste(f: dict | None) -> dict | None:
    if not f:
        return None
    return {"clase_automatica": f.get("clase_ia", f["clase"]), "lecturas": f.get("lecturas"),
            "sv_primer_grado": f["sv_primer_grado"], "sv_temas": f["sv_temas"][:5],
            "grado_consenso": f["grado_consenso"], "mediana_paises": f["mediana_primer_grado_nucleo"],
            "paises_nucleo": {p: d["primer_grado_nucleo"] for p, d in sorted(f["paises"].items())}}


def _exp_decisiones() -> dict[str, dict]:
    from goes_science_kg import revision_decisiones as rd

    contrastes = {"clase_internacional": _contraste("9_11"), "clase_internacional_2_8": _contraste("2_8")}
    salida = {}
    for tipo, (clave, descripcion, campo_just, campo_quien) in rd.DESCRIPCION.items():
        for r in rd._leer(tipo):
            involucrados = {"equivalencia_retirada": [r.get("a"), r.get("b")],
                            "prerrequisito_rechazado": [r.get("origen"), r.get("destino")],
                            "division": [r.get("concepto")], "parte_de": [r.get("parte"), r.get("todo")]
                            }.get(tipo, [r.get("concepto")])
            roles = sorted({_rol(c) for c in involucrados if c})
            if tipo in config()["tipos"]["decision"]["psicopedagogo"]:
                roles.append("psicopedagogo")
            datos = {"decision_tomada": descripcion(r), "justificacion": r.get(campo_just, ""),
                     "decidido_por": r.get(campo_quien, ""), "conceptos": [_concepto(c) for c in involucrados if c]}
            if tipo == "division":
                datos |= {"redefinir": r.get("redefinir"), "nuevo": r.get("nuevo")}
            if tipo in contrastes:
                datos["contraste"] = _resumen_contraste(contrastes[tipo].get(r["concepto"]))
            salida[f"DEC:{tipo}:{clave(r)}"] = {
                "tipo": "decision", "subtipo": tipo, "titulo": descripcion(r), "roles": roles, "datos": datos,
                "pregunta": "¿El panel respalda esta decisión del equipo GOES con criterio técnico? Si la rechaza, "
                            "propone la alternativa."}
    return salida


def _exp_asignaciones() -> dict[str, dict]:
    from goes_science_kg import revision_decisiones as rd

    textos, salida = rd._textos(), {}
    for d in rd._leer("division"):
        opciones = [d["concepto"], d["nuevo"]["id"]]
        for conjunto, items in sorted(d["asignaciones"].items()):
            for item, ids in sorted(items.items()):
                salida[f"ASG:{d['concepto']}::{conjunto}::{item}"] = {
                    "tipo": "asignacion", "titulo": f"{item} → {', '.join(ids)}", "roles": [_rol(d["concepto"])],
                    "pregunta": "¿El elemento corresponde a la versión asignada del concepto dividido?",
                    "datos": {"conjunto": conjunto, "elemento": item,
                              "texto": textos.get(conjunto, {}).get(item, "")[:400], "asignado_a": ids,
                              "opciones": [_concepto(c) for c in opciones],
                              "criterio_division": d.get("justificacion")}}
    return salida


def _exp_cambios_asignatura() -> dict[str, dict]:
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t for t in extraer()}
    salida = {}
    for p in sorted(ruta("data/interim/revisiones").glob("20*_coherencia_asignatura*.json")):
        for r in json.loads(p.read_text(encoding="utf-8")):
            t = temas.get(r["id"])
            salida[f"ASI:{r['id']}"] = {
                "tipo": "cambio_asignatura", "archivo": relativa(p),
                "titulo": f"{r['id']}: {r['asignatura_anterior']} → {r['asignatura']}"
                          + (" (revisión de conceptos)" if r["asignatura"] == r["asignatura_anterior"] else ""),
                "roles": sorted({_rol(r["asignatura_anterior"]), _rol(r["asignatura"])}),
                "pregunta": "¿Son correctos la asignatura y los conceptos que la revisión asignó al tema?",
                "datos": {"tema": r["id"], "antes": r["asignatura_anterior"], "ahora": r["asignatura"],
                          "justificacion": r["justificacion"], "conceptos": [_concepto(c) for c in r["conceptos"]],
                          "texto": f"{t.unidad} · {t.contenido}. {t.procedimental} Indicador: {t.indicador}"
                          if t else ""}}
    return salida


def _exp_hallazgos() -> dict[str, dict]:
    p = ruta(f"{DIR}/hallazgos.json")
    return {f"HAL:{h['id']}": {"tipo": "hallazgo", "titulo": h["titulo"], "roles": [_rol(h["asignatura"]),
                                                                                   "psicopedagogo"],
                               "pregunta": "¿El panel respalda la lectura y la recomendación curricular?",
                               "datos": h} for h in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}


def _exp_propuestas() -> dict[str, dict]:
    p = ruta("data/interim/propuestas/adopcion_v2.json")
    if not p.exists():
        return {}
    salida = {}
    for a in json.loads(p.read_text(encoding="utf-8")):
        if a["estado"] != "no_adoptada":
            continue
        asig, resto = a["clave"].split(":", 1)
        ciclo, n = resto.split("#")
        prop = json.loads(ruta(f"asignaturas/{asig}/propuesta/propuesta_{ciclo}.json").read_text(encoding="utf-8"))
        accion = next(x for x in prop["acciones"] if x["n"] == int(n))
        salida[f"PRO:{a['clave']}"] = {
            "tipo": "propuesta", "titulo": accion.get("tema_propuesto") or accion["accion"],
            "roles": [_rol(asig), "psicopedagogo"],
            "pregunta": "La V2 no adoptó esta acción de la propuesta. ¿Se adopta, se adapta o se descarta?",
            "datos": {"asignatura": asig, "ciclo": ciclo,
                      **{k: accion.get(k) for k in ("accion", "grado_propuesto", "unidad_propuesta", "tema_propuesto",
                                                    "indicador_logro", "conceptos", "evidencia", "justificacion")},
                      "conciliacion_v2": a["justificacion"]}}
    return salida


def _notas_revision() -> dict[str, str]:
    """Puntos de REVISION_PENDIENTE.md por objetivo (encabezados «## <tema> · …»)."""
    p = ruta("data/pedagogia/REVISION_PENDIENTE.md")
    if not p.exists():
        return {}
    notas, actual = {}, None
    for linea in p.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"## (G\d\d-\S+)", linea):
            actual = f"TEMA:{m.group(1)}"
            notas[actual] = ""
        elif actual:
            notas[actual] += linea + "\n"
    return notas


def _objetivo_de(e: dict) -> str | None:
    if e.get("objetivos"):
        return e["objetivos"][0]
    m = re.search(r"\((G\d\d-[^)]+?)(?:-r\d+)?\)", e.get("origen") or "")
    return f"TEMA:{m.group(1)}" if m else None


def _exp_contenido() -> dict[str, dict]:
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia, navegador_compartido, palabras_max, registro

    ped, nav, notas = Pedagogia.cargar(), navegador_compartido(), _notas_revision()
    salida = {}
    for e in [*ped.actividades.values(), *ped.dificultades.values(), *ped.microtemas.values()]:
        if e.get("estado") != "propuesta_pendiente":
            continue
        obj = _objetivo_de(e)
        t = nav.por_id.get(obj) if obj else None
        concepto = e.get("concepto") or next((c for c in e.get("evalua", []) if c.startswith("CON:")), None)
        grado = min(e.get("grados") or [t.grado if t and t.grado else 9])
        salida[f"PED:{e['id']}"] = {
            "tipo": "contenido", "titulo": e["id"], "elemento": e["tipo"],
            "etapas": [[_rol(concepto or "quimica")], ["psicopedagogo"], [_rol(concepto or "quimica")]],
            "roles": [_rol(concepto or "quimica"), "psicopedagogo"],
            "pregunta": "¿El elemento se puede usar tal cual con estudiantes del grado? Si no, corrígelo.",
            "datos": {"elemento": e, "concepto": _concepto(concepto) if concepto else None,
                      "objetivo": {"id": obj, "grado": t.grado if t else None,
                                   "indicador": t.props.get("indicador") if t else None,
                                   "evidencia": t.props.get("evidencia") if t else None},
                      "adaptacion": {"palabras_max": palabras_max(grado), "registro": registro(grado)},
                      "notas_de_los_redactores": notas.get(obj or "", "").strip()[:2500]}}
    return salida


def _exp_piloto() -> dict[str, dict]:
    return {f"PIL:{d['id']}": {"tipo": "piloto", "titulo": d["pregunta"], "roles": ["psicopedagogo"],
                               "pregunta": d["pregunta"],
                               "datos": {"propuesta": "aprendizaje/PILOTO.md",
                                         "spec": "specs/13_apoyo_al_aprendizaje.md",
                                         "prueba_vertex": "aprendizaje/README.md (prueba de humo)"}}
            for d in config()["piloto"]}


def expedientes() -> dict[str, dict]:
    """Todos los expedientes que el panel puede dictaminar, por id."""
    return {**_exp_decisiones(), **_exp_asignaciones(), **_exp_cambios_asignatura(), **_exp_contenido(),
            **_exp_hallazgos(), **_exp_propuestas(), **_exp_piloto()}


# -- estado ---------------------------------------------------------------------------------------------------------
def _p_estado() -> Path:
    return ruta(f"{DIR}/estado.json")


def cargar_estado() -> dict[str, dict]:
    p = _p_estado()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def _guardar_estado(estado: dict) -> None:
    _p_estado().parent.mkdir(parents=True, exist_ok=True)
    _p_estado().write_text(json.dumps(dict(sorted(estado.items())), ensure_ascii=False, indent=1) + "\n",
                           encoding="utf-8")


def _quienes(x: dict, ronda: int) -> list[str]:
    """Roles que dictaminan el expediente en esta ronda (vacío si no le toca)."""
    if x["estado"] in ("resuelta", "sin_consenso"):
        return []
    dict_previos = [d for d in x["dictamenes"] if d["ronda"] < ronda]
    if x["tipo"] == "contenido":
        etapa = len({d["ronda"] for d in dict_previos})
        return x["etapas"][etapa] if etapa < len(x["etapas"]) else []
    rondas = sorted({d["ronda"] for d in dict_previos})
    return x["roles"] if len(rondas) < 2 else []


# -- lotes ----------------------------------------------------------------------------------------------------------
def _dir_lotes() -> Path:
    return ruta(f"{DIR}/lotes")


def iniciar(tipos: list[str] | None = None) -> int:
    """Agrega al estado los expedientes que todavía no tiene (de los tipos pedidos). Devuelve cuántos agregó."""
    estado = cargar_estado()
    nuevos = {i: {**x, "dictamenes": [], "estado": "pendiente", "version": VERSION}
              for i, x in expedientes().items() if (tipos is None or x["tipo"] in tipos) and i not in estado}
    _guardar_estado({**estado, **nuevos})
    return len(nuevos)


def preparar(ronda: int, tipos: list[str] | None = None) -> list[str]:
    """Escribe los lotes de la ronda con los expedientes del estado (por rol, partidos por peso: PESO_MAX_LOTE). Desde
    la ronda 2, cada expediente lleva los dictámenes anteriores (deliberación) o la versión vigente del elemento
    (contenido). Devuelve las rutas escritas."""
    estado = cargar_estado()
    por_rol: dict[str, list[dict]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        if tipos is not None and x["tipo"] not in tipos:
            continue
        for rol in _quienes(x, ronda):
            exp = {k: x[k] for k in ("tipo", "titulo", "pregunta", "datos") if k in x}
            exp["id"], exp["opciones"] = i, config()["tipos"][x["tipo"]]["opciones"]
            if x["tipo"] == "contenido":
                exp["datos"] = {**x["datos"], "elemento": x.get("version_vigente") or x["datos"]["elemento"]}
                exp["etapa"] = {0: "exactitud científica (experto)", 1: "revisión psicopedagógica",
                                2: "visto bueno final del experto"}[len({d["ronda"] for d in x["dictamenes"]})]
                exp["campos_editables"] = config()["campos_editables"][x["elemento"]]
                if x["dictamenes"]:
                    exp["revisiones_anteriores"] = x["dictamenes"]
            elif x["dictamenes"]:
                exp["dictamenes_anteriores"] = [d for d in x["dictamenes"] if d["rol"] != rol] + \
                    [{**d, "nota": "tu dictamen anterior"} for d in x["dictamenes"] if d["rol"] == rol]
            por_rol[rol].append(exp)
    d = _dir_lotes()
    d.mkdir(parents=True, exist_ok=True)
    escritos = []
    for rol, exps in sorted(por_rol.items()):
        partes: list[list[dict]] = [[]]
        for exp in exps:   # en orden de id: los lotes quedan casi homogéneos por tipo
            if partes[-1] and sum(PESO[x["tipo"]] for x in partes[-1]) + PESO[exp["tipo"]] > PESO_MAX_LOTE:
                partes.append([])
            partes[-1].append(exp)
        for k, parte in enumerate(partes, start=1):
            nombre = f"r{ronda}_{rol}" + (f"_{k}" if len(partes) > 1 else "")
            lote = {"lote": nombre, "ronda": ronda, "rol": rol, "version": VERSION,
                    "instrucciones": ["prompts/panel_dictaminar.md", f".claude/agents/{rol}.md"],
                    "expedientes": parte}
            p = d / f"lote_{nombre}.json"
            p.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            escritos.append(relativa(p))
    return escritos


# -- validación de un dictamen ----------------------------------------------------------------------------------------
@cache
def _nav():
    from goes_science_kg.aprendizaje.pedagogia import navegador_compartido

    return navegador_compartido()


def errores_elemento_corregido(original: dict, cambios: dict, campos: list[str]) -> list[str]:
    """La corrección toca solo campos editables y el elemento corregido sigue pasando la validación de la capa."""
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia, errores_elemento

    e = [f"campo no editable: {k}" for k in cambios if k not in campos]
    if e:
        return e
    nuevo = {**copy.deepcopy(original), **cambios}
    ped = Pedagogia.cargar()
    return errores_elemento(nuevo, _nav(), ped.con([nuevo]))


def errores_lote(lote: dict, salida: list[dict]) -> list[str]:
    """Errores de la salida de un rol: un dictamen por expediente, con decisión válida, justificación breve,
    evidencia, confianza y lo que cada decisión exige (alternativa, texto, asignación o cambios válidos)."""
    exps = {x["id"]: x for x in lote["expedientes"]}
    ids = Counter(d.get("id") for d in salida)
    errores = [f"expediente sin dictamen {i}" for i in sorted(exps.keys() - ids.keys())]
    errores += [f"id fuera del lote {i}" for i in sorted(k for k in ids.keys() - exps.keys() if k)]
    errores += [f"id repetido {i}" for i, n in ids.items() if n > 1]
    maximo = config()["palabras_justificacion"]
    for d in salida:
        x = exps.get(d.get("id"))
        if not x:
            continue
        pre = f"{d['id']}: "
        if d.get("decision") not in x["opciones"]:
            errores.append(pre + f"decisión {d.get('decision')!r} fuera de {x['opciones']}")
            continue
        if not d.get("justificacion") or _palabras(d["justificacion"]) > maximo:
            errores.append(pre + f"justificación de 1 a {maximo} palabras")
        if not d.get("evidencia") or not all(isinstance(v, dict) and v.get("fuente") and v.get("cita")
                                             for v in d["evidencia"]):
            errores.append(pre + "evidencia: lista de {fuente, cita} no vacía")
        if d.get("confianza") not in CONFIANZAS:
            errores.append(pre + "confianza alta, media o baja")
        if (campo := REQUIERE_TEXTO.get(d["decision"])) and not (d.get(campo) or "").strip():
            errores.append(pre + f"«{d['decision']}» exige «{campo}»")
        if x["tipo"] == "asignacion" and d["decision"] == "cambiar":
            validos = {c["id"] for c in x["datos"]["opciones"]}
            nuevo = d.get("asignado_a") or []
            if not nuevo or not set(nuevo) <= validos or set(nuevo) == set(x["datos"]["asignado_a"]):
                errores.append(pre + f"«cambiar» exige asignado_a ⊆ {sorted(validos)} y distinto del actual")
        if x["tipo"] == "contenido":
            cambios = d.get("cambios") or {}
            if d["decision"] == "corregir":
                if not cambios:
                    errores.append(pre + "«corregir» exige «cambios» (campo → valor nuevo)")
                else:
                    errores += [pre + e for e in errores_elemento_corregido(x["datos"]["elemento"], cambios,
                                                                            x["campos_editables"])]
            elif cambios:
                errores.append(pre + "«aprobar» no lleva cambios")
    return errores


# -- consolidación --------------------------------------------------------------------------------------------------
def _clave_decision(d: dict) -> tuple:
    return (d["decision"], tuple(sorted(d.get("asignado_a") or [])))


def consolidar(ronda: int) -> dict:
    """Lee las salidas de la ronda (todas válidas o nada), agrega los dictámenes al estado y avanza cada expediente.
    Devuelve los conteos por estado."""
    estado = cargar_estado()
    nuevos = []
    for p_lote in sorted(_dir_lotes().glob(f"lote_r{ronda}_*.json")):
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            raise ValueError(f"falta {p_sal.name}")
        lote, salida = (json.loads(x.read_text(encoding="utf-8")) for x in (p_lote, p_sal))
        if errs := errores_lote(lote, salida):
            raise ValueError(f"{p_sal.name}: {len(errs)} errores: " + "; ".join(errs[:10]))
        nuevos += [{**d, "ronda": ronda, "rol": lote["rol"], "fecha": date.today().isoformat()} for d in salida]
    for d in nuevos:
        x = estado[d["id"]]
        x["dictamenes"] = [v for v in x["dictamenes"] if not (v["ronda"] == ronda and v["rol"] == d["rol"])] + [d]
    for x in estado.values():
        if any(d["ronda"] == ronda for d in x["dictamenes"]):
            _avanzar(x, ronda)
    _guardar_estado(estado)
    return dict(Counter(x["estado"] for x in estado.values()))


def _avanzar(x: dict, ronda: int) -> None:
    de_ronda = [d for d in x["dictamenes"] if d["ronda"] == ronda]
    if any(d["confianza"] == "baja" for d in de_ronda):
        x["estado"] = "sin_consenso"
        x["motivo"] = "confianza baja de " + ", ".join(d["rol"] for d in de_ronda if d["confianza"] == "baja")
        return
    if x["tipo"] == "contenido":
        d = de_ronda[0]
        version = x.get("version_vigente") or x["datos"]["elemento"]
        if d["decision"] == "corregir":
            x["version_vigente"] = {**version, **d["cambios"]}
        etapa = len({v["ronda"] for v in x["dictamenes"]})
        psico_aprueba = d["rol"] == "psicopedagogo" and d["decision"] == "aprobar"
        x["estado"] = "resuelta" if psico_aprueba or etapa >= len(x["etapas"]) else "en_revision"
        if x["estado"] == "resuelta":
            corregido = any(v["decision"] == "corregir" for v in x["dictamenes"])
            x["resolucion"] = {"decision": "corregir" if corregido else "aprobar", "ronda": ronda}
        return
    if {d["rol"] for d in de_ronda} != set(x["roles"]):
        x["estado"] = "en_deliberacion"
        return
    claves = {_clave_decision(d) for d in de_ronda}
    if len(claves) == 1:
        x["estado"] = "resuelta"
        x["resolucion"] = {"decision": de_ronda[0]["decision"], "ronda": ronda,
                           **({"asignado_a": de_ronda[0]["asignado_a"]} if de_ronda[0].get("asignado_a") else {})}
    else:
        x["estado"] = "sin_consenso" if len({d["ronda"] for d in x["dictamenes"]}) >= 2 else "en_deliberacion"
        if x["estado"] == "sin_consenso":
            x["motivo"] = "sin unanimidad tras la deliberación: " + "; ".join(
                f"{d['rol']} {d['decision']}" for d in de_ronda)


def resumen() -> dict:
    """Conteo por tipo y estado."""
    c: dict[str, Counter] = defaultdict(Counter)
    for x in cargar_estado().values():
        c[x["tipo"]][x["estado"]] += 1
        if x["estado"] == "resuelta":
            c[x["tipo"]][f"→ {x['resolucion']['decision']}"] += 1
    return {k: dict(v) for k, v in sorted(c.items())}


# -- aplicar lo resuelto ----------------------------------------------------------------------------------------------
def _registro(x: dict) -> dict:
    """Lo que queda en una capa como procedencia de un dictamen del panel."""
    finales = [d for d in x["dictamenes"] if d["ronda"] == x["resolucion"]["ronda"]] or x["dictamenes"][-1:]
    return {"fecha": date.today().isoformat(), "version": VERSION, "decision": x["resolucion"]["decision"],
            "roles": sorted({d["rol"] for d in x["dictamenes"]}),
            "rondas": sorted({d["ronda"] for d in x["dictamenes"]}),
            "justificaciones": {d["rol"]: d["justificacion"] for d in finales},
            **{k: v for d in finales for k in ("alternativa", "texto") if (v := d.get(k))},
            "nota": "dictamen del panel de expertos IA (spec 14); no es una confirmación del MINED"}


def aplicar() -> dict:
    """Escribe lo resuelto y aún no aplicado en las capas, con su procedencia (idempotente):
    - decisiones y cambios de asignatura: `dictamenes_panel`; un rechazo además va a `observaciones` (pide una nueva
      decisión, como un rechazo del MINED);
    - asignaciones de una división: «cambiar» reasigna el elemento y deja el historial en la división;
    - capa pedagógica: la versión revisada, con estado «revisado_panel», `revision_panel` y los valores anteriores.
    Hallazgos, propuestas y piloto no tocan capas: van al informe. Devuelve los conteos por tipo."""
    from goes_science_kg import revision_decisiones as rd

    estado = cargar_estado()
    hechos: Counter = Counter()
    capas = {t: rd._leer(t) for t in rd.ARCHIVOS}
    claves = {t: {rd.DESCRIPCION[t][0](r): r for r in capas[t]} for t in capas}
    coherencia = {p: json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted(ruta("data/interim/revisiones").glob("20*_coherencia_asignatura*.json"))}
    from goes_science_kg.aprendizaje.pedagogia import ARCHIVOS, directorio

    capa_ped = {t: {e["id"]: e for e in json.loads((directorio() / a).read_text(encoding="utf-8"))}
                for t, a in ARCHIVOS.items()}
    for i, x in sorted(estado.items()):
        if x["estado"] != "resuelta" or x.get("aplicado") or x["tipo"] in ("hallazgo", "propuesta", "piloto"):
            continue
        reg = _registro(x)
        if x["tipo"] == "decision":
            r = claves[x["subtipo"]][i.split(":", 2)[2]]
            r.setdefault("dictamenes_panel", []).append(reg)
            if reg["decision"] == "rechazar":
                r.setdefault("observaciones", []).append({"fecha": reg["fecha"], "revisado_por": "panel de expertos IA",
                                                          "comentario": reg.get("alternativa", "")})
        elif x["tipo"] == "asignacion":
            concepto, conjunto, item = i.removeprefix("ASG:").split("::")
            div = claves["division"][concepto]
            div.setdefault("dictamenes_panel_asignaciones", {})[f"{conjunto}::{item}"] = reg
            if reg["decision"] == "cambiar":
                antes = div["asignaciones"][conjunto][item]
                div["asignaciones"][conjunto][item] = x["resolucion"]["asignado_a"]
                div.setdefault("historial_asignaciones", []).append(
                    {"elemento": f"{conjunto}::{item}", "antes": antes, "despues": x["resolucion"]["asignado_a"],
                     "por": "panel de expertos IA", "fecha": reg["fecha"]})
        elif x["tipo"] == "cambio_asignatura":
            p = ruta(x["archivo"])
            r = next(e for e in coherencia[p] if e["id"] == i.removeprefix("ASI:"))
            r.setdefault("dictamenes_panel", []).append(reg)
            if reg["decision"] == "rechazar":
                r.setdefault("observaciones", []).append({"fecha": reg["fecha"], "revisado_por": "panel de expertos IA",
                                                          "comentario": reg.get("alternativa", "")})
        elif x["tipo"] == "contenido":
            e = capa_ped[x["elemento"]][i.removeprefix("PED:")]
            nueva = x.get("version_vigente") or e
            anteriores = {k: e.get(k) for k in nueva if k in config()["campos_editables"][x["elemento"]]
                          and nueva.get(k) != e.get(k)}
            e.update({k: nueva[k] for k in anteriores})
            e["estado"] = "revisado_panel"
            e["revision_panel"] = {**reg, **({"valores_anteriores": anteriores} if anteriores else {})}
        x["aplicado"] = reg["fecha"]
        hechos[x["tipo"]] += 1
    for t, registros in capas.items():
        if registros:
            rd._guardar(t, registros)
    for p, datos in coherencia.items():
        p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for t, archivo in ARCHIVOS.items():
        (directorio() / archivo).write_text(json.dumps(sorted(capa_ped[t].values(), key=lambda e: e["id"]),
                                                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _guardar_estado(estado)
    return dict(hechos)


# -- informe ----------------------------------------------------------------------------------------------------------
def _celda(s: str | None, n: int = 260) -> str:
    s = re.sub(r"\s+", " ", s or "").replace("|", "/").strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def _texto_final(x: dict) -> str:
    finales = [d for d in x["dictamenes"] if d["ronda"] == max(v["ronda"] for v in x["dictamenes"])]
    partes = [f"**{d['rol']}:** {d.get('texto') or d.get('alternativa') or d.get('recomendacion') or ''} "
              f"{d['justificacion']}" for d in finales]
    return " ".join(partes)


def informe() -> str:
    """panel/DICTAMEN.md: lo que resolvió el panel, lo que dejó sin consenso y su asesoría del piloto."""
    estado = cargar_estado()
    res = resumen()
    por_tipo: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        por_tipo[x["tipo"]].append((i, x))
    md = ["# Dictamen del panel de expertos IA", "",
          "> Generado por `uv run gskg panel informe` (spec 14). El panel lo forman un experto en la didáctica de "
          "cada ciencia y un psicopedagogo, todos IA. **Sus dictámenes no son confirmaciones del MINED**: quedan "
          "registrados con su evidencia y una persona puede confirmarlos o revertirlos. Lo que el panel no resolvió "
          "por unanimidad queda para una decisión humana.", "",
          "| Tipo | Expedientes | Resueltos | Sin consenso | Decisiones |", "|---|---|---|---|---|"]
    for t, c in res.items():
        decisiones = ", ".join(f"{k.removeprefix('→ ')} {v}" for k, v in sorted(c.items()) if k.startswith("→"))
        total = sum(v for k, v in c.items() if not k.startswith("→"))
        md.append(f"| {t} | {total} | {c.get('resuelta', 0)} | {c.get('sin_consenso', 0)} | {decisiones} |")
    secciones = [("decision", "Decisiones de contenido"),
                 ("cambio_asignatura", "Asignatura y conceptos de los temas"),
                 ("asignacion", "Asignaciones de la división de «configuración electrónica»"),
                 ("hallazgo", "Hallazgos del contraste internacional"),
                 ("propuesta", "Acciones de las propuestas que la V2 no adoptó"),
                 ("contenido", "Capa pedagógica"), ("piloto", "Asesoría para el piloto del tutor")]
    for t, titulo in secciones:
        filas = por_tipo.get(t, [])
        if not filas:
            continue
        md += ["", f"## {titulo}", ""]
        if t in ("asignacion", "contenido", "cambio_asignatura"):
            cambios = [(i, x) for i, x in filas if x["estado"] == "resuelta" and x["resolucion"]["decision"]
                       in ("cambiar", "corregir", "rechazar")]
            md.append(f"{sum(x['estado'] == 'resuelta' for _, x in filas)} resueltos; {len(cambios)} con cambios o "
                      "rechazo (abajo); el resto se aceptó o aprobó tal cual.")
            if cambios:
                md += ["", "| Expediente | Decisión | Fundamento |", "|---|---|---|"]
                md += [f"| {_celda(x['titulo'], 90)} | {x['resolucion']['decision']} | {_celda(_texto_final(x))} |"
                       for _, x in cambios]
        else:
            md += ["| Expediente | Dictamen | Fundamento |", "|---|---|---|"]
            md += [f"| {_celda(x['titulo'], 120)} | "
                   f"{x['resolucion']['decision'] if x['estado'] == 'resuelta' else x['estado']} "
                   f"| {_celda(_texto_final(x), 600 if t == 'piloto' else 360)} |" for _, x in filas]
        pendientes = [(i, x) for i, x in filas if x["estado"] == "sin_consenso"]
        if pendientes:
            md += ["", f"**Sin consenso ({len(pendientes)}), para una decisión humana:**", ""]
            md += [f"- {_celda(x['titulo'], 120)}: {_celda(x.get('motivo', ''), 200)}" for _, x in pendientes]
    p = ruta("panel/DICTAMEN.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(md) + "\n", encoding="utf-8")
    return relativa(p)
