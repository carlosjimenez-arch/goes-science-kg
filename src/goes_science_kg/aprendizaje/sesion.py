"""El ciclo de apoyo (spec 13, «Retroalimentación educativa»): el grafo orienta, la respuesta aporta evidencia, la
evidencia actualiza el estado y el estado decide la siguiente intervención.

1. Objetivo: el tema de la malla (ya alineado) y sus bases.
2. Previo: activación breve si una base de profundidad 1 la malla la enseña después del objetivo.
3. Evaluación inicial con una actividad del objetivo.
4. Si falla: hipótesis → sondeos → refuerzo de lo confirmado (planificador, con límites).
5. Reevaluación con OTRA actividad del objetivo (otra habilidad).
6. Estado: logro provisional o nota al docente; repasos espaciados; vuelta al objetivo.

La evaluación de opción múltiple y numérica es determinista. Las respuestas abiertas las califica el evaluador
(evaluador.py, separado del tutor) con su rúbrica; sin evaluador, o si el evaluador no está seguro, van a revisión
docente y no cambian el estado. Con un tutor (tutor.py), cada refuerzo se presenta como diálogo; sin él, con el texto
del microtema.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from goes_science_kg.aprendizaje import diagnostico, planificador
from goes_science_kg.aprendizaje.contexto import paquete
from goes_science_kg.aprendizaje.estudiante import Evidencia, Intervencion, Perfil
from goes_science_kg.aprendizaje.evaluador import Evaluador
from goes_science_kg.aprendizaje.pedagogia import Pedagogia
from goes_science_kg.aprendizaje.relaciones import Navegador
from goes_science_kg.aprendizaje.salvaguardas import limpiar, texto_para_estudiante
from goes_science_kg.aprendizaje.tutor import Tutor
from goes_science_kg.config import cargar


def config() -> dict:
    return cargar("aprendizaje")


def lecturas_numericas(texto: str) -> list[float]:
    """Los valores que puede querer decir una respuesta numérica escrita a mano: «50 000», «50000 Pa», «50.000» o
    «50,000» (miles o decimales: se prueban las dos lecturas), «3,5» o «3.5». Vacía si no hay un número."""
    t = re.sub(r"[^\d.,\-]", "", texto.replace(" ", ""))
    if not re.search(r"\d", t):
        return []
    lecturas = set()
    for decimal, miles in ((".", ","), (",", ".")):
        try:
            lecturas.add(float(t.replace(miles, "").replace(decimal, ".")))
        except ValueError:
            continue
    return sorted(lecturas)


def evaluar(actividad: dict, respuesta: str, ped: Pedagogia) -> tuple[bool, str | None]:
    """Función de evaluación: (¿correcta?, dificultad que delata la respuesta, si alguna). Una respuesta numérica es
    correcta si alguna lectura razonable de lo escrito cae dentro de la tolerancia (panel, 2026-10-12: «50 000» o
    «50000 Pa» no son errores de física)."""
    if actividad["formato"] == "numerica":
        valor, tol = float(actividad["valor"]), float(actividad["tolerancia"])
        return any(abs(x - valor) <= tol for x in lecturas_numericas(str(respuesta))), None
    if respuesta == actividad["correcta"]:
        return True, None
    dif = ped.dificultad_de_opcion(actividad, respuesta)
    return False, dif["id"] if dif else None


def barajar(actividad: dict, semilla: str) -> tuple[dict, dict[str, str]]:
    """La actividad de opción múltiple con las opciones en otro orden, determinista por `semilla` (p. ej. estudiante y
    actividad), y el mapa letra mostrada → letra original para evaluar. La clave y los distractores se reescriben con
    las letras nuevas: el diagnóstico no cambia. Panel, 2026-10-12: la clave era la A en 34 de 84 ítems y la opción más
    larga en 57; sin barajar, un estudiante aprende a elegir la A. La interfaz del piloto muestra la barajada."""
    if actividad.get("formato") != "opcion_multiple":
        return actividad, {}
    originales = sorted(actividad["opciones"])
    orden = originales[:]
    random.Random(f"{semilla}|{actividad['id']}").shuffle(orden)
    a_original = dict(zip(originales, orden, strict=True))          # letra mostrada → letra original
    a_mostrada = {v: k for k, v in a_original.items()}
    mostrada = {**actividad, "opciones": {k: actividad["opciones"][a_original[k]] for k in originales},
                "correcta": a_mostrada[actividad["correcta"]],
                "distractores": {a_mostrada[k]: v for k, v in (actividad.get("distractores") or {}).items()}}
    return mostrada, a_original


@dataclass
class Guion:
    """Estudiante simulado: por id de actividad, «correcta», «distractor» (elige el distractor que delata una
    dificultad) o «incorrecta» (otra opción errónea). Lo que no figura se responde bien."""

    respuestas: dict[str, str] = field(default_factory=dict)

    def responder(self, actividad: dict) -> str:
        modo = self.respuestas.get(actividad["id"], "correcta")
        if actividad["formato"] == "abierta":   # «correcta»: la respuesta modelo; si no, un error típico o el texto
            r = actividad["rubrica"]
            errores = r.get("errores") or []
            if modo == "correcta":
                return r["respuesta_modelo"]
            if modo in ("distractor", "incorrecta") and errores:
                return errores[0 if modo == "distractor" else -1]["ejemplo"]
            return modo
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
                 cola: Path | None = None, tutor: Tutor | None = None, evaluador: Evaluador | None = None):
        self.perfil, self.nav, self.ped, self.guion, self.fecha = perfil, nav, ped, guion, fecha
        self.tutor, self.evaluador = tutor, evaluador
        self.revision_docente: list[dict] = []
        self.presupuesto = planificador.Presupuesto(cola=cola, grado=perfil.grado)
        self.previas: dict[str, tuple[float, str]] = {}
        self.usadas: set[str] = set()
        self.pasos: list[Paso] = []
        self.contextos: list[dict] = []

    # -- utilidades ---------------------------------------------------------------------------------------------
    def _paso(self, fase: str, texto: str) -> None:
        self.pasos.append(Paso(len(self.pasos) + 1, fase, texto))

    def _nombre(self, cid: str) -> str:
        return self.nav.por_id[cid].etiqueta if cid.startswith("CON:") else cid.removeprefix("TEMA:")

    def presentar(self, actividad: dict, objetivo: str, fase: str) -> Evidencia | None:
        """Presenta una actividad, evalúa la respuesta y actualiza SOLO lo que la actividad evalúa. Una respuesta
        abierta que el evaluador no decide va a revisión docente: devuelve None y no cambia el estado."""
        respuesta = self.guion.responder(actividad)
        if actividad["formato"] == "abierta":
            ev_abierta = (self.evaluador.evaluar(actividad, respuesta) if self.evaluador else None)
            if ev_abierta is None or ev_abierta.requiere_docente:
                motivo = ev_abierta.motivo if ev_abierta else "no hay evaluador de respuestas abiertas"
                self.revision_docente.append({"actividad": actividad["id"], "objetivo": objetivo, "motivo": motivo})
                self.usadas.add(actividad["id"])
                self._paso(fase, f"{actividad['id']} [abierta, {actividad['habilidad']}] → «{respuesta}» → revisión "
                                 f"docente ({motivo}). El estado no cambia.")
                return None
            correcta, dif = bool(ev_abierta.correcta), ev_abierta.dificultad
            cumplidos = [c["id"] for c in ev_abierta.criterios if c["cumple"]]
            detalle = f" Evaluador ({ev_abierta.confianza}): criterios cumplidos {', '.join(cumplidos) or 'ninguno'}."
        else:
            correcta, dif = evaluar(actividad, respuesta, self.ped)
            detalle = ""
        for c in actividad["evalua"]:
            self.previas.setdefault(c, diagnostico.previa(self.nav, objetivo, c))
        antes = {c: self._p(c) for c in actividad["evalua"]}
        ev = Evidencia(f"E{len(self.perfil.evidencias) + 1}", self.fecha.isoformat(), actividad["id"], objetivo,
                       list(actividad["evalua"]), respuesta, correcta, dif)
        self.perfil.observar(ev, actividad["formato"], self.previas)
        self.usadas.add(actividad["id"])
        cambios = ", ".join(f"P({self._nombre(c)}) {antes[c]:.2f}→{self._p(c):.2f}" for c in actividad["evalua"])
        self._paso(fase, f"{actividad['id']} [{actividad['rol']}, {actividad['habilidad']}] → «{respuesta}» "
                         f"{'✓' if correcta else '✗'}{f' (delata {dif})' if dif else ''}.{detalle} {cambios}")
        return ev

    def _p(self, cid: str) -> float:
        tabla = self.perfil.objetivos if cid.startswith("TEMA:") else self.perfil.conceptos
        return tabla[cid].p if cid in tabla else self.previas.get(cid, (float("nan"), ""))[0]

    def _turno(self, tarea: str, paq: dict, mt: dict, actividad: dict | None = None, anterior: dict | None = None,
               ev: Evidencia | None = None) -> None:
        """Un turno del tutor (si hay tutor): el texto que vería el estudiante, con las guardas aplicadas."""
        if not self.tutor:
            return
        ultimo = None
        if anterior is not None and ev is not None:
            dif = self.ped.dificultades.get(ev.dificultad or "")
            ultimo = {"enunciado": anterior["enunciado"], "respuesta": limpiar(ev.respuesta)[0],
                      "correcta": ev.correcta, "dificultad": dif["descripcion"] if dif else None}
        t = self.tutor.turno(tarea, paq, mt, actividad, ultimo)
        nota = f" [respaldo: {'; '.join(t.errores)}]" if t.origen == "respaldo" else (
            f" [corregido tras: {'; '.join(t.errores)}]" if t.errores else "")
        self._paso("tutor", f"«{texto_para_estudiante(t.texto())}» (fuentes {', '.join(t.fuentes) or '—'}){nota}")

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
        paq = paquete(self.perfil, self.nav, self.ped, objetivo, concepto)
        self.contextos.append(paq)
        self._paso(momento, f"Refuerzo {i.id} ({momento}, profundidad {profundidad}): {mt['id']} «{mt['titulo']}» "
                            f"[{mt['estado']}], {mt['duracion_min']} min. Motivo: {motivo}.")
        practica = self.ped.actividades[mt["practica"]]
        self._turno("introducir", paq, mt, practica)
        ev_practica = self.presentar(practica, objetivo, momento)
        comprobaciones = [mt["comprobacion"]] + [a["id"] for a in self.ped.es_evaluado_por(
            concepto, grado=self.perfil.grado) if a["rol"] in ("sondeo", "comprobacion")]
        for _ in range(config()["refuerzo"]["intentos_por_refuerzo"]):
            act_id = next((x for x in comprobaciones if x not in self.usadas), None)
            if act_id is None:
                break
            act = self.ped.actividades[act_id]
            self._turno("retroalimentar", paq, mt, act, practica, ev_practica)
            ev = self.presentar(act, objetivo, momento)
            practica, ev_practica = act, ev
            i.intentos += 1
            if ev is not None and ev.correcta:
                i.resultado = "cumplido"
                self.perfil.aprendio(concepto)
                if concepto in self.nav.conceptos_de_tema(objetivo, ("principal",)):
                    self.perfil.aprendio(objetivo)   # reforzar el concepto del objetivo es reforzar el objetivo
                self._turno("cerrar", paq, mt)
                self._paso(momento, f"Criterio cumplido: se vuelve a {objetivo.removeprefix('TEMA:')}.")
                return True
            if ev is None:
                continue
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
        todas = self.ped.es_evaluado_por(objetivo, rol="objetivo", grado=self.perfil.grado)
        acts = [a for a in todas if a["formato"] != "abierta"]
        abiertas = [a for a in todas if a["formato"] == "abierta"] if self.evaluador else []
        if not acts:
            raise ValueError(f"No hay actividades para {objetivo} en {self.perfil.grado}.°")
        inicial = acts[0]
        ev = self.presentar(inicial, objetivo, "evaluación")
        assert ev is not None   # la evaluación inicial nunca es abierta
        if not ev.correcta:
            conf = self.diagnosticar(objetivo, inicial, ev)
            if conf:
                self.reforzar(objetivo, conf.concepto, "durante", f"hipótesis {conf.id} confirmada",
                              0 if conf.tipo == "en_el_concepto" else 1)
            else:
                self.reforzar(objetivo, principal, "durante", "ninguna base confirmada: dificultad en el objetivo", 0)
        # Con evaluador, la reevaluación es la respuesta abierta: otra forma de evidencia (producir una explicación en
        # lugar de elegir una opción). Sin él, otra actividad con otra habilidad.
        otra = next((a for a in abiertas if a["id"] not in self.usadas), None) or next(
            (a for a in acts if a["id"] not in self.usadas and a["habilidad"] != inicial["habilidad"]),
            next((a for a in acts if a["id"] not in self.usadas), None))
        final = self.presentar(otra, objetivo, "reevaluación") if otra else ev
        estado = self.perfil.objetivos[objetivo]
        if final is None:
            self.presupuesto.notas_docente.append("La reevaluación abierta espera la revisión del docente; el objetivo "
                                                  "queda como estaba hasta entonces.")
            self._paso("cierre", self.presupuesto.notas_docente[-1])
        elif final.correcta:
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
                "notas_docente": self.presupuesto.notas_docente, "propuestas": self.presupuesto.propuestas,
                **({"revision_docente": self.revision_docente} if self.revision_docente else {})}
