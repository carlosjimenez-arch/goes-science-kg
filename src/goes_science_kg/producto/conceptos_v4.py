"""Prepare, validate, and join blind concept tagging of V4 curriculum rows and refined proposals."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from goes_science_kg.archivos import destino_generado
from goes_science_kg.producto.contratos import ProductoMaterializado

VERSION = "etiquetado-v4-1"
INSTRUCCIONES = "prompts/etiquetar_conceptos_v4.md"
DIR_LOTES = "data/interim/conceptos/lotes_v4"
ARCHIVO_ETIQUETADO = "data/producto/conceptos_v4/etiquetado.json"
CONFIANZAS = {"alta", "media", "baja"}
DISCIPLINAS = ("biologia", "fisica", "quimica", "ciencias_tierra_espacio")
CAMPOS_ORIGINAL = ("contenido", "subcontenido", "procedimental", "indicadores_logro")
CAMPOS_PROPUESTA = ("objetivo_propuesto", "indicador_observable")
PREFIJO_PROPUESTA = "PROPUESTA:"
MAX_PALABRAS_JUSTIFICACION = 15
MIN_EVIDENCIA = 4


def normalizar(texto: str) -> str:
    """Return NFKC, case-folded text with collapsed whitespace for literal evidence checks."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", texto or "")).strip().casefold()


def sha_json(valor) -> str:
    """Return the SHA-256 of a canonical JSON serialization."""
    raw = json.dumps(valor, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def items_v4(producto: ProductoMaterializado) -> list[dict]:
    """Build taggable items: in-scope original rows plus proposals that refine their objective."""
    catalogo = {f.fila_id: f for f in producto.catalogo.filas}
    items = []
    for fila in producto.curriculo.filas:
        estado = catalogo[fila.id]
        if estado.estado == "fuera_alcance":
            continue
        items.append(
            {
                "id": fila.id,
                "origen": "original",
                "grado": fila.grado,
                "asignatura_malla": fila.asignatura_malla,
                "unidad": fila.unidad,
                "disciplinas_catalogo": sorted(estado.disciplinas),
                **{c: getattr(fila, c) or "" for c in CAMPOS_ORIGINAL},
            }
        )
    originales = {i["id"]: i for i in items}
    for unidad in producto.mejoras.unidades if producto.mejoras else ():
        for propuesta in unidad.resultado.propuesta.filas if unidad.resultado.propuesta else ():
            if propuesta.accion != "precisar_objetivo" or propuesta.fila_id not in originales:
                continue
            base = originales[propuesta.fila_id]
            items.append(
                {
                    "id": PREFIJO_PROPUESTA + propuesta.fila_id,
                    "origen": "propuesta",
                    "grado": base["grado"],
                    "asignatura_malla": base["asignatura_malla"],
                    "unidad": base["unidad"],
                    "disciplinas_catalogo": sorted(propuesta.disciplinas_propuestas or base["disciplinas_catalogo"]),
                    **{c: getattr(propuesta, c) or "" for c in CAMPOS_PROPUESTA},
                }
            )
    return sorted(items, key=lambda i: (i["grado"], i["origen"], i["id"]))


def texto_item(item: dict) -> str:
    """Join the item fields that may support literal evidence."""
    campos = CAMPOS_ORIGINAL if item["origen"] == "original" else CAMPOS_PROPUESTA
    return " \n ".join(item.get(c) or "" for c in campos)


def _grupo(item: dict) -> str:
    disciplinas = item["disciplinas_catalogo"]
    return disciplinas[0] if len(disciplinas) == 1 else "mixta"


def armar_lotes(items: list[dict], vocabulario: dict, practicas: dict, *, snapshot_id: str, por_lote: int = 24):
    """Group items by grade and catalogued discipline, with the matching vocabulary slice."""
    if not 4 <= por_lote <= 60:
        raise ValueError("El tamaño de lote debe estar entre 4 y 60 ítems")
    grupos: dict[tuple[int, str], list[dict]] = defaultdict(list)
    for item in items:
        grupos[(item["grado"], _grupo(item))].append(item)
    lotes = []
    for (grado, grupo), miembros in sorted(grupos.items()):
        permitidas = set(DISCIPLINAS) if grupo == "mixta" else {grupo}
        voc = [
            {k: c.get(k) for k in ("id", "nombre", "definicion", "sinonimos", "nivel", "asignatura")}
            for c in sorted(vocabulario.values(), key=lambda c: c["id"])
            if c["asignatura"] in permitidas
        ]
        prac = [
            {k: p[k] for k in ("id", "nombre", "definicion")} for p in sorted(practicas.values(), key=lambda p: p["id"])
        ]
        for n, inicio in enumerate(range(0, len(miembros), por_lote), start=1):
            lotes.append(
                {
                    "lote": f"v4_G{grado:02d}_{grupo}_{n}",
                    "version": VERSION,
                    "snapshot_id": snapshot_id,
                    "instrucciones": INSTRUCCIONES,
                    "vocabulario": voc,
                    "practicas": prac,
                    "items": miembros[inicio : inicio + por_lote],
                }
            )
    return lotes


def escribir_lotes(lotes: list[dict], carpeta: Path) -> list[Path]:
    """Write new batches only; refuse to overwrite any existing batch or output."""
    if carpeta.exists() and any(carpeta.iterdir()):
        raise ValueError("La carpeta de lotes V4 ya existe; no se sobrescriben lotes ni salidas")
    carpeta.mkdir(parents=True, exist_ok=True)
    escritos = []
    for lote in lotes:
        destino = destino_generado(carpeta / f"lote_{lote['lote']}.json")
        destino.write_text(json.dumps(lote, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        escritos.append(destino)
    return escritos


def errores_lote_v4(lote: dict, salida: list[dict]) -> list[str]:
    """Validate one output against the batch vocabulary, literal evidence, and size limits."""
    if not isinstance(salida, list) or not all(isinstance(s, dict) for s in salida):
        return ["la salida debe ser un arreglo de objetos JSON"]
    voc = {c["id"] for c in lote["vocabulario"]}
    prac = {p["id"] for p in lote["practicas"]}
    por_id = {s.get("id"): s for s in salida}
    esperados = [i["id"] for i in lote["items"]]
    errores = []
    if faltan := [i for i in esperados if i not in por_id]:
        errores.append(f"faltan {faltan[:3]}")
    if sobran := sorted(set(por_id) - set(esperados)):
        errores.append(f"ids ajenos al lote {sobran[:3]}")
    if len(salida) != len(por_id):
        errores.append("ids duplicados en la salida")
    for item in lote["items"]:
        if not (s := por_id.get(item["id"])):
            continue
        if "conceptos" not in s or "practicas" not in s:
            errores.append(f"{item['id']}: faltan las claves conceptos y prácticas")
            continue
        conceptos, practicas_ = s["conceptos"], s["practicas"]
        if not isinstance(conceptos, list) or not isinstance(practicas_, list):
            errores.append(f"{item['id']}: conceptos y prácticas deben ser listas")
            continue
        if len(conceptos) > 4 or len(set(conceptos)) != len(conceptos):
            errores.append(f"{item['id']}: hasta 4 conceptos distintos")
        if len(practicas_) > 2 or len(set(practicas_)) != len(practicas_):
            errores.append(f"{item['id']}: hasta 2 prácticas distintas")
        if malos := [c for c in conceptos if c not in voc]:
            errores.append(f"{item['id']}: conceptos fuera del vocabulario del lote {malos}")
        if malos := [p for p in practicas_ if p not in prac]:
            errores.append(f"{item['id']}: prácticas inexistentes {malos}")
        if not conceptos and not practicas_:
            errores.append(f"{item['id']}: sin conceptos ni prácticas")
        if s.get("confianza") not in CONFIANZAS:
            errores.append(f"{item['id']}: confianza inválida")
        justificacion = s.get("justificacion")
        if not isinstance(justificacion, str) or not 1 <= len(justificacion.split()) <= MAX_PALABRAS_JUSTIFICACION:
            errores.append(f"{item['id']}: justificación de 1 a {MAX_PALABRAS_JUSTIFICACION} palabras")
        evidencia = s.get("evidencia")
        if not isinstance(evidencia, str) or len(normalizar(evidencia)) < MIN_EVIDENCIA:
            errores.append(f"{item['id']}: falta la evidencia literal")
        elif normalizar(evidencia) not in normalizar(texto_item(item)):
            errores.append(f"{item['id']}: la evidencia no es un fragmento literal del ítem")
        if not isinstance(s.get("nuevos", []), list):
            errores.append(f"{item['id']}: nuevos debe ser una lista")
    return errores


def unir(carpeta: Path, producto: ProductoMaterializado, vocabulario: dict, practicas: dict) -> dict:
    """Validate every batch output against the current product and return the joined labels."""
    lotes = sorted(carpeta.glob("lote_*.json"))
    if not lotes:
        raise ValueError("No hay lotes V4 preparados")
    esperados = {i["id"]: i for i in items_v4(producto)}
    filas, errores, nuevos, huellas = {}, [], Counter(), {}
    for p_lote in lotes:
        lote = json.loads(p_lote.read_text(encoding="utf-8"))
        if lote["version"] != VERSION or lote["snapshot_id"] != producto.manifest.snapshot_id:
            errores.append(f"{p_lote.name}: versión o snapshot distinto")
            continue
        p_sal = p_lote.with_name(p_lote.name.replace("lote_", "salida_", 1))
        if not p_sal.exists():
            errores.append(f"falta {p_sal.name}")
            continue
        salida = json.loads(p_sal.read_text(encoding="utf-8"))
        errores_salida = errores_lote_v4(lote, salida)
        errores += [f"{p_sal.name}: {e}" for e in errores_salida]
        huellas[p_lote.name] = {"lote": sha_json(lote), "salida": hashlib.sha256(p_sal.read_bytes()).hexdigest()}
        if errores_salida:
            continue
        for s in salida:
            item = next((i for i in lote["items"] if i["id"] == s.get("id")), None)
            if item is None:
                continue
            if esperados.get(item["id"]) != item:
                errores.append(f"{p_sal.name}: {item['id']} no coincide con el ítem del producto vigente")
                continue
            if item["id"] in filas:
                errores.append(f"{item['id']}: etiquetado en dos lotes")
                continue
            for n in s.get("nuevos", []):
                nuevos[n] += 1
            filas[item["id"]] = {
                "id": item["id"],
                "fila_id": item["id"].removeprefix(PREFIJO_PROPUESTA),
                "origen": item["origen"],
                "grado": item["grado"],
                "conceptos": s["conceptos"],
                "practicas": s["practicas"],
                "evidencia": s["evidencia"],
                "nuevos": s.get("nuevos", []),
                "confianza": s["confianza"],
                "justificacion": s["justificacion"],
                "lote": lote["lote"],
            }
    if faltan := sorted(set(esperados) - set(filas)):
        errores.append(f"{len(faltan)} ítems del producto sin etiqueta, p. ej. {faltan[:2]}")
    if errores:
        raise ValueError(f"{len(errores)} errores: " + "; ".join(errores[:15]))
    return {
        "version": VERSION,
        "estado": "hipotesis_validada_por_reglas",
        "snapshot_id": producto.manifest.snapshot_id,
        "vocabulario_sha256": sha_json(sorted(vocabulario.values(), key=lambda c: c["id"])),
        "practicas_sha256": sha_json(sorted(practicas.values(), key=lambda p: p["id"])),
        "lotes": huellas,
        "limite": (
            "Etiquetas asignadas por agentes de lotes con validación determinista de vocabulario y evidencia literal. "
            "No constituyen aprobación del MINED ni una relación curricular publicada."
        ),
        "conceptos_propuestos": sorted(nuevos.items(), key=lambda x: (-x[1], x[0])),
        "etiquetas": sorted(filas.values(), key=lambda f: (f["grado"], f["id"])),
    }
