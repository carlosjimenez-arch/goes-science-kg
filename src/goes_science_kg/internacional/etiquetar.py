"""Tag country objectives and V2 curriculum topics with concepts and practices."""

# Historical implementation notes:
# Ambos lados usan el mismo vocabulario (`conceptos.vocabulario()` y `conceptos.practicas()`) y el mismo modelo,
# así que el contraste compara con la misma escala. Los ids que no existen se descartan y se cuentan:
# no se inventan códigos. Un concepto que falte se propone como nombre (`propuestos`) para el triaje.

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from functools import cache

from goes_science_kg import conceptos
from goes_science_kg.config import ruta
from goes_science_kg.ingesta.mallas import extraer
from goes_science_kg.internacional import tramo, vertex

DIR = tramo.ETIQUETADO_COMUN  # malla V2 y catálogo; los países, en la carpeta de su tramo
VERSION = "etiquetado-internacional-v1"
POR_LOTE = 20
ASIG_VOCAB = {
    "fisica": ["fisica"],
    "quimica": ["quimica"],
    "biologia": ["biologia"],
    "tierra_espacio": ["ciencias_tierra_espacio"],
    "ciencias": ["fisica", "quimica", "biologia", "ciencias_tierra_espacio"],
}

ESQUEMA = {
    "type": "OBJECT",
    "properties": {
        "etiquetas": {
            "type": "ARRAY",
            "items": {
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
                "required": [
                    "id",
                    "principales",
                    "secundarios",
                    "practicas",
                    "propuestos",
                    "confianza",
                    "justificacion",
                ],
            },
        }
    },
    "required": ["etiquetas"],
}


CATALOGO = "data/interim/internacional/catalogo_etiquetado.json"
Grupo = tuple[list[dict], str, str]  # (items [{id, texto}], asignatura del vocabulario, nombre del archivo)


@cache
def catalogo_congelado() -> dict:
    """Load the intentionally frozen tagging vocabulary."""

    # Implementation notes:
    # cualquier cambio (triaje, divisiones) cambiaría todos los prompts e invalidaría la caché de Vertex. Los cambios de
    # vocabulario entran por las capas de decisión al cargar. Sin archivo, se usa el vocabulario vivo.
    p = ruta(CATALOGO)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {
        "version": "vivo",
        "conceptos": sorted(conceptos.vocabulario().values(), key=lambda c: c["id"]),
        "practicas": sorted(conceptos.practicas().values(), key=lambda p: p["id"]),
    }


def congelar_catalogo(version: str) -> dict:
    """Freeze the current vocabulary and explicitly invalidate previous tagging caches."""

    # Implementation notes:
    # etiquetado: volver a etiquetar se paga completo. Solo para re-etiquetar a propósito con el vocabulario nuevo.
    voc = sorted(conceptos.vocabulario().values(), key=lambda c: c["id"])
    prac = sorted(conceptos.practicas().values(), key=lambda p: p["id"])
    datos = {
        "version": version,
        "conceptos": [{k: c.get(k) for k in ("id", "nombre", "definicion", "asignatura")} for c in voc],
        "practicas": [{k: p[k] for k in ("id", "nombre")} for p in prac],
    }
    ruta(CATALOGO).write_text(json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    catalogo_congelado.cache_clear()
    return {"version": version, "conceptos": len(datos["conceptos"])}


def _catalogo(asignatura: str) -> str:
    cat = catalogo_congelado()
    asigs = ASIG_VOCAB[asignatura]
    filas = [
        f"{c['id']} | {c['nombre']} | {(c.get('definicion') or '')[:140]}"
        for c in cat["conceptos"]
        if c["asignatura"] in asigs
    ]
    prac = [f"{p['id']} | {p['nombre']}" for p in cat["practicas"]]
    return (
        "CONCEPTOS (id | nombre | definición):\n"
        + "\n".join(filas)
        + "\n\nPRÁCTICAS (id | nombre):\n"
        + "\n".join(prac)
    )


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
    """Correct only a recognized concept-identifier separator before validation."""

    # Implementation notes:
    # tiene que existir en el catálogo; si no existe, queda como estaba y se descarta como inválido.
    if i in voc or i in prac or ":" not in i:
        return i
    prefijo, resto = i.split(":", 1)
    if ":" in resto:
        candidato = f"{prefijo}:{resto.replace(':', '/', 1)}"
        return candidato if candidato in voc or candidato in prac else i
    if "/" not in resto:  # «CON:tabla-periodica»: le falta la asignatura; vale solo si el nombre es único
        candidatos = [c for c in voc if c.startswith(f"{prefijo}:") and c.endswith(f"/{resto}")]
        return candidatos[0] if len(candidatos) == 1 else i
    return i


def _lotes(items: list[dict]) -> list[list[dict]]:
    return [items[i : i + POR_LOTE] for i in range(0, len(items), POR_LOTE)]


def pendientes(grupos: list[Grupo]) -> int:
    """Estimate uncached Vertex tagging calls for the selected groups."""
    return sum(
        not vertex.en_cache(_prompt(asig, lote), modelo=vertex.MODELO_ETIQUETAR, esquema=ESQUEMA)
        for items, asig, _ in grupos
        for lote in _lotes(items)
    )


def etiquetar(items: list[dict], asignatura: str, nombre: str, hilos: int = 6) -> dict:
    """Tag a same-subject objective batch and write its validated output."""
    voc, prac = conceptos.vocabulario(), conceptos.practicas()
    lotes = _lotes(items)

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
            "confianza": e["confianza"],
            "justificacion": e["justificacion"],
            "modelo": vertex.MODELO_ETIQUETAR,
            "version": VERSION,
        }
    faltan = sorted(validos - set(salida))
    destino = ruta(_carpeta(nombre)) / f"{nombre}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(dict(sorted(salida.items())), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    _leer_etiquetados.cache_clear()
    return {
        "nombre": nombre,
        "items": len(items),
        "etiquetados": len(salida),
        "faltan": len(faltan),
        "ids_invalidos": invalidos,
    }


def _carpeta(nombre: str) -> str:
    """Separate band-specific country labels from shared V2 curriculum labels."""
    return tramo.actual().etiquetado if nombre.startswith("pais_") else tramo.ETIQUETADO_COMUN


def leer_etiquetados(prefijo: str) -> tuple[tuple[str, dict], ...]:
    """Read matching label files deterministically and apply explicit concept splits."""

    # Implementation notes:
    # carpeta: `etiquetar` la limpia al escribir.
    return _leer_etiquetados(prefijo, _carpeta(prefijo))


@cache
def _leer_etiquetados(prefijo: str, carpeta: str) -> tuple[tuple[str, dict], ...]:
    conjunto = {"pais_": "internacional", "malla_v2_": "malla_v2"}.get(prefijo)
    return tuple(
        (f.stem, _con_divisiones(conjunto, json.loads(f.read_text(encoding="utf-8"))))
        for f in sorted(ruta(carpeta).glob(f"{prefijo}*.json"))
    )


def _con_divisiones(conjunto: str | None, etiquetas: dict[str, dict]) -> dict[str, dict]:
    """Apply reviewed concept divisions to principal and secondary labels."""
    if not conjunto:
        return etiquetas
    salida = {}
    for i, e in etiquetas.items():
        principales = conceptos.aplicar_divisiones(conjunto, i, e["principales"])
        secundarios = [c for c in conceptos.aplicar_divisiones(conjunto, i, e["secundarios"]) if c not in principales]
        salida[i] = {**e, "principales": principales, "secundarios": secundarios}
    return salida


def cargar_etiquetas(prefijo: str) -> dict[str, dict]:
    """Merge label files by identity under the documented last-file precedence."""
    salida: dict[str, dict] = {}
    for _, etiquetas in leer_etiquetados(prefijo):
        salida.update(etiquetas)
    return salida


def items_malla_v2(grado_min: int = 9) -> dict[str, list[dict]]:
    """Group V2 topic identities and text by their declared curriculum subject."""

    grupos: dict[str, list[dict]] = {}
    for t in extraer():
        if t.grado < grado_min:
            continue
        texto = f"{t.contenido}. {t.subcontenido}. {t.procedimental} Indicador: {t.indicador}"
        grupos.setdefault(t.asignatura, []).append({"id": t.id, "texto": texto[:700]})
    return grupos


def grupos_malla_v2(asignaturas: list[str] | None = None) -> list[Grupo]:
    """Prepare V2 tagging groups and the earlier-grade reference context."""
    grupos: list[Grupo] = []
    for asig, items in sorted(items_malla_v2().items()):
        if asignaturas and asig not in asignaturas:
            continue
        grupos.append((items, asig, f"malla_v2_{asig}"))
        if asig != "ciencias":  # 9.° ya usa el vocabulario completo
            grupos.append((items, "ciencias", f"malla_v2_{asig}_completo"))
    if not asignaturas:
        antecedente = [i for i in items_malla_v2(grado_min=2)["ciencias"] if int(i["id"][1:3]) <= 8]
        grupos.append((antecedente, "ciencias", "malla_v2_g02_08"))
    return grupos
