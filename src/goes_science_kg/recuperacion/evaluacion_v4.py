"""Adapt V4 source locators and evaluate the frozen baseline offline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.recuperacion.evaluacion_agentic import (
    ConsultaEvaluacion,
    ObjetivoRelevante,
)


def _huella(datos) -> str:
    return hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def preparar_conjunto_v4(datos: dict, curriculo: Curriculo) -> dict:
    """Transcribe all declared V4 cells without interpreting private judgments or tuning queries."""

    # Implementation notes:
    # Sólo consulta id, consulta, grado, asignatura, fuente y referencias_adicionales. Los archivos son
    # identidades del currículo ingerido; este adaptador no abre rutas proporcionadas por el dataset.
    if curriculo.version != "V4":
        raise ValueError("Esta adaptación requiere un currículo V4 verificado")
    fuentes = {f.archivo_local: f for f in curriculo.fuentes}
    fuentes_por_nombre = {f.archivo: f for f in curriculo.fuentes}
    if len(fuentes_por_nombre) != len(curriculo.fuentes):
        raise ValueError("Los nombres de archivo de las fuentes no son inequívocos")
    celdas_originales = {
        (hoja.fuente_id, hoja.nombre, celda.coordenada): celda
        for hoja in curriculo.hojas
        for registro in hoja.registros
        for celda in registro.celdas
    }
    filas = {(f.fuente_id, f.hoja, f.fila): f for f in curriculo.filas}
    consultas, gold, localizadores, avisos = [], {}, {}, []
    for caso in datos["casos"]:
        consulta = ConsultaEvaluacion(
            id=caso["id"], consulta=caso["consulta"], version="V4", grado=caso["grado"], asignatura=caso["asignatura"]
        )
        if consulta.id in gold:
            raise ValueError("El conjunto contiene consultas duplicadas")
        consultas.append(consulta.model_dump(mode="json"))
        objetivos, registro_localizadores = [], []
        for indice, localizador in enumerate([caso["fuente"], *caso.get("referencias_adicionales", [])]):
            archivo = localizador["archivo"]
            path = PurePosixPath(archivo)
            if path.is_absolute() or ".." in path.parts or "\\" in archivo:
                raise ValueError("El localizador debe identificar una fuente relativa registrada")
            fuente = fuentes.get(archivo)
            if fuente is None and len(path.parts) == 1:
                fuente = fuentes_por_nombre.get(archivo)
            if fuente is None or fuente.sha256 != localizador["sha256"]:
                raise ValueError("El localizador no coincide con una fuente y SHA del currículo ingerido")
            filas_declaradas = localizador["filas"]
            if not filas_declaradas or len(filas_declaradas) != len(set(filas_declaradas)):
                raise ValueError("El localizador debe declarar filas únicas")
            pendientes = set(localizador["celdas"])
            if len(pendientes) != len(localizador["celdas"]):
                raise ValueError("El localizador no admite celdas repetidas")
            for fila in filas_declaradas:
                coordenadas = tuple(
                    c
                    for c in localizador["celdas"]
                    if c.rstrip("0123456789") != c and c[len(c.rstrip("0123456789")) :] == str(fila)
                )
                objetivo = ObjetivoRelevante(
                    documento=fuente.id, hoja=localizador["hoja"], fila=fila, celdas=coordenadas
                )
                objetivos.append(objetivo.model_dump(mode="json"))
                pendientes.difference_update(coordenadas)
                fila_curricular = filas.get((fuente.id, objetivo.hoja, fila))
                registro_localizadores.append(
                    {
                        "rol": "fuente" if indice == 0 else "referencia_adicional",
                        "archivo": fuente.archivo_local,
                        "sha256": fuente.sha256,
                        **objetivo.model_dump(mode="json"),
                        "fila_curricular_id": fila_curricular.id if fila_curricular else None,
                    }
                )
                if fila_curricular is None:
                    avisos.append(
                        {
                            "caso": consulta.id,
                            "tipo": "fila_no_curricular_o_ausente",
                            **objetivo.model_dump(mode="json"),
                        }
                    )
                for coordenada in coordenadas:
                    celda = celdas_originales.get((fuente.id, objetivo.hoja, coordenada))
                    if celda is None or celda.valor is None or not str(celda.valor).strip():
                        avisos.append(
                            {
                                "caso": consulta.id,
                                "tipo": "celda_ausente_o_vacia",
                                "documento": fuente.id,
                                "hoja": objetivo.hoja,
                                "celda": coordenada,
                            }
                        )
            if pendientes:
                raise ValueError("Hay celdas fuera de las filas declaradas en el localizador")
        gold[consulta.id], localizadores[consulta.id] = objetivos, registro_localizadores
    if not consultas:
        raise ValueError("El conjunto no contiene consultas")
    return {
        "consultas": {
            "schema_version": "1.0",
            "conjunto_id": datos.get("conjunto_id"),
            "nivel": datos.get("nivel"),
            "casos": consultas,
        },
        "gold_offline": {
            "schema_version": "1.0",
            "conjunto_id": datos.get("conjunto_id"),
            "huella_curriculo": curriculo.huella,
            "objetivos": gold,
            "localizadores_originales": localizadores,
            "avisos": avisos,
            "regla": "Transcripción íntegra de fuente y referencias_adicionales, sin filtrar labels",
        },
    }


def escribir_conjunto_v4(conjunto: dict, destino: Path) -> dict[str, str]:
    """Write public queries and offline evaluation locators into separate files."""
    destino.mkdir(parents=True, exist_ok=True)
    rutas = {"consultas": destino / "consultas_publicas.json", "gold_offline": destino / "gold_offline.json"}
    for clave, archivo in rutas.items():
        archivo.write_text(json.dumps(conjunto[clave], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {clave: hashlib.sha256(archivo.read_bytes()).hexdigest() for clave, archivo in rutas.items()}
