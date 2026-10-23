"""Prepare evidence-backed lesson inputs for a curriculum topic."""

# Historical implementation notes:
# No es la revisión de la malla (eso es el refuerzo, spec 15): es lo que necesita quien prepara la clase, con su fuente.
# - **Texto crudo:** la fila completa de la malla (todas las celdas) y lo que absorbió de la V2; los objetivos de los
#   países que enseñan sus conceptos, con su texto ORIGINAL, documento y página; los objetivos de los marcos.
# - **Conceptos y bases:** definiciones y prerrequisitos, con si la malla los enseña antes.
# - **Ideas previas erróneas:** las dificultades de la capa pedagógica de sus conceptos, con la señal en una respuesta.
# - **Actividades, microtemas y experimentos con procedimiento** de la capa pedagógica.
# - **Datos de referencia** (constantes, tablas): solo de una fuente citable en data/fuentes/; si no hay, el paquete
#   dice cuáles faltan, nunca los inventa.
# - **Refuerzo de la malla** que toca el tema (propuesta GOES, no MINED).
#
# Cada paquete trae su `completitud`: qué hueco está cubierto, cuál parcial y cuál falta, para que nadie lo use creyendo
# que está completo. Lo que no revisó el panel va marcado; nada llega al estudiante sin la firma del docente.

from __future__ import annotations

import json
from collections import defaultdict
from functools import cache
from pathlib import Path

from goes_science_kg.config import ruta

SALIDA = "entregas/paquetes_clase"
DATOS_REFERENCIA = "data/interim/datos_referencia.json"  # extraídos de una fuente en data/fuentes/ (con página)
POR_PAIS = 3
AVISO = (
    "Insumo para preparar clases. La malla es la V3 del MINED; lo demás son propuestas del equipo GOES con "
    "revisión del panel de expertos IA cuando se indica. No son confirmaciones del MINED y nada llega al "
    "estudiante sin la firma del docente."
)


@cache
def _etiquetas_paises() -> dict[str, dict]:
    """Index country-objective concept labels across both historical grade bands."""
    from goes_science_kg.internacional import etiquetar, tramo

    salida: dict[str, dict] = {}
    for t in tramo.TRAMOS.values():
        for _, etq in etiquetar._leer_etiquetados("pais_", t.etiquetado):
            salida.update(etq)
    return salida


@cache
def _objetivos_por_concepto() -> dict[str, list[dict]]:
    from goes_science_kg import bucle

    objs = bucle._objetivos()
    por: dict[str, list[dict]] = defaultdict(list)
    for i, e in _etiquetas_paises().items():
        o = objs.get(i)
        if not o or not o.get("cita"):
            continue
        for c in e.get("principales", []):
            por[c].append({**o, "_peso": 2})
        for c in e.get("secundarios", []) if e.get("confianza") in ("alta", "media") else []:
            por[c].append({**o, "_peso": 1})
    return por


def _raices(texto: str) -> set[str]:
    import re
    import unicodedata

    t = "".join(c for c in unicodedata.normalize("NFKD", (texto or "").lower()) if not unicodedata.combining(c))
    return {w[:6] for w in re.findall(r"[a-zñ]{4,}", t)}


def _fuentes_paises(conceptos: list[str], grado: int, texto_tema: str) -> list[dict]:
    """Select the closest country objectives teaching the topic's concepts."""

    # Implementation notes:
    # comparten el texto del tema (procedimental, indicador y contenido), los del núcleo, los del concepto principal
    # y los del grado más cercano. Así no entran por delante objetivos de un concepto vecino.
    tema = _raices(texto_tema)
    candidatos = {}
    for k, c in enumerate(conceptos):
        for o in _objetivos_por_concepto().get(c, []):
            g = (float(o.get("grado_sv_min") or 0) + float(o.get("grado_sv_max") or 0)) / 2
            cerca = len(tema & _raices(o.get("texto", "")))
            orden = (-cerca, o.get("nivel") != "nucleo", k, -o["_peso"], abs(g - grado), o["id"])
            if o["id"] not in candidatos or orden < candidatos[o["id"]][0]:
                candidatos[o["id"]] = (orden, c, o)
    por_pais: dict[str, list[dict]] = defaultdict(list)
    for _, c, o in sorted(candidatos.values(), key=lambda x: x[0]):
        if len(por_pais[o["pais"]]) < POR_PAIS:
            por_pais[o["pais"]].append(
                {
                    "pais": o["pais"],
                    "id": o["id"],
                    "concepto": c,
                    "nivel": o.get("nivel"),
                    "curso": o.get("curso"),
                    "grado_sv": f"{o.get('grado_sv_min')}–{o.get('grado_sv_max')}",
                    "documento": o.get("archivo"),
                    "pagina": o.get("pagina"),
                    "texto_original": o.get("cita"),
                    "texto_es": o.get("texto"),
                }
            )
    return [x for p in sorted(por_pais) for x in por_pais[p]]


def _datos_referencia(conceptos: list[str]) -> list[dict]:
    p = ruta(DATOS_REFERENCIA)
    if not p.exists():
        return []
    return [d for d in json.loads(p.read_text(encoding="utf-8")) if set(d.get("conceptos", [])) & set(conceptos)]


def _hace_falta_un_dato(texto: object) -> bool:
    return "tabla de referencia" in json.dumps(texto, ensure_ascii=False).lower()


MAGNITUD = (
    r"\b(pKa\d?|pKb|pI|Ka|Kb|Kc|Kp|Kw|Kps|densidad|calor específico|calor latente|presión atmosférica|"
    r"punto isoeléctrico|constante de [a-záéíóúñ]+|masa molar|solubilidad|entalpía|"
    r"coeficientes? de (?:fricción|rozamiento)|μs?|energías? de ionización|electronegatividad(?:es)?|"
    r"radios? atómicos?|índices? de refracción|resistividad|conductividad|punto de (?:fusión|ebullición)|"
    r"módulo de Young|potencial(?:es)? estándar|viscosidad(?:es)?|tensión superficial|"
    r"calores? de (?:fusión|vaporización))\b"
    r"(?:\s+(?:de|del)\s+(?:la\s+|el\s+|los\s+|las\s+)?([a-záéíóúñ\-]+(?:\s+[a-záéíóúñ\-]+)?))?"
)


# Palabras que siguen a la magnitud pero no nombran una sustancia
_NO_SUSTANCIA = {
    "es",
    "sea",
    "son",
    "sean",
    "está",
    "están",
    "que",
    "y",
    "o",
    "en",
    "con",
    "para",
    "se",
    "al",
    "del",
    "no",
    "lugar",
    "un",
    "una",
    "cada",
    "este",
    "esta",
    "ese",
    "esa",
}
_NOMBRE_DATO = {"μ": "coeficiente de fricción (μ)", "μs": "coeficiente de fricción estática (μs)"}


def _clave_dato(dato: str) -> str:
    """Normalize reference-data labels to avoid singular and plural duplicates."""
    import re

    return re.sub(r"(?<=[a-záéíóúñ])s\b", "", dato.lower())


def _datos_que_faltan(elementos: list[dict]) -> list[dict]:
    """Identify reference quantities required by the selected teaching materials."""

    # Implementation notes:
    # que nombra (pKa, pI, Kc, densidad…) con su sustancia cuando la dice.
    import re

    salida: list[dict] = []
    for e in elementos:
        texto = " ".join(str(v) for v in e.values() if isinstance(v, str | list))
        for oracion in re.split(r"(?<=[.;:])\s+", texto):
            if "tabla de referencia" not in oracion.lower():
                continue
            for m in re.finditer(MAGNITUD, oracion, re.IGNORECASE):
                palabras = (m.group(2) or "").split()
                if len(palabras) > 1 and palabras[1].lower() in _NO_SUSTANCIA:
                    palabras = palabras[:1]  # «del aluminio sea» → «del aluminio»
                sustancia = " ".join(palabras)
                nombre = _NOMBRE_DATO.get(m.group(1).lower(), m.group(1))
                dato = nombre + (
                    f" de {sustancia}"
                    if sustancia
                    and palabras[0].lower() not in _NO_SUSTANCIA
                    and not sustancia.lower().startswith(("tabla", "referencia", "valor"))
                    else ""
                )
                if not any(_clave_dato(x["dato"]) == _clave_dato(dato) for x in salida):
                    salida.append(
                        {
                            "dato": dato,
                            "elemento": e["id"],
                            "contexto": e.get("titulo") or (e.get("enunciado") or "")[:90],
                        }
                    )
    return salida


def paquete(tema: str) -> dict:
    """Build a lesson package for a current or explicitly mapped historical topic."""
    from goes_science_kg.aprendizaje.pedagogia import Pedagogia, navegador_compartido
    from goes_science_kg.config import cargar
    from goes_science_kg.ingesta.mallas import extraer, textos_completos, vigente_de

    tid = vigente_de(tema if tema.startswith("TEMA:") else f"TEMA:{tema}")
    if tid is None:
        raise ValueError(f"{tema} ya no está en la malla vigente (la V3 lo quitó): no hay tema para la clase")
    i = tid.removeprefix("TEMA:")
    t = {x.id: x for x in extraer()}[i]
    nav, ped = navegador_compartido(), Pedagogia.cargar()
    nodo = nav.por_id[tid]
    principales = nav.conceptos_de_tema(tid, ("principal",))
    todos = nav.conceptos_de_tema(tid)
    bases = nav.bases(tid)
    corr = json.loads(ruta(cargar("mallas")["correspondencia"]).read_text(encoding="utf-8"))
    absorbe = [
        {"id_v2": x["id"], "procedimental": x["procedimental"]} for x in corr["sin_par"] if x["absorbido_por"] == i
    ]
    marcos = [
        {
            "codigo": a.destino.removeprefix("OBJ:"),
            "marco": nav.por_id[a.destino].props.get("marco"),
            "objetivo": nav.por_id[a.destino].etiqueta,
        }
        for a in nav.aristas
        if a.origen == tid and a.tipo.value == "CUBRE" and a.destino in nav.por_id
    ]
    conceptos_pedagogicos = {*todos, *(b.concepto for b in bases if b.profundidad == 1)}
    actividades = [
        a for a in ped.actividades.values() if tid in a.get("objetivos", []) or set(a.get("evalua", [])) & set(todos)
    ]
    dificultades = [d for d in ped.dificultades.values() if d.get("concepto") in conceptos_pedagogicos]
    microtemas = [m for m in ped.microtemas.values() if m.get("concepto") in conceptos_pedagogicos]
    experimentos = [e for e in ped.experimentos.values() if tid in [vigente_de(o) for o in e.get("objetivos", [])]]
    refuerzos = []
    p_ref = ruta("data/interim/refuerzo_v3/refuerzos.json")
    if p_ref.exists():
        refuerzos = [
            {k: r.get(k) for k in ("id", "decision", "forma", "refuerzo", "fila", "estado", "origen")}
            for r in json.loads(p_ref.read_text(encoding="utf-8"))
            if r.get("tema_ancla") == i
        ]
    datos = _datos_referencia(todos)
    faltan_datos = [e["id"] for e in [*actividades, *experimentos, *microtemas] if _hace_falta_un_dato(e)]
    texto_tema = f"{t.contenido} {t.subcontenido} {t.procedimental} {t.indicador}"
    fuentes = _fuentes_paises(principales + [c for c in todos if c not in principales], t.grado, texto_tema)
    elementos = [*actividades, *dificultades, *microtemas, *experimentos]
    sin_revisar = sorted(e["id"] for e in elementos if e.get("estado") == "propuesta_pendiente")
    completitud = {
        "texto_crudo": "completo" if fuentes and textos_completos().get(i) else "parcial",
        "ideas_previas": "completo" if len(dificultades) >= 2 else "parcial" if dificultades else "falta",
        "experimentos": "completo" if experimentos else "falta",
        "capa_pedagogica": "completo"
        if sum(a.get("rol") == "objetivo" for a in actividades) >= 2 and microtemas
        else "ligera"
        if sum(a.get("rol") == "objetivo" for a in actividades) >= 2
        else "parcial"
        if actividades or microtemas
        else "falta",
        "datos_de_referencia": "completo"
        if datos and not faltan_datos
        else ("pendiente_de_fuente" if faltan_datos or not datos else "parcial"),
        "revision_del_panel": "completa" if elementos and not sin_revisar else "pendiente" if elementos else "—",
    }
    return {
        "aviso": AVISO,
        "tema": {
            "id": i,
            "grado": t.grado,
            "asignatura": nodo.asignatura,
            "archivo": t.ruta,
            "hoja": t.hoja,
            "fila": t.fila,
            "unidad": t.unidad,
            "contenido": t.contenido,
            "subcontenido": t.subcontenido,
            "procedimental": t.procedimental,
            "indicador": t.indicador,
            "evidencia": t.evidencia,
            "habilidad_timss": t.habilidad_timss,
            "competencia_pisa": t.competencia_pisa,
            "microhabilidades_pisa": t.micro_pisa,
            "texto_completo_de_la_fila": textos_completos().get(i),
            "origen_frente_a_la_v2": t.origen,
            "absorbe_de_la_v2": absorbe,
        },
        "conceptos": [
            {
                "id": c,
                "nombre": nav.por_id[c].etiqueta,
                "definicion": nav.por_id[c].props.get("definicion"),
                "rol": "principal" if c in principales else "secundario",
            }
            for c in todos
        ],
        "bases": [
            {
                "concepto": b.concepto,
                "nombre": nav.por_id[b.concepto].etiqueta,
                "profundidad": b.profundidad,
                "la_malla_la_enseña_antes": b.antes_del_objetivo,
                "primer_tema": b.primer_tema,
            }
            for b in bases
        ],
        "fuentes": {"paises": fuentes, "marcos": marcos},
        "ideas_previas": [
            {k: d.get(k) for k in ("id", "concepto", "descripcion", "senales", "estado", "fuente")}
            for d in dificultades
        ],
        "actividades": actividades,
        "microtemas": microtemas,
        "experimentos": experimentos,
        "datos_de_referencia": {
            "valores": datos,
            "hacen_falta_en": faltan_datos,
            "datos_que_faltan": _datos_que_faltan([*actividades, *experimentos, *microtemas]),
            "fuente_esperada": "tabla de referencia citable en data/fuentes/ (pendiente)" if not datos else None,
        },
        "refuerzo_de_la_malla": refuerzos,
        "completitud": completitud,
        "sin_revision_del_panel": sin_revisar,
    }


def _markdown(p: dict) -> str:
    t = p["tema"]
    md = [f"# Paquete de clase: {t['id']} ({t['grado']}.°, {t['asignatura']})", "", f"> {p['aviso']}", ""]
    if r := p.get("reemplazo"):
        md += [
            f"> **Reemplaza a {r['pedido']}, que la V3 quitó.** "
            + (
                "Enseña lo mismo en lo esencial"
                if r["equivalente"]
                else "**No es equivalente:** es el tema vecino más cercano"
            )
            + f" ({int(r['coincidencia_conceptos'] * 100)} % de los conceptos y "
            f"{int(r['contencion_texto'] * 100)} % del texto del pedido). Elegir otro tema es decisión de quien "
            "genera las clases.",
            "",
        ]
    md += ["## Completitud", "", "| Hueco | Estado |", "|---|---|"]
    md += [f"| {k.replace('_', ' ')} | {v} |" for k, v in p["completitud"].items()]
    md += [
        "",
        "## Tema (malla V3, texto crudo)",
        "",
        f"- **Ubicación:** {t['archivo']}, hoja «{t['hoja']}», fila {t['fila']}",
        f"- **Contenido:** {t['contenido']} — {t['subcontenido']}",
        f"- **Procedimental:** {t['procedimental']}",
        f"- **Indicador:** {t['indicador']}",
        f"- **Evidencia:** {t['evidencia']}",
    ]
    if t["absorbe_de_la_v2"]:
        md.append(
            "- **Absorbe de la V2:** "
            + "; ".join(f"{a['id_v2']} ({a['procedimental']})" for a in t["absorbe_de_la_v2"])
        )
    md += ["", "## Conceptos y bases", ""]
    md += [f"- **{c['nombre']}** ({c['rol']}): {c['definicion'] or ''}" for c in p["conceptos"]]
    md += [
        f"- Base: {b['nombre']} (profundidad {b['profundidad']}; "
        f"{'la malla la enseña antes' if b['la_malla_la_enseña_antes'] else 'NO la enseña antes'})"
        for b in p["bases"]
    ]
    md += [
        "",
        "## Fuentes de los países (texto original)",
        "",
        "| País | Nivel | SV | Documento, página | Texto original | Paráfrasis |",
        "|---|---|---|---|---|---|",
    ]
    md += [
        f"| {f['pais']} | {f['nivel']} | {f['grado_sv']} | {str(f['documento']).split('/')[-1]}, "
        f"p. {f['pagina']} | {str(f['texto_original'])[:200]} | {str(f['texto_es'])[:200]} |"
        for f in p["fuentes"]["paises"]
    ]
    md += ["", "## Marcos", ""] + [f"- {m['marco']} {m['codigo']}: {m['objetivo']}" for m in p["fuentes"]["marcos"]]
    md += ["", "## Ideas previas erróneas", ""]
    md += [f"- **{d['id']}** ({d['estado']}): {d['descripcion']} *Señal:* {d['senales']}" for d in p["ideas_previas"]]
    md += ["", "## Experimentos con procedimiento", ""]
    for e in p["experimentos"]:
        md += [
            f"### {e['titulo']} ({e['id']}, {e.get('duracion_min')} min, {e.get('estado')})",
            "",
            f"**Propósito:** {e['proposito']}",
            "",
            "**Materiales:** " + "; ".join(e["materiales"]),
            "",
            "**Procedimiento:**",
            *[f"{k}. {s.split('. ', 1)[-1]}" for k, s in enumerate(e["procedimiento"], 1)],
            "",
            "**Seguridad:** " + "; ".join(e["seguridad"]),
            "",
            f"**Datos esperados:** {e['datos_esperados']}",
            "",
            "**Análisis:** " + " | ".join(e["analisis"]),
            "",
        ]
    md += ["## Actividades", ""]
    md += [
        f"- **{a['id']}** ({a.get('rol')}, {a.get('habilidad')}, {a.get('formato')}): {a.get('enunciado', '')[:220]}"
        for a in p["actividades"]
    ]
    md += ["", "## Datos de referencia", ""]
    d = p["datos_de_referencia"]
    md += [f"- {v}" for v in d["valores"]] or [
        "- **Pendiente de fuente** (tabla citable en data/fuentes/). Datos que piden los elementos:",
        *[f"  - {x['dato']} — en «{x['contexto']}» ({x['elemento']})" for x in d.get("datos_que_faltan", [])],
    ]
    if p["refuerzo_de_la_malla"]:
        md += ["", "## Refuerzo de la malla que toca este tema (propuesta GOES, no MINED)", ""]
        md += [f"- {r['id']} ({r['estado']}): {r['refuerzo']}" for r in p["refuerzo_de_la_malla"]]
    if p["sin_revision_del_panel"]:
        md += ["", f"*Sin revisión del panel todavía: {len(p['sin_revision_del_panel'])} elementos.*"]
    return "\n".join(md) + "\n"


def vecinos(tema_v2: str, k: int = 3) -> list[dict]:
    """Find same-grade neighbors for a topic absent from the current curriculum."""

    # Implementation notes:
    # conceptos que comparten (etiquetas) y la parte de su texto que está en el tema nuevo (contención). Las etiquetas
    # solas engañan: 10.° FIS 5.10 comparte todos los conceptos de 6.4 (curvas), pero el que enseña la curva peraltada
    # es 6.5. Se ordena por la suma de las dos. Es una sugerencia, no una equivalencia.
    from goes_science_kg import conceptos
    from goes_science_kg.ingesta.mallas import _contencion, _raices, extraer

    i = tema_v2.removeprefix("TEMA:")
    etq = conceptos.etiquetado()
    v2 = {t.id: t for t in extraer("mallas_v2")}
    cs = (etq.get(i) or {}).get("conceptos", [])
    if i not in v2 or not cs:
        return []
    salida = []
    from goes_science_kg.aprendizaje.pedagogia import navegador_compartido

    nav = navegador_compartido()  # los conceptos del grafo: con las revisiones de etiquetas aplicadas
    for t in extraer():
        if t.grado != v2[i].grado:
            continue
        c3 = nav.conceptos_de_tema(f"TEMA:{t.id}") if f"TEMA:{t.id}" in nav.por_id else []
        comunes = [c for c in cs if c in c3]
        texto = _contencion(v2[i], _raices(" ".join([t.procedimental, t.subcontenido, t.contenido, t.indicador])))
        if not comunes and texto < 0.3:
            continue
        salida.append(
            {
                "id": t.id,
                "procedimental": t.procedimental,
                "coincidencia": round(len(comunes) / len(cs), 2),
                "contencion_texto": texto,
                "comparte": comunes,
            }
        )
    return sorted(salida, key=lambda x: (-(x["coincidencia"] + x["contencion_texto"]), x["id"]))[:k]


def escribir(temas: list[str]) -> list:
    """Write lesson packages and their completeness index without modifying originals."""

    # Implementation notes:
    # o «pedido=vigente» (p. ej. G10-FIS-U6-6.4=G10-FIS-U6-6.5) cuando la V3 quitó el pedido y alguien eligió el tema
    # que lo reemplaza; un pedido que la V3 quitó y sin reemplazo queda en el índice con sus vecinos, sin paquete.
    from goes_science_kg.ingesta.mallas import vigente_de

    d = ruta(SALIDA)
    d.mkdir(parents=True, exist_ok=True)
    escritos, filas, sin_tema = [], [], []
    for pedido in temas:
        original, _, elegido = pedido.partition("=")
        if not elegido and vigente_de(original if original.startswith("TEMA:") else f"TEMA:{original}") is None:
            sin_tema.append((original, vecinos(original)))
            continue
        p = paquete(elegido or original)
        if elegido:
            vs = vecinos(original, k=10)
            usado = next((v for v in vs if v["id"] == p["tema"]["id"]), None)
            p["reemplazo"] = {
                "pedido": original,
                "tema_usado": p["tema"]["id"],
                "motivo": "la V3 quitó el tema pedido; este es el que se eligió en su lugar",
                "coincidencia_conceptos": usado["coincidencia"] if usado else 0.0,
                "contencion_texto": usado["contencion_texto"] if usado else 0.0,
                "equivalente": bool(usado and max(usado["coincidencia"], usado["contencion_texto"]) >= 0.6),
                "vecinos": vs[:3],
            }
        i = p["tema"]["id"]
        (d / f"{i}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (d / f"{i}.md").write_text(_markdown(p), encoding="utf-8")
        escritos += [d / f"{i}.json", d / f"{i}.md"]
        filas.append((original, i, p["completitud"], p.get("reemplazo")))
    filas = _filas_del_indice(d)  # el índice lista todos los paquetes de la carpeta, no solo los de esta llamada
    claves = list(filas[0][2]) if filas else []
    md = [
        "# Paquetes de clase",
        "",
        AVISO,
        "",
        "| Pedido | Tema vigente | " + " | ".join(c.replace("_", " ") for c in claves) + " |",
        "|---|---|" + "---|" * len(claves),
    ]

    def nota(r: dict | None) -> str:
        if not r:
            return ""
        tipo = "reemplazo" if r["equivalente"] else "VECINO, no equivalente"
        return (
            f" ({tipo}: {int(r['coincidencia_conceptos'] * 100)} % de los conceptos y "
            f"{int(r['contencion_texto'] * 100)} % del texto del pedido)"
        )

    md += [
        f"| {pedido} | [{i}]({i}.md){nota(r)} | " + " | ".join(c[k] for k in claves) + " |" for pedido, i, c, r in filas
    ]
    if sin_tema:
        md += [
            "",
            "## Pedidos que la V3 quitó y no tienen reemplazo elegido",
            "",
            "Ningún tema de la V3 los enseña. Estos vecinos comparten parte de sus conceptos; elegir uno es "
            "decisión de quien genera las clases (`gskg tutor paquete <pedido>=<vecino>`).",
            "",
        ]
        for pedido, vs in sin_tema:
            md.append(
                f"- **{pedido}**: "
                + (
                    "; ".join(
                        f"{v['id']} ({int(v['coincidencia'] * 100)} % de sus conceptos, "
                        f"{int(v['contencion_texto'] * 100)} % de su texto) "
                        f"{v['procedimental'][:80]}"
                        for v in vs
                    )
                    or "sin vecinos por concepto"
                )
            )
    if (d / "REVISION_HUMANA.md").exists():
        md += ["", "> Hay elementos que esperan una decisión humana: ver [REVISION_HUMANA.md](REVISION_HUMANA.md)."]
    (d / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return escritos


def _filas_del_indice(d: Path) -> list[tuple]:
    """List written packages in grade, unit, and topic order."""
    import re

    def orden(i: str) -> list:
        return [int(x) if x.isdigit() else x for x in re.split(r"(\d+)", i)]

    filas = []
    for f in d.glob("*.json"):
        p = json.loads(f.read_text(encoding="utf-8"))
        if "tema" not in p or "completitud" not in p:
            continue
        r = p.get("reemplazo")
        filas.append(((r or {}).get("pedido") or f"TEMA:{p['tema']['id']}", p["tema"]["id"], p["completitud"], r))
    return sorted(filas, key=lambda x: orden(x[1]))
