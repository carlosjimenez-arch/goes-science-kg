"""LangGraph durable: redacción, cuatro jueces ciegos y una reparación sólo de filas fallidas."""

from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TypedDict

from goes_science_kg.clases.contratos import (
    CRITERIOS,
    MAX_HALLAZGOS_BYTES,
    ROLES,
    BorradorClases,
    LecturaClases,
    esquema_lectura,
    esquema_transporte,
)
from goes_science_kg.clases.preparacion import contexto, validar_importacion
from goes_science_kg.clases.prompts import ESPECIALIDADES, JUEZ, REDACTOR
from goes_science_kg.clases.validacion import (
    certificar_resultado,
    huella_contenido,
    recuperar_validos,
    validar_borrador,
    validar_lectura,
)
from goes_science_kg.motor.contratos import Evidencia, huella

LOGGER = logging.getLogger(__name__)


class EstadoClases(TypedDict, total=False):
    solicitud: dict
    ejecucion_id: str
    huella_entorno: str
    iteracion: int
    pendientes: list[str]
    borrador: dict | None
    a_revisar: list[dict]
    errores_estructura: dict
    error_generacion: str | None
    respuesta_rechazada: str | None
    clases_ciencia: dict
    clases_curriculo: dict
    clases_psicopedagogia: dict
    clases_adversarial: dict
    resultados: dict
    rondas: list[dict]
    resultado: dict
    tipo_ronda: str
    siguiente: str


class MotorClases:
    def __init__(self, proveedor, corpus):
        self.modelo = proveedor
        self.corpus = corpus

    def validar_estado(self, estado):
        p = estado["solicitud"]
        if p["id"] != huella({k: v for k, v in p.items() if k != "id"}):
            raise ValueError("La preparación cambió")
        if p["corpus_sha256"] != self.corpus.huella:
            raise ValueError("Cambió el corpus científico del guion")
        if p.get("borrador_inicial"):
            validar_importacion(p, self.corpus.raiz.parent.parent)
        for e in p["fuentes"]:
            self.corpus.verificar(Evidencia.model_validate(e))
        if estado.get("resultado"):
            certificar_resultado(estado["resultado"], p, {r: self.modelo.nombre_modelo(r) for r in ROLES})

    def redactar(self, estado):
        self.validar_estado(estado)
        p = estado["solicitud"]
        ids = estado.get("pendientes", [f["fila_id"] for f in p["filas"]])
        mensaje = contexto(p, ids=ids)
        if p.get("hallazgos_previos"):
            mensaje["hallazgos_a_corregir"] = p["hallazgos_previos"]
        if estado.get("iteracion", 0):
            mensaje["hallazgos_a_corregir"] = {id_: estado["resultados"][id_]["motivos"] for id_ in ids}
            previo = estado.get("borrador")
            mensaje["borrador_anterior"] = (
                {"guiones": [g for g in previo["guiones"] if g["fila_id"] in ids]}
                if previo
                else estado.get("respuesta_rechazada")
            )
        try:
            if (
                len(json.dumps(mensaje.get("hallazgos_a_corregir", {}), ensure_ascii=False).encode())
                > MAX_HALLAZGOS_BYTES
            ):
                raise ValueError(
                    "Los hallazgos exceden el contexto de reparación; se conservan íntegros sin truncarlos"
                )
            if not estado.get("iteracion") and p.get("borrador_inicial"):
                # Recuperación técnica: sólo cuando ese guion no recibió dictámenes válidos antes.
                if not p.get("antecedente_sin_dictamenes"):
                    raise ValueError("No se importa un borrador sin un antecedente técnico explícito")
                borrador = BorradorClases.model_validate(p["borrador_inicial"])
            else:
                borrador = self.modelo.generar(
                    rol="clases_redactor",
                    sistema=REDACTOR,
                    mensaje=json.dumps(mensaje, ensure_ascii=False, sort_keys=True),
                    esquema=esquema_transporte(BorradorClases),
                )
            errores = validar_borrador(borrador, p, ids_esperados=ids)
            validos = [g.model_dump(mode="json") for g in borrador.guiones if g.fila_id not in errores]
            datos, error, rechazada = borrador.model_dump(mode="json"), None, None
        except Exception as fallo:
            if getattr(fallo, "code", None) in {400, 401, 403, 404}:
                raise  # Fallo de solicitud/configuración: no se gasta una reparación pedagógica.
            detalles = getattr(fallo, "detalles_validacion", ())
            error = type(fallo).__name__ + (": " + "; ".join(detalles[:8]) if detalles else ": " + str(fallo)[:400])
            rechazada = getattr(fallo, "texto_respuesta", None)
            if rechazada and len(rechazada.encode()) > 120000:
                rechazada = None  # La salida íntegra permanece en el ledger; no se inyecta fuera de presupuesto.
            datos, validos, errores = None, [], {id_: [error] for id_ in ids}
            if rechazada:
                try:
                    parcial, errores = recuperar_validos(rechazada, p, ids)
                    if parcial:
                        datos = parcial.model_dump(mode="json")
                        validos = [g.model_dump(mode="json") for g in parcial.guiones if g.fila_id not in errores]
                except (ValueError, TypeError, KeyError):
                    pass  # No se reconstruye ni normaliza una respuesta incompleta o incompatible.
            LOGGER.warning("AMARILLO guiones %s: %s", p["id"][:10], type(fallo).__name__)
        if datos:
            for guion in datos["guiones"]:
                id_ = guion["fila_id"]
                anterior = (estado.get("resultados", {}).get(id_) or {}).get("guion")
                huellas = list(p.get("huellas_vetadas", {}).get(id_, []))
                if anterior:
                    huellas.append(huella_contenido(anterior))
                if huella_contenido(guion) in huellas:
                    errores[id_] = ["La reparación no cambia el contenido vetado; no se repiten votos del mismo guion"]
            validos = [g for g in validos if g["fila_id"] not in errores]
        return {
            "pendientes": ids,
            "iteracion": estado.get("iteracion", 0) + 1,
            "borrador": datos,
            "a_revisar": validos,
            "errores_estructura": errores,
            "error_generacion": error,
            "respuesta_rechazada": rechazada,
            "tipo_ronda": "redaccion",
        }

    def revisar(self, estado, rol, *, recuperacion_tecnica=False):
        guiones = BorradorClases.model_validate({"guiones": estado["a_revisar"]}).guiones
        ids = {g.fila_id for g in guiones}
        mensaje = contexto(estado["solicitud"], ids=ids) | {
            "guiones": estado["a_revisar"],
            "criterios_obligatorios": CRITERIOS[rol],
        }
        try:
            opciones = {"recuperacion_tecnica": True} if recuperacion_tecnica else {}
            lectura = self.modelo.generar(
                rol=rol,
                sistema=JUEZ + "\n" + ESPECIALIDADES[rol],
                mensaje=json.dumps(mensaje, ensure_ascii=False, sort_keys=True),
                esquema=esquema_transporte(esquema_lectura(rol)),
                **opciones,
            )
            lectura = LecturaClases.model_validate(lectura.model_dump(mode="json"))
            validar_lectura(lectura, rol, guiones, estado["solicitud"])
            datos, error = lectura.model_dump(mode="json"), None
        except Exception as fallo:
            if getattr(fallo, "code", None) in {400, 401, 403, 404}:
                raise
            datos, error = None, type(fallo).__name__ + ": " + str(fallo)[:500]
            LOGGER.warning("AMARILLO juez %s: %s", rol, type(fallo).__name__)
        salida = {"rol": rol, "modelo": self.modelo.nombre_modelo(rol), "lectura": datos, "error": error}
        if recuperacion_tecnica:
            salida["recuperacion_tecnica"] = True
        return {rol: salida}

    def recuperar_lectores(self, estado):
        """Una única recuperación de roles sin lectura; conserva el guion y los votos válidos."""
        faltantes = [r for r in ROLES if estado[r]["error"] or not estado[r]["lectura"]]
        if not faltantes or estado["iteracion"] != 1 or estado["errores_estructura"]:
            raise ValueError("La recuperación técnica no tiene un antecedente elegible")
        for rol in set(ROLES) - set(faltantes):
            if any(v != "si" for f in estado[rol]["lectura"]["filas"] for v in f["criterios"].values()):
                raise ValueError("No se usa una recuperación técnica para repetir un veto válido")
        salidas = {"iteracion": 2, "tipo_ronda": "recuperacion_tecnica"}
        with ThreadPoolExecutor(max_workers=len(faltantes)) as pool:
            for salida in pool.map(lambda rol: self.revisar(estado, rol, recuperacion_tecnica=True), faltantes):
                salidas.update(salida)
        return salidas

    def consolidar(self, estado):
        resultados = dict(estado.get("resultados", {}))
        guiones = {g["fila_id"]: g for g in (estado["borrador"] or {}).get("guiones", [])}
        lectores = {r: estado.get(r) for r in ROLES} if estado["a_revisar"] else {}
        for id_ in estado["pendientes"]:
            g = guiones.get(id_)
            motivos = list(estado["errores_estructura"].get(id_, []))
            dictamenes = []
            hay_no = False
            if not motivos and g:
                for rol in ROLES:
                    lector = lectores[rol]
                    lectura = next(
                        (f for f in (lector.get("lectura") or {}).get("filas", []) if f["fila_id"] == id_), None
                    )
                    dictamenes.append(
                        {
                            "rol": rol,
                            "modelo": lector["modelo"],
                            "huella_guion": huella(g),
                            "huella_preparacion": estado["solicitud"]["id"],
                            "lectura": lectura,
                            "error": lector["error"],
                        }
                    )
                    if lectura is None:
                        motivos.append(rol + ": " + (lector["error"] or "Lectura ausente"))
                    elif any(v != "si" for v in lectura["criterios"].values()):
                        motivos.extend(rol + ": " + h for h in lectura["hallazgos"])
                        hay_no = hay_no or "no" in lectura["criterios"].values()
            estado_fila = (
                "respaldado_automaticamente"
                if not motivos and len(dictamenes) == 4
                else ("no_respaldado" if hay_no else "abstencion")
            )
            resultados[id_] = {
                "fila_id": id_,
                "estado": estado_fila,
                "guion": g,
                "dictamenes": dictamenes,
                "motivos": motivos,
                "ronda_seleccionada": estado["iteracion"],
            }
        ronda = {
            "numero": estado["iteracion"],
            "filas": estado["pendientes"],
            "borrador": estado["borrador"],
            "lectores": lectores,
            "error_generacion": estado["error_generacion"],
            "errores_estructura": estado["errores_estructura"],
            "respuesta_rechazada": estado["respuesta_rechazada"],
            "tipo": estado.get("tipo_ronda", "redaccion"),
        }
        pendientes = [id_ for id_, r in resultados.items() if r["estado"] != "respaldado_automaticamente"]
        siguiente = "cerrar"
        if pendientes and estado["iteracion"] < 2:
            recuperable = (
                bool(estado["a_revisar"])
                and not estado["errores_estructura"]
                and any(lector["error"] or not lector["lectura"] for lector in lectores.values())
                and all(
                    all(v == "si" for f in lector["lectura"]["filas"] for v in f["criterios"].values())
                    for lector in lectores.values()
                    if not lector["error"] and lector["lectura"]
                )
            )
            siguiente = "recuperar_lectores" if recuperable else "redactar"
        LOGGER.info(
            "%s guiones %s: %s/%s respaldados; ronda %s",
            "VERDE" if not pendientes else "AMARILLO",
            estado["solicitud"]["id"][:10],
            len(resultados) - len(pendientes),
            len(resultados),
            estado["iteracion"],
        )
        return {
            "resultados": resultados,
            "pendientes": pendientes,
            "rondas": [*estado.get("rondas", []), ronda],
            "siguiente": siguiente,
        }

    def cerrar(self, estado):
        return {
            "resultado": {
                "version": "resultado-clases-1",
                "preparacion_id": estado["solicitud"]["id"],
                "snapshot_id": estado["solicitud"]["snapshot_id"],
                "ejecucion_id": estado["ejecucion_id"],
                "huella_entorno": estado["huella_entorno"],
                "estado": "respaldado_automaticamente" if not estado["pendientes"] else "parcial",
                "filas": estado["resultados"],
                "rondas": estado["rondas"],
            }
        }

    def compilar(self, *, checkpointer=None):
        from langgraph.graph import END, START, StateGraph

        grafo = StateGraph(EstadoClases)
        grafo.add_node("redactar", self.redactar)
        grafo.add_node("consolidar", self.consolidar)
        grafo.add_node("cerrar", self.cerrar)
        grafo.add_node("recuperar_lectores", self.recuperar_lectores)
        grafo.add_edge("recuperar_lectores", "consolidar")
        for rol in ROLES:
            grafo.add_node("juez_" + rol, lambda e, r=rol: self.revisar(e, r))
        grafo.add_edge(START, "redactar")
        grafo.add_conditional_edges(
            "redactar", lambda e: ["juez_" + r for r in ROLES] if e["a_revisar"] else ["consolidar"]
        )
        grafo.add_edge(["juez_" + r for r in ROLES], "consolidar")
        grafo.add_conditional_edges("consolidar", lambda e: e["siguiente"])
        grafo.add_edge("cerrar", END)
        return grafo.compile(checkpointer=checkpointer)
