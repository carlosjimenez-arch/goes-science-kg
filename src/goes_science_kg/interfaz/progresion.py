"""Serve the derived grade 2–11 progression artifact bound to the verified publication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock

from goes_science_kg.interfaz.consulta import normalizar
from goes_science_kg.interfaz.servicio import FuenteNoDisponible

SIN_DATOS = "No hay datos disponibles de progresión para esta publicación"
VISTAS = ("original", "propuesta")
CAMPOS_LISTADO = (
    "grados",
    "primera",
    "ultima",
    "patron",
    "max_hueco",
    "construido_en",
    "filas_por_grado",
    "grados_mencion",
    "patron_con_menciones",
)


class ProgresionCurricular:
    """Load the progression document once per file signature and reject any other snapshot."""

    def __init__(self, archivo: Path) -> None:
        self.archivo = archivo
        self._lock = Lock()
        self._firma: tuple[int, int] | None = None
        self._documento: dict | None = None

    def documento(self, snapshot_id: str) -> dict:
        """Return the progression document only when it belongs to the active snapshot."""
        with self._lock:
            try:
                estado = self.archivo.stat()
            except OSError as error:
                raise FuenteNoDisponible(SIN_DATOS) from error
            firma = (estado.st_mtime_ns, estado.st_size)
            if firma != self._firma:
                try:
                    self._documento = json.loads(self.archivo.read_text(encoding="utf-8"))
                except (OSError, ValueError) as error:
                    raise FuenteNoDisponible(SIN_DATOS) from error
                self._firma = firma
        if self._documento.get("snapshot_id") != snapshot_id:
            raise FuenteNoDisponible(SIN_DATOS)
        return self._documento

    def resumen(self, snapshot_id: str, vista: str) -> dict:
        """Return aggregate patterns, prerequisite order, transition, and grade summaries for one view."""
        doc = self.documento(snapshot_id)
        v = doc["vistas"][vista]
        prer = v["prerrequisitos"]
        nombres = {c: d["nombre"] for c, d in v["conceptos"].items()}
        orden = {"prioritaria": 0, "revisar": 1, "introduccion_cualitativa": 2}
        tardias = sorted(prer["tardias"], key=lambda t: (orden.get(t.get("clase"), 3), -t["desfase"], t["concepto"]))
        return {
            "version": doc["version"],
            "vista": vista,
            "limite": doc["limite"],
            "procedencia": doc["procedencia"],
            "acuerdo_v3": doc["acuerdo_v3"],
            "filas_etiquetadas": v["filas_etiquetadas"],
            "conceptos_presentes": v["conceptos_presentes"],
            "conceptos_vocabulario": v["conceptos_vocabulario"],
            "grados_promedio_por_concepto": v["grados_promedio_por_concepto"],
            "patrones": v["patrones"],
            "patrones_con_menciones": v.get("patrones_con_menciones", {}),
            "verificacion": self.verificacion(),
            "prerrequisitos": {
                k: prer[k] for k in ("aristas_evaluables", "ordenadas", "simultaneas", "proporcion_ordenada")
            }
            | {
                "tardias": [
                    {"nombre_prerrequisito": nombres.get(t["prerrequisito"], t["prerrequisito"])}
                    | {"nombre_concepto": nombres.get(t["concepto"], t["concepto"])}
                    | t
                    for t in tardias[:60]
                ],
                "total_tardias": len(prer["tardias"]),
                "tardias_por_clase": prer.get("tardias_por_clase", {}),
                "total_ausentes": len(prer["ausentes"]),
            },
            "aislados_por_tramo": v.get("aislados_por_tramo", {}),
            "transicion_bachillerato": v["transicion_bachillerato"],
            "grados": v["grados"],
            "practicas": {p: {k: d[k] for k in CAMPOS_LISTADO if k in d} for p, d in sorted(v["practicas"].items())},
        }

    def verificacion(self) -> dict | None:
        """Return the independent verification summary only if it was made on this exact artifact."""
        for archivo in sorted(self.archivo.parent.glob("verificacion_prioritarias_*.json"), reverse=True):
            try:
                datos = json.loads(archivo.read_text(encoding="utf-8"))
                actual = hashlib.sha256(self.archivo.read_bytes()).hexdigest()
            except (OSError, ValueError):
                continue
            if datos.get("progresion_sha256") == actual:
                return {k: datos[k] for k in ("fecha", "metodo", "limite")} | {"conteo": datos["vigente"]["conteo"]}
        return None

    def conceptos(self, snapshot_id: str, vista: str, *, disciplina=None, patron=None, q: str = "") -> list[dict]:
        """List concept trajectories filtered by discipline, pattern, or normalized text."""
        v = self.documento(snapshot_id)["vistas"][vista]
        consulta = normalizar(q)
        salida = []
        for ident, d in sorted(v["conceptos"].items(), key=lambda x: (x[1]["primera"], x[1]["nombre"])):
            if disciplina and d["asignatura"] != disciplina:
                continue
            if patron and d["patron"] != patron:
                continue
            if consulta and consulta not in normalizar(f"{d['nombre']} {ident}"):
                continue
            salida.append(
                {"id": ident, "nombre": d["nombre"], "asignatura": d["asignatura"], "nivel": d["nivel"]}
                | {k: d[k] for k in CAMPOS_LISTADO}
            )
        return salida

    def concepto(self, snapshot_id: str, vista: str, ident: str, filas: dict) -> dict:
        """Return one concept trajectory with the verified row text behind each grade."""
        v = self.documento(snapshot_id)["vistas"][vista]
        if ident not in v["conceptos"]:
            raise KeyError(ident)
        d = v["conceptos"][ident]
        por_grado = {
            g: [
                {
                    "fila_id": f,
                    "asignatura_malla": filas[f].asignatura_malla,
                    "unidad": filas[f].unidad,
                    "procedimental": filas[f].procedimental,
                }
                for f in ids
                if f in filas
            ]
            for g, ids in d["filas"].items()
        }
        return {"id": ident} | {k: valor for k, valor in d.items() if k != "filas"} | {"filas": por_grado}
