"""Extrae y valida los objetivos de aprendizaje de los currículos de países (spec 11).

Cada documento de `config/internacional.yaml` se recorre en ventanas de pocas páginas. Gemini lee el PDF de la
ventana directamente, lo que funciona igual en japonés, coreano, chino o con tablas, y devuelve los objetivos
con su página. Un segundo modelo, distinto del primero, revisa cada objetivo contra las mismas páginas:
- «no_fiel»: se descarta.
- «parcial»: se conserva marcado para revisión humana.

Los HTML (ACARA, Ontario) se convierten a texto y se parten en secciones del mismo tamaño.
Salida: data/interim/internacional/objetivos/<pais>.json, ordenada y con ids estables.
"""

from __future__ import annotations

import html as html_mod
import io
import json
import re
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from goes_science_kg.config import cargar, ruta
from goes_science_kg.internacional import vertex

DIR_SALIDA = "data/interim/internacional/objetivos"
VERSION = "internacional-v1"
VENTANA = 2
CARACTERES_SECCION = 12000
CODIGO_ASIG = {"fisica": "FIS", "quimica": "QUI", "biologia": "BIO", "tierra_espacio": "TYE",
               "ciencias_integradas": "CIN"}

SISTEMA = (
    "Eres un especialista en currículo de ciencias. Extraes objetivos de aprendizaje de documentos curriculares "
    "oficiales con total fidelidad: no agregas nada que el documento no diga y no omites objetivos."
)

ESQUEMA_EXTRAER = {
    "type": "OBJECT",
    "properties": {"objetivos": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "pagina": {"type": "INTEGER"},
            "eje": {"type": "STRING"},
            "grado_pais": {"type": "STRING"},
            "tipo": {"type": "STRING", "enum": ["conocimiento", "practica", "aplicacion"]},
            "demanda": {"type": "STRING", "enum": ["recordar", "aplicar", "razonar"]},
            "asignatura": {"type": "STRING", "enum": ["fisica", "quimica", "biologia", "tierra_espacio"]},
            "texto": {"type": "STRING"},
            "cita": {"type": "STRING"},
        },
        "required": ["pagina", "eje", "tipo", "demanda", "asignatura", "texto", "cita"],
    }}},
    "required": ["objetivos"],
}

ESQUEMA_VALIDAR = {
    "type": "OBJECT",
    "properties": {"juicios": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "n": {"type": "INTEGER"},
            "veredicto": {"type": "STRING", "enum": ["fiel", "parcial", "no_fiel"]},
            "motivo": {"type": "STRING"},
        },
        "required": ["n", "veredicto", "motivo"],
    }},
        "omitidos": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "pagina": {"type": "INTEGER"},
                "eje": {"type": "STRING"},
                "tipo": {"type": "STRING", "enum": ["conocimiento", "practica", "aplicacion"]},
                "demanda": {"type": "STRING", "enum": ["recordar", "aplicar", "razonar"]},
                "asignatura": {"type": "STRING", "enum": ["fisica", "quimica", "biologia", "tierra_espacio"]},
                "texto": {"type": "STRING"},
                "cita": {"type": "STRING"},
            },
            "required": ["pagina", "eje", "tipo", "demanda", "asignatura", "texto", "cita"],
        }}},
    "required": ["juicios", "omitidos"],
}


@dataclass
class Ventana:
    doc: dict
    paginas: list[int]            # números de página del documento (1 = primera página del archivo)
    adjuntos: list[tuple[bytes, str]]
    texto: str                    # solo para HTML: la sección en texto plano
    etiqueta: str                 # «p. 12–15» o «sección 3»


def _ventanas_pdf(doc: dict) -> Iterator[Ventana]:
    from pypdf import PdfReader, PdfWriter

    lector = PdfReader(ruta(doc["archivo"]))
    rangos = doc.get("paginas") or [1, len(lector.pages)]
    if isinstance(rangos[0], int):   # un solo rango [p0, p1] o varios [[p0, p1], …]
        rangos = [rangos]
    for p0, p1 in rangos:
        fin = min(p1, len(lector.pages))
        for ini in range(p0, fin + 1, VENTANA):
            pags = list(range(ini, min(ini + VENTANA - 1, fin) + 1))
            escritor = PdfWriter()
            for p in pags:
                escritor.add_page(lector.pages[p - 1])
            buf = io.BytesIO()
            escritor.write(buf)
            yield Ventana(doc, pags, [(buf.getvalue(), "application/pdf")], "", f"p. {pags[0]}–{pags[-1]}")


def _texto_html(h: str) -> str:
    h = re.sub(r"(?is)<(script|style|nav|header|footer)[^>]*>.*?</\1>", " ", h)
    h = re.sub(r"(?i)<(br|/p|/li|/h\d|/tr|/div)[^>]*>", "\n", h)
    t = html_mod.unescape(re.sub(r"<[^>]+>", " ", h))
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()


def _ventanas_html(doc: dict) -> Iterator[Ventana]:
    texto = _texto_html(ruta(doc["archivo"]).read_text(encoding="utf-8", errors="replace"))
    if marca := doc.get("desde_texto"):
        texto = texto[max(0, texto.find(marca)):]
    secciones, actual = [], ""
    for linea in texto.split("\n"):
        if len(actual) + len(linea) > CARACTERES_SECCION and actual:
            secciones.append(actual)
            actual = ""
        actual += linea + "\n"
    if actual.strip():
        secciones.append(actual)
    for i, s in enumerate(secciones, start=1):
        yield Ventana(doc, [i], [], s, f"sección {i}")


def ventanas(doc: dict) -> Iterator[Ventana]:
    return _ventanas_html(doc) if doc["archivo"].endswith((".html", ".htm")) else _ventanas_pdf(doc)


def _seccion(v: Ventana) -> str:
    return f"TEXTO DE LA SECCIÓN:\n{v.texto}" if v.texto else ""


def _prompt_extraer(v: Ventana) -> str:
    d = v.doc
    donde = (f"el PDF adjunto ({len(v.paginas)} páginas). En «pagina» pon la POSICIÓN de la página dentro del "
             f"adjunto (1 a {len(v.paginas)}), no el número impreso en la página"
             if v.adjuntos else "la sección del documento copiada abajo; usa «pagina»: 1")
    grados = d.get("grados_pais") or {}
    return f"""Documento: {d['titulo']} ({d['pais_nombre']}). Curso: {d['curso']}. Asignatura: {d['asignatura']}.
Lee {donde}.

Extrae TODOS los objetivos de aprendizaje de ciencias DEL CURSO «{d['curso']}» que el documento enumere en este
tramo (si en el tramo aparecen objetivos de otro curso o de otra asignatura no científica, ignóralos): cada resultado
de aprendizaje, descripción de contenido o enunciado de «los estudiantes deben…» es un objetivo. Reglas:
- Un objetivo = la unidad mínima evaluable que el documento enumera. No partas oraciones ni juntes viñetas.
- Si el documento tiene una jerarquía numerada (p. ej. (1) ア (ア) ㋐, 1.1 a), i., códigos como PKa-Vc-1 o
  ACSPH001), extrae CADA ítem hoja como un objetivo; los títulos intermedios van en «eje». Las notas sobre cómo
  tratar el contenido (alcance, nivel de profundidad) se extraen solo si agregan o limitan contenido.
- Ignora índices, introducciones, fines generales, especificaciones de examen, ponderaciones, notas
  administrativas, glosarios y ejemplos de preguntas. Si el tramo no tiene objetivos, devuelve una lista vacía.
- Incluye prácticas científicas (indagación, experimentos requeridos, habilidades) con tipo «practica».
- «texto»: paráfrasis fiel en ESPAÑOL, de 30 palabras como máximo, que conserve la profundidad (conceptos,
  ecuaciones, ejemplos exigidos).
- «cita»: fragmento literal del original, de 20 palabras como máximo, que permita ubicar el objetivo.
- «eje»: el tema o unidad del documento al que pertenece, traducido al español.
- «grado_pais»: el año o grado si el documento lo indica para ese objetivo ({', '.join(grados) or 'p. ej. Year 11'});
  si no lo indica, deja una cadena vacía.
- «asignatura»: la disciplina del objetivo (fisica, quimica, biologia o tierra_espacio). En un curso integrado,
  decide por el contenido; las prácticas generales van en la disciplina de la unidad donde aparecen.
- «demanda»: recordar (conocer, describir, nombrar), aplicar (usar, calcular, clasificar, relacionar) o razonar
  (explicar con modelos, analizar, evaluar, diseñar, argumentar).
{_seccion(v)}"""


def _prompt_validar(v: Ventana, objetivos: list[dict]) -> str:
    lista = "\n".join(f"{i}. [posición {o['pagina']}] {o['texto']} || cita: {o['cita']}"
                      for i, o in enumerate(objetivos))
    return f"""Eres auditor de fidelidad. Abajo hay objetivos que otro modelo extrajo de {v.etiqueta} del documento
«{v.doc['titulo']}» (curso {v.doc['curso']}). Compara cada uno con el documento.
- fiel: el documento dice eso, con la misma profundidad, y la cita existe en el tramo.
- parcial: el sentido es correcto pero agrega, omite o exagera algo.
La «cita» se recortó a propósito a 20 palabras: no la penalices por incompleta. Una paráfrasis puede unir el
verbo y su complemento aunque estén en oraciones contiguas.
(Las páginas se cuentan por su POSICIÓN dentro del adjunto, de 1 a {len(v.paginas) if v.adjuntos else 1}; no uses
la numeración impresa y no juzgues el número de página.)
- no_fiel: el documento no dice eso, no es un objetivo de aprendizaje o no es de ciencias.
«motivo»: 15 palabras como máximo.
Luego revisa la COMPLETITUD: en «omitidos» lista los objetivos de aprendizaje del curso «{v.doc['curso']}» que
están en el tramo y faltan en la lista (mismas reglas: un ítem hoja por objetivo, paráfrasis en español de ≤30
palabras, cita literal de ≤20 palabras, «pagina» = posición dentro del adjunto). NO cuentes como omitidos los
fines u objetivos generales del curso o de la asignatura (actitudes, «fomentar…», «cultivar…»), introducciones,
especificaciones de examen ni notas administrativas. Si no falta ninguno, devuelve una lista vacía.

OBJETIVOS:
{lista}
{_seccion(v)}"""


def _procesar(v: Ventana) -> list[dict]:
    r = vertex.generar_json(_prompt_extraer(v), modelo=vertex.MODELO_EXTRAER, sistema=SISTEMA,
                            esquema=ESQUEMA_EXTRAER, adjuntos=v.adjuntos)
    objetivos = [o for o in r.get("objetivos", []) if o.get("texto")]
    if not objetivos:
        return []
    j = vertex.generar_json(_prompt_validar(v, objetivos), modelo=vertex.MODELO_VALIDAR,
                            esquema=ESQUEMA_VALIDAR, adjuntos=v.adjuntos)
    juicios = {x["n"]: x for x in j.get("juicios", [])}
    for i, o in enumerate(objetivos):
        x = juicios.get(i, {"veredicto": "parcial", "motivo": "sin juicio del validador"})
        o["validacion"] = {"veredicto": x["veredicto"], "motivo": x["motivo"], "modelo": vertex.MODELO_VALIDAR}
    # Lo que el validador encontró omitido entra marcado: lo propuso un solo modelo, así que va a revisión.
    for o in j.get("omitidos", []):
        if not o.get("texto"):
            continue
        o["validacion"] = {"veredicto": "parcial", "motivo": "agregado por el validador (completitud)",
                           "modelo": vertex.MODELO_VALIDAR}
        objetivos.append(o)
    for o in objetivos:   # posición dentro del adjunto → página del documento
        pos = o["pagina"]
        if not 1 <= pos <= len(v.paginas):
            o["nota_pagina"] = f"el modelo dio la posición {pos}"
            pos = 1
        o["pagina"] = v.paginas[pos - 1]
    return objetivos


def _importados(pais: str) -> list[dict]:
    """Objetivos de sesiones anteriores que se reutilizan tal cual (config: importar)."""
    tipos = {"Práctica": "practica", "Conocimiento": "conocimiento", "Aplicación": "aplicacion"}
    salida = []
    for imp in cargar("internacional").get("importar", []):
        if imp["pais"] != pais:
            continue
        for o in json.loads(ruta(imp["archivo"]).read_text(encoding="utf-8")):
            if o["grado_min"] not in imp["grados_sv"]:
                continue
            salida.append({
                "id": f"{pais}-IMP-{o['id']}", "pais": pais, "documento": imp["documento"], "archivo": o["documento"],
                "pagina": o.get("pagina"), "localizador": o.get("localizador"), "curso": imp["curso"],
                "nivel": imp["nivel"], "asignatura": None, "grado_pais": o.get("grado_o_tramo", ""),
                "grado_sv_min": o["grado_min"], "grado_sv_max": o["grado_max"], "eje": o.get("eje", ""),
                "tipo": tipos.get(o.get("tipo"), "conocimiento"), "demanda": None, "texto": o["texto"], "cita": "",
                "validacion": {"veredicto": "fiel", "motivo": "importado de una extracción anterior", "modelo": None},
                "modelo": None, "version": "importado",
            })
    return salida


def extraer_pais(pais: str, hilos: int = 6, solo: list[str] | None = None) -> dict:
    """Extrae y valida los documentos del país (o solo los ids de `solo`). Devuelve conteos."""
    cfg = cargar("internacional")
    info = cfg["paises"][pais]
    docs = [{**d, "pais": pais, "pais_nombre": info["nombre"]} for d in cfg["documentos"]
            if d["pais"] == pais and (not solo or d["id"] in solo)]
    vs = [v for d in docs for v in ventanas(d)]
    with ThreadPoolExecutor(hilos) as ex:
        resultados = list(ex.map(_procesar, vs))
    salida, descartados = [], []
    for v, objs in zip(vs, resultados, strict=True):
        for o in objs:
            d = v.doc
            grado = (d.get("grados_pais") or {}).get(o.get("grado_pais", "").strip())
            g0, g1 = (grado, grado) if grado else tuple(d["grado_sv"])
            fila = {
                "pais": pais, "documento": d["id"], "archivo": d["archivo"], "pagina": o["pagina"],
                "curso": d["curso"], "nivel": d["nivel"],
                "asignatura": o["asignatura"] if d["asignatura"] == "ciencias_integradas" else d["asignatura"],
                "grado_pais": o.get("grado_pais", ""), "grado_sv_min": g0, "grado_sv_max": g1,
                "eje": o["eje"], "tipo": o["tipo"], "demanda": o["demanda"], "texto": o["texto"],
                "cita": o["cita"], "validacion": o["validacion"], "modelo": vertex.MODELO_EXTRAER,
                "version": VERSION, **({"nota_pagina": o["nota_pagina"]} if "nota_pagina" in o else {}),
            }
            (descartados if o["validacion"]["veredicto"] == "no_fiel" else salida).append(fila)
    _asignar_ids(salida)
    salida += _importados(pais)
    base = ruta(DIR_SALIDA)
    base.mkdir(parents=True, exist_ok=True)
    (base / f"{pais}.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (base / f"{pais}_descartados.json").write_text(
        json.dumps(descartados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    parciales = sum(o["validacion"]["veredicto"] == "parcial" for o in salida)
    return {"pais": pais, "ventanas": len(vs), "objetivos": len(salida), "parciales": parciales,
            "descartados": len(descartados), "llamadas": vertex.llamadas()}


def _asignar_ids(objs: list[dict]) -> None:
    objs.sort(key=lambda o: (o["documento"], o["pagina"], o["eje"], o["texto"]))
    contador: dict[str, int] = {}
    for o in objs:
        base = f"{o['pais']}-{CODIGO_ASIG[o['asignatura']]}-{o['documento']}-p{o['pagina']:03d}"
        contador[base] = contador.get(base, 0) + 1
        o["id"] = f"{base}-{contador[base]:02d}"
