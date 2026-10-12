"""El ciclo de apoyo (spec 13, «Retroalimentación educativa»): el grafo orienta, la respuesta aporta evidencia, la
evidencia actualiza el estado y el estado decide la siguiente intervención.

1. Objetivo: el tema de la malla (ya alineado) y sus bases.
2. Previo: activación breve si una base de profundidad 1 la malla la enseña después del objetivo.
3. Evaluación inicial con una actividad del objetivo.
4. Si falla: hipótesis → sondeos → refuerzo de lo confirmado (planificador, con límites).
5. Reevaluación con OTRA actividad del objetivo (otra habilidad).
6. Estado: logro provisional o nota al docente; repasos espaciados; vuelta al objetivo.

La evaluación de opción múltiple y numérica es determinista. Las respuestas abiertas necesitan un evaluador con
rúbrica (pendiente; spec 13), por eso la capa pedagógica del prototipo solo usa esos dos formatos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from goes_science_kg.config import cargar

from . import diagnostico, planificador
from .contexto import paquete
from .estudiante import Evidencia, Intervencion, Perfil
from .pedagogia import Pedagogia
from .relaciones import Navegador


def config() -> dict:
    return cargar("aprendizaje")


def evaluar(actividad: dict, respuesta: str, ped: Pedagogia) -> tuple[bool, str | None]:
    """Función de evaluación: (¿correcta?, dificultad que delata la respuesta, si alguna)."""
    if actividad["formato"] == "numerica":
        try:
            return abs(float(respuesta) - float(actividad["valor"])) <= float(actividad["tolerancia"]), None
        except ValueError:
            return False, None
    if respuesta == actividad["correcta"]:
        return True, None
    dif = ped.dificultad_de_opcion(actividad, respuesta)
    return False, dif["id"] if dif else None


@dataclass
class Guion:
    """Estudiante simulado: por id de actividad, «correcta», «distractor» (elige el distractor que delata una
    dificultad) o «incorrecta» (otra opción errónea). Lo que no figura se responde bien."""

    respuestas: dict[str, str] = field(default_factory=dict)

    def responder(self, actividad: dict) -> str:
        modo = self.respuestas.get(actividad["id"], "correcta")
        if actividad["formato"] == "numerica":
            return str(actividad["valor"]) if modo == "correcta" else str(round(float(actividad["valor"]) * 2 + 1, 3))
        if modo == "correcta":
            return actividad["correcta"]
        distractores = sorted(actividad.get("distractores") or {})
        if modo == "distractor" and distractores:
            return distractores[0]
        erroneas = sorted(o for o in actividad["opciones"] if o != actividad["correcta"])
        return next((o for o in erroneas if o not in distractores), erroneas[0])


@dataclass
class Paso:
    n: int
    fase: str
    texto: str


class Sesion:
    """Una sesión de un estudiante con un objetivo. No escribe en las capas compartidas."""

    def __init__(self, perfil: Perfil, nav: Navegador, ped: Pedagogia, guion: Guion, fecha: date,
                 cola: Path | None = None):
        self.perfil, self.nav, self.ped, self.guion, self.fecha = perfil, nav, ped, guion, fecha
        self.presupuesto = planificador.Presupuesto(cola=cola)
        self.previas: dict[str, tuple[float, str]] = {}
        self.usadas: set[str] = set()
        self.pasos: list[Paso] = []
        self.contextos: list[dict] = []

    # -- utilidades ---------------------------------------------------------------------------------------------
    def _paso(self, fase: str, texto: str) -> None:
        self.pasos.append(Paso(len(self.pasos) + 1, fase, texto))

    def _nombre(self, cid: str) -> str:
        return self.nav.por_id[cid].etiqueta if cid.startswith("CON:") else cid.removeprefix("TEMA:")

    def presentar(self, actividad: dict, objetivo: str, fase: str) -> Evidencia:
        """Presenta una actividad, evalúa la respuesta y actualiza SOLO lo que la actividad evalúa."""
        respuesta = self.guion.responder(actividad)
        correcta, dif = evaluar(actividad, respuesta, self.ped)
        for c in actividad["evalua"]:
            self.previas.setdefault(c, diagnostico.previa(self.nav, objetivo, c))
        antes = {c: self._p(c) for c in actividad["evalua"]}
        ev = Evidencia(f"E{len(self.perfil.evidencias) + 1}", self.fecha.isoformat(), actividad["id"], objetivo,
                       list(actividad["evalua"]), respuesta, correcta, dif)
        self.perfil.observar(ev, actividad["formato"], self.previas)
        self.usadas.add(actividad["id"])
        cambios = ", ".join(f"P({self._nombre(c)}) {antes[c]:.2f}→{self._p(c):.2f}" for c in actividad["evalua"])
        self._paso(fase, f"{actividad['id']} [{actividad['rol']}, {actividad['habilidad']}] → «{respuesta}» "
                         f"{'✓' if correcta else '✗'}{f' (delata {dif})' if dif else ''}. {cambios}")
        return ev

    def _p(self, cid: str) -> float:
        tabla = self.perfil.objetivos if cid.startswith("TEMA:") else self.perfil.conceptos
        return tabla[cid].p if cid in tabla else self.previas.get(cid, (float("nan"), ""))[0]

    # -- funciones -----------------------------------------------------------------------------------------------
    def diagnosticar(self, objetivo: str, actividad: dict, ev: Evidencia) -> diagnostico.Hipotesis | None:
        hs = diagnostico.abrir(self.perfil, self.nav, self.ped, objetivo, actividad, ev, self.previas)
        self._paso("diagnóstico", "Hipótesis (en el orden en que se comprueban): " + "; ".join(
            f"{h.id} {h.tipo.replace('_', ' ')} «{self._nombre(h.concepto)}» ({h.puntaje})" for h in hs))
        conf = diagnostico.comprobar(hs, self.perfil, self.ped, self.perfil.grado,
                                     lambda a: self.presentar(a, objetivo, "sondeo"), self.usadas)
        self._paso("diagnóstico", "Resultado: " + "; ".join(f"{h.id} {h.estado}" for h in hs))
        return conf

    def reforzar(self, objetivo: str, concepto: str, momento: str, motivo: str, profundidad: int) -> bool:
        """Planifica y aplica un refuerzo; si su comprobación falla, busca una base faltante (con límites)."""
        i = planificador.refuerzo(self.perfil, self.nav, self.ped, objetivo, concepto, momento, motivo, profundidad,
                                  self.presupuesto)
        if i is None:
            self._paso(momento, self.presupuesto.notas_docente[-1])
            return False
        mt = self.ped.microtemas[i.recurso]
        self.contextos.append(paquete(self.perfil, self.nav, self.ped, objetivo, concepto))
        self._paso(momento, f"Refuerzo {i.id} ({momento}, profundidad {profundidad}): {mt['id']} «{mt['titulo']}» "
                            f"[{mt['estado']}], {mt['duracion_min']} min. Motivo: {motivo}.")
        self.presentar(self.ped.actividades[mt["practica"]], objetivo, momento)
        comprobaciones = [mt["comprobacion"]] + [a["id"] for a in self.ped.es_evaluado_por(
            concepto, grado=self.perfil.grado) if a["rol"] in ("sondeo", "comprobacion")]
        for _ in range(config()["refuerzo"]["intentos_por_refuerzo"]):
            act_id = next((x for x in comprobaciones if x not in self.usadas), None)
            if act_id is None:
                break
            act = self.ped.actividades[act_id]
            ev = self.presentar(act, objetivo, momento)
            i.intentos += 1
            if ev.correcta:
                i.resultado = "cumplido"
                self.perfil.aprendio(concepto)
                if concepto in self.nav.conceptos_de_tema(objetivo, ("principal",)):
                    self.perfil.aprendio(objetivo)   # reforzar el concepto del objetivo es reforzar el objetivo
                self._paso(momento, f"Criterio cumplido: se vuelve a {objetivo.removeprefix('TEMA:')}.")
                return True
            conf = self.diagnosticar(objetivo, act, ev)
            if conf and conf.tipo == "base":
                self.reforzar(objetivo, conf.concepto, "durante", f"hipótesis {conf.id} confirmada", profundidad + 1)
        i.resultado = "no_cumplido"
        self.presupuesto.notas_docente.append(f"«{self._nombre(concepto)}»: criterio no cumplido tras {i.intentos} "
                                              "intentos; acompañamiento del docente.")
        self._paso(momento, self.presupuesto.notas_docente[-1])
        return False

    def ejecutar(self, objetivo: str) -> dict:
        """El ciclo completo para un objetivo. Devuelve el resumen (también queda en el perfil)."""
        principal = self.nav.conceptos_de_tema(objetivo, ("principal",))[0]
        t = self.nav.por_id[objetivo]
        self._paso("objetivo", f"{objetivo.removeprefix('TEMA:')} ({t.grado}.°): {t.props.get('indicador')}")
        self.contextos.append(paquete(self.perfil, self.nav, self.ped, objetivo))
        for b in planificador.bases_previas(self.nav, objetivo):
            self.reforzar(objetivo, b.concepto, "previo",
                          f"secuencia de la malla: «{self._nombre(b.concepto)}» se trabaja por primera vez en "
                          f"{(b.primer_tema or 'ningún tema').removeprefix('TEMA:')}, no antes del objetivo", 1)
        acts = self.ped.es_evaluado_por(objetivo, rol="objetivo", grado=self.perfil.grado)
        if not acts:
            raise ValueError(f"No hay actividades para {objetivo} en {self.perfil.grado}.°")
        inicial = acts[0]
        ev = self.presentar(inicial, objetivo, "evaluación")
        if not ev.correcta:
            conf = self.diagnosticar(objetivo, inicial, ev)
            if conf:
                self.reforzar(objetivo, conf.concepto, "durante", f"hipótesis {conf.id} confirmada",
                              0 if conf.tipo == "en_el_concepto" else 1)
            else:
                self.reforzar(objetivo, principal, "durante", "ninguna base confirmada: dificultad en el objetivo", 0)
        otra = next((a for a in acts if a["id"] not in self.usadas and a["habilidad"] != inicial["habilidad"]),
                    next((a for a in acts if a["id"] not in self.usadas), None))
        final = self.presentar(otra, objetivo, "reevaluación") if otra else ev
        estado = self.perfil.objetivos[objetivo]
        if final.correcta:
            if estado.estado != "dominado":
                estado.estado = "logrado_provisional"
            repasos = self.perfil.programar_repasos(objetivo, self.fecha)
            self.perfil.intervenciones.append(Intervencion(
                f"I{len(self.perfil.intervenciones) + 1}", "posterior", objetivo, principal,
                f"logro en la sesión ({final.id})", "repaso espaciado con actividades del objetivo", "—",
                [f"malla {objetivo}"], 5, "una actividad del objetivo distinta de las ya usadas, correcta",
                "un fallo vuelve el repaso al primer intervalo", 0, "pendiente"))
            self._paso("cierre", f"Objetivo {estado.estado.replace('_', ' ')} (P={estado.p:.2f}). Repasos: "
                                 + ", ".join(r.fecha for r in repasos) + ". Se vuelve a la secuencia de la malla.")
        else:
            self.presupuesto.notas_docente.append("La reevaluación del objetivo no se cumplió: acompañamiento docente.")
            self._paso("cierre", self.presupuesto.notas_docente[-1])
        return {"objetivo": objetivo, "estado": estado.estado, "p": round(estado.p, 3),
                "refuerzos": self.presupuesto.refuerzos, "minutos_desvio": self.presupuesto.minutos,
                "notas_docente": self.presupuesto.notas_docente, "propuestas": self.presupuesto.propuestas}
