"""Validate materialized products against verified original curriculum cells."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from openpyxl.utils.cell import coordinate_to_tuple, get_column_letter

from goes_science_kg.curriculo.catalogacion import DECLARADAS, ROLES, CatalogoDisciplinas
from goes_science_kg.curriculo.contexto_fuentes import documento_de_fila, fuentes_del_curriculo
from goes_science_kg.curriculo.contratos import Curriculo, RegistroHoja
from goes_science_kg.recuperacion import Documento

TOTAL_FILAS_V4 = 1020


def json_bytes(valor: object) -> bytes:
    """Serialize canonical bytes for identity and integrity checks."""
    return json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(contenido: bytes) -> str:
    """Compute the SHA-256 fingerprint of canonical serialized bytes."""

    return hashlib.sha256(contenido).hexdigest()


def validar_entrada(curriculo: Curriculo, catalogo: CatalogoDisciplinas) -> None:
    """Reject pilot catalogs, version mixtures, missing rows, and inconsistent assignments."""
    if curriculo.version != "V4" or catalogo.version_curriculo != "V4":
        raise ValueError("El producto V4 no admite otra versión curricular")
    if catalogo.modo != "completo" or not catalogo.piloto_superado:
        raise ValueError("El producto requiere catálogo completo con piloto superado")
    if catalogo.huella_curriculo != curriculo.huella or not re.fullmatch(r"[a-f0-9]{64}", curriculo.huella):
        raise ValueError("El catálogo no corresponde a la huella del currículo")
    if any(
        not re.fullmatch(r"[a-f0-9]{64}", valor) for valor in (catalogo.huella_instrucciones, catalogo.huella_harness)
    ):
        raise ValueError("El catálogo requiere huellas de instrucciones y harness")
    if set(catalogo.modelos) != set(ROLES) or not all(catalogo.modelos.values()):
        raise ValueError("El catálogo requiere identidad de los dos modelos")
    ids = [f.id for f in curriculo.filas]
    if len(ids) != TOTAL_FILAS_V4 or len(set(ids)) != TOTAL_FILAS_V4:
        raise ValueError("La entrega V4 requiere exactamente 1020 filas con IDs únicos")
    if Counter(ids) != Counter(f.fila_id for f in catalogo.filas):
        raise ValueError("La cobertura del catálogo debe coincidir exactamente con las filas curriculares")
    fuentes = {f.id: f for f in curriculo.fuentes}
    if len(fuentes) != len(curriculo.fuentes) or len({f.archivo for f in fuentes.values()}) != len(fuentes):
        raise ValueError("Fuentes duplicadas")
    for fuente in fuentes.values():
        identidad = f"FUENTE:V4:{sha(json_bytes(['V4', fuente.archivo, fuente.sha256]))}"
        if fuente.version != "V4" or fuente.id != identidad:
            raise ValueError("Fuente de otra versión o identidad incompatible")
    hojas = {(h.fuente_id, h.nombre): h for h in curriculo.hojas}
    if len(hojas) != len(curriculo.hojas) or any(h.fuente_id not in fuentes for h in curriculo.hojas):
        raise ValueError("Hojas duplicadas o sin fuente")
    registros = {(h.fuente_id, h.nombre, r.fila): r for h in curriculo.hojas for r in h.registros}
    clasificaciones = {f.fila_id: f for f in catalogo.filas}
    posiciones = set()
    for fila in curriculo.filas:
        posicion = (fila.fuente_id, fila.hoja, fila.fila)
        hoja = hojas.get(posicion[:2])
        if posicion in posiciones or fila.fuente_id not in fuentes or fila.version != "V4":
            raise ValueError("Fila duplicada, sin fuente o de otra versión curricular")
        posiciones.add(posicion)
        if hoja is None or hoja.tratamiento != "curricular":
            raise ValueError("Fila sin hoja curricular declarada")
        if hoja.grado != fila.grado or hoja.asignatura_malla != fila.asignatura_malla:
            raise ValueError("El grado o la asignatura no corresponde a la hoja original")
        if hoja.unidad is not None and hoja.unidad != fila.unidad:
            raise ValueError("La unidad de la fila no corresponde a su agrupación original")
        registro = RegistroHoja(fila=fila.fila, celdas=fila.celdas)
        if registro != registros.get(posicion):
            raise ValueError("La fila curricular no corresponde al registro original de su hoja")
        identidad = sha(
            json_bytes(
                {
                    "fuente": fila.fuente_id,
                    "version": "V4",
                    "hoja": fila.hoja,
                    "fila": fila.fila,
                    "contenido": registro.model_dump(mode="json"),
                }
            )
        )
        if fila.id != f"CURRICULO:V4:{identidad}":
            raise ValueError("La identidad de una fila no corresponde a su contenido versionado")
        if not 1 <= len(fila.celdas) <= 64 or len({c.coordenada for c in fila.celdas}) != len(fila.celdas):
            raise ValueError("Las filas requieren entre una y 64 coordenadas únicas")
        campos = {c.campo: c for c in fila.celdas if c.campo}
        if len(fila.celdas) != len(hoja.columnas) or any(
            c.columna != descriptor.columna or c.campo != descriptor.campo
            for c, descriptor in zip(fila.celdas, hoja.columnas, strict=True)
        ):
            raise ValueError("Los roles de las celdas no corresponden al esquema de la hoja")
        for celda in fila.celdas:
            fisica, columna = coordinate_to_tuple(celda.coordenada)
            if fisica != fila.fila or get_column_letter(columna) != celda.columna:
                raise ValueError("Coordenada física incompatible con su fila o columna")
        if len(campos) != sum(c.campo is not None for c in fila.celdas) or any(
            c.fila != fila.fila for c in fila.celdas
        ):
            raise ValueError("Campos repetidos o celdas de otra fila")
        for nombre, fase in fila.fases.items():
            if fase.presente_en_hoja != (f"fase_{nombre}" in campos) or (
                not fase.presente_en_hoja and (fase.texto or fase.codigos_locales or fase.coordenadas)
            ):
                raise ValueError("Ausencia de fase incoherente con el esquema de la fila")
        for campo, celda in campos.items():
            texto = "" if celda.valor is None else str(celda.valor).strip()
            if campo.startswith("fase_"):
                fase = fila.fases[campo.removeprefix("fase_")]
                if not fase.presente_en_hoja or fase.texto != texto:
                    raise ValueError("La fase no corresponde a su celda original")
            elif campo != "unidad" or hoja.unidad is None:
                if getattr(fila, campo) != texto:
                    raise ValueError(f"El campo {campo} no corresponde a su celda original")
        decision = clasificaciones[fila.id]
        tiene = bool(decision.disciplinas)
        if len(set(decision.disciplinas)) != len(decision.disciplinas) or (
            tiene != (decision.estado in {"declarado_malla", "coincidencia_automatica"})
        ):
            raise ValueError("Clasificación incoherente: abstenciones y fuera de alcance no asignan disciplinas")
        if decision.estado == "declarado_malla" and (decision.disciplinas != (DECLARADAS.get(fila.asignatura_malla),)):
            raise ValueError("La disciplina declarada no coincide con la asignatura de malla")
        if decision.estado == "coincidencia_automatica":
            if set(decision.lecturas) != set(ROLES) or decision.errores:
                raise ValueError("Coincidencia automática sin dos lecturas completas")
            for lectura in decision.lecturas.values():
                if (
                    lectura.fila_id != fila.id
                    or lectura.estado != "en_alcance"
                    or (set(lectura.disciplinas) != set(decision.disciplinas))
                ):
                    raise ValueError("Las lecturas no respaldan la clasificación automática")
    grupos = Counter(i for g in curriculo.agrupaciones for i in g.filas)
    if {f.fuente_id for f in curriculo.filas} != set(fuentes):
        raise ValueError("El currículo declara fuentes sin filas verificables")
    inventario_hojas = Counter(i for h in curriculo.hojas for i in h.filas_curriculares)
    if grupos != Counter(ids) or inventario_hojas != Counter(ids):
        raise ValueError("Agrupaciones u hojas omiten o duplican filas curriculares")
    por_id = {f.id: f for f in curriculo.filas}
    for grupo in curriculo.agrupaciones:
        if any(
            (por_id[i].grado, por_id[i].asignatura_malla, por_id[i].unidad)
            != (grupo.grado, grupo.asignatura_malla, grupo.unidad)
            for i in grupo.filas
        ):
            raise ValueError("Agrupación con grado, asignatura o unidad incorrectos")
    for hoja in curriculo.hojas:
        esperadas = Counter(f.id for f in curriculo.filas if (f.fuente_id, f.hoja) == (hoja.fuente_id, hoja.nombre))
        if Counter(hoja.filas_curriculares) != esperadas:
            raise ValueError("Una hoja atribuye filas curriculares de otra hoja")


def verificar_celdas(curriculo: Curriculo, raiz_v4: Path) -> tuple[dict[str, dict], dict[str, int]]:
    """Reopen original snapshots rather than substituting metadata for source values."""
    fuentes = fuentes_del_curriculo(curriculo, raiz_v4=raiz_v4)
    evidencias = {}
    for hoja in curriculo.hojas:
        if hoja.tratamiento != "curricular":
            continue
        originales = {
            f"{col.columna}{fila}": col.encabezados[i]
            for i, fila in enumerate(hoja.filas_encabezado)
            for col in hoja.columnas
        }
        coordenadas = list(originales)
        comprobadas = []
        evidencia = None
        for inicio in range(0, len(coordenadas), 64):
            documento = Documento(
                id=f"ENCABEZADOS:{hoja.fuente_id}:{hoja.nombre}:{inicio}",
                texto="Encabezados originales",
                version="V4",
                fuente={"documento": hoja.fuente_id, "hoja": hoja.nombre, "celdas": coordenadas[inicio : inicio + 64]},
            )
            evidencia = fuentes.hidratar(documento)
            if evidencia is None:
                raise ValueError("Encabezados originales no verificables")
            for celda in evidencia.fuente["celdas_verificadas"]:
                valor = originales[celda["coordenada_solicitada"]]
                if (type(valor), valor) != (type(celda["valor_original"]), celda["valor_original"]):
                    raise ValueError("Encabezado distinto de la celda original")
                comprobadas.append(celda)
        if evidencia is not None:
            datos = evidencia.model_dump(mode="json")
            datos["fuente"]["celdas"] = coordenadas
            datos["fuente"]["celdas_verificadas"] = comprobadas
            evidencias[f"ENCABEZADOS:{hoja.fuente_id}:{hoja.nombre}"] = datos
    for fila in curriculo.filas:
        evidencia = fuentes.hidratar(documento_de_fila(fila))
        if evidencia is None:
            raise ValueError(f"Fila sin respaldo en las fuentes originales: {fila.id}")
        originales = evidencia.fuente["celdas_verificadas"]
        if len(originales) != len(fila.celdas):
            raise ValueError("La fuente no devolvió todas las celdas solicitadas")
        for celda, original in zip(fila.celdas, originales, strict=True):
            origen = original["coordenada_origen"] if original["rango_combinado"] else None
            if (
                celda.coordenada != original["coordenada_solicitada"]
                or celda.origen_combinado != origen
                or celda.tipo_excel != original["tipo_excel"]
                or (type(celda.valor_original), celda.valor_original)
                != (type(original["valor_original"]), original["valor_original"])
                or (type(celda.valor), celda.valor) != (type(original["valor_real"]), original["valor_real"])
            ):
                raise ValueError(f"Celda curricular distinta del original: {fila.hoja}!{celda.coordenada}")
        evidencias[fila.id] = evidencia.model_dump(mode="json")
    return evidencias, fuentes.estadisticas()
