"""Tramo de grados del estudio internacional: 9.°–11.° (spec 11) o 2.°–8.° (spec 12).

El método es el mismo; cambian los grados, el catálogo de documentos y las carpetas. El tramo activo se elige con
`usar()` (la CLI lo hace con --tramo) o con la variable GSKG_TRAMO; por defecto, 9_11, con las rutas de siempre.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Tramo:
    clave: str
    grados: tuple[int, ...]
    config: str          # config/<config>.yaml: países y documentos
    objetivos: str       # objetivos extraídos por país
    etiquetado: str      # etiquetado de los objetivos de los países (pais_*.json)
    grafo: str           # grafo por país y consenso
    informe: str         # informes, Excel, visor y CSV de revisión
    revisiones: str      # clases corregidas en revisión experta
    spec: str            # especificación del método

    @property
    def etiqueta(self) -> str:
        return f"{self.grados[0]}.°–{self.grados[-1]}.°"

    @property
    def rango(self) -> str:
        """«9-11»: para encabezados de Excel (sin caracteres especiales)."""
        return f"{self.grados[0]}-{self.grados[-1]}"

    def contiene(self, g0: float, g1: float | None = None) -> bool:
        """Si el rango [g0, g1] de grados SV toca el tramo."""
        return g0 <= self.grados[-1] and (g1 if g1 is not None else g0) >= self.grados[0]


TRAMOS = {
    "9_11": Tramo("9_11", (9, 10, 11), "internacional", "data/interim/internacional/objetivos",
                  "data/interim/internacional/etiquetado", "data/grafo/internacional", "internacional",
                  "data/interim/internacional/revisiones.json", "specs/11_grafos_internacionales_9_11.md"),
    "2_8": Tramo("2_8", (2, 3, 4, 5, 6, 7, 8), "internacional_2_8", "data/interim/internacional_2_8/objetivos",
                 "data/interim/internacional_2_8/etiquetado", "data/grafo/internacional_2_8", "internacional/2_8",
                 "data/interim/internacional_2_8/revisiones.json", "specs/12_grafos_internacionales_2_8.md"),
}
# El etiquetado de la malla V2 (2.°–11.°) y el catálogo congelado son comunes a los dos tramos.
ETIQUETADO_COMUN = "data/interim/internacional/etiquetado"

_activo: str | None = None


def usar(clave: str) -> Tramo:
    """Fija el tramo activo del proceso."""
    global _activo   # noqa: PLW0603 — estado de proceso, como el directorio de trabajo
    if clave not in TRAMOS:
        raise ValueError(f"Tramo desconocido {clave!r}; opciones: {', '.join(TRAMOS)}")
    _activo = clave
    return TRAMOS[clave]


def actual() -> Tramo:
    """Tramo activo: el fijado con usar(), si no GSKG_TRAMO, si no 9_11."""
    return TRAMOS[_activo or os.environ.get("GSKG_TRAMO", "9_11")]
