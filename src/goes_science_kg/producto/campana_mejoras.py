"""Run finite campaigns with cumulative budgets and durable unit preparation."""

from __future__ import annotations

import hashlib
import json
import logging
from pathlib import Path

from goes_science_kg.archivos import destino_generado
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import _bloqueo, ejecutar_durable
from goes_science_kg.motor.esquemas import contrato_transporte
from goes_science_kg.motor.mejoras import REDACTOR, MotorMejoras, prompt_revision
from goes_science_kg.motor.prompts import serializar
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.seleccion import esquema_por_grupos
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.operacion.fondos import FondosCampana
from goes_science_kg.producto.mejoras_contratos import (
    MAX_BYTES_BORRADOR,
    ROLES_MEJORA,
    BorradorMejora,
    PreparacionMejora,
    esquema_revision,
)
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras, datos_mejora

LOGGER = logging.getLogger(__name__)


def escribir_nuevo_o_igual(path: Path, datos: dict) -> None:
    """Write an artifact only when absent or byte-identical to the existing file."""

    path = destino_generado(path)
    texto = json.dumps(datos, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text() != texto:
            raise ValueError(f"No se sobrescribe un archivo curricular distinto: {path.name}")
        return
    with path.open("x", encoding="utf-8") as archivo:
        archivo.write(texto)


def reserva_unidad(p: PreparacionMejora, cfg: ConfiguracionVertex) -> dict:
    """Bound complete unit context and contract-limited output in UTF-8 bytes."""

    # Implementation notes:
    # La reparación incluye el borrador previo y hasta 12 hallazgos por juez, acotados adicionalmente
    # por el controlador a 16 KiB. No son tokens facturados; las reservas del adaptador son acumulativas.
    contexto = serializar(datos_mejora(p))
    bytes_contexto = len(contexto.encode())
    coste = 0.0
    for rol in ("redactor_curricular", *ROLES_MEJORA):
        sistema = REDACTOR if rol == "redactor_curricular" else prompt_revision(rol)
        esquema = (
            BorradorMejora
            if rol == "redactor_curricular"
            else esquema_por_grupos(esquema_revision(rol), p.fragmentos, p.grupos)
        )
        entrada = bytes_contexto + len(
            (sistema + json.dumps(contrato_transporte(esquema).model_json_schema())).encode()
        )
        # JSON serializar agrega espacios al volcar el borrador; <= 4 KiB adicionales por fila.
        entrada += 2 * MAX_BYTES_BORRADOR + 4096 * len(p.filas_originales) + 16384
        tarifa = cfg.tarifas[cfg.modelos[rol]]
        coste += (entrada * tarifa.entrada + cfg.max_salida_tokens * tarifa.salida) / 1_000_000
    return {"max_llamadas": 10, "max_reserva_usd": coste * 2, "bytes_contexto": bytes_contexto}


def crear_plan(directorio: Path, cfg: ConfiguracionVertex, ejecucion_id: str, motor: MotorMejoras) -> dict:
    """Prepare a complete finite curriculum campaign with explicit unit identities and budget."""

    preparaciones = json.loads((directorio / "preparaciones.json").read_bytes())
    unidades = []
    for unidad in preparaciones["unidades"]:
        archivo = directorio / unidad["archivo"]
        if archivo.name != huella(unidad["solicitud"]) + ".json" or archivo.is_symlink():
            raise ValueError("Preparación fuera del inventario autorizado")
        p = PreparacionMejora.model_validate_json(archivo.read_bytes())
        if p.id != unidad["id"] or p.id != huella(p.model_dump(mode="json", exclude={"id"})):
            raise ValueError("La preparación no corresponde a su inventario")
        unidades.append(
            unidad
            | {
                "sha256": hashlib.sha256(archivo.read_bytes()).hexdigest(),
                "entorno": motor.entorno(p),
                "preflight": reserva_unidad(p, cfg),
            }
        )
    if len(unidades) != 108 or sum(u["filas"] for u in unidades) != 1020:
        raise ValueError("Esta campaña debe conservar las 108 unidades y 1.020 filas V4")
    datos = {
        "version": "campana-mejoras-1",
        "ejecucion_id": ejecucion_id,
        "configuracion": cfg.model_dump(mode="json"),
        "unidades": unidades,
        "huella_curriculo": preparaciones["huella_curriculo"],
        "huella_catalogo": preparaciones["huella_catalogo"],
        "preflight": {
            "llamadas_maximas": sum(u["preflight"]["max_llamadas"] for u in unidades),
            "reserva_maxima_usd": sum(u["preflight"]["max_reserva_usd"] for u in unidades),
            "llamadas_preparacion": 0,
        },
    }
    return {"id": huella(datos), **datos}


def ejecutar_campana(
    plan: dict, *, directorio: Path, raiz: Path, runtime, seleccion: tuple[str, ...] = (), trabajadores: int = 1
) -> dict:
    """Execute or resume the fixed campaign without resetting accumulated reservations."""

    if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
        raise ValueError("El protocolo de campaña cambió")
    cfg = ConfiguracionVertex.model_validate(plan["configuracion"])
    registro = Registro(raiz / "data/operaciones/registro.sqlite")
    proveedor = Vertex(cfg, registro, plan["ejecucion_id"])
    motor = MotorMejoras(PreparadorMejoras(runtime, raiz=raiz), proveedor)
    if not 1 <= trabajadores <= 8:
        raise ValueError("La campaña permite entre uno y ocho workflows concurrentes")

    def procesar(unidad):
        archivo = directorio / unidad["archivo"]
        if archivo.name != huella(unidad["solicitud"]) + ".json" or archivo.is_symlink():
            raise ValueError("La ruta de una preparación cambió")
        if hashlib.sha256(archivo.read_bytes()).hexdigest() != unidad["sha256"]:
            raise ValueError("Una preparación cambió después del preflight")
        p = PreparacionMejora.model_validate_json(archivo.read_bytes())
        if p.id != unidad["id"] or motor.entorno(p) != unidad["entorno"]:
            raise ValueError("Cambió el contexto, código, prompts o modelos de la campaña")
        # La reanudación terminal no requiere nuevas reservas, pero sí toda la verificación durable.
        salida = directorio / "resultados" / f"{p.id}.json"
        cota = unidad["preflight"] if not salida.exists() else {"max_llamadas": 0, "max_reserva_usd": 0}
        with fondos.unidad(p.id, cota):
            return ejecutar_preparada(unidad, p, salida)

    def ejecutar_preparada(unidad, p, salida):
        LOGGER.info(
            "VERDE propuesta: grado %s, %s, %s", p.solicitud.grado, p.solicitud.asignatura_malla, p.solicitud.unidad
        )
        estado = ejecutar_durable(
            motor,
            archivo=raiz / "data/operaciones/mejoras_checkpoints.sqlite",
            solicitud=p.solicitud.model_dump(mode="json"),
            thread_id=plan["id"] + ":" + p.id,
            ejecucion_id=plan["ejecucion_id"],
            huella_entorno=unidad["entorno"],
            max_concurrencia=4,
        )
        resultado = estado["resultado"]
        escribir_nuevo_o_igual(
            salida,
            {
                "preparacion": p.model_dump(mode="json"),
                "resultado": resultado,
                "entorno": unidad["entorno"],
                "plan_id": plan["id"],
            },
        )
        LOGGER.info("%s cierre curricular: %s", "VERDE" if resultado["propuesta"] else "AMARILLO", resultado["estado"])
        return resultado

    fondos = FondosCampana(registro, plan["ejecucion_id"], max_llamadas=cfg.max_llamadas, max_usd=cfg.max_usd)
    unidades = [u for u in plan["unidades"] if not seleccion or u["id"] in seleccion]
    from concurrent.futures import ThreadPoolExecutor

    archivo = raiz / "data/operaciones/mejoras_checkpoints.sqlite"
    with _bloqueo(archivo, "campana-" + huella(plan["ejecucion_id"])):
        with ThreadPoolExecutor(max_workers=trabajadores) as pool:
            resultados = list(pool.map(procesar, unidades))
    return {"resultados": resultados, "consumo": registro.resumen(plan["ejecucion_id"])}
