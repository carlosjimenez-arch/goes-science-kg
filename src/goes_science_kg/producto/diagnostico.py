"""Diagnose curriculum declarations separately from verified international coverage."""

from __future__ import annotations

from collections import Counter

from goes_science_kg.curriculo.catalogacion import CatalogoDisciplinas
from goes_science_kg.curriculo.contratos import FASES, Curriculo
from goes_science_kg.modelos import Nodo, TipoNodo
from goes_science_kg.producto._validacion import json_bytes, sha
from goes_science_kg.producto.contratos import AlertaSolicitada

CAMPOS_DIAGNOSTICO = (
    "contenido",
    "subcontenido",
    "procedimental",
    "indicador_avanzado",
    "indicadores_logro",
    "evidencia_aprendizaje",
    "competencia_pisa",
    "conocimiento_pisa",
    "contexto_pisa",
    "habilidad_timss",
    "habilidad_siglo_xxi",
    "competencia_digital",
    "actividad_digital",
    "habilidad_transversal",
    "actitudinal",
    "competencia_men",
    "dominio_clave",
    "notacion",
    "origen_contenido",
)


def diagnosticar(curriculo: Curriculo, catalogo: CatalogoDisciplinas, nodos: list[Nodo]) -> dict:
    """Count declared content and absences without inferring competence from vocabulary overlap."""
    total = len(curriculo.filas)
    campos = {}
    for campo in CAMPOS_DIAGNOSTICO:
        presentes = sum(bool(getattr(fila, campo).strip()) for fila in curriculo.filas)
        campos[campo] = {"declarado": presentes, "ausente": total - presentes, "candidato": 0, "verificado": 0}
    fases = {}
    for fase in FASES:
        fases[fase] = {
            "declarado": sum(bool(f.fases[fase].texto.strip()) for f in curriculo.filas),
            "columna_ausente": sum(not f.fases[fase].presente_en_hoja for f in curriculo.filas),
            "celda_vacia": sum(
                f.fases[fase].presente_en_hoja and not f.fases[fase].texto.strip() for f in curriculo.filas
            ),
            "candidato": 0,
            "verificado": 0,
            "autoridad_codigos": "insumo_local",
        }
    dimensiones = [n for n in nodos if n.tipo == TipoNodo.DIMENSION_DOCUMENTAL]
    return {
        "version_curriculo": "V4",
        "huella_curriculo": curriculo.huella,
        "unidad_conteo": "filas curriculares, no desempeños estudiantiles",
        "temas": total,
        "fuentes": len(curriculo.fuentes),
        "hojas": len(curriculo.hojas),
        "agrupaciones": len(curriculo.agrupaciones),
        "clasificacion": dict(sorted(Counter(f.estado for f in catalogo.filas).items())),
        "disciplinas": dict(sorted(Counter(d for f in catalogo.filas for d in f.disciplinas).items())),
        "filas_multidisciplinares": sum(len(f.disciplinas) > 1 for f in catalogo.filas),
        "pendientes_clasificacion": sum(f.estado == "abstencion" for f in catalogo.filas),
        "campos": campos,
        "fases": fases,
        "alineacion_internacional": {
            "estado": "pendiente_de_alineacion",
            "declarado": sum(bool(f.competencia_pisa.strip() or f.habilidad_timss.strip()) for f in curriculo.filas),
            "ausente": sum(not (f.competencia_pisa.strip() or f.habilidad_timss.strip()) for f in curriculo.filas),
            "candidato": 0,
            "verificado": 0,
            "limite": "Declaración de la malla; no mide cobertura de PISA, ERCE o TIMSS ni equivale a CUBRE",
        },
        "categorias_documentales": {
            "total": len(dimensiones),
            "anclas_verificadas": sum(
                n.props.get("estado_ancla") == "ancla_documental_verificada" for n in dimensiones
            ),
            "implican_cobertura": False,
        },
        "limites": [
            "Las ausencias no demuestran que el tema no se enseñe; describen los campos de esta entrega",
            "La clasificación disciplinar no verifica contenido científico o adecuación pedagógica",
            "Las referencias históricas no atribuyen conceptos, prerrequisitos o cobertura a las nuevas filas",
        ],
    }


def construir_alertas(
    curriculo: Curriculo,
    catalogo: CatalogoDisciplinas,
    evidencias: dict[str, dict],
    solicitadas: tuple[AlertaSolicitada, ...],
) -> dict:
    """Anchor every observation to real curriculum cells, including verified blanks."""
    por_id = {f.id: f for f in curriculo.filas}
    tareas: list[tuple[AlertaSolicitada, tuple[str, ...]]] = [(a, (a.fila_id,)) for a in solicitadas]
    for hoja in curriculo.hojas:
        if hoja.tratamiento != "curricular" or not hoja.filas_curriculares:
            continue
        for fase in FASES:
            ids = tuple(i for i in hoja.filas_curriculares if not por_id[i].fases[fase].presente_en_hoja)
            if ids:
                tareas.append(
                    (
                        AlertaSolicitada(
                            fila_id=ids[0],
                            campo=f"fase_{fase}",
                            codigo="fase_sin_columna",
                            descripcion=f"La hoja no contiene columna para {fase}; no se completa por inferencia.",
                        ),
                        ids,
                    )
                )
    for decision in catalogo.filas:
        if decision.estado == "abstencion":
            tareas.append(
                (
                    AlertaSolicitada(
                        fila_id=decision.fila_id,
                        campo="procedimental",
                        codigo="clasificacion_pendiente",
                        descripcion="La catalogación se abstuvo; se conserva el tema sin asignatura inferida.",
                    ),
                    (decision.fila_id,),
                )
            )
    salida, vistos = [], set()
    for alerta, afectadas in tareas:
        fila = por_id.get(alerta.fila_id)
        if fila is None:
            raise ValueError("Una alerta señala una fila ajena al currículo")
        coords = [c.coordenada for c in fila.celdas if c.campo == alerta.campo]
        respaldo_ausencia = not coords and alerta.campo.startswith("fase_")
        if respaldo_ausencia:
            fase = alerta.campo.removeprefix("fase_")
            if fase not in FASES or fila.fases[fase].presente_en_hoja:
                raise ValueError("Alerta de fase ausente sin respaldo en el esquema")
            evidencia = evidencias[f"ENCABEZADOS:{fila.fuente_id}:{fila.hoja}"]
            coords = evidencia["fuente"]["celdas"]
        else:
            evidencia = evidencias[fila.id]
        if not coords:
            raise ValueError(f"Una alerta señala un campo sin celdas: {alerta.campo}")
        fuente = evidencia["fuente"]
        celdas = [c for c in fuente["celdas_verificadas"] if c["coordenada_solicitada"] in coords]
        identidad = sha(json_bytes([alerta.model_dump(mode="json"), afectadas]))
        if identidad in vistos:
            raise ValueError("Alertas duplicadas")
        vistos.add(identidad)
        salida.append(
            {
                "id": f"ALERTA:V4:{identidad}",
                **alerta.model_dump(mode="json"),
                "estado": "observacion_pendiente",
                "filas_afectadas": list(afectadas),
                "fuente": {k: v for k, v in fuente.items() if k not in {"celdas", "celdas_verificadas"}}
                | {
                    "celdas": coords,
                    "celdas_verificadas": celdas,
                },
                "alcance_evidencia": (
                    "Ausencia de fase constatada en encabezados físicos cotejados con el archivo original"
                    if respaldo_ausencia
                    else "Valores de las celdas originales; la observación no es un dictamen científico"
                ),
            }
        )
    return {
        "version_curriculo": "V4",
        "huella_curriculo": curriculo.huella,
        "alertas": sorted(salida, key=lambda a: a["id"]),
        "resumen": dict(sorted(Counter(a["codigo"] for a in salida).items())),
        "limite": "Las alertas conservan el contenido; no aprueban, corrigen ni eliminan temas automáticamente",
    }
