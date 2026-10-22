"""Track individual learning evidence by concept and curriculum objective."""

# Historical implementation notes:
# El estado se estima con un rastreo bayesiano simplificado (BKT): cada respuesta es una observación ruidosa
# (desliz, acierto al azar) que actualiza la probabilidad de dominio SOLO de lo que la actividad evalúa. Las bases
# relacionadas no cambian por una respuesta: para ellas se abren hipótesis que hay que comprobar (diagnostico.py).
#
# El almacén vive fuera de las capas compartidas y se niega a escribir dentro de ellas: la evidencia de un estudiante
# nunca altera el conocimiento compartido.

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path

from goes_science_kg.config import cargar, ruta

ESTADOS = ("sin_evidencia", "en_progreso", "brecha", "logrado_provisional", "dominado")


def config() -> dict:
    """Load learner-state and spaced-review configuration."""

    return cargar("aprendizaje")


@dataclass
class Estado:
    """Track one learner's state for a concept or curriculum objective."""

    id: str
    p: float  # probabilidad estimada de dominio
    previa: str  # de dónde salió la probabilidad inicial
    estado: str = "sin_evidencia"
    evidencias: list[str] = field(default_factory=list)


@dataclass
class Evidencia:
    """Record one activity response and the specific skills it assesses."""

    id: str
    fecha: str
    actividad: str
    objetivo: str  # objetivo curricular (TEMA) en cuyo contexto se respondió
    evalua: list[str]
    respuesta: str
    correcta: bool
    dificultad: str | None = None  # la dificultad que delata el distractor elegido, si alguna


@dataclass
class Hipotesis:
    """Represent a possible learning gap that requires diagnostic verification."""

    id: str
    objetivo: str
    concepto: str
    tipo: str  # base | en_el_concepto (el evaluado)
    motivo: str  # evidencia que la abrió
    puntaje: float
    estado: str = "abierta"  # abierta | confirmada | descartada | sin_comprobar
    evidencias: list[str] = field(default_factory=list)


@dataclass
class Intervencion:
    """Record a bounded intervention with its objective, rationale, resources, and evidence."""

    # Implementation notes:
    # cuánto dura, cómo se comprueba y cuándo se vuelve.

    id: str
    momento: str  # previo | durante | posterior
    objetivo: str
    concepto: str
    motivo: str  # evidencia o regla que lo disparó
    recurso: str  # microtema (o actividad) de la capa pedagógica
    estado_recurso: str  # propuesta_pendiente | verificado
    fuentes: list[str]
    duracion_min: int
    criterio: str
    condicion_regreso: str
    profundidad: int = 0
    resultado: str = "pendiente"  # cumplido | no_cumplido | limite | pendiente
    intentos: int = 0


@dataclass
class Repaso:
    """Schedule an objective review for an explicit date and interval."""

    objetivo: str
    fecha: str
    intervalo: int


@dataclass
class Perfil:
    """Store one learner's evidence, hypotheses, interventions, and review schedule."""

    id: str
    grado: int
    conceptos: dict[str, Estado] = field(default_factory=dict)
    objetivos: dict[str, Estado] = field(default_factory=dict)
    evidencias: list[Evidencia] = field(default_factory=list)
    hipotesis: list[Hipotesis] = field(default_factory=list)
    intervenciones: list[Intervencion] = field(default_factory=list)
    repasos: list[Repaso] = field(default_factory=list)

    # -- probabilidad inicial ----------------------------------------------------------------------------------------
    def estado_de(self, cid: str, previa: tuple[float, str]) -> Estado:
        """Get a learning state or create it with the supplied prior probability."""
        tabla = self.objetivos if cid.startswith("TEMA:") else self.conceptos
        if cid not in tabla:
            tabla[cid] = Estado(cid, previa[0], previa[1])
        return tabla[cid]

    # -- actualización con evidencia ---------------------------------------------------------------------------------
    def observar(self, ev: Evidencia, formato: str, previas: dict[str, tuple[float, str]]) -> None:
        """Update only the skills assessed by the activity using Bayesian knowledge tracing."""
        cfg = config()["dominio"]
        s, g = cfg["desliz"], cfg["acierto_azar"].get(formato, cfg["acierto_azar"]["abierta"])
        self.evidencias.append(ev)
        for cid in ev.evalua:
            e = self.estado_de(cid, previas[cid])
            p = e.p
            e.p = (p * (1 - s)) / (p * (1 - s) + (1 - p) * g) if ev.correcta else (p * s) / (p * s + (1 - p) * (1 - g))
            e.evidencias.append(ev.id)
            e.estado = clasificar(e)

    def aprendio(self, cid: str) -> None:
        """Apply the learning transition after a completed reinforcement activity."""
        t = config()["dominio"]["aprendizaje_tras_refuerzo"]
        for tabla in (self.conceptos, self.objetivos):
            if cid in tabla:
                tabla[cid].p += (1 - tabla[cid].p) * t
                tabla[cid].estado = clasificar(tabla[cid])

    def programar_repasos(self, objetivo: str, desde: date) -> list[Repaso]:
        """Replace pending reviews with the configured spaced-repetition schedule."""
        self.repasos = [r for r in self.repasos if r.objetivo != objetivo]
        nuevos = [
            Repaso(objetivo, (desde + timedelta(days=d)).isoformat(), d) for d in config()["repaso"]["intervalos_dias"]
        ]
        self.repasos += nuevos
        return nuevos


def clasificar(e: Estado) -> str:
    """Classify a learning state under the configured mastery thresholds."""

    cfg = config()["dominio"]
    if not e.evidencias:
        return "sin_evidencia"
    if e.p >= cfg["umbral_dominio"]:
        return "dominado"
    if e.p < cfg["umbral_brecha"] and len(e.evidencias) >= config()["diagnostico"]["evidencias_para_confirmar"]:
        return "brecha"
    return "en_progreso"


# -- almacén --------------------------------------------------------------------------------------------------------
class Almacen:
    """Store individual learner profiles outside shared curriculum layers."""

    def __init__(self, directorio: Path | None = None):
        self.dir = Path(directorio) if directorio else ruta(config()["rutas"]["estudiantes"])
        compartidas = [ruta("data/grafo"), ruta(config()["rutas"]["pedagogia"]), ruta("data/fuentes")]
        destino = self.dir.resolve()
        if any(destino == c.resolve() or c.resolve() in destino.parents for c in compartidas):
            raise ValueError(f"El estado individual no puede guardarse en una capa compartida: {self.dir}")

    def guardar(self, perfil: Perfil) -> Path:
        """Persist one learner profile outside shared curriculum layers."""

        self.dir.mkdir(parents=True, exist_ok=True)
        p = self.dir / f"{perfil.id}.json"
        p.write_text(json.dumps(asdict(perfil), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        return p

    def cargar(self, estudiante: str) -> Perfil | None:
        """Load a learner profile or initialize a new grade-specific profile."""

        p = self.dir / f"{estudiante}.json"
        if not p.exists():
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
        return Perfil(
            d["id"],
            d["grado"],
            {k: Estado(**v) for k, v in d["conceptos"].items()},
            {k: Estado(**v) for k, v in d["objetivos"].items()},
            [Evidencia(**x) for x in d["evidencias"]],
            [Hipotesis(**x) for x in d["hipotesis"]],
            [Intervencion(**x) for x in d["intervenciones"]],
            [Repaso(**x) for x in d["repasos"]],
        )
