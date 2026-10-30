"""Define local evaluation criteria with explicit hierarchy and documentary evidence."""

# Historical implementation notes:
# La validación comprueba identidad y localización, nunca la alineación de una tarea.
# Una paráfrasis sólo adquiere procedencia verificada al cargarla junto al repositorio.

from __future__ import annotations

import hashlib
import json
import unicodedata
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.motor.contratos import Evidencia

TipoReferente = Literal["competencia", "subcompetencia", "tipo_conocimiento", "dominio", "proceso", "indicador"]
EjeReferente = Literal["contenido", "practica", "conocimiento", "demanda", "contexto"]
IdentificadorLocal = Annotated[str, Field(pattern=r"^LOCAL:[a-z0-9_]+$")]
PaginaPDF = Annotated[int, Field(strict=True, ge=1)]


def _normalizar(texto: str) -> str:
    """Normalize Unicode and whitespace while preserving words, numbers, and punctuation."""
    return " ".join(unicodedata.normalize("NFKC", texto).split())


def _paginas_validas(paginas: tuple[int, ...]) -> tuple[int, ...]:
    if any(p < 1 for p in paginas) or tuple(sorted(set(paginas))) != paginas:
        raise ValueError("Las páginas PDF deben ser positivas, únicas y ordenadas")
    return paginas


class ReferenteOperativo(BaseModel):
    """Represent a local analysis criterion without claiming an OECD or UNESCO code."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: IdentificadorLocal
    marco: str = Field(min_length=3)
    ciclo: str = Field(pattern=r"^[0-9]{4}$")
    version_documental: str = Field(min_length=5)
    fuente: str = Field(pattern=r"^[a-z0-9_]+$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    paginas_pdf: tuple[PaginaPDF, ...] = Field(min_length=1, max_length=6)
    ancla: str = Field(min_length=12, max_length=280)
    descripcion: str = Field(min_length=20, max_length=1800)
    eje: EjeReferente
    tipo: TipoReferente
    padre: IdentificadorLocal | None = None
    alcance: str = Field(min_length=25)
    grado_referencia: int | None = Field(default=None, ge=1, le=12, strict=True)
    edad_referencia: int | None = Field(default=None, ge=5, le=25, strict=True)

    _paginas = field_validator("paginas_pdf")(_paginas_validas)

    @field_validator("ancla")
    @classmethod
    def _ancla_breve(cls, texto: str) -> str:
        if texto != texto.strip() or len(texto.split()) > 20:
            raise ValueError("El ancla debe ser un fragmento literal de hasta veinte palabras, sin bordes vacíos")
        return texto

    @model_validator(mode="after")
    def _jerarquia_local(self) -> ReferenteOperativo:
        if self.tipo == "subcompetencia" and self.padre is None:
            raise ValueError("Una subcompetencia requiere una competencia padre explícita")
        if self.padre == self.id:
            raise ValueError("Un referente no puede ser su propio padre")
        return self


class CoberturaReferentes(BaseModel):
    """Count visible criteria on explicit pages rather than claiming complete framework coverage."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fuente: str
    unidad: str = Field(min_length=5)
    paginas_pdf: tuple[PaginaPDF, ...] = Field(min_length=1)
    tipo: TipoReferente
    padre: IdentificadorLocal | None = None
    esperados: int | None = Field(default=None, ge=0, strict=True)
    incluidos: int = Field(ge=0, strict=True)
    estado: Literal["completa_en_unidad_declarada", "parcial", "no_incluida"]
    limites: str = Field(min_length=20)

    _paginas = field_validator("paginas_pdf")(_paginas_validas)

    @model_validator(mode="after")
    def _conteo(self) -> CoberturaReferentes:
        if self.esperados is not None and self.incluidos > self.esperados:
            raise ValueError("La cobertura incluida excede la unidad declarada")
        if self.estado == "completa_en_unidad_declarada" and self.esperados != self.incluidos:
            raise ValueError("La cobertura completa requiere conteos esperados e incluidos iguales")
        if self.estado == "no_incluida" and self.incluidos:
            raise ValueError("Una unidad no incluida debe contener cero referentes")
        return self


class MetaReferentesOperativos(BaseModel):
    """Describe local reference scope, consultation date, provenance, and limitations."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    clasificacion: Literal["parafrasis_del_proyecto"]
    no_equivalencia: str = Field(min_length=30)
    fecha_consulta: date
    alcance: str = Field(min_length=30)
    exhaustividad: Literal["por_unidad_no_global"]
    paginas: str = Field(min_length=20)
    procedencia: Literal["data/referencias_2026/manifest.json"]
    documentacion: str = Field(min_length=10)
    limites: tuple[str, ...] = Field(min_length=1)
    cobertura: tuple[CoberturaReferentes, ...] = Field(min_length=1)


class CatalogoReferentesOperativos(BaseModel):
    """Collect versioned local assessment criteria and documentary metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"]
    meta: MetaReferentesOperativos
    referentes: tuple[ReferenteOperativo, ...] = Field(min_length=1, max_length=1000)

    @property
    def por_id(self) -> dict[str, ReferenteOperativo]:
        """Index validated assessment criteria by their local identifiers."""

        return {referente.id: referente for referente in self.referentes}

    @model_validator(mode="after")
    def _integridad_catalogo(self) -> CatalogoReferentesOperativos:
        por_id = self.por_id
        if len(por_id) != len(self.referentes):
            raise ValueError("Hay identificadores locales duplicados")
        for referente in self.referentes:
            if referente.padre:
                padre = por_id.get(referente.padre)
                if padre is None:
                    raise ValueError(f"{referente.id}: padre ausente del catálogo")
                if (padre.marco, padre.ciclo, padre.fuente) != (referente.marco, referente.ciclo, referente.fuente):
                    raise ValueError(f"{referente.id}: la jerarquía mezcla marcos, ciclos o fuentes")
                if (padre.edad_referencia, padre.grado_referencia) != (
                    referente.edad_referencia,
                    referente.grado_referencia,
                ):
                    raise ValueError(f"{referente.id}: la jerarquía mezcla poblaciones de referencia")
                if referente.tipo == "subcompetencia" and padre.tipo != "competencia":
                    raise ValueError(f"{referente.id}: el padre no es una competencia")
                visitados = {referente.id}
                actual = padre
                while actual.padre:
                    if actual.id in visitados:
                        raise ValueError("La jerarquía del catálogo contiene un ciclo")
                    visitados.add(actual.id)
                    if actual.padre not in por_id:
                        raise ValueError(f"{actual.id}: padre ausente del catálogo")
                    actual = por_id[actual.padre]
        cubiertos: set[str] = set()
        for unidad in self.meta.cobertura:
            seleccion = [
                r for r in self.referentes if (r.fuente, r.tipo, r.padre) == (unidad.fuente, unidad.tipo, unidad.padre)
            ]
            if len(seleccion) != unidad.incluidos:
                raise ValueError(f"{unidad.unidad}: el conteo no coincide con los referentes")
            ids = {r.id for r in seleccion}
            if ids.intersection(cubiertos):
                raise ValueError("Una unidad de cobertura contabiliza referentes repetidos")
            if any(not set(r.paginas_pdf).issubset(unidad.paginas_pdf) for r in seleccion):
                raise ValueError(f"{unidad.unidad}: las páginas declaradas no cubren los localizadores")
            cubiertos.update(ids)
        if cubiertos != set(por_id):
            raise ValueError("Hay referentes sin declaración de cobertura")
        return self


def evidencias_referentes(
    catalogo: CatalogoReferentesOperativos,
    repositorio: RepositorioReferencias,
) -> dict[str, tuple[Evidencia, ...]]:
    """Verify reference versions, pages, hashes, and literal anchors without network calls."""
    manifiesto = repositorio.manifiesto()
    for referente in catalogo.referentes:
        registro = manifiesto.referencias.get(referente.fuente)
        if registro is None:
            raise ValueError(f"{referente.id}: fuente pendiente de ingesta")
        if (registro.sha256, registro.version_documental) != (referente.sha256, referente.version_documental):
            raise ValueError(f"{referente.id}: SHA o versión documental no coinciden con el manifiesto")
    paginas: dict[tuple[str, int], Evidencia] = {}
    salida = {}
    for referente in catalogo.referentes:
        evidencias = []
        for pagina in referente.paginas_pdf:
            clave = (referente.fuente, pagina)
            if clave not in paginas:
                evidencia = repositorio.pagina(*clave)
                if evidencia is None or evidencia.fuente.get("sha256") != referente.sha256:
                    raise ValueError(f"{referente.id}: evidencia PDF no verificable")
                paginas[clave] = evidencia
            evidencias.append(paginas[clave])
        if not any(_normalizar(referente.ancla) in _normalizar(e.texto) for e in evidencias):
            raise ValueError(f"{referente.id}: ancla ausente de las páginas PDF indicadas")
        salida[referente.id] = tuple(evidencias)
    if repositorio.manifiesto() != manifiesto:
        raise ValueError("El manifiesto cambió durante la validación")
    return salida


def validar_referentes(
    catalogo: CatalogoReferentesOperativos,
    repositorio: RepositorioReferencias,
) -> dict:
    """Report auditable reference provenance without scoring tasks or asserting alignment."""
    evidencias = evidencias_referentes(catalogo, repositorio)
    serializado = json.dumps(catalogo.model_dump(mode="json"), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return {
        "estado": "procedencia_y_anclas_verificadas",
        "huella_catalogo": hashlib.sha256(serializado).hexdigest(),
        "total_referentes": len(catalogo.referentes),
        "huella_extraccion": getattr(repositorio, "huella_extraccion", None),
        "limite": "No acredita alineación de tareas, equivalencia entre grados ni eficacia educativa",
        "referentes": [
            {
                "id": r.id,
                "fuente": r.fuente,
                "sha256": r.sha256,
                "evidencias": [
                    {
                        "id": e.id,
                        "pagina_pdf": e.fuente["pagina"],
                        "huella_texto": e.huella,
                        "contiene_ancla": _normalizar(r.ancla) in _normalizar(e.texto),
                    }
                    for e in evidencias[r.id]
                ],
            }
            for r in catalogo.referentes
        ],
    }


def cargar_referentes(archivo: Path, repositorio: RepositorioReferencias) -> CatalogoReferentesOperativos:
    """Load safe YAML and require valid provenance before exposing usable criteria."""
    catalogo = CatalogoReferentesOperativos.model_validate(yaml.safe_load(archivo.read_text(encoding="utf-8")))
    evidencias_referentes(catalogo, repositorio)
    return catalogo
