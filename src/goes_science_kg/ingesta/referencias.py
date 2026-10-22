"""Fuentes públicas PDF con identidad de bytes y extracción reproducible por página.

El catálogo de investigación no activa marcos en el grafo. La ingesta produce un
manifiesto separado y rechaza sustituciones silenciosas de los documentos fijados.
"""

from __future__ import annotations

import hashlib
import json
import logging
import ssl
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from importlib.metadata import version
from io import BytesIO
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from goes_science_kg.motor.contratos import Evidencia
from goes_science_kg.motor.fuentes import FuentesVerificadas
from goes_science_kg.recuperacion import Documento

LOGGER = logging.getLogger(__name__)
MAX_BYTES = 32 * 1024 * 1024
SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
# Incorporar otro publicador exige revisar su dominio; el agente no navega URLs arbitrarias.
HOSTS_PDF = frozenset(
    {
        "www.oecd.org",
        "oecd.org",
        "unesdoc.unesco.org",
        "enlaces.mined.gob.sv",
        "edu.mineduc.gob.gt",
        "www.mined.gob.sv",
        "files.eric.ed.gov",
        "timss2027.org",
        "www.timss2027.org",
        "timssandpirls.bc.edu",
        "assets.publishing.service.gov.uk",
        "www.mext.go.jp",
        "www.moe.gov.sg",
        "www.bipm.org",
        "www.nextgenscience.org",
    }
)


def _sha(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()


class FuentePublica(BaseModel):
    """Selección explícita del registro oficial; no acepta direcciones con credenciales."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^[a-z0-9_]+$")
    titulo: str = Field(min_length=1)
    institucion: str = Field(min_length=1)
    version_documental: str = Field(min_length=1)
    url_catalogo: str
    url_documento: str
    estado_publicacion: str = Field(min_length=1)

    @field_validator("url_catalogo", "url_documento")
    @classmethod
    def _https_publico(cls, valor: str) -> str:
        partes = urlparse(valor)
        if partes.scheme != "https" or not partes.hostname or partes.username or partes.password or partes.fragment:
            raise ValueError("La fuente requiere una URL HTTPS sin credenciales ni fragmento")
        return valor


class ReferenciaIngerida(FuentePublica):
    """Identidad documental y del extractor; las páginas no son objetivos oficiales."""

    url_final: str
    sha256: SHA
    bytes: int = Field(gt=0, le=MAX_BYTES)
    paginas: int = Field(gt=0, le=1000)
    paginas_con_texto: int = Field(gt=0)
    sha256_paginas: SHA
    extractor: str

    @field_validator("url_final")
    @classmethod
    def _url_final_https(cls, valor: str) -> str:
        return FuentePublica._https_publico(valor)

    @model_validator(mode="after")
    def _conteo_coherente(self) -> ReferenciaIngerida:
        if self.paginas_con_texto > self.paginas:
            raise ValueError("Las páginas con texto exceden el total del PDF")
        return self

    @property
    def archivo_pdf(self) -> str:
        return f"objetos/{self.sha256}.pdf"

    @property
    def archivo_paginas(self) -> str:
        return f"paginas/{self.sha256_paginas}.jsonl"


class ManifiestoReferencias(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1.0"] = "1.0"
    referencias: dict[str, ReferenciaIngerida] = Field(default_factory=dict)


def fuentes_del_catalogo(catalogo: dict, seleccion: list[str]) -> list[FuentePublica]:
    """Solo documentos seleccionados: no rastrea enlaces ni inventa un PDF para una página."""
    if not seleccion or len(seleccion) != len(set(seleccion)):
        raise ValueError("Seleccione al menos una fuente, sin duplicados")
    salida = []
    for identificador in seleccion:
        registro = catalogo["fuentes"][identificador]
        if not registro.get("url_documento"):
            raise ValueError(f"{identificador}: falta una URL documental explícita")
        salida.append(
            FuentePublica(
                id=identificador,
                titulo=registro["titulo"],
                institucion=registro["institucion"],
                version_documental=registro["version"],
                url_catalogo=registro["url"],
                url_documento=registro["url_documento"],
                estado_publicacion=registro["estado_publicacion"],
            )
        )
    return sorted(salida, key=lambda fuente: fuente.id)


def descargar_pdf(fuente: FuentePublica) -> tuple[bytes, str]:
    """Una descarga pública acotada. Nunca adjunta ADC, cookies ni tokens de GCP."""
    _validar_destino(fuente.url_documento)
    import certifi

    contexto = ssl.create_default_context()
    # Conserva la confianza del sistema y añade el bundle fijado en uv.lock. Algunas
    # instalaciones Python de macOS no reconocen por defecto la cadena oficial de MEXT.
    contexto.load_verify_locations(cafile=certifi.where())
    solicitud = Request(fuente.url_documento, headers={"User-Agent": "goes-science-kg/referencias-1.0"})
    with build_opener(_RedireccionOficial(), HTTPSHandler(context=contexto)).open(solicitud, timeout=45) as respuesta:
        url_final = respuesta.geturl()
        _validar_destino(url_final)
        contenido = respuesta.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise ValueError("La descarga supera 32 MiB")
    if not contenido.startswith(b"%PDF-"):
        raise ValueError("La respuesta no es un PDF; no se archiva HTML como documento")
    return contenido, url_final


def _validar_destino(url: str) -> None:
    FuentePublica._https_publico(url)
    partes = urlparse(url)
    if partes.hostname not in HOSTS_PDF or partes.port not in {None, 443}:
        raise ValueError("El PDF debe proceder de un host oficial autorizado")


class _RedireccionOficial(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _validar_destino(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class RepositorioReferencias:
    """Objetos inmutables locales y manifiesto cuya escritura exige ingesta explícita."""

    def __init__(self, raiz: Path):
        self.raiz = raiz.resolve()
        self.archivo_manifest = self.raiz / "manifest.json"

    def manifiesto(self) -> ManifiestoReferencias:
        self._resolver("manifest.json")
        if not self.archivo_manifest.exists():
            return ManifiestoReferencias()
        datos = ManifiestoReferencias.model_validate_json(self.archivo_manifest.read_bytes())
        if any(clave != referencia.id for clave, referencia in datos.referencias.items()):
            raise ValueError("Identidad ambigua en el manifiesto de referencias")
        return datos

    def _leer(self, relativo: str, esperada: str) -> bytes:
        archivo = self._resolver(relativo)
        contenido = archivo.read_bytes()
        if _sha(contenido) != esperada:
            raise ValueError(f"Integridad incorrecta: {relativo}")
        return contenido

    def _resolver(self, relativo: str) -> Path:
        archivo = (self.raiz / relativo).resolve()
        if not archivo.is_relative_to(self.raiz):
            raise ValueError("Objeto fuera del repositorio de referencias")
        return archivo

    @contextmanager
    def _bloquear(self) -> Iterator[None]:
        # macOS y Linux/GCP. El lock del sistema se libera también si el proceso muere.
        import fcntl

        self.raiz.mkdir(parents=True, exist_ok=True)
        with self._resolver(".ingesta.lock").open("a+b") as bloqueo:
            fcntl.flock(bloqueo, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(bloqueo, fcntl.LOCK_UN)

    def _escribir_objeto(self, relativo: str, contenido: bytes) -> None:
        archivo = self._resolver(relativo)
        archivo.parent.mkdir(parents=True, exist_ok=True)
        if archivo.exists():
            if archivo.read_bytes() != contenido:
                raise ValueError("No se sobrescribe un objeto documental existente")
            return
        temporal = archivo.with_name(f".{archivo.name}.{uuid4().hex}.tmp")
        try:
            temporal.write_bytes(contenido)
            temporal.replace(archivo)
        finally:
            temporal.unlink(missing_ok=True)

    def incorporar(
        self,
        fuentes: list[FuentePublica],
        *,
        descargar: bool = False,
        sha256_esperados: Mapping[str, str] | None = None,
    ) -> ManifiestoReferencias:
        """Sin --descargar solo comprueba. Un lote fallido nunca publica un manifiesto parcial."""
        if len({fuente.id for fuente in fuentes}) != len(fuentes):
            raise ValueError("Identificadores de fuente duplicados")
        esperados = dict(sha256_esperados or {})
        if set(esperados) - {f.id for f in fuentes} or any(
            not isinstance(v, str) or len(v) != 64 or any(c not in "0123456789abcdef" for c in v)
            for v in esperados.values()
        ):
            raise ValueError("Las huellas esperadas deben corresponder a fuentes seleccionadas y ser SHA-256")
        if not descargar:
            return self._incorporar(fuentes, descargar=False, sha256_esperados=esperados)
        with self._bloquear():
            return self._incorporar(fuentes, descargar=descargar, sha256_esperados=esperados)

    def _incorporar(
        self,
        fuentes: list[FuentePublica],
        *,
        descargar: bool,
        sha256_esperados: Mapping[str, str],
    ) -> ManifiestoReferencias:
        previo = self.manifiesto()
        registros = dict(previo.referencias)
        for fuente in fuentes:
            anterior = registros.get(fuente.id)
            esperada = sha256_esperados.get(fuente.id)
            if anterior and esperada and anterior.sha256 != esperada:
                raise ValueError(f"{fuente.id}: el objeto fijado no corresponde a la edición esperada")
            if anterior and any(getattr(anterior, k) != v for k, v in fuente.model_dump().items()):
                raise ValueError(f"{fuente.id}: cambió la identidad registrada; use un ID de versión nuevo")
            if not descargar:
                if anterior is None:
                    raise FileNotFoundError(f"{fuente.id}: fuente pendiente; se requiere --descargar")
                self._leer(anterior.archivo_pdf, anterior.sha256)
                self._leer(anterior.archivo_paginas, anterior.sha256_paginas)
                continue
            contenido, url_final = descargar_pdf(fuente)
            _validar_destino(url_final)
            huella = _sha(contenido)
            if esperada and huella != esperada:
                raise ValueError(f"{fuente.id}: el PDF recibido no corresponde al SHA-256 esperado")
            if anterior and huella != anterior.sha256:
                raise ValueError(f"{fuente.id}: el servidor cambió el PDF fijado; no se sustituye la referencia")
            registro, paginas = self._extraer(fuente, contenido, url_final)
            if anterior and registro.sha256_paginas != anterior.sha256_paginas:
                raise ValueError(f"{fuente.id}: cambió la extracción; se requiere una migración explícita")
            self._escribir_objeto(registro.archivo_pdf, contenido)
            self._escribir_objeto(registro.archivo_paginas, paginas)
            registros[fuente.id] = registro
            LOGGER.info("VERDE fuente %s: %d páginas, SHA %s", fuente.id, registro.paginas, huella[:12])
        manifiesto = ManifiestoReferencias(referencias=dict(sorted(registros.items())))
        if descargar:
            self._escribir_manifest(manifiesto)
        return manifiesto

    def _escribir_manifest(self, manifiesto: ManifiestoReferencias) -> None:
        self.raiz.mkdir(parents=True, exist_ok=True)
        self._resolver("manifest.json")
        temporal = self._resolver(f".manifest.{uuid4().hex}.tmp")
        try:
            temporal.write_text(manifiesto.model_dump_json(indent=2) + "\n", encoding="utf-8")
            temporal.replace(self.archivo_manifest)
        finally:
            temporal.unlink(missing_ok=True)

    @staticmethod
    def _extraer(fuente: FuentePublica, contenido: bytes, url_final: str) -> tuple[ReferenciaIngerida, bytes]:
        from pypdf import PdfReader
        from pypdf.constants import UserAccessPermissions
        from pypdf.errors import FileNotDecryptedError

        if len(contenido) > MAX_BYTES or not contenido.startswith(b"%PDF-"):
            raise ValueError("PDF inválido o demasiado grande")
        lector = PdfReader(BytesIO(contenido), strict=True)
        if lector.is_encrypted:
            permisos = lector.user_access_permissions
            if (
                permisos is None
                or not permisos & UserAccessPermissions.EXTRACT
                or getattr(lector, "are_permissions_valid", None) is False
            ):
                raise ValueError("El PDF cifrado no habilita extracción de texto")
        try:
            total_paginas = len(lector.pages)
        except FileNotDecryptedError as error:
            raise ValueError("El PDF requiere una clave de apertura; no se importa") from error
        if not 0 < total_paginas <= 1000:
            raise ValueError("El PDF debe tener entre 1 y 1000 páginas")
        paginas = [{"pagina": i, "texto": p.extract_text() or ""} for i, p in enumerate(lector.pages, 1)]
        con_texto = sum(bool(p["texto"].strip()) for p in paginas)
        if not con_texto:
            raise ValueError("El PDF no contiene texto extraíble; requiere un proceso de OCR evaluado")
        serializado = "".join(json.dumps(p, ensure_ascii=False, sort_keys=True) + "\n" for p in paginas).encode("utf-8")
        registro = ReferenciaIngerida(
            **fuente.model_dump(),
            url_final=url_final,
            sha256=_sha(contenido),
            bytes=len(contenido),
            paginas=len(paginas),
            paginas_con_texto=con_texto,
            sha256_paginas=_sha(serializado),
            extractor=f"pypdf/{version('pypdf')};fonttools/{version('fonttools')};paginas-jsonl/1",
        )
        return registro, serializado

    def documentos(self, seleccion: list[str] | None = None) -> list[Documento]:
        """Páginas verificadas para localizar evidencia; no acreditan cobertura por tema."""
        registros = self.manifiesto().referencias
        documentos = []
        for identificador in sorted(registros if seleccion is None else seleccion):
            registro = registros[identificador]
            contenido = self._leer(registro.archivo_pdf, registro.sha256)
            if len(contenido) != registro.bytes:
                raise ValueError("El tamaño registrado no coincide con el PDF")
            paginas = self._leer(registro.archivo_paginas, registro.sha256_paginas)
            filas = [json.loads(linea) for linea in paginas.decode("utf-8").splitlines()]
            if [p["pagina"] for p in filas] != list(range(1, registro.paginas + 1)):
                raise ValueError("La extracción omite o duplica páginas del PDF")
            if sum(bool(p["texto"].strip()) for p in filas) != registro.paginas_con_texto:
                raise ValueError("El conteo de páginas con texto no coincide con el manifiesto")
            for pagina in filas:
                if not pagina["texto"].strip():
                    continue
                documentos.append(
                    Documento(
                        id=f"REF:{identificador}:P{pagina['pagina']:04d}",
                        texto=pagina["texto"],
                        fuente={"documento": identificador, "pagina": pagina["pagina"], "tipo": "documental"},
                        version="referencia",
                        metadata={
                            "titulo": registro.titulo,
                            "version_documental": registro.version_documental,
                            "unidad": "pagina_pdf_1_based",
                            "sha256": registro.sha256,
                        },
                    )
                )
        return documentos

    def fuentes_verificadas(self) -> FuentesVerificadas:
        catalogo = {
            id_: {"archivo_local": r.archivo_pdf, "sha256": r.sha256}
            for id_, r in self.manifiesto().referencias.items()
        }
        return FuentesVerificadas(catalogo, raiz_fuentes=self.raiz)

    def leer_pdf_verificado(self, identificador: str) -> bytes:
        """Bytes de la edición fijada para extractores explícitos; no cambia su extracción original."""
        registro = self.manifiesto().referencias[identificador]
        contenido = self._leer(registro.archivo_pdf, registro.sha256)
        if len(contenido) != registro.bytes:
            raise ValueError("El tamaño del PDF no coincide con la edición fijada")
        return contenido

    def pagina(self, identificador: str, pagina: int) -> Evidencia:
        registros = self.manifiesto().referencias
        registro = registros[identificador]
        if not 1 <= pagina <= registro.paginas:
            raise ValueError("Página PDF fuera de rango")
        documento = Documento(
            id=f"REF:{identificador}:P{pagina:04d}",
            texto="La evidencia se extrae de los bytes verificados del PDF",
            fuente={"documento": identificador, "pagina": pagina, "tipo": "documental"},
            version="referencia",
        )
        evidencia = self.fuentes_verificadas().hidratar(documento)
        if evidencia is None:
            raise ValueError("No hay texto verificable en la página solicitada")
        return evidencia
