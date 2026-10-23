"""Correcciones editoriales explícitas; producen otro borrador que necesita cuatro lecturas nuevas."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Literal

from pydantic import Field, JsonValue

from goes_science_kg.clases.compilacion import leer_propio
from goes_science_kg.clases.contratos import BorradorClases, GuionClase
from goes_science_kg.clases.validacion import huella_contenido, validar_borrador
from goes_science_kg.materiales.compilacion import serializar, sha
from goes_science_kg.motor.contratos import Contrato, huella

CampoEditable = Literal[
    "titulo",
    "conocimientos_a_activar",
    "explicacion_docente",
    "sesiones",
    "tareas",
    "recursos",
    "alternativa_sin_recursos",
    "apoyos",
    "dificultad_previsible",
    "retroalimentacion",
    "seguridad",
    "implementacion_condicionada",
]


class CambioCampo(Contrato):
    campo: CampoEditable
    anterior: JsonValue
    nuevo: JsonValue
    motivo: str = Field(min_length=30, max_length=2000)


class CambioGuion(Contrato):
    fila_id: str
    resultado: str
    resultado_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    campos: tuple[CambioCampo, ...] = Field(min_length=1, max_length=12)


class ParcheEditorial(Contrato):
    version: Literal["parche-editorial-clases-1"]
    editor: str = Field(min_length=5, max_length=200)
    cambios: tuple[CambioGuion, ...] = Field(min_length=1, max_length=4)
    limite: str = Field(min_length=40, max_length=1200)


def _leer_parche(base, referencia):
    archivo = leer_propio(base, referencia["ruta"])
    if not archivo.resolve().is_relative_to((base / "data/clases_v4/ediciones_editoriales").resolve()):
        raise ValueError("El parche debe pertenecer al expediente editorial propio")
    raw = archivo.read_bytes()
    if len(raw) > 2 * 1024**2 or sha(raw) != referencia["sha256"]:
        raise ValueError("El parche editorial cambió o excede la cota")
    return raw, ParcheEditorial.model_validate_json(raw)


def reconstruir(base, preparacion, referencia):
    _, parche = _leer_parche(base, referencia)
    ids = [c.fila_id for c in parche.cambios]
    if len(set(ids)) != len(ids) or set(ids) != {f["fila_id"] for f in preparacion["filas"]}:
        raise ValueError("La edición no conserva exactamente los objetivos de la preparación")
    guiones = []
    for cambio in parche.cambios:
        archivo = leer_propio(base, cambio.resultado)
        if not archivo.resolve().is_relative_to((base / "data/clases_v4/ejecuciones").resolve()):
            raise ValueError("El antecedente editorial debe ser un resultado propio")
        raw = archivo.read_bytes()
        if sha(raw) != cambio.resultado_sha256:
            raise ValueError("El resultado anterior de la edición cambió")
        resultado = json.loads(raw)
        if resultado["snapshot_id"] != preparacion["snapshot_id"]:
            raise ValueError("La edición pertenece a otro snapshot")
        anterior = resultado["filas"][cambio.fila_id]["guion"]
        if anterior is None:
            raise ValueError("El antecedente editorial no contiene un guion")
        nuevo = deepcopy(anterior)
        campos = [c.campo for c in cambio.campos]
        if len(set(campos)) != len(campos):
            raise ValueError("El parche repite campos y no define una corrección inequívoca")
        for campo in cambio.campos:
            if nuevo[campo.campo] != campo.anterior or campo.anterior == campo.nuevo:
                raise ValueError("La precondición del campo no coincide o el cambio es vacío")
            nuevo[campo.campo] = campo.nuevo
        if huella_contenido(nuevo) == huella_contenido(anterior):
            raise ValueError("Un cambio de título o espacios no corrige el contenido")
        guiones.append(GuionClase.model_validate(nuevo))
    borrador = BorradorClases(guiones=guiones)
    errores = validar_borrador(borrador, preparacion)
    if errores:
        raise ValueError("La edición incumple el contrato de clase: " + json.dumps(errores, ensure_ascii=False))
    return borrador.model_dump(mode="json")


def preparar(base: Path, plantilla: dict, parche: Path):
    """No modifica resultados ni dictámenes; devuelve una preparación nueva para revisión."""
    nombre = parche.relative_to(base).as_posix()
    referencia = {"ruta": nombre, "sha256": sha(leer_propio(base, nombre).read_bytes())}
    p = deepcopy(plantilla)
    p.pop("id", None)
    for campo in ("borrador_inicial", "antecedente_sin_dictamenes", "edicion_editorial"):
        p.pop(campo, None)
    p["edicion_editorial"] = referencia
    p["borrador_inicial"] = reconstruir(base, p, referencia)
    _, documento = _leer_parche(base, referencia)
    vetos = p.setdefault("huellas_vetadas", {})
    for cambio in documento.cambios:
        raw = leer_propio(base, cambio.resultado).read_bytes()
        if sha(raw) != cambio.resultado_sha256:
            raise ValueError("El resultado anterior cambió al preparar sus huellas")
        anterior = json.loads(raw)["filas"][cambio.fila_id]["guion"]
        vetos[cambio.fila_id] = sorted(set(vetos.get(cambio.fila_id, [])) | {huella_contenido(anterior)})
    p["id"] = huella(p)
    return p


def validar(base, preparacion):
    esperado = reconstruir(base, preparacion, preparacion["edicion_editorial"])
    if esperado != preparacion.get("borrador_inicial"):
        raise ValueError("El borrador no corresponde exactamente al parche editorial archivado")
    return esperado


def archivos(base, preparacion):
    if not preparacion.get("edicion_editorial"):
        return {}
    validar(base, preparacion)
    ref = preparacion["edicion_editorial"]
    return {ref["ruta"]: _leer_parche(base, ref)[0]}


def guardar_parche(base, archivo, contenido):
    """Las ediciones quedan fijadas en un archivo nuevo; nunca sobrescriben un antecedente."""
    parche = ParcheEditorial.model_validate(contenido)
    if (
        archivo.is_symlink()
        or any(p.is_symlink() for p in archivo.parents)
        or not archivo.resolve().is_relative_to((base / "data/clases_v4/ediciones_editoriales").resolve())
    ):
        raise ValueError("La escritura requiere un archivo editorial nuevo dentro del expediente propio")
    raw = serializar(parche.model_dump(mode="json"))
    archivo.parent.mkdir(parents=True, exist_ok=True)
    with archivo.open("xb") as f:
        f.write(raw)
    return sha(raw)
