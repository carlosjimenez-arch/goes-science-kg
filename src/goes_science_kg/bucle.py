"""Strengthen expert-panel reviews through documented challenges and bounded responses."""

# Historical implementation notes:
# El panel resuelve por unanimidad, pero sus miembros son el mismo tipo de modelo: pueden equivocarse juntos, citar de
# memoria o apoyarse en los informes del propio proyecto. El bucle somete cada dictamen resuelto a tres pruebas y solo
# lo da por «sólido» si las pasa:
#
# 1. **Anclaje** (código, sin IA). Cada evidencia se clasifica:
#    - primaria: fila de la malla, objetivo de un país o página de un documento fuente;
#    - interna: README, contraste, vocabulario u otro dictamen (circular: el proyecto citándose a sí mismo);
#    - argumento («criterio disciplinar»);
#    - literatura no verificada.
#    En las primarias el código busca la cita en el texto de la fuente: «anclada» si está literal, «ubicada» si la
#    fuente existe pero la cita es paráfrasis o traducción, «inexistente» si el id o la página no existen.
# 2. **Impugnación** (IA adversarial). El subagente `refutador` busca en las fuentes la prueba más fuerte contra cada
#    dictamen y, si no la encuentra, aporta anclas literales a favor. Solo una contraevidencia anclada (el código la
#    encuentra en la fuente) reabre un expediente; en la capa pedagógica basta un error con su corrección válida.
# 3. **Sonda ciega** (IA, muestra). Una instancia nueva del mismo rol dictamina una muestra sin ver la resolución. El
#    acuerdo por tipo mide la estabilidad, y una discrepancia también reabre el expediente.
#
# Lo reabierto va a la **réplica**: los roles del panel ven la impugnación y mantienen o cambian su decisión, con las
# reglas del panel (unanimidad, una deliberación y, si no, «sin consenso» para una persona). Lo que cambió se impugna
# otra vez en la vuelta siguiente; el bucle se detiene cuando una vuelta no cambia nada o al llegar a `vueltas_max`.
#
# Circuito de la vuelta k (las rondas de réplica en el estado del panel son 10k + paso):
#   anclar()                → estado[x]["bucle"]["anclaje"]
#   impugnar(k)             → data/interim/panel/bucle/lotes/lote_b<k>_refutador_<disciplina>[_n].json
#   sonda(k, n)             → data/interim/panel/lotes/lote_c<k>_<rol>[_n].json (formato del panel, a ciegas)
#   cerrar_impugnacion(k)   → verifica las citas por código; lo impugnado queda «pendiente_paso_1»
#   replicar(k, paso)       → data/interim/panel/lotes/lote_r<10k+paso>_<rol>[_n].json
#   cerrar_replica(k, paso) → mantiene o cambia la resolución (y deja `aplicado` en blanco para volver a aplicarla)
#   solidez() / seccion_informe() → «sólido», «respaldado», «frágil», «sin consenso»

from __future__ import annotations

import json
import random
import re
import unicodedata
import zipfile
from collections import Counter, defaultdict
from collections.abc import Callable
from datetime import date
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from goes_science_kg import panel
from goes_science_kg.config import relativa, ruta

if TYPE_CHECKING:
    from goes_science_kg.ingesta.mallas import TemaMalla

DIR = "data/interim/panel/bucle"
VERSION = "bucle-v1"
VEREDICTOS = ("se_sostiene", "debilitada", "refutada")
PESO = {
    "asignacion": 0.4,
    "cambio_asignatura": 0.6,
    "decision": 1.2,
    "hallazgo": 1.5,
    "propuesta": 1.2,
    "contenido": 1.0,
    "clase_incierta": 1.5,
}
PESO_MAX_LOTE = 30
SOLIDECES = ("solido", "respaldado", "fragil", "delegada", "sin_consenso", "en_bucle", "sin_bucle")


def config() -> dict:
    """Load challenge-cycle configuration and evidence thresholds."""

    return panel.config()["bucle"]


# -- texto de las fuentes ---------------------------------------------------------------------------------------------
def norma(s: str) -> str:
    """Normalize letters and digits for accent-insensitive source quotation checks."""

    # Implementation notes:
    # saltos de línea, guiones de corte, comillas o mayúsculas. Conserva los caracteres chinos, japoneses y coreanos.
    s = unicodedata.normalize("NFKD", unicodedata.normalize("NFKC", s or "").lower())
    return "".join(c for c in s if c.isalnum() and not unicodedata.combining(c))


def _es_cjk(s: str) -> bool:
    return sum(ord(c) > 0x2E80 for c in s) * 2 >= len(s) > 0


def _largo_minimo(n: str) -> int:
    return config()["cita_minima"]["cjk" if _es_cjk(n) else "latin"]


def cita_en(cita: str, texto: str) -> bool:
    """Verify ordered literal quotation segments, including supported ellipses."""

    # Implementation notes:
    # alcanza el largo mínimo.
    tramos = [norma(t) for t in re.split(r"…|\.\.\.|\[…\]", cita or "")]
    tramos = [t for t in tramos if t]
    if not tramos or sum(map(len, tramos)) < _largo_minimo("".join(tramos)):
        return False
    t, pos = norma(texto), 0
    for tramo in tramos:
        if len(tramo) < 4:
            continue
        i = t.find(tramo, pos)
        if i < 0:
            return False
        pos = i + len(tramo)
    return True


@cache
def _indice_fuentes() -> dict[str, str]:
    """Index source filenames to their repository-relative paths without modifying them."""
    base = ruta("data/fuentes")
    return {p.name: relativa(p) for p in sorted(base.rglob("*")) if p.is_file()}


@cache
def _lector(archivo: str):
    import logging

    from pypdf import PdfReader

    logging.getLogger("pypdf").setLevel(logging.ERROR)  # avisos de fuentes CFF sin fontTools: no afectan al texto
    try:
        return PdfReader(ruta(archivo))
    except Exception:  # noqa: BLE001 — un PDF ilegible no ancla nada
        return None


@cache
def texto_pagina(archivo: str, pagina: int) -> str | None:
    """Read a one-based PDF page or return None when unavailable."""
    lector = _lector(archivo)
    if lector is None or not 1 <= pagina <= len(lector.pages):
        return None
    return lector.pages[pagina - 1].extract_text() or ""


@cache
def texto_documento(archivo: str) -> str | None:
    """Read supported non-PDF document text without inventing page locators."""
    p = ruta(archivo)
    if p.suffix == ".docx":
        with zipfile.ZipFile(p) as z:
            xml = z.read("word/document.xml").decode("utf-8", errors="replace")
        return re.sub(r"<[^>]+>", " ", re.sub(r"</w:p>", "\n", xml))
    if p.suffix in (".html", ".htm"):
        from goes_science_kg.internacional.extraer import _texto_html

        return _texto_html(p.read_text(encoding="utf-8", errors="replace"))
    if p.suffix in (".json", ".ttl"):  # .ttl: el Course of Study de Japón (texto UTF-8)
        return p.read_text(encoding="utf-8")
    return None


@cache
def _temas() -> dict[str, TemaMalla]:
    from goes_science_kg.ingesta.mallas import extraer

    temas = {t.id: t for t in extraer("mallas_v1")}
    temas.update({t.id: t for t in extraer("mallas_v2")})
    temas.update({t.id: t for t in extraer()})  # la vigente (V3) gana si el id existe en varias
    return temas


VIGENTE = "mallas"
ANTERIOR = " · versión anterior de la malla (no está en la vigente)"  # marca de una cita que solo está en la V2/V1


@cache
def _filas_completas(version: str = VIGENTE) -> dict[str, str]:
    """Index complete source-row text, including PISA skills and advanced indicators."""
    from goes_science_kg.ingesta.mallas import textos_completos

    return textos_completos(version)


@cache
def _ids_de(version: str) -> frozenset[str]:
    from goes_science_kg.ingesta.mallas import extraer

    return frozenset(t.id for t in extraer(version))


def _ids_vigentes() -> frozenset[str]:
    return _ids_de(VIGENTE)


@cache
def _temas_anteriores() -> dict[str, TemaMalla]:
    """Find historical topics whose identifiers now refer to changed or absent content."""
    from goes_science_kg.ingesta.mallas import extraer

    vigentes = {t.id: _texto_tema(t) for t in extraer()}
    salida: dict[str, TemaMalla] = {}
    for version in ("mallas_v1", "mallas_v2"):
        for t in extraer(version):
            if vigentes.get(t.id) != _texto_tema(t, version):
                salida[t.id] = t
    return salida


def _texto_tema(t: TemaMalla, version: str = VIGENTE) -> str:
    return " ".join(
        [
            t.unidad,
            t.contenido,
            t.subcontenido,
            t.procedimental,
            t.indicador,
            t.evidencia,
            t.habilidad_timss,
            _filas_completas(version).get(t.id, ""),
        ]
    )


@cache
def _objetivos() -> dict[str, dict]:
    """Index country objectives from both grade bands and historical references."""
    from goes_science_kg.internacional import tramo

    objs: dict[str, dict] = {}
    for t in tramo.TRAMOS.values():
        for p in sorted(ruta(t.objetivos).glob("*.json")):
            if not p.stem.endswith("_descartados"):
                objs.update({o["id"]: o for o in json.loads(p.read_text(encoding="utf-8"))})
    from goes_science_kg.ingesta import legado

    for o in [*legado.alineacion_paises(), *legado.paises_nuevos()]:  # UY, CO, SG y países de antecedente
        archivo = _indice_fuentes().get(o.get("documento") or "")
        objs.setdefault(o["id"], {**o, "archivo": archivo, "cita": ""})
    return objs


@cache
def _prefijos_objetivos() -> frozenset[str]:
    return frozenset(i.split("-", 1)[0] for i in _objetivos())


@cache
def _nodos_obj() -> dict[str, str]:
    """Index the graph's framework and senior-secondary objective texts."""
    p = ruta("data/grafo/nodos.jsonl")
    salida = {}
    for linea in p.read_text(encoding="utf-8").splitlines():
        n = json.loads(linea)
        if n["id"].startswith("OBJ:"):
            salida[n["id"].removeprefix("OBJ:")] = (
                n.get("etiqueta", "") + " " + json.dumps(n.get("props", {}), ensure_ascii=False)
            )
    return salida


# Páginas vecinas en que se busca una cita: los documentos imprimen una numeración distinta de la posición en el PDF
# (KR y TW, de 4 a 6 páginas). La cita debe ser literal, así que la ventana no ancla nada que no esté.
VECINAS = (0, -1, 1, -2, 2, -3, 3, -4, 4, -5, 5, -6, 6, -7, 7, -8, 8)

PAISES = {
    "ENG": "inglaterra",
    "SG": "singapur",
    "EE": "estonia",
    "AU": "australia",
    "UY": "uruguay",
    "TW": "taiwan",
    "ON": "ontario",
    "CO": "colombia",
    "HK": "hong_kong",
    "KR": "corea",
    "JP": "japon",
}

# Ids de tema, también los nuevos de la V3 («…-v3», spec 15): sin el sufijo se leería OTRO tema de la V2.
_RE_TEMA = re.compile(r"\bG\d\d-[A-Z]{3}-U\d+-(?:f\d+|\d+\.\d+(?:-f\d+)?(?:-v3)?(?:\s*(?:/|y|,)\s*\d+\.\d+)*)")
_RE_ID_PAIS = re.compile(r"\b[A-Z]{2,3}-[\w-]*\w")  # candidato a id de objetivo de un país
_RE_FORMA_OBJ = re.compile(r"-(?:p\d{3}|[A-Z]+\d+)-\d{2}$")  # forma de id de objetivo (si no existe: inventado)
_RE_CODIGO = re.compile(
    r"\b(AC9S[FU\d]*[UHI]\d{2}|ACS(?:CH|BL|PH|ES)\d{3}|PISA-[A-Z]{1,2}\d+|"
    r"T(?:4|8|A)(?:_27)?-[A-Z]\d(?:\.\d+)?)\b"
)
_RE_ARCHIVO = re.compile(r"(?:[\w.-]+/)*[\w.-]+\.(?:pdf|docx|html|xlsx|json|ttl)\b")
_RE_PAGINAS = re.compile(r"\bpp?\.\s*(\d+)(?:\s*[–-]\s*(\d+))?")
_RE_PAIS = re.compile(r"\b(" + "|".join(PAISES) + r")\b")
_RE_FILA = re.compile(r"\bfilas?\s*(\d+)")
_RE_INTERNA = re.compile(
    r"(?i)(readme|\.md\b|\.json\b|contraste|dictamen|internacional/|asignaturas/|data/|panel/|"
    r"\bCON:|vocabulario|grafo|objetivos de los|búsqueda en los)"
)
_RE_LITERATURA = re.compile(
    r"\b[A-ZÁÉÍÓÚ][a-záéíóúñ'-]+(?:\s+et al\.?|\s+(?:y|and|&)\s+[A-ZÁÉÍÓÚ][a-záéíóúñ'-]+)?"
    r"(?:,?\s*\((?:19|20)\d\d[a-z]?\)|,\s*(?:19|20)\d\d\b)"
)


@cache
def _rutas_fuentes() -> tuple[str, ...]:
    return tuple(sorted(relativa(p) for p in ruta("data/fuentes").rglob("*") if p.is_file()))


def _resolver(m: str) -> list[str]:
    """Resolve complete or partial document names within the source tree."""

    # Implementation notes:
    # que terminan así (los .ttl de Japón repiten nombres entre carpetas).
    return [a for a in _rutas_fuentes() if a == m or a.endswith("/" + m)]


def _paginas(fuente: str) -> list[int]:
    pags = []
    for a, b in _RE_PAGINAS.findall(fuente):
        a, b = int(a), int(b or a)
        pags += list(range(a, min(b, a + 15) + 1))
    return pags


def _candidatos(fuente: str) -> tuple[list[tuple[str, str]], list[str], list[str]]:
    """Find source text candidates and distinguish existing from missing references."""
    textos: list[tuple[str, str]] = []
    refs: list[str] = []
    malas: list[str] = []
    temas, objs = _temas(), _objetivos()
    for m in _RE_TEMA.finditer(fuente):
        base, *extra = re.split(r"\s*(?:/|y|,)\s*", m.group(0))
        prefijo = base.rsplit("-", 1)[0]
        for tid in [base, *[f"{prefijo}-{e}" for e in extra]]:
            refs.append(tid)
            if tid in temas:
                t = temas[tid]
                vigente = tid in _ids_vigentes()
                if vigente:
                    textos.append((f"{tid} ({t.ruta}, hoja «{t.hoja}», fila {t.fila})", _texto_tema(t)))
                if (a := _temas_anteriores().get(tid)) is not None:
                    version = "mallas_v2" if a.id in _ids_de("mallas_v2") else "mallas_v1"
                    textos.append(
                        (f"{tid} ({a.ruta}, hoja «{a.hoja}», fila {a.fila}){ANTERIOR}", _texto_tema(a, version))
                    )
            else:
                malas.append(tid)
    for oid in _RE_ID_PAIS.findall(_RE_TEMA.sub(" ", fuente)):
        if oid not in objs and not (oid.split("-", 1)[0] in _prefijos_objetivos() and _RE_FORMA_OBJ.search(oid)):
            continue
        refs.append(oid)
        if o := objs.get(oid):
            # Solo el original ancla: la cita literal extraída, la página del documento o, en Japón, el .ttl del Course
            # of Study. El «texto» del objetivo es la paráfrasis del proyecto: citarlo sería circular.
            textos.append((oid, o.get("cita", "")))
            if (m := re.fullmatch(r"JP-(\d{3})(\d{13})", oid)) and (ttl := _resolver(f"{m[1]}/{m[2]}.ttl")):
                textos.append((ttl[0].split("japon/")[-1], texto_documento(ttl[0]) or ""))
            if o.get("archivo") and o.get("pagina"):
                for p in (o["pagina"] + d for d in VECINAS):
                    if (t := texto_pagina(o["archivo"], p)) is not None:
                        textos.append((f"{o['archivo'].split('/')[-1]} p. {p}", t))
        else:
            malas.append(oid)
    for cod in _RE_CODIGO.findall(fuente):
        refs.append(cod)
        hallados = [
            (oid, o.get("cita", "")) for oid, o in objs.items() if oid.endswith(cod) or o.get("localizador") == cod
        ]
        if cod in _nodos_obj():
            hallados.append((f"OBJ:{cod}", _nodos_obj()[cod]))
        if cod.startswith("AC9S"):  # el tramo del docx de ese código: descripción (antes) y elaboraciones (después)
            for nombre in ("AU_Science_F-6_v9_contenido.docx", "AU_Science_7-10_v9_contenido.docx"):
                if (a := _indice_fuentes().get(nombre)) and (i := (t := texto_documento(a) or "").find(cod)) >= 0:
                    hallados.append((f"{nombre} ({cod})", re.sub(r"\s+", " ", t[max(0, i - 800) : i + 3000])))
        textos += hallados
        if not hallados:
            malas.append(cod)
    paginas = _paginas(fuente)
    archivos = [(m, a) for m in _RE_ARCHIVO.findall(fuente) for a in _resolver(m)]
    for m, a in archivos:
        nombre = a.split("/")[-1]
        refs.append(m)
        if nombre.endswith(".xlsx"):
            filas = [int(f) for f in _RE_FILA.findall(fuente)]
            ts = [t for t in temas.values() if t.archivo == nombre and (not filas or t.fila in filas)]
            textos += [(f"{nombre} fila {t.fila}", _texto_tema(t)) for t in ts]
        elif nombre.endswith(".pdf"):
            if not paginas:
                textos.append((nombre, ""))  # existe, pero sin página no se puede anclar una cita
            for p in paginas:
                for q in (p + d for d in VECINAS):
                    if (t := texto_pagina(a, q)) is not None:
                        textos.append((f"{nombre} p. {q}", t))
                if texto_pagina(a, p) is None:
                    malas.append(f"{nombre} p. {p}")
        else:
            textos.append((nombre, texto_documento(a) or ""))
    if not archivos and paginas:  # «HK p. 60», «KR (p. 55)»: todas las fuentes de ese país en esa página
        for pais in dict.fromkeys(_RE_PAIS.findall(fuente)):
            docs = [a for n, a in _indice_fuentes().items() if f"/paises/{PAISES[pais]}/" in a and n.endswith(".pdf")]
            refs.append(f"{pais} p. {', '.join(map(str, paginas))}")
            antes = len(textos)
            for a in docs:
                for p in paginas:
                    for q in (p + d for d in VECINAS):
                        if (t := texto_pagina(a, q)) is not None:
                            textos.append((f"{a.split('/')[-1]} p. {q}", t))
            if len(textos) == antes:  # sin PDF con esa página: los documentos sin páginas del país (docx, html)
                otros = [
                    a
                    for n, a in _indice_fuentes().items()
                    if f"/paises/{PAISES[pais]}/" in a and n.endswith((".docx", ".html"))
                ]
                textos += [(a.split("/")[-1], texto_documento(a) or "") for a in otros]
                if not otros:
                    malas.append(f"{pais} p. {paginas[0]}")
    return textos, refs, malas


def verificar(fuente: str, cita: str) -> dict:
    """Classify evidence and verify primary-source quotations against original text."""

    # Implementation notes:
    # → {"tipo": primaria|interna|argumento|literatura|otra, "estado": anclada|ubicada|inexistente|None,
    #    "refs": [...], "inexistentes": [...], "donde": dónde se encontró la cita}
    fuente = fuente or ""
    textos, refs, malas = _candidatos(fuente)
    if refs:
        donde = next((d for d, t in textos if t and cita_en(cita, t)), None)
        estado = "anclada" if donde else "ubicada" if textos else "inexistente"
        # «version»: la cita está en la malla vigente o solo en una anterior (la V2 o la V1).
        return {
            "tipo": "primaria",
            "estado": estado,
            "refs": refs,
            "inexistentes": malas,
            "donde": donde,
            "version": "anterior" if donde and donde.endswith(ANTERIOR) else "vigente" if donde else None,
        }
    if re.search(r"(?i)criterio", fuente):
        tipo = "argumento"
    elif _RE_INTERNA.search(fuente):
        tipo = "interna"
    elif _RE_LITERATURA.search(fuente):
        tipo = "literatura"
    else:
        tipo = "otra"
    return {"tipo": tipo, "estado": None, "refs": [], "inexistentes": [], "donde": None}


def textos_de_fuente(texto: str) -> list[tuple[str, str]]:
    """Return the exact source texts used by quotation verification."""

    # Implementation notes:
    # paráfrasis en español de los objetivos citados, como orientación: esa no ancla.
    objs = _objetivos()
    parafrasis = [
        (f"{oid} · paráfrasis del proyecto (no ancla)", objs[oid].get("texto", ""))
        for oid in _candidatos(texto)[1]
        if oid in objs
    ]
    return parafrasis + [(d, t) for d, t in _candidatos(texto)[0] if t]


def anclaje(x: dict) -> dict:
    """Collect all review evidence and verified challenge anchors for a dossier."""
    c: Counter = Counter()
    inexistentes: list[str] = []
    sobre_v3 = x.get("malla") == "V3"  # un dictamen hecho sobre la V3 no se ancla en texto que la V3 ya no tiene
    for d in x.get("dictamenes", []):
        for v in d.get("evidencia") or []:
            r = verificar(v.get("fuente", ""), v.get("cita_literal") or v.get("cita", ""))
            c[r["tipo"]] += 1
            if r["estado"]:
                c["ubicada" if sobre_v3 and r.get("version") == "anterior" else r["estado"]] += 1
            inexistentes += r["inexistentes"]
    c["anclada"] += len((x.get("bucle") or {}).get("anclas", []))
    c["primaria"] += len((x.get("bucle") or {}).get("anclas", []))
    nivel = "anclado" if c["anclada"] else "ubicado" if c["ubicada"] else "sin_fuente_primaria"
    return {
        "nivel": nivel,
        **{
            k: c[k]
            for k in ("primaria", "anclada", "ubicada", "inexistente", "interna", "argumento", "literatura", "otra")
        },
        "inexistentes": sorted(set(inexistentes)),
    }


def _en_alcance(x: dict, tipos: list[str] | None = None) -> bool:
    return x["tipo"] in (tipos or config()["tipos"]) and x["tipo"] != "piloto"


def anclar(tipos: list[str] | None = None) -> dict:
    """Measure primary-source anchoring for resolved and unresolved dossiers."""
    estado = panel.cargar_estado()
    conteo: dict[str, Counter] = defaultdict(Counter)
    for x in estado.values():
        if not _en_alcance(x, tipos) or x["estado"] not in ("resuelta", "sin_consenso") or x["tipo"] == "contenido":
            continue
        a = anclaje(x)
        x.setdefault("bucle", {})["anclaje"] = a
        conteo[x["tipo"]][a["nivel"]] += 1
        conteo[x["tipo"]]["con_inexistentes"] += bool(a["inexistentes"])
    panel._guardar_estado(estado)
    return {k: dict(v) for k, v in sorted(conteo.items())}


# -- lotes ------------------------------------------------------------------------------------------------------------
def _dir_lotes() -> Path:
    return ruta(f"{DIR}/lotes")


def _partir(exps: list[dict], peso: dict[str, float], maximo: float) -> list[list[dict]]:
    partes: list[list[dict]] = [[]]
    for e in exps:
        if partes[-1] and sum(peso[x["tipo"]] for x in partes[-1]) + peso[e["tipo"]] > maximo:
            partes.append([])
        partes[-1].append(e)
    return [p for p in partes if p]


def _escribir_lotes(
    carpeta: Path,
    prefijo: str,
    grupos: dict[str, list[dict]],
    cabecera: Callable[[str], dict],
    peso: dict[str, float],
    maximo: float,
) -> list[str]:
    carpeta.mkdir(parents=True, exist_ok=True)
    escritos = []
    for clave, exps in sorted(grupos.items()):
        partes = _partir(exps, peso, maximo)
        for k, parte in enumerate(partes, start=1):
            nombre = f"{prefijo}_{clave}" + (f"_{k}" if len(partes) > 1 else "")
            lote = {"lote": nombre, **cabecera(clave), "expedientes": parte}
            p = carpeta / f"lote_{nombre}.json"
            p.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            escritos.append(relativa(p))
    return escritos


def _disciplina(x: dict) -> str:
    expertos = [
        r
        for r in (x.get("etapas", [[None]])[0] if x["tipo"] == "contenido" else x["roles"])
        if r and r != "psicopedagogo"
    ]
    return (expertos[0] if expertos else "experto-quimica").removeprefix("experto-")


def _finales(x: dict) -> list[dict]:
    """Select the reviews supporting the current resolution across required content stages."""
    if x["tipo"] == "contenido":
        return x["dictamenes"]
    r = (x.get("resolucion") or {}).get("ronda")
    return [d for d in x["dictamenes"] if d["ronda"] == r] or x["dictamenes"][-1:]


def _resumen_dictamen(d: dict) -> dict:
    return {
        k: d[k]
        for k in (
            "id",
            "rol",
            "ronda",
            "decision",
            "justificacion",
            "evidencia",
            "confianza",
            "texto",
            "alternativa",
            "asignado_a",
            "cambios",
        )
        if k in d
    }


def _vuelta(x: dict, k: int) -> dict:
    """Get or initialize the dossier's record for the requested challenge cycle."""
    vueltas = x.setdefault("bucle", {}).setdefault("vueltas", [])
    v = next((v for v in vueltas if v["vuelta"] == k), None)
    if v is None:
        v = {"vuelta": k}
        vueltas.append(v)
    return v


def _a_impugnar(x: dict, k: int, tipos: list[str] | None, serie: str = "") -> bool:
    if not _en_alcance(x, tipos) or x["estado"] != "resuelta":
        return False
    vueltas = (x.get("bucle") or {}).get("vueltas", [])
    if k == 1:
        return not any(v.get("impugnacion") for v in vueltas)
    previa = next((v for v in vueltas if v["vuelta"] == k - 1), None)
    ya = any(v["vuelta"] == k and v.get("impugnacion") for v in vueltas)
    # Solo lo que cambió en la vuelta anterior DE ESTA SERIE y aún no se impugnó en esta vuelta.
    return bool(previa) and previa.get("replica") == "cambiada" and previa.get("serie", "") == serie and not ya


def _s(serie: str) -> str:
    """Build the suffix for an independent challenge-series batch."""
    return f"-{serie}" if serie else ""


def impugnar(k: int, tipos: list[str] | None = None, serie: str = "") -> list[str]:
    """Prepare challenge batches for eligible resolved dossiers in the selected cycle."""

    # Implementation notes:
    # vuelta anterior cambió. Un lote por disciplina (partido por peso).
    if k > config()["vueltas_max"]:
        raise ValueError(f"el bucle llega a {config()['vueltas_max']} vueltas (config/panel.yaml, bucle.vueltas_max)")
    estado = panel.cargar_estado()
    por_disciplina: dict[str, list[dict]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        if not _a_impugnar(x, k, tipos, serie):
            continue
        exp = {
            "id": i,
            "tipo": x["tipo"],
            "titulo": x["titulo"],
            "opciones": panel.config()["tipos"][x["tipo"]]["opciones"],
            "datos": x["datos"],
            "resolucion": x["resolucion"],
            "fundamentos": [_resumen_dictamen(d) for d in _finales(x)],
            "anclaje": (x.get("bucle") or {}).get("anclaje"),
        }
        if x["tipo"] == "contenido":
            exp["elemento_vigente"] = x.get("version_vigente") or x["datos"]["elemento"]
            exp["campos_editables"] = panel.config()["campos_editables"][x["elemento"]]
            exp["datos"] = {k2: v for k2, v in x["datos"].items() if k2 != "elemento"}
        por_disciplina[_disciplina(x)].append(exp)

    def cabecera(disciplina: str) -> dict:
        return {
            "vuelta": k,
            "rol": "refutador",
            "disciplina": disciplina,
            "version": VERSION,
            "instrucciones": [
                "prompts/bucle_refutar.md",
                ".claude/agents/refutador.md",
                f".claude/agents/experto-{disciplina}.md (solo «Tus criterios»)",
            ],
        }

    return _escribir_lotes(_dir_lotes(), f"b{k}{_s(serie)}_refutador", por_disciplina, cabecera, PESO, PESO_MAX_LOTE)


# Lo que una sonda ciega no puede leer: todo lo que deja ver lo que decidió el panel. La primera sonda (vuelta 1)
# avisó de dos fugas: los campos `revision` del contraste y los conteos de los README.
NO_LEER_SONDA = [
    "data/interim/panel/estado.json",
    "data/interim/panel/bucle/",
    "data/interim/panel/lotes/salida_*",
    "panel/",
    "internacional/*/README.md y internacional/README.md",
    "el campo «revision» de internacional/*/contraste.json",
    "data/interim/internacional*/revisiones.json",
    "asignaturas/decisiones/",
]


def sonda(k: int, n: int | None = None, semilla: int | None = None, tipos: list[str] | None = None) -> list[str]:
    """Prepare a stratified blind sample for repeat review."""

    # Implementation notes:
    # roles del panel dictaminan otra vez sin ver la resolución ni los dictámenes. Lotes en formato del panel.
    cfg = config()["sonda"]
    n, semilla = n or cfg["n"], cfg["semilla"] if semilla is None else semilla
    estado = panel.cargar_estado()
    por_tipo: dict[str, list[str]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        if _en_alcance(x, tipos) and x["estado"] == "resuelta" and x["tipo"] != "contenido":
            por_tipo[x["tipo"]].append(i)
    total = sum(map(len, por_tipo.values())) or 1
    rng = random.Random(semilla)
    elegidos = []
    for _t, ids in sorted(por_tipo.items()):
        m = min(len(ids), max(cfg["minimo_por_tipo"], round(n * len(ids) / total)))
        elegidos += rng.sample(ids, m)
    por_rol: dict[str, list[dict]] = defaultdict(list)
    for i in sorted(elegidos):
        x = estado[i]
        _vuelta(x, k)["sonda"] = {"pendiente": True}
        for rol in x["roles"]:
            por_rol[rol].append(
                {
                    "id": i,
                    "tipo": x["tipo"],
                    "titulo": x["titulo"],
                    "pregunta": x["pregunta"],
                    "datos": x["datos"],
                    "opciones": panel.config()["tipos"][x["tipo"]]["opciones"],
                }
            )
    panel._guardar_estado(estado)

    def cabecera(rol: str) -> dict:
        return {
            "ronda": f"c{k}",
            "rol": rol,
            "version": panel.VERSION,
            "ciega": True,
            "instrucciones": ["prompts/panel_dictaminar.md", f".claude/agents/{rol}.md"],
            "no_leer": NO_LEER_SONDA,
        }

    return _escribir_lotes(panel._dir_lotes(), f"c{k}", por_rol, cabecera, panel.PESO, panel.PESO_MAX_LOTE)


# -- validación de la salida del refutador ---------------------------------------------------------------------------
def _citas(d: dict, campo: str) -> list[dict]:
    v = d.get(campo) or []
    return v if isinstance(v, list) else []


def errores_cita(v: dict) -> str | None:
    """Return errors in a challenge quotation's source identity or literal anchor."""

    if not isinstance(v, dict) or not all((v.get(k) or "").strip() for k in ("fuente", "cita_literal", "dice")):
        return "cada cita es {fuente, cita_literal, dice}"
    r = verificar(v["fuente"], v["cita_literal"])
    if r["tipo"] != "primaria":
        return f"«{v['fuente'][:60]}» no es una fuente primaria (fila de la malla, objetivo o página de un documento)"
    if r["estado"] != "anclada":
        return (
            f"la cita «{v['cita_literal'][:50]}» no aparece en «{v['fuente'][:60]}»"
            + (f" (no existen: {', '.join(r['inexistentes'][:3])})" if r["inexistentes"] else "")
            + "; cópiala literal, en el idioma de la fuente, o quítala "
            '(compruébala con `uv run gskg bucle cita "<fuente>" "<cita>"`)'
        )
    return None


def errores_lote(lote: dict, salida: list[dict]) -> list[str]:
    """Validate one concise, source-anchored challenge verdict per dossier."""

    # Implementation notes:
    # encuentra en la fuente, contraevidencia anclada para debilitar o refutar, propuesta válida y patrón del error.
    exps = {x["id"]: x for x in lote["expedientes"]}
    ids = Counter(d.get("id") for d in salida)
    errores = [f"expediente sin veredicto {i}" for i in sorted(exps.keys() - ids.keys())]
    errores += [f"id fuera del lote {i}" for i in sorted(k for k in ids.keys() - exps.keys() if k)]
    errores += [f"id repetido {i}" for i, n in ids.items() if n > 1]
    maximo = panel.config()["palabras_justificacion"]
    for d in salida:
        x = exps.get(d.get("id"))
        if not x:
            continue
        pre = f"{d['id']}: "
        if d.get("veredicto") not in VEREDICTOS:
            errores.append(pre + f"veredicto {d.get('veredicto')!r} fuera de {list(VEREDICTOS)}")
            continue
        if not d.get("argumento") or panel._palabras(d["argumento"]) > maximo:
            errores.append(pre + f"argumento de 1 a {maximo} palabras")
        if d.get("confianza") not in panel.CONFIANZAS:
            errores.append(pre + "confianza alta, media o baja")
        for campo in ("contraevidencia", "anclas"):
            errores += [pre + f"{campo}: {e}" for v in _citas(d, campo) if (e := errores_cita(v))]
        impugna = d["veredicto"] != "se_sostiene"
        if impugna and d.get("patron") not in config()["patrones"]:
            errores.append(pre + f"patrón del error en {config()['patrones']}")
        if x["tipo"] == "contenido":
            cambios = d.get("cambios") or {}
            if d["veredicto"] == "refutada" and not cambios:
                errores.append(pre + "«refutada» en contenido exige «cambios» (campo → valor corregido)")
            if cambios and not impugna:
                errores.append(pre + "«se_sostiene» no lleva cambios")
            if cambios:
                errores += [
                    pre + e
                    for e in panel.errores_elemento_corregido(x["elemento_vigente"], cambios, x["campos_editables"])
                ]
            continue
        if impugna and not _citas(d, "contraevidencia"):
            errores.append(pre + f"«{d['veredicto']}» exige contraevidencia anclada en una fuente primaria")
        if d["veredicto"] == "refutada":
            prop = d.get("propuesta")
            if prop not in x["opciones"] or prop == x["resolucion"]["decision"] and x["tipo"] != "asignacion":
                errores.append(pre + f"«refutada» exige «propuesta» en {x['opciones']} distinta de la resolución")
    return errores


# -- cierre de la impugnación -----------------------------------------------------------------------------------------
def _leer_pares(carpeta: Path, patron: str, validar) -> list[tuple[dict, list[dict]]]:
    pares = []
    for p_lote in sorted(carpeta.glob(patron)):
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            raise ValueError(f"falta {p_sal.name}")
        lote, salida = (json.loads(x.read_text(encoding="utf-8")) for x in (p_lote, p_sal))
        if errs := validar(lote, salida):
            raise ValueError(f"{p_sal.name}: {len(errs)} errores: " + "; ".join(errs[:10]))
        pares.append((lote, salida))
    return pares


def _misma(d: dict, resolucion: dict) -> bool:
    return d["decision"] == resolucion["decision"] and (
        d["decision"] != "cambiar" or sorted(d.get("asignado_a") or []) == sorted(resolucion.get("asignado_a") or [])
    )


def cerrar_impugnacion(k: int, serie: str = "") -> dict:
    """Validate challenge and blind-probe outputs before resolving the complete cycle."""

    # Implementation notes:
    # - impugnada: el refutador debilita o refuta con confianza media o alta y con contraevidencia anclada (en
    # contenido,
    #   con un error y su corrección válida), o la sonda ciega no coincide con la resolución;
    # - sostenida: lo demás. Las anclas verificadas se suman al expediente.
    # Lo impugnado queda «pendiente_paso_1» de la réplica. Devuelve los conteos.
    estado = panel.cargar_estado()
    hoy = date.today().isoformat()
    for lote, salida in _leer_pares(_dir_lotes(), f"lote_b{k}{_s(serie)}_refutador_*.json", errores_lote):
        for d in salida:
            x = estado[d["id"]]
            v = _vuelta(x, k)
            if serie:
                v["serie"] = serie
            v["impugnacion"] = {
                **{
                    c: d[c]
                    for c in ("veredicto", "argumento", "confianza", "propuesta", "cambios", "patron")
                    if d.get(c)
                },
                "contraevidencia": [
                    {**c, "donde": verificar(c["fuente"], c["cita_literal"])["donde"]}
                    for c in _citas(d, "contraevidencia")
                ],
                "lote": lote["lote"],
                "fecha": hoy,
            }
            anclas = [
                {**a, "donde": verificar(a["fuente"], a["cita_literal"])["donde"], "vuelta": k}
                for a in _citas(d, "anclas")
            ]
            if anclas:
                b = x.setdefault("bucle", {})
                b["anclas"] = [a for a in b.get("anclas", []) if a.get("vuelta") != k] + anclas
            fuerte = d["confianza"] != "baja"
            if x["tipo"] == "contenido":
                impugnada = (
                    fuerte
                    and d["veredicto"] == "refutada"
                    or d["veredicto"] == "debilitada"
                    and fuerte
                    and bool(d.get("cambios"))
                )
            else:
                impugnada = fuerte and d["veredicto"] != "se_sostiene" and bool(_citas(d, "contraevidencia"))
            v["resultado"] = "impugnada" if impugnada else "sostenida"
    sonda_pares = _leer_pares(panel._dir_lotes(), f"lote_c{k}{_s(serie)}_*.json", panel.errores_lote)
    ciegos: dict[str, list[dict]] = defaultdict(list)
    for lote, salida in sonda_pares:
        ciegos_rol = [{**_resumen_dictamen(d), "rol": lote["rol"]} for d in salida]
        for d in ciegos_rol:
            ciegos[d["id"]].append(d)
    for i, ds in ciegos.items():
        x = estado[i]
        v = _vuelta(x, k)
        acuerdo = all(_misma(d, x["resolucion"]) for d in ds) and {d["rol"] for d in ds} == set(x["roles"])
        v["sonda"] = {"acuerdo": acuerdo, "dictamenes": ds}
        if not acuerdo:
            v["resultado"] = "impugnada"
        v.setdefault("resultado", "sostenida")
    for x in estado.values():
        for v in (x.get("bucle") or {}).get("vueltas", []):
            if v["vuelta"] == k and v.get("resultado") == "impugnada" and "replica" not in v:
                v["replica"] = "pendiente_paso_1"
    panel._guardar_estado(estado)
    return metricas(k)


# -- réplica ----------------------------------------------------------------------------------------------------------
PREGUNTA_REPLICA = (
    "Un revisor adversarial o una sonda ciega impugnó la resolución del panel (abajo, con su evidencia "
    "verificada en la fuente). Revísala contra la fuente: mantén la decisión vigente (elige la misma "
    "opción) si la impugnación no la derriba, o cámbiala. Explica por qué en la justificación."
)


def _pendientes(estado: dict, k: int, paso: int, serie: str = "") -> list[tuple[str, dict, dict]]:
    salida = []
    for i, x in sorted(estado.items()):
        v = next((v for v in (x.get("bucle") or {}).get("vueltas", []) if v["vuelta"] == k), None)
        if v and v.get("replica") == f"pendiente_paso_{paso}" and v.get("serie", "") == serie:
            salida.append((i, x, v))
    return salida


def _quienes_replica(x: dict, paso: int) -> list[str]:
    if x["tipo"] != "contenido":
        return x["roles"]
    return [x["etapas"][0][0]] if paso in (1, 3) else ["psicopedagogo"]


def replicar(k: int, paso: int, serie: str = "") -> list[str]:
    """Prepare role-specific response batches for challenged dossiers."""

    # Implementation notes:
    # Paso 1: todos los roles (en contenido, el experto). Paso 2: deliberación con las réplicas de los demás (en
    # contenido, el psicopedagogo revisa la corrección). Paso 3: solo contenido, visto bueno del experto.
    estado = panel.cargar_estado()
    ronda = 10 * k + paso
    por_rol: dict[str, list[dict]] = defaultdict(list)
    for i, x, v in _pendientes(estado, k, paso, serie):
        imp = {
            "impugnacion": v.get("impugnacion")
            if (v.get("impugnacion") or {}).get("veredicto") != "se_sostiene"
            else None,
            "sonda_ciega": v.get("sonda") if (v.get("sonda") or {}).get("acuerdo") is False else None,
        }
        for rol in _quienes_replica(x, paso):
            exp = {
                "id": i,
                "tipo": x["tipo"],
                "titulo": x["titulo"],
                "pregunta": PREGUNTA_REPLICA,
                "opciones": panel.config()["tipos"][x["tipo"]]["opciones"],
                "datos": x["datos"],
                "resolucion_vigente": x["resolucion"],
                "dictamenes_anteriores": [_resumen_dictamen(d) for d in _finales(x) if d["ronda"] < 10 * k],
                **{c: val for c, val in imp.items() if val},
            }
            if paso > 1:
                exp["replicas_de_esta_vuelta"] = [
                    _resumen_dictamen(d) for d in x["dictamenes"] if 10 * k < d["ronda"] < ronda
                ]
            if x["tipo"] == "contenido":
                exp["datos"] = {**x["datos"], "elemento": x.get("version_vigente") or x["datos"]["elemento"]}
                exp["campos_editables"] = panel.config()["campos_editables"][x["elemento"]]
                exp["etapa"] = {
                    1: "réplica: exactitud científica (experto)",
                    2: "réplica: revisión psicopedagógica",
                    3: "réplica: visto bueno final del experto",
                }[paso]
            por_rol[rol].append(exp)

    def cabecera(rol: str) -> dict:
        return {
            "ronda": ronda,
            "rol": rol,
            "version": panel.VERSION,
            "replica_del_bucle": k,
            "instrucciones": [
                "prompts/panel_dictaminar.md",
                f".claude/agents/{rol}.md",
                "prompts/bucle_refutar.md (sección «Réplica»)",
            ],
        }

    return _escribir_lotes(
        panel._dir_lotes(), f"r{ronda}{_s(serie)}", por_rol, cabecera, panel.PESO, panel.PESO_MAX_LOTE
    )


def _cambiar_resolucion(x: dict, nueva: dict, k: int) -> None:
    x.setdefault("historial_resoluciones", []).append({**x["resolucion"], "reemplazada_por_bucle": k})
    x["resolucion"] = nueva
    x["aplicado"] = None


def cerrar_replica(k: int, paso: int, serie: str = "") -> dict:
    """Consolidate all valid responses under the panel's documented resolution rules."""

    # Implementation notes:
    # - confianza baja de cualquier rol → «sin consenso» (una persona decide);
    # - en paralelo: unanimidad → mantiene o cambia la resolución; si no, deliberación (paso 2) y, si sigue sin
    #   unanimidad, «sin consenso»;
    # - contenido: experto → psicopedagogo (si el experto corrigió) → experto (si el psicopedagogo corrigió).
    # Devuelve los conteos de la vuelta.
    estado = panel.cargar_estado()
    ronda = 10 * k + paso
    hoy = date.today().isoformat()
    nuevos = []
    for lote, salida in _leer_pares(panel._dir_lotes(), f"lote_r{ronda}{_s(serie)}_*.json", panel.errores_lote):
        nuevos += [{**d, "ronda": ronda, "rol": lote["rol"], "fecha": hoy, "bucle": k} for d in salida]
    for d in nuevos:
        x = estado[d["id"]]
        x["dictamenes"] = [v for v in x["dictamenes"] if not (v["ronda"] == ronda and v["rol"] == d["rol"])] + [d]
    for i in sorted({d["id"] for d in nuevos}):
        x = estado[i]
        v = _vuelta(x, k)
        de_paso = [d for d in x["dictamenes"] if d["ronda"] == ronda]
        if any(d["confianza"] == "baja" for d in de_paso):
            x["estado"], v["replica"] = "sin_consenso", "sin_consenso"
            x["motivo"] = f"réplica del bucle {k}: confianza baja de " + ", ".join(
                d["rol"] for d in de_paso if d["confianza"] == "baja"
            )
            continue
        if x["tipo"] == "contenido":
            d = de_paso[0]
            if d["decision"] == "corregir":
                x["version_vigente"] = {**(x.get("version_vigente") or x["datos"]["elemento"]), **d["cambios"]}
                v["corregida"] = True
            fin = d["decision"] == "aprobar" or paso == 3
            if not fin:
                v["replica"] = f"pendiente_paso_{paso + 1}"
            elif v.get("corregida"):
                v["replica"] = "cambiada"
                _cambiar_resolucion(x, {"decision": "corregir", "ronda": ronda}, k)
            else:
                v["replica"] = "mantenida"
            continue
        if {d["rol"] for d in de_paso} != set(x["roles"]):
            continue
        claves = {panel._clave_decision(d) for d in de_paso}
        if len(claves) == 1:
            nueva = {
                "decision": de_paso[0]["decision"],
                "ronda": ronda,
                **({"asignado_a": de_paso[0]["asignado_a"]} if de_paso[0].get("asignado_a") else {}),
            }
            if _misma(de_paso[0], x["resolucion"]):
                v["replica"] = "mantenida"
                x["resolucion"]["mantenida_en_bucle"] = k
            else:
                v["replica"] = "cambiada"
                _cambiar_resolucion(x, nueva, k)
        elif paso == 1:
            v["replica"] = "pendiente_paso_2"
        else:
            x["estado"], v["replica"] = "sin_consenso", "sin_consenso"
            x["motivo"] = f"réplica del bucle {k} sin unanimidad: " + "; ".join(
                f"{d['rol']} {d['decision']}" for d in de_paso
            )
    for x in estado.values():
        if x["estado"] in ("resuelta", "sin_consenso") and x["tipo"] != "piloto":
            x.setdefault("bucle", {})["solidez"], x["bucle"]["motivo_solidez"] = _solidez(x)
    panel._guardar_estado(estado)
    return metricas(k)


# -- solidez y métricas -----------------------------------------------------------------------------------------------
def _solidez(x: dict) -> tuple[str, str]:
    """Return the evidence-strength label and its supporting reason."""

    # Implementation notes:
    # sobrevivió, pero la fuente solo está ubicada (paráfrasis); frágil: sin fuente primaria verificable, con una fuente
    # inexistente, inestable en la sonda o cambiado en la última vuelta sin nueva impugnación.
    if x["estado"] == "sin_consenso":
        if dd := x.get("decision_delegada"):
            return "delegada", (
                f"el panel no llegó a consenso ({x.get('motivo', '')}); decidió el responsable por "
                f"delegación: {dd['decision']} (pendiente de confirmar)"
            )
        return "sin_consenso", x.get("motivo", "")
    b = x.get("bucle") or {}
    vueltas = sorted(b.get("vueltas", []), key=lambda v: v["vuelta"])
    if not vueltas or not any(v.get("resultado") for v in vueltas):
        return "sin_bucle", "no pasó por el bucle"
    ult = vueltas[-1]
    if str(ult.get("replica", "")).startswith("pendiente") or (ult.get("resultado") is None and ult.get("sonda")):
        return "en_bucle", "réplica pendiente"
    if ult.get("replica") == "cambiada":
        return "fragil", f"cambió en la vuelta {ult['vuelta']} y no se volvió a impugnar"
    # La sonda se compara con la resolución VIGENTE: si la réplica corrigió el dictamen y llegó a lo mismo que la sonda
    # dictaminó a ciegas, eso corrobora; solo es inestable si la sonda discrepa de lo que quedó.
    ciega = next((v["sonda"]["dictamenes"] for v in vueltas if (v.get("sonda") or {}).get("dictamenes")), None)
    inestable = ciega is not None and not all(_misma(d, x["resolucion"]) for d in ciega)
    corroborada = (
        ciega is not None and not inestable and any((v.get("sonda") or {}).get("acuerdo") is False for v in vueltas)
    )
    if x["tipo"] == "contenido":
        return (
            ("respaldado", "la mantuvo la réplica tras una impugnación")
            if ult.get("replica") == "mantenida"
            else ("solido", "el revisor adversarial no encontró errores")
        )
    a = anclaje(x)
    b["anclaje"] = a
    contestada = any(
        v.get("replica") == "mantenida" and v.get("impugnacion", {}).get("veredicto") != "se_sostiene" for v in vueltas
    )
    if a["inexistentes"]:
        return "fragil", "cita una fuente que no existe: " + ", ".join(a["inexistentes"][:3])
    if a["nivel"] == "sin_fuente_primaria":
        return "fragil", "sin fuente primaria verificable (solo argumentos o fuentes internas)"
    if inestable:
        return "respaldado", "inestable: la sonda ciega dictaminó otra opción que la resolución vigente"
    if contestada:
        return "respaldado", "hay contraevidencia anclada; la réplica la ponderó y mantuvo la decisión"
    if a["nivel"] == "anclado":
        if corroborada:
            return "solido", (
                "la réplica corrigió el dictamen y llegó a lo mismo que la sonda ciega; cita literal "
                "verificada en la fuente"
            )
        return "solido", "sobrevivió a la impugnación, con cita literal verificada en la fuente"
    return "respaldado", "sobrevivió a la impugnación; la fuente existe, pero la cita no es literal"


def solidez() -> dict:
    """Recompute dossier strength after panel review, excluding the pilot."""
    estado = panel.cargar_estado()
    conteo: dict[str, Counter] = defaultdict(Counter)
    for x in estado.values():
        if x["estado"] in ("resuelta", "sin_consenso") and x["tipo"] != "piloto":
            s, motivo = _solidez(x)
            x.setdefault("bucle", {}).update({"solidez": s, "motivo_solidez": motivo})
            conteo[x["tipo"]][s] += 1
    panel._guardar_estado(estado)
    return {t: dict(c) for t, c in sorted(conteo.items())}


def metricas(k: int | None = None) -> dict:
    """Measure challenge outcomes, decision changes, and remaining disagreement."""

    # Implementation notes:
    # acuerdo de la sonda ciega por tipo y patrones de error.
    estado = panel.cargar_estado()
    m: Counter = Counter()
    sonda_tipo: dict[str, Counter] = defaultdict(Counter)
    patrones: Counter = Counter()
    for x in estado.values():
        for v in (x.get("bucle") or {}).get("vueltas", []):
            if k is not None and v["vuelta"] != k:
                continue
            if imp := v.get("impugnacion"):
                m[f"refutador_{imp['veredicto']}"] += 1
                if v.get("resultado") == "impugnada" and imp["veredicto"] != "se_sostiene":
                    patrones[imp.get("patron", "otro")] += 1
            if v.get("resultado"):
                m[v["resultado"]] += 1
            if v.get("replica"):
                m[f"replica_{v['replica']}"] += 1
            if (s := v.get("sonda")) and "acuerdo" in s:
                sonda_tipo[x["tipo"]]["acuerdo" if s["acuerdo"] else "discrepa"] += 1
    return {
        "vuelta": k,
        **dict(sorted(m.items())),
        "sonda": {t: dict(c) for t, c in sorted(sonda_tipo.items())},
        "patrones": dict(patrones.most_common()),
    }


# -- informe ----------------------------------------------------------------------------------------------------------
ETIQUETA = {
    "solido": "sólido",
    "respaldado": "respaldado",
    "fragil": "frágil",
    "delegada": "delegada",
    "sin_consenso": "sin consenso",
    "en_bucle": "en el bucle",
    "sin_bucle": "sin bucle",
}


def seccion_informe(estado: dict) -> list[str]:
    """Render the strengthening section or return an empty string before execution."""
    if not any((x.get("bucle") or {}).get("vueltas") for x in estado.values()):
        return []
    md = [
        "",
        "## Bucle de fortalecimiento (spec 14, sección 7)",
        "",
        "Cada dictamen resuelto pasó por un revisor adversarial que buscó en las fuentes la prueba en contra; una "
        "muestra se volvió a dictaminar a ciegas. Solo la contraevidencia que el código encuentra literal en la "
        "fuente reabre un expediente. **Sólido:** sobrevivió y tiene una cita literal verificada en una fuente "
        "primaria. **Respaldado:** sobrevivió, pero su fuente solo está ubicada (paráfrasis o traducción). "
        "**Frágil:** sin fuente primaria verificable, con una fuente inexistente o cambiado sin nueva impugnación.",
        "**Delegada:** el panel no llegó a consenso y decidió el responsable con evidencia (pendiente de confirmar).",
        "",
        "| Tipo | Sólido | Respaldado | Frágil | Delegada | Sin consenso |",
        "|---|---|---|---|---|---|",
    ]
    por_tipo: dict[str, Counter] = defaultdict(Counter)
    for x in estado.values():
        if s := (x.get("bucle") or {}).get("solidez"):
            por_tipo[x["tipo"]][s] += 1
    for t, c in sorted(por_tipo.items()):
        md.append(
            f"| {t} | {c['solido']} | {c['respaldado']} | {c['fragil']} | {c['delegada']} | {c['sin_consenso']} |"
        )
    vueltas = sorted({v["vuelta"] for x in estado.values() for v in (x.get("bucle") or {}).get("vueltas", [])})
    md += [
        "",
        "| Vuelta | Impugnados | Sostenidos | Réplica: mantenidos | Réplica: cambiados | Réplica: sin consenso |",
        "|---|---|---|---|---|---|",
    ]
    for k in vueltas:
        m = metricas(k)
        md.append(
            f"| {k} | {m.get('impugnada', 0)} | {m.get('sostenida', 0)} | {m.get('replica_mantenida', 0)} | "
            f"{m.get('replica_cambiada', 0)} | {m.get('replica_sin_consenso', 0)} |"
        )
    total = metricas()
    if total["sonda"]:
        md += [
            "",
            "**Sonda ciega** (el mismo rol, sin ver la resolución): "
            + "; ".join(
                f"{t} {c.get('acuerdo', 0)}/{c.get('acuerdo', 0) + c.get('discrepa', 0)}"
                for t, c in total["sonda"].items()
            )
            + " coinciden.",
        ]
    if total["patrones"]:
        md += [
            "",
            "**Patrones de error de lo impugnado:** "
            + ", ".join(f"{p} {n}" for p, n in total["patrones"].items())
            + ".",
        ]
    cambios = [(i, x) for i, x in sorted(estado.items()) if x.get("historial_resoluciones")]
    if cambios:
        md += ["", "**Lo que el bucle cambió:**", "", "| Expediente | Antes | Ahora | Por qué |", "|---|---|---|---|"]
        for _i, x in cambios:
            antes = x["historial_resoluciones"][-1]["decision"]
            v = max(x["bucle"]["vueltas"], key=lambda v: v["vuelta"])
            por = (v.get("impugnacion") or {}).get("argumento") or "discrepancia de la sonda ciega"
            md.append(
                f"| {panel._celda(x['titulo'], 90)} | {antes} | {x['resolucion']['decision']} | "
                f"{panel._celda(panel._texto_final(x) or por, 300)} |"
            )
    frageles = [
        (i, x)
        for i, x in sorted(estado.items())
        if (x.get("bucle") or {}).get("solidez") == "fragil"
        and x["tipo"] in ("hallazgo", "decision", "clase_incierta", "propuesta")
    ]
    if frageles:
        md += [
            "",
            f"**Frágiles en hallazgos, decisiones, clases y propuestas ({len(frageles)}):** necesitan una "
            "fuente primaria antes de llevarse al MINED como recomendación.",
            "",
        ]
        md += [
            f"- {panel._celda(x['titulo'], 110)}: {panel._celda(x['bucle']['motivo_solidez'], 160)}"
            for _i, x in frageles
        ]
    return md


# -- snapshots por ciencia --------------------------------------------------------------------------------------------
CIENCIAS = {
    "biologia": "Biología",
    "fisica": "Física",
    "quimica": "Química",
    "tierra-espacio": "Ciencias de la Tierra y del Espacio",
}
TIPOS = {
    "decision": "decisiones de contenido",
    "asignacion": "asignaciones de concepto",
    "cambio_asignatura": "asignatura de temas",
    "hallazgo": "hallazgos del contraste",
    "propuesta": "propuestas curriculares",
    "clase_incierta": "clases del contraste de 2.°–8.°",
    "contenido": "capa pedagógica",
}


def _ultima(x: dict) -> dict:
    vueltas = (x.get("bucle") or {}).get("vueltas") or [{}]
    return max(vueltas, key=lambda v: v.get("vuelta", 0))


def _cambios_del_bucle(x: dict) -> tuple[str, str] | None:
    """Return prior and current states when a challenge changed a dossier."""
    hist = [h for h in x.get("historial_resoluciones", []) if h.get("reemplazada_por_bucle")]
    if not hist:
        return None
    antes, ahora = hist[0]["decision"], x["resolucion"]["decision"]
    return antes, ahora if ahora != antes else f"{ahora} (nueva versión)"


def snapshot(etapa: str) -> list[str]:
    """Write subject-specific strengthening snapshots and their summary."""

    # Implementation notes:
    # regeneran en cada etapa y se versionan: el historial de git guarda cada corte.
    estado = panel.cargar_estado()
    for x in estado.values():  # solidez al día
        if x["estado"] in ("resuelta", "sin_consenso") and x["tipo"] != "piloto":
            s, motivo = _solidez(x)
            x.setdefault("bucle", {}).update({"solidez": s, "motivo_solidez": motivo})
    hoy = date.today().isoformat()
    d = ruta("panel/bucle")
    d.mkdir(parents=True, exist_ok=True)
    por_ciencia: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    for i, x in sorted(estado.items()):
        if x["tipo"] != "piloto" and x["estado"] in ("resuelta", "sin_consenso"):  # también lo que aún no pasó
            por_ciencia[_disciplina(x)].append((i, x))
    escritos, filas_resumen = [], []
    for clave, nombre in CIENCIAS.items():
        exps = por_ciencia.get(clave, [])
        c: Counter = Counter()
        for _i, x in exps:
            v = _ultima(x)
            c["expedientes"] += 1
            c["anclas"] += len((x.get("bucle") or {}).get("anclas", []))
            c[f"solidez_{x['bucle'].get('solidez')}"] += 1
            for w in x["bucle"].get("vueltas", []):
                c["impugnados"] += w.get("resultado") == "impugnada"
                c["cambiados"] += w.get("replica") == "cambiada"
                c["mantenidos"] += w.get("replica") == "mantenida"
                if (s := w.get("sonda")) and "acuerdo" in s:
                    c["sonda"] += 1
                    c["sonda_acuerdo"] += bool(s["acuerdo"])
            c["en_bucle"] += str(v.get("replica", "")).startswith("pendiente")
        md = [
            f"# Reforzamiento de {nombre}: snapshot",
            "",
            f"> Generado por `uv run gskg bucle snapshot` el {hoy}, etapa: **{etapa}**. Bucle de fortalecimiento de "
            "los dictámenes del panel de expertos IA (spec 14, sección 7). Estos son dictámenes del panel, **no "
            "confirmaciones del MINED**. Cada corte queda en el historial de git de este archivo.",
            "",
            "| Expedientes | Impugnados (reabiertos) | Cambiados por la réplica | Mantenidos | Anclas literales "
            "nuevas | Sonda ciega (coinciden) | En el bucle |",
            "|---|---|---|---|---|---|---|",
            f"| {c['expedientes']} | {c['impugnados']} | {c['cambiados']} | {c['mantenidos']} | {c['anclas']} | "
            f"{c['sonda_acuerdo']}/{c['sonda']} | {c['en_bucle']} |",
            "",
            "## Solidez por tipo",
            "",
            "| Tipo | Sólido | Respaldado | Frágil | Delegada | Sin consenso | En el bucle |",
            "|---|---|---|---|---|---|---|",
        ]
        por_tipo: dict[str, Counter] = defaultdict(Counter)
        for _i, x in exps:
            por_tipo[x["tipo"]][x["bucle"].get("solidez")] += 1
        md += [
            f"| {TIPOS.get(t, t)} | {k['solido']} | {k['respaldado']} | {k['fragil']} | {k['delegada']} | "
            f"{k['sin_consenso']} | {k['en_bucle']} |"
            for t, k in sorted(por_tipo.items())
        ]
        cambios = [(i, x, ch) for i, x in exps if (ch := _cambios_del_bucle(x))]
        if cambios:
            md += [
                "",
                "## Lo que el bucle cambió",
                "",
                "| Expediente | Antes | Ahora | Por qué (revisor adversarial) |",
                "|---|---|---|---|",
            ]
            for _i, x, (antes, ahora) in cambios:
                imp = (
                    next(
                        (
                            w.get("impugnacion")
                            for w in x["bucle"].get("vueltas", [])
                            if w.get("resultado") == "impugnada"
                            and (w.get("impugnacion") or {}).get("veredicto") != "se_sostiene"
                        ),
                        None,
                    )
                    or {}
                )
                por = imp.get("argumento") or "discrepancia de la sonda ciega"
                md.append(f"| {panel._celda(x['titulo'], 80)} | {antes} | {ahora} | {panel._celda(por, 260)} |")
        contestados = [
            (i, x)
            for i, x in exps
            if x["bucle"].get("solidez") == "respaldado" and "contraevidencia" in x["bucle"].get("motivo_solidez", "")
        ]
        if contestados:
            md += ["", "## Mantenidos frente a contraevidencia anclada (la réplica la ponderó)", ""]
            md += [f"- {panel._celda(x['titulo'], 100)}" for _i, x in contestados]
        frageles = [(i, x) for i, x in exps if x["bucle"].get("solidez") in ("fragil", "delegada", "sin_consenso")]
        if frageles:
            md += ["", "## Frágiles, sin consenso o decididos por delegación (pendientes de confirmar)", ""]
            md += [
                f"- {panel._celda(x['titulo'], 100)}: {panel._celda(x['bucle'].get('motivo_solidez'), 160)}"
                for _i, x in frageles
            ]
        pat = Counter(
            (w.get("impugnacion") or {}).get("patron")
            for _i, x in exps
            for w in x["bucle"].get("vueltas", [])
            if w.get("resultado") == "impugnada" and (w.get("impugnacion") or {}).get("patron")
        )
        if pat:
            md += [
                "",
                "**Patrones de error de lo impugnado:** " + ", ".join(f"{p} {n}" for p, n in pat.most_common()) + ".",
            ]
        p = d / f"{clave}.md"
        p.write_text("\n".join(md) + "\n", encoding="utf-8")
        escritos.append(relativa(p))
        filas_resumen.append(
            f"| [{nombre}]({clave}.md) | {c['expedientes']} | {c['impugnados']} | {c['cambiados']} | "
            f"{c['solidez_solido']} | {c['solidez_respaldado']} | {c['solidez_fragil']} | "
            f"{c['solidez_delegada']} | {c['solidez_sin_consenso']} | {c['solidez_sin_bucle']} |"
        )
    resumen = [
        "# Reforzamiento por ciencia: resumen del snapshot",
        "",
        f"> Generado por `uv run gskg bucle snapshot` el {hoy}, etapa: **{etapa}**. Diseño y reglas: "
        "`specs/14_panel_expertos.md`, sección 7; narrativa: `panel/bucle/README.md`.",
        "",
        "| Ciencia | Expedientes | Impugnados | Cambiados | Sólidos | Respaldados | Frágiles | Delegadas | "
        "Sin consenso | Sin bucle |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *filas_resumen,
    ]
    p = d / "RESUMEN.md"
    p.write_text("\n".join(resumen) + "\n", encoding="utf-8")
    panel._guardar_estado(estado)
    return [relativa(p), *escritos, *snapshot_grados(etapa)]


# -- snapshot por grado ------------------------------------------------------------------------------------------------
_RE_GRADO_TEMA = re.compile(r"\bG(\d\d)-[A-Z]{3}-U\d+")
_RE_GRADO_TEXTO = re.compile(r"(\d{1,2})\.°(?:\s*[–-]\s*(\d{1,2})\.°)?")
# Documentos que reúnen varios grados: los tramos del contraste internacional (specs 11 y 12).
SNAPSHOTS_POR_TRAMO = {"9-11": (11, 10, 9), "2-8": (8, 7, 6, 5, 4, 3, 2)}
NOTA_SOLIDEZ = (
    "**Cómo leer la solidez.** «Sólido» quiere decir que el dictamen sobrevivió a un revisor adversarial "
    "y que una cita literal de una fuente primaria lo apoya; no prueba que la interpretación sea la "
    "correcta. La estabilidad solo se midió en la muestra de la sonda ciega (63 de 486). Todos son "
    "dictámenes del panel de expertos IA, **no confirmaciones del MINED**."
)


@cache
def _contraste_vigente() -> dict[tuple[str, str], dict]:
    """Index the current contrast by grade band and concept."""
    salida = {}
    for tramo, archivo in (("9_11", "internacional/contraste.json"), ("2_8", "internacional/2_8/contraste.json")):
        p = ruta(archivo)
        if p.exists():
            for f in json.loads(p.read_text(encoding="utf-8"))["filas"]:
                salida[(tramo, f["concepto"])] = f
    return salida


def _concepto_y_tramo(x: dict) -> tuple[str, str] | None:
    d = x.get("datos") or {}
    if x["tipo"] == "clase_incierta":
        return d.get("tramo", "2_8"), d["concepto"]["id"]
    if x.get("subtipo") in ("clase_internacional", "clase_internacional_2_8"):
        return ("9_11" if x["subtipo"] == "clase_internacional" else "2_8"), d["conceptos"][0]["id"]
    return None


def _grados_texto(texto: str) -> set[int]:
    grados = set()
    for a, b in _RE_GRADO_TEXTO.findall(texto):
        a, b = int(a), int(b or a)
        grados |= {g for g in range(a, b + 1) if 2 <= g <= 11}
    return grados


def grados_de(i: str, x: dict) -> list[int]:
    """Return curriculum grades associated with a dossier, when explicitly known."""

    # Implementation notes:
    # objetivo de otro país o un hallazgo de todo un tramo (ver tramo_de).
    d = x.get("datos") or {}
    if x["tipo"] == "contenido":
        return [g] if (g := (d.get("objetivo") or {}).get("grado")) else []
    if x["tipo"] in ("cambio_asignatura", "asignacion"):
        m = _RE_GRADO_TEMA.search(i.rsplit("::", 1)[-1])  # solo los temas de la malla tienen grado propio
        return [int(m[1])] if m else []
    if x["tipo"] == "propuesta":
        return [g] if (g := d.get("grado_propuesto")) else []
    if ct := _concepto_y_tramo(x):
        g = (_contraste_vigente().get(ct) or {}).get("sv_primer_grado")
        return [int(g)] if isinstance(g, (int, float)) else []
    if x["tipo"] == "hallazgo":
        texto = " ".join(str(d.get(k, "")) for k in ("evidencia", "recomendacion"))
        grados = {int(m) for m in _RE_GRADO_TEMA.findall(texto)} | _grados_texto(d.get("titulo", ""))
        return sorted(grados)
    return []


def tramo_de(i: str, x: dict) -> str | None:
    """Return the native grade band for dossiers without a local curriculum grade."""
    if grados_de(i, x):
        return None
    if x["tipo"] == "asignacion":
        o = _objetivos().get(i.rsplit("::", 1)[-1], {})
        lo = o.get("grado_sv_min") or o.get("grado_min")
        return ("9-11" if int(lo) >= 9 else "2-8") if lo else None
    if x["tipo"] == "hallazgo":
        return {"9_11": "9-11", "2_8": "2-8"}.get((x.get("datos") or {}).get("tramo"))
    return None


def _n(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def snapshot_grados(etapa: str) -> list[str]:
    """Write grade-specific strengthening snapshots and band summaries."""

    # Implementation notes:
    # revisó, cambió y dejó en cada grado de la malla. Los objetivos de otros países y los hallazgos de todo un tramo no
    # tienen grado de la malla: van una sola vez, en la sección «Del tramo» del documento del tramo.
    estado = panel.cargar_estado()
    hoy = date.today().isoformat()
    d = ruta("panel/bucle/grados")
    d.mkdir(parents=True, exist_ok=True)
    por_grado: dict[int, list[tuple[str, dict]]] = defaultdict(list)
    del_tramo: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    transversales, total = [], 0
    for i, x in sorted(estado.items()):
        if x["tipo"] == "piloto" or x["estado"] not in ("resuelta", "sin_consenso"):
            continue
        total += 1
        if gs := grados_de(i, x):
            for g in gs:
                por_grado[g].append((i, x))
        elif t := tramo_de(i, x):
            del_tramo[t].append((i, x))
        else:
            transversales.append((i, x))

    def titulo(i: str, x: dict) -> str:
        t = x["titulo"]
        if x["tipo"] == "asignacion":
            t = f"[{i.split('::')[1].replace('_', ' ')}] {t}"
        return t

    def resolucion(x: dict) -> str:
        if x["estado"] != "resuelta":
            dd = x.get("decision_delegada")
            return f"delegada: {dd['decision']}" if dd else x["estado"].replace("_", " ")
        r = x["resolucion"]["decision"]
        if (ct := _concepto_y_tramo(x)) and x["tipo"] == "decision":
            clase = (_contraste_vigente().get(ct) or {}).get("clase")
            return f"{r} (clase vigente: {clase})" if clase else r
        return r

    def apoyo(x: dict) -> str:
        b = x["bucle"]
        if a := (b.get("anclas") or [None])[0]:
            return f"{a.get('dice', '')} — «{a.get('cita_literal', '')[:90]}» ({a.get('donde') or a.get('fuente')})"
        return f"sin cita del revisor; {b.get('motivo_solidez', '')}"

    def fila(i: str, x: dict, extra: str) -> str:
        return (
            f"| {TIPOS.get(x['tipo'], x['tipo'])} | {panel._celda(titulo(i, x), 95)} | {resolucion(x)} | "
            f"{ETIQUETA.get(x['bucle'].get('solidez'), '—')} | {panel._celda(extra, 260)} |"
        )

    def secciones(exps: list[tuple[str, dict]], nivel: str = "###") -> list[str]:
        orden = sorted(exps, key=lambda e: (e[1]["tipo"], e[1]["titulo"]))
        cab = "| Tipo | Expediente | Resolución | Solidez | {} |"
        sep = "|---|---|---|---|---|"
        md = []
        cambiados = [(i, x) for i, x in orden if _cambios_del_bucle(x)]
        if cambiados:
            md += [
                f"{nivel} Lo que el bucle cambió",
                "",
                cab.format("Antes → ahora y por qué (réplica del panel)"),
                sep,
            ]
            md += [
                fila(i, x, f"{_cambios_del_bucle(x)[0]} → {_cambios_del_bucle(x)[1]}. {panel._texto_final(x)}")
                for i, x in cambiados
            ]
            md.append("")
        mantenidos = [
            (i, x)
            for i, x in orden
            if not _cambios_del_bucle(x) and any(v.get("replica") == "mantenida" for v in x["bucle"].get("vueltas", []))
        ]
        if mantenidos:
            md += [
                f"{nivel} Reabiertos y mantenidos por la réplica",
                "",
                cab.format("Impugnación → respuesta del panel"),
                sep,
            ]
            for i, x in mantenidos:
                imp = next(
                    (
                        (v.get("impugnacion") or {}).get("argumento") or "discrepancia de la sonda ciega"
                        for v in x["bucle"]["vueltas"]
                        if v.get("replica") == "mantenida"
                    ),
                    "",
                )
                md.append(fila(i, x, f"{panel._celda(imp, 130)} → {panel._texto_final(x)}"))
            md.append("")
        debiles = [(i, x) for i, x in orden if x["bucle"].get("solidez") in ("fragil", "delegada", "sin_consenso")]
        if debiles:
            md += [
                f"{nivel} Frágiles, sin consenso o decididos por delegación (pendientes de confirmar)",
                "",
                cab.format("Motivo y decisión"),
                sep,
            ]
            md += [
                fila(
                    i,
                    x,
                    f"{x['bucle'].get('motivo_solidez', '')}. "
                    f"{(x.get('decision_delegada') or {}).get('justificacion', '')}",
                )
                for i, x in debiles
            ]
            md.append("")
        md += [
            f"{nivel} Detalle: todos los dictámenes",
            "",
            cab.format("Apoyo: qué dice la cita literal verificada y dónde"),
            sep,
        ]
        md += [fila(i, x, apoyo(x)) for i, x in orden]
        return md

    def conteo(exps: list[tuple[str, dict]]) -> tuple[Counter, int]:
        return Counter(x["bucle"].get("solidez") for _i, x in exps), sum(bool(_cambios_del_bucle(x)) for _i, x in exps)

    def linea(exps: list[tuple[str, dict]]) -> str:
        c, cambiados = conteo(exps)
        return (
            f"{_n(len(exps), 'dictamen', 'dictámenes')}: {_n(cambiados, 'cambiado', 'cambiados')} por el bucle; "
            f"{_n(c['solido'], 'sólido', 'sólidos')}, {_n(c['respaldado'], 'respaldado', 'respaldados')}, "
            f"{_n(c['fragil'], 'frágil', 'frágiles')}, {_n(c['delegada'], 'delegado', 'delegados')}, "
            f"{c['sin_consenso']} sin consenso y {c['sin_bucle']} que aún no pasan por el bucle."
        )

    def fila_resumen(etiqueta: str, exps: list[tuple[str, dict]]) -> str:
        c, cambiados = conteo(exps)
        return (
            f"| {etiqueta} | {len(exps)} | {cambiados} | {c['solido']} | {c['respaldado']} | {c['fragil']} | "
            f"{c['delegada']} | {c['sin_consenso']} | {c['sin_bucle']} |"
        )

    aviso = (
        f"> Generado por `uv run gskg bucle snapshot` el {hoy}, etapa: **{etapa}**. Cada dictamen se ubica en el "
        "grado de la malla al que corresponde: el tema, el objetivo del contenido o el primer grado de la V2 en "
        "el contraste vigente. Un hallazgo que menciona varios grados aparece en cada uno; los objetivos de otros "
        "países y los hallazgos de todo un tramo van una sola vez, en la sección «Del tramo»."
    )
    encabezado = (
        "| {} | Dictámenes | Cambiados | Sólidos | Respaldados | Frágiles | Delegados | Sin consenso | Sin bucle |"
    )
    escritos = []
    for g in sorted(por_grado, reverse=True):
        md = [
            f"# Reforzamiento por grado: {g}.°",
            "",
            aviso,
            "",
            NOTA_SOLIDEZ,
            "",
            linea(por_grado[g]),
            "",
            *secciones(por_grado[g], "##"),
        ]
        p = d / f"G{g:02d}.md"
        p.write_text("\n".join(md) + "\n", encoding="utf-8")
        escritos.append(relativa(p))
    resumen = [
        "# Reforzamiento por grado: resumen",
        "",
        aviso,
        "",
        NOTA_SOLIDEZ,
        "",
        encabezado.format("Grado"),
        "|---|---|---|---|---|---|---|---|---|",
    ]
    resumen += [fila_resumen(f"[{g}.°](G{g:02d}.md)", por_grado[g]) for g in sorted(por_grado, reverse=True)]
    resumen += [
        fila_resumen(f"Del tramo {t.replace('-', '.°–')}.° (sin grado de la malla)", del_tramo[t])
        for t in SNAPSHOTS_POR_TRAMO
        if del_tramo.get(t)
    ]
    resumen += [
        fila_resumen("Transversales (conceptos, sin grado)", transversales),
        "",
        f"**Total sin duplicar:** {total} dictámenes. La suma de las filas es mayor porque un hallazgo puede "
        "estar en varios grados.",
    ]
    p = d / "RESUMEN.md"
    p.write_text("\n".join(resumen) + "\n", encoding="utf-8")
    escritos.insert(0, relativa(p))
    for nombre, grados in SNAPSHOTS_POR_TRAMO.items():  # un documento por tramo, del grado mayor al menor
        presentes = [g for g in grados if g in por_grado]
        junto = [
            f"# Reforzamiento de {grados[0]}.° a {grados[-1]}.°: snapshot",
            "",
            aviso,
            "",
            NOTA_SOLIDEZ,
            "",
            encabezado.format("Grado"),
            "|---|---|---|---|---|---|---|---|---|",
        ]
        junto += [fila_resumen(f"[{g}.°](#{g}-grado)", por_grado[g]) for g in presentes]
        if del_tramo.get(nombre):
            junto.append(fila_resumen("[Del tramo](#del-tramo-sin-grado-de-la-malla)", del_tramo[nombre]))
        junto.append("")
        for g in presentes:
            junto += [f"## {g}.° grado", "", linea(por_grado[g]), "", *secciones(por_grado[g]), ""]
        if del_tramo.get(nombre):
            junto += [
                "## Del tramo (sin grado de la malla)",
                "",
                "Objetivos de otros países asignados a una versión de un concepto, y hallazgos de todo el tramo.",
                "",
                linea(del_tramo[nombre]),
                "",
                *secciones(del_tramo[nombre]),
                "",
            ]
        p = ruta(f"panel/bucle/SNAPSHOT_{nombre}.md")
        p.write_text("\n".join(junto) + "\n", encoding="utf-8")
        escritos.insert(0, relativa(p))
    return escritos
