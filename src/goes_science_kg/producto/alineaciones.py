"""Preserve complete documentary alignment cohorts and reconstruct their review outcomes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from typing import Literal

from pydantic import Field

from goes_science_kg.curriculo.contratos import Curriculo
from goes_science_kg.ingesta.extraccion import CatalogoPerfilesPDF
from goes_science_kg.ingesta.referentes_operativos import ReferenteOperativo
from goes_science_kg.motor.alineacion import (
    LIMITE,
    ROLES_ALINEACION,
    DictamenAlineacion,
    PreparacionAlineacion,
    ResultadoAlineacion,
    SolicitudAlineacion,
    resolver_alineacion,
)
from goes_science_kg.motor.contratos import Contrato, huella
from goes_science_kg.recuperacion import Documento


class LecturaArchivada(Contrato):
    """Retain either an archived alignment judgment or its explicit failure."""

    dictamen: DictamenAlineacion | None
    error: str | None = Field(default=None, max_length=200)


class CasoAlineacion(Contrato):
    """Preserve one alignment request, preparation, complete readings, and reconstructed result."""

    solicitud: SolicitudAlineacion
    ejecucion_id: str = Field(min_length=1, max_length=100)
    huella_entorno: str = Field(pattern=r"^[a-f0-9]{64}$")
    preparacion: PreparacionAlineacion
    lecturas: dict[str, LecturaArchivada]
    resultado: ResultadoAlineacion

    def estado_original(self) -> dict:
        """Reconstruct the workflow input state from the original archived alignment case."""

        return {
            "solicitud": self.solicitud.model_dump(mode="json"),
            "ejecucion_id": self.ejecucion_id,
            "huella_entorno": self.huella_entorno,
            "preparacion": self.preparacion.model_dump(mode="json"),
            **{r: lectura.model_dump(mode="json") for r, lectura in self.lecturas.items()},
            "resultado": self.resultado.model_dump(mode="json"),
        }


class ArchivoAlineaciones(Contrato):
    """Archive a complete alignment cohort with source, extraction, and model identities."""

    version: Literal["alineaciones-publicadas-1"] = "alineaciones-publicadas-1"
    id: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_curriculo: str = Field(pattern=r"^[a-f0-9]{64}$")
    huella_extraccion: str = Field(pattern=r"^[a-f0-9]{64}$")
    perfiles: CatalogoPerfilesPDF | None = None
    modelos: dict[str, str]
    referentes: dict[str, ReferenteOperativo]
    fuentes: dict[str, dict]
    casos: tuple[CasoAlineacion, ...] = Field(min_length=1, max_length=10000)
    limite: Literal[LIMITE] = LIMITE

    @property
    def admitidos(self) -> tuple[CasoAlineacion, ...]:
        """Return alignment cases that satisfy the documented admission rules."""

        return tuple(c for c in self.casos if c.resultado.estado == "respaldo_documental_automatico")


def _verificar_preparacion(caso, archivo, curriculo, *, fuentes=None, paginas=None):
    p = caso.preparacion
    fila = next((f for f in curriculo.filas if f.id == caso.solicitud.fila_id), None)
    referente = archivo.referentes.get(caso.solicitud.referente_id)
    if (
        fila is None
        or referente is None
        or p.fila_id != fila.id
        or p.referente_id != referente.id
        or p.huella_curriculo != curriculo.huella
        or p.huella_referente != huella(referente)
        or p.referente != referente.model_dump(mode="json")
        or (p.grado, p.asignatura_malla) != (fila.grado, fila.asignatura_malla)
        or p.limite != LIMITE
    ):
        raise ValueError("La alineación no corresponde a su fila, referente, población o edición")
    registro = archivo.fuentes.get(referente.fuente)
    if not registro or registro.get("sha256") != referente.sha256:
        raise ValueError("La alineación requiere el documento primario de la edición indicada")
    if paginas is not None:
        actual = paginas.manifiesto().referencias[referente.fuente]
        if actual.sha256 != referente.sha256 or actual.version_documental != referente.version_documental:
            raise ValueError("Cambió la edición documental de la alineación")
    evidencias = {e.id: e for e in p.evidencias}
    if len(evidencias) != len(p.evidencias) or len({f.id for f in p.fragmentos}) != len(p.fragmentos):
        raise ValueError("La preparación contiene evidencias o fragmentos repetidos")
    fuente_local = next(f for f in curriculo.fuentes if f.id == fila.fuente_id)
    locales, externas = set(), set()
    for e in p.evidencias:
        if hashlib.sha256(e.texto.encode()).hexdigest() != e.huella:
            raise ValueError("Una evidencia no conserva su texto original")
        if e.version == curriculo.version:
            if (
                e.id.partition("#CELDA:")[0] != fila.id
                or e.fuente.get("documento") != fila.fuente_id
                or e.fuente.get("hoja") != fila.hoja
                or e.fuente.get("fila") != fila.fila
                or e.fuente.get("sha256") != fuente_local.sha256
            ):
                raise ValueError("Evidencia de otra fila o fuente curricular")
            locales.add(e.id)
            actual = (
                fuentes.hidratar(Documento(id=e.id, texto="Releer fuente física", fuente=e.fuente, version=e.version))
                if fuentes
                else e
            )
        elif e.version == "referencia":
            pagina = e.fuente.get("pagina")
            if (
                e.fuente.get("documento") != referente.fuente
                or e.fuente.get("sha256") != referente.sha256
                or pagina not in referente.paginas_pdf
            ):
                raise ValueError("Evidencia de otro referente, página o edición")
            externas.add(pagina)
            actual = paginas.pagina(referente.fuente, pagina) if paginas else e
        else:
            raise ValueError("Versión documental incompatible")
        if actual != e:
            raise ValueError("La evidencia cambió al releer la fuente primaria")
    if p.estado == "preparado" and (not locales or externas != set(referente.paginas_pdf)):
        raise ValueError("Faltan fuentes locales o páginas obligatorias del referente")
    if fuentes is not None and fuentes.motivos_bloqueo(p.evidencias):
        raise ValueError("La fila tiene una alerta científica bloqueante")
    for f in p.fragmentos:
        e = evidencias.get(f.evidencia_id)
        if e is None or f.literal not in " ".join(e.texto.split()):
            raise ValueError("Fragmento ajeno al texto primario")
        datos = [e.id, e.version, e.huella, e.fuente, f.literal]
        identidad = (
            "F:" + hashlib.sha256(json.dumps(datos, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:24]
        )
        if f.id != identidad:
            raise ValueError("El identificador del fragmento no corresponde a sus bytes")


def validar_archivo_alineaciones(
    archivo: ArchivoAlineaciones,
    curriculo: Curriculo,
    *,
    fuentes=None,
    paginas=None,
    modelos: Mapping[str, str] | None = None,
) -> None:
    """Reconstruct every alignment outcome and optionally rehydrate its physical sources."""

    # Implementation notes:
    # La selección histórica permanece intacta: no se vuelve a seleccionar contexto con un prompt
    # nuevo. El publicador exige ambos puertos físicos; un lector del snapshot valida su integridad.
    if (fuentes is None) != (paginas is None):
        raise ValueError("La comprobación física requiere fuentes locales y páginas primarias")
    if archivo.id != huella(archivo.model_dump(mode="json", exclude={"id"})):
        raise ValueError("El archivo de alineaciones no conserva su identidad")
    if archivo.huella_curriculo != curriculo.huella or set(archivo.modelos) != set(ROLES_ALINEACION):
        raise ValueError("Currículo o protocolo de tres lectores incompatible")
    if modelos is not None and archivo.modelos != dict(modelos):
        raise ValueError("Modelos distintos del protocolo de publicación configurado")
    if (
        paginas is not None
        and getattr(paginas, "huella_extraccion", archivo.huella_extraccion) != archivo.huella_extraccion
    ):
        raise ValueError("Cambió el perfil o implementación de extracción documental")
    claves = [huella(c.solicitud) for c in archivo.casos]
    if len(set(claves)) != len(claves):
        raise ValueError("Una fila/referente se repite; no se seleccionan rondas favorables")
    for caso in archivo.casos:
        if set(caso.lecturas) != set(ROLES_ALINEACION):
            raise ValueError("El archivo debe conservar los tres lectores, incluidos sus fallos")
        _verificar_preparacion(caso, archivo, curriculo, fuentes=fuentes, paginas=paginas)
        reconstruido = resolver_alineacion(caso.estado_original(), curriculo, archivo.referentes, archivo.modelos)
        if reconstruido != caso.resultado:
            raise ValueError("El resultado archivado no corresponde al cierre de sus lecturas")


def coleccionar_alineaciones(
    estados: Sequence[dict],
    curriculo: Curriculo,
    referentes: Mapping[str, ReferenteOperativo],
    modelos: Mapping[str, str],
    fuentes,
    paginas,
) -> ArchivoAlineaciones:
    """Preserve every supplied terminal outcome, including rejection and abstention, without model calls."""
    casos = tuple(
        CasoAlineacion(
            solicitud=s["solicitud"],
            ejecucion_id=s["ejecucion_id"],
            huella_entorno=s["huella_entorno"],
            preparacion=s["preparacion"],
            lecturas={r: s.get(r, {"dictamen": None, "error": None}) for r in ROLES_ALINEACION},
            resultado=s["resultado"],
        )
        for s in estados
    )
    usados = {c.solicitud.referente_id for c in casos}
    referencias = {r: referentes[r] for r in sorted(usados)}
    documentos = {r.fuente for r in referencias.values()}
    registros = paginas.manifiesto().referencias
    datos = dict(
        huella_curriculo=curriculo.huella,
        huella_extraccion=getattr(paginas, "huella_extraccion", huella(sorted(documentos))),
        perfiles=getattr(paginas, "perfiles", None),
        modelos=dict(modelos),
        referentes=referencias,
        fuentes={
            d: registros[d].model_dump(mode="json")
            | {"archivo_local": registros[d].archivo_pdf, "raiz_fuente": "referencias_2026"}
            for d in sorted(documentos)
        },
        casos=casos,
    )
    provisional = ArchivoAlineaciones(id="0" * 64, **datos)
    archivo = provisional.model_copy(update={"id": huella(provisional.model_dump(mode="json", exclude={"id"}))})
    validar_archivo_alineaciones(archivo, curriculo, fuentes=fuentes, paginas=paginas, modelos=modelos)
    return archivo
