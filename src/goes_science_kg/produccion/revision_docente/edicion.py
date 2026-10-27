"""Preparación efectiva derivada, siempre separada de las celdas y declaraciones originales."""

from __future__ import annotations

from copy import deepcopy

from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.produccion.revision_docente.contratos import ROLES, leer_ruta

FASES = {"aproximar", "explorar", "explicar", "indagar", "reforzar"}


def crear(registros, completacion, reglas, huella):
    if completacion["huella_curriculo"] != huella:
        raise ValueError("La completación pertenece a otra captura")
    salida = deepcopy(registros)
    completadas = 0
    for r in salida:
        d = r["documento"]
        if r["tipo"] == "paquete_unidad":
            d["edicion_docente"] = deepcopy(
                {
                    "articulacion": d["didactica_unidad"]["articulacion"],
                    "progresion": d["didactica_unidad"]["progresion_propuesta"],
                    "regla": d["didactica_unidad"]["regla"],
                    "filas_ids": d["filas_ids"],
                }
            )
            continue
        f = d["didactica"]
        actividades = [
            {
                "id": t["id"],
                "fase": t["fase"],
                "codigo": t["codigo"],
                "texto": t["actividad_literal"],
                "origen_tarea_id": t["id"],
            }
            for t in f["tareas"]
        ]
        e = {
            "indicador": f["indicador_original"],
            "producto": f["producto_original"],
            "explicacion": f["transposicion"]["nucleo_conceptual_declarado"]
            or "Contenido declarado: " + d["original"]["contenido"] + ". " + d["original"]["subcontenido"],
            "actividades": actividades,
            "criterios": deepcopy(f["criterios"]),
            "perfil_apoyo": f["perfil_apoyo"],
            "aplicacion": f["aplicacion"],
            "recuperacion": f["recuperacion"],
            "seguridad": f["contexto_y_factibilidad"]["seguridad"],
            "factibilidad": f["contexto_y_factibilidad"],
            "caso_resuelto": f["caso_resuelto"],
            "rubrica": f["transposicion"]["rubrica"],
            "completacion": None,
        }
        e = deepcopy(e)
        if "Las biomoléculas son polímeros orgánicos" in e["explicacion"]:
            e["explicacion"] = (
                "Las biomoléculas incluyen moléculas pequeñas y macromoléculas. Algunas macromoléculas, "
                "como las proteínas y los ácidos nucleicos, son polímeros; no todas las biomoléculas lo son. "
                "Su estructura y propiedades se relacionan con sus funciones biológicas."
            )
        if any(c["referencia_id"] == "openstax_resorte" for c in f["controles_cientificos"]):
            for t in actividades:
                if "interpreta la pendiente como su constante elástica" in t["texto"]:
                    t["texto"] = (
                        "Obtiene la ecuación del resorte: en x frente a F interpreta la pendiente como 1/k, "
                        "en m/N; al invertir los ejes a F frente a x la pendiente es k, en N/m. "
                        "Delimita el intervalo compatible con el modelo sin extrapolar fuera de los datos."
                    )
        if any(c["referencia_id"] == "openstax_disolucion" for c in f["controles_cientificos"]):
            for t in actividades:
                if "soplar" in t["texto"]:
                    t["texto"] = (
                        "Analiza un registro documental de formación de un precipitado con reactivos identificados, "
                        "distingue observación e interpretación y explica qué evidencia respalda sustancias nuevas. "
                        "No se sopla en soluciones ni se ejecuta esta demostración en el aula."
                    )
                if "cuatro estaciones de reactivos seguros" in t["texto"]:
                    t["texto"] = (
                        "Propone un diseño documental para comparar observaciones antes y después de mezclar "
                        "sustancias identificadas, con controles y registros; explica por qué color, burbujas "
                        "o temperatura por separado no identifican una reacción. La ejecución experimental requiere "
                        "evaluación específica de materiales, cantidades, supervisión y residuos; no se autoriza aquí."
                    )
        if r["id"] == completacion["fila_id"]:
            if actividades or e["indicador"] or e["producto"]:
                raise ValueError("No se completa una fila que ya contiene esos campos")
            completadas += 1
            for k in ("indicador", "producto", "explicacion", "seguridad"):
                e[k] = completacion[k]
            e["actividades"] = [
                dict(t, id="DERIVADA:" + sha(serializar([r["id"], i, t])), origen_tarea_id=None)
                for i, t in enumerate(completacion["actividades"])
            ]
            e["completacion"] = {
                "metodo": "adaptacion_docente_separada_del_original",
                "indicador_procedencia": completacion["indicador_procedencia"],
                "criterios_especificos": completacion["criterios_especificos"],
                "original_intacto": True,
            }
            e["criterios"] = criterios(e["actividades"], reglas)
        d["edicion_docente"] = e
        validar_edicion(e)
    if completadas != 1:
        raise ValueError("Se requiere completar exactamente la fila anclada")
    return salida


def criterios(actividades, reglas):
    salida = []
    for codigo in sorted({t["codigo"] for t in actividades}):
        p = reglas["habilidades"][codigo]
        salida.append(
            {
                "codigo": codigo,
                "tarea_ids": [t["id"] for t in actividades if t["codigo"] == codigo],
                "evidencia_propuesta": p["evidencia"],
                "criterios_observables": p["criterios"],
                "retroalimentacion": p["retroalimentacion"],
                "error_a_indagar": p["error"],
                "apoyo": p["apoyo"],
                "retirada_del_apoyo": p["retirada"],
                "transferencia": p["transferencia"],
                "respuesta_observada": None,
                "logro_observado": None,
            }
        )
    return deepcopy(salida)


def validar_edicion(edicion):
    if "actividades" not in edicion:
        return
    if not all(edicion.get(k) for k in ("indicador", "producto", "explicacion", "actividades", "seguridad")):
        raise ValueError("La edición efectiva requiere propósito evaluable y actividades")
    if any(
        c.get("logro_observado") is not None or c.get("respuesta_observada") is not None for c in edicion["criterios"]
    ):
        raise ValueError("La preparación no contiene respuestas o logros observados")
    if edicion["factibilidad"].get("desempeno_practico_observado") is not None:
        raise ValueError("No se atribuye ejecución práctica observada")
    tareas = {t["id"]: t for t in edicion["actividades"]}
    if len(tareas) != len(edicion["actividades"]) or any(t["fase"] not in FASES for t in tareas.values()):
        raise ValueError("Actividades repetidas o fase desconocida")
    cubiertas = [i for c in edicion["criterios"] for i in c["tarea_ids"]]
    if len(cubiertas) != len(set(cubiertas)) or set(cubiertas) != set(tareas):
        raise ValueError("Los criterios deben cubrir exactamente las actividades efectivas")
    if any(tareas[i]["codigo"] != c["codigo"] for c in edicion["criterios"] for i in c["tarea_ids"]):
        raise ValueError("El criterio y la actividad deben conservar el mismo código")


def corregir_omisiones(registros, cfg, reglas, huella):
    """Correcciones editoriales explícitas de consignas y códigos, sin tocar las celdas originales."""
    if cfg["huella_curriculo"] != huella:
        raise ValueError("Las derivaciones pertenecen a otra captura")
    por_id = {r["id"]: r for r in registros}
    for f in cfg["filas"]:
        e = por_id[f["fila_id"]]["documento"]["edicion_docente"]
        if f.get("reemplazar_todas_actividades"):
            e["actividades"] = []
        if f.get("reemplazar_fases"):
            e["actividades"] = [t for t in e["actividades"] if t["fase"] not in f["reemplazar_fases"]]
        for i, t in enumerate(f["actividades"]):
            e["actividades"].append(
                dict(t, id="DERIVADA:" + sha(serializar([f["fila_id"], i, t])), origen_tarea_id=None)
            )
        if f.get("producto"):
            e["producto"] = f["producto"]
        e["explicacion"] += " " + f.get("explicacion_adicional", "")
        e["seguridad"] += " " + f.get("seguridad_adicional", "")
        e["derivacion_editorial"] = {"motivo": f["motivo"], "original_intacto": True}
        e["criterios"] = criterios(e["actividades"], reglas)
        validar_edicion(e)
    return registros


def escribir_campo(e, ruta, texto):
    leer_ruta(e, ruta)
    partes = ruta.split("/")
    nodo = e
    for parte in partes[:-1]:
        nodo = nodo[int(parte)] if isinstance(nodo, list) else nodo[parte]
    if isinstance(nodo, list):
        nodo[int(partes[-1])] = texto
    else:
        nodo[partes[-1]] = texto


def ajustes_posteriores(registros, revisiones, cfg):
    """Publica correcciones editoriales como pendientes; conserva, sin reutilizar, los votos previos."""
    import re
    from collections import defaultdict
    from decimal import Decimal

    por_id = {r["id"]: r for r in registros}
    grupos = defaultdict(list)
    for c in cfg["cambios"]:
        grupos[c["item_id"]].append(c)
    contextos = []
    for id_, cambios in grupos.items():
        e = por_id[id_]["documento"]["edicion_docente"]
        huella = sha(serializar(e))
        antecedente = deepcopy(revisiones[id_])
        if any(c["edicion_previa_sha256"] != huella for c in cambios):
            raise ValueError("El ajuste editorial no corresponde a la edición realmente revisada")
        for c in cambios:
            anterior = leer_ruta(e, c["ruta"])
            if anterior != c["anterior"]:
                raise ValueError("El campo editorial cambió después de redactar el ajuste")
            if c["tipo"] == "notacion_decimal":
                patron = r"\b\d+,\d+\b"
                esperado = re.sub(patron, lambda m: m[0].replace(",", "."), anterior)
                if c["nuevo"] != esperado:
                    raise ValueError("Un ajuste de notación no puede modificar otros caracteres")
                for m in re.finditer(patron, anterior):
                    if (
                        Decimal(m[0].replace(",", ".")).as_tuple()
                        != Decimal(c["nuevo"][m.start() : m.end()]).as_tuple()
                    ):
                        raise ValueError("El ajuste cambió un valor o su precisión declarada")
            escribir_campo(e, c["ruta"], c["nuevo"])
        validar_edicion(e)
        contexto = {
            "version": cfg["version"],
            "item_id": id_,
            "edicion": deepcopy(e),
            "ajustes": cambios,
            "antecedente_contexto_sha256": antecedente["contexto_sha256"],
        }
        contextos.append(contexto)
        revisiones[id_] = {
            "estado": "revision_automatica_con_pendientes",
            "edicion_sha256": sha(serializar(e)),
            "lote": antecedente["lote"],
            "ronda": None,
            "etapa": "ajuste_editorial_sin_relectura",
            "contexto_sha256": sha(serializar(contexto)),
            "lecturas": [],
            "faltan_roles": list(ROLES),
            "errores_validacion": {},
            "roles_sin_control_superado": [],
            "controles_negativos": {},
            "antecedente_revisado": antecedente,
            "ajustes_editoriales": cambios,
            "limite": "Esta edición contiene ajustes posteriores. Sus cuatro lecturas están pendientes; "
            "los votos de la edición anterior se conservan como antecedente y no la aprueban.",
        }
    return contextos
