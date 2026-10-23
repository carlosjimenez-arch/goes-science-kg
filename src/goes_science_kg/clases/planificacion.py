"""Agrupa contextos documentales por grado y asignatura sin modificar sus objetivos ni perder procedencia."""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy

from goes_science_kg.clases.contratos import MAX_CONTEXTO_BYTES
from goes_science_kg.clases.preparacion import contexto
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.motor.contratos import Evidencia, huella


def reagrupar(preparaciones, corpus):
    """Sólo contextos sin borrador ni tabla externa; máximo cuatro objetivos y contexto íntegro por lote."""
    if not preparaciones:
        raise ValueError("No hay preparaciones documentales para agrupar")
    comunes = ("version", "biblioteca_id", "snapshot_id", "escenario")
    cabecera = {k: deepcopy(preparaciones[0][k]) for k in comunes}
    fuentes, filas, antecedentes, hallazgos, vetadas = {}, {}, {}, {}, {}
    for p in preparaciones:
        if p["id"] != huella({k: v for k, v in p.items() if k != "id"}):
            raise ValueError("Una preparación documental cambió")
        if any(p[k] != cabecera[k] for k in comunes):
            raise ValueError("No se mezclan bibliotecas, snapshots o escenarios diferentes")
        if p.get("borrador_inicial") or p.get("insumos_tabulares"):
            raise ValueError("Los borradores o insumos tabulares requieren conservar su preparación específica")
        if p["corpus_sha256"] not in corpus.huellas_compatibles:
            raise ValueError("La versión de fuentes original no pertenece al registro de corpus")
        por_id = {e["id"]: e for e in p["fuentes"]}
        if len(por_id) != len(p["fuentes"]):
            raise ValueError("Una preparación repite identidades de fuente")
        for f in p["filas"]:
            id_ = f["fila_id"]
            if id_ in filas:
                raise ValueError("Un objetivo aparece en más de una preparación documental")
            filas[id_] = deepcopy(f)
            historico = {
                k: filas[id_].pop(k)
                for k in (
                    "seleccion_documental_anterior",
                    "consultas_documentales_adicionales",
                    "antecedente_documental",
                )
                if k in filas[id_]
            }
            antecedentes[id_] = {
                "preparacion_id": p["id"],
                "preparacion_sha256": sha(serializar(p)),
                "corpus_sha256": p["corpus_sha256"],
                "recuperacion": deepcopy(p.get("recuperacion")),
                "historico_recuperacion": historico,
            }
            hallazgos[id_] = deepcopy(p.get("hallazgos_previos", {}).get(id_, []))
            vetadas[id_] = deepcopy(p.get("huellas_vetadas", {}).get(id_, []))
            for nombre in f["fuentes_cientificas_ids"]:
                e = por_id[nombre]
                corpus.verificar(Evidencia.model_validate(e))
                if nombre in fuentes and fuentes[nombre] != e:
                    raise ValueError("Dos preparaciones atribuyen contenidos diferentes a la misma fuente")
                fuentes[nombre] = deepcopy(e)
    grupos = defaultdict(list)
    for f in filas.values():
        grupos[(f["grado"], f["asignatura"])].append(f)
    lotes = []

    def crear(filas_lote):
        ids = {f["fila_id"] for f in filas_lote}
        evidencias = {i for f in filas_lote for i in f["fuentes_cientificas_ids"]}
        p = deepcopy(cabecera) | {
            "corpus_sha256": corpus.huella,
            "filas": deepcopy(filas_lote),
            "fuentes": [fuentes[i] for i in sorted(evidencias)],
            "antecedentes_documentales": {i: antecedentes[i] for i in sorted(ids)},
            "hallazgos_previos": {i: hallazgos[i] for i in sorted(ids) if hallazgos[i]},
            "huellas_vetadas": {i: vetadas[i] for i in sorted(ids) if vetadas[i]},
            "limite_agrupacion": (
                "Agrupación operativa por grado y asignatura; conserva objetivo, unidad y contexto de cada fila. "
                "No declara equivalencias curriculares ni una nueva secuencia didáctica entre unidades."
            ),
        }
        if len(serializar(contexto(p))) > MAX_CONTEXTO_BYTES:
            if len(filas_lote) == 1:
                raise ValueError("Una fila excede el contexto; se requiere curación, no truncamiento")
            mitad = len(filas_lote) // 2
            crear(filas_lote[:mitad])
            crear(filas_lote[mitad:])
            return
        p["id"] = huella(p)
        lotes.append(p)

    for _, grupo in sorted(grupos.items()):
        grupo.sort(key=lambda f: (f["unidad"], f["origen"]["hoja"], f["origen"]["fila"], f["fila_id"]))
        for n in range(0, len(grupo), 4):
            crear(grupo[n : n + 4])
    resultantes = [f["fila_id"] for p in lotes for f in p["filas"]]
    if len(resultantes) != len(filas) or set(resultantes) != set(filas):
        raise ValueError("La agrupación no conserva exactamente todos los objetivos")
    return lotes
