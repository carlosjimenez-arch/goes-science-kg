"""Etiqueta con conceptos y prácticas los objetivos de los países y los temas de la malla V2 (spec 11).

Ambos lados usan el mismo vocabulario (`conceptos.vocabulario()` y `conceptos.practicas()`) y el mismo modelo,
así que el contraste compara con la misma escala. Los ids que no existen se descartan y se cuentan:
no se inventan códigos. Un concepto que falte se propone como nombre (`propuestos`) para el triaje.
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from functools import cache

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.ingesta.mallas import extraer
from goes_science_kg.internacional import vertex

DIR = "data/interim/internacional/etiquetado"
VERSION = "etiquetado-internacional-v1"
POR_LOTE = 20
ASIG_VOCAB = {"fisica": ["fisica"], "quimica": ["quimica"], "biologia": ["biologia"],
              "tierra_espacio": ["ciencias_tierra_espacio"],
              "ciencias": ["fisica", "quimica", "biologia", "ciencias_tierra_espacio"]}

ESQUEMA = {
    "type": "OBJECT",
    "properties": {"etiquetas": {"type": "ARRAY", "items": {
        "type": "OBJECT",
        "properties": {
            "id": {"type": "STRING"},
            "principales": {"type": "ARRAY", "items": {"type": "STRING"}},
            "secundarios": {"type": "ARRAY", "items": {"type": "STRING"}},
            "practicas": {"type": "ARRAY", "items": {"type": "STRING"}},
            "propuestos": {"type": "ARRAY", "items": {"type": "STRING"}},
            "confianza": {"type": "STRING", "enum": ["alta", "media", "baja"]},
            "justificacion": {"type": "STRING"},
        },
        "required": ["id", "principales", "secundarios", "practicas", "propuestos", "confianza", "justificacion"],
    }}},
    "required": ["etiquetas"],
}


def _catalogo(asignatura: str) -> str:
    voc = conceptos.vocabulario()
    asigs = ASIG_VOCAB[asignatura]
    filas = [f"{c['id']} | {c['nombre']} | {c.get('definicion', '')[:140]}"
             for c in sorted(voc.values(), key=lambda c: c["id"]) if c["asignatura"] in asigs]
    prac = [f"{p['id']} | {p['nombre']}" for p in sorted(conceptos.practicas().values(), key=lambda p: p["id"])]
    return ("CONCEPTOS (id | nombre | definición):\n" + "\n".join(filas)
            + "\n\nPRÁCTICAS (id | nombre):\n" + "\n".join(prac))


def _prompt(asignatura: str, items: list[dict]) -> str:
    lista = "\n".join(f"- id: {i['id']}\n  texto: {i['texto']}" for i in items)
    return f"""Eres especialista en didáctica de las ciencias. Etiqueta cada enunciado curricular con los conceptos
del catálogo que ENSEÑA (no los que solo menciona de pasada).
- «principales»: 1 o 2 conceptos que son el foco del enunciado.
- «secundarios»: hasta 3 conceptos que el enunciado trabaja de forma real pero no central.
- «practicas»: prácticas científicas que el enunciado exige de forma explícita (si no exige ninguna, lista vacía).
- Usa SOLO ids exactos del catálogo. Si falta un concepto importante, escribe su nombre en «propuestos»
  (en español, al nivel de granularidad del catálogo) y no inventes ids.
- «confianza»: alta si el enunciado es inequívoco; baja si es vago o mezcla muchos temas.
- «justificacion»: 15 palabras como máximo.

{_catalogo(asignatura)}

ENUNCIADOS:
{lista}"""


def _normalizar(i: str, voc: dict, prac: dict) -> str:
    """Corrige solo el separador cuando el modelo escribe «CON:fisica:x» en lugar de «CON:fisica/x». El id corregido
    tiene que existir en el catálogo; si no existe, queda como estaba y se descarta como inválido."""
    if i in voc or i in prac or ":" not in i:
        return i
    prefijo, resto = i.split(":", 1)
    if ":" in resto:
        candidato = f"{prefijo}:{resto.replace(':', '/', 1)}"
        return candidato if candidato in voc or candidato in prac else i
    if "/" not in resto:   # «CON:tabla-periodica»: le falta la asignatura; vale solo si el nombre es único
        candidatos = [c for c in voc if c.startswith(f"{prefijo}:") and c.endswith(f"/{resto}")]
        return candidatos[0] if len(candidatos) == 1 else i
    return i


def etiquetar(items: list[dict], asignatura: str, nombre: str, hilos: int = 6) -> dict:
    """items: [{id, texto}] de una misma asignatura. Escribe data/interim/internacional/etiquetado/<nombre>.json."""
    voc, prac = conceptos.vocabulario(), conceptos.practicas()
    lotes = [items[i:i + POR_LOTE] for i in range(0, len(items), POR_LOTE)]

    def uno(lote: list[dict]) -> list[dict]:
        r = vertex.generar_json(_prompt(asignatura, lote), modelo=vertex.MODELO_ETIQUETAR, esquema=ESQUEMA)
        return r.get("etiquetas", [])

    with ThreadPoolExecutor(hilos) as ex:
        crudas = [e for lote in ex.map(uno, lotes) for e in lote]
    validos = {i["id"] for i in items}
    salida, invalidos = {}, 0
    for e in crudas:
        if e["id"] not in validos:
            invalidos += 1
            continue
        for clave in ("principales", "secundarios", "practicas"):
            e[clave] = [_normalizar(x, voc, prac) for x in e[clave]]
        limpiar = [c for c in e["principales"] + e["secundarios"] if c not in voc]
        invalidos += len(limpiar) + sum(p not in prac for p in e["practicas"])
        salida[e["id"]] = {
            "principales": sorted({c for c in e["principales"] if c in voc}),
            "secundarios": sorted({c for c in e["secundarios"] if c in voc} - set(e["principales"])),
            "practicas": sorted({p for p in e["practicas"] if p in prac}),
            "propuestos": sorted(set(e["propuestos"]) | set(limpiar)),
            "confianza": e["confianza"], "justificacion": e["justificacion"],
            "modelo": vertex.MODELO_ETIQUETAR, "version": VERSION,
        }
    faltan = sorted(validos - set(salida))
    destino = ruta(DIR) / f"{nombre}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dict(sorted(salida.items())), ensure_ascii=False, indent=1) + "\n",
                       encoding="utf-8")
    leer_etiquetados.cache_clear()
    return {"nombre": nombre, "items": len(items), "etiquetados": len(salida), "faltan": len(faltan),
            "ids_invalidos": invalidos}


@cache
def leer_etiquetados(prefijo: str) -> tuple[tuple[str, dict], ...]:
    """(nombre, etiquetas) de cada etiquetado/<prefijo>*.json, en orden de nombre. Con caché: `etiquetar` la limpia."""
    return tuple((f.stem, json.loads(f.read_text(encoding="utf-8")))
                 for f in sorted(ruta(DIR).glob(f"{prefijo}*.json")))


def cargar_etiquetas(prefijo: str) -> dict[str, dict]:
    """Etiquetas de todos los archivos con ese prefijo, unidas por id (si un id se repite, gana el último archivo)."""
    salida: dict[str, dict] = {}
    for _, etiquetas in leer_etiquetados(prefijo):
        salida.update(etiquetas)
    return salida


def items_malla_v2(grado_min: int = 9) -> dict[str, list[dict]]:
    """Temas de la malla V2 desde `grado_min`, agrupados por asignatura de la malla, como {id, texto}."""

    grupos: dict[str, list[dict]] = {}
    for t in extraer("mallas_v2"):
        if t.grado < grado_min:
            continue
        texto = f"{t.contenido}. {t.subcontenido}. {t.procedimental} Indicador: {t.indicador}"
        grupos.setdefault(t.asignatura, []).append({"id": t.id, "texto": texto[:700]})
    return grupos


def etiquetar_malla_v2(asignaturas: list[str] | None = None) -> list[dict]:
    """Temas de 9.°–11.° de la V2, dos veces: con el vocabulario de su asignatura y con el vocabulario COMPLETO
    (`malla_v2_<asig>_completo`). La V2 reparte Tierra y Espacio entre Biología, Química y Física de Bachillerato
    (p. ej. el cambio climático está en Biología 11.°), y con un solo vocabulario esos temas no reciben su concepto.
    El contraste toma la UNIÓN de los dos etiquetados: afirmar que a El Salvador le falta algo exige que ninguno de
    los dos lo encuentre (cada etiquetado tiene ~20 % de variación en conceptos individuales)."""
    grupos = items_malla_v2()
    salida = []
    for asig, items in sorted(grupos.items()):
        if asignaturas and asig not in asignaturas:
            continue
        salida.append(etiquetar(items, asig, f"malla_v2_{asig}"))
        if asig != "ciencias":   # 9.° ya usa el vocabulario completo
            salida.append(etiquetar(items, "ciencias", f"malla_v2_{asig}_completo"))
    return salida


def etiquetar_malla_v2_antecedente() -> dict:
    """Temas de 2.°–8.° de la V2 (antecedente del contraste) → etiquetado/malla_v2_g02_08.json."""
    items = [i for i in items_malla_v2(grado_min=2)["ciencias"] if int(i["id"][1:3]) <= 8]
    return etiquetar(items, "ciencias", "malla_v2_g02_08")
