"""Require exact user authorization and isolate new reservations in the historical ledger."""

from __future__ import annotations

import hashlib
import json
import math
import re
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import uuid4

from goes_science_kg.campanas_vertex.continuidad import ContinuidadCampana
from goes_science_kg.campanas_vertex.contratos import plazas_disponibles
from goes_science_kg.clases.presupuesto import comprobar_continuidad, configuracion
from goes_science_kg.config import ruta
from goes_science_kg.motor.registro import PresupuestoAgotado, Registro

VERSION_AUTORIZACION = "autorizacion-campana-vertex-1"


def _canonico(valor: Any) -> bytes:
    return (
        json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _sha(valor: bytes) -> str:
    return hashlib.sha256(valor).hexdigest()


def _ruta_interna(archivo: Path) -> Path:
    base = ruta(".").resolve()
    candidato = archivo if archivo.is_absolute() else base / archivo
    if any(p.is_symlink() for p in (candidato, *candidato.parents)):
        raise ValueError("El recibo y el ledger no pueden usar enlaces simbólicos")
    if not candidato.resolve().is_relative_to(base):
        raise ValueError("El recibo y el ledger deben permanecer dentro del repositorio")
    return candidato.resolve()


def _positivo(valor: Any) -> bool:
    return (type(valor) is int and valor > 0) or (type(valor) is float and math.isfinite(valor) and valor > 0)


def verificar_autorizacion(plan: dict, autorizacion: Path | None) -> dict:
    """Reject missing, unrelated, malformed, or insufficient explicit user receipts."""
    if autorizacion is None:
        raise ValueError("Falta un recibo literal de autorización presupuestaria explícita del usuario")
    if (
        not isinstance(plan, dict)
        or not isinstance(plan.get("campana_id"), str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{4,199}", plan["campana_id"])
        or type(plan.get("max_llamadas")) is not int
        or plan["max_llamadas"] <= 0
        or not _positivo(plan.get("max_reserva_usd"))
    ):
        raise ValueError("El plan requiere campaña nueva y máximos positivos de llamadas y reserva")
    for campo in ("modelos", "prompts_sha256", "esquemas_sha256"):
        contenido = plan.get(campo)
        if not isinstance(contenido, dict) or not contenido:
            raise ValueError(f"El plan debe fijar {campo}")
        if any(not isinstance(v, str) or not v.strip() for v in contenido.values()):
            raise ValueError(f"El plan contiene {campo} inválidos")
        if campo != "modelos" and any(not re.fullmatch(r"[a-f0-9]{64}", v) for v in contenido.values()):
            raise ValueError(f"El plan requiere SHA-256 completos en {campo}")
    componentes = plan.get("componentes")
    limites = plan.get("limites")
    if (
        not isinstance(componentes, list)
        or not componentes
        or any(not isinstance(c, dict) or not isinstance(c.get("id"), str) or not c["id"] for c in componentes)
        or len({c["id"] for c in componentes}) != len(componentes)
        or not isinstance(limites, dict)
        or type(limites.get("plazas_por_componente")) is not int
        or limites["plazas_por_componente"] != 2
    ):
        raise ValueError("El plan requiere componentes únicos y hasta dos plazas por componente")
    if plan["max_llamadas"] > sum(plazas_disponibles(c) for c in componentes):
        raise ValueError("El máximo de llamadas excede las plazas disponibles de los componentes")
    archivo = _ruta_interna(Path(autorizacion))
    if not archivo.is_file() or archivo.stat().st_size > 256_000:
        raise ValueError("El recibo de autorización falta o excede el tamaño permitido")
    raw = archivo.read_bytes()
    try:
        recibo = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise ValueError("El recibo de autorización no es JSON UTF-8 válido") from error
    if not isinstance(recibo, dict) or recibo.get("version") != VERSION_AUTORIZACION:
        raise ValueError("Versión de recibo de autorización no reconocida")
    if recibo.get("campana_id") != plan["campana_id"] or recibo.get("plan_sha256") != _sha(_canonico(plan)):
        raise ValueError("El recibo de autorización corresponde a otra campaña o versión exacta del plan")
    if recibo.get("autorizacion_usuario_explicita") is not True:
        raise ValueError("El recibo no registra una autorización explícita del usuario")
    if not isinstance(recibo.get("texto_usuario"), str) or not recibo["texto_usuario"].strip():
        raise ValueError("El recibo necesita el texto literal del usuario; no se puede inferir ni fabricar")
    try:
        date.fromisoformat(recibo.get("fecha", ""))
    except (TypeError, ValueError) as error:
        raise ValueError("El recibo necesita una fecha ISO explícita") from error
    if (
        type(recibo.get("max_llamadas")) is not int
        or recibo["max_llamadas"] != plan["max_llamadas"]
        or not _positivo(recibo.get("max_reserva_usd"))
        or Decimal(str(recibo["max_reserva_usd"])) != Decimal(str(plan["max_reserva_usd"]))
    ):
        raise ValueError("Los topes autorizados deben coincidir con el plan exacto")
    return {**recibo, "autorizacion_sha256": _sha(raw), "plan_sha256": _sha(_canonico(plan))}


class PresupuestoCampana:
    """Continue a newly authorized campaign without replacing historical consumption or caches."""

    def __init__(self, plan: dict, autorizacion: Path | None, archivo: Path):
        self.autorizacion = verificar_autorizacion(plan, autorizacion)
        self.plan = json.loads(_canonico(plan))
        self.ejecucion_id = self.plan["campana_id"]
        self._plan_sha256 = self.autorizacion["plan_sha256"]
        self._autorizacion_sha256 = _sha(_canonico(self.autorizacion))
        self._ejecucion_fijada = self.ejecucion_id
        if self.ejecucion_id == configuracion()["ejecucion"]:
            raise ValueError("La campaña nueva no puede reutilizar la ejecución histórica")
        destino = _ruta_interna(Path(archivo))
        if destino != ruta("data/operaciones/registro.sqlite").resolve():
            raise ValueError("La campaña debe continuar en el mismo ledger data/operaciones/registro.sqlite")
        continuidad = comprobar_continuidad(destino)
        if continuidad.get("baseline_verificado") is not True:
            raise ValueError("No se verificó la continuidad del consumo histórico")
        self.registro = Registro(destino)
        self.componentes = frozenset(c["id"] for c in self.plan["componentes"])
        self._componentes_fijados = self.componentes
        self.continuidad = ContinuidadCampana(
            self.ejecucion_id, self._plan_sha256, self.autorizacion["autorizacion_sha256"]
        )
        with self.continuidad.bloqueo():
            with self.registro.conexion() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "CREATE TABLE IF NOT EXISTS campanas_vertex_autorizaciones ("
                    "campana_id TEXT PRIMARY KEY,plan_sha256 TEXT NOT NULL,autorizacion_sha256 TEXT NOT NULL)"
                )
                anterior = db.execute(
                    "SELECT plan_sha256,autorizacion_sha256 FROM campanas_vertex_autorizaciones WHERE campana_id=?",
                    (self.ejecucion_id,),
                ).fetchone()
                esperado = (self.autorizacion["plan_sha256"], self.autorizacion["autorizacion_sha256"])
                if anterior is not None and tuple(anterior) != esperado:
                    raise ValueError("La campaña existente está fijada a otro plan o recibo; no se reinicia")
                if anterior is None:
                    anteriores = db.execute(
                        "SELECT COUNT(*) FROM llamadas WHERE ejecucion=?", (self.ejecucion_id,)
                    ).fetchone()[0]
                    if anteriores:
                        raise ValueError("Hay consumo de la campaña sin su recibo anclado; no se adopta")
                    db.execute(
                        "INSERT INTO campanas_vertex_autorizaciones VALUES(?,?,?)", (self.ejecucion_id, *esperado)
                    )
            self.continuidad.inicializar(self.registro, nueva=anterior is None)

    @contextmanager
    def _control(self):
        self._verificar_plan()
        with self.continuidad.bloqueo():
            self.continuidad.verificar(self.registro)
            self._verificar_plan()
            yield

    def _verificar_plan(self) -> None:
        try:
            intacto = (
                _sha(_canonico(self.plan)) == self._plan_sha256
                and _sha(_canonico(self.autorizacion)) == self._autorizacion_sha256
                and self.ejecucion_id == self._ejecucion_fijada
                and self.componentes == self._componentes_fijados
            )
        except (TypeError, ValueError) as error:
            raise ValueError("El plan o la autorización cambiaron después de su validación") from error
        if not intacto:
            raise ValueError("El plan o la autorización cambiaron después de su validación")

    def _clave(self, clave: str) -> str:
        self._verificar_plan()
        return _sha(_canonico([self._ejecucion_fijada, self._plan_sha256, clave]))

    def _llamada_propia(self, id_llamada: str) -> None:
        self._verificar_plan()
        with self.registro.conexion() as db:
            propia = db.execute(
                "SELECT 1 FROM llamadas WHERE id=? AND ejecucion=?", (id_llamada, self.ejecucion_id)
            ).fetchone()
        if propia is None:
            raise ValueError("La llamada no pertenece a esta campaña")

    def autorizar_reserva(self, *, clave: str, modelo: str, rol: str, reserva_usd: float) -> str:
        """Reserve a unique component-round atomically while preserving both cumulative caps."""
        self._verificar_plan()
        if modelo not in self.plan["modelos"].values() or not _positivo(reserva_usd):
            raise ValueError("Modelo o reserva no autorizados por el plan")
        componente, separador, ronda = rol.rpartition(":ronda")
        if not separador or componente not in self.componentes or ronda not in {"0", "1"}:
            raise ValueError("El rol debe identificar un componente del plan y su ronda 0 o 1")
        ficha = next(c for c in self.plan["componentes"] if c["id"] == componente)
        if int(ronda) >= plazas_disponibles(ficha):
            raise ValueError("El componente no dispone de otra plaza autorizada")
        with self._control():
            with self.registro.conexion() as db:
                db.execute("BEGIN IMMEDIATE")
                self._verificar_plan()
                if db.execute(
                    "SELECT 1 FROM llamadas WHERE ejecucion=? AND rol=?", (self.ejecucion_id, rol)
                ).fetchone():
                    raise PresupuestoAgotado(
                        "La plaza del componente ya tiene una reserva; no se repite una llamada ambigua"
                    )
                if (
                    ronda == "1"
                    and not db.execute(
                        "SELECT 1 FROM llamadas WHERE ejecucion=? AND rol=?",
                        (self.ejecucion_id, componente + ":ronda0"),
                    ).fetchone()
                ):
                    raise ValueError("No se puede reservar una corrección sin la primera plaza del componente")
                total, reservado = db.execute(
                    "SELECT COUNT(*),COALESCE(SUM(reserva_usd),0) FROM llamadas WHERE ejecucion=?",
                    (self.ejecucion_id,),
                ).fetchone()
                if total >= self.plan["max_llamadas"] or reservado + reserva_usd > self.plan["max_reserva_usd"]:
                    raise PresupuestoAgotado("La reserva excede el máximo de llamadas o USD de la campaña nueva")
                id_llamada = uuid4().hex
                db.execute(
                    "INSERT INTO llamadas(id,ejecucion,clave,modelo,rol,reserva_usd,estado) VALUES(?,?,?,?,?,?,?)",
                    (id_llamada, self.ejecucion_id, self._clave(clave), modelo, rol, reserva_usd, "reservada"),
                )
                reserva = dict(
                    db.execute(
                        "SELECT id,ejecucion,clave,modelo,rol,reserva_usd,creada FROM llamadas WHERE id=?",
                        (id_llamada,),
                    ).fetchone()
                )
            self.continuidad.registrar(self.registro, reserva)
            return id_llamada

    def terminar(self, id_llamada: str, **kwargs: Any) -> None:
        """Finalize only a reservation belonging to this campaign."""
        with self._control():
            self._llamada_propia(id_llamada)
            self.registro.terminar(id_llamada, **kwargs)

    def cache(self, clave: str) -> dict | None:
        """Read only exact responses from this campaign and plan namespace."""
        with self._control():
            return self.registro.cache(self._clave(clave))

    def guardar_cache(self, clave: str, respuesta: dict) -> None:
        """Store a validated response in this campaign's namespace."""
        with self._control():
            self.registro.guardar_cache(self._clave(clave), respuesta)

    def salida(self, clave: str) -> str | None:
        """Recover a received response without adopting another campaign's output."""
        with self._control():
            return self.registro.salida(self._clave(clave))

    def guardar_salida(self, id_llamada: str, texto: str) -> None:
        """Preserve the exact provider response for a reservation owned by this campaign."""
        with self._control():
            self._llamada_propia(id_llamada)
            self.registro.guardar_salida(id_llamada, texto)
