"""Review complete unit proposals with four blind roles and bounded repair."""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import TypedDict

from goes_science_kg.motor.contratos import huella
from goes_science_kg.motor.esquemas import contrato_transporte
from goes_science_kg.motor.esquemas_mejoras import esquema_redaccion
from goes_science_kg.motor.prompts import BASE, serializar
from goes_science_kg.motor.seleccion import esquema_por_grupos, ids_seleccionados
from goes_science_kg.producto.mejoras_contratos import (
    MAX_BYTES_BORRADOR,
    ROLES_MEJORA,
    BorradorMejora,
    DictamenMejora,
    LecturaMejora,
    PreparacionMejora,
    ResultadoMejora,
    RondaMejora,
    SolicitudMejora,
    esquema_revision,
)
from goes_science_kg.producto.preparacion_mejoras import PreparadorMejoras, datos_mejora
from goes_science_kg.producto.validacion_mejoras import evaluar_ronda, resolver_mejora, validar_borrador

LOGGER = logging.getLogger(__name__)
VERSION = "curricularizacion-v4-1"
REDACTOR = (
    BASE
    + """
Diseña una propuesta de mejora curricular para TODAS las filas de la unidad, en su orden. No redactas
una nueva fuente ni afirmas eficacia. Las filas son originales V4; los textos repetidos se conservan
íntegros en textos_originales_registrados: resuelve cada objeto texto_registrado por su ID T:.
Preserva intención, contenido científico, número de temas, grado, horas y etapas originales. No quites,
agregues, fusiones ni muevas temas. No completes una fase ausente como si perteneciera al original.
Cada componente exigido por los indicadores, la evidencia y las fases originales debe seguir evaluándose:
no reduzcas tres magnitudes a dos, tres estados a dos, clasificación por origen y propiedades a sólo origen,
ni experimentos con control a demostraciones sin control. No confundas dureza con deformabilidad ni calor
con temperatura. Todos los objetos e instrumentos utilizados, incluso los cotidianos o las tarjetas,
deben declararse como recursos condicionales cuando no sean papel y lápiz. Esas condiciones no constatan
que una escuela disponga de ellos. Para ilustraciones propuestas en papel declara expresamente dibujadas.
Puedes proponer precisión del objetivo, un indicador observable, producto evaluable, criterio de logro,
orientación didáctica y andamiaje. Si mantienes el objetivo, cópialo exactamente; si lo precisas, declara
precisar_objetivo. Conserva todas las disciplinas ya respaldadas; las propuestas para clasificaciones
pendientes son sugerencias revisables que no sobrescriben el catálogo. Marca fuera_alcance solamente
las filas que el catálogo original ya declara fuera de Ciencias, con disciplinas_propuestas vacías.
Usa PISA/ERCE, progresiones y países como referencias de diseño: no homologues grados, equipares
poblaciones ni afirmes cobertura por compartir tema o verbo. No fuerces indagación experimental cuando
el objetivo exige otro desempeño. Los recursos son hipotéticos: papel/lápiz; puede proponerse observación
cotidiana segura o representación en papel. No supongas laboratorio, internet, dispositivos ni datos de
una escuela. El contexto salvadoreño es un ejemplo propuesto, sin estadísticas inventadas.
Si el desempeño original exige medir, experimentar o salir al campo, no lo sustituyas por copiar,
leer ni dibujar: declara en recursos_condicionales lo necesario, no constatado, y en seguridad las
restricciones de uso y supervisión. La orientación es un diseño condicionado a conseguir esos recursos.
Cuando papel/lápiz bastan, recursos_condicionales puede ser vacío. Nunca propongas cultivos patógenos,
ingestión, mezclas domésticas peligrosas, tensión de red ni contacto directo con peligros naturales.
La evaluación debe comprobar el objetivo, con criterios concretos, sin limitarse a copiar la explicación.
Propón apoyos lectores y cuantitativos apropiados al grado. No introduzcas una corrección factual sin
soporte primario. Las alertas conocidas se explicitan; nunca enseñes el error como correcto.
Las enmiendas_cientificas_propuestas muestran antes/después de celdas originales: evalúalas con las
definiciones primarias y declara TODOS sus IDs, en orden, en enmiendas_aceptadas (vacío si no hay).
Su aceptación forma parte de la propuesta que los cuatro especialistas deben juzgar. Las notas
originales con errores se leen como originales, y las enmiendas como correcciones derivadas explícitas.
En fragmentos_ids de cada fila elige al menos un F: del grupo fila_XX correspondiente al objetivo y uno
de fuente externa pertinente. No inventes IDs, literales ni citas de otra fila. Se requieren TODOS los
campos del esquema, aunque una mejora sea mantener un objetivo correcto. Sé conciso sin omitir exigencias:
indicador, producto y criterio pueden agrupar todos los desempeños mediante una lista breve. No copies
errores de las fuentes. No atribuyas una afirmación a una referencia que sólo comparte tema o vocabulario.
"""
)
ENFOQUES = {
    "revision_ciencia": (
        "Eres especialista en las disciplinas científicas de cada fila. Comprueba conceptos, condiciones, "
        "nomenclatura y errores científicos, también en el original. Verifica las propuestas de disciplina "
        "y exige evidencia pertinente para cualquier cambio factual."
    ),
    "revision_curriculo": (
        "Eres especialista en curricularización de Ciencias para El Salvador. Contrasta intención y evaluación "
        "original con objetivo, indicador, producto y criterio propuestos; exige conservación de alcance, filas "
        "y presupuesto, sin confundir referencias nativas con homologación o eficacia."
    ),
    "revision_psicopedagogia": (
        "Eres psicopedagogo en educación científica. Examina abstracción, carga, vocabulario, apoyos lectores "
        "y cuantitativos, gradualidad y accesibilidad para el grado. Evalúas un diseño condicional, "
        "no aprendizaje medido ni un diagnóstico del alumnado."
    ),
    "revision_adversarial": (
        "Eres revisor adversarial. Busca contradicciones, citas que no implican la justificación, supuestos "
        "no declarados, recursos inexistentes, seguridad, falsa cobertura y sustitución de errores científicos "
        "por nuevas afirmaciones no fundamentadas."
    ),
}


def prompt_revision(rol: str) -> str:
    """Build a blind role-specific review prompt for the exact unit proposal."""

    return (
        BASE
        + ENFOQUES[rol]
        + """
Revisa la propuesta completa y TODAS sus filas sin conocer autor, modelo u otros votos.
Los textos_originales_registrados son deduplicación exacta, no resúmenes: resuelve sus referencias T:.
Lee las fuentes originales disponibles y las evidencias de cada grupo. Selecciona un F: válido por
grupo; esa selección documenta lectura y no afirma que todas las bandas extranjeras correspondan al
grado SV. Las cuatro bandas conservan sus poblaciones nativas. No exijas enseñar todos los referentes
en la misma unidad. Evalúas pertinencia del diseño propuesto, no su eficacia ni una enseñanza realizada.
Cada criterio admite si/no/insuficiente. Usa no ante un error identificable e insuficiente si falta
evidencia decisiva; nunca compensar un error con otra fortaleza. Hallazgos contiene sólo problemas no
resueltos: para aprobación completa debe ser vacío. Declara límites por separado. No inventes citas.
Expón cada hallazgo en como máximo 100 palabras, identificando la fila y la contradicción precisa;
no copies párrafos enteros del insumo ni repitas el mismo hallazgo. Las limitaciones comunes de una
propuesta condicional (recursos no constatados, falta de eficacia medida) van en limites, no son defectos
si están expresamente declaradas y el diseño sí exige obtener los recursos necesarios para impartirse.
"""
    )


class EstadoMejora(TypedDict, total=False):
    """Persist complete unit-improvement preparation, draft, errors, rounds, and outcome."""

    solicitud: dict
    ejecucion_id: str
    huella_entorno: str
    preparacion: dict
    borrador: dict | None
    error_generacion: str | None
    respuesta_rechazada: str | None
    errores_generacion: list[str]
    errores: list[str]
    rondas: list[dict]
    reparaciones: int
    revision_ciencia: dict | None
    revision_curriculo: dict | None
    revision_psicopedagogia: dict | None
    revision_adversarial: dict | None
    resultado: dict


class MotorMejoras:
    """Generate and review unit proposals through four blind roles and bounded repair."""

    def __init__(self, preparador: PreparadorMejoras, modelo):
        self.preparador, self.modelo = preparador, modelo

    def entorno(self, p: PreparacionMejora) -> str:
        """Fingerprint the improvement engine and its explicit preparation environment."""

        raiz = Path(__file__).resolve().parents[1]
        modulos = (
            "motor/mejoras.py",
            "motor/seleccion.py",
            "motor/fragmentos.py",
            "motor/vertex.py",
            "motor/esquemas.py",
            "motor/esquemas_mejoras.py",
            "motor/registro.py",
            "motor/ejecuciones.py",
            "producto/mejoras_contratos.py",
            "producto/preparacion_mejoras.py",
            "producto/validacion_mejoras.py",
            "ingesta/progresiones.py",
            "ingesta/web_cientifica.py",
            "recuperacion/ciencia_web.py",
        )
        return huella(
            {
                "version": VERSION,
                "preparacion": p.id,
                "codigo": {n: hashlib.sha256((raiz / n).read_bytes()).hexdigest() for n in modulos},
                "configuracion": self.modelo.configuracion.model_dump(mode="json")
                if getattr(self.modelo, "configuracion", None)
                else None,
                "modelos": {r: self.modelo.nombre_modelo(r) for r in ("redactor_curricular", *ROLES_MEJORA)},
                "prompts": {"redactor": REDACTOR, **{r: prompt_revision(r) for r in ROLES_MEJORA}},
            }
        )

    def _contexto(self, estado):
        p = self.preparador.preparar(SolicitudMejora.model_validate(estado["solicitud"]))
        if estado.get("huella_entorno") and estado["huella_entorno"] != self.entorno(p):
            raise ValueError("El entorno cambió antes de iniciar; no se invoca ningún modelo")
        return {"preparacion": p.model_dump(mode="json"), "rondas": [], "reparaciones": 0}

    def _generar(self, estado):
        p = PreparacionMejora.model_validate(estado["preparacion"])
        datos = datos_mejora(p)
        datos["restricciones_de_salida"] = BorradorMejora.model_json_schema()
        datos["max_bytes_utf8_respuesta"] = MAX_BYTES_BORRADOR
        if estado["rondas"]:
            anterior = RondaMejora.model_validate(estado["rondas"][-1])
            _, motivos = evaluar_ronda(anterior, p, self._modelos())
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
                sistema=REDACTOR,
                mensaje=serializar(datos),
                esquema=contrato_transporte(esquema_redaccion(p)),
            )
            b = BorradorMejora.model_validate(b.model_dump(mode="json"))
            if estado["rondas"] and anterior.borrador == b:
                return nuevo | {"borrador": None, "error_generacion": "ReparacionIdentica"}
            return nuevo | {
                "borrador": b.model_dump(mode="json"),
                "error_generacion": None,
                "respuesta_rechazada": None,
                "errores_generacion": [],
            }
        except Exception as error:
            LOGGER.error("ROJO propuesta curricular: %s", type(error).__name__)
            texto = getattr(error, "texto_respuesta", None)
            return nuevo | {
                "borrador": None,
                "error_generacion": type(error).__name__,
                "respuesta_rechazada": texto if texto and len(texto.encode()) <= MAX_BYTES_BORRADOR else None,
                "errores_generacion": list(getattr(error, "detalles_validacion", ())),
            }

    def _validar(self, estado):
        p = PreparacionMejora.model_validate(estado["preparacion"])
        b = BorradorMejora.model_validate(estado["borrador"]) if estado.get("borrador") else None
        return {"errores": list(validar_borrador(b, p)) if b else ["No hay borrador válido"]}

    def _revisar(self, estado, rol):
        p = PreparacionMejora.model_validate(estado["preparacion"])
        b = BorradorMejora.model_validate(estado["borrador"])
        lectura, error = None, None
        try:
            esquema = esquema_por_grupos(esquema_revision(rol), p.fragmentos, p.grupos)
            respuesta = self.modelo.generar(
                rol=rol,
                sistema=prompt_revision(rol),
                mensaje=serializar(datos_mejora(p) | {"propuesta": b.model_dump(mode="json")}),
                esquema=contrato_transporte(esquema),
            )
            lectura = LecturaMejora(
                criterios=respuesta.criterios.model_dump(),
                fragmentos_ids=ids_seleccionados(respuesta),
                hallazgos=respuesta.hallazgos,
                limites=respuesta.limites,
            )
        except Exception as fallo:
            error = type(fallo).__name__
            LOGGER.error("ROJO revisión curricular %s: %s", rol, error)
        d = DictamenMejora(
            rol=rol,
            modelo=self.modelo.nombre_modelo(rol),
            huella_preparacion=p.id,
            huella_borrador=huella(b),
            lectura=lectura,
            error=error,
        )
        return {rol: d.model_dump(mode="json")}

    def _modelos(self):
        return {r: self.modelo.nombre_modelo(r) for r in ROLES_MEJORA}

    def _cerrar_ronda(self, estado):
        r = RondaMejora(
            borrador=estado.get("borrador"),
            errores_estructura=tuple(estado["errores"]),
            dictamenes=tuple(estado[r] for r in ROLES_MEJORA if estado.get(r)),
            error_generacion=estado.get("error_generacion"),
            respuesta_rechazada=estado.get("respuesta_rechazada"),
            errores_generacion=tuple(estado.get("errores_generacion", ())),
        )
        return {"rondas": [*estado["rondas"], r.model_dump(mode="json")]}

    def _continuar(self, estado):
        p = PreparacionMejora.model_validate(estado["preparacion"])
        r = RondaMejora.model_validate(estado["rondas"][-1])
        tipo, _ = evaluar_ronda(r, p, self._modelos())
        if tipo == "respaldado_automaticamente" or estado["reparaciones"] >= 1:
            return "finalizar"
        if r.error_generacion and r.error_generacion != "ValidationError":
            return "finalizar"
        if r.error_generacion == "ValidationError" and r.respuesta_rechazada is None:
            return "finalizar"
        if any(d.error for d in r.dictamenes):
            return "finalizar"
        if (
            len(
                serializar(
                    {"problemas": evaluar_ronda(r, p, self._modelos())[1], "errores_generacion": r.errores_generacion}
                ).encode()
            )
            > 16384
        ):
            return "finalizar"
        return "reparar"

    def _finalizar(self, estado):
        p = PreparacionMejora.model_validate(estado["preparacion"])
        self.preparador.validar(p)
        resultado = resolver_mejora(
            p,
            tuple(RondaMejora.model_validate(r) for r in estado["rondas"]),
            ejecucion_id=estado["ejecucion_id"],
            modelos=self._modelos(),
        )
        return {"resultado": resultado.model_dump(mode="json")}

    def validar_estado(self, estado):
        """Rehydrate and reconstruct an improvement checkpoint before resumption."""

        p = (
            PreparacionMejora.model_validate(estado["preparacion"])
            if estado.get("preparacion")
            else self.preparador.preparar(SolicitudMejora.model_validate(estado["solicitud"]))
        )
        self.preparador.validar(p)
        if estado["huella_entorno"] != self.entorno(p):
            raise ValueError("El entorno durable cambió; no se reutilizan votos incompatibles")
        if estado.get("resultado"):
            esperado = resolver_mejora(
                p,
                tuple(RondaMejora.model_validate(r) for r in estado["rondas"]),
                ejecucion_id=estado["ejecucion_id"],
                modelos=self._modelos(),
            )
            if ResultadoMejora.model_validate(estado["resultado"]) != esperado:
                raise ValueError("El resultado curricular no corresponde a sus cuatro revisiones")

    def compilar(self, *, checkpointer=None):
        """Compile the unit-improvement workflow with an injected checkpoint backend."""

        from langgraph.graph import END, START, StateGraph

        g = StateGraph(EstadoMejora)
        g.add_node("contexto", self._contexto)
        g.add_node("generar", self._generar)
        g.add_node("validar", self._validar)
        g.add_node("cerrar_ronda", self._cerrar_ronda)
        g.add_node("reparar", lambda e: {"reparaciones": e["reparaciones"] + 1})
        g.add_node("finalizar", self._finalizar)
        for rol in ROLES_MEJORA:
            g.add_node(rol, lambda e, rol=rol: self._revisar(e, rol))
        g.add_edge(START, "contexto")
        g.add_edge("contexto", "generar")
        g.add_edge("generar", "validar")
        g.add_conditional_edges("validar", lambda e: "cerrar_ronda" if e["errores"] else list(ROLES_MEJORA))
        g.add_edge(list(ROLES_MEJORA), "cerrar_ronda")
        g.add_conditional_edges("cerrar_ronda", self._continuar)
        g.add_edge("reparar", "generar")
        g.add_edge("finalizar", END)
        return g.compile(checkpointer=checkpointer)
