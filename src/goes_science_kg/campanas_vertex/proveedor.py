"""Enforce separately authorized, bounded authoring calls with exact provenance and finish metadata."""

from __future__ import annotations

import json
import time
from functools import cached_property
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel

from goes_science_kg.campanas_vertex.contratos import (
    ESQUEMAS,
    PERFIL_LISTA,
    canonico,
    contrato_autor_api,
    equivalencia_raw_normalizado,
    esquema_transporte,
    perfil_transporte_plan,
    plazas_disponibles,
    sha256,
)
from goes_science_kg.campanas_vertex.presupuesto import PresupuestoCampana
from goes_science_kg.campanas_vertex.validacion import validar_contenido, validar_contexto

TARIFAS = {"gemini-4-argon": (4, 20), "gemini-3.8-flash": (1.5, 7.5)}
LIMITES = {
    "entrada_inicial_bytes": 128000,
    "entrada_correccion_bytes": 308000,
    "salida_bytes": 120000,
    "max_salida_tokens": 65536,
    "plazas_por_componente": 2,
}


class SalidaNoUtilizable(ValueError):
    """Preserve a received but unusable response without silently repairing its content."""

    def __init__(self, motivo: str, texto: str):
        super().__init__(motivo)
        self.texto_respuesta = texto
        self.sha256 = sha256(texto.encode())


def huella_codigo() -> dict[str, str]:
    """Pin the new execution and validation modules without rewriting historical protocols."""
    raiz = Path(__file__).parent
    nombres = (
        "__init__.py",
        "__main__.py",
        "contratos.py",
        "presupuesto.py",
        "proveedor.py",
        "validacion.py",
        "continuidad.py",
    )
    dependencias = (
        "aprendizaje/cierre_recorridos.py",
        "clases/contratos.py",
        "clases/complementaria.py",
        "clases/validacion.py",
        "clases/presupuesto.py",
        "motor/registro.py",
        "motor/contratos.py",
        "config.py",
    )
    return (
        {nombre: sha256((raiz / nombre).read_bytes()) for nombre in nombres}
        | {"../" + nombre: sha256((raiz.parent / nombre).read_bytes()) for nombre in dependencias}
        | {
            "uv.lock": sha256((raiz.parents[2] / "uv.lock").read_bytes()),
        }
    )


def _componente(plan: dict, identificador: str) -> dict:
    componentes = plan.get("componentes", [])
    ids = [c["id"] for c in componentes]
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("El plan requiere componentes únicos y no vacíos")
    encontrados = [c for c in componentes if c["id"] == identificador]
    if len(encontrados) != 1 or encontrados[0]["tipo"] not in ESQUEMAS:
        raise ValueError("El componente no pertenece al plan y contrato autorizables")
    return encontrados[0]


def preparar_solicitud(plan: dict, componente_id: str, *, contexto: dict, sistema: str, correccion=None) -> dict:
    """Validate pinned inputs and measure the SDK-converted payload without creating a client."""
    from google.genai import models, types

    componente = _componente(plan, componente_id)
    tipo = componente["tipo"]
    if plan.get("codigo_sha256") != huella_codigo():
        raise ValueError("El código o las dependencias no conservan la huella del plan")
    if plan.get("limites") != LIMITES:
        raise ValueError("El plan debe fijar los límites del protocolo nuevo exactamente")
    if sha256(canonico(contexto)) != componente["contexto_sha256"]:
        raise ValueError("El contexto no conserva el SHA del plan")
    validar_contexto(tipo, contexto)
    if sha256(sistema.encode()) != plan["prompts_sha256"][tipo]:
        raise ValueError("El prompt no conserva el SHA del plan")
    esquema = ESQUEMAS[tipo]
    perfil = perfil_transporte_plan(plan, tipo)
    contrato_api = contrato_autor_api(tipo, perfil)
    transporte = esquema_transporte(contrato_api)
    esquema_sha = sha256(canonico(transporte.model_json_schema()))
    if esquema_sha != plan["esquemas_sha256"][tipo]:
        raise ValueError("El esquema no conserva el SHA del plan")
    negocio_sha = sha256(canonico(esquema.model_json_schema()))
    negocio_fijado = plan.get("esquemas_negocio_sha256", {}).get(tipo)
    if negocio_fijado != negocio_sha and (
        negocio_fijado is not None or perfil == PERFIL_LISTA or "perfiles_transporte" in plan
    ):
        raise ValueError("El contrato de negocio no conserva el SHA del plan")
    modelo = plan["modelos"].get(tipo, plan["modelos"].get("redactor"))
    if modelo not in TARIFAS:
        raise ValueError("El modelo no tiene una tarifa conservadora fijada en este protocolo")
    mensaje = canonico({"componente_id": componente_id, "contexto": contexto, "correccion": correccion}).decode()
    configuracion = types.GenerateContentConfig(
        system_instruction=sistema,
        response_mime_type="application/json",
        response_schema=transporte,
        max_output_tokens=LIMITES["max_salida_tokens"],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        thinking_config=types.ThinkingConfig(thinking_level="MEDIUM"),
    )
    parametros = types._GenerateContentParameters(model=modelo, contents=mensaje, config=configuracion)
    # This is the installed SDK's pure local conversion, including expanded schema and text wrappers.
    convertido = models._GenerateContentParameters_to_vertex(SimpleNamespace(vertexai=True), parametros)

    def serializar_sdk(valor):
        if isinstance(valor, BaseModel):
            return valor.model_dump(mode="json", by_alias=True, exclude_none=True)
        raise TypeError(f"Valor SDK no serializable: {type(valor).__name__}")

    entrada_bytes = len(
        json.dumps(convertido, ensure_ascii=True, sort_keys=True, default=serializar_sdk, allow_nan=False).encode()
    )
    limite = LIMITES["entrada_correccion_bytes" if correccion is not None else "entrada_inicial_bytes"]
    if entrada_bytes > limite:
        raise ValueError(f"Solicitud de {entrada_bytes} bytes excede {limite}; no se recorta ni invoca")
    entrada, salida = TARIFAS[modelo]
    reserva = (entrada_bytes * entrada + LIMITES["max_salida_tokens"] * salida) / 1_000_000
    identidad = {
        "plan_sha256": sha256(canonico(plan)),
        "componente_id": componente_id,
        "contexto_sha256": componente["contexto_sha256"],
        "modelo": modelo,
        "prompt_sha256": plan["prompts_sha256"][tipo],
        "esquema_sha256": esquema_sha,
        "esquema_negocio_sha256": negocio_sha,
        "perfil_transporte": perfil,
        "mensaje_sha256": sha256(mensaje.encode()),
        "max_salida_tokens": LIMITES["max_salida_tokens"],
        "razonamiento": "MEDIUM",
        "proyecto": "g-edu-lxp-xai-dev-prj-976d",
        "region": "global",
    }
    return {
        "identidad": identidad,
        "clave": sha256(canonico(identidad)),
        "modelo": modelo,
        "mensaje": mensaje,
        "configuracion": configuracion,
        "esquema": esquema,
        "esquema_api": contrato_api,
        "perfil_transporte": perfil,
        "entrada_bytes": entrada_bytes,
        "reserva_usd": reserva,
    }


def preflight(plan: dict, solicitudes: dict[str, dict], sistemas: dict[str, str]) -> dict:
    """Check all planned initial calls and reserve the finite correction bound without inference."""
    ids = [c["id"] for c in plan.get("componentes", [])]
    if not ids or len(ids) != len(set(ids)) or set(ids) != set(solicitudes):
        raise ValueError("Las solicitudes deben cubrir exactamente los componentes del plan")
    max_llamadas = sum(plazas_disponibles(c) for c in plan["componentes"])
    reserva = 0.0
    detalle = []
    for componente in plan["componentes"]:
        solicitud = preparar_solicitud(
            plan, componente["id"], contexto=solicitudes[componente["id"]], sistema=sistemas[componente["tipo"]]
        )
        entrada, salida = TARIFAS[solicitud["modelo"]]
        plazas = plazas_disponibles(componente)
        segunda = (LIMITES["entrada_correccion_bytes"] * entrada + 65536 * salida) / 1_000_000 if plazas == 2 else 0.0
        reserva += solicitud["reserva_usd"] + segunda
        detalle.append(
            {
                "id": componente["id"],
                "entrada_bytes": solicitud["entrada_bytes"],
                "plazas_disponibles": plazas,
                "reserva_inicial_usd": solicitud["reserva_usd"],
                "reserva_segunda_plaza_usd": segunda,
                "reserva_maxima_usd": solicitud["reserva_usd"] + segunda,
            }
        )
    if plan["max_llamadas"] != max_llamadas or reserva > plan["max_reserva_usd"]:
        raise ValueError("Los topes propuestos no cubren las plazas disponibles del preflight completo")
    return {
        "estado": "preparado_sin_autorizacion_de_gasto",
        "plan_sha256": sha256(canonico(plan)),
        "componentes": len(ids),
        "llamadas_maximas": max_llamadas,
        "reserva_maxima_usd": reserva,
        "detalle": detalle,
        "llamadas_efectuadas": 0,
        "limite": "Completitud técnica; faltan autorización explícita y dictámenes del contenido generado.",
    }


class ProveedorCampana:
    """Authorize before client creation and allow one paid attempt per component and round."""

    def __init__(self, plan: dict, autorizacion, archivo, *, cliente=None):
        self.presupuesto = PresupuestoCampana(plan, autorizacion, archivo)
        self.plan = self.presupuesto.plan
        self._cliente = cliente
        with self.presupuesto.registro.conexion() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS campanas_vertex_respuestas ("
                "llamada TEXT PRIMARY KEY, ejecucion TEXT NOT NULL, clave TEXT NOT NULL, "
                "respuesta_sha256 TEXT NOT NULL, finish_reason TEXT, metadata TEXT NOT NULL)"
            )

    @cached_property
    def cliente(self):
        """Open ADC lazily after a matching explicit authorization and durable ledger check."""
        if self._cliente is not None:
            return self._cliente
        from google import genai
        from google.genai import types

        return genai.Client(
            vertexai=True,
            project="g-edu-lxp-xai-dev-prj-976d",
            location="global",
            http_options=types.HttpOptions(timeout=600000, retry_options=types.HttpRetryOptions(attempts=1)),
        )

    def _anterior(self, componente_id: str, anterior: bytes | None, hallazgos: list[str] | None) -> dict:
        if not hallazgos or len(canonico(hallazgos)) > 48000 or any(not x.strip() for x in hallazgos):
            raise ValueError("La segunda plaza requiere hallazgos explícitos de hasta 48.000 bytes")
        with self.presupuesto.registro.conexion() as db:
            fila = db.execute(
                "SELECT l.id,l.estado,s.texto,s.sha256 FROM llamadas l LEFT JOIN salidas_llm s ON s.llamada=l.id "
                "WHERE l.ejecucion=? AND l.rol=?",
                (self.plan["campana_id"], componente_id + ":ronda0"),
            ).fetchone()
        if fila is None or fila["estado"] == "reservada":
            raise ValueError("No hay una primera plaza terminada; no se duplica una llamada ambigua")
        texto = anterior.decode() if anterior is not None else None
        if fila["texto"] != texto or (texto is not None and sha256(anterior) != fila["sha256"]):
            raise ValueError("La corrección no conserva exactamente la respuesta recibida")
        if anterior is not None and len(anterior) > LIMITES["salida_bytes"]:
            raise ValueError("La respuesta anterior excede la cota de corrección; requiere un plan nuevo")
        return {
            "llamada_anterior": fila["id"],
            "anterior_sha256": fila["sha256"],
            "texto": texto,
            "hallazgos": hallazgos,
        }

    def _recuperar(self, solicitud: dict) -> BaseModel | None:
        clave = solicitud["clave"]
        texto = self.presupuesto.salida(clave)
        if cache := self.presupuesto.cache(clave):
            if cache.get("identidad") != solicitud["identidad"] or cache.get("finish_reason") != "STOP":
                raise ValueError("La caché no acredita esta campaña, solicitud y terminación")
            if texto != cache["texto"] or texto is None or sha256(texto.encode()) != cache["respuesta_sha256"]:
                raise ValueError("El SHA de la caché no coincide")
            traza = ("normalizado_sha256", "perfil_transporte", "adapter_version", "adapter_codigo_sha256")
            if solicitud["perfil_transporte"] == PERFIL_LISTA or any(campo in cache for campo in traza):
                tipo = _componente(self.plan, solicitud["identidad"]["componente_id"])["tipo"]
                conversion = equivalencia_raw_normalizado(texto, tipo, perfil=solicitud["perfil_transporte"])
                if any(cache.get(campo) != conversion[campo] for campo in traza):
                    raise ValueError("La traza de normalización de la caché no coincide; no se repara ni adopta")
        if texto is None:
            return None
        with self.presupuesto.registro.conexion() as db:
            fila = db.execute(
                "SELECT r.*,l.estado FROM campanas_vertex_respuestas r JOIN llamadas l ON l.id=r.llamada "
                "WHERE r.ejecucion=? AND r.clave=?",
                (self.plan["campana_id"], clave),
            ).fetchone()
        if fila is None or fila["respuesta_sha256"] != sha256(texto.encode()):
            raise SalidaNoUtilizable(
                "La respuesta recibida no tiene terminación verificable; no se vuelve a pagar", texto
            )
        if fila["finish_reason"] != "STOP":
            if fila["estado"] == "reservada":
                self._cerrar_recuperada(fila, "fallida")
            raise SalidaNoUtilizable("La respuesta recibida no terminó en STOP; no se vuelve a pagar", texto)
        try:
            resultado = self._validar(solicitud, texto, fila["finish_reason"])
        except SalidaNoUtilizable:
            if fila["estado"] == "reservada":
                self._cerrar_recuperada(fila, "fallida")
            raise
        if fila["estado"] == "reservada":
            self._cerrar_recuperada(fila, "completada")
        return resultado

    def _cerrar_recuperada(self, fila, estado: str):
        uso = json.loads(fila["metadata"])
        self.presupuesto.terminar(
            fila["llamada"],
            estado=estado,
            latencia_ms=None,
            entrada_tokens=uso["entrada_tokens"],
            salida_tokens=uso["salida_tokens"],
        )

    def _validar(self, solicitud: dict, texto: str, finish_reason: str | None) -> BaseModel:
        if finish_reason != "STOP" or not texto.strip() or len(texto.encode()) > LIMITES["salida_bytes"]:
            raise SalidaNoUtilizable("Salida vacía, excesiva o sin terminación STOP; queda retenida", texto)
        try:
            contexto = json.loads(solicitud["mensaje"])["contexto"]
            tipo = _componente(self.plan, solicitud["identidad"]["componente_id"])["tipo"]
            conversion = equivalencia_raw_normalizado(texto, tipo, perfil=solicitud["perfil_transporte"])
            resultado = solicitud["esquema"].model_validate(conversion["autor_normalizado"])
            validar_contenido(tipo, resultado, contexto)
        except (ValueError, KeyError) as error:
            raise SalidaNoUtilizable("La respuesta incumple el contrato local y se conserva íntegra", texto) from error
        self.presupuesto.guardar_cache(
            solicitud["clave"],
            {
                "identidad": solicitud["identidad"],
                "texto": texto,
                "respuesta_sha256": sha256(texto.encode()),
                "finish_reason": finish_reason,
                "normalizado_sha256": conversion["normalizado_sha256"],
                "perfil_transporte": conversion["perfil_transporte"],
                "adapter_version": conversion["adapter_version"],
                "adapter_codigo_sha256": conversion["adapter_codigo_sha256"],
            },
        )
        return resultado

    def generar(
        self, componente_id: str, *, contexto: dict, sistema: str, ronda: int = 0, anterior=None, hallazgos=None
    ) -> BaseModel:
        """Generate one pinned component, preserving raw output and reserving every paid attempt first."""
        if sha256(canonico(self.plan)) != self.presupuesto.autorizacion["plan_sha256"]:
            raise ValueError("El plan autorizado cambió en memoria; no se invoca ni se adopta su caché")
        if type(ronda) is not int or ronda not in (0, 1):
            raise ValueError("Sólo se admiten las plazas 0 y 1")
        if ronda >= plazas_disponibles(_componente(self.plan, componente_id)):
            raise ValueError("El componente no dispone de otra plaza autorizada")
        if ronda == 0 and (anterior is not None or hallazgos is not None):
            raise ValueError("La primera plaza no admite una corrección")
        correccion = self._anterior(componente_id, anterior, hallazgos) if ronda else None
        solicitud = preparar_solicitud(
            self.plan, componente_id, contexto=contexto, sistema=sistema, correccion=correccion
        )
        if recuperada := self._recuperar(solicitud):
            return recuperada
        if sha256(canonico(self.plan)) != self.presupuesto.autorizacion["plan_sha256"]:
            raise ValueError("El plan autorizado cambió antes de reservar")
        llamada = self.presupuesto.autorizar_reserva(
            clave=solicitud["clave"],
            modelo=solicitud["modelo"],
            rol=f"{componente_id}:ronda{ronda}",
            reserva_usd=solicitud["reserva_usd"],
        )
        inicio = time.perf_counter()
        entrada_tokens, salida_tokens = None, None
        try:
            respuesta = self.cliente.models.generate_content(
                model=solicitud["modelo"], contents=solicitud["mensaje"], config=solicitud["configuracion"]
            )
            texto = respuesta.text or ""
            uso = getattr(respuesta, "usage_metadata", None)
            entrada_tokens = getattr(uso, "prompt_token_count", None)
            candidatos = getattr(uso, "candidates_token_count", None)
            salida_tokens = (
                None if candidatos is None else candidatos + (getattr(uso, "thoughts_token_count", None) or 0)
            )
            candidato = (getattr(respuesta, "candidates", None) or [None])[0]
            motivo = getattr(candidato, "finish_reason", None)
            motivo = getattr(motivo, "value", motivo)
            self.presupuesto.guardar_salida(llamada, texto)
            metadata = {"entrada_tokens": entrada_tokens, "salida_tokens": salida_tokens}
            with self.presupuesto.registro.conexion() as db:
                db.execute(
                    "INSERT INTO campanas_vertex_respuestas VALUES(?,?,?,?,?,?)",
                    (
                        llamada,
                        self.plan["campana_id"],
                        solicitud["clave"],
                        sha256(texto.encode()),
                        motivo,
                        json.dumps(metadata),
                    ),
                )
            resultado = self._validar(solicitud, texto, motivo)
        except Exception:
            self.presupuesto.terminar(
                llamada,
                estado="fallida",
                latencia_ms=(time.perf_counter() - inicio) * 1000,
                entrada_tokens=entrada_tokens,
                salida_tokens=salida_tokens,
            )
            raise
        self.presupuesto.terminar(
            llamada,
            estado="completada",
            latencia_ms=(time.perf_counter() - inicio) * 1000,
            entrada_tokens=entrada_tokens,
            salida_tokens=salida_tokens,
        )
        return resultado
