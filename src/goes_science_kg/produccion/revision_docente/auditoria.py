"""Vincula cada selección archivada con la respuesta realmente recibida en el ledger compartido."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from goes_science_kg.clases.presupuesto import configuracion
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.motor.vertex import clave_solicitud
from goes_science_kg.produccion.revision_docente.contratos import ROLES
from goes_science_kg.produccion.revision_docente.ejecucion import TRANSPORTE, guardar, mensaje, proveedor_cfg
from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion
from goes_science_kg.produccion.revision_docente.prompts import sistema


def vincular(campana: Path, ledger: Path):
    cfg = proveedor_cfg()
    contextos = {}
    for ronda in (1, 2):
        p = campana / f"ronda_{ronda}.json"
        if p.exists():
            contextos.update({(ronda, s["lote"]): s for s in json.loads(p.read_bytes())})
    vinculos = {}
    with closing(sqlite3.connect(ledger.resolve().as_uri() + "?mode=ro", uri=True)) as db:
        db.row_factory = sqlite3.Row
        for p in sorted((campana / "lecturas").glob("*.json")):
            d = json.loads(p.read_bytes())
            identidad = d["identidad"]
            rol = identidad["rol"]
            if rol not in ROLES:
                raise ValueError("Rol ajeno al protocolo")
            s = contextos[(identidad["ronda"], identidad["lote"])]
            prompt = mensaje(s)
            if (
                identidad["solicitud_sha256"] != sha(serializar(s))
                or identidad["mensaje_sha256"] != sha(prompt.encode())
                or identidad["sistema_sha256"] != sha(sistema(rol).encode())
                or identidad["modelo"] != cfg.modelos[rol]
                or identidad["transporte_sha256"] != sha(serializar(TRANSPORTE.model_json_schema()))
            ):
                raise ValueError("Cambió el contexto o la configuración del lector")
            from goes_science_kg.config import cargar

            original = cargar("mejoras_curriculares")["vertex"]["niveles_razonamiento"]
            niveles = dict(cfg.niveles_razonamiento)
            niveles[rol] = identidad.get("nivel_razonamiento", original.get(rol))
            actual = cfg.model_copy(update={"niveles_razonamiento": niveles})
            clave = clave_solicitud(actual, rol=rol, sistema=sistema(rol), mensaje=prompt, esquema=TRANSPORTE)
            filas = db.execute(
                "SELECT l.id,l.estado,l.modelo,l.rol,s.texto,s.sha256 FROM llamadas l "
                "JOIN salidas_llm s ON s.llamada=l.id WHERE l.clave=? AND l.ejecucion=? ORDER BY l.creada,l.id",
                (clave, configuracion()["ejecucion"]),
            ).fetchall()
            correctas = []
            for r in filas:
                if r["estado"] not in {"completada", "fallida"} or r["modelo"] != cfg.modelos[rol] or r["rol"] != rol:
                    continue
                if sha(r["texto"].encode()) != r["sha256"]:
                    continue
                if parcial := d.get("recuperacion_parcial"):
                    from goes_science_kg.produccion.revision_docente.recuperacion import extraer_prefijo

                    seleccion, meta = extraer_prefijo(r["texto"])
                    if parcial != meta | {"llamada_id": r["id"], "respuesta_sha256": r["sha256"]}:
                        raise ValueError("La recuperación parcial no corresponde a la respuesta original")
                else:
                    seleccion = DictamenSeleccion.model_validate_json(r["texto"])
                if seleccion.model_dump(mode="json") == d["salida_selecciones"]:
                    correctas.append(r)
            if not correctas:
                raise ValueError("El checkpoint no reproduce una respuesta recibida verificable del proveedor")
            r = correctas[-1]
            vinculos[p.name] = {
                "clave": clave,
                "llamada_id": r["id"],
                "respuesta_sha256": r["sha256"],
                "lectura_sha256": sha(p.read_bytes()),
                "modelo": r["modelo"],
                "rol": rol,
                "estado_original_ledger": r["estado"],
                "respuesta_parcial": bool(d.get("recuperacion_parcial")),
                "recuperacion_local_sin_nueva_invocacion": r["estado"] == "fallida",
            }
    documento = {
        "version": "vinculos-ledger-revision-1",
        "lecturas": vinculos,
        "llamadas_nuevas": 0,
        "ledger_sha256": sha(ledger.read_bytes()),
    }
    guardar(campana / "vinculos_proveedor.json", documento)
    return documento
