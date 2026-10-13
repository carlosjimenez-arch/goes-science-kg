"""Paquete de clase por tema: el insumo para GENERAR una clase de un tema de la malla vigente (spec 13, sección 9).

No es la revisión de la malla (eso es el refuerzo, spec 15): es lo que necesita quien prepara la clase, con su fuente.
- **Texto crudo:** la fila completa de la malla (todas las celdas) y lo que absorbió de la V2; los objetivos de los
  países que enseñan sus conceptos, con su texto ORIGINAL, documento y página; los objetivos de los marcos.
- **Conceptos y bases:** definiciones y prerrequisitos, con si la malla los enseña antes.
- **Ideas previas erróneas:** las dificultades de la capa pedagógica de sus conceptos, con la señal en una respuesta.
- **Actividades, microtemas y experimentos con procedimiento** de la capa pedagógica.
- **Datos de referencia** (constantes, tablas): solo de una fuente citable en data/fuentes/; si no hay, el paquete
  dice cuáles faltan, nunca los inventa.
- **Refuerzo de la malla** que toca el tema (propuesta GOES, no MINED).

Cada paquete trae su `completitud`: qué hueco está cubierto, cuál parcial y cuál falta, para que nadie lo use creyendo
que está completo. Lo que no revisó el panel va marcado; nada llega al estudiante sin la firma del docente.
"""

from __future__ import annotations

import json
from collections import defaultdict
from functools import cache

from goes_science_kg.config import ruta

SALIDA = "entregas/paquetes_clase"
DATOS_REFERENCIA = "data/interim/datos_referencia.json"   # extraídos de una fuente en data/fuentes/ (con página)
POR_PAIS = 3
AVISO = ("Insumo para preparar clases. La malla es la V3 del MINED; lo demás son propuestas del equipo GOES con "
         "revisión del panel de expertos IA cuando se indica. No son confirmaciones del MINED y nada llega al "
         "estudiante sin la firma del docente.")


@cache
def _etiquetas_paises() -> dict[str, dict]:
    """Etiquetas de los objetivos de los países de los dos tramos (id → principales y secundarios)."""
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


def _fuentes_paises(conceptos: list[str], grado: int) -> list[dict]:
    """Hasta POR_PAIS objetivos por país que enseñan los conceptos del tema: primero el núcleo, el concepto
    principal y el grado más cercano al del tema."""
    candidatos = {}
    for k, c in enumerate(conceptos):
        for o in _objetivos_por_concepto().get(c, []):
            g = (float(o.get("grado_sv_min") or 0) + float(o.get("grado_sv_max") or 0)) / 2
            orden = (o.get("nivel") != "nucleo", k, -o["_peso"], abs(g - grado), o["id"])
            if o["id"] not in candidatos or orden < candidatos[o["id"]][0]:
                candidatos[o["id"]] = (orden, c, o)
    por_pais: dict[str, list[dict]] = defaultdict(list)
    for _, c, o in sorted(candidatos.values(), key=lambda x: x[0]):
        if len(por_pais[o["pais"]]) < POR_PAIS:
            por_pais[o["pais"]].append({
                "pais": o["pais"], "id": o["id"], "concepto": c, "nivel": o.get("nivel"), "curso": o.get("curso"),
                "grado_sv": f"{o.get('grado_sv_min')}–{o.get('grado_sv_max')}",
                "documento": o.get("archivo"), "pagina": o.get("pagina"),
                "texto_original": o.get("cita"), "texto_es": o.get("texto")})
    return [x for p in sorted(por_pais) for x in por_pais[p]]


def _datos_referencia(conceptos: list[str]) -> list[dict]:
    p = ruta(DATOS_REFERENCIA)
    if not p.exists():
        return []
    return [d for d in json.loads(p.read_text(encoding="utf-8")) if set(d.get("conceptos", [])) & set(conceptos)]


def _hace_falta_un_dato(texto: object) -> bool:
    return "tabla de referencia" in json.dumps(texto, ensure_ascii=False).lower()


def paquete(tema: str) -> dict:
    """El paquete de clase de un tema de la malla vigente (acepta un id de la V2 que la V3 absorbió)."""
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
    absorbe = [{"id_v2": x["id"], "procedimental": x["procedimental"]} for x in corr["sin_par"]
               if x["absorbido_por"] == i]
    marcos = [{"codigo": a.destino.removeprefix("OBJ:"), "marco": nav.por_id[a.destino].props.get("marco"),
               "objetivo": nav.por_id[a.destino].etiqueta}
              for a in nav.aristas if a.origen == tid and a.tipo.value == "CUBRE" and a.destino in nav.por_id]
    conceptos_pedagogicos = {*todos, *(b.concepto for b in bases if b.profundidad == 1)}
    actividades = [a for a in ped.actividades.values() if tid in a.get("objetivos", [])
                   or set(a.get("evalua", [])) & set(todos)]
    dificultades = [d for d in ped.dificultades.values() if d.get("concepto") in conceptos_pedagogicos]
    microtemas = [m for m in ped.microtemas.values() if m.get("concepto") in conceptos_pedagogicos]
    experimentos = [e for e in ped.experimentos.values() if tid in [vigente_de(o) for o in e.get("objetivos", [])]]
    refuerzos = []
    p_ref = ruta("data/interim/refuerzo_v3/refuerzos.json")
    if p_ref.exists():
        refuerzos = [{k: r.get(k) for k in ("id", "decision", "forma", "refuerzo", "fila", "estado", "origen")}
                     for r in json.loads(p_ref.read_text(encoding="utf-8")) if r.get("tema_ancla") == i]
    datos = _datos_referencia(todos)
    faltan_datos = [e["id"] for e in [*actividades, *experimentos, *microtemas] if _hace_falta_un_dato(e)]
    fuentes = _fuentes_paises(principales + [c for c in todos if c not in principales], t.grado)
    elementos = [*actividades, *dificultades, *microtemas, *experimentos]
    sin_revisar = sorted(e["id"] for e in elementos if e.get("estado") == "propuesta_pendiente")
    completitud = {
        "texto_crudo": "completo" if fuentes and textos_completos().get(i) else "parcial",
        "ideas_previas": "completo" if len(dificultades) >= 2 else "parcial" if dificultades else "falta",
        "experimentos": "completo" if experimentos else "falta",
        "capa_pedagogica": "completo" if sum(a.get("rol") == "objetivo" for a in actividades) >= 2 and microtemas
        else "parcial" if actividades or microtemas else "falta",
        "datos_de_referencia": "completo" if datos and not faltan_datos else
        ("pendiente_de_fuente" if faltan_datos or not datos else "parcial"),
        "revision_del_panel": "completa" if elementos and not sin_revisar else "pendiente" if elementos else "—",
    }
    return {
        "aviso": AVISO,
        "tema": {"id": i, "grado": t.grado, "asignatura": nodo.asignatura, "archivo": t.ruta, "hoja": t.hoja,
                 "fila": t.fila, "unidad": t.unidad, "contenido": t.contenido, "subcontenido": t.subcontenido,
                 "procedimental": t.procedimental, "indicador": t.indicador, "evidencia": t.evidencia,
                 "habilidad_timss": t.habilidad_timss, "competencia_pisa": t.competencia_pisa,
                 "microhabilidades_pisa": t.micro_pisa, "texto_completo_de_la_fila": textos_completos().get(i),
                 "origen_frente_a_la_v2": t.origen, "absorbe_de_la_v2": absorbe},
        "conceptos": [{"id": c, "nombre": nav.por_id[c].etiqueta, "definicion": nav.por_id[c].props.get("definicion"),
                       "rol": "principal" if c in principales else "secundario"} for c in todos],
        "bases": [{"concepto": b.concepto, "nombre": nav.por_id[b.concepto].etiqueta, "profundidad": b.profundidad,
                   "la_malla_la_enseña_antes": b.antes_del_objetivo, "primer_tema": b.primer_tema} for b in bases],
        "fuentes": {"paises": fuentes, "marcos": marcos},
        "ideas_previas": [{k: d.get(k) for k in ("id", "concepto", "descripcion", "senales", "estado", "fuente")}
                          for d in dificultades],
        "actividades": actividades, "microtemas": microtemas, "experimentos": experimentos,
        "datos_de_referencia": {"valores": datos, "hacen_falta_en": faltan_datos,
                                "fuente_esperada": "tabla de referencia citable en data/fuentes/ (pendiente)"
                                if not datos else None},
        "refuerzo_de_la_malla": refuerzos,
        "completitud": completitud,
        "sin_revision_del_panel": sin_revisar,
    }


def _markdown(p: dict) -> str:
    t = p["tema"]
    md = [f"# Paquete de clase: {t['id']} ({t['grado']}.°, {t['asignatura']})", "", f"> {p['aviso']}", "",
          "## Completitud", "", "| Hueco | Estado |", "|---|---|"]
    md += [f"| {k.replace('_', ' ')} | {v} |" for k, v in p["completitud"].items()]
    md += ["", "## Tema (malla V3, texto crudo)", "",
           f"- **Ubicación:** {t['archivo']}, hoja «{t['hoja']}», fila {t['fila']}",
           f"- **Contenido:** {t['contenido']} — {t['subcontenido']}", f"- **Procedimental:** {t['procedimental']}",
           f"- **Indicador:** {t['indicador']}", f"- **Evidencia:** {t['evidencia']}"]
    if t["absorbe_de_la_v2"]:
        md.append("- **Absorbe de la V2:** " + "; ".join(f"{a['id_v2']} ({a['procedimental']})"
                                                          for a in t["absorbe_de_la_v2"]))
    md += ["", "## Conceptos y bases", ""]
    md += [f"- **{c['nombre']}** ({c['rol']}): {c['definicion'] or ''}" for c in p["conceptos"]]
    md += [f"- Base: {b['nombre']} (profundidad {b['profundidad']}; "
           f"{'la malla la enseña antes' if b['la_malla_la_enseña_antes'] else 'NO la enseña antes'})"
           for b in p["bases"]]
    md += ["", "## Fuentes de los países (texto original)", "",
           "| País | Nivel | SV | Documento, página | Texto original | Paráfrasis |", "|---|---|---|---|---|---|"]
    md += [f"| {f['pais']} | {f['nivel']} | {f['grado_sv']} | {str(f['documento']).split('/')[-1]}, "
           f"p. {f['pagina']} | {str(f['texto_original'])[:200]} | {str(f['texto_es'])[:200]} |"
           for f in p["fuentes"]["paises"]]
    md += ["", "## Marcos", ""] + [f"- {m['marco']} {m['codigo']}: {m['objetivo']}" for m in p["fuentes"]["marcos"]]
    md += ["", "## Ideas previas erróneas", ""]
    md += [f"- **{d['id']}** ({d['estado']}): {d['descripcion']} *Señal:* {d['senales']}" for d in p["ideas_previas"]]
    md += ["", "## Experimentos con procedimiento", ""]
    for e in p["experimentos"]:
        md += [f"### {e['titulo']} ({e['id']}, {e.get('duracion_min')} min, {e.get('estado')})", "",
               f"**Propósito:** {e['proposito']}", "", "**Materiales:** " + "; ".join(e["materiales"]), "",
               "**Procedimiento:**", *[f"{k}. {s.split('. ', 1)[-1]}" for k, s in enumerate(e["procedimiento"], 1)],
               "", "**Seguridad:** " + "; ".join(e["seguridad"]), "", f"**Datos esperados:** {e['datos_esperados']}",
               "", "**Análisis:** " + " | ".join(e["analisis"]), ""]
    md += ["## Actividades", ""]
    md += [f"- **{a['id']}** ({a.get('rol')}, {a.get('habilidad')}, {a.get('formato')}): "
           f"{a.get('enunciado', '')[:220]}" for a in p["actividades"]]
    md += ["", "## Datos de referencia", ""]
    d = p["datos_de_referencia"]
    md += ([f"- {v}" for v in d["valores"]] or [f"- **Pendiente de fuente.** Hacen falta en: "
                                                 f"{', '.join(d['hacen_falta_en']) or '—'}."])
    if p["refuerzo_de_la_malla"]:
        md += ["", "## Refuerzo de la malla que toca este tema (propuesta GOES, no MINED)", ""]
        md += [f"- {r['id']} ({r['estado']}): {r['refuerzo']}" for r in p["refuerzo_de_la_malla"]]
    if p["sin_revision_del_panel"]:
        md += ["", f"*Sin revisión del panel todavía: {len(p['sin_revision_del_panel'])} elementos.*"]
    return "\n".join(md) + "\n"


def escribir(temas: list[str]) -> list:
    """Escribe <SALIDA>/<tema>.json y .md, y el índice con la completitud de cada paquete."""
    d = ruta(SALIDA)
    d.mkdir(parents=True, exist_ok=True)
    escritos, filas = [], []
    for tema in temas:
        p = paquete(tema)
        i = p["tema"]["id"]
        (d / f"{i}.json").write_text(json.dumps(p, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (d / f"{i}.md").write_text(_markdown(p), encoding="utf-8")
        escritos += [d / f"{i}.json", d / f"{i}.md"]
        filas.append((tema, i, p["completitud"]))
    claves = list(filas[0][2]) if filas else []
    md = ["# Paquetes de clase", "", AVISO, "", "| Pedido | Tema vigente | " + " | ".join(c.replace("_", " ")
                                                                                         for c in claves) + " |",
          "|---|---|" + "---|" * len(claves)]
    md += [f"| {pedido} | [{i}]({i}.md) | " + " | ".join(c[k] for k in claves) + " |" for pedido, i, c in filas]
    (d / "README.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return escritos
