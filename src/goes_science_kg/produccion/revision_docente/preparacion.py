"""Fija el corpus, las propuestas y la cota de revisión antes de gastar una invocación."""

from __future__ import annotations

from pathlib import Path

import yaml

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.materiales.almacen import Biblioteca
from goes_science_kg.produccion.didactica.catalogo import definiciones
from goes_science_kg.produccion.revision_docente.contexto import (
    codificar_identidades,
    fuentes,
    fuentes_por_objetivo,
    lotes_equilibrados,
)
from goes_science_kg.produccion.revision_docente.edicion import corregir_omisiones, crear
from goes_science_kg.produccion.revision_docente.ejecucion import guardar, preflight, proveedor_cfg
from goes_science_kg.produccion.revision_docente.fuentes import guia_mezclas
from goes_science_kg.produccion.revision_docente.procesamiento import numerar_fuentes


def biblioteca_origen(base: Path):
    origen = base / "data/materiales_produccion_v4_didactica_v2"
    if not (origen / "manifest.json").is_file():
        origen = base / "data/materiales_produccion_v4"
    biblioteca = Biblioteca(origen)
    biblioteca.validar()
    if biblioteca.manifest["procedencia"].get("version_diseno") != "preparacion-malla-final-2":
        raise ValueError("Se requiere la edición didáctica V2, sin sustituir su captura")
    return biblioteca


def preparar(base: Path, destino: Path):
    biblioteca = biblioteca_origen(base)
    rs, fs = biblioteca.exportar()
    reglas = yaml.safe_load(fs["didactica/reglas.yaml"])
    completacion = yaml.safe_load((base / "config/completacion_mezclas_ciencias.yaml").read_bytes())
    registros = crear(rs, completacion, reglas, biblioteca.manifest["procedencia"]["snapshot_id"])
    registros = corregir_omisiones(
        registros,
        yaml.safe_load((base / "config/derivaciones_revision_ciencias.yaml").read_bytes()),
        reglas,
        biblioteca.manifest["procedencia"]["snapshot_id"],
    )
    documentos = fuentes(base, fs)
    extra, enlaces = fuentes_por_objetivo(base, registros)
    solicitudes = lotes_equilibrados(registros, documentos)
    catalogo = definiciones(Curriculo.model_validate_json(fs["curriculo.json"]))
    guia, _ = guia_mezclas(base / "data/revision_docente_20261026/fuentes")
    for s in solicitudes:
        ids = {id_ for i in s["items"] for id_ in enlaces.get(i["id"], [])}
        s["fuentes"] += [extra[id_] for id_ in sorted(ids) if id_ not in {x["id"] for x in documentos}]
        s["fuentes"] += guia
        libros = {i["original"]["fuente_id"] for i in s["items"] if i["original"] is not None}
        s["catalogo_local"] = [d.model_dump(mode="json") for (f, _), d in sorted(catalogo.items()) if f in libros]
        for i in s["items"]:
            i["fuentes_recuperadas_ids"] = enlaces.get(i["id"], [])
    solicitudes = [numerar_fuentes(codificar_identidades(s)) for s in solicitudes]
    plan = preflight(solicitudes, base / "data/operaciones/registro.sqlite", proveedor_cfg())
    plan["biblioteca_origen"] = biblioteca.manifest["id"]
    plan["filas_con_recuperacion_documental"] = len(enlaces)
    plan["pasajes_adicionales_verificados"] = len(extra)
    guardar(destino / "candidato_1.json", registros)
    guardar(destino / "ronda_1.json", solicitudes)
    guardar(destino / "preflight.json", plan)
    return plan
