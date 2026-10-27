"""Materialización de preparaciones revisadas y propuestas pendientes, sin alterar el insumo."""

from __future__ import annotations

import json
from collections import Counter
from copy import deepcopy
from pathlib import Path

import yaml

from goes_science_kg.clases.presupuesto import comprobar_continuidad
from goes_science_kg.materiales.almacen import construir
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.compilacion import exportar
from goes_science_kg.produccion.revision_docente.auditoria import vincular
from goes_science_kg.produccion.revision_docente.correcciones import resumir
from goes_science_kg.produccion.revision_docente.edicion import ajustes_posteriores, validar_edicion
from goes_science_kg.produccion.revision_docente.fuentes import complementarias, guia_mezclas
from goes_science_kg.produccion.revision_docente.preparacion import biblioteca_origen

VERSION = "preparacion-malla-final-3"
LIMITE = (
    "Edición docente derivada de las mallas finales, con originales intactos. Cada paquete declara "
    "su revisión automática, contenido exacto y pendientes; un veto, abstención o falta de lectura "
    "impide considerarlo respaldado. No acredita eficacia en aula, alineación internacional, "
    "seguridad de prácticas no verificadas ni aprobación institucional. No es un guion cronometrado."
)


def compilar(registros, campana, biblioteca_base, *, ajustes=None):
    nuevos = deepcopy(registros)
    revisiones = resumir(nuevos, campana)
    controles_por_lote = {str(r["lote"]): r.get("controles_negativos", {}) for r in revisiones.values()}
    contextos_editoriales = ajustes_posteriores(nuevos, revisiones, ajustes) if ajustes else []
    for r in nuevos:
        if r["tipo"] == "paquete_unidad":
            hijos = r["documento"]["filas_ids"]
            pendientes = [id_ for id_ in hijos if revisiones[id_]["estado"] != "revision_automatica_completa"]
            revisiones[r["id"]]["dependencias_pendientes"] = pendientes
            if pendientes:
                revisiones[r["id"]]["estado"] = "revision_automatica_con_pendientes"
    for r in nuevos:
        d = r["documento"]
        validar_edicion(d["edicion_docente"])
        d.update(
            version_contenido=VERSION,
            biblioteca_didactica_v2=biblioteca_base,
            estado_revision=revisiones[r["id"]]["estado"],
            revision_docente=revisiones[r["id"]],
            limite_biblioteca=LIMITE,
        )
        r["estado"] = revisiones[r["id"]]["estado"]
    por_id = {r["id"]: r for r in nuevos}
    indice = []
    for r in nuevos:
        if r["tipo"] != "paquete_objetivo":
            continue
        d, e = r["documento"], r["documento"]["edicion_docente"]
        codigos = sorted({t["codigo"] for t in e["actividades"]})
        macros = sorted({macro(c) for c in codigos})
        indice.append(
            {
                "fila_id": r["id"],
                "grado": r["grados"][0],
                "asignatura": r["asignatura"],
                "unidad": r["unidad"],
                "objetivo": r["titulo"],
                "codigos": codigos,
                "macrohabilidades": macros,
                "tareas": len(e["actividades"]),
                "incidencias": len(d["revision_docente"]["faltan_roles"])
                + sum(len(v["hallazgos"]) for v in d["revision_docente"]["lecturas"]),
                "controles_cientificos": len(d["didactica"]["controles_cientificos"]),
                "caso_resuelto_id": e["caso_resuelto"]["id"] if e["caso_resuelto"] else None,
                "completacion_derivada": e["completacion"] is not None,
                "estado_revision": r["estado"],
            }
        )
    for r in nuevos:
        if r["tipo"] == "paquete_unidad":
            r["documento"]["mapa_docente"] = [
                {
                    "fila_id": id_,
                    "objetivo": por_id[id_]["titulo"],
                    "estado_revision": por_id[id_]["estado"],
                    "codigos": sorted(
                        {t["codigo"] for t in por_id[id_]["documento"]["edicion_docente"]["actividades"]}
                    ),
                }
                for id_ in r["documento"]["filas_ids"]
            ]
    reporte = {
        "version": "auditoria-revision-docente-1",
        "huella_final": nuevos[0]["documento"]["snapshot_id"],
        "biblioteca_didactica_v2": biblioteca_base,
        "paquetes": len(nuevos),
        "por_estado": dict(Counter(r["estado"] for r in nuevos)),
        "por_tipo_y_estado": {
            tipo: dict(Counter(r["estado"] for r in nuevos if r["tipo"] == tipo))
            for tipo in ("paquete_objetivo", "paquete_unidad")
        },
        "completaciones_derivadas": [i["fila_id"] for i in indice if i["completacion_derivada"]],
        "actividades_efectivas": sum(i["tareas"] for i in indice),
        "originales_modificados": 0,
        "logros_observados": 0,
        "controles_negativos_por_lote": controles_por_lote,
        "ajustes_editoriales_sin_relectura": [c["item_id"] for c in contextos_editoriales],
        "eficacia_observada": None,
        "pendientes": [
            {
                "id": r["id"],
                "grado": r["grados"][0],
                "asignatura": r["asignatura"],
                "titulo": r["titulo"],
                "faltan_roles": r["documento"]["revision_docente"]["faltan_roles"],
                "controles_fallidos": r["documento"]["revision_docente"].get("roles_sin_control_superado", []),
                "dependencias_pendientes": r["documento"]["revision_docente"].get("dependencias_pendientes", []),
                "hallazgos": [
                    {"rol": v["rol"], "veredicto": v["veredicto"], "ruta": h["ruta"], "problema": h["problema"]}
                    for v in r["documento"]["revision_docente"]["lecturas"]
                    for h in v["hallazgos"]
                ],
            }
            for r in nuevos
            if r["estado"] != "revision_automatica_completa"
        ],
        "limite": LIMITE,
    }
    return nuevos, reporte, sorted(indice, key=lambda i: i["fila_id"]), contextos_editoriales


def macro(codigo):
    return {"E": "explicacion_modelizacion", "D": "indagacion_datos", "I": "informacion_argumentacion_decisiones"}[
        codigo[0]
    ]


def guardar_entrega(base: Path, campana: Path, registros, destino: Path, zips: Path):
    if destino.exists() or zips.exists():
        raise ValueError("La nueva entrega necesita destinos propios")
    vincular(campana, base / "data/operaciones/registro.sqlite")
    b = biblioteca_origen(base)
    b.validar()
    anteriores, archivos = b.exportar()
    originales = {r["id"]: r["documento"] for r in anteriores}
    for r in registros:
        if r["tipo"] == "paquete_objetivo" and r["documento"]["original"] != originales[r["id"]]["original"]:
            raise ValueError("Se alteró la fila original antes de materializar")
    ajustes_raw = (base / "config/ajustes_editoriales_entrega.yaml").read_bytes()
    nuevos, reporte, filas, contextos_editoriales = compilar(
        registros, campana, b.manifest["id"], ajustes=yaml.safe_load(ajustes_raw)
    )
    fuente_indice = json.loads(archivos["didactica/indice.json"])
    indice = fuente_indice | {
        "version": "indice-didactico-2",
        "estado_revision": "revision_automatica_completa"
        if not reporte["pendientes"]
        else "revision_automatica_con_pendientes",
        "filas": filas,
        "limite": "Índice de preparaciones efectivas y sus lecturas; sin dominio observado.",
    }
    activos = {p: raw for p, raw in archivos.items() if not p.startswith("paquetes/")}
    for nombre in ("indice", "auditoria", "grafo"):
        activos[f"edicion_didactica_v2/{nombre}.json"] = activos["didactica/" + nombre + ".json"]
    activos["didactica/indice.json"] = serializar(indice)
    activos["didactica/auditoria.json"] = serializar(reporte)
    activos["informe.json"] = serializar(reporte)
    activos["didactica/completacion_mezclas.yaml"] = (base / "config/completacion_mezclas_ciencias.yaml").read_bytes()
    _, raw_guia = guia_mezclas(base / "data/revision_docente_20261026/fuentes")
    fuentes_ahora = {f["id"]: f for f in complementarias(base)}
    capturadas = {}
    for solicitud in json.loads((campana / "ronda_2.json").read_bytes()):
        for f in solicitud["fuentes"]:
            id_ = f.get("identidad_original", f["id"])
            if id_ in fuentes_ahora:
                capturadas[id_] = f
            if id_.startswith("MINED:GUIA3:") and f["fuente"]["sha256"] != sha(raw_guia):
                raise ValueError("La guía cambió después de fijar el contexto de revisión")
    if set(capturadas) != set(fuentes_ahora) or any(
        "".join(capturadas[id_]["fragmentos"]) != f["texto"] or capturadas[id_]["fuente"] != f["fuente"]
        for id_, f in fuentes_ahora.items()
    ):
        raise ValueError("Las referencias críticas cambiaron después de la revisión")
    if yaml.safe_load((base / "config/enmiendas_revision_docente.yaml").read_bytes()) != json.loads(
        (campana / "enmiendas_editoriales.json").read_bytes()
    ):
        raise ValueError("Las enmiendas archivadas no corresponden a la configuración actual")
    activos["didactica/referencias/mined_guia_3_t1.pdf"] = raw_guia
    activos["didactica/derivaciones_revision.yaml"] = (base / "config/derivaciones_revision_ciencias.yaml").read_bytes()
    for nombre in ("enmiendas_revision_docente", "referencias_revision_docente"):
        activos[f"didactica/{nombre}.yaml"] = (base / f"config/{nombre}.yaml").read_bytes()
    for p in sorted((base / "data/revision_docente_20261026/fuentes/criticas").iterdir()):
        if p.is_file() and not p.is_symlink():
            activos["didactica/referencias_criticas/" + p.name] = p.read_bytes()
    for p in sorted(campana.rglob("*.json")):
        if p.name.startswith("candidato_"):
            continue
        activos["didactica/revision/" + p.relative_to(campana).as_posix()] = p.read_bytes()
    activos["didactica/revision/edicion_editorial_posterior.json"] = serializar(
        {
            "contextos": contextos_editoriales,
            "limite": "Cambios posteriores sin votos; los resultados anteriores no se transfieren.",
        }
    )
    activos["didactica/ajustes_editoriales_entrega.yaml"] = ajustes_raw
    activos["didactica/grafo.json"] = serializar(grafo(nuevos))
    estado = "revision_automatica_completa" if not reporte["pendientes"] else "revision_automatica_con_pendientes"
    exportados = exportar(
        nuevos,
        activos,
        reporte,
        zips,
        version=VERSION,
        estado_revision=estado,
        archivos_comunes={
            "didactica/completacion_mezclas.yaml": activos["didactica/completacion_mezclas.yaml"],
        },
    )
    for p in [*(zips / e["archivo"] for e in exportados), zips / "indice.json"]:
        activos["paquetes/" + p.name] = p.read_bytes()
    consumo = comprobar_continuidad(base / "data/operaciones/registro.sqlite")
    manifest = construir(
        nuevos,
        activos,
        destino,
        procedencia=b.manifest["procedencia"]
        | {
            "version_diseno": VERSION,
            "biblioteca_didactica_v2": b.manifest["id"],
            "estado_revision": estado,
            "metodo": "edicion_derivada_y_cuatro_lecturas_sobre_contenido_exacto",
            "consumo_acumulado": consumo,
            "ledger_sha256": sha((base / "data/operaciones/registro.sqlite").read_bytes()),
        },
    )
    return manifest, reporte


def grafo(registros):
    nodos, aristas = [], []
    codigos = sorted(
        {
            t["codigo"]
            for r in registros
            if r["tipo"] == "paquete_objetivo"
            for t in r["documento"]["edicion_docente"]["actividades"]
        }
    )
    for m in sorted({macro(c) for c in codigos}):
        nodos.append({"id": "MACRO_PROPUESTA:" + m, "tipo": "macro_propuesta", "nombre": m})
    for c in codigos:
        id_ = "MICRO_LOCAL:" + c
        nodos.append(
            {
                "id": id_,
                "tipo": "microhabilidad_local",
                "codigo": c,
                "alcance": "Etiqueta local; su definición se conserva en el Excel de cada objetivo.",
            }
        )
        aristas.append({"origen": id_, "destino": "MACRO_PROPUESTA:" + macro(c), "tipo": "ORGANIZADO_EN"})
    for r in registros:
        if r["tipo"] != "paquete_objetivo":
            continue
        d = r["documento"]
        nodos.append(
            {
                "id": r["id"],
                "tipo": "objetivo_original",
                "grado": r["grados"][0],
                "estado_revision_derivada": r["estado"],
            }
        )
        criterio_por_tarea = {}
        for c in d["edicion_docente"]["criterios"]:
            id_ = "CRITERIO_EFECTIVO:" + sha(serializar([r["id"], c]))
            nodos.append(
                {
                    "id": id_,
                    "tipo": "criterio_propuesto",
                    "codigo_local": c["codigo"],
                    "criterios_observables": c["criterios_observables"],
                    "desempeno_observado": None,
                    "estado_revision": r["estado"],
                }
            )
            criterio_por_tarea.update({t: id_ for t in c["tarea_ids"]})
        for t in d["edicion_docente"]["actividades"]:
            id_ = "ACTIVIDAD_EFECTIVA:" + sha(serializar([r["id"], t]))
            nodos.append(
                {
                    "id": id_,
                    "tipo": "actividad_derivada",
                    "texto": t["texto"],
                    "codigo_local": t["codigo"],
                    "macro_propuesta": macro(t["codigo"]),
                    "origen_tarea_id": t["origen_tarea_id"],
                    "estado_revision": r["estado"],
                    "desempeno_observado": None,
                }
            )
            aristas.append({"origen": r["id"], "destino": id_, "tipo": "PROPONE_ACTIVIDAD_DERIVADA"})
            aristas.append({"origen": id_, "destino": "MICRO_LOCAL:" + t["codigo"], "tipo": "DECLARA_CODIGO_LOCAL"})
            aristas.append({"origen": id_, "destino": criterio_por_tarea[t["id"]], "tipo": "PROPONE_EVALUAR_CON"})
    return {
        "version": "grafo-didactico-2",
        "nodos": nodos,
        "aristas": aristas,
        "limite": "Versiona actividades efectivas; no acredita dominio ni prerrequisitos.",
    }
