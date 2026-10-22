"""Document scientific false-positive corrections with new context and four reviews."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila
from goes_science_kg.ingesta.web_cientifica import RepositorioWeb
from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.ejecuciones import _bloqueo, ejecutar_durable
from goes_science_kg.motor.fragmentos import preparar_fragmentos
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.motor.registro import Registro
from goes_science_kg.motor.vertex import ConfiguracionVertex, Vertex
from goes_science_kg.operacion.fondos import FondosCampana
from goes_science_kg.producto.campana_mejoras import escribir_nuevo_o_igual, reserva_unidad
from goes_science_kg.producto.mejoras_contratos import ROLES_MEJORA
from goes_science_kg.producto.mejoras_publicadas import CasoMejora, verificar_preparacion
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras, compactar, datos_mejora
from goes_science_kg.producto.seguimiento_mejoras import MotorSeguimiento
from goes_science_kg.producto.validacion_mejoras import resolver_mejora
from goes_science_kg.recuperacion.ciencia_web import fragmentar_web
from goes_science_kg.recuperacion.modelos import Documento

SOLICITUD = (11, "Biología", "5. Biotecnología microbiana")
HALLAZGO = (
    "La fila 5.3 exige cultivos bacterianos y el original K41 permite levadura como sustituto. "
    "Las levaduras son hongos eucariotas, no bacterias. La propuesta aprobada conservó esa contradicción. "
    "Debe distinguir explícitamente ambos grupos y conservar el objetivo bacteriano. Una práctica requiere "
    "cepa bacteriana identificada de bajo riesgo y procedencia documentada, evaluación previa de riesgos "
    "y condiciones docentes de bioseguridad; nunca suponer que un alimento garantiza un cultivo puro inocuo."
)


class PreparadorRectificacion(PreparadorMejoras):
    """Prepare corrected scientific context while preserving the original false-positive dossier."""

    def preparar(self, solicitud):
        """Build the rectification preparation with original rows and targeted primary evidence."""

        p = super().preparar(solicitud)
        if (solicitud.grado, solicitud.asignatura_malla, solicitud.unidad) != SOLICITUD:
            raise ValueError("Esta rectificación sólo cubre el hallazgo científico documentado")
        fila = next(
            f
            for f in self.runtime.producto.curriculo.filas
            if f.id in p.clasificaciones_originales and f.procedimental.startswith("5.3.")
        )
        celdas = self.runtime.fuentes.hidratar_celdas(documento_de_fila(fila))
        celda = next(c for c in celdas if c.fuente["celdas_verificadas"][0]["coordenada_origen"] == "K41")
        antes = celda.texto
        patron = "levadura o de yogur diluido"
        if antes.count(patron) != 1:
            raise ValueError("La rectificación requiere el texto original exacto de K41")
        despues = antes.replace(
            patron, "una cepa bacteriana identificada de grupo de riesgo 1 y procedencia documentada"
        )
        despues += (
            " La levadura es un hongo y no sustituye a las bacterias del objetivo; "
            "toda práctica exige evaluación previa de riesgos y condiciones docentes de bioseguridad."
        )
        datos = {
            "fuente_id": fila.fuente_id,
            "sha256": celda.fuente["sha256"],
            "hoja": fila.hoja,
            "celda_ancla": "K41",
            "antes": antes,
            "despues": despues,
            "alcance": "Enmienda propuesta para una copia derivada; el original se conserva íntegro",
        }
        enmienda = {"id": "ENMIENDA:" + huella(datos), **datos}
        documento = RepositorioWeb(self.raiz / "data/referencias_complementos_2026").evidencia(
            "openstax_hongos_20261022"
        )
        seleccion = tuple(
            e
            for e in fragmentar_web(documento)
            if "Unicellular fungi are called yeasts" in e.texto or "Fungi are eukaryotes" in e.texto
        )
        if len(seleccion) != 2:
            raise ValueError("La fuente primaria perdió las definiciones de hongos y levaduras")
        import yaml

        cfg = yaml.safe_load((self.raiz / "config/bioseguridad_escolar_2026.yaml").read_text())
        fuentes = FuentesVerificadas(
            {cfg["id"]: cfg},
            raiz_fuentes=self.raiz / "data/referencias_bioseguridad_2026",
            raices_adicionales={"bioseguridad_escolar": self.raiz / "data/referencias_bioseguridad_2026"},
        )
        seguridad = tuple(
            fuentes.hidratar(
                Documento(
                    id=f"BIOSEGURIDAD:{cfg['id']}:P{n:04d}",
                    texto=cfg["titulo"],
                    fuente={"documento": cfg["id"], "pagina": n},
                    version="referencia",
                )
            )
            for n in cfg["paginas_pdf"]
        )
        if any(e is None for e in seguridad):
            raise ValueError("La rectificación perdió su guía primaria de bioseguridad")
        seguridad = tuple(
            e.model_copy(
                update={
                    "fuente": e.fuente
                    | {
                        "titulo": cfg["titulo"],
                        "version_documental": cfg["version_documental"],
                        "url": cfg["url_documento"],
                        "fuente_primaria": True,
                        "alcance": cfg["alcance"],
                    }
                }
            )
            for e in seguridad
        )
        evidencias = (*p.evidencias, compactar(celda), *seleccion, *seguridad)
        grupos = p.grupos | {
            "enmienda_K41": (celda.id,),
            "distincion_hongos_bacterias": tuple(e.id for e in seleccion),
            "bioseguridad_escolar": tuple(e.id for e in seguridad),
        }
        fragmentos = preparar_fragmentos(
            evidencias,
            solicitud.unidad,
            max_caracteres=self.max_caracteres,
            max_fragmentos=96,
            grupos_obligatorios=grupos,
        )
        p = p.model_copy(
            update={
                "evidencias": evidencias,
                "grupos": grupos,
                "fragmentos": tuple(fragmentos),
                "correcciones_requeridas": (enmienda,),
                "alertas": p.alertas | {fila.id: HALLAZGO},
            }
        )
        p = p.model_copy(update={"id": huella(p.model_dump(mode="json", exclude={"id"}))})
        if len(json.dumps(datos_mejora(p), ensure_ascii=False)) > self.max_caracteres:
            raise ValueError("La rectificación excede el contexto completo permitido")
        return p


class MotorRectificacion(MotorSeguimiento):
    """Run the existing improvement protocol against an explicit rectification context."""

    def entorno(self, p):
        """Fingerprint the rectification environment and its explicit implementation."""

        return huella(
            {
                "base": super().entorno(p),
                "codigo_rectificacion": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            }
        )


def preparar_rectificacion(caso, *, configuracion, ejecucion_id, raiz, runtime, destino):
    """Prepare one documented false-positive correction with its new evidence."""

    if not caso.resultado.propuesta:
        raise ValueError("La rectificación documenta un falso positivo previo, no oculta un veto")
    cfg = ConfiguracionVertex.model_validate(configuracion)
    verificar_preparacion(caso.preparacion)
    if (
        resolver_mejora(
            caso.preparacion,
            caso.resultado.rondas,
            ejecucion_id=caso.resultado.ejecucion_id,
            modelos={r: cfg.modelos[r] for r in ROLES_MEJORA},
        )
        != caso.resultado
    ):
        raise ValueError("El antecedente no conserva sus votos completos")
    proveedor = Vertex(cfg, Registro(raiz / "data/operaciones/registro.sqlite"), ejecucion_id)
    preparador = PreparadorRectificacion(runtime, raiz=raiz)
    p = preparador.preparar(caso.preparacion.solicitud)
    motor = MotorRectificacion(preparador, proveedor, caso)
    datos = {
        "version": "rectificacion-cientifica-1",
        "anterior": caso.model_dump(mode="json"),
        "hallazgo": HALLAZGO,
        "preparacion": p.model_dump(mode="json"),
        "configuracion": cfg.model_dump(mode="json"),
        "ejecucion_id": ejecucion_id,
        "entorno": motor.entorno(p),
        "preflight": reserva_unidad(p, cfg),
    }
    plan = {"id": huella(datos), **datos}
    escribir_nuevo_o_igual(destino / "plan.json", plan)
    return plan


def ejecutar_rectificacion(plan, *, raiz, runtime, destino):
    """Execute or resume the correction under its explicit durable budget."""

    if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
        raise ValueError("El protocolo de rectificación cambió")
    cfg = ConfiguracionVertex.model_validate(plan["configuracion"])
    registro = Registro(raiz / "data/operaciones/registro.sqlite")
    proveedor = Vertex(cfg, registro, plan["ejecucion_id"])
    preparador = PreparadorRectificacion(runtime, raiz=raiz)
    anterior = CasoMejora.model_validate(plan["anterior"])
    p = preparador.preparar(anterior.preparacion.solicitud)
    motor = MotorRectificacion(preparador, proveedor, anterior)
    if p.model_dump(mode="json") != plan["preparacion"] or motor.entorno(p) != plan["entorno"]:
        raise ValueError("El entorno de rectificación cambió")
    salida = destino / "resultados" / (p.id + ".json")
    fondos = FondosCampana(registro, plan["ejecucion_id"], max_llamadas=cfg.max_llamadas, max_usd=cfg.max_usd)
    with _bloqueo(raiz / "data/operaciones/mejoras_checkpoints.sqlite", "campana-" + huella(plan["ejecucion_id"])):
        with fondos.unidad(
            p.id, plan["preflight"] if not salida.exists() else {"max_llamadas": 0, "max_reserva_usd": 0}
        ):
            estado = ejecutar_durable(
                motor,
                archivo=raiz / "data/operaciones/mejoras_checkpoints.sqlite",
                solicitud=p.solicitud.model_dump(mode="json"),
                thread_id=plan["id"] + ":" + p.id,
                ejecucion_id=plan["ejecucion_id"],
                huella_entorno=plan["entorno"],
                max_concurrencia=2,
            )
    c = CasoMejora(preparacion=p, resultado=estado["resultado"], entorno=plan["entorno"], plan_id=plan["id"])
    escribir_nuevo_o_igual(salida, c.model_dump(mode="json"))
    return c


def incorporar_rectificacion(casos, directorio):
    """Incorporate the correction while retaining the prior case and full review history."""

    plan = json.loads((directorio / "plan.json").read_bytes())
    if plan["id"] != huella({k: v for k, v in plan.items() if k != "id"}):
        raise ValueError("La rectificación cambió")
    anterior = CasoMejora.model_validate(plan["anterior"])
    if sum(c == anterior for c in casos) != 1:
        raise ValueError("La rectificación no conserva su antecedente exacto")
    nuevo = CasoMejora.model_validate_json(
        (directorio / "resultados" / (plan["preparacion"]["id"] + ".json")).read_bytes()
    )
    if (nuevo.preparacion.model_dump(mode="json"), nuevo.plan_id, nuevo.entorno) != (
        plan["preparacion"],
        plan["id"],
        plan["entorno"],
    ):
        raise ValueError("La rectificación perdió la identidad de su protocolo")
    return [nuevo if c == anterior else c for c in casos]
