"""Contextos completos factorizados por repetición, con fuentes literales y lotes de unidades intactas."""

from __future__ import annotations

import json
from copy import deepcopy
from html.parser import HTMLParser

from goes_science_kg.materiales.compilacion import serializar, sha


class TextoHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.partes, self.oculto = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.oculto += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style"}:
            self.oculto = max(0, self.oculto - 1)

    def handle_data(self, data):
        if not self.oculto and data.strip():
            self.partes.append(data.strip())


def fuentes(base, archivos):
    """Las preparaciones finales aportan párrafos científicos, no sus votos ni propuestas."""
    from io import BytesIO

    from pypdf import PdfReader

    corpus = {}
    from goes_science_kg.ingesta.web_cientifica import RepositorioWeb
    from goes_science_kg.recuperacion.ciencia_web import IndiceCienciaWeb

    web = IndiceCienciaWeb(RepositorioWeb(base / "data/referencias_web_cientificas_2026"))
    from goes_science_kg.ingesta.progresiones import cargar_progresiones

    nativas = cargar_progresiones(
        base / "config/progresiones_documentales_2026.yaml", base / "data/referencias_progresiones_2026"
    ).archivo()["evidencias"]
    for p in sorted((base / "data/produccion_v4_20261026/preparaciones_p2").glob("*.json")):
        d = json.loads(p.read_bytes())
        ids = set(d.get("grupos", {}).get("definiciones_cientificas", []))
        ids.update(d.get("grupos", {}).get("progresiones_documentales", []))
        for e in d.get("evidencias", []):
            if e["id"] not in ids:
                continue
            if sha(e["texto"].encode()) != e["huella"]:
                raise ValueError("El párrafo científico perdió su huella")
            if e["id"].startswith("WEBPAR:") and (
                e["id"] not in web.evidencias or web.evidencias[e["id"]].model_dump(mode="json") != e
            ):
                raise ValueError("La preparación no reproduce el párrafo científico de la captura verificada")
            if e["id"] in d.get("grupos", {}).get("progresiones_documentales", []) and nativas.get(e["id"]) != e:
                raise ValueError("La progresión no reproduce la región primaria verificada")
            anterior = corpus.get(e["id"])
            limpio = {k: e[k] for k in ("id", "texto", "fuente")}
            if anterior and anterior != limpio:
                raise ValueError("Una identidad documental tiene dos contenidos")
            corpus[e["id"]] = limpio
    manifest = json.loads(archivos["didactica/referencias/manifest.json"])
    for s in manifest["fuentes"]:
        if s["estado"] != "descargado":
            continue
        raw = archivos["didactica/referencias/" + s["archivo"]]
        if (len(raw), sha(raw)) != (s["bytes"], s["sha256"]):
            raise ValueError("La referencia no conserva sus bytes")
        if raw.startswith(b"%PDF"):
            lector = PdfReader(BytesIO(raw))
            paginas = [22, 23, 33, 34] if s["id"] == "pisa_final_2026" else [5, 6, 7, 8, 9, 47]
            for i in paginas:
                texto = lector.pages[i].extract_text() or ""
                id_ = s["id"] + ":pdf:" + str(i + 1)
                corpus[id_] = {
                    "id": id_,
                    "texto": texto,
                    "fuente": {"url": s["url"], "sha256": s["sha256"], "pagina_pdf": i + 1},
                }
        else:
            h = TextoHTML()
            h.feed(raw.decode("utf-8"))
            corpus[s["id"]] = {
                "id": s["id"],
                "texto": "\n".join(h.partes),
                "fuente": {"url": s["url"], "sha256": s["sha256"], "tipo": "HTML completo visible"},
            }
    return sorted(corpus.values(), key=lambda f: f["id"])


def item(r):
    d = r["documento"]
    original = deepcopy(d.get("original"))
    if original is not None:
        # Los campos lógicos mantienen el texto completo. Las coordenadas/bytes se auditan por separado.
        original.pop("celdas")
    return {
        "id": r["id"],
        "tipo": r["tipo"],
        "grado": r["grados"][0],
        "asignatura": r["asignatura"],
        "unidad": r["unidad"],
        "original": original,
        "objetivos_originales": d.get("objetivos"),
        "edicion": d["edicion_docente"],
    }


def factorizar(solicitud):
    """Interna textos y estructuras repetidas, con expansión exacta y sin resumen."""
    from collections import Counter

    textos, estructuras, valores = Counter(), Counter(), {}

    def contar(x):
        if isinstance(x, str) and len(x) >= 40:
            textos[x] += 1
        elif isinstance(x, (dict, list)):
            raw = serializar(x)
            if len(raw) >= 100:
                clave = sha(raw)
                estructuras[clave] += 1
                valores[clave] = x
            for v in x.values() if isinstance(x, dict) else x:
                contar(v)

    contar(solicitud)
    ts = {t: f"T{i:04d}" for i, t in enumerate(sorted(t for t, n in textos.items() if n > 1))}
    vs = {c: f"V{i:04d}" for i, c in enumerate(sorted(c for c, n in estructuras.items() if n > 1))}

    def transformar(x, omitir=None):
        if isinstance(x, str) and x in ts:
            return {"$texto": ts[x]}
        if isinstance(x, (dict, list)):
            clave = sha(serializar(x))
            if clave in vs and clave != omitir:
                return {"$valor": vs[clave]}
            if isinstance(x, dict):
                return {k: transformar(v) for k, v in x.items()}
            return [transformar(v) for v in x]
        return x

    return {
        "formato": "Resolver recursivamente $texto y $valor en sus tablas. Expansión exacta sin omitir contenido.",
        "textos_compartidos": {v: k for k, v in ts.items()},
        "valores_compartidos": {v: transformar(valores[k], omitir=k) for k, v in vs.items()},
        "solicitud": transformar(solicitud),
    }


def fuentes_por_objetivo(base, registros):
    """Recupera dos pasajes completos de la selección documental anterior; nunca sus votos."""
    from goes_science_kg.clases.corpora import cargar_corpus
    from goes_science_kg.clases.fundamentacion import texto_visible

    anteriores = {}
    for p in sorted((base / "data/clases_v4").glob("preparaciones*/lote_*.json")):
        d = json.loads(p.read_bytes())
        for f in d.get("filas", []):
            if not f.get("fila_id") or not f.get("fuentes_cientificas_ids"):
                continue
            a = anteriores.setdefault(f["fila_id"], {"ids": set(), "consultas": set()})
            a["ids"].update(f["fuentes_cientificas_ids"])
            if f.get("consulta_recuperacion"):
                a["consultas"].add(f["consulta_recuperacion"])
    corpus = cargar_corpus(base, todos=True)
    coleccion = {id_: e for c in getattr(corpus, "corpora", [corpus]) for id_, e in c.evidencias.items()}
    from goes_science_kg.recuperacion.lexico import IndiceLexico
    from goes_science_kg.recuperacion.modelos import Documento

    indice = IndiceLexico(
        Documento(id=e.id, texto=e.texto, fuente=e.fuente, version=e.version) for e in coleccion.values()
    )
    fuentes, enlaces = {}, {}
    for r in registros:
        if r["tipo"] != "paquete_objetivo":
            continue
        previo = r["documento"]["comparacion"]["antecedente_localizador"]
        a = anteriores.get(previo)
        if not a:
            continue
        ids = set(a["ids"]) & set(coleccion)
        q = " ".join(sorted(a["consultas"])) or r["titulo"]
        seleccion = indice.buscar(q, permitidos=ids, limite=2)
        enlaces[r["id"]] = [id_ for id_, _ in seleccion]
        for id_, _ in seleccion:
            e = coleccion[id_]
            corpus.verificar(e)
            fuentes[id_] = {
                "id": id_,
                "texto": texto_visible(e.texto),
                "fuente": e.fuente,
                "huella_texto_original": e.huella,
                "ambito": "ciencia",
            }
    return fuentes, enlaces


def codificar_identidades(solicitud):
    """Alias reversibles para evitar gastar la salida del revisor repitiendo hashes."""
    s = deepcopy(solicitud)
    fuentes_ids = {f["id"]: f"F{i:04d}" for i, f in enumerate(s["fuentes"])}
    if len(fuentes_ids) != len(s["fuentes"]):
        raise ValueError("Fuentes duplicadas en el contexto")
    for i, item_ in enumerate(s["items"]):
        item_["identidad_original"] = item_["id"]
        item_["id"] = f"I{i:03d}"
        item_["fuentes_recuperadas_ids"] = [fuentes_ids[id_] for id_ in item_.get("fuentes_recuperadas_ids", [])]
    for f in s["fuentes"]:
        f["identidad_original"] = f["id"]
        f["id"] = fuentes_ids[f["id"]]
    return s


def lotes_equilibrados(registros, documentos, numero=5):
    """Unidades intactas, hasta 227 elementos y tres lugares reservados para controles."""
    objetivos = {r["id"]: r for r in registros if r["tipo"] == "paquete_objetivo"}
    unidades = sorted(
        (r for r in registros if r["tipo"] == "paquete_unidad"),
        key=lambda r: (-len(r["documento"]["filas_ids"]), r["id"]),
    )
    grupos = [[] for _ in range(numero)]
    for u in unidades:
        grupo = min(grupos, key=len)
        grupo.extend([u, *(objetivos[id_] for id_ in u["documento"]["filas_ids"])])
    if max(map(len, grupos)) > 227 or sum(map(len, grupos)) != len(registros):
        raise ValueError("Las unidades no caben en el transporte acotado")
    return [
        {"lote": i, "items": sorted((item(r) for r in g), key=lambda x: x["id"]), "fuentes": deepcopy(documentos)}
        for i, g in enumerate(grupos)
    ]


def vista_revision(solicitud):
    """Contenido docente íntegro; metadatos de procedencia quedan fuera del mensaje y dentro del expediente.

    No resume tareas, explicaciones, criterios, apoyos, casos o fuentes. Los IDs instrumentales
    se representan por índices verificables. Las celdas y declaraciones originales se auditan
    con los once Excel por separado; el lector recibe sus objetivos y contenidos declarados.
    """
    s = deepcopy(solicitud)
    s.pop("controles_revision", None)
    ids = {i.get("identidad_original", i["id"]): i["id"] for i in s["items"]}
    for i in s["items"]:
        i.pop("identidad_original", None)
        original = i.get("original")
        if original is not None:
            i["original"] = {k: original[k] for k in ("procedimental", "contenido", "subcontenido")}
        e = i["edicion"]
        if solicitud.get("iteracion_lectura") == 2 and "aplicacion" in e:
            e["aplicacion"].pop("tarea_de_transferencia_original", None)
        if "actividades" in e:
            tareas = {t["id"]: f"A{n}" for n, t in enumerate(e["actividades"])}
            for t in e["actividades"]:
                t["id"] = tareas[t["id"]]
                t.pop("origen_tarea_id")
            for c in e["criterios"]:
                c["tarea_ids"] = [tareas[t] for t in c["tarea_ids"]]
            if e.get("caso_resuelto"):
                for k in ("fuentes", "referencias", "fila_id", "huella_curriculo", "destino"):
                    e["caso_resuelto"].pop(k, None)
        if "filas_ids" in e:
            e["filas_ids"] = [ids[t] for t in e["filas_ids"]]
    for f in s["fuentes"]:
        f["fuente"] = {k: v for k, v in f["fuente"].items() if k in {"url", "pagina_pdf", "titulo"}}
        f.pop("identidad_original", None)
        f.pop("huella_texto_original", None)
        f.pop("texto_visible_sha256", None)
    s["protocolo_vista"] = "Contenido docente completo e índices locales; procedencia íntegra en captura auditada."
    return s
