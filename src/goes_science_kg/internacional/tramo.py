"""Select the explicit grade band for the historical international study."""

# Historical implementation notes:
# El método es el mismo; cambian los grados, el catálogo de documentos y las carpetas. El tramo activo se elige con
# `usar()` (la CLI lo hace con --tramo) o con la variable GSKG_TRAMO; por defecto, 9_11, con las rutas de siempre.

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Tramo:
    """Configure one historical international-study band and its artifact locations."""

    clave: str
    grados: tuple[int, ...]
    config: str  # config/<config>.yaml: países y documentos
    objetivos: str  # objetivos extraídos por país
    etiquetado: str  # etiquetado de los objetivos de los países (pais_*.json)
    grafo: str  # grafo por país y consenso
    informe: str  # informes, Excel, visor y CSV de revisión
    revisiones: str  # clases corregidas en revisión experta
    spec: str  # especificación del método
    # Doble lectura (spec 12, método v2): una clase solo se afirma si sale igual con la lectura más amplia y con la más
    # estricta de la presencia en la V2 y en los países; si no, queda «incierta» y va a revisión.
    lectura_doble: bool = False

    @property
    def etiqueta(self) -> str:
        """Return the human-readable label for the selected grade band."""

        return f"{self.grados[0]}.°–{self.grados[-1]}.°"

    @property
    def rango(self) -> str:
        """Format the active grade range for interoperable Excel headers."""
        return f"{self.grados[0]}-{self.grados[-1]}"

    def contiene(self, g0: float, g1: float | None = None) -> bool:
        """Check whether a configured local grade interval intersects the active band."""
        return g0 <= self.grados[-1] and (g1 if g1 is not None else g0) >= self.grados[0]


TRAMOS = {
    "9_11": Tramo(
        "9_11",
        (9, 10, 11),
        "internacional",
        "data/interim/internacional/objetivos",
        "data/interim/internacional/etiquetado",
        "data/grafo/internacional",
        "internacional",
        "data/interim/internacional/revisiones.json",
        "specs/11_grafos_internacionales_9_11.md",
        lectura_doble=True,
    ),  # desde el 2026-10-13: núcleo parcial y ausencias verificadas en el texto
    "2_8": Tramo(
        "2_8",
        (2, 3, 4, 5, 6, 7, 8),
        "internacional_2_8",
        "data/interim/internacional_2_8/objetivos",
        "data/interim/internacional_2_8/etiquetado",
        "data/grafo/internacional_2_8",
        "internacional/2_8",
        "data/interim/internacional_2_8/revisiones.json",
        "specs/12_grafos_internacionales_2_8.md",
        lectura_doble=True,
    ),
}
# El etiquetado de la malla V2 (2.°–11.°) y el catálogo congelado son comunes a los dos tramos.
ETIQUETADO_COMUN = "data/interim/internacional/etiquetado"

_activo: str | None = None


def usar(clave: str) -> Tramo:
    """Set the process's explicit international-study grade band."""
    global _activo  # noqa: PLW0603 — estado de proceso, como el directorio de trabajo
    if clave not in TRAMOS:
        raise ValueError(f"Tramo desconocido {clave!r}; opciones: {', '.join(TRAMOS)}")
    _activo = clave
    return TRAMOS[clave]


def actual() -> Tramo:
    """Resolve the active band from explicit selection, environment, or default."""
    return TRAMOS[_activo or os.environ.get("GSKG_TRAMO", "9_11")]
