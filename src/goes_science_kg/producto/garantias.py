"""Bloqueos localizados para errores científicos ya documentados en las fuentes."""

from __future__ import annotations

import json
import unicodedata
from pathlib import Path

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.recuperacion import Documento


def _normalizar(texto: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(texto)).split()).casefold()


def bloqueos_cientificos(curriculo: Curriculo, fuentes: FuentesVerificadas, archivo: Path) -> dict[str, str]:
    """Revalida el localizador de la alerta; no vuelve a certificar su contraste científico.

    El archivo de alertas es configuración de confianza del repositorio. Una alerta ajena a la
    edición actual se rechaza. Se conservan los originales; los bloqueos se aplican a generación.
    """
    documento = json.loads(archivo.read_text(encoding="utf-8"))
    por_archivo = {f.archivo: f for f in curriculo.fuentes}
    bloqueos: dict[str, list[str]] = {}
    for alerta in documento["alertas"]:
        if alerta.get("clase") != "error_cientifico" or alerta.get("estado_verificacion") != "confirmada":
            continue
        ancla = alerta.get("ancla_original")
        if not isinstance(ancla, str) or not _normalizar(ancla):
            raise ValueError("Una alerta científica confirmada requiere un ancla original no vacía")
        localizador = alerta["fuente"]
        fuente = por_archivo[Path(localizador["archivo"]).name]
        if fuente.sha256 != localizador["sha256"]:
            raise ValueError("La alerta científica pertenece a otra edición de la fuente")
        celdas = localizador["celdas"]
        evidencias = fuentes.hidratar_celdas(
            Documento(
                id=alerta["id"],
                texto="El texto se rehidrata desde el archivo original",
                version=curriculo.version,
                fuente={"documento": fuente.id, "hoja": localizador["hoja"], "celdas": celdas},
            )
        )
        if len(evidencias) != len(celdas) or any(_normalizar(ancla) not in _normalizar(e.texto) for e in evidencias):
            raise ValueError("El ancla de una alerta científica no coincide con las celdas originales")
        # Una coordenada secundaria combinada comparte valor con todas las filas que leen su ancla.
        origenes = set(celdas) | {
            celda["coordenada_origen"]
            for evidencia in evidencias
            for celda in evidencia.fuente["celdas_verificadas"]
            if isinstance(celda.get("coordenada_origen"), str)
        }
        afectadas = set()
        for fila in curriculo.filas:
            if fila.fuente_id != fuente.id or fila.hoja != localizador["hoja"]:
                continue
            if any(c.coordenada in origenes or c.origen_combinado in origenes for c in fila.celdas):
                afectadas.add(fila.id)
        if not afectadas:
            raise ValueError("Una alerta científica no tiene filas curriculares localizadas")
        for fila_id in afectadas:
            bloqueos.setdefault(fila_id, []).append(f"{alerta['id']}: {alerta['explicacion']}")
    return {id_: " | ".join(motivos) for id_, motivos in bloqueos.items()}
