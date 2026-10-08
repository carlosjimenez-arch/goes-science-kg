"""Extrae cada TEMA (fila con «Procedimental») de las mallas del MINED.

Migrado de reportes/cobertura_curricular/scripts/extract_temas.py con dos cambios:
- El archivo de cada malla se fija en config/mallas.yaml (no se elige por fecha de modificación).
- El id del tema es estable: grado + asignatura + unidad + código del procedimental
  (p. ej. «G07-CIE-U2-2.3»), no la posición de lectura.

Hojas de unidad: las que empiezan con «Unidad» (2.°–9.°) o contienen «N.°» (Bachillerato).
Nunca se modifican los archivos de origen.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from functools import cache
from typing import TYPE_CHECKING

import openpyxl

from goes_science_kg.config import cargar, ruta

if TYPE_CHECKING:
    from openpyxl.worksheet._read_only import ReadOnlyWorksheet

CODIGO_ASIG = {"ciencias": "CIE", "fisica": "FIS", "quimica": "QUI", "biologia": "BIO"}


@dataclass
class TemaMalla:
    """Un tema: una fila con «Procedimental» de una malla, con su ubicación (archivo, hoja, fila) y sus columnas."""

    id: str
    archivo: str          # nombre canónico (sin «(1)»): es la llave de las clasificaciones previas
    ruta: str             # archivo realmente leído
    hoja: str
    fila: int
    grado: int
    asignatura: str       # ciencias | fisica | quimica | biologia (asignatura de la MALLA)
    unidad: str
    contenido: str
    subcontenido: str
    procedimental: str
    indicador: str
    evidencia: str
    habilidad_timss: str
    competencia_pisa: str
    micro_pisa: dict[str, list[str]] = field(default_factory=dict)

    def dict(self) -> dict:
        """Los campos del tema como diccionario."""
        return asdict(self)


def _limpio(v: object) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def _num(texto: str, patron: str) -> str | None:
    m = re.match(patron, texto or "")
    return m.group(1) if m else None


def _columnas(ws: ReadOnlyWorksheet) -> list[str]:
    h1 = [c.value or "" for c in ws[1]]
    h2 = [c.value or "" for c in ws[2]]
    cols = [(str(a) or str(b)).split("\n")[0].strip() for a, b in zip(h1, h2, strict=False)]
    for i, s in enumerate(h2):
        if s:
            cols[i] = str(s).split("\n")[0].strip()
    return cols


@cache
def extraer(nombre_config: str = "mallas") -> tuple[TemaMalla, ...]:
    """Lee las mallas que fija config/<nombre_config>.yaml (por defecto la Versión 1).

    Con caché: leer los Excel es lo más lento del proceso y varios pasos piden la misma malla en una corrida.
    """
    cfg = cargar(nombre_config)
    base = ruta(cfg["directorio"])
    fases = cfg["fases_pisa"]
    temas: list[TemaMalla] = []
    for item in cfg["archivos"]:
        archivo = item["archivo"]
        canonico = item.get("canonico", archivo)
        asig = item["asignatura"]
        wb = openpyxl.load_workbook(base / archivo, data_only=True, read_only=True)
        for ws in wb.worksheets:
            if not (ws.title.startswith("Unidad") or re.search(r"\d+\.°", ws.title)):
                continue
            grado = item.get("grado") or int(re.search(r"(\d+)\.°", ws.title).group(1))
            cols = _columnas(ws)
            unidad = contenido = ""
            for fila, row in enumerate(ws.iter_rows(min_row=cfg["fila_datos"], values_only=True),
                                       start=cfg["fila_datos"]):
                d = dict(zip(cols, row, strict=False))
                if d.get("Unidad"):
                    unidad = _limpio(d["Unidad"])
                if d.get("Contenido"):
                    contenido = _limpio(d["Contenido"])
                if not d.get("Procedimental"):
                    continue
                proc = _limpio(d["Procedimental"])
                temas.append(TemaMalla(
                    id="", archivo=canonico, ruta=archivo, hoja=ws.title, fila=fila, grado=grado,
                    asignatura=asig, unidad=unidad, contenido=contenido,
                    subcontenido=_limpio(d.get("Subcontenidos")), procedimental=proc,
                    indicador=_limpio(d.get("Indicadores de logro") or d.get("Indicador avanzado")),
                    evidencia=_limpio(d.get("Evidencia de aprendizaje")),
                    habilidad_timss=_limpio(d.get("Habilidad TIMSS")),
                    competencia_pisa=_limpio(d.get("Competencia PISA 2025")),
                    micro_pisa={f: re.findall(r"\b([EDI]\d)\s*·", str(d.get(f) or "")) for f in fases},
                ))
        wb.close()
    _asignar_ids(temas)
    return tuple(temas)


def _asignar_ids(temas: list[TemaMalla]) -> None:
    """G{grado}-{ASIG}-U{unidad}-{código}; si el código se repite, se agrega la fila."""
    base: dict[str, list[TemaMalla]] = {}
    for t in temas:
        u = _num(t.unidad, r"\s*(\d+)") or _num(t.hoja, r"\D*(\d+)") or "0"
        c = _num(t.procedimental, r"\s*(\d+(?:\.\d+)+)") or f"f{t.fila}"
        base.setdefault(f"G{t.grado:02d}-{CODIGO_ASIG[t.asignatura]}-U{u}-{c}", []).append(t)
    for clave, grupo in base.items():
        for t in grupo:
            t.id = clave if len(grupo) == 1 else f"{clave}-f{t.fila}"
