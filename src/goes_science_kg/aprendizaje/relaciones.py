"""Relaciones con significado explícito y su inversa, y el navegador bidireccional (spec 13, «Bidireccionalidad A»).

Cada relación se GUARDA una sola vez, en su sentido canónico, y su inversa se CONSULTA con un índice inverso
construido de la misma arista. Así las dos lecturas nunca se contradicen: «A es_prerrequisito_de B» y
«B requiere A» son la misma arista leída desde cada extremo. No se materializa la inversa porque ninguna relación
tiene datos propios de un solo sentido; si alguna los tuviera (p. ej. una evidencia distinta para cada dirección),
pasaría a ser dos relaciones distintas, no una arista duplicada. Solo `equivale_a` es simétrica.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from goes_science_kg.modelos import Arista, Nodo, TipoArista
from goes_science_kg.prerrequisitos import evidencia_orden


@dataclass(frozen=True)
class Relacion:
    nombre: str          # sentido canónico (el que se guarda)
    inversa: str         # cómo se lee desde el destino
    origen: str          # tipo de nodo del origen
    destino: str         # tipo de nodo del destino
    capa: str            # curricular | cientifica | pedagogica
    guardada_en: str     # dónde vive la arista
    simetrica: bool = False
    significado: str = ""


RELACIONES = {r.nombre: r for r in (
    Relacion("es_prerrequisito_de", "requiere", "Concepto", "Concepto", "pedagogica",
             "data/grafo (PRERREQUISITO_DE)", significado="sin comprender el origen no se construye el destino; "
             "inferida por IA con justificación y confianza, pendiente de revisión humana"),
    Relacion("trabaja", "es_trabajado_en", "Tema", "Concepto", "curricular", "data/grafo (TRABAJA)",
             significado="el tema de la malla enseña el concepto (rol principal o secundario)"),
    Relacion("equivale_a", "equivale_a", "Concepto", "Concepto", "cientifica", "data/grafo (EQUIVALE_A)",
             simetrica=True, significado="el mismo concepto nombrado en dos asignaturas"),
    Relacion("evalua", "es_evaluado_por", "Actividad", "Concepto|Tema", "pedagogica", "data/pedagogia/actividades",
             significado="la actividad aporta evidencia sobre el concepto o el objetivo"),
    Relacion("sirve_a", "se_apoya_en", "Actividad", "Tema", "pedagogica", "data/pedagogia/actividades",
             significado="la actividad se escribió para ese objetivo curricular"),
    Relacion("refuerza", "es_reforzado_por", "Microtema", "Concepto", "pedagogica", "data/pedagogia/microtemas",
             significado="el microtema trabaja el concepto a la profundidad de un grado"),
    Relacion("es_dificultad_de", "tiene_dificultad", "Dificultad", "Concepto", "pedagogica",
             "data/pedagogia/dificultades", significado="dificultad frecuente al aprender el concepto"),
    Relacion("detecta", "es_detectada_por", "Actividad", "Dificultad", "pedagogica", "data/pedagogia/actividades",
             significado="un distractor de la actividad es la respuesta típica de esa dificultad"),
)}
CONFIANZA_ORDEN = {"baja": 0, "media": 1, "alta": 2}


def orden_tema(tema: str) -> tuple:
    """Posición de un tema en la malla: (grado, asignatura de la malla, unidad, código del procedimental)."""
    m = re.match(r"TEMA:G(\d+)-(\w+)-U(\d+)-([\d.]+)", tema)
    if not m:
        return (99, "", 0, ())
    return (int(m.group(1)), m.group(2), int(m.group(3)), tuple(int(x) for x in m.group(4).split(".") if x))


def antes_en_la_malla(tema_a: str, tema_b: str) -> bool:
    """Si la malla enseña `tema_a` antes que `tema_b`: un grado anterior, o el mismo grado y la misma asignatura de
    la malla con una unidad o un código anterior. Asignaturas distintas del mismo grado van en paralelo: no cuenta."""
    a, b = orden_tema(tema_a), orden_tema(tema_b)
    return a[0] < b[0] or (a[0] == b[0] and a[1] == b[1] and a[2:] < b[2:])


def confianza(a: Arista) -> str:
    """Confianza de una arista inferida («baja» si no la declara)."""
    return a.confianza.value if a.confianza else "baja"


@dataclass(frozen=True)
class Base:
    """Un concepto que el objetivo necesita: a qué profundidad, por qué camino y con qué respaldo."""

    concepto: str
    profundidad: int                 # 1 = prerrequisito directo de un concepto del objetivo
    via: tuple[str, ...]             # cadena de conceptos desde el objetivo
    confianza: str
    justificacion: str
    primer_grado_sv: float | None    # primer grado en que la malla lo trabaja (None: no lo trabaja)
    primer_tema: str | None          # primer tema que lo trabaja (principal, o secundario con confianza alta o media)
    antes_del_objetivo: bool         # la malla lo enseña antes que el objetivo (orden de la malla)
    estado_relacion: str             # «propuesta_ia_pendiente» o «revisada»


@dataclass
class Navegador:
    """Recorre el grafo en los dos sentidos. Lee el grafo compartido; nunca lo modifica."""

    nodos: list[Nodo]
    aristas: list[Arista]
    por_id: dict[str, Nodo] = field(init=False)

    def __post_init__(self) -> None:
        self.por_id = {n.id: n for n in self.nodos}
        self._salientes: dict[tuple[str, TipoArista], list[Arista]] = defaultdict(list)
        self._entrantes: dict[tuple[str, TipoArista], list[Arista]] = defaultdict(list)
        for a in self.aristas:
            self._salientes[(a.origen, a.tipo)].append(a)
            self._entrantes[(a.destino, a.tipo)].append(a)
        self._ev = evidencia_orden(self.nodos, self.aristas)

    # -- relaciones básicas en los dos sentidos ----------------------------------------------------------------
    def requiere(self, concepto: str, minima: str = "media") -> list[Arista]:
        """«¿Qué necesita?»: aristas PRERREQUISITO_DE que llegan al concepto (leídas como «requiere»)."""
        return sorted((a for a in self._entrantes[(concepto, TipoArista.PRERREQUISITO_DE)]
                       if CONFIANZA_ORDEN[confianza(a)] >= CONFIANZA_ORDEN[minima]),
                      key=lambda a: (-CONFIANZA_ORDEN[confianza(a)], a.origen))

    def es_prerrequisito_de(self, concepto: str, minima: str = "media") -> list[Arista]:
        """«¿A qué ayuda?»: las mismas aristas leídas desde el origen."""
        return sorted((a for a in self._salientes[(concepto, TipoArista.PRERREQUISITO_DE)]
                       if CONFIANZA_ORDEN[confianza(a)] >= CONFIANZA_ORDEN[minima]),
                      key=lambda a: (-CONFIANZA_ORDEN[confianza(a)], a.destino))

    def equivalentes(self, concepto: str) -> set[str]:
        """El concepto y sus equivalentes en otras asignaturas (relación simétrica: se lee en ambos sentidos)."""
        return ({concepto} | {a.destino for a in self._salientes[(concepto, TipoArista.EQUIVALE_A)]}
                | {a.origen for a in self._entrantes[(concepto, TipoArista.EQUIVALE_A)]})

    def conceptos_de_tema(self, tema: str, roles: tuple[str, ...] = ("principal", "secundario")) -> list[str]:
        """Conceptos que trabaja un tema (objetivo curricular), el principal primero."""
        orden = {r: i for i, r in enumerate(roles)}
        aristas = [a for a in self._salientes[(tema, TipoArista.TRABAJA)]
                   if a.destino.startswith("CON:") and a.rol in orden]
        return [a.destino for a in sorted(aristas, key=lambda a: (orden[a.rol or ""], a.destino))]

    def temas_de_concepto(self, concepto: str, rol: str = "principal") -> list[Nodo]:
        """Inversa de `trabaja`: los temas de la malla donde se enseña el concepto (en cualquier grado)."""
        temas = {a.origen for c in self.equivalentes(concepto) for a in self._entrantes[(c, TipoArista.TRABAJA)]
                 if a.origen.startswith("TEMA:") and a.rol == rol}
        return sorted((self.por_id[t] for t in temas), key=lambda n: (n.grado or 0, n.id))

    def primer_tema(self, concepto: str) -> str | None:
        """Primer tema de la malla que trabaja el concepto o un equivalente (principal, o secundario con confianza
        alta o media; la misma regla que el primer grado en prerrequisitos.evidencia_orden)."""
        temas = [a.origen for c in self.equivalentes(concepto) for a in self._entrantes[(c, TipoArista.TRABAJA)]
                 if a.origen.startswith("TEMA:") and (a.rol == "principal" or confianza(a) in ("alta", "media"))]
        return min(temas, key=orden_tema, default=None)

    def primer_grado_sv(self, concepto: str) -> float | None:
        """Primer grado en que la malla trabaja el concepto (regla de prerrequisitos.evidencia_orden)."""
        return self._ev.get(concepto, {}).get("sv")

    # -- recorridos ---------------------------------------------------------------------------------------------
    def bases(self, tema: str, profundidad: int = 2, minima: str = "media") -> list[Base]:
        """Desde un objetivo hacia sus bases: conceptos que necesita, hasta `profundidad` saltos de prerrequisito.

        Cada base dice si la malla la enseña antes del grado del objetivo: si no, el hueco es de la secuencia de la
        malla y no del estudiante (se ofrece una activación previa, no un diagnóstico de déficit). Solo el concepto
        principal es «el objetivo»: un secundario del mismo tema que el principal requiere sigue siendo una base."""
        vistos, salida = set(self.conceptos_de_tema(tema, ("principal",))), []
        frontera = [(c, (c,)) for c in self.conceptos_de_tema(tema, ("principal",))]
        for nivel in range(1, profundidad + 1):
            siguiente = []
            for c, via in frontera:
                for a in self.requiere(c, minima):
                    if a.origen in vistos:
                        continue
                    vistos.add(a.origen)
                    primero = self.primer_tema(a.origen)
                    salida.append(Base(a.origen, nivel, via, confianza(a), a.justificacion or "",
                                       self.primer_grado_sv(a.origen), primero,
                                       primero is not None and antes_en_la_malla(primero, tema),
                                       "revisada" if a.props.get("revisado_por") else "propuesta_ia_pendiente"))
                    siguiente.append((a.origen, (*via, a.origen)))
            frontera = siguiente
        return salida

    def apoya(self, concepto: str, grado: int | None = None, profundidad: int = 2, alcance: int = 2) -> list[dict]:
        """Desde una base hacia lo que apoya: «¿dónde ayudará reforzar esto?». Recorre `es_prerrequisito_de` y
        devuelve los temas que trabajan (como principal) el concepto o los que dependen de él, entre `grado` y
        `grado + alcance` si se da un grado."""
        dependientes, frontera = {concepto: 0}, [concepto]
        for nivel in range(1, profundidad + 1):
            siguiente = []
            for c in frontera:
                for a in self.es_prerrequisito_de(c):
                    if a.destino not in dependientes:
                        dependientes[a.destino] = nivel
                        siguiente.append(a.destino)
            frontera = siguiente
        filas = []
        for c, nivel in dependientes.items():
            for t in self.temas_de_concepto(c):
                if grado is None or grado <= (t.grado or 0) <= grado + alcance:
                    filas.append({"tema": t.id, "grado": t.grado, "tema_texto": t.etiqueta, "concepto": c,
                                  "concepto_nombre": self.por_id[c].etiqueta, "distancia": nivel})
        return sorted(filas, key=lambda f: (f["distancia"], f["grado"] or 0, f["tema"]))
