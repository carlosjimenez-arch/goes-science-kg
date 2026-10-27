"""Verify explicit complementary reviews against the exact artifacts and preserve every finding."""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

CARPETA = Path("data/clases_v4/complementaria")
VERSION = "revision-complementaria-2"


class DictamenAnexo(BaseModel):
    """Bind one explicit annex verdict to its exact reviewed bytes."""

    model_config = ConfigDict(extra="forbid")
    fila_corta: str = Field(pattern=r"^[0-9a-f]{10}$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    veredicto: Literal["liberable", "bloquear"]
    hallazgos: list[str]


class DictamenEvaluacion(BaseModel):
    """Bind the assessment verdict and item findings to the reviewed assessment."""

    model_config = ConfigDict(extra="forbid")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    veredicto: Literal["liberable", "bloquear"]
    items_con_defecto: list[str]
    hallazgos: list[str]


class RevisionComplementaria(BaseModel):
    """Describe a complete independent review and, when applicable, its correction record."""

    model_config = ConfigDict(extra="forbid")
    version: Literal["revision-complementaria-2"]
    unidad_id: str
    expediente_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    revisor: str = Field(min_length=1)
    ronda: Literal["inicial", "final"]
    anexos: list[DictamenAnexo]
    evaluacion: DictamenEvaluacion
    observaciones_sobre_guiones: list[str]
    correccion_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")


def digest(archivo: Path) -> str:
    """Hash the exact bytes reviewed, including formatting and line endings."""
    return hashlib.sha256(archivo.read_bytes()).hexdigest()


def _identidad_actor(valor: object) -> tuple[str, str] | None:
    """Identify the agent independently of its correction or review role."""
    if not isinstance(valor, str) or not (nombre := valor.strip().casefold()):
        return None
    if nombre == "codex-root":
        return ("codex", "root")
    for prefijo in ("codex-corrector-", "codex-revisor-"):
        if nombre.startswith(prefijo):
            actor = nombre.removeprefix(prefijo).strip()
            return ("codex", actor) if actor else None
    return ("literal", nombre)


def leer_revision(carpeta: Path, unidad: str) -> dict | None:
    """Select the latest round, without falling back when its contents are invalid."""
    nombres = (
        f"{unidad}_codex_final.json",
        f"{unidad}_codex_r1.json",
        f"{unidad}_final.json",
        f"{unidad}_r2.json",
        f"{unidad}.json",
    )
    for nombre in nombres:
        archivo = carpeta / "revision" / nombre
        if archivo.is_file():
            try:
                datos = json.loads(archivo.read_bytes())
                if not isinstance(datos, dict):
                    raise ValueError("El dictamen no es un objeto")
            except ValueError:
                datos = {}
            return {"datos": datos, "archivo": nombre, "sha256": digest(archivo)}
    return None


def validar_revision(carpeta: Path, exp: dict, revision: dict) -> list[str]:
    """Require exhaustive explicit verdicts, matching bytes, and an independent final reviewer."""
    try:
        r = RevisionComplementaria.model_validate(revision["datos"])
    except (KeyError, ValidationError):
        return ["Dictamen sin contrato de revisión verificable"]
    errores = []
    unidad = exp["corto"]
    if revision["archivo"].endswith("_codex_final.json") != (r.ronda == "final"):
        errores.append("El nombre del dictamen no corresponde a su ronda")
    if r.ronda == "inicial" and (carpeta / "correcciones" / f"{unidad}_codex.json").exists():
        errores.append("La unidad corregida requiere revisión final independiente")
    if r.unidad_id != exp["unidad_id"]:
        errores.append("La revisión corresponde a otra unidad")
    if r.expediente_sha256 != digest(carpeta / "expedientes" / f"{unidad}.json"):
        errores.append("El expediente cambió después de la revisión")
    esperados = {c["fila_id"][-10:] for c in exp["clases"]}
    filas = [a.fila_corta for a in r.anexos]
    if set(filas) != esperados or len(filas) != len(esperados):
        errores.append("La revisión no cubre cada anexo exactamente una vez")
    for anexo in r.anexos:
        archivo = carpeta / "anexos" / unidad / f"{anexo.fila_corta}.json"
        if not archivo.is_file() or digest(archivo) != anexo.sha256:
            errores.append(f"Anexo no coincide con la revisión: {anexo.fila_corta}")
        if anexo.veredicto == "bloquear" and not anexo.hallazgos:
            errores.append(f"Bloqueo sin motivo: {anexo.fila_corta}")
    evaluacion = carpeta / "evaluaciones" / f"{unidad}.json"
    if not evaluacion.is_file() or digest(evaluacion) != r.evaluacion.sha256:
        errores.append("La evaluación no coincide con la revisión")
    if r.evaluacion.veredicto == "bloquear" and not r.evaluacion.hallazgos:
        errores.append("Evaluación bloqueada sin motivo")
    if r.ronda == "final":
        archivo = carpeta / "correcciones" / f"{unidad}_codex.json"
        try:
            correccion = json.loads(archivo.read_bytes())
            if not isinstance(correccion, dict):
                raise ValueError("El registro de corrección no es un objeto")
            inicial = carpeta / "revision" / f"{unidad}_codex_r1.json"
            primera = RevisionComplementaria.model_validate_json(inicial.read_bytes())
            if digest(archivo) != r.correccion_sha256:
                errores.append("La revisión final no fija la corrección exacta")
            if correccion.get("revision_inicial_sha256") != digest(inicial):
                errores.append("La corrección no fija el dictamen inicial")
            corrector = _identidad_actor(correccion.get("corrector"))
            revisor = _identidad_actor(r.revisor)
            if corrector is None or revisor is None or corrector == revisor:
                errores.append("La revisión final no es independiente del corrector")
            if correccion.get("version") != "correccion-complementaria-1" or correccion.get("unidad_id") != r.unidad_id:
                errores.append("El registro de corrección no corresponde a esta unidad")
            anteriores = {f"anexos/{unidad}/{a.fila_corta}.json": a.sha256 for a in primera.anexos}
            anteriores[f"evaluaciones/{unidad}.json"] = primera.evaluacion.sha256
            cambios = correccion["cambios"]
            rutas = [c["ruta"] for c in cambios]
            if len(set(rutas)) != len(rutas):
                errores.append("El registro de corrección repite archivos")
            for cambio in cambios:
                rel = cambio["ruta"]
                if rel not in anteriores or cambio["antes_sha256"] != anteriores[rel]:
                    errores.append("La corrección no conserva la identidad de la versión anterior")
                elif not (carpeta / rel).is_file() or digest(carpeta / rel) != cambio["despues_sha256"]:
                    errores.append("La corrección no corresponde a los bytes actuales")
            actuales = {f"anexos/{unidad}/{a.fila_corta}.json": a.sha256 for a in r.anexos}
            actuales[f"evaluaciones/{unidad}.json"] = r.evaluacion.sha256
            if any(anteriores[rel] != actual and rel not in rutas for rel, actual in actuales.items()):
                errores.append("Hay ediciones sin registrar en la corrección")
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            errores.append("Falta el registro verificable de la corrección")
    elif r.correccion_sha256 is not None:
        errores.append("Una revisión inicial no puede certificar una corrección")
    return errores


def estado_revisiones(raiz: Path) -> dict:
    """Derive resumable work queues from artifacts, never from an agent's success message."""
    from goes_science_kg.clases.complementaria_publicacion import compilar

    carpeta = raiz / CARPETA
    publicable = compilar(raiz)
    retenidos = {r["id"]: r["motivo"] for r in publicable["retenidos"]}
    unidades = []
    for archivo in sorted((carpeta / "expedientes").glob("*.json")):
        exp = json.loads(archivo.read_bytes())
        revision = leer_revision(carpeta, exp["corto"])
        errores = validar_revision(carpeta, exp, revision) if revision else ["Sin revisión independiente"]
        datos = revision["datos"] if revision and not errores else {}
        bloqueados = [a["fila_corta"] for a in datos.get("anexos", []) if a.get("veredicto") == "bloquear"]
        evaluacion_bloqueada = (datos.get("evaluacion") or {}).get("veredicto") == "bloquear"
        ids = {exp["unidad_id"], *(c["fila_id"] for c in exp["clases"])}
        errores_contenido = [retenidos[id_] for id_ in sorted(ids) if id_ in retenidos] if not errores else []
        retenida = bloqueados or evaluacion_bloqueada or errores_contenido
        estado = "pendiente_revision" if errores else "retenida" if retenida else "liberable"
        unidades.append(
            {
                "corto": exp["corto"],
                "estado": estado,
                "revision": revision["archivo"] if revision else None,
                "errores_revision": errores,
                "errores_contenido": errores_contenido,
                "anexos_bloqueados": bloqueados,
                "evaluacion_bloqueada": evaluacion_bloqueada,
                "requiere_correccion": not errores and estado == "retenida" and datos.get("ronda") == "inicial",
                "requiere_revision_final": (carpeta / "correcciones" / f"{exp['corto']}_codex.json").exists()
                and not (revision and revision["archivo"].endswith("_codex_final.json")),
            }
        )
    return {
        "version": "estado-complementaria-1",
        "total": len(unidades),
        "pendientes_revision": sum(u["estado"] == "pendiente_revision" for u in unidades),
        "liberables": sum(u["estado"] == "liberable" for u in unidades),
        "retenidas": sum(u["estado"] == "retenida" for u in unidades),
        "anexos_publicables": len(publicable["clases"]),
        "evaluaciones_publicables": len(publicable["unidades"]),
        "unidades": unidades,
    }


def informe_observaciones(raiz: Path) -> dict:
    """Preserve findings from all rounds, merging only identical normalized text per unit."""
    carpeta = raiz / CARPETA
    observaciones: dict[tuple[str, str], dict] = {}
    for archivo in sorted((carpeta / "revision").rglob("*.json")):
        datos = json.loads(archivo.read_bytes())
        if not isinstance(datos, dict):
            raise ValueError(f"No se puede consolidar una revisión inválida: {archivo.name}")
        unidad = archivo.stem.split("_", 1)[0]
        for texto in datos.get("observaciones_sobre_guiones", []):
            normalizado = " ".join(unicodedata.normalize("NFKC", texto).split())
            clave = (unidad, normalizado)
            if clave not in observaciones:
                observaciones[clave] = {
                    "unidad": unidad,
                    "observacion": texto,
                    "estado": "pendiente_de_contraste",
                    "evidencias": [],
                }
            observaciones[clave]["evidencias"].append(
                {"revision": archivo.relative_to(carpeta / "revision").as_posix(), "sha256": digest(archivo)}
            )
    return {
        "version": "observaciones-guiones-complementaria-1",
        "limite": (
            "Posibles defectos señalados por revisores de IA; no son errores confirmados ni aprobación del MINED."
        ),
        "deduplicacion": (
            "Sólo texto idéntico normalizado por unidad; hallazgos parecidos conservan entradas separadas."
        ),
        "observaciones": list(observaciones.values()),
    }
