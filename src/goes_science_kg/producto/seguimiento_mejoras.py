"""Follow finite incident cohorts without repeating approved units or hiding prior evidence."""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from goes_science_kg.ingesta.web_cientifica import RepositorioWeb
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import _bloqueo, ejecutar_durable
from goes_science_kg.motor.esquemas import contrato_transporte
from goes_science_kg.motor.esquemas_mejoras import esquema_redaccion
from goes_science_kg.motor.fragmentos import preparar_fragmentos
from goes_science_kg.motor.mejoras import REDACTOR, MotorMejoras
from goes_science_kg.motor.prompts import serializar
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.operacion.fondos import FondosCampana
from goes_science_kg.producto.campana_mejoras import escribir_nuevo_o_igual, reserva_unidad
from goes_science_kg.producto.mejoras_contratos import MAX_BYTES_BORRADOR, ROLES_MEJORA, BorradorMejora
from goes_science_kg.producto.mejoras_publicadas import CasoMejora
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras, datos_mejora
from goes_science_kg.producto.validacion_mejoras import evaluar_ronda, resolver_mejora, validar_borrador
from goes_science_kg.recuperacion.ciencia_web import fragmentar_web

INSTRUCCION = """
Seguimiento documentado de incidencias, con los mismos criterios de aprobación. Corrige todos los
hallazgos recibidos y conserva el alcance completo del original. No busques otro voto para un texto
vetado: produce una modificación sustantiva. Una cita puede respaldar un principio de diseño concreto,
no todo el contenido ni la eficacia del ejemplo. Relaciona en justificacion cada cita con su aporte
preciso; omite citas accesorias que no lo impliquen. Para fuera_alcance conserva el objetivo original
y explica que la referencia externa sólo informa un principio, sin afirmar pertenencia a Ciencias.
Si accion es mantener_objetivo copia literalmente el procedimental, incluidos prefijos y puntuación.
Comprueba todos los materiales contra todas las actividades, incluidos globos, pilas, cables, recipientes,
datos impresos y calculadoras. Condiciona consistentemente indicador, producto y criterio al montaje
cuando requieren recursos. No sustituyas la medición original por una lectura sin declararlo.
No cierres rígidamente recipientes que producen gas. Para conservar masa usa un sistema flexible
adecuado que capture el gas, con supervisión, sin sobrepresión ni improvisar un recipiente hermético.
Respeta estrictamente los máximos: sintesis <= 800 caracteres, indicador/producto/criterio <= 650,
orientacion <= 850, seguridad <= 450, andamiaje/contexto/justificacion <= 600. Son metas de concisión
inferiores al límite del contrato, no autorización para eliminar desempeños. No repitas textos.
"""


class PreparadorSeguimiento(PreparadorMejoras):
    """Add targeted incident evidence without changing the fixed P5 retrieval corpus."""

    def preparar(self, solicitud):
        """Prepare targeted follow-up context without changing the fixed retrieval corpus."""

        p = super().preparar(solicitud)
        fuente = None
        if (solicitud.grado, solicitud.asignatura_malla, solicitud.unidad) == (
            10,
            "Física",
            "1. La física como ciencia",
        ):
            fuente = "openstax_hooke_20261022"
        elif (solicitud.grado, solicitud.asignatura_malla, solicitud.unidad) == (
            10,
            "Química",
            "9. Reacciones químicas",
        ):
            fuente = "openstax_disolucion_20261022"
        if fuente is None:
            return p
        documento = RepositorioWeb(self.raiz / "data/referencias_complementos_2026").evidencia(fuente)
        parrafos = fragmentar_web(documento)
        if fuente.startswith("openstax_hooke"):
            seleccion = [
                e for e in parrafos if "slope of the straight region" in e.texto or "small deformations" in e.texto
            ][:3]
        else:
            seleccion = [e for e in parrafos if "physical" in e.texto.lower() or "exothermic" in e.texto.lower()][:3]
        if not seleccion:
            raise ValueError("La fuente complementaria perdió los párrafos científicos requeridos")
        evidencias = (*p.evidencias, *seleccion)
        grupos = p.grupos | {"complemento_cientifico": tuple(e.id for e in seleccion)}
        fragmentos = preparar_fragmentos(
            evidencias,
            solicitud.unidad,
            max_caracteres=self.max_caracteres,
            max_fragmentos=96,
            grupos_obligatorios=grupos,
        )
        p = p.model_copy(update={"evidencias": evidencias, "grupos": grupos, "fragmentos": tuple(fragmentos)})
        p = p.model_copy(update={"id": huella(p.model_dump(mode="json", exclude={"id"}))})
        if len(json.dumps(datos_mejora(p), ensure_ascii=False)) > self.max_caracteres:
            raise ValueError("El complemento excede el contexto íntegro permitido")
        return p


def solo_revision_fallida(caso: CasoMejora) -> bool:
    """Identify a missing review without repeating already received substantive votes."""

    r = caso.resultado.rondas[-1]
    return bool(
        r.borrador is not None
        and not validar_borrador(r.borrador, caso.preparacion)
        and len(r.dictamenes) == 4
        and any(d.error for d in r.dictamenes)
        and all(
            d.error or (d.lectura and not d.lectura.hallazgos and set(d.lectura.criterios.values()) == {"si"})
            for d in r.dictamenes
        )
    )


class MotorSeguimiento(MotorMejoras):
    """Follow unresolved incidents under the original finite improvement protocol."""

    def __init__(self, preparador, modelo, anterior):
        super().__init__(preparador, modelo)
        self.anterior = anterior

    def entorno(self, p):
        """Fingerprint the follow-up preparation and its original campaign environment."""

        return huella(
            {
                "base": super().entorno(p),
                "anterior": huella(self.anterior),
                "seguimiento": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "instruccion": INSTRUCCION,
            }
        )

    def _generar(self, estado):
        if not estado["rondas"] and solo_revision_fallida(self.anterior):
            return {r: None for r in ROLES_MEJORA} | {
                "borrador": self.anterior.resultado.rondas[-1].borrador.model_dump(mode="json"),
                "error_generacion": None,
                "respuesta_rechazada": None,
                "errores_generacion": [],
            }
        from goes_science_kg.producto.mejoras_contratos import PreparacionMejora, RondaMejora

        p = PreparacionMejora.model_validate(estado["preparacion"])
        datos = datos_mejora(p) | {"restricciones_de_salida": BorradorMejora.model_json_schema()}
        if estado["rondas"]:
            anterior = RondaMejora.model_validate(estado["rondas"][-1])
            motivos = evaluar_ronda(anterior, p, self._modelos())[1]
        else:
            anterior = self.anterior.resultado.rondas[-1]
            motivos = tuple(
                m
                for r in self.anterior.resultado.rondas
                for m in evaluar_ronda(r, self.anterior.preparacion, self._modelos())[1]
            )
        datos |= {
            "borrador_anterior": anterior.borrador.model_dump(mode="json") if anterior.borrador else None,
            "problemas_a_corregir": motivos,
            "respuesta_previa_no_validada": anterior.respuesta_rechazada,
            "errores_de_contrato": anterior.errores_generacion,
        }
        nuevo = {r: None for r in ROLES_MEJORA}
        try:
            b = self.modelo.generar(
                rol="redactor_curricular",
                sistema=REDACTOR + INSTRUCCION,
                mensaje=serializar(datos),
                esquema=contrato_transporte(esquema_redaccion(p)),
            )
            b = BorradorMejora.model_validate(b.model_dump(mode="json"))
            if anterior.borrador == b:
                return nuevo | {"borrador": None, "error_generacion": "ReparacionIdentica"}
            return nuevo | {
                "borrador": b.model_dump(mode="json"),
                "error_generacion": None,
                "respuesta_rechazada": None,
                "errores_generacion": [],
            }
        except Exception as error:
            texto = getattr(error, "texto_respuesta", None)
            return nuevo | {
                "borrador": None,
                "error_generacion": type(error).__name__,
                "respuesta_rechazada": texto if texto and len(texto.encode()) <= MAX_BYTES_BORRADOR else None,
                "errores_generacion": list(getattr(error, "detalles_validacion", ())),
            }

    def _revisar(self, estado, rol):
        previo = self.anterior.resultado.rondas[-1]
        if not estado["rondas"] and solo_revision_fallida(self.anterior):
            d = next(d for d in previo.dictamenes if d.rol == rol)
            if not d.error:
                return {rol: d.model_dump(mode="json")}
        return super()._revisar(estado, rol)


def crear_seguimiento(directorio, *, raiz, runtime, destino):
    """Create a fixed follow-up plan retaining all prior unit outcomes."""

    plan_base = json.loads((directorio / "plan.json").read_bytes())
    if plan_base["id"] != huella({k: v for k, v in plan_base.items() if k != "id"}):
        raise ValueError("El plan anterior cambió")
    cfg = ConfiguracionVertex.model_validate(plan_base["configuracion"])
    registro = Registro(raiz / "data/operaciones/registro.sqlite")
    proveedor = Vertex(cfg, registro, plan_base["ejecucion_id"])
    preparador = PreparadorSeguimiento(runtime, raiz=raiz)
    tareas = []
    for u in plan_base["unidades"]:
        c = CasoMejora.model_validate_json((directorio / "resultados" / f"{u['id']}.json").read_bytes())
        if c.plan_id != plan_base["id"] or c.entorno != u["entorno"] or c.preparacion.id != u["id"]:
            raise ValueError("El antecedente pertenece a otro protocolo")
        if (
            resolver_mejora(
                c.preparacion,
                c.resultado.rondas,
                ejecucion_id=c.resultado.ejecucion_id,
                modelos={r: cfg.modelos[r] for r in ROLES_MEJORA},
            )
            != c.resultado
        ):
            raise ValueError("Los antecedentes no corresponden a sus votos")
        if c.resultado.propuesta:
            continue
        p = preparador.preparar(c.preparacion.solicitud)
        motor = MotorSeguimiento(preparador, proveedor, c)
        tareas.append(
            {
                "anterior": c.model_dump(mode="json"),
                "preparacion": p.model_dump(mode="json"),
                "modo": "recuperar_revision" if solo_revision_fallida(c) else "reparar_con_hallazgos",
                "entorno": motor.entorno(p),
                "preflight": reserva_unidad(p, cfg),
            }
        )
    datos = {
        "version": "seguimiento-mejoras-1",
        "plan_anterior_id": plan_base["id"],
        "configuracion": cfg.model_dump(mode="json"),
        "ejecucion_id": plan_base["ejecucion_id"],
        "tareas": tareas,
    }
    plan = {"id": huella(datos), **datos}
    escribir_nuevo_o_igual(destino / "plan.json", plan)
    return plan


def ejecutar_seguimiento(plan, *, raiz, runtime, destino):
    """Execute or resume unresolved incident work without resetting the shared budget."""

    if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
        raise ValueError("El plan de seguimiento cambió")
    cfg = ConfiguracionVertex.model_validate(plan["configuracion"])
    registro = Registro(raiz / "data/operaciones/registro.sqlite")
    proveedor = Vertex(cfg, registro, plan["ejecucion_id"])
    preparador = PreparadorSeguimiento(runtime, raiz=raiz)
    fondos = FondosCampana(registro, plan["ejecucion_id"], max_llamadas=cfg.max_llamadas, max_usd=cfg.max_usd)

    def procesar(tarea):
        anterior = CasoMejora.model_validate(tarea["anterior"])
        if anterior.resultado.propuesta:
            raise ValueError("No se reevalúa una propuesta ya respaldada")
        p = preparador.preparar(anterior.preparacion.solicitud)
        motor = MotorSeguimiento(preparador, proveedor, anterior)
        if p.model_dump(mode="json") != tarea["preparacion"] or motor.entorno(p) != tarea["entorno"]:
            raise ValueError("El entorno del seguimiento cambió")
        salida = destino / "resultados" / f"{p.id}.json"
        cota = tarea["preflight"] if not salida.exists() else {"max_llamadas": 0, "max_reserva_usd": 0}
        with fondos.unidad(p.id, cota):
            estado = ejecutar_durable(
                motor,
                archivo=raiz / "data/operaciones/mejoras_checkpoints.sqlite",
                solicitud=p.solicitud.model_dump(mode="json"),
                thread_id=plan["id"] + ":" + p.id,
                ejecucion_id=plan["ejecucion_id"],
                huella_entorno=tarea["entorno"],
                max_concurrencia=2,
            )
        caso = CasoMejora(preparacion=p, resultado=estado["resultado"], entorno=tarea["entorno"], plan_id=plan["id"])
        escribir_nuevo_o_igual(salida, caso.model_dump(mode="json"))
        return caso

    with _bloqueo(raiz / "data/operaciones/mejoras_checkpoints.sqlite", "campana-" + huella(plan["ejecucion_id"])):
        with ThreadPoolExecutor(max_workers=2) as pool:
            return list(pool.map(procesar, plan["tareas"]))


def incorporar_seguimiento(casos, directorio, plan_base):
    """Incorporate follow-up results without erasing original failures or abstentions."""

    plan = json.loads((directorio / "plan.json").read_bytes())
    if (
        plan["id"] != huella({k: v for k, v in plan.items() if k != "id"})
        or plan["plan_anterior_id"] != plan_base["id"]
    ):
        raise ValueError("El seguimiento no corresponde al protocolo anterior")
    anteriores = {c.preparacion.id: c for c in casos}
    pendientes = {i for i, c in anteriores.items() if c.resultado.propuesta is None}
    ids = [t["anterior"]["preparacion"]["id"] for t in plan["tareas"]]
    if len(ids) != len(set(ids)) or set(ids) != pendientes:
        raise ValueError("El seguimiento debe conservar todas las incidencias, sin repetir aprobaciones")
    reemplazos = {}
    for t in plan["tareas"]:
        if anteriores[t["anterior"]["preparacion"]["id"]].model_dump(mode="json") != t["anterior"]:
            raise ValueError("El seguimiento perdió sus antecedentes completos")
        c = CasoMejora.model_validate_json(
            (directorio / "resultados" / (t["preparacion"]["id"] + ".json")).read_bytes()
        )
        if (c.preparacion.model_dump(mode="json"), c.plan_id, c.entorno) != (
            t["preparacion"],
            plan["id"],
            t["entorno"],
        ):
            raise ValueError("El resultado de seguimiento cambió de contexto o entorno")
        reemplazos[t["anterior"]["preparacion"]["id"]] = c
    return [reemplazos.get(c.preparacion.id, c) for c in casos]
