"""Preflight de una nueva revisión; un catálogo pendiente no se presenta como publicado."""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel

from goes_science_kg.curriculo.catalogacion import DECLARADAS, ClasificacionFila
from goes_science_kg.curriculo.contexto_fuentes import fuentes_del_curriculo
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.vertex import ConfiguracionVertex
from goes_science_kg.produccion.compilacion import alertas_de_fila
from goes_science_kg.producto.campana_mejoras import reserva_unidad
from goes_science_kg.producto.mejoras_contratos import SolicitudMejora
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras


class CatalogoPendiente(BaseModel):
    """Sólo permite presupuestar; no satisface el contrato de publicación del producto."""

    estado: str = "pendiente_catalogacion_edicion_final"
    huella_curriculo: str
    filas: tuple[ClasificacionFila, ...]


class PreparadorMallasFinales(PreparadorMejoras):
    def preparar(self, solicitud):
        p = super().preparar(solicitud)
        ids = {f["id"] for f in p.filas_originales}
        extras = {
            f.id: [c.model_dump(mode="json") for c in f.celdas if c.campo is None and c.valor is not None]
            for f in self.runtime.producto.curriculo.filas
            if f.id in ids
        }
        p = p.model_copy(
            update={
                "contexto_aula": p.contexto_aula | {"celdas_originales_sin_campo": extras},
                "limites": p.limites
                + (
                    "Respetar las fases presentes de cada hoja, incluidas sus excepciones. "
                    "No agregar fases ausentes ni asignar por "
                    "suposición las celdas sin encabezado; toda reinterpretación sería "
                    "una propuesta derivada explícita.",
                ),
            }
        )
        from goes_science_kg.producto.preparacion_mejoras import datos_mejora

        if len(json.dumps(datos_mejora(p), ensure_ascii=False)) > self.max_caracteres:
            raise ValueError("El contexto final completo excede el límite; no se truncan celdas")
        return p.model_copy(update={"id": huella(p.model_dump(mode="json", exclude={"id"}))})


def preparar_preflight(final, antecedentes, base: Path, cfg: ConfiguracionVertex, consumo: dict):
    decisiones = []
    for f in final.filas:
        declarada = DECLARADAS.get(f.asignatura_malla)
        decisiones.append(
            ClasificacionFila(
                fila_id=f.id,
                estado="declarado_malla" if declarada else "abstencion",
                disciplinas=(declarada,) if declarada else (),
                metodo="asignatura_explicita_malla_final" if declarada else "pendiente_nueva_catalogacion",
                justificacion="Asignatura explícita de la malla final."
                if declarada
                else "No se trasladan los votos de la clasificación anterior.",
            )
        )
    catalogo = CatalogoPendiente(huella_curriculo=final.huella, filas=tuple(decisiones))
    fuentes = fuentes_del_curriculo(final, raiz_v4=base / "insumos/v4_produccion_20261026")
    por_fuente = {f.id: f for f in final.fuentes}
    fuentes.bloqueos_curriculares = {
        f.id: "\n".join(
            a["descripcion"]
            for a in alertas_de_fila(f, por_fuente[f.fuente_id], antecedentes)
            if a["codigo"].startswith("ANTECEDENTE_CIENTIFICO")
        )
        for f in final.filas
    }
    fuentes.bloqueos_curriculares = {k: v for k, v in fuentes.bloqueos_curriculares.items() if v}
    runtime = SimpleNamespace(producto=SimpleNamespace(curriculo=final, catalogo=catalogo), fuentes=fuentes)
    preparador = PreparadorMallasFinales(runtime, raiz=base)
    preparaciones, unidades = [], []
    for grupo in final.agrupaciones:
        p = preparador.preparar(
            SolicitudMejora(grado=grupo.grado, asignatura_malla=grupo.asignatura_malla, unidad=grupo.unidad)
        )
        preparaciones.append(p)
        unidades.append(
            {
                "id": p.id,
                "filas": len(p.filas_originales),
                "solicitud": p.solicitud.model_dump(mode="json"),
                **reserva_unidad(p, cfg),
            }
        )
    pendientes = sum(d.estado == "abstencion" for d in decisiones)
    # Dos lectores por lote de 24. No se han realizado ni se simulan esos votos.
    catalogacion = 2 * ceil(pendientes / 24)
    plan = {
        "version": "preflight-mallas-finales-1",
        "huella_curriculo": final.huella,
        "catalogo_provisional": catalogo.model_dump(mode="json"),
        "unidades": unidades,
        "consumo_previo": consumo,
        "max_llamadas_vigente": cfg.max_llamadas,
        "max_reserva_usd_vigente": cfg.max_usd,
        "saldo_llamadas": max(0, cfg.max_llamadas - consumo["llamadas"]),
        "saldo_reserva_usd": max(0, cfg.max_usd - consumo["reserva_usd"]),
        "primera_pasada_revision_llamadas": 5 * len(unidades),
        "catalogacion_llamadas": catalogacion,
        "revision_con_una_reparacion_llamadas": sum(u["max_llamadas"] for u in unidades),
        "revision_con_una_reparacion_reserva_usd": sum(u["max_reserva_usd"] for u in unidades),
        "controles_adversariales_llamadas": 20,
        "safe_to_start": False,
        "ejecutable": False,
        "motivos": [
            "El saldo no cubre siquiera las cinco invocaciones iniciales por unidad.",
            "Las preparaciones conservan catálogo provisional; hay que completar la catalogación "
            "antes de fijar su identidad ejecutable.",
            "El presupuesto de revisión no incluye aún el precio de catalogación "
            "ni de los veinte controles adversariales.",
        ],
        "llamadas_realizadas": 0,
    }
    return preparaciones, {"id": huella(plan), **plan}
