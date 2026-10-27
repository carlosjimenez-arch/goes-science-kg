"""Propuestas de reparación trazables; ningún cambio conserva un voto de otro contenido."""

from __future__ import annotations

import json
from collections import defaultdict
from copy import deepcopy
from pathlib import Path

from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.revision_docente.calibracion import agregar, evaluar
from goes_science_kg.produccion.revision_docente.contratos import ROLES, DictamenLote, leer_ruta, validar_dictamen
from goes_science_kg.produccion.revision_docente.edicion import criterios, escribir_campo, validar_edicion
from goes_science_kg.produccion.revision_docente.ejecucion import guardar
from goes_science_kg.produccion.revision_docente.procesamiento import DictamenSeleccion, numerar_fuentes, procesar


def lecturas(solicitud, destino: Path, ronda):
    salida = {}
    for rol in ROLES:
        p = destino / "lecturas" / f"r{ronda}_l{solicitud['lote']}_{rol}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_bytes())
        if d["identidad"]["solicitud_sha256"] != sha(serializar(solicitud)) or d["identidad"]["rol"] != rol:
            raise ValueError("El voto no corresponde al contexto y rol seleccionados")
        if "salida_selecciones" in d:
            esperado = procesar(DictamenSeleccion.model_validate(d["salida_selecciones"]), solicitud, rol)
            if any(d[k] != v for k, v in esperado.items()):
                raise ValueError("Las decisiones no reproducen las selecciones originales")
        else:
            validar_dictamen(DictamenLote.model_validate(d["dictamen"]), solicitud)
        salida[rol] = d
    return salida


def reparar(registros, solicitudes, destino, reglas, *, resoluciones=None, fuentes_adicionales=()):
    nuevos, contextos = deepcopy(registros), deepcopy(solicitudes)
    por_id = {r["id"]: r for r in nuevos}
    cambios, conflictos, rechazadas = [], [], []
    resoluciones = resoluciones or {}
    for s in contextos:
        votos = lecturas(s, destino, 1)
        if set(votos) != set(ROLES):
            raise ValueError("Terminar las cuatro lecturas antes de proponer la reparación del lote")
        propuestas = defaultdict(list)
        for rol in ROLES:
            for item in votos[rol]["dictamen"]["items"]:
                for h in item["hallazgos"]:
                    if "tarea_de_transferencia_original" in h["ruta"]:
                        rechazadas.append(
                            {
                                "item_id": item["id"],
                                "rol": rol,
                                "hallazgo": h,
                                "motivo": "Antecedente literal; no es una instrucción efectiva.",
                            }
                        )
                        continue
                    if h["reemplazo"] and h["respaldo"]:
                        propuestas[(item["id"], h["ruta"])].append({"rol": rol, **h})
        alias_por_real = {i.get("identidad_original", i["id"]): i["id"] for i in s["items"]}
        for clave in resoluciones:
            real, ruta = clave.split("#", 1)
            if real in alias_por_real:
                propuestas.setdefault((alias_por_real[real], ruta), [])
        for (id_, ruta), opciones in sorted(propuestas.items()):
            item = next(i for i in s["items"] if i["id"] == id_)
            real = item.get("identidad_original", id_)
            anterior = leer_ruta(item["edicion"], ruta)
            clave = real + "#" + ruta
            reemplazo = resoluciones[clave] if clave in resoluciones else opciones[0]["reemplazo"]
            if len({o["reemplazo"] for o in opciones}) > 1:
                conflictos.append(
                    {
                        "item_id": real,
                        "ruta": ruta,
                        "alternativas": opciones,
                        "seleccion": reemplazo,
                        "regla": "Ciencia, currículo, psicopedagogía, adversarial; "
                        "prioridad editorial provisional, requiere las cuatro relecturas.",
                    }
                )
            if anterior == reemplazo:
                continue
            escribir_campo(item["edicion"], ruta, reemplazo)
            cambios.append(
                {
                    "item_id": real,
                    "ruta": ruta,
                    "anterior": anterior,
                    "nuevo": reemplazo,
                    "origen": opciones,
                    "resolucion_explicita": clave in resoluciones,
                }
            )
        for item in s["items"]:
            e = item["edicion"]
            if "actividades" in e:
                if any(t["codigo"] not in reglas["habilidades"] for t in e["actividades"]):
                    raise ValueError("La reparación propone un código local inexistente")
                # Conservar las mejoras de criterios; actualizar sus vínculos si cambió un código.
                previos = {c["codigo"]: c for c in e["criterios"]}
                actualizados = criterios(e["actividades"], reglas)
                for c in actualizados:
                    if c["codigo"] in previos:
                        anterior = previos[c["codigo"]]
                        c.update({k: v for k, v in anterior.items() if k != "tarea_ids"})
                e["criterios"] = actualizados
            validar_edicion(e)
            por_id[item.get("identidad_original", item["id"])]["documento"]["edicion_docente"] = e
    reparados = contextos
    for s in reparados:
        s["iteracion_lectura"] = 2
        agregar(s, nuevos)
        for j, f in enumerate(fuentes_adicionales, start=len(s["fuentes"])):
            nueva = numerar_fuentes({"fuentes": [f]})["fuentes"][0]
            nueva["identidad_original"], nueva["id"] = nueva["id"], f"F{j:04d}"
            s["fuentes"].append(nueva)
    guardar(destino / "candidato_2.json", nuevos)
    guardar(destino / "ronda_2.json", reparados)
    guardar(
        destino / "reparaciones.json",
        {"cambios": cambios, "conflictos": conflictos, "propuestas_no_aplicadas": rechazadas},
    )
    return nuevos, reparados, cambios, conflictos


def resumir(registros, destino):
    originales = json.loads((destino / "ronda_1.json").read_bytes())
    reparados = json.loads((destino / "ronda_2.json").read_bytes()) if (destino / "ronda_2.json").exists() else []
    contextos = {s["lote"]: (s, 1) for s in originales}
    contextos.update({s["lote"]: (s, 2) for s in reparados})
    revisiones = {}
    for solicitud, ronda in contextos.values():
        votos = lecturas(solicitud, destino, ronda)
        controles = evaluar(solicitud, votos)
        for item in solicitud["items"]:
            if item["id"] in solicitud.get("controles_revision", {}).get("claves", {}):
                continue
            real = item.get("identidad_original", item["id"])
            decisiones = []
            for rol, voto in votos.items():
                lectura = next((v for v in voto["dictamen"]["items"] if v["id"] == item["id"]), None)
                if lectura is None:
                    continue
                fuentes = {f["id"]: f for f in solicitud["fuentes"]}
                lectura = deepcopy(lectura)
                for ref in lectura["respaldos"]:
                    ref["localizador"] = fuentes[ref["fuente_id"]]["fuente"]
                    ref["identidad_original"] = fuentes[ref["fuente_id"]].get("identidad_original", ref["fuente_id"])
                decisiones.append(
                    {
                        "rol": rol,
                        "modelo": voto["identidad"]["modelo"],
                        "lectura_sha256": sha(serializar(voto)),
                        **lectura,
                    }
                )
            falta = sorted(set(ROLES) - {d["rol"] for d in decisiones})
            fallan_controles = [rol for rol, c in controles.items() if not c["superado"]]
            completo = not falta and not fallan_controles and all(v["veredicto"] == "aprobar" for v in decisiones)
            revisiones[real] = {
                "estado": "revision_automatica_completa" if completo else "revision_automatica_con_pendientes",
                "edicion_sha256": sha(serializar(item["edicion"])),
                "lote": solicitud["lote"],
                "ronda": ronda,
                "contexto_sha256": sha(serializar(solicitud)),
                "lecturas": decisiones,
                "faltan_roles": falta,
                "roles_sin_control_superado": fallan_controles,
                "controles_negativos": controles,
                "errores_validacion": {
                    rol: voto.get("validacion_local", {}).get("errores_por_item", {}).get(item["id"])
                    for rol, voto in votos.items()
                    if item["id"] in voto.get("validacion_local", {}).get("errores_por_item", {})
                },
                "limite": "Lecturas automáticas sobre este contenido exacto; proveedor compartido, "
                "sin independencia estadística, aprobación institucional ni eficacia observada.",
            }
    if set(revisiones) != {r["id"] for r in registros}:
        raise ValueError("El resumen perdió paquetes")
    for r in registros:
        if sha(serializar(r["documento"]["edicion_docente"])) != revisiones[r["id"]]["edicion_sha256"]:
            raise ValueError("El paquete difiere del contenido revisado")
    return revisiones
