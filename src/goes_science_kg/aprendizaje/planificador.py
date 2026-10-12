"""Función de planificación del refuerzo (spec 13): qué refuerzo, cuándo, con qué límites y cuándo se vuelve.

Momentos:
- previo: antes del objetivo, solo para bases que la MALLA enseña después (o en el mismo tema). Es una activación
  breve por la secuencia de la malla, no un diagnóstico de déficit del estudiante (a lo sumo `max_previos`).
- durante: tras confirmar una hipótesis (una base, o una dificultad en el concepto evaluado).
- posterior: repaso espaciado del objetivo y transferencia con otra actividad.

Límites (config/aprendizaje.yaml, refuerzo): profundidad, refuerzos por sesión, minutos por refuerzo y por sesión,
intentos. Al tocar un límite se vuelve al objetivo y se deja una nota para el docente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from goes_science_kg.config import cargar

from .estudiante import Intervencion, Perfil
from .pedagogia import Pedagogia, proponer
from .relaciones import CONFIANZA_ORDEN, Base, Navegador, orden_tema


def config() -> dict:
    return cargar("aprendizaje")


@dataclass
class Presupuesto:
    """Lo que lleva gastado una sesión en desvíos (se comprueba antes de cada refuerzo)."""

    refuerzos: int = 0
    minutos: int = 0
    notas_docente: list[str] = field(default_factory=list)
    propuestas: list[dict] = field(default_factory=list)
    cola: Path | None = None   # cola de propuestas (None: la de config/aprendizaje.yaml)

    def admite(self, minutos: int, profundidad: int) -> str | None:
        """None si cabe; si no, el límite que se tocaría."""
        r = config()["refuerzo"]
        if profundidad > r["profundidad_maxima"]:
            return f"profundidad {profundidad} > {r['profundidad_maxima']}"
        if self.refuerzos + 1 > r["max_por_sesion"]:
            return f"más de {r['max_por_sesion']} refuerzos en la sesión"
        if self.minutos + minutos > r["minutos_max_por_sesion"]:
            return f"más de {r['minutos_max_por_sesion']} minutos de desvío"
        return None


def bases_previas(nav: Navegador, objetivo: str) -> list[Base]:
    """Bases de profundidad 1 que la malla no enseña antes del objetivo, la más cercana al objetivo primero."""
    huecos = [b for b in nav.bases(objetivo, profundidad=1) if not b.antes_del_objetivo]
    return sorted(huecos, key=lambda b: (-CONFIANZA_ORDEN[b.confianza], orden_tema(b.primer_tema or "TEMA:G99"),
                                         b.concepto))[:config()["refuerzo"]["max_previos"]]


def refuerzo(perfil: Perfil, nav: Navegador, ped: Pedagogia, objetivo: str, concepto: str, momento: str,
             motivo: str, profundidad: int, presupuesto: Presupuesto) -> Intervencion | None:
    """Arma el refuerzo de un concepto para un objetivo, o None si no hay microtema o se toca un límite (y deja la
    nota o la propuesta correspondiente). No modifica la capa pedagógica: un microtema que falta va a la cola."""
    mt = ped.es_reforzado_por(concepto, perfil.grado)
    nombre = nav.por_id[concepto].etiqueta
    if mt is None:
        presupuesto.propuestas.append(proponer(
            "microtema_faltante", {"concepto": concepto, "grado": perfil.grado, "objetivo": objetivo},
            f"se necesitó reforzar «{nombre}» para {objetivo.removeprefix('TEMA:')} y no hay microtema",
            presupuesto.cola))
        presupuesto.notas_docente.append(f"Sin microtema para «{nombre}» ({perfil.grado}.°): propuesto a revisión.")
        return None
    if limite := presupuesto.admite(mt["duracion_min"], profundidad):
        presupuesto.notas_docente.append(f"Límite ({limite}): no se reforzó «{nombre}»; volver con el docente.")
        return None
    r = config()["refuerzo"]
    presupuesto.refuerzos += 1
    presupuesto.minutos += mt["duracion_min"]
    fuentes = [f"concepto {concepto} (definición del vocabulario)"] + list(mt.get("fuentes") or [])
    i = Intervencion(
        id=f"I{len(perfil.intervenciones) + 1}", momento=momento, objetivo=objetivo, concepto=concepto,
        motivo=motivo, recurso=mt["id"], estado_recurso=mt["estado"], fuentes=fuentes,
        duracion_min=mt["duracion_min"], criterio=f"{mt['criterio']} (actividad {mt['comprobacion']})",
        condicion_regreso=(f"criterio cumplido, {r['intentos_por_refuerzo']} intentos o {mt['duracion_min']} min "
                           f"→ volver a {objetivo.removeprefix('TEMA:')}"),
        profundidad=profundidad)
    perfil.intervenciones.append(i)
    return i
