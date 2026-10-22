"""Unidades nativas DOCX/HTML por código explícito, sin red, OCR ni texto de metadatos.

La visibilidad es estática: se omiten ocultación declarada, campos y cambios eliminados; no se
ejecutan Word, JavaScript ni CSS externo. Una unidad demasiado grande se rechaza, nunca se corta.
"""

from __future__ import annotations

import copy
import hashlib
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path, PurePosixPath
from xml.etree import ElementTree as ET
from zipfile import ZipFile

MAX_BYTES = 64 * 1024 * 1024
MAX_ZIP = 128 * 1024 * 1024
MAX_XML = 16 * 1024 * 1024
MAX_ELEMENTOS = 100000
MAX_PROFUNDIDAD = 128
MAX_UNIDAD = 100000
CODIGO = re.compile(r"[A-Z][A-Z0-9]{2,39}")
TOKEN = re.compile(r"(?<!\w)[A-Z][A-Z0-9]{2,39}(?!\w)")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
VERSION = "estructurados/1"


def huella_implementacion() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


@dataclass(frozen=True)
class ExtraccionCodigo:
    texto: str
    localizador: str
    metodo: str
    ubicacion: dict
    limites: str
    huella_implementacion: str


@dataclass(frozen=True)
class _Unidad:
    texto: str
    ubicacion: dict
    error: str | None = None


class IndiceEstructurado:
    """Índice local cacheable; ningún resultado mutable expone los registros internos."""

    def __init__(self, formato: str, unidades: dict[str, list[_Unidad]]):
        self.formato = formato
        self._unidades = copy.deepcopy(unidades)
        self.huella_implementacion = huella_implementacion()

    def extraer(self, codigo: str) -> ExtraccionCodigo:
        if not isinstance(codigo, str) or CODIGO.fullmatch(codigo) is None:
            raise ValueError("El código debe contener entre 3 y 40 letras mayúsculas/dígitos, iniciando con letra")
        unidades = self._unidades.get(codigo, [])
        if len(unidades) != 1:
            raise ValueError("El código no posee un anclaje único y completo en el documento")
        unidad = unidades[0]
        if unidad.error:
            raise ValueError(unidad.error)
        if not unidad.texto.strip() or len(unidad.texto) > MAX_UNIDAD:
            raise ValueError("La unidad está vacía o excede el límite; no se recorta para producir evidencia")
        motor = f"ElementTree/{ET.VERSION}" if self.formato == "docx" else "HTMLParser"
        return ExtraccionCodigo(
            texto=unidad.texto, localizador=codigo,
            metodo=f"{VERSION};stdlib.{motor};Python/{sys.version_info.major}.{sys.version_info.minor}",
            ubicacion=copy.deepcopy(unidad.ubicacion), huella_implementacion=self.huella_implementacion,
            limites=(
                "Texto nativo de una fila de word/document.xml; sin paginación, renderizado Word, "
                "imágenes, notas ni ejecución de campos. Se excluyen texto eliminado y ocultación explícita."
                if self.formato == "docx" else
                "Texto nativo de una sección DOM; sin paginación, JavaScript, recursos externos ni renderizado. "
                "La visibilidad se limita a atributos, estilos inline y reglas simples del CSS incrustado."
            ),
        )


def _contenido(contenido: bytes) -> None:
    if not isinstance(contenido, bytes) or not contenido or len(contenido) > MAX_BYTES:
        raise ValueError("Se requieren bytes de un documento dentro del límite de 64 MiB")


def _xml(contenido: bytes) -> ET.Element:
    if len(contenido) > MAX_XML:
        raise ValueError("La parte XML supera 16 MiB")
    texto = contenido.decode("utf-8-sig")
    if "\x00" in texto or re.search(r"<!\s*(DOCTYPE|ENTITY)\b", texto, re.IGNORECASE):
        raise ValueError("No se permiten DTD, entidades declaradas ni XML con codificación ambigua")
    parser = ET.iterparse(BytesIO(contenido), events=("start", "end"))
    elementos = profundidad = 0
    for evento, _ in parser:
        if evento == "start":
            elementos += 1
            profundidad += 1
            if elementos > MAX_ELEMENTOS or profundidad > MAX_PROFUNDIDAD:
                raise ValueError("La estructura XML excede el límite de elementos o profundidad")
        else:
            profundidad -= 1
    return parser.root


def _oculto_word(elemento: ET.Element) -> bool:
    if elemento.tag in {W + "del", W + "moveFrom"}:
        return True
    propiedades = elemento.find(W + "rPr") if elemento.tag == W + "r" else None
    return propiedades is not None and any(
        e.tag in {W + "vanish", W + "webHidden"} and e.get(W + "val", "true").lower() not in {"0", "false", "off"}
        for e in propiedades
    )


def _texto_word(elemento: ET.Element) -> str:
    if _oculto_word(elemento):
        return ""
    if elemento.tag == W + "t":
        return elemento.text or ""
    if elemento.tag in {W + "tab", W + "br", W + "cr"}:
        return "\n" if elemento.tag != W + "tab" else "\t"
    texto = "".join(_texto_word(hijo) for hijo in elemento)
    return texto + ("\n" if elemento.tag in {W + "p", W + "tc", W + "tr"} else "")


def _indice_word(contenido: bytes) -> dict[str, list[_Unidad]]:
    with ZipFile(BytesIO(contenido)) as paquete:
        entradas = paquete.infolist()
        if len(entradas) > 4096 or sum(e.file_size for e in entradas) > MAX_ZIP:
            raise ValueError("El ZIP descomprimido supera los límites")
        nombres = [e.filename for e in entradas]
        if len(nombres) != len(set(nombres)) or any(
            PurePosixPath(n).is_absolute() or ".." in PurePosixPath(n).parts or "\\" in n or "\x00" in n
            for n in nombres
        ):
            raise ValueError("El ZIP contiene partes duplicadas o rutas ambiguas")
        with paquete.open("word/document.xml") as parte:
            raiz = _xml(parte.read(MAX_XML + 1))
        if raiz.tag != W + "document":
            raise ValueError("La parte DOCX no es word/document.xml del namespace esperado")
        # Una definición de estilo oculto requiere un renderizador de estilos, fuera de este adaptador.
        if "word/styles.xml" in nombres:
            with paquete.open("word/styles.xml") as parte:
                estilos = _xml(parte.read(MAX_XML + 1))
            if any(e.tag in {W + "vanish", W + "webHidden"} for e in estilos.iter()):
                raise ValueError("Los estilos DOCX declaran ocultación que este adaptador no interpreta")
    padres = {hijo: padre for padre in raiz.iter() for hijo in padre}
    rutas = {raiz: "/w:document[1]"}
    for padre in raiz.iter():
        contadores: dict[str, int] = defaultdict(int)
        for hijo in padre:
            contadores[hijo.tag] += 1
            nombre = "w:" + hijo.tag[len(W):] if hijo.tag.startswith(W) else hijo.tag
            rutas[hijo] = f"{rutas[padre]}/{nombre}[{contadores[hijo.tag]}]"
    filas: dict[ET.Element, _Unidad] = {}
    unidades: dict[str, list[_Unidad]] = defaultdict(list)
    for parrafo in raiz.iter(W + "p"):
        ancestros = []
        actual = parrafo
        while actual in padres:
            ancestros.append(actual)
            actual = padres[actual]
        if any(_oculto_word(e) for e in ancestros):
            continue
        texto = " ".join(_texto_word(parrafo).split())
        codigos = TOKEN.findall(texto)
        if not codigos:
            continue
        fila = next((e for e in ancestros if e.tag == W + "tr"), None)
        if fila is None:
            unidad = _Unidad("", {}, "El código aparece fuera de una fila de tabla DOCX")
        else:
            if fila not in filas:
                lineas = [" ".join(linea.split()) for linea in _texto_word(fila).splitlines() if linea.strip()]
                filas[fila] = _Unidad("\n".join(lineas), {"parte": "word/document.xml", "ruta_xml": rutas[fila],
                                                        "unidad": "fila_tabla"})
            unidad = filas[fila]
        for codigo in codigos:
            unidades[codigo].append(unidad)
    return dict(unidades)


@dataclass
class _NodoHTML:
    tag: str
    atributos: dict[str, str | None]
    ruta: str
    padre: _NodoHTML | None = None
    hijos: list[_NodoHTML | str] = field(default_factory=list)
    cerrado: bool = False
    contadores: dict[str, int] = field(default_factory=lambda: defaultdict(int))


VACIOS = frozenset({"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param",
                    "source", "track", "wbr"})
OMITIDOS = frozenset({"head", "script", "style", "template", "noscript", "iframe", "object", "embed", "svg"})
BLOQUES = frozenset({"p", "div", "section", "li", "ul", "ol", "br", "h1", "h2", "h3", "h4", "h5", "h6"})


class _ParserHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = _NodoHTML("document", {}, "")
        self.pila = [self.raiz]
        self.nodos: list[_NodoHTML] = []

    def handle_starttag(self, tag, attrs):
        if len(self.nodos) >= MAX_ELEMENTOS or len(self.pila) >= MAX_PROFUNDIDAD:
            raise ValueError("La estructura HTML excede sus límites")
        nombres = [nombre for nombre, _ in attrs]
        if len(nombres) != len(set(nombres)):
            raise ValueError("Un elemento HTML contiene atributos duplicados y ambiguos")
        padre = self.pila[-1]
        padre.contadores[tag] += 1
        nodo = _NodoHTML(tag, dict(attrs), f"{padre.ruta}/{tag}[{padre.contadores[tag]}]", padre)
        padre.hijos.append(nodo)
        self.nodos.append(nodo)
        if tag not in VACIOS:
            self.pila.append(nodo)
        else:
            nodo.cerrado = True

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VACIOS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.pila) - 1, 0, -1):
            if self.pila[i].tag == tag:
                self.pila[i].cerrado = True
                del self.pila[i:]
                break

    def handle_data(self, data):
        self.pila[-1].hijos.append(data)

    def handle_decl(self, decl):
        if decl.strip().casefold() != "doctype html":
            raise ValueError("El HTML sólo admite DOCTYPE html sin DTD ni entidades externas")

    def unknown_decl(self, data):
        raise ValueError("El HTML contiene una declaración no admitida")


def _estilo_oculto(estilo: str) -> bool:
    estilo = re.sub(r"/\*.*?\*/", "", estilo, flags=re.DOTALL).casefold()
    if "\\" in estilo or re.search(
        r"(?:display|visibility|content-visibility|opacity|font-size)\s*:[^;]*(?:var|calc)\s*\(", estilo,
    ):
        raise ValueError("La visibilidad CSS contiene escapes o expresiones que no se pueden verificar")
    return bool(re.search(
        r"(?:^|;)\s*(?:display\s*:\s*none|visibility\s*:\s*(?:hidden|collapse)|"
        r"content-visibility\s*:\s*hidden|opacity\s*:\s*0(?:\.0+)?|font-size\s*:\s*0(?:px|em|rem|%)?)"
        r"\s*(?:!important\s*)?(?:;|$)", estilo,
    ))


def _selectores_ocultos(nodos: list[_NodoHTML]) -> list[str]:
    selectores = []
    for nodo in nodos:
        if nodo.tag != "style":
            continue
        css = re.sub(r"/\*.*?\*/", "", "".join(h for h in nodo.hijos if isinstance(h, str)), flags=re.DOTALL)
        for selector, cuerpo in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
            if not _estilo_oculto(cuerpo):
                continue
            for opcion in selector.split(","):
                opcion = opcion.strip()
                if re.fullmatch(r"(?:[a-zA-Z][a-zA-Z0-9_-]*|\*)?(?:[.#][a-zA-Z_][a-zA-Z0-9_-]*)*", opcion) is None:
                    raise ValueError("El CSS incrustado oculta contenido mediante un selector no interpretable")
                selectores.append(opcion)
    return selectores


def _coincide_selector(nodo: _NodoHTML, selector: str) -> bool:
    tag = re.match(r"^[a-zA-Z][a-zA-Z0-9_-]*|^\*", selector)
    if tag and tag[0] != "*" and tag[0].casefold() != nodo.tag:
        return False
    for prefijo, nombre in re.findall(r"([.#])([a-zA-Z_][a-zA-Z0-9_-]*)", selector):
        if prefijo == "#" and nodo.atributos.get("id") != nombre:
            return False
        if prefijo == "." and nombre not in (nodo.atributos.get("class") or "").split():
            return False
    return True


def _oculto_html(nodo: _NodoHTML, selectores: list[str]) -> bool:
    actual: _NodoHTML | None = nodo
    while actual is not None:
        attrs = actual.atributos
        if (
            actual.tag in OMITIDOS or "hidden" in attrs
            or (attrs.get("aria-hidden") or "").strip().casefold() == "true"
            or _estilo_oculto(attrs.get("style") or "")
            or any(_coincide_selector(actual, s) for s in selectores)
            or (actual.padre is not None and actual.padre.tag == "details"
                and "open" not in actual.padre.atributos and actual.tag != "summary")
        ):
            return True
        actual = actual.padre
    return False


def _texto_html(nodo: _NodoHTML, selectores: list[str]) -> str:
    if _oculto_html(nodo, selectores):
        return ""
    partes = [h if isinstance(h, str) else _texto_html(h, selectores) for h in nodo.hijos]
    return "".join(partes) + ("\n" if nodo.tag in BLOQUES else "")


def _indice_html(contenido: bytes) -> dict[str, list[_Unidad]]:
    texto = contenido.decode("utf-8-sig")
    if "\x00" in texto or re.search(r"<!\s*ENTITY\b", texto, re.IGNORECASE):
        raise ValueError("No se permiten entidades declaradas ni HTML con codificación ambigua")
    parser = _ParserHTML()
    parser.feed(texto)
    parser.close()
    selectores = _selectores_ocultos(parser.nodos)
    unidades: dict[str, list[_Unidad]] = defaultdict(list)
    for nodo in parser.nodos:
        codigo = nodo.atributos.get("id")
        if not codigo or CODIGO.fullmatch(codigo) is None:
            continue
        error = None
        if nodo.tag != "section" or not nodo.cerrado or _oculto_html(nodo, selectores):
            error = "El anclaje no es una sección HTML cerrada y visible"
        visibles = []
        pendientes = [nodo]
        while pendientes:
            actual = pendientes.pop()
            if actual.tag == "p" and not _oculto_html(actual, selectores):
                visibles.extend(c for c in TOKEN.findall(_texto_html(actual, selectores)) if c == codigo)
            pendientes.extend(h for h in actual.hijos if isinstance(h, _NodoHTML))
        if len(visibles) != 1:
            error = "La sección debe contener exactamente una mención completa del código en un párrafo visible"
        lineas = [" ".join(linea.split()) for linea in _texto_html(nodo, selectores).splitlines() if linea.strip()]
        unidades[codigo].append(_Unidad("\n".join(lineas), {"section_id": codigo, "ruta_dom": nodo.ruta,
                                                          "unidad": "section_html"}, error))
    return dict(unidades)


def indexar_documento(contenido: bytes, formato: str) -> IndiceEstructurado:
    """Lee una estructura una vez; devuelve un índice por identificadores físicos inequívocos."""
    _contenido(contenido)
    if formato == "docx":
        return IndiceEstructurado(formato, _indice_word(contenido))
    if formato in {"html", "htm"}:
        return IndiceEstructurado("html", _indice_html(contenido))
    raise ValueError("El adaptador sólo admite formatos docx, html y htm")


def extraer_codigo(contenido: bytes, formato: str, codigo: str) -> ExtraccionCodigo:
    return indexar_documento(contenido, formato).extraer(codigo)
