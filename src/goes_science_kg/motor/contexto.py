"""Select bounded evidence without truncating quotations or mixing curriculum versions."""

from __future__ import annotations

from collections.abc import Sequence

from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.recuperacion import Resultado


def grupos_obligatorios(resultados: Sequence[Resultado], evidencias: Sequence[Evidencia]) -> dict | None:
    """Reserve every primary page linked to the requested row before ranking other context."""
    requeridas = {r.documento.id for r in resultados if r.documento.metadata.get("obligatoria") is True}
    if not requeridas:
        return None
    conocidas = {e.id for e in evidencias}
    if not requeridas.issubset(conocidas):
        raise ValueError("Falta una fuente primaria obligatoria dentro del presupuesto de contexto")
    return {id_: [id_] for id_ in sorted(requeridas)}


def construir_contexto(
    resultados: Sequence[Resultado],
    *,
    version: str,
    max_caracteres: int = 18000,
    fuentes: FuentesVerificadas | None = None,
) -> list[Evidencia]:
    """Build bounded source-verified context for one explicit curriculum version."""

    if max_caracteres < 100:
        raise ValueError("El presupuesto de contexto debe ser al menos de 100 caracteres")
    if any(resultado.documento.fuente.get("celdas") for resultado in resultados):
        if fuentes is None:
            return []
        from goes_science_kg.curriculo.contexto_fuentes import contexto_celdas

        return contexto_celdas(resultados, version=version, max_caracteres=max_caracteres, fuentes=fuentes)
    salida = []
    vistos = set()
    utilizados = 0
    for resultado in resultados:
        d = resultado.documento
        if d.id in vistos or d.version not in {version, "referencia"}:
            continue
        if not d.fuente.get("documento") or d.fuente.get("tipo") == "derivada":
            continue
        # Se empaqueta el fragmento completo; si no cabe, se busca el siguiente.
        e = fuentes.hidratar(d) if fuentes else Evidencia.crear(d.id, d.texto, d.fuente, d.version)
        if e is None:
            continue
        largo = len(e.model_dump_json())
        if utilizados + largo > max_caracteres:
            continue
        salida.append(e)
        utilizados += largo
        vistos.add(d.id)
    return salida
