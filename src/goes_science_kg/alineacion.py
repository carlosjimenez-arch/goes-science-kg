"""Lotes de alineación de temas de la malla contra un catálogo pivote (skill alinear-objetivos).

preparar → data/interim/alineaciones/lotes/lote_<nombre>.json   (lo lee un subagente)
           el subagente escribe salida_<nombre>.json: [{id, obj1, obj2, confianza, justificacion}]
unir     → data/interim/alineaciones/<destino>.json            (validado: códigos, ids, confianza)

Hoy se usa para Biología y Química de 10.°–11.° contra ACARA Senior Secondary (marco AUSS).
"""

from __future__ import annotations

import json
from collections import Counter

from goes_science_kg.config import relativa, ruta
from goes_science_kg.ingesta.mallas import TemaMalla, extraer

DIR = "data/interim/alineaciones"
CONFIANZAS = {"alta", "media", "baja"}
CAMPOS_TEMA = ("id", "unidad", "contenido", "subcontenido", "procedimental", "indicador")


def preparar_bachillerato(catalogo: list[dict], version: str) -> list[str]:
    """Un lote por asignatura y grado (Biología y Química de 10.° y 11.°)."""
    d = ruta(DIR) / "lotes"
    d.mkdir(parents=True, exist_ok=True)
    escritos = []
    temas = [t for t in extraer() if t.asignatura in ("biologia", "quimica")]
    for (asig, grado) in sorted({(t.asignatura, t.grado) for t in temas}):
        objs = [{k: o[k] for k in ("codigo", "unidad", "eje", "tema", "objetivo")}
                for o in catalogo if o["asignatura"] == asig]
        lote = {
            "lote": f"AUSS_{asig}_G{grado}", "version": version, "marco": "AUSS",
            "instrucciones": "prompts/alinear_bachillerato_auss.md",
            "catalogo": objs,
            "items": [{k: getattr(t, k) for k in CAMPOS_TEMA} for t in temas
                      if t.asignatura == asig and t.grado == grado],
        }
        p = d / f"lote_{lote['lote']}.json"
        p.write_text(json.dumps(lote, ensure_ascii=False, indent=1), encoding="utf-8")
        escritos.append(relativa(p))
    return escritos


def unir(prefijo_lote: str, destino: str, catalogo: list[dict]) -> dict:
    """Valida y une las salidas de los subagentes. Lanza ValueError ante cualquier problema."""
    d = ruta(DIR) / "lotes"
    codigos = {o["codigo"] for o in catalogo}
    por_tema: dict[str, TemaMalla] = {t.id: t for t in extraer()}
    filas, errores = [], []
    for p_lote in sorted(d.glob(f"lote_{prefijo_lote}*.json")):
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        salida = {s["id"]: s for s in json.loads(p_sal.read_text(encoding="utf-8"))}
        esperados = {i["id"] for i in lote["items"]}
        if faltan := esperados - salida.keys():
            errores.append(f"{p_sal.name}: faltan {len(faltan)} ids, p. ej. {sorted(faltan)[:3]}")
        for i in sorted(esperados & salida.keys()):
            s = salida[i]
            obj1, obj2 = s.get("obj1") or "", s.get("obj2") or ""
            if obj1 != "FUERA" and obj1 not in codigos:
                errores.append(f"{i}: obj1 inválido {obj1!r}")
            if obj2 and (obj2 not in codigos or obj2 == obj1):
                errores.append(f"{i}: obj2 inválido {obj2!r}")
            if s.get("confianza") not in CONFIANZAS:
                errores.append(f"{i}: confianza inválida {s.get('confianza')!r}")
            if not s.get("justificacion"):
                errores.append(f"{i}: sin justificación")
            t = por_tema[i]
            filas.append({"id": i, "archivo": t.archivo, "hoja": t.hoja, "fila": t.fila,
                          "procedimental": t.procedimental, "obj1": obj1,
                          "obj2": "" if obj2 == "FUERA" else obj2, "confianza": s.get("confianza"),
                          "justificacion": s.get("justificacion"), "version": lote["version"],
                          "revisado_por": ""})
    if errores:
        raise ValueError(f"{len(errores)} errores al unir: " + "; ".join(errores[:15]))
    salida = ruta(DIR) / f"{destino}.json"
    salida.write_text(json.dumps(filas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"temas": len(filas), "confianza": dict(Counter(f["confianza"] for f in filas)),
            "fuera": sum(f["obj1"] == "FUERA" for f in filas)}
