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
        self._cargado: tuple[dict, str] | None = None

    def _cargar(self) -> tuple[dict, str]:
        """Return the cached document and the SHA-256 of the exact bytes it was parsed from."""
        with self._lock:
            try:
                estado = self.archivo.stat()
                firma = (estado.st_mtime_ns, estado.st_size)
                if firma != self._firma or self._cargado is None:
                    raw = self.archivo.read_bytes()
                    documento = json.loads(raw)
                    if not isinstance(documento, dict):
                        raise ValueError("Documento de progresión inválido")
                    self._cargado, self._firma = (documento, hashlib.sha256(raw).hexdigest()), firma
            except (OSError, ValueError) as error:
                raise FuenteNoDisponible(SIN_DATOS) from error
            return self._cargado

    def documento(self, snapshot_id: str) -> dict:
        """Return the progression document only when it belongs to the active snapshot."""
        documento, _ = self._cargar()
        if documento.get("snapshot_id") != snapshot_id:
            raise FuenteNoDisponible(SIN_DATOS)
        return documento

    def resumen(self, snapshot_id: str, vista: str) -> dict:
        """Return aggregate patterns, prerequisite order, transition, and grade summaries for one view."""
        doc, sha = self._cargar()
        if doc.get("snapshot_id") != snapshot_id:
            raise FuenteNoDisponible(SIN_DATOS)
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
            "verificacion": self.verificacion(sha),
            "prerrequisitos_solo_etiquetas": v.get("prerrequisitos_solo_etiquetas"),
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

    def verificacion(self, sha: str) -> dict | None:
        """Return the independent verification summary only if it was made on the bytes being served."""
        for archivo in sorted(self.archivo.parent.glob("verificacion_prioritarias_*.json"), reverse=True):
            try:
                datos = json.loads(archivo.read_text(encoding="utf-8"))
                if datos.get("progresion_sha256") == sha:
                    return {k: datos[k] for k in ("fecha", "metodo", "limite")} | {"conteo": datos["vigente"]["conteo"]}
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                continue
        return None

    def conceptos(self, snapshot_id: str, vista: str, *, disciplina=None, patron=None, q: str = "") -> list[dict]:
        """List concept trajectories filtered by discipline, pattern, or normalized text."""
        v = self.documento(snapshot_id)["vistas"][vista]
        consulta = normalizar(q)
        salida = []
        for ident, d in sorted(v["conceptos"].items(), key=lambda x: (x[1]["primera"], x[1]["nombre"])):
            if disciplina and disciplina not in (d.get("asignaturas") or [d["asignatura"]]):
                continue
            if patron and d["patron"] != patron:
                continue
            if consulta and consulta not in normalizar(f"{d['nombre']} {ident}"):
                continue
            salida.append(
                {"id": ident, "nombre": d["nombre"], "asignatura": d["asignatura"], "nivel": d["nivel"]}
                | {"asignaturas": d.get("asignaturas") or [d["asignatura"]]}
                | {k: d[k] for k in CAMPOS_LISTADO}
            )
        return salida

    def concepto(self, snapshot_id: str, vista: str, ident: str, filas: dict, objetivo=None) -> dict:
        """Return one concept trajectory with the verified row text behind each grade.

        `objetivo(fila_id)` may supply the proposal's refined objective for the proposals view.
        """
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
                    "objetivo_propuesto": objetivo(f) if objetivo else None,
                }
                for f in ids
                if f in filas
            ]
            for g, ids in d["filas"].items()
        }
        return {"id": ident} | {k: valor for k, valor in d.items() if k != "filas"} | {"filas": por_grado}
