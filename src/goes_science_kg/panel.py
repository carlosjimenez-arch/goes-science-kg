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
        "contenido": 1.2, "clase_incierta": 1.2}
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
    for e in [*ped.actividades.values(), *ped.dificultades.values(), *ped.microtemas.values(),
              *ped.experimentos.values()]:
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


def _exp_refuerzos() -> dict[str, dict]:
    """Refuerzos de la malla V3 redactados y todavía sin revisar (spec 15): experto de la disciplina → psicopedagogo →
    experto, como la capa pedagógica. Se pueden aprobar, corregir o convertir en descarte."""
    from goes_science_kg.aprendizaje.pedagogia import palabras_max, registro
    from goes_science_kg.ingesta.mallas import extraer

    p = ruta("data/interim/refuerzo_v3/refuerzos.json")
    if not p.exists():
        return {}
    temas = {t.id: t for t in extraer()}
    salida = {}
    for r in json.loads(p.read_text(encoding="utf-8")):
        if r.get("estado") != "propuesta_pendiente":
            continue
        rol = _rol(r.get("asignatura") or "quimica")
        t = temas.get(r.get("tema_ancla") or "")
        grado = t.grado if t else max(r.get("grados_destino") or [9])
        salida[f"RFZ:{r['id']}"] = {
            "tipo": "contenido", "titulo": f"{r['id']} ({r['tipo']}, {grado}.°)", "elemento": "refuerzo",
            "etapas": [[rol], ["psicopedagogo"], [rol]], "roles": [rol, "psicopedagogo"],
            "pregunta": "¿El refuerzo se puede proponer al MINED tal cual (ubicación, redacción, nivel del grado y "
                        "evidencia)? Si no, corrígelo; si no se sostiene o la V3 ya lo cubre, conviértelo en descarte "
                        "(decision «descartar» con motivo).",
            "datos": {"elemento": {k: r.get(k) for k in ("id", "tipo", "decision", "motivo", "forma", "tema_ancla",
                                                         "refuerzo", "fila", "evidencia", "confianza")},
                      "candidato": {k: r.get(k) for k in ("origen", "problema", "texto_base", "conceptos",
                                                          "temas_ancla", "solidez")},
                      "tema_ancla": {"id": t.id, "grado": t.grado, "unidad": t.unidad, "contenido": t.contenido,
                                     "procedimental": t.procedimental, "indicador": t.indicador} if t else None,
                      "adaptacion": {"palabras_max": palabras_max(grado), "registro": registro(grado)}}}
    return salida


def _exp_piloto() -> dict[str, dict]:
    return {f"PIL:{d['id']}": {"tipo": "piloto", "titulo": d["pregunta"], "roles": ["psicopedagogo"],
                               "pregunta": d["pregunta"],
                               "datos": {"propuesta": "aprendizaje/PILOTO.md",
                                         "spec": "specs/13_apoyo_al_aprendizaje.md",
                                         "prueba_vertex": "aprendizaje/README.md (prueba de humo)"}}
            for d in config()["piloto"]}


OPCIONES_CLASE = {
    "2_8": ("INC:", "internacional/2_8/README.md y specs/12, sección «Método v2»",
            ["faltante", "tardio", "posterior", "adelantado", "sin_referente", "alineado", "no_aplica"]),
    "9_11": ("INC:9_11:", "specs/11 («Cómo leer las clases» de internacional/README.md) y specs/12 («Método v2»)",
             ["retomado", "no_retomado", "previo", "solo_especializacion", "alineado", "tardio", "adelantado",
              "sin_referente", "faltante", "no_aplica"]),
}
ID_TEMA = r"G\d\d-[A-Z]{3}-U\d+-\d+(?:\.\d+)+(?:-f\d+|-v3)?"


def _objetivos_del_tramo(clave: str) -> dict[str, dict]:
    from goes_science_kg.internacional import tramo
    from goes_science_kg.internacional.consenso import objetivos

    anterior = tramo.actual().clave
    tramo.usar(clave)
    try:
        return {o["id"]: o for o in objetivos()}
    finally:
        tramo.usar(anterior)


def _datos_clase(clave: str, c: str, f: dict, objs: dict, temas: dict) -> dict:
    """Los datos de un expediente de clase del contraste: lecturas, grados, consenso, temas de la malla y un ejemplo
    de objetivo por país."""
    paises = {}
    for p, d in sorted(f["paises"].items()):
        o = next((objs[i] for i in d["objetivos"] if i in objs), None)
        paises[p] = {"primer_grado_nucleo": d["primer_grado_nucleo"], "en_especializacion": d["en_especializacion"],
                     **({"ejemplo": f"{o['id']} [{o['archivo'].split('/')[-1]} p. {o.get('pagina')}, SV "
                                    f"{o['grado_sv_min']}–{o['grado_sv_max']}, {o['nivel']}]: "
                                    f"{o['texto'][:160]}"} if o else {})}
    ids = [*f["sv_temas"], *f.get("sv_temas_texto", [])]
    sv = [f"{t} (grado {temas[t].grado}, {temas[t].ruta}, hoja «{temas[t].hoja}», fila {temas[t].fila}): "
          f"{temas[t].contenido}. {temas[t].indicador}"[:300] for t in ids if t in temas][:6]
    return {"tramo": clave, "concepto": _concepto(c), "lecturas": f["lecturas"], "alertas": f.get("alertas"),
            "v2_primer_grado": {"amplio": f["sv_primer_grado"], "estricto": f["sv_primer_grado_solido"]},
            "consenso": {"grado_amplio": f["grado_consenso"], "grado_estricto": f["grado_consenso_solido"],
                         "mediana": f["mediana_primer_grado_nucleo"], "n_paises": f["n_nucleo"]},
            "temas_v2": sv, "paises": paises}   # «temas_v2»: los temas de la malla VIGENTE (el nombre es histórico)


def _exp_inciertos() -> dict[str, dict]:
    """Conceptos «inciertos» del contraste (las dos lecturas dan clases distintas y una afirma un desajuste) sin
    revisión experta, de los dos tramos: 2.°–8.° (ids «INC:<concepto>») y, desde el 2026-10-13, 9.°–11.°
    («INC:9_11:<concepto>»)."""
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t for t in extraer()}
    salida = {}
    for clave, (prefijo, spec, opciones) in OPCIONES_CLASE.items():
        objs = _objetivos_del_tramo(clave)
        for c, f in sorted(_contraste(clave).items()):
            if f["clase"] != "incierto" or f.get("revision"):
                continue
            salida[f"{prefijo}{c}"] = {
                "tipo": "clase_incierta", "titulo": f"{f['nombre']} ({c}, {clave.replace('_', '.°–')}.°)",
                "roles": [_rol(c)], "opciones": opciones,
                "pregunta": f"Las dos lecturas dan clases distintas y una afirma un desajuste. Verifica en la fuente y "
                            f"decide la clase con la regla del tramo {clave.replace('_', '.°–')}.° ({spec}). En el "
                            "umbral, gana la clase que no afirma un desajuste («solo se afirma lo que coincide»).",
                "datos": _datos_clase(clave, c, f, objs, temas)}
    return salida


def temas_perdidos_en_v3(r: dict) -> list[str]:
    """Temas que cita una revisión del contraste (justificación y evidencia) y que la malla vigente quitó o movió
    de grado (spec 15)."""
    from goes_science_kg.ingesta.mallas import vigente_de

    texto = json.dumps({k: r.get(k) for k in ("justificacion", "evidencia")}, ensure_ascii=False)
    return sorted(i for i in set(re.findall(ID_TEMA, texto)) if vigente_de(i) is None)


def _exp_revision_v3() -> dict[str, dict]:
    """Clases del contraste ya decididas (por el panel o por delegación, no confirmadas por el MINED) cuya evidencia
    cita temas que la V3 quitó o movió de grado: vuelven al panel con la decisión anterior a la vista
    («V3:<tramo>:<concepto>», spec 15)."""
    from goes_science_kg import revision_decisiones as rd
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t for t in extraer()}
    salida = {}
    for clave, (_, spec, opciones) in OPCIONES_CLASE.items():
        objs, contraste = _objetivos_del_tramo(clave), _contraste(clave)
        tipo = "clase_internacional_2_8" if clave == "2_8" else "clase_internacional"
        for r in rd._leer(tipo):
            if r.get("confirmaciones") or not (perdidos := temas_perdidos_en_v3(r)) or r["concepto"] not in contraste:
                continue
            c, f = r["concepto"], contraste[r["concepto"]]
            salida[f"V3:{clave}:{c}"] = {
                "tipo": "clase_incierta", "titulo": f"{f['nombre']} ({c}, {clave.replace('_', '.°–')}.°, malla V3)",
                "roles": [_rol(c)], "opciones": opciones,
                "pregunta": f"La clase «{r['clase']}» se decidió con la malla V2 y su evidencia cita temas que la V3 "
                            f"quitó o movió de grado ({', '.join(perdidos)}). Verifica en la fuente con la malla V3 y "
                            f"decide la clase con la regla del tramo {clave.replace('_', '.°–')}.° ({spec}): mantenla "
                            "si sigue valiendo o cámbiala.",
                "datos": {**_datos_clase(clave, c, f, objs, temas),
                          "clase_automatica_v3": f.get("clase_ia", f["clase"]),
                          "decision_anterior": {"clase": r["clase"], "justificacion": r.get("justificacion"),
                                                "revisado_por": r.get("revisado_por")},
                          "temas_que_la_v3_quito_o_movio": perdidos}}
    return salida


def expedientes() -> dict[str, dict]:
    """Todos los expedientes que el panel puede dictaminar, por id."""
    return {**_exp_decisiones(), **_exp_asignaciones(), **_exp_cambios_asignatura(), **_exp_contenido(),
            **_exp_hallazgos(), **_exp_propuestas(), **_exp_piloto(), **_exp_inciertos(),
            **_exp_revision_v3(), **_exp_refuerzos()}


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
    malla = cargar("mallas").get("version", "V2")   # sobre qué malla se dictamina (spec 15: el bucle lo usa)
    nuevos = {i: {**x, "dictamenes": [], "estado": "pendiente", "version": VERSION, "malla": malla}
              for i, x in expedientes().items() if (tipos is None or x["tipo"] in tipos) and i not in estado}
    _guardar_estado({**estado, **nuevos})
    return len(nuevos)


def preparar(ronda: int, tipos: list[str] | None = None, serie: str = "", prefijo: str = "") -> list[str]:
    """Escribe los lotes de la ronda con los expedientes del estado (por rol, partidos por peso: PESO_MAX_LOTE). Desde
    la ronda 2, cada expediente lleva los dictámenes anteriores (deliberación) o la versión vigente del elemento
    (contenido). `serie` separa los lotes de un grupo de tipos que corre aparte (p. ej. «inc»). Devuelve las rutas."""
    estado = cargar_estado()
    # Un expediente que está en un lote EN CURSO de otra serie (de cualquier ronda, todavía sin su dictamen de esa
    # ronda) no se vuelve a preparar: se dictaminaría dos veces. Los lotes de la misma serie y ronda sí se rehacen.
    otra_serie: set[str] = set()
    for p in _dir_lotes().glob("lote_r*.json"):
        if p.stem.startswith(f"lote_r{ronda}{'-' + serie if serie else ''}_"):
            continue
        lote = json.loads(p.read_text(encoding="utf-8"))
        otra_serie |= {e["id"] for e in lote["expedientes"] if e["id"] in estado
                       and not any(d["ronda"] == lote["ronda"] for d in estado[e["id"]]["dictamenes"])}
    por_rol: dict[str, list[dict]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        if (tipos is not None and x["tipo"] not in tipos) or not i.startswith(prefijo) or i in otra_serie:
            continue
        for rol in _quienes(x, ronda):
            exp = {k: x[k] for k in ("tipo", "titulo", "pregunta", "datos") if k in x}
            exp["id"], exp["opciones"] = i, x.get("opciones") or config()["tipos"][x["tipo"]]["opciones"]
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
            nombre = f"r{ronda}{'-' + serie if serie else ''}_{rol}" + (f"_{k}" if len(partes) > 1 else "")
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
    if str(original.get("id", "")).startswith("REF:"):   # un refuerzo de la malla V3: las reglas del redactor
        from goes_science_kg import refuerzo

        return refuerzo.errores_lote({"candidatos": [{"id": original["id"], "tipo": original["tipo"]}]}, [nuevo])
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


def consolidar(ronda: int, serie: str = "") -> dict:
    """Lee las salidas de la ronda (todas válidas o nada), agrega los dictámenes al estado y avanza cada expediente.
    Devuelve los conteos por estado."""
    estado = cargar_estado()
    nuevos = []
    for p_lote in sorted(_dir_lotes().glob(f"lote_r{ronda}{'-' + serie if serie else ''}_*.json")):
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
    for i in sorted({d["id"] for d in nuevos}):   # solo lo que recibió dictámenes en esta llamada (y esta serie)
        _avanzar(estado[i], ronda)
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
            **({"solidez": s} if (s := (x.get("bucle") or {}).get("solidez")) else {}),
            **({"bucle": max(v["vuelta"] for v in x["bucle"]["vueltas"])} if (x.get("bucle") or {}).get("vueltas")
               else {}),
            "nota": "dictamen del panel de expertos IA (spec 14); no es una confirmación del MINED"}


def aplicar() -> dict:
    """Escribe lo resuelto y aún no aplicado en las capas, con su procedencia (idempotente):
    - decisiones y cambios de asignatura: `dictamenes_panel`; un rechazo además va a `observaciones` (pide una nueva
      decisión, como un rechazo del MINED);
    - asignaciones de una división: «cambiar» reasigna el elemento y deja el historial en la división;
    - capa pedagógica: la versión revisada, con estado «revisado_panel», `revision_panel` y los valores anteriores.
    Hallazgos, propuestas y piloto no tocan capas: van al informe. Devuelve los conteos por tipo.
    Si el bucle de fortalecimiento (bucle.py) cambió una resolución ya aplicada, deja `aplicado` en blanco y esta
    función la vuelve a aplicar: agrega el nuevo registro, retira la observación del panel si ya no rechaza, devuelve
    una asignación a su versión original si el panel deja de cambiarla y actualiza la clase del contraste."""
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
    p_refuerzos = ruta("data/interim/refuerzo_v3/refuerzos.json")   # refuerzos de la malla V3 (spec 15)
    if p_refuerzos.exists():
        capa_ped["refuerzo"] = {e["id"]: e for e in json.loads(p_refuerzos.read_text(encoding="utf-8"))}
    revs_por_tramo = {"2_8": capas["clase_internacional_2_8"], "9_11": capas["clase_internacional"]}
    clases_panel: list[dict] = []
    for i, x in sorted(estado.items()):
        if x["estado"] != "resuelta" or x["tipo"] in ("hallazgo", "propuesta", "piloto"):
            continue
        if x.get("aplicado"):   # ya aplicado: solo se actualiza la solidez que midió el bucle
            # Las clases inciertas buscan su registro en las revisiones de SU tramo. Antes miraban siempre las de
            # 2.°–8.°: las de 9.°–11.° quedaban sin solidez y se pisaba la de un registro de 2.°–8.° del mismo concepto.
            revs = _revisiones_del_tramo(x, revs_por_tramo)
            if (s := (x.get("bucle") or {}).get("solidez")) and (reg := _registro_en_capa(
                    i, x, claves, coherencia, capa_ped, revs)) is not None and reg.get("solidez") != s:
                reg["solidez"] = s
                hechos["solidez"] += 1
            continue
        if x["tipo"] == "clase_incierta":
            clases_panel.append((i, x))
            x["aplicado"] = date.today().isoformat()
            hechos[x["tipo"]] += 1
            continue
        reg = _registro(x)
        if x["tipo"] == "decision":
            r = claves[x["subtipo"]][i.split(":", 2)[2]]
            r.setdefault("dictamenes_panel", []).append(reg)
            _observacion_del_panel(r, reg)
        elif x["tipo"] == "asignacion":
            concepto, conjunto, item = i.removeprefix("ASG:").split("::")
            div = claves["division"][concepto]
            div.setdefault("dictamenes_panel_asignaciones", {})[f"{conjunto}::{item}"] = reg
            antes = div["asignaciones"][conjunto][item]
            # «cambiar» reasigna; «aceptar» deja la asignación original (deshace un cambio anterior del panel);
            # «rechazar» (ninguna versión corresponde) no reasigna: queda como observación del elemento (no de toda la
            # división) para una persona.
            destino = {"cambiar": x["resolucion"].get("asignado_a"), "aceptar": x["datos"]["asignado_a"]}.get(
                reg["decision"], antes)
            obs = div.setdefault("observaciones_asignaciones", {})
            if reg["decision"] == "rechazar":
                obs.setdefault(f"{conjunto}::{item}", {
                    "fecha": reg["fecha"], "revisado_por": "panel de expertos IA",
                    "comentario": "Ninguna versión del concepto corresponde: retirar la etiqueta. "
                                  + " ".join(reg["justificaciones"].values())[:300]})
            else:
                obs.pop(f"{conjunto}::{item}", None)
            if not obs:
                del div["observaciones_asignaciones"]
            if sorted(antes) != sorted(destino):
                div["asignaciones"][conjunto][item] = destino
                div.setdefault("historial_asignaciones", []).append(
                    {"elemento": f"{conjunto}::{item}", "antes": antes, "despues": destino,
                     "por": "panel de expertos IA", "fecha": reg["fecha"]})
        elif x["tipo"] == "cambio_asignatura":
            p = ruta(x["archivo"])
            r = next(e for e in coherencia[p] if e["id"] == i.removeprefix("ASI:"))
            r.setdefault("dictamenes_panel", []).append(reg)
            _observacion_del_panel(r, reg)
        elif x["tipo"] == "contenido":
            e = capa_ped[x["elemento"]][i.split(":", 1)[1]]
            nueva = x.get("version_vigente") or e
            anteriores = {k: e.get(k) for k in nueva if k in config()["campos_editables"][x["elemento"]]
                          and nueva.get(k) != e.get(k)}
            e.update({k: nueva[k] for k in anteriores})
            e["estado"] = "revisado_panel"
            if e.get("revision_panel"):   # una revisión anterior del panel (el bucle la reemplazó)
                e.setdefault("historial_revision_panel", []).append(e["revision_panel"])
            e["revision_panel"] = {**reg, **({"valores_anteriores": anteriores} if anteriores else {})}
        x["aplicado"] = reg["fecha"]
        hechos[x["tipo"]] += 1
    for i, x in clases_panel:   # clases del contraste: entran como revisión experta del panel (ganan sobre la regla)
        revs = _revisiones_del_tramo(x, revs_por_tramo)
        ya = {r["concepto"]: r for r in revs}
        c = x["datos"]["concepto"]["id"]
        d = x["dictamenes"][-1]
        nuevo = {"concepto": c, "nombre": x["datos"]["concepto"]["nombre"],
                 "clase": x["resolucion"]["decision"], "clase_ia": "incierto",
                 "justificacion": d["justificacion"], "evidencia": d["evidencia"],
                 "revisado_por": f"panel de expertos IA ({d['rol']}, {d['fecha']}; dictamen, pendiente de confirmar)"}
        if c not in ya:
            revs.append({**nuevo, "dictamenes_panel": [_registro(x)]})
        elif str(ya[c].get("revisado_por", "")).startswith("panel de expertos IA"):   # lo humano no se toca
            ya[c].update({**nuevo, "dictamenes_panel": [*ya[c].get("dictamenes_panel", []), _registro(x)]})
        elif i.startswith("V3:") and not ya[c].get("confirmaciones"):
            # Una decisión delegada (no confirmada por el MINED) que la V3 dejó sin parte de su evidencia: el dictamen
            # del panel entra como nueva decisión delegada y la anterior queda en el historial (reversible).
            anterior = {k: ya[c].get(k) for k in ("clase", "justificacion", "revisado_por")}
            ya[c].update({**nuevo, "revisado_por": "decisión delegada del responsable por la malla V3 (spec 15), con "
                                                   f"el {nuevo['revisado_por']}",
                          "dictamenes_panel": [*ya[c].get("dictamenes_panel", []), _registro(x)],
                          "historial": [*ya[c].get("historial", []),
                                        {**anterior, "reemplazada": d["fecha"],
                                         "motivo": "la V3 quitó o movió temas que la sostenían"}]})
    for t, registros in capas.items():
        if registros:
            rd._guardar(t, registros)
    for p, datos in coherencia.items():
        p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for t, archivo in ARCHIVOS.items():
        (directorio() / archivo).write_text(json.dumps(sorted(capa_ped[t].values(), key=lambda e: e["id"]),
                                                       ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if "refuerzo" in capa_ped:
        p_refuerzos.write_text(json.dumps(sorted(capa_ped["refuerzo"].values(), key=lambda e: e["id"]),
                                          ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _guardar_estado(estado)
    return dict(hechos)


def _revisiones_del_tramo(x: dict, revs_por_tramo: dict[str, list[dict]]) -> list[dict]:
    """Las revisiones del contraste donde va la clase incierta x: las de su tramo (las anteriores a 9.°–11.° no
    guardaban el tramo y son de 2.°–8.°). Otros tipos no escriben ahí."""
    return revs_por_tramo[x["datos"].get("tramo", "2_8")] if x["tipo"] == "clase_incierta" else []


def _registro_en_capa(i: str, x: dict, claves: dict, coherencia: dict, capa_ped: dict, revs: list[dict]) -> dict | None:
    """El último registro del panel que dejó `aplicar` en la capa del expediente (None si no está)."""
    if x["tipo"] == "decision":
        regs = claves[x["subtipo"]].get(i.split(":", 2)[2], {}).get("dictamenes_panel") or [None]
    elif x["tipo"] == "asignacion":
        concepto, conjunto, item = i.removeprefix("ASG:").split("::")
        regs = [claves["division"][concepto].get("dictamenes_panel_asignaciones", {}).get(f"{conjunto}::{item}")]
    elif x["tipo"] == "cambio_asignatura":
        r = next((e for e in coherencia.get(ruta(x["archivo"]), []) if e["id"] == i.removeprefix("ASI:")), {})
        regs = r.get("dictamenes_panel") or [None]
    elif x["tipo"] == "contenido":
        regs = [capa_ped[x["elemento"]].get(i.split(":", 1)[1], {}).get("revision_panel")]
    else:   # clase_incierta
        r = next((r for r in revs if r["concepto"] == x["datos"]["concepto"]["id"]), {})
        regs = r.get("dictamenes_panel") or [None]
    return regs[-1]


def _observacion_del_panel(r: dict, reg: dict) -> None:
    """Un rechazo del panel va a `observaciones` (pide una nueva decisión); si una resolución posterior del panel ya no
    rechaza, su observación pasa a `observaciones_superadas`. Las observaciones humanas no se tocan."""
    del_panel = [o for o in r.get("observaciones", []) if o.get("revisado_por") == "panel de expertos IA"]
    if reg["decision"] == "rechazar":
        if not del_panel:
            r.setdefault("observaciones", []).append({"fecha": reg["fecha"], "revisado_por": "panel de expertos IA",
                                                      "comentario": reg.get("alternativa", "")})
    elif del_panel:
        r["observaciones"] = [o for o in r["observaciones"] if o not in del_panel]
        r.setdefault("observaciones_superadas", []).extend({**o, "superada": reg["fecha"]} for o in del_panel)
        if not r["observaciones"]:
            del r["observaciones"]


# -- informe ----------------------------------------------------------------------------------------------------------
def _celda(s: str | None, n: int = 260) -> str:
    s = re.sub(r"\s+", " ", s or "").replace("|", "/").strip()
    return s if len(s) <= n else s[:n - 1] + "…"


def _solidez(x: dict) -> str:
    """Solidez que midió el bucle de fortalecimiento (bucle.py), o «—» si no pasó por él."""
    from goes_science_kg.bucle import ETIQUETA

    return ETIQUETA.get((x.get("bucle") or {}).get("solidez"), "—")


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
                 ("clase_incierta", "Conceptos inciertos del contraste de 2.°–8.°"),
                 ("contenido", "Capa pedagógica"), ("piloto", "Asesoría para el piloto del tutor")]
    for t, titulo in secciones:
        filas = por_tipo.get(t, [])
        if not filas:
            continue
        md += ["", f"## {titulo}", ""]
        if t in ("asignacion", "contenido", "cambio_asignatura", "clase_incierta"):
            cambios = [(i, x) for i, x in filas if x["estado"] == "resuelta" and x["resolucion"]["decision"]
                       in ("cambiar", "corregir", "rechazar")]
            md.append(f"{sum(x['estado'] == 'resuelta' for _, x in filas)} resueltos; {len(cambios)} con cambios o "
                      "rechazo (abajo); el resto se aceptó o aprobó tal cual.")
            if cambios:
                md += ["", "| Expediente | Decisión | Solidez | Fundamento |", "|---|---|---|---|"]
                md += [f"| {_celda(x['titulo'], 90)} | {x['resolucion']['decision']} | {_solidez(x)} | "
                       f"{_celda(_texto_final(x))} |" for _, x in cambios]
        else:
            md += ["| Expediente | Dictamen | Solidez | Fundamento |", "|---|---|---|---|"]
            md += [f"| {_celda(x['titulo'], 120)} | "
                   f"{x['resolucion']['decision'] if x['estado'] == 'resuelta' else x['estado']} | {_solidez(x)} "
                   f"| {_celda(_texto_final(x), 600 if t == 'piloto' else 360)} |" for _, x in filas]
        pendientes = [(i, x) for i, x in filas if x["estado"] == "sin_consenso"]
        if pendientes:
            md += ["", f"**Sin consenso ({len(pendientes)}), para una decisión humana:**", ""]
            md += [f"- {_celda(x['titulo'], 120)}: {_celda(x.get('motivo', ''), 200)}"
                   + (f" **Decisión delegada:** {x['decision_delegada']['decision']}: "
                      f"{_celda(x['decision_delegada']['justificacion'], 260)}" if x.get("decision_delegada") else "")
                   for _, x in pendientes]
    from goes_science_kg import bucle

    md += bucle.seccion_informe(estado)
    p = ruta("panel/DICTAMEN.md")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(md) + "\n", encoding="utf-8")
    return relativa(p)
