"""Capa pedagógica (spec 13): actividades, dificultades frecuentes y microtemas de refuerzo.

Es conocimiento COMPARTIDO: vive en data/pedagogia/, se versiona y solo cambia por un proceso de revisión. Cada
elemento declara su `estado`: «propuesta_pendiente» (lo redactó un especialista IA y nadie lo revisó) o «verificado»
(con `revisado_por`). Nada de lo que hace un estudiante escribe aquí: una sesión solo puede agregar una entrada a la
cola de propuestas (data/interim/aprendizaje/propuestas_pendientes.jsonl, fuera de la capa), que revisa
una persona.

Circuito de contenido (igual que el resto del proyecto): `preparar_lote()` escribe un lote por objetivo con las
ranuras que hay que llenar → el subagente `redactor-actividades` escribe la salida → `unir()` valida y agrega.
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from pathlib import Path

from goes_science_kg.config import cargar, relativa, ruta

from .relaciones import Navegador

HABILIDADES = ("recordar", "observar", "explicar", "interpretar_datos", "razonar")
ROLES = ("objetivo", "sondeo", "practica", "comprobacion")
FORMATOS = ("opcion_multiple", "numerica")   # «abierta» exige un evaluador con rúbrica (pendiente: spec 13)
ESTADOS = ("propuesta_pendiente", "verificado")
VERSION = "pedagogia-v1"
ARCHIVOS = {"actividad": "actividades.json", "dificultad": "dificultades.json", "microtema": "microtemas.json"}


def config() -> dict:
    return cargar("aprendizaje")


def directorio() -> Path:
    return ruta(config()["rutas"]["pedagogia"])


def palabras_max(grado: int) -> int:
    """Largo máximo de una explicación para el grado (config/aprendizaje.yaml, adaptacion)."""
    return next(t["palabras_max"] for t in config()["adaptacion"].values() if grado in t["grados"])


def registro(grado: int) -> str:
    return next(t["registro"] for t in config()["adaptacion"].values() if grado in t["grados"])


@dataclass
class Pedagogia:
    """La capa pedagógica cargada, con las relaciones leídas en los dos sentidos."""

    actividades: dict[str, dict] = field(default_factory=dict)
    dificultades: dict[str, dict] = field(default_factory=dict)
    microtemas: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def cargar(cls, base: Path | None = None) -> Pedagogia:
        d = base or directorio()

        def leer(nombre: str) -> dict[str, dict]:
            p = d / nombre
            return {x["id"]: x for x in json.loads(p.read_text(encoding="utf-8"))} if p.exists() else {}

        return cls(leer(ARCHIVOS["actividad"]), leer(ARCHIVOS["dificultad"]), leer(ARCHIVOS["microtema"]))

    def con(self, elementos: list[dict]) -> Pedagogia:
        """Una copia con elementos agregados (para validar una salida antes de unirla)."""
        nueva = Pedagogia(dict(self.actividades), dict(self.dificultades), dict(self.microtemas))
        for e in elementos:
            getattr(nueva, {"actividad": "actividades", "dificultad": "dificultades",
                            "microtema": "microtemas"}[e["tipo"]])[e["id"]] = e
        return nueva

    # «evalua» leída desde el concepto u objetivo: es_evaluado_por
    def es_evaluado_por(self, objetivo_o_concepto: str, rol: str | None = None, grado: int | None = None,
                        excluir: tuple[str, ...] = ()) -> list[dict]:
        return sorted((a for a in self.actividades.values()
                       if objetivo_o_concepto in a["evalua"] and (rol is None or a["rol"] == rol)
                       and (grado is None or grado in a["grados"]) and a["id"] not in excluir),
                      key=lambda a: a["id"])

    # «refuerza» leída desde el concepto: es_reforzado_por
    def es_reforzado_por(self, concepto: str, grado: int) -> dict | None:
        """El microtema del concepto para el grado; si no hay, el del grado más cercano por debajo."""
        candidatos = [m for m in self.microtemas.values() if m["concepto"] == concepto and min(m["grados"]) <= grado]
        return max(candidatos, key=lambda m: (max(g for g in m["grados"] if g <= grado), m["id"]), default=None)

    def dificultad_de_opcion(self, actividad: dict, opcion: str | None) -> dict | None:
        """La dificultad que delata un distractor (relación `detecta`)."""
        dif = (actividad.get("distractores") or {}).get(opcion or "")
        return self.dificultades.get(dif) if dif else None


# -- validación ---------------------------------------------------------------------------------------------------
def _palabras(texto: str | None) -> int:
    return len((texto or "").split())


def _errores_actividad(a: dict, nav: Navegador, ped: Pedagogia) -> list[str]:
    e = []
    if not a["id"].startswith("ACT:"):
        e.append("id sin prefijo ACT:")
    if not a.get("objetivos") or any(t not in nav.por_id for t in a["objetivos"]):
        e.append("toda actividad sirve a ≥1 objetivo curricular existente (TEMA:…)")
    if not a.get("evalua") or any(x not in nav.por_id for x in a["evalua"]):
        e.append(f"evalua con ids inexistentes {a.get('evalua')}")
    for campo, validos in (("rol", ROLES), ("habilidad", HABILIDADES), ("formato", FORMATOS), ("estado", ESTADOS)):
        if a.get(campo) not in validos:
            e.append(f"{campo} inválido {a.get(campo)!r}")
    if not a.get("grados") or any(not 2 <= g <= 11 for g in a["grados"]):
        e.append("grados fuera de 2–11")
    if not a.get("enunciado"):
        e.append("sin enunciado")
    if not 1 <= int(a.get("duracion_min") or 0) <= config()["refuerzo"]["minutos_max_por_refuerzo"]:
        e.append("duración fuera de límites")
    if a.get("formato") == "opcion_multiple":
        ops = a.get("opciones") or {}
        if len(ops) < 3 or a.get("correcta") not in ops:
            e.append("opción múltiple: ≥3 opciones y la correcta entre ellas")
        for op, dif in (a.get("distractores") or {}).items():
            if op not in ops or op == a.get("correcta") or dif not in ped.dificultades:
                e.append(f"distractor {op}→{dif} inválido")
    if a.get("formato") == "numerica" and (a.get("valor") is None or a.get("tolerancia") is None):
        e.append("numérica: valor y tolerancia")
    if a.get("estado") == "verificado" and not a.get("revisado_por"):
        e.append("«verificado» exige revisado_por")
    return [f"{a['id']}: {x}" for x in e]


def _errores_dificultad(d: dict, nav: Navegador) -> list[str]:
    e = []
    if not d["id"].startswith("DIF:") or d.get("concepto") not in nav.por_id:
        e.append("id DIF: y concepto existente")
    if not d.get("descripcion") or d.get("estado") not in ESTADOS:
        e.append("descripción y estado válido")
    if d.get("estado") == "verificado" and not (d.get("revisado_por") and d.get("fuente")):
        e.append("«verificada» exige revisado_por y fuente")
    return [f"{d['id']}: {x}" for x in e]


def _errores_microtema(m: dict, nav: Navegador, ped: Pedagogia) -> list[str]:
    e = []
    if not m["id"].startswith("MT:") or m.get("concepto") not in nav.por_id:
        e.append("id MT: y concepto existente")
    conceptos = nav.equivalentes(m.get("concepto", ""))
    for campo, rol in (("practica", None), ("comprobacion", "comprobacion")):
        a = ped.actividades.get(m.get(campo) or "")
        if not a or not conceptos & set(a["evalua"]) or (rol and a["rol"] != rol):
            e.append(f"{campo} debe ser una actividad que evalúe el concepto")
    if m.get("practica") == m.get("comprobacion"):
        e.append("práctica y comprobación distintas")
    if m.get("grados") and _palabras(m.get("explicacion")) > palabras_max(min(m["grados"])):
        e.append(f"explicación de más de {palabras_max(min(m['grados']))} palabras para {min(m['grados'])}.°")
    if not 1 <= int(m.get("duracion_min") or 0) <= config()["refuerzo"]["minutos_max_por_refuerzo"]:
        e.append("duración fuera de límites")
    if not m.get("criterio") or m.get("estado") not in ESTADOS:
        e.append("criterio de comprensión y estado válido")
    return [f"{m['id']}: {x}" for x in e]


def errores_capa(ped: Pedagogia, nav: Navegador) -> list[str]:
    """Integridad de la capa pedagógica: cada elemento vinculado a ids existentes y a un objetivo curricular."""
    return ([x for a in ped.actividades.values() for x in _errores_actividad(a, nav, ped)]
            + [x for d in ped.dificultades.values() for x in _errores_dificultad(d, nav)]
            + [x for m in ped.microtemas.values() for x in _errores_microtema(m, nav, ped)])


# -- cola de propuestas (lo único que una sesión puede escribir en lo compartido) ------------------------------------
def proponer(tipo: str, contenido: dict, motivo: str, cola: Path | None = None) -> dict:
    """Agrega una propuesta a la cola de revisión. No lleva datos del estudiante: solo el motivo agregado."""
    entrada = {"fecha": date.today().isoformat(), "tipo": tipo, "contenido": contenido, "motivo": motivo,
               "origen": "sesión de tutoría (prototipo)", "estado": "pendiente_revision"}
    p = cola or ruta(config()["rutas"]["propuestas"])
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return entrada


# -- lotes para el subagente redactor-actividades ------------------------------------------------------------------
def _slug(cid: str) -> str:
    return cid.removeprefix("CON:").removeprefix("TEMA:")


def _ranuras_de_base(cid: str, grado: int, rol_base: str) -> list[dict]:
    s, g = _slug(cid), f"G{grado:02d}"
    sondeos = [] if rol_base == "objetivo" else [
        {"id": f"ACT:{s}/sondeo-2-{g}", "tipo": "actividad", "rol": "sondeo", "evalua": [cid],
         "requisito": "otra habilidad que sondeo-1, para confirmar o descartar la hipótesis"}]
    return [
        {"id": f"ACT:{s}/sondeo-1-{g}", "tipo": "actividad", "rol": "sondeo", "evalua": [cid],
         "requisito": "pregunta breve (≤3 min) que detecta si falta esta base; un distractor por dificultad"},
        *sondeos,
        {"id": f"ACT:{s}/practica-{g}", "tipo": "actividad", "rol": "practica", "evalua": [cid],
         "requisito": "actividad guiada del microtema: observar, explicar o interpretar datos, no solo recordar"},
        {"id": f"ACT:{s}/comprobacion-{g}", "tipo": "actividad", "rol": "comprobacion", "evalua": [cid],
         "requisito": "comprueba la comprensión con una situación distinta de la práctica y de los sondeos"},
        {"id": f"MT:{s}/{g}", "tipo": "microtema", "concepto": cid,
         "requisito": f"explicación ≤{palabras_max(grado)} palabras, un ejemplo, práctica y comprobación de arriba"},
        {"id": f"DIF:{s}/1", "tipo": "dificultad", "concepto": cid,
         "requisito": "dificultad frecuente y conocida al aprender este concepto; no inventes fuentes"},
    ]


def preparar_lote(temas: list[str], nav: Navegador, ped: Pedagogia | None = None) -> list[str]:
    """Un lote por objetivo con las ranuras que faltan: dos actividades del objetivo (habilidades distintas), el
    concepto principal y sus bases de profundidad 1, y las de profundidad 2 (confianza alta) cuando la base de
    profundidad 1 no se enseña antes en la malla. Una ranura ya llenada (en la capa o en un lote anterior) no se
    repite. Devuelve las rutas escritas."""
    ped = ped or Pedagogia.cargar()
    hechos = set(ped.actividades) | set(ped.dificultades) | set(ped.microtemas)
    d = directorio() / "lotes"
    d.mkdir(parents=True, exist_ok=True)
    escritos = []
    for tid in temas:
        t = nav.por_id[tid]
        grado = t.grado or 0
        principal = nav.conceptos_de_tema(tid, ("principal",))[0]
        bases = nav.bases(tid)
        huecos = {b.concepto for b in bases if b.profundidad == 1 and not b.antes_del_objetivo}
        elegidas = [b for b in bases if b.profundidad == 1
                    or (b.confianza == "alta" and b.via[-1] in huecos)]
        ranuras = [{"id": f"ACT:{_slug(tid)}/obj-{i}", "tipo": "actividad", "rol": "objetivo",
                    "evalua": [tid, principal], "requisito": r}
                   for i, r in ((1, "evaluación inicial del objetivo (indicador de logro)"),
                                (2, "reevaluación con OTRA habilidad que obj-1 (p. ej. interpretar datos)"))]
        ranuras += _ranuras_de_base(principal, grado, "objetivo")
        for b in elegidas:
            ranuras += _ranuras_de_base(b.concepto, grado, "base")
        ranuras = [r for r in ranuras if r["id"] not in hechos]
        hechos |= {r["id"] for r in ranuras}
        definicion = lambda c: nav.por_id[c].props.get("definicion")  # noqa: E731
        lote = {
            "lote": _slug(tid).replace("/", "_"), "version": VERSION,
            "instrucciones": "prompts/redactar_actividades.md",
            "grado": grado, "adaptacion": {"palabras_max": palabras_max(grado), "registro": registro(grado)},
            "objetivo": {"id": tid, "procedimental": t.etiqueta, "indicador": t.props.get("indicador"),
                         "evidencia": t.props.get("evidencia"), "unidad": t.props.get("unidad"),
                         "principal": {"id": principal, "nombre": nav.por_id[principal].etiqueta,
                                       "definicion": definicion(principal)}},
            "bases": [{"id": b.concepto, "nombre": nav.por_id[b.concepto].etiqueta,
                       "definicion": definicion(b.concepto),
                       "profundidad": b.profundidad, "via": list(b.via), "antes_del_objetivo": b.antes_del_objetivo,
                       "primer_tema": b.primer_tema, "confianza_prerrequisito": b.confianza} for b in elegidas],
            "ranuras": ranuras,
        }
        p = d / f"lote_{lote['lote']}.json"
        p.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        escritos.append(relativa(p))
    return escritos


def errores_lote(lote: dict, salida: list[dict], nav: Navegador | None = None,
                 ped: Pedagogia | None = None) -> list[str]:
    """Errores de una salida de redactor-actividades: cubre cada ranura una vez, respeta su tipo, rol y concepto, y
    cada elemento pasa la validación de la capa (con la capa vigente más esta salida)."""
    nav = nav or navegador_compartido()
    ped = (ped or Pedagogia.cargar()).con([e for e in salida if e.get("tipo") in ARCHIVOS])
    ranuras = {r["id"]: r for r in lote["ranuras"]}
    ids = Counter(e.get("id") for e in salida)
    errores = [f"ranura sin llenar {i}" for i in sorted(ranuras.keys() - ids.keys())]
    errores += [f"id fuera de las ranuras {i}" for i in sorted(k for k in ids.keys() - ranuras.keys() if k)]
    errores += [f"id repetido {i}" for i, n in ids.items() if n > 1]
    errores += ["un elemento sin id"] if None in ids else []
    for e in salida:
        r = ranuras.get(e.get("id"))
        if not r:
            continue
        if e.get("tipo") != r["tipo"] or (r.get("rol") and e.get("rol") != r["rol"]):
            errores.append(f"{e['id']}: tipo o rol distinto del de la ranura")
        if r.get("evalua") and set(e.get("evalua") or []) != set(r["evalua"]):
            errores.append(f"{e['id']}: evalua debe ser {r['evalua']}")
        if r.get("concepto") and e.get("concepto") != r["concepto"]:
            errores.append(f"{e['id']}: concepto debe ser {r['concepto']}")
        if e.get("estado") != "propuesta_pendiente":
            errores.append(f"{e['id']}: lo que redacta un subagente nace «propuesta_pendiente»")
        if e.get("tipo") == "actividad" and lote["grado"] not in (e.get("grados") or []):
            errores.append(f"{e['id']}: grados debe incluir {lote['grado']}")
    obj = [e for e in salida if e.get("rol") == "objetivo"]
    if len(obj) == 2 and obj[0].get("habilidad") == obj[1].get("habilidad"):
        errores.append("obj-1 y obj-2 deben usar habilidades distintas")
    validar = {"actividad": lambda x: _errores_actividad(x, nav, ped),
               "dificultad": lambda x: _errores_dificultad(x, nav),
               "microtema": lambda x: _errores_microtema(x, nav, ped)}
    for e in salida:
        if e.get("tipo") in validar and e.get("id") in ranuras:
            errores += validar[e["tipo"]](e)
    return errores


@cache
def navegador_compartido() -> Navegador:
    """Navegador sobre el grafo versionado (data/grafo/), en caché por proceso."""
    from goes_science_kg.grafo.almacen import cargar as cargar_grafo

    return Navegador(*cargar_grafo())


def unir(base: Path | None = None) -> dict:
    """Valida cada salida de lote y agrega sus elementos a la capa (sin sobrescribir los existentes). Lanza ValueError
    si hay errores; devuelve los conteos por tipo."""
    d = base or directorio()
    ped = Pedagogia.cargar(d)
    nuevos, errores = [], []
    for p_lote in sorted((d / "lotes").glob("lote_*.json")):
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        lote, salida = (json.loads(x.read_text(encoding="utf-8")) for x in (p_lote, p_sal))
        errores += [f"{p_sal.name}: {e}" for e in errores_lote(lote, salida, ped=ped)]
        nuevos += [{**e, "origen": f"redactor-actividades ({lote['lote']})", "version": lote["version"],
                    "revisado_por": ""} for e in salida if e.get("tipo") in ARCHIVOS]
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    ped = ped.con([e for e in nuevos if e["id"] not in
                   set(ped.actividades) | set(ped.dificultades) | set(ped.microtemas)])
    for tipo, archivo in ARCHIVOS.items():
        elementos = getattr(ped, {"actividad": "actividades", "dificultad": "dificultades",
                                  "microtema": "microtemas"}[tipo])
        (d / archivo).write_text(json.dumps(sorted(elementos.values(), key=lambda x: x["id"]), ensure_ascii=False,
                                            indent=1) + "\n", encoding="utf-8")
    return {"actividades": len(ped.actividades), "dificultades": len(ped.dificultades),
            "microtemas": len(ped.microtemas)}
