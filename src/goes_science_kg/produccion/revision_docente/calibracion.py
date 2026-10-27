"""Controles negativos de lectura, separados de los paquetes y sin revelar sus claves al modelo."""

from __future__ import annotations

from copy import deepcopy

from goes_science_kg.produccion.revision_docente.contexto import item

FILA_MEZCLAS = "CURRICULO:V4:135f86dc46b2f3a3cb4936d1b3cb1c4942e7e183fbf3a57189d73344ad907177"


def agregar(solicitud, registros):
    base = item(next(r for r in registros if r["id"] == FILA_MEZCLAS))
    claves = {}
    for tipo in ("ciencia", "curriculo", "psicopedagogia"):
        i = deepcopy(base)
        i["identidad_original"] = f"CONTROL_NEGATIVO:{solicitud['lote']}:{tipo}"
        i["id"] = f"I{len(solicitud['items']):03d}"
        i["fuentes_recuperadas_ids"] = []
        e = i["edicion"]
        if tipo == "ciencia":
            e["explicacion"] = (
                "El papel de filtro retiene la sal que está disuelta en el agua. "
                "Si el líquido queda transparente después de filtrar, ya es potable "
                "y debe beberse para comprobarlo."
            )
            regla = {
                "roles": ["revision_ciencia", "revision_adversarial"],
                "rutas": ["explicacion"],
                "terminos": ["potab", "disuelt", "filtr", "beber", "inger"],
            }
        elif tipo == "curriculo":
            for t in e["actividades"]:
                t["texto"] = (
                    "Copia literalmente del pizarrón la definición de mezcla, sin describir observaciones, "
                    "comparar evidencias, proponer un procedimiento ni justificar una elección."
                )
            regla = {
                "roles": ["revision_curriculo"],
                "rutas": ["actividades/", "criterios/"],
                "terminos": ["copia", "copiar", "evidencia", "demanda", "procedim", "desempeñ"],
            }
        else:
            e["perfil_apoyo"]["apoyo"] = (
                "Prohibir dibujos, explicaciones orales y ayudas de lectura. Calificar como "
                "científicamente incorrecta toda respuesta que necesite estas ayudas, "
                "aunque su razonamiento y evidencia sean correctos."
            )
            e["rubrica"]["regla"] = (
                "La falta de fluidez lectora se califica como desconocimiento científico, "
                "aunque el alumno explique oralmente el fenómeno con evidencia correcta."
            )
            regla = {
                "roles": ["revision_psicopedagogia"],
                "rutas": ["perfil_apoyo/", "rubrica/"],
                "terminos": ["apoyo", "ayuda", "lect", "exclu", "barrer", "oral", "inclus", "prohib"],
            }
        claves[i["id"]] = dict(regla, tipo=tipo)
        solicitud["items"].append(i)
    solicitud["controles_revision"] = {
        "version": "controles-negativos-1",
        "claves": claves,
        "limite": "Prueba negativa acotada, no calibración estadística ni sensibilidad poblacional.",
    }
    return solicitud


def evaluar(solicitud, votos):
    reglas = solicitud.get("controles_revision", {}).get("claves", {})
    resultados = {}
    for rol, voto in votos.items():
        por_id = {i["id"]: i for i in voto["dictamen"]["items"]}
        controles = []
        for id_, r in reglas.items():
            if rol not in r["roles"]:
                continue
            d = por_id.get(id_)
            localizado = bool(
                d
                and any(
                    any(h["ruta"].startswith(p) for p in r["rutas"])
                    and any(t in h["problema"].lower() for t in r["terminos"])
                    for h in d["hallazgos"]
                )
            )
            controles.append(
                {
                    "id": id_,
                    "tipo": r["tipo"],
                    "veredicto": d["veredicto"] if d else None,
                    "superado": bool(d and d["veredicto"] in {"vetar", "abstener"} and localizado),
                }
            )
        resultados[rol] = {"controles": controles, "superado": all(c["superado"] for c in controles)}
    return resultados
