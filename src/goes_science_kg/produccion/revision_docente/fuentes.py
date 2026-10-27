"""Verificación de la extracción literal de la guía primaria; el recibo no sustituye sus bytes."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from goes_science_kg.materiales.compilacion import sha


def guia_mezclas(carpeta: Path):
    from pypdf import PdfReader

    archivo = carpeta / "mined_guia_3_t1.pdf"
    if archivo.is_symlink() or not archivo.is_file():
        raise ValueError("Falta la guía metodológica primaria de mezclas")
    raw = archivo.read_bytes()
    referencias = json.loads((carpeta / "mezclas.json").read_bytes())
    lector = PdfReader(BytesIO(raw))
    if not referencias or len({r["id"] for r in referencias}) != len(referencias):
        raise ValueError("La extracción requiere páginas únicas")
    for r in referencias:
        origen = r["fuente"]
        pagina = origen["pagina_pdf"]
        if origen["sha256"] != sha(raw) or not 1 <= pagina <= len(lector.pages):
            raise ValueError("La extracción no corresponde a los bytes de la guía")
        if (lector.pages[pagina - 1].extract_text() or "") != r["texto"]:
            raise ValueError("El fragmento no reproduce la página primaria completa")
    return referencias, raw


def complementarias(base: Path):
    import yaml

    from goes_science_kg.produccion.revision_docente.contexto import TextoHTML

    carpeta = base / "data/revision_docente_20261026/fuentes/criticas"
    fuentes = json.loads((carpeta / "pasajes.json").read_bytes())
    manifest = json.loads((carpeta / "manifest.json").read_bytes())
    visibles = {}
    for f in manifest["fuentes"]:
        raw = (carpeta / f["archivo"]).read_bytes()
        if (len(raw), sha(raw)) != (f["bytes"], f["sha256"]):
            raise ValueError("La referencia crítica perdió sus bytes")
        h = TextoHTML()
        h.feed(raw.decode("utf-8"))
        texto = "\n".join(h.partes)
        if sha(texto.encode()) != f["texto_visible_sha256"]:
            raise ValueError("La extracción crítica perdió su huella")
        visibles[f["url"]] = texto
    for f in fuentes:
        meta = f["fuente"]
        texto = visibles[meta["url"]]
        if texto[meta["inicio"] : meta["fin"]] != f["texto"]:
            raise ValueError("El pasaje no reproduce su rango literal")
    config = yaml.safe_load((base / "config/referencias_revision_docente.yaml").read_bytes())
    for f in config["capturas_textuales_web"]:
        fuentes.append(
            {
                "id": f["id"],
                "texto": f["texto"],
                "ambito": "ciencia",
                "fuente": {k: v for k, v in f.items() if k not in {"id", "texto"}}
                | {"texto_capturado_sha256": sha(f["texto"].encode()), "html_original_recuperado": False},
            }
        )
    return fuentes
