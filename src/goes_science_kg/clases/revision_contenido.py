"""Impide liberar versiones con defectos conocidos o una muestra de revisión incompleta."""

from __future__ import annotations

import json

from goes_science_kg.clases.compilacion import leer_propio
from goes_science_kg.clases.validacion import huella_contenido
from goes_science_kg.materiales.compilacion import serializar, sha


def validar_seleccion(base, seleccion, *, obligatoria=False, excluidos=frozenset()):
    """Block released versions with known defects; objectives declared without a script keep their review open."""
    raiz = "data/clases_v4/auditoria_contenido/"
    archivo_plan = base / raiz / "plan.json"
    if not archivo_plan.exists() and not obligatoria:
        return None
    plan_raw = leer_propio(base, raiz + "plan.json").read_bytes()
    plan = json.loads(plan_raw)
    revision_raw = leer_propio(base, raiz + "revision_desarrollo.json").read_bytes()
    revision = json.loads(revision_raw)
    if (
        plan["version"] != "auditoria-contenido-desarrollo-1"
        or revision["version"] != "revision-contenido-desarrollo-1"
    ):
        raise ValueError("Versión de revisión del contenido desconocida")
    if revision["plan_sha256"] != sha(plan_raw):
        raise ValueError("La revisión pertenece a otro plan de muestra")
    casos = {c["fila_id"] for c in plan["casos"]}
    if obligatoria and len(casos) != 32:
        raise ValueError("La entrega completa requiere los 32 casos de revisión del contenido")
    filas = {r["fila_id"] for r in revision["revisiones"]}
    if len(casos) != len(plan["casos"]) or len(filas) != len(revision["revisiones"]) or filas != casos:
        raise ValueError("La revisión del contenido no cubre exactamente la muestra congelada")
    ruta_resoluciones = base / raiz / "resoluciones.json"
    resoluciones = (
        json.loads(leer_propio(base, raiz + "resoluciones.json").read_bytes()) if ruta_resoluciones.is_file() else {}
    )
    revisiones = list(revision["revisiones"])
    archivo_seguimiento = base / raiz / "seguimiento.json"
    if archivo_seguimiento.is_file():
        seguimiento = json.loads(leer_propio(base, raiz + "seguimiento.json").read_bytes())
        if seguimiento["version"] != "seguimiento-contenido-clases-1":
            raise ValueError("Versión de seguimiento del contenido desconocida")
        if any(r["fila_id"] not in seleccion and r["fila_id"] not in excluidos for r in seguimiento["revisiones"]):
            raise ValueError("El seguimiento incluye objetivos ajenos a la selección")
        revisiones.extend(seguimiento["revisiones"])
    abiertas = 0
    for r in revisiones:
        id_ = r["fila_id"]
        if id_ in excluidos:
            abiertas += 1
            continue
        anterior_raw = leer_propio(base, r["resultado"]).read_bytes()
        anterior = json.loads(anterior_raw)["filas"][id_]["guion"]
        if sha(anterior_raw) != r["resultado_sha256"] or sha(serializar(anterior)) != r["guion_sha256"]:
            raise ValueError("La revisión del contenido no corresponde al guion archivado")
        if r["estado"] not in {"requiere_correccion", "sin_defecto_material_en_revision"}:
            raise ValueError("Estado de revisión del contenido desconocido")
        actual_ref = seleccion[id_]
        actual_raw = leer_propio(base, actual_ref["resultado"]).read_bytes()
        actual = json.loads(actual_raw)["filas"][id_]["guion"]
        mismo = sha(serializar(actual)) == r["guion_sha256"]
        if mismo and r["estado"] == "sin_defecto_material_en_revision":
            continue
        resolucion = resoluciones.get(id_, {})
        if (
            mismo
            or huella_contenido(actual) == huella_contenido(anterior)
            or resolucion.get("estado") != "corregido_y_revisado"
            or resolucion.get("expediente") != actual_ref
            or resolucion.get("resultado_sha256") != sha(actual_raw)
            or resolucion.get("guion_sha256") != sha(serializar(actual))
            or len(resolucion.get("hallazgos_atendidos", [])) < len(r["hallazgos"])
            or any(not isinstance(h, str) or len(h.strip()) < 30 for h in resolucion.get("hallazgos_atendidos", []))
        ):
            raise ValueError("Un guion auditado cambió o conserva defectos sin una resolución exacta")
    return {
        "plan_sha256": sha(plan_raw),
        "revision_sha256": sha(revision_raw),
        "casos": len(casos),
        "revisiones_abiertas_sin_guion": abiertas,
    }
