"""Build V4 context from verified spreadsheet cells without activating a graph."""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path

from goes_science_kg.config import ruta
from goes_science_kg.curriculo.contratos import Curriculo, FilaCurricular
from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.fuentes import MAX_CELDAS, FuentesVerificadas
from goes_science_kg.recuperacion import Documento, Resultado

LOGGER = logging.getLogger(__name__)
PRIORIDADES = {
    "procedimental": 0,
    "indicadores_logro": 1,
    "evidencia_aprendizaje": 1,
    "indicador_avanzado": 1,
    "fase_aproximar": 2,
    "fase_explorar": 2,
    "fase_explicar": 2,
    "fase_indagar": 2,
    "fase_reforzar": 2,
    "conocimiento_pisa": 3,
    "contexto_pisa": 3,
    "competencia_pisa": 3,
    "contenido": 4,
    "subcontenido": 4,
    "unidad": 4,
}


def catalogo_fuentes_v4(curriculo: Curriculo) -> dict[str, dict]:
    """Build source identities from ingestion while injecting authorized roots separately."""
    catalogo = {}
    for fuente in curriculo.fuentes:
        if fuente.version != curriculo.version or fuente.id in catalogo:
            raise ValueError("Las fuentes duplican identidad o mezclan versiones de currículo")
        archivo = Path(fuente.archivo)
        if archivo.name != fuente.archivo or archivo.suffix.lower() != ".xlsx":
            raise ValueError("Una fuente curricular debe identificar un nombre de archivo XLSX simple")
        catalogo[fuente.id] = {
            "archivo_local": fuente.archivo,
            "sha256": fuente.sha256,
            "bytes": fuente.bytes,
            "raiz_fuente": "v4",
            "version_curriculo": curriculo.version,
        }
    return catalogo


def fuentes_del_curriculo(
    curriculo: Curriculo,
    *,
    raiz_v4: Path,
    catalogo_historico: Mapping[str, dict] | None = None,
    raiz_historica: Path | None = None,
    raiz_cientificas: Path | None = None,
) -> FuentesVerificadas:
    """Combine explicit source permissions for V4 and optional historical material."""
    catalogo = dict(catalogo_historico or {})
    nuevas = catalogo_fuentes_v4(curriculo)
    if set(catalogo).intersection(nuevas):
        raise ValueError("Una fuente V4 no puede sustituir una fuente histórica con el mismo ID")
    catalogo.update(nuevas)
    return FuentesVerificadas(
        catalogo,
        raiz_fuentes=raiz_historica or ruta("data/fuentes"),
        raices_adicionales={
            "v4": raiz_v4,
            "referencias_cientificas_2026": raiz_cientificas or ruta("data/referencias_cientificas_2026"),
        },
    )


def documento_de_fila(fila: FilaCurricular) -> Documento:
    """Build a row locator without treating retrieval text as source evidence."""
    if not 1 <= len(fila.celdas) <= MAX_CELDAS or any(c.fila != fila.fila for c in fila.celdas):
        raise ValueError("La fila debe declarar entre una y 64 celdas de la misma fila física")
    coordenadas = [c.coordenada for c in fila.celdas]
    if len(coordenadas) != len(set(coordenadas)):
        raise ValueError("La fila contiene coordenadas duplicadas")
    texto = "\n".join(str(c.valor) for c in fila.celdas if c.valor is not None)
    return Documento(
        id=fila.id,
        texto=texto,
        fuente={"documento": fila.fuente_id, "hoja": fila.hoja, "fila": fila.fila, "celdas": coordenadas},
        version=fila.version,
        grado=fila.grado,
        asignatura=fila.asignatura_malla,
        metadata={
            "tipo": "fila_curricular",
            "campos_por_celda": {c.coordenada: c.campo for c in fila.celdas if c.campo in PRIORIDADES},
        },
    )


def contexto_celdas(
    resultados: Sequence[Resultado],
    *,
    version: str,
    fuentes: FuentesVerificadas,
    max_caracteres: int = 18000,
    max_filas: int = 3,
) -> list[Evidencia]:
    """Prioritize original objectives, assessment, phases, and context within the evidence budget."""

    # Implementation notes:
    # El presupuesto incluye el JSON completo de evidencias y procedencia. Los nombres de campo sólo
    # ordenan el contexto; los valores publicados se extraen nuevamente del snapshot, no de metadatos.
    if max_caracteres < 100 or not 1 <= max_filas <= 16:
        raise ValueError("Presupuesto de al menos 100 caracteres y entre una y 16 filas")
    candidatos: list[tuple[int, int, int, Evidencia]] = []
    filas = 0
    for posicion, resultado in enumerate(resultados):
        documento = resultado.documento
        if documento.version not in {version, "referencia"}:
            continue
        es_excel = bool(documento.fuente.get("hoja"))
        if es_excel:
            if documento.version == version:
                if filas >= max_filas:
                    continue
                filas += 1
            celdas = fuentes.hidratar_celdas(documento)
            campos = documento.metadata.get("campos_por_celda", {})
            for indice, evidencia in enumerate(celdas):
                coordenada = evidencia.fuente["celdas"][0]
                campo = campos.get(coordenada) if isinstance(campos, dict) else None
                prioridad = PRIORIDADES.get(campo, 5) if isinstance(campo, str) else 5
                candidatos.append((prioridad, posicion, indice, evidencia))
        else:
            evidencia = fuentes.hidratar(documento)
            if evidencia is not None:
                candidatos.append((3, posicion, 0, evidencia))
    candidatos.sort(key=lambda candidato: candidato[:3])

    def cabe(evidencias: list[Evidencia]) -> bool:
        return len(json.dumps([e.model_dump(mode="json") for e in evidencias], ensure_ascii=False)) <= max_caracteres

    anclaje = next((e for _, _, _, e in candidatos if e.version == version and cabe([e])), None)
    if anclaje is None:
        LOGGER.warning("AMARILLO contexto sin celda local verificable dentro del presupuesto")
        return []
    salida = [anclaje]
    vistos = {anclaje.id}
    origenes = set()
    requeridas = {r.documento.id for r in resultados if r.documento.metadata.get("obligatoria") is True}
    for _, _, _, evidencia in candidatos:
        if evidencia.id in requeridas and evidencia.id not in vistos and cabe(salida + [evidencia]):
            salida.append(evidencia)
            vistos.add(evidencia.id)

    def origen(evidencia: Evidencia) -> tuple:
        celda = evidencia.fuente.get("celdas_verificadas", [{}])[0]
        return (
            evidencia.fuente["documento"],
            evidencia.fuente.get("hoja"),
            celda.get("coordenada_origen"),
            evidencia.fuente.get("pagina"),
            evidencia.fuente["sha256"],
        )

    origenes.add(origen(anclaje))
    origenes.update(origen(e) for e in salida)
    for _, _, _, evidencia in candidatos:
        identidad_origen = origen(evidencia)
        if evidencia.id in vistos or identidad_origen in origenes:
            continue
        if cabe(salida + [evidencia]):
            salida.append(evidencia)
            vistos.add(evidencia.id)
            origenes.add(identidad_origen)
    return salida
