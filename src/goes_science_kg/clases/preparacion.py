"""Congela objetivos, escenario, fuentes y lotes; ningún recorte elimina filas del denominador."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from goes_science_kg.clases.contratos import MAX_CONTEXTO_BYTES
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.materiales.compilacion import serializar
from goes_science_kg.motor.contratos import huella

ESCENARIO = {
    "version": "clases-escenario-1",
    "minutos_por_sesion_propuesta": 60,
    "recursos_base_hipoteticos": ["papel", "lapiz", "pizarra"],
    "conectividad_propuesta": "sin_conexion",
    "limite": "Duraciones y recursos son propuestas. No acreditan carga oficial ni disponibilidad escolar.",
}


def contexto(preparacion, *, ids=None):
    seleccion = [f for f in preparacion["filas"] if ids is None or f["fila_id"] in ids]
    fuentes = {i for f in seleccion for i in f["fuentes_cientificas_ids"]}
    return {
        "escenario": preparacion["escenario"],
        "filas": seleccion,
        "fuentes": [f for f in preparacion["fuentes"] if f["id"] in fuentes],
    }


def preparar(base: Path, corpus, destino: Path, *, consultas=None):
    biblioteca = Biblioteca(base / "data/materiales")
    biblioteca.validar()
    if destino.exists() or destino.is_symlink():
        raise ValueError("La preparación requiere un directorio nuevo")
    registros = []
    offset = 0
    while True:
        pagina = biblioteca.listar(tipo="paquete_objetivo", limite=200, offset=offset)
        registros.extend(pagina["materiales"])
        offset += len(pagina["materiales"])
        if offset == pagina["total"]:
            break
    grupos = defaultdict(list)
    evidencias = {}
    for r in registros:
        d = biblioteca.detalle(r["id"])["documento"]
        propuesta = d["propuesta"]
        texto = " ".join([propuesta["objetivo_propuesto"], d["original"]["contenido"], d["unidad"]])
        consulta = (consultas or {}).get(r["id"], "")
        fuentes = corpus.buscar(consulta + " " + texto, k=4, max_caracteres=7000)
        if len(fuentes) < 2:
            raise ValueError(
                "Contexto científico insuficiente para " + r["id"] + ": " + propuesta["objetivo_propuesto"]
            )
        for e in fuentes:
            corpus.verificar(e)
            evidencias[e.id] = e.model_dump(mode="json")
        fila = {
            "fila_id": r["id"],
            "grado": d["grado"],
            "asignatura": d["asignatura"],
            "unidad": d["unidad"],
            "propuesta": propuesta,
            "alerta_original": d["alerta_original"],
            "enmiendas": d["enmiendas"],
            "origen": {
                "fuente_id": d["original"]["fuente_id"],
                "hoja": d["hoja"],
                "fila": d["fila"],
                "sha256": d["fuente_original"]["sha256"],
            },
            "fuentes_cientificas_ids": [e.id for e in fuentes],
            "consulta_recuperacion": consulta,
        }
        grupos[(d["grado"], d["asignatura"], d["unidad"])].append(fila)
    lotes = []

    def anexar(filas):
        ids = {id_ for f in filas for id_ in f["fuentes_cientificas_ids"]}
        datos = {
            "version": "preparacion-clases-1",
            "biblioteca_id": biblioteca.manifest["id"],
            "snapshot_id": biblioteca.manifest["procedencia"]["snapshot_id"],
            "corpus_sha256": corpus.huella,
            "escenario": ESCENARIO,
            "filas": filas,
            "fuentes": [evidencias[i] for i in sorted(ids)],
        }
        if len(serializar(contexto(datos))) > MAX_CONTEXTO_BYTES:
            if len(filas) == 1:
                raise ValueError("La fila excede el contexto de generación; no se trunca")
            mitad = len(filas) // 2
            anexar(filas[:mitad])
            anexar(filas[mitad:])
            return
        datos["id"] = huella(datos)
        lotes.append(datos)

    for _clave, filas in sorted(grupos.items()):
        filas.sort(key=lambda f: (f["origen"]["hoja"], f["origen"]["fila"], f["fila_id"]))
        for i in range(0, len(filas), 4):
            anexar(filas[i : i + 4])
    todos = [f["fila_id"] for p in lotes for f in p["filas"]]
    if len(todos) != len(set(todos)) or set(todos) != {r["id"] for r in registros}:
        raise ValueError("Los lotes no conservan el denominador íntegro")
    destino.mkdir(parents=True)
    for numero, lote in enumerate(lotes, 1):
        (destino / f"lote_{numero:03d}.json").write_bytes(serializar(lote))
    resumen = {
        "version": "plan-clases-1",
        "biblioteca_id": biblioteca.manifest["id"],
        "snapshot_id": biblioteca.manifest["procedencia"]["snapshot_id"],
        "corpus_sha256": corpus.huella,
        "filas": len(registros),
        "unidades": len(grupos),
        "lotes": len(lotes),
        "grados": dict(sorted(Counter(f["grado"] for p in lotes for f in p["filas"]).items())),
        "preparaciones": [p["id"] for p in lotes],
        "llamadas_minimas_primera_pasada": len(lotes) * 5,
        "llamadas_maximas_dos_rondas": len(lotes) * 10,
        "fuentes_cientificas_seleccionadas": len(evidencias),
        "modelo_contexto": "CNXML primario bilingue",
    }
    (destino / "plan.json").write_bytes(serializar(resumen))
    return resumen


def leer_preparacion(p):
    d = json.loads(p.read_bytes())
    if d["id"] != huella({k: v for k, v in d.items() if k != "id"}):
        raise ValueError("La preparación cambió")
    return d


def validar_importacion(preparacion, base):
    """Un guion importado debe corresponder a una abstención técnica real sin votos previos."""
    if not preparacion.get("borrador_inicial"):
        return
    ref = preparacion["antecedente_sin_dictamenes"]
    p = base / ref["ruta"]
    if (
        p.is_symlink()
        or any(a.is_symlink() for a in p.parents)
        or not p.resolve().is_relative_to((base / "data/clases_v4/ejecuciones").resolve())
    ):
        raise ValueError("El antecedente debe pertenecer al expediente propio de Ciencias")
    raw = p.read_bytes()
    if hashlib.sha256(raw).hexdigest() != ref["sha256"]:
        raise ValueError("El antecedente técnico cambió")
    r = json.loads(raw)
    if r["snapshot_id"] != preparacion["snapshot_id"]:
        raise ValueError("El antecedente pertenece a otro snapshot")
    for g in preparacion["borrador_inicial"]["guiones"]:
        fila = r["filas"][g["fila_id"]]
        original = fila["guion"]
        if original is None and r["rondas"][-1].get("respuesta_rechazada"):
            raw_borrador = json.loads(r["rondas"][-1]["respuesta_rechazada"])
            candidatos = [f for f in raw_borrador["guiones"] if f["fila_id"] == g["fila_id"]]
            original = candidatos[0] if len(candidatos) == 1 else None
        if fila["estado"] != "abstencion" or fila["dictamenes"] or original != g:
            raise ValueError("No se importa un guion cambiado o con dictámenes anteriores")
