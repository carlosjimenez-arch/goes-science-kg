"""Capturas HTML primarias por selector explícito; sin navegador, scripts ni paginación inventada."""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from pydantic import Field

from goes_science_kg.motor.contratos import Contrato, Evidencia, huella

HOSTS = frozenset({"openstax.org", "www.genome.gov", "iupac.org", "science.nasa.gov"})
MAX_BYTES = 8 * 1024 * 1024


class SelectorWeb(Contrato):
    etiqueta: str
    atributo: str | None = None
    valor: str | None = None


class FuenteWeb(Contrato):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    titulo: str
    institucion: str
    version_documental: str
    url: str
    selector: SelectorWeb
    licencia: str


def _url(url: str) -> None:
    p = urlparse(url)
    if p.scheme != "https" or p.hostname not in HOSTS or p.username or p.password or p.fragment or p.port:
        raise ValueError("La fuente científica requiere HTTPS y un dominio oficial revisado")


class _Redireccion(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        _url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def descargar_web(fuente: FuenteWeb) -> bytes:
    import certifi

    _url(fuente.url)
    opener = build_opener(_Redireccion(), HTTPSHandler(context=ssl.create_default_context(cafile=certifi.where())))
    with opener.open(Request(fuente.url, headers={"User-Agent": "goes-science-kg/evidencia-1.0"}), timeout=40) as r:
        _url(r.url)
        if r.headers.get_content_type() not in {"text/html", "application/xhtml+xml"}:
            raise ValueError("La fuente no devolvió HTML")
        contenido = r.read(MAX_BYTES + 1)
    if len(contenido) > MAX_BYTES:
        raise ValueError("La captura científica excede 8 MiB")
    return contenido


class _Lectura(HTMLParser):
    def __init__(self, selector: SelectorWeb):
        super().__init__(convert_charrefs=True)
        self.selector = selector
        self.pila = []
        self.partes = []
        self.coincidencias = 0

    def handle_starttag(self, tag, atributos):
        attrs = dict(atributos)
        vacio = tag in {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
        coincide = tag == self.selector.etiqueta and (
            self.selector.atributo is None or attrs.get(self.selector.atributo) == self.selector.valor
        )
        self.coincidencias += coincide
        activo = coincide or bool(self.pila and self.pila[-1][1])
        estilo = (attrs.get("style") or "").lower().replace(" ", "")
        oculto = tag in {"script", "style", "nav", "footer", "noscript", "template", "button", "svg"} or (
            "hidden" in attrs
            or attrs.get("aria-hidden") == "true"
            or "display:none" in estilo
            or "visibility:hidden" in estilo
            or bool(self.pila and self.pila[-1][2])
        )
        if activo and not oculto and tag in {"p", "div", "section", "h1", "h2", "h3", "li", "tr", "br"}:
            self.partes.append("\n")
        if not vacio:
            self.pila.append((tag, activo, oculto))

    def handle_endtag(self, tag):
        for i in range(len(self.pila) - 1, -1, -1):
            if self.pila[i][0] == tag:
                del self.pila[i:]
                return

    def handle_data(self, data):
        if self.pila and self.pila[-1][1] and not self.pila[-1][2]:
            self.partes.append(data)


def extraer_html(contenido: bytes, selector: SelectorWeb) -> str:
    if not contenido or len(contenido) > MAX_BYTES:
        raise ValueError("Se requiere una captura HTML acotada")
    lector = _Lectura(selector)
    lector.feed(contenido.decode("utf-8", errors="strict"))
    texto = "\n".join(" ".join(linea.split()) for linea in "".join(lector.partes).splitlines() if linea.strip())
    if lector.coincidencias != 1 or len(texto) < 80 or len(texto) > 100000 or "\ufffd" in texto:
        raise ValueError("La fuente requiere un selector único, texto íntegro y extracción válida")
    return texto


class RepositorioWeb:
    def __init__(self, raiz: Path):
        self.raiz = raiz

    def incorporar(self, fuente: FuenteWeb) -> dict:
        _url(fuente.url)
        contenido = descargar_web(fuente)
        texto = extraer_html(contenido, fuente.selector)
        digest = hashlib.sha256(contenido).hexdigest()
        registro = fuente.model_dump(mode="json") | {
            "sha256": digest,
            "sha256_texto": hashlib.sha256(texto.encode()).hexdigest(),
            "bytes": len(contenido),
            "extractor": "html-cientifico-1",
        }
        directorio = self.raiz / "objetos"
        directorio.mkdir(parents=True, exist_ok=True)
        archivo = directorio / f"{digest}.html"
        if archivo.is_symlink():
            raise ValueError("Un objeto científico no puede ser un enlace")
        if archivo.exists() and archivo.read_bytes() != contenido:
            raise ValueError("Colisión o mutación de un objeto científico")
        if not archivo.exists():
            archivo.write_bytes(contenido)
        from goes_science_kg.motor.ejecuciones import _bloqueo

        path = self.raiz / "manifest.json"
        if path.is_symlink():
            raise ValueError("El manifiesto científico no puede ser un enlace")
        with _bloqueo(path, "ingesta", esperar=True):
            manifest = (
                json.loads(path.read_bytes()) if path.exists() else {"version": "web-cientifica-1", "fuentes": {}}
            )
            anterior = manifest["fuentes"].get(fuente.id)
            if anterior and anterior != registro:
                raise ValueError("La edición web cambió; registre una captura con otra identidad")
            manifest["fuentes"][fuente.id] = registro
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.raiz, delete=False) as temporal:
                nombre = Path(temporal.name)
                temporal.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
                temporal.flush()
                os.fsync(temporal.fileno())
            try:
                os.replace(nombre, path)
            finally:
                nombre.unlink(missing_ok=True)
        return registro

    def evidencia(self, id_: str) -> Evidencia:
        manifest = json.loads((self.raiz / "manifest.json").read_bytes())
        r = manifest["fuentes"][id_]
        digest = r["sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("Identidad web incompatible")
        archivo = self.raiz / "objetos" / f"{digest}.html"
        if archivo.is_symlink() or not archivo.is_file():
            raise ValueError("Se requiere una captura científica regular")
        contenido = archivo.read_bytes()
        if hashlib.sha256(contenido).hexdigest() != digest or len(contenido) != r["bytes"]:
            raise ValueError("Cambió la captura HTML de la fuente primaria")
        selector = SelectorWeb.model_validate(r["selector"])
        texto = extraer_html(contenido, selector)
        if hashlib.sha256(texto.encode()).hexdigest() != r["sha256_texto"]:
            raise ValueError("La extracción no corresponde a su edición registrada")
        return Evidencia.crear(
            "WEB:" + huella([id_, digest, selector.model_dump(mode="json")]),
            texto,
            {
                "documento": id_,
                "sha256": digest,
                "url": r["url"],
                "selector_dom": selector.model_dump(mode="json"),
                "version_documental": r["version_documental"],
                "extractor": "html-cientifico-1",
                "verificacion": "contenido_fuente",
                "tipo": "documental",
                "fuente_primaria": True,
                "raiz_fuente": "referencias_web_cientificas_2026",
            },
            "referencia",
        )
