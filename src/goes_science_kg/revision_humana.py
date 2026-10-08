"""Circuito de revisión humana con el equipo de Ciencias del MINED (skill revision-humana; spec 07).

exportar() → asignaturas/<x>/revision/<fecha>_conceptos_temas.csv y <fecha>_prerrequisitos.csv
  - conceptos_temas: temas cuyo etiquetado de conceptos tiene confianza baja.
  - prerrequisitos: las aristas que sostienen los hallazgos de secuencia («llega tarde / nunca») y todas las de
    confianza baja. Son las que más cambian las conclusiones si están mal.
importar(csv) → data/interim/revisiones/<fecha>_humana_<asig>.json (temas) y
                data/interim/prerrequisitos/rechazados.json (aristas rechazadas).
Columnas de decisión: decision (aceptar | cambiar | rechazar), nuevos_conceptos (ids separados por «;»),
comentario, revisado_por.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

from goes_science_kg.brechas import analizar
from goes_science_kg.conceptos import vocabulario
from goes_science_kg.config import cargar, ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista
from goes_science_kg.prerrequisitos import cargar_prerrequisitos, evidencia_orden

COLUMNAS_DECISION = ["decision (aceptar|cambiar|rechazar)", "nuevos_conceptos (ids; separados por ;)", "comentario",
                     "revisado_por"]


def _escribir(p: Path, encabezado: list[str], filas: list[list]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(encabezado)
        w.writerows(filas)


def exportar(nodos: list[Nodo], aristas: list[Arista], fecha: str | None = None) -> list[str]:
    fecha = fecha or date.today().isoformat()
    por_id = {n.id: n for n in nodos}
    ev = evidencia_orden(nodos, aristas)
    escritos = []
    for asig, cfg in cargar("asignaturas")["asignaturas"].items():
        d = ruta(cfg["carpeta"]) / "revision"
        # 1. Etiquetas de conceptos de confianza baja
        filas = []
        for a in sorted(aristas, key=lambda x: (por_id[x.origen].grado or 0, x.origen)):
            if (a.tipo == TipoArista.TRABAJA and a.origen.startswith("TEMA:") and a.rol == "principal"
                    and a.confianza and a.confianza.value == "baja" and por_id[a.origen].asignatura == asig):
                t = por_id[a.origen]
                conceptos = [por_id[x.destino].etiqueta for x in aristas
                             if x.origen == a.origen and x.tipo == TipoArista.TRABAJA and x.destino.startswith("CON:")]
                filas.append([t.id.removeprefix("TEMA:"), t.grado, t.props.get("unidad"), t.etiqueta,
                              " | ".join(conceptos), a.justificacion, "", "", "", ""])
        p1 = _libre(d / f"{fecha}_conceptos_temas.csv")
        _escribir(p1, ["id", "grado", "unidad", "tema", "conceptos_asignados", "justificacion_ia",
                       *COLUMNAS_DECISION], filas)
        # 2. Prerrequisitos que sostienen hallazgos + los de confianza baja
        r = analizar(asig, nodos, aristas, ev)
        clave = {(s["prerrequisito"], s["concepto"]) for s in r["secuencia"]}
        filas = []
        for a in aristas:
            if a.tipo != TipoArista.PRERREQUISITO_DE or por_id[a.destino].asignatura != asig:
                continue
            o, dd = por_id[a.origen], por_id[a.destino]
            sostiene = (o.etiqueta, dd.etiqueta) in clave
            if sostiene or (a.confianza and a.confianza.value == "baja"):
                filas.append([a.origen, o.etiqueta, a.destino, dd.etiqueta, ev[a.origen]["sv"], ev[a.destino]["sv"],
                              "sí" if sostiene else "no", a.confianza.value if a.confianza else "",
                              a.props.get("tipo_evidencia"), a.justificacion, "", "", "", ""])
        filas.sort(key=lambda f: (f[6] != "sí", f[7] != "alta", f[3]))
        p2 = _libre(d / f"{fecha}_prerrequisitos.csv")
        _escribir(p2, ["prerrequisito_id", "prerrequisito", "concepto_id", "concepto", "primer_grado_sv_prerrequisito",
                       "primer_grado_sv_concepto", "sostiene_hallazgo_de_secuencia", "confianza", "tipo_evidencia",
                       "justificacion_ia", *COLUMNAS_DECISION], filas)
        escritos += [str(p1.relative_to(ruta("."))), str(p2.relative_to(ruta(".")))]
    return escritos


RECHAZADOS = "data/interim/prerrequisitos/rechazados.json"


def _libre(p: Path) -> Path:
    """No sobrescribe un CSV que el equipo pueda estar llenando: agrega -2, -3… al nombre."""
    i, q = 2, p
    while q.exists():
        q = p.with_name(f"{p.stem}-{i}{p.suffix}")
        i += 1
    return q


def importar(archivo: str) -> dict:
    """Lee un CSV revisado (de conceptos o de prerrequisitos) y lo convierte en revisiones.

    Valida antes de escribir: decisión conocida, `revisado_por` obligatorio y códigos de concepto existentes.
    Las revisiones del mismo día y asignatura se acumulan (no se sobrescriben).
    """

    p = ruta(archivo)
    with open(p, encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        campos = lector.fieldnames or []
        filas = [r for r in lector if (r.get(COLUMNAS_DECISION[0]) or "").strip()]
    if not filas:
        return {"decisiones": 0}
    errores = []
    for i, r in enumerate(filas, 2):
        decision = r[COLUMNAS_DECISION[0]].strip().lower()
        if decision not in ("aceptar", "cambiar", "rechazar"):
            errores.append(f"fila {i}: decisión desconocida {decision!r}")
        if not (r.get(COLUMNAS_DECISION[3]) or "").strip():
            errores.append(f"fila {i}: falta revisado_por")
    hoy = date.today().isoformat()
    if "prerrequisito_id" in campos:
        if errores:
            raise ValueError("; ".join(errores))
        destino = ruta(RECHAZADOS)
        previos = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else []
        nuevos = [{"origen": r["prerrequisito_id"], "destino": r["concepto_id"], "comentario": r[COLUMNAS_DECISION[2]],
                   "revisado_por": r[COLUMNAS_DECISION[3]], "fecha": hoy}
                  for r in filas if r[COLUMNAS_DECISION[0]].strip().lower() == "rechazar"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(json.dumps(previos + nuevos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        cargar_prerrequisitos.cache_clear()
        return {"prerrequisitos_rechazados": len(nuevos), "aceptados": len(filas) - len(nuevos)}
    voc = vocabulario()
    revisiones = []
    for i, r in enumerate(filas, 2):
        decision = r[COLUMNAS_DECISION[0]].strip().lower()
        if decision == "rechazar":
            errores.append(f"fila {i}: «rechazar» no aplica a conceptos; usa «cambiar» con los conceptos correctos")
        elif decision == "cambiar":
            ids = [x.strip() for x in r[COLUMNAS_DECISION[1]].split(";") if x.strip()]
            if not ids or (malos := [x for x in ids if x not in voc]):
                errores.append(f"fila {i}: conceptos inexistentes o vacíos {ids if not ids else malos}")
                continue
            revisiones.append({"id": r["id"], "conceptos": ids, "confianza": "alta",
                               "justificacion": r[COLUMNAS_DECISION[2]] or "Corrección del equipo de Ciencias.",
                               "version": f"revision-humana-{hoy}", "revisado_por": r[COLUMNAS_DECISION[3]]})
    if errores:
        raise ValueError("; ".join(errores))
    asig = p.parent.parent.name
    destino = ruta(f"data/interim/revisiones/{hoy}_humana_{asig}.json")
    previas = {x["id"]: x for x in json.loads(destino.read_text(encoding="utf-8"))} if destino.exists() else {}
    previas.update({x["id"]: x for x in revisiones})
    destino.write_text(json.dumps(sorted(previas.values(), key=lambda x: x["id"]), ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    return {"temas_corregidos": len(revisiones), "decisiones": len(filas)}
