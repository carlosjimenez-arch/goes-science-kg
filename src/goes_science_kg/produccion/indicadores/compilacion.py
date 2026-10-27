"""Agrupación literal por indicador y ámbito, sin equivalencias semánticas ni votos nuevos."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from copy import deepcopy

from goes_science_kg.materiales.compilacion import _entrada, serializar, sha

VERSION = "paquete-indicador-malla-final-1"
LIMITE = (
    "Paquete organizado por indicador de logro de la malla final. Las preparaciones se conservan "
    "íntegras y sus lecturas se refieren a esos contextos completos. El reagrupamiento y la "
    "correspondencia de cada actividad con el indicador no tienen revisión específica. "
    "No acredita desempeño observado, eficacia en aula ni aprobación institucional."
)
COMPLETO = "contextos_con_revision_completa"
PENDIENTE = "contextos_con_pendientes"


def normalizar_texto(texto):
    """Sólo normaliza espacios; conserva mayúsculas, puntuación y contenido científico."""
    return " ".join(texto.split())


def codigo_literal(texto):
    """Un prefijo de la celda, nunca un número mencionado dentro del enunciado."""
    m = re.match(r"^\s*(\d+(?:\.\d+)*)(?:\.)?\s+", texto)
    return m[1] if m else None


def orden_natural(texto):
    return tuple((0, int(p)) if p.isdecimal() else (1, p.casefold()) for p in re.split(r"(\d+)", texto))


def compilar(registros, *, biblioteca_id, snapshot_id):
    """Una celda lógica por indicador; conserva enunciados compuestos y contextos completos."""
    objetivos = [r for r in registros if r["tipo"] == "paquete_objetivo"]
    if not objetivos or len({r["id"] for r in objetivos}) != len(objetivos):
        raise ValueError("Se requieren objetivos únicos")
    grupos = defaultdict(list)
    for r in objetivos:
        d, o = r["documento"], r["documento"]["original"]
        if d["version_contenido"] != "preparacion-malla-final-3" or d["snapshot_id"] != snapshot_id:
            raise ValueError("Se requiere la misma edición V3 revisada para todos los objetivos")
        if sha(serializar(d["edicion_docente"])) != d["revision_docente"]["edicion_sha256"]:
            raise ValueError("La preparación difiere del contenido declarado por su revisión")
        if d["estado_revision"] != r["estado"] or d["revision_docente"]["estado"] != r["estado"]:
            raise ValueError("El estado de la preparación es inconsistente")
        if r["estado"] not in {"revision_automatica_completa", "revision_automatica_con_pendientes"}:
            raise ValueError("Estado de revisión de origen no reconocido")
        if r["grados"] != [o["grado"]] or (r["asignatura"], r["unidad"]) != (o["asignatura_malla"], o["unidad"]):
            raise ValueError("El ámbito del objetivo difiere del insumo")
        texto = o["indicadores_logro"]
        origen = "malla_final"
        if not texto.strip():
            if not d["edicion_docente"]["completacion"]:
                raise ValueError("Un indicador ausente necesita una completación explícita")
            texto, origen = d["edicion_docente"]["indicador"], "completacion_derivada"
        if not texto.strip():
            raise ValueError("No se publican indicadores vacíos")
        clave = (o["grado"], o["asignatura_malla"], o["unidad"], origen, normalizar_texto(texto))
        grupos[clave].append(r)

    paquetes, indice = [], []
    for (grado, asignatura, unidad, origen, canonico), padres in sorted(grupos.items()):
        padres = sorted(padres, key=lambda r: r["id"])
        texto = (
            padres[0]["documento"]["original"]["indicadores_logro"]
            if origen == "malla_final"
            else padres[0]["documento"]["edicion_docente"]["indicador"]
        )
        id_ = "INDICADOR-FINAL:" + sha(serializar([snapshot_id, grado, asignatura, unidad, origen, canonico]))
        estado = COMPLETO if all(r["estado"] == "revision_automatica_completa" for r in padres) else PENDIENTE
        codigo = codigo_literal(texto)
        d = {
            "version_contenido": VERSION,
            "snapshot_id": snapshot_id,
            "biblioteca_preparaciones_id": biblioteca_id,
            "indicador": {"texto": texto, "codigo": codigo, "origen": origen},
            "fuentes_originales": list(
                {
                    p["documento"]["fuente_original"]["archivo_local"]: p["documento"]["fuente_original"]
                    for p in padres
                }.values()
            ),
            "preparaciones": deepcopy(padres),
            "revision": {
                "estado_contextos": estado,
                "estado_reagrupamiento": "sin_revision_especifica",
                "alcance_lecturas": "preparaciones_completas_de_origen",
                "preparaciones_pendientes": [p["id"] for p in padres if p["estado"] != "revision_automatica_completa"],
                "llamadas_modelos": 0,
            },
            "limite_biblioteca": LIMITE,
        }
        paquetes.append(
            _entrada(
                id_,
                "V4",
                "paquete_indicador",
                texto,
                d,
                grados=[grado],
                asignatura=asignatura,
                unidad=unidad,
                estado=estado,
            )
        )
        indice.append(
            {
                "id": id_,
                "grado": grado,
                "asignatura": asignatura,
                "unidad": unidad,
                "codigo": codigo,
                "indicador": texto,
                "origen": origen,
                "estado_contextos": estado,
                "estado_reagrupamiento": "sin_revision_especifica",
                "filas_ids": [p["id"] for p in padres],
                "indicadores_docentes": sorted({p["documento"]["edicion_docente"]["indicador"] for p in padres}),
                "colision_codigo": False,
            }
        )
    por_codigo = defaultdict(list)
    for i in indice:
        if i["codigo"]:
            por_codigo[(i["grado"], i["asignatura"], i["unidad"], i["codigo"])].append(i)
    ambiguos = []
    for (grado, asignatura, unidad, codigo), items in sorted(por_codigo.items()):
        if len(items) > 1:
            for i in items:
                i["colision_codigo"] = True
            ambiguos.append(
                {
                    "grado": grado,
                    "asignatura": asignatura,
                    "unidad": unidad,
                    "codigo": codigo,
                    "indicadores_ids": [i["id"] for i in items],
                }
            )
    por_id = {i["id"]: i for i in indice}
    for p in paquetes:
        p["documento"]["indicador"]["colision_codigo"] = por_id[p["id"]]["colision_codigo"]
    informe = {
        "version": VERSION,
        "huella_final": snapshot_id,
        "biblioteca_preparaciones_id": biblioteca_id,
        "paquetes": len(paquetes),
        "filas_cubiertas": len(objetivos),
        "por_estado_contextos": dict(Counter(p["estado"] for p in paquetes)),
        "por_origen": dict(Counter(i["origen"] for i in indice)),
        "sin_codigo_en_texto": sum(i["codigo"] is None for i in indice),
        "codigos_ambiguos": ambiguos,
        "grupos_con_multiples_filas": [i["id"] for i in indice if len(i["filas_ids"]) > 1],
        "celdas_compuestas_conservadas": [
            r["id"]
            for r in sorted(objetivos, key=lambda r: r["id"])
            if "\n" in r["documento"]["original"]["indicadores_logro"]
        ],
        "originales_modificados": 0,
        "llamadas_modelos": 0,
        "estado_reagrupamiento": "sin_revision_especifica",
        "limite": LIMITE,
    }
    return (
        paquetes,
        sorted(
            indice,
            key=lambda i: (
                i["grado"],
                i["asignatura"],
                orden_natural(i["unidad"]),
                orden_natural(i["indicador"]),
                i["id"],
            ),
        ),
        informe,
    )
