"""Confirmación con el MINED de las decisiones tomadas fuera de la IA (spec 07, circuito de revisión humana).

Las decisiones de contenido viven en capas que se aplican al cargar: equivalencias retiradas, prerrequisitos
rechazados, divisiones de conceptos y clases corregidas del contraste internacional. Este módulo las lleva al
equipo de Ciencias y trae su veredicto, con las mismas columnas de decisión que los demás CSV de revisión:

exportar_decisiones() → asignaturas/decisiones/<fecha>_decisiones.csv (una fila por decisión) y
                        <fecha>_asignaciones_division.csv (una fila por elemento reasignado en cada división).
importar_decisiones(csv) → en cada decisión:
  - aceptar: agrega {revisado_por, fecha, comentario} a «confirmaciones».
  - cambiar: solo en asignaciones; reemplaza los conceptos asignados (deben ser el original o el nuevo de la división).
  - rechazar: agrega la objeción a «observaciones». No revierte nada: una objeción pide una nueva decisión
    pedagógica, y queda listada hasta que se tome.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from datetime import date
from pathlib import Path

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.revision_humana import COLUMNAS_DECISION, _escribir, _libre

DIR = "asignaturas/decisiones"
ARCHIVOS = {
    "equivalencia_retirada": "data/interim/conceptos/equivalencias_retiradas.json",
    "prerrequisito_rechazado": "data/interim/prerrequisitos/rechazados.json",
    "division": "data/interim/conceptos/divisiones.json",
    "clase_internacional": "data/interim/internacional/revisiones.json",
}
ENCABEZADO = ["clave", "tipo", "decision_tomada", "justificacion", "decidido_por", "estado", *COLUMNAS_DECISION]
ENCABEZADO_ASIGNACIONES = ["clave", "concepto_dividido", "conjunto", "elemento", "texto", "asignado_a",
                           *COLUMNAS_DECISION]


def _leer(tipo: str) -> list[dict]:
    p = ruta(ARCHIVOS[tipo])
    if not p.exists():
        return []
    datos = json.loads(p.read_text(encoding="utf-8"))
    return datos["divisiones"] if tipo == "division" else datos


def _guardar(tipo: str, registros: list[dict]) -> None:
    p = ruta(ARCHIVOS[tipo])
    if tipo == "division":
        datos = json.loads(p.read_text(encoding="utf-8"))
        datos["divisiones"] = registros
    else:
        datos = registros
    p.write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _nombre(cid: str) -> str:
    return conceptos.vocabulario().get(cid, {}).get("nombre", cid)


# Por tipo: (clave del registro, descripción de la decisión, justificación, quién decidió).
DESCRIPCION: dict[str, tuple[Callable[[dict], str], Callable[[dict], str], str, str]] = {
    "equivalencia_retirada": (lambda r: f"{r['a']}|{r['b']}",
                              lambda r: f"Retirar la equivalencia «{_nombre(r['a'])}» ≡ «{_nombre(r['b'])}»",
                              "motivo_retiro", "retirado_por"),
    "prerrequisito_rechazado": (lambda r: f"{r['origen']}|{r['destino']}",
                                lambda r: (f"Rechazar el prerrequisito «{_nombre(r['origen'])}» → "
                                           f"«{_nombre(r['destino'])}»"),
                                "comentario", "revisado_por"),
    "division": (lambda r: r["concepto"],
                 lambda r: f"Dividir «{_nombre(r['concepto'])}»: se crea «{r['nuevo']['nombre']}»",
                 "justificacion", "revisado_por"),
    "clase_internacional": (lambda r: r["concepto"],
                            lambda r: f"Clase de «{r['nombre']}» en el contraste: {r['clase_ia']} → {r['clase']}",
                            "justificacion", "revisado_por"),
}


def _estado(r: dict) -> str:
    if r.get("observaciones"):
        return "observada (pide nueva decisión)"
    return "confirmada" if r.get("confirmaciones") else "pendiente de confirmar"


def _textos() -> dict[str, dict[str, str]]:
    """Texto de cada elemento que puede tener una asignación, por conjunto."""
    from goes_science_kg.ingesta import legado
    from goes_science_kg.ingesta.mallas import extraer
    from goes_science_kg.internacional.consenso import objetivos

    tema = lambda t: f"{t.contenido}. {t.indicador}"  # noqa: E731
    return {"malla_v1": {t.id: tema(t) for t in extraer()},
            "malla_v2": {t.id: tema(t) for t in extraer("mallas_v2")},
            "objetivos_pais": {o["id"]: o["texto"] for o in [*legado.alineacion_paises(), *legado.paises_nuevos()]},
            "internacional": {o["id"]: o["texto"] for o in objetivos()}}


def exportar_decisiones(fecha: str | None = None) -> list[str]:
    """Escribe los dos CSV para el equipo de Ciencias (sin sobrescribir los existentes). Devuelve las rutas."""
    fecha = fecha or date.today().isoformat()
    filas = []
    for tipo, (clave, descripcion, campo_just, campo_quien) in DESCRIPCION.items():
        for r in _leer(tipo):
            filas.append([clave(r), tipo, descripcion(r), r.get(campo_just, ""), r.get(campo_quien, ""), _estado(r),
                          "", "", "", ""])
    textos, asignaciones = _textos(), []
    for d in _leer("division"):
        for conjunto, items in sorted(d["asignaciones"].items()):
            for item, ids in sorted(items.items()):
                asignaciones.append([f"{d['concepto']}::{conjunto}::{item}", _nombre(d["concepto"]), conjunto, item,
                                     textos.get(conjunto, {}).get(item, "")[:300],
                                     " + ".join(_nombre(i) for i in ids), "", "", "", ""])
    p1, p2 = _libre(ruta(DIR) / f"{fecha}_decisiones.csv"), _libre(ruta(DIR) / f"{fecha}_asignaciones_division.csv")
    _escribir(p1, ENCABEZADO, filas)
    _escribir(p2, ENCABEZADO_ASIGNACIONES, asignaciones)
    return [str(p1), str(p2)]


def importar_decisiones(archivo: str | Path) -> dict:
    """Aplica un CSV revisado (de decisiones o de asignaciones). Valida todo antes de escribir; lanza ValueError si
    algo no cuadra. Devuelve los conteos y las decisiones observadas que piden una nueva decisión."""
    with open(ruta(archivo), encoding="utf-8-sig") as f:
        lector = csv.DictReader(f)
        es_asignacion = "conjunto" in (lector.fieldnames or [])
        filas = [r for r in lector if (r.get(COLUMNAS_DECISION[0]) or "").strip()]
    hoy, errores = date.today().isoformat(), []
    registros = {tipo: _leer(tipo) for tipo in ARCHIVOS}
    por_clave = {(tipo, DESCRIPCION[tipo][0](r)): r for tipo, rs in registros.items() for r in rs}
    divisiones = {d["concepto"]: d for d in registros["division"]}
    conteo = {"aceptar": 0, "cambiar": 0, "rechazar": 0}
    observadas = []
    for i, r in enumerate(filas, 2):
        decision = r[COLUMNAS_DECISION[0]].strip().lower()
        quien = (r.get(COLUMNAS_DECISION[3]) or "").strip()
        nota = {"revisado_por": quien, "fecha": hoy, "comentario": (r.get(COLUMNAS_DECISION[2]) or "").strip()}
        if decision not in conteo:
            errores.append(f"fila {i}: decisión desconocida {decision!r}")
            continue
        if not quien:
            errores.append(f"fila {i}: falta revisado_por")
            continue
        if es_asignacion:
            concepto, conjunto, item = r["clave"].split("::")
            d = divisiones.get(concepto)
            if not d or item not in d["asignaciones"].get(conjunto, {}):
                errores.append(f"fila {i}: asignación desconocida {r['clave']!r}")
                continue
            registro = d
            if decision == "cambiar":
                nuevos = [x.strip() for x in (r.get(COLUMNAS_DECISION[1]) or "").split(";") if x.strip()]
                if not nuevos or not set(nuevos) <= {concepto, d["nuevo"]["id"]}:
                    errores.append(f"fila {i}: «cambiar» admite solo {concepto} y/o {d['nuevo']['id']}")
                    continue
                d["asignaciones"][conjunto][item] = nuevos
            nota["elemento"] = f"{conjunto}::{item}"
        else:
            registro = por_clave.get((r["tipo"], r["clave"]))
            if registro is None:
                errores.append(f"fila {i}: decisión desconocida {r['tipo']}:{r['clave']}")
                continue
            if decision == "cambiar":
                errores.append(f"fila {i}: «cambiar» solo se usa en asignaciones; para otra decisión, «rechazar» y "
                               "explicar en el comentario")
                continue
        clave = "observaciones" if decision == "rechazar" else "confirmaciones"
        registro.setdefault(clave, []).append(nota)
        conteo[decision] += 1
        if decision == "rechazar":
            observadas.append(r["clave"])
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    for tipo, rs in registros.items():
        if rs:
            _guardar(tipo, rs)
    conceptos.divisiones.cache_clear()
    conceptos.vocabulario.cache_clear()
    conceptos.etiquetado.cache_clear()
    conceptos.etiquetado_paises.cache_clear()
    return {**conteo, "observadas_piden_nueva_decision": observadas}
