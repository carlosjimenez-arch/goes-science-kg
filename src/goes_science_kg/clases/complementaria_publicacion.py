"""Compila la capa complementaria publicable: sólo anexos y evaluaciones válidos con revisión final liberable."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from goes_science_kg.clases.complementaria import (
    LIMITE,
    AnexoClase,
    EvaluacionUnidad,
    markdown_anexo,
    validar_anexo,
    validar_evaluacion,
)
from goes_science_kg.clases.contratos import GuionClase
from goes_science_kg.materiales.compilacion import serializar, sha

VERSION = "complementos-ciencias-1"
CARPETA = Path("data/clases_v4/complementaria")
RECIBO = Path("config/complementos_ciencias.lock.json")


def _revision_final(carpeta: Path, unidad: str) -> dict | None:
    """Prefer the re-review after corrections, then the pilot second review, then the first review."""
    for nombre in (f"{unidad}_final.json", f"{unidad}_r2.json", f"{unidad}.json"):
        archivo = carpeta / "revision" / nombre
        if archivo.is_file():
            return json.loads(archivo.read_bytes()) | {"archivo": nombre}
    return None


def markdown_evaluacion(evaluacion: dict, titulo: str) -> str:
    """Render the unit assessment with answer key and rubric for teachers."""
    e = EvaluacionUnidad.model_validate(evaluacion)
    lineas = [f"# Evaluación de unidad · {titulo}", "", f"> {LIMITE}", "", f"Tiempo sugerido: {e.minutos} minutos.", ""]
    for i in e.items:
        lineas += [f"## {i.id} · {i.dominio} · {i.formato.replace('_', ' ')}", "", i.enunciado, ""]
        lineas += [f"- {o.letra}) {o.texto}" for o in i.opciones]
        lineas += ["", f"Clave: {i.clave}", "", f"Justificación: {i.justificacion}", ""]
        lineas += [
            f"- Distractor {o.letra}: {o.concepcion_que_detecta}" for o in i.opciones if o.concepcion_que_detecta
        ]
        lineas += [f"- Rúbrica · {c.criterio}: logrado {c.logrado}; en proceso {c.en_proceso}" for c in i.rubrica]
        lineas.append("")
    return "\n".join(lineas)


def compilar(raiz: Path) -> dict:
    """Build the publishable document; anything invalid or blocked is withheld with its reason."""
    carpeta = raiz / CARPETA
    registro = {d["id"]: d for d in json.loads((carpeta / "fuentes_nacionales/registro.json").read_bytes())}
    pasajes = {
        p["id"]: p
        for f in sorted((carpeta / "fuentes_nacionales/pasajes").glob("*.json"))
        for p in json.loads(f.read_bytes())
    }
    clases, unidades, retenidos, citados = {}, {}, [], set()
    for archivo in sorted((carpeta / "expedientes").glob("*.json")):
        exp = json.loads(archivo.read_bytes())
        unidad = exp["corto"]
        revision = _revision_final(carpeta, unidad)
        if revision is None:
            retenidos.append({"tipo": "unidad", "id": exp["unidad_id"], "motivo": "Sin revisión independiente"})
            continue
        bloqueados = {a["fila_corta"] for a in revision.get("anexos", []) if a.get("veredicto") != "liberable"}
        fuentes = {x["id"] for x in exp["fuentes_nacionales"]}
        for c in exp["clases"]:
            corto = c["fila_id"][-10:]
            ruta = carpeta / "anexos" / unidad / f"{corto}.json"
            try:
                anexo = AnexoClase.model_validate_json(ruta.read_bytes())
                candidatos = {
                    "previas": {(x["concepto"], x["fila_id"]) for x in c["candidatos_previas"]},
                    "continuidad": {(x["concepto"], x["fila_id"]) for x in c["candidatos_continuidad"]},
                    "fuentes": fuentes,
                }
                errores = validar_anexo(anexo, GuionClase.model_validate(c["guion"]), c["guion_sha256"], candidatos)
            except (OSError, ValidationError) as error:
                errores = [type(error).__name__]
            if errores or corto in bloqueados:
                motivo = "Bloqueado en revisión independiente" if corto in bloqueados else "No supera la validación"
                retenidos.append({"tipo": "anexo", "id": c["fila_id"], "motivo": motivo})
                continue
            datos = anexo.model_dump(mode="json")
            citados |= {i for a in anexo.contexto_nacional.afirmaciones for i in a.fuentes_ids}
            clases[c["fila_id"]] = {
                "unidad_id": exp["unidad_id"],
                "titulo": c["titulo"],
                "grado": c["grado"],
                "guion_sha256": c["guion_sha256"],
                "anexo": datos,
                "markdown": markdown_anexo(datos, c["titulo"]),
                "revision": revision["archivo"],
            }
        ruta = carpeta / "evaluaciones" / f"{unidad}.json"
        try:
            evaluacion = EvaluacionUnidad.model_validate_json(ruta.read_bytes())
            errores = validar_evaluacion(evaluacion, exp["unidad_id"], {c["fila_id"] for c in exp["clases"]})
        except (OSError, ValidationError) as error:
            errores = [type(error).__name__]
        if errores or (revision.get("evaluacion") or {}).get("veredicto") != "liberable":
            retenidos.append({"tipo": "evaluacion", "id": exp["unidad_id"], "motivo": "Bloqueada o inválida"})
        else:
            datos = evaluacion.model_dump(mode="json")
            unidades[exp["unidad_id"]] = {
                "unidad": exp["unidad"],
                "grado": exp["grado"],
                "asignatura": exp["asignatura"],
                "evaluacion": datos,
                "markdown": markdown_evaluacion(datos, exp["unidad"]),
                "revision": revision["archivo"],
            }
    fuentes_publicadas = {
        i: {k: pasajes[i][k] for k in ("documento", "pagina", "texto")}
        | {k: registro[pasajes[i]["documento"]][k] for k in ("institucion", "titulo", "anio", "url", "sha256")}
        for i in sorted(citados)
    }
    documento = {
        "version": VERSION,
        "limite": LIMITE,
        "clases": clases,
        "unidades": unidades,
        "fuentes_nacionales": fuentes_publicadas,
        "retenidos": retenidos,
    }
    documento["id"] = sha(serializar(documento))
    return documento


def publicar(raiz: Path) -> dict:
    """Write the compiled document under a new content-addressed name and return its receipt."""
    documento = compilar(raiz)
    raw = serializar(documento)
    ruta = CARPETA / "publicacion" / f"complementos-{documento['id'][:16]}.json"
    destino = raiz / ruta
    destino.parent.mkdir(parents=True, exist_ok=True)
    if not destino.exists():
        with destino.open("xb") as f:
            f.write(raw)
    elif destino.read_bytes() != raw:
        raise ValueError("Ya existe una publicación distinta con esa identidad")
    return {
        "version": VERSION,
        "ruta": ruta.as_posix(),
        "sha256": sha(raw),
        "id": documento["id"],
        "clases": len(documento["clases"]),
        "unidades": len(documento["unidades"]),
        "fuentes_nacionales": len(documento["fuentes_nacionales"]),
        "retenidos": len(documento["retenidos"]),
    }


def leer_publicada(raiz: Path) -> dict:
    """Load the pinned publication and verify its bytes and identity against the receipt."""
    recibo = json.loads((raiz / RECIBO).read_bytes())
    archivo = (raiz / recibo["ruta"]).resolve()
    if not archivo.is_relative_to((raiz / CARPETA).resolve()) or archivo.is_symlink():
        raise ValueError("La publicación complementaria está fuera de su carpeta")
    raw = archivo.read_bytes()
    documento = json.loads(raw)
    if sha(raw) != recibo["sha256"] or documento.get("id") != recibo["id"]:
        raise ValueError("La publicación complementaria no coincide con su recibo")
    if documento["id"] != sha(serializar({k: v for k, v in documento.items() if k != "id"})):
        raise ValueError("La identidad de la publicación complementaria cambió")
    return documento
