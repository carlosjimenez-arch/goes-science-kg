"""Grafos por grado: el subgrafo que vive un estudiante de El Salvador en un grado dado.

Para el grado g:
- núcleo: temas de g (de las 4 asignaturas), los conceptos y prácticas que trabajan y los objetivos de marco
  que cubren;
- anclajes: prerrequisitos (directos) de los conceptos de g, con su estado:
  previo (la malla lo trabaja antes de g) · mismo_grado · posterior (la malla lo trabaja después) · ausente;
- referentes: objetivos de los países de referencia cuyo grado equivalente es g y que comparten un objetivo de marco.

Diagnóstico didáctico (lo que el equipo curricular necesita ver):
- conceptos nuevos en g vs. conceptos que se retoman (espiral);
- prerrequisitos que llegan tarde o nunca;
- conceptos que la mediana de los países ya trabaja a esta altura y El Salvador todavía no.

Salidas: data/grafo/grados/G<gg>/{nodos,aristas}.jsonl + diagnostico.json, y grados/G<gg>/ficha.md.
"""

from __future__ import annotations

import html as h
import json
from collections import Counter, defaultdict

from goes_science_kg.comunidades import comunidades_grado
from goes_science_kg.config import cargar, ruta
from goes_science_kg.grafo.almacen import guardar
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.prerrequisitos import evidencia_orden, paises_alto_desempeno
from goes_science_kg.visor import escribir_visor

GRADOS = range(2, 12)
NOMBRE_ASIG = {k: v["nombre"] for k, v in cargar("asignaturas")["asignaturas"].items()}


def _indices(aristas: list[Arista]):
    sal, ent = defaultdict(list), defaultdict(list)
    for a in aristas:
        sal[a.origen].append(a)
        ent[a.destino].append(a)
    return sal, ent


def subgrafo(g: int, nodos: list[Nodo], aristas: list[Arista], ev: dict[str, dict]) -> tuple[list, list, dict]:
    por_id = {n.id: n for n in nodos}
    sal, ent = _indices(aristas)
    temas = [n for n in nodos if n.tipo == TipoNodo.TEMA and n.grado == g and n.asignatura]
    ids = {f"GRADO:{g:02d}"} | {t.id for t in temas}
    conceptos, practicas, objetivos = Counter(), Counter(), set()
    for t in temas:
        for a in sal[t.id]:
            if a.tipo == TipoArista.TRABAJA:
                (conceptos if a.destino.startswith("CON:") else practicas)[a.destino] += 1
            elif a.tipo == TipoArista.CUBRE:
                objetivos.add(a.destino)
            if a.tipo in (TipoArista.DE_ASIGNATURA, TipoArista.FUENTE):
                ids.add(a.destino)
    ids |= set(conceptos) | set(practicas) | objetivos

    # Anclajes: prerrequisitos directos de los conceptos del grado.
    anclajes = []
    for c in conceptos:
        for a in ent[c]:
            if a.tipo != TipoArista.PRERREQUISITO_DE:
                continue
            primero = ev.get(a.origen, {}).get("sv")
            estado = ("ausente" if primero is None else "previo" if primero < g
                      else "mismo_grado" if primero == g else "posterior")
            anclajes.append({"prerrequisito": a.origen, "concepto": c, "estado": estado, "primer_grado_sv": primero,
                             "confianza": a.confianza.value if a.confianza else None})
            ids.add(a.origen)

    # Referentes: objetivos de países del mismo grado equivalente que comparten objetivo de marco.
    def _en_grado(op: Nodo) -> bool:  # un objetivo por banda (p. ej. KS3 = 5.°–7.°) cuenta en cada grado que cubre
        gmin = op.props.get("grado_min") or 0
        return gmin <= g <= (op.props.get("grado_max") or gmin)

    referentes = [a.origen for o in sorted(objetivos) for a in ent[o]
                  if a.tipo == TipoArista.ALINEA_CON and _en_grado(por_id[a.origen])]
    ids |= set(referentes)

    sub_nodos = [por_id[i] for i in sorted(ids) if i in por_id]
    sub_aristas = [a for a in aristas if a.origen in ids and a.destino in ids]

    nuevos = [c for c in conceptos if ev.get(c, {}).get("sv") == g]
    retomados = [c for c in conceptos if (ev.get(c, {}).get("sv") or 99) < g]
    # Mencionados aquí de forma secundaria, pero enseñados de verdad en un grado posterior.
    anticipados = [c for c in conceptos if (ev.get(c, {}).get("sv") or 0) > g]
    faltantes_edad = sorted(
        (c for c, e in ev.items()
         if e["paises_mediana"] is not None and e["paises_mediana"] <= g and len(e["paises"]) >= 2
         and (e["sv"] is None or e["sv"] > g) and e["sv"] != g),
        key=lambda c: (ev[c]["paises_mediana"], c))
    diagnostico = {
        "grado": g,
        "temas": len(temas),
        "temas_por_asignatura": dict(Counter(t.asignatura for t in temas)),
        "conceptos": len(conceptos), "conceptos_nuevos": len(nuevos),
        "conceptos_retomados": len(retomados), "conceptos_anticipados": len(anticipados),
        "practicas": dict(sorted(practicas.items(), key=lambda x: (-x[1], x[0]))),
        "objetivos_marco": dict(sorted(Counter(por_id[o].props.get("marco") for o in objetivos).items())),
        "anclajes": sorted(anclajes, key=lambda x: (x["estado"], x["concepto"])),
        "faltantes_por_edad": [{"concepto": c, "sv": ev[c]["sv"], "paises": ev[c]["paises"]}
                               for c in faltantes_edad if not _ya_trabajado(c, ev, g)],
        "referentes_paises": len(set(referentes)),
        "top_conceptos": sorted(conceptos.items(), key=lambda x: (-x[1], x[0]))[:15],
    }
    return sub_nodos, sub_aristas, diagnostico


def _ya_trabajado(c: str, ev: dict, g: int) -> bool:
    return ev[c]["sv"] is not None and ev[c]["sv"] <= g


def _ficha(d: dict, por_id: dict[str, Nodo]) -> str:
    nombre = lambda i: por_id[i].etiqueta if i in por_id else i  # noqa: E731
    g = d["grado"]
    md = [f"# Grafo del {g}.° grado", "",
         "> Generado por `gskg grados construir`. No editar a mano. Subgrafo en "
         f"`data/grafo/grados/G{g:02d}/`.", "",
         "## Resumen", "",
         "| Asignatura | Temas |", "|---|---|",
         *[f"| {NOMBRE_ASIG[a]} | {k} |" for a, k in sorted(d["temas_por_asignatura"].items())],
         "", f"- **{d['conceptos']} conceptos**: {d['conceptos_nuevos']} nuevos en este grado, "
         f"{d['conceptos_retomados']} que se retoman de grados anteriores y {d['conceptos_anticipados']} que solo se "
         "mencionan aquí y se enseñan de lleno más adelante.",
         "- Objetivos de marco cubiertos: "
         + ", ".join(f"{m} {k}" for m, k in sorted(d["objetivos_marco"].items())) + ".",
         "- Objetivos de países de referencia del mismo grado que comparten objetivo de marco: "
         f"{d['referentes_paises']}.",
         "", "## Conceptos más trabajados", "",
         "| Concepto | Asignatura | Temas |", "|---|---|---|",
         *[f"| {nombre(c)} | {NOMBRE_ASIG.get(por_id[c].asignatura, '—') if c in por_id else '—'} | {k} |"
           for c, k in d["top_conceptos"]], ""]
    if d.get("comunidades"):
        md += ["## Bloques temáticos del grado", "",
               "Comunidades de conceptos (Louvain sobre co-ocurrencia en temas y prerrequisitos).", "",
               "| Bloque | Conceptos | Temas | Asignaturas | Unidades |", "|---|---|---|---|---|",
               *[f"| {c.get('titulo') or c['nombre']} | {len(c['conceptos'])} | {len(c['temas'])} | "
                 + ", ".join(NOMBRE_ASIG.get(a, a) for a in c["asignaturas"]) + " | "
                 + "; ".join(u for u in c["unidades"][:3] if u) + " |"
                 for c in d["comunidades"] if len(c["conceptos"]) >= 2], ""]
        resumidos = [c for c in d["comunidades"] if c.get("resumen_ia")]
        if resumidos:
            md += ["### Qué se aprende en cada bloque", "",
                   *[f"- **{c['titulo']}.** {c['resumen_ia']}" for c in resumidos], ""]
    if d["practicas"]:
        md += ["## Prácticas científicas", "", "| Práctica | Temas |", "|---|---|",
              *[f"| {nombre(p)} | {k} |" for p, k in d["practicas"].items()], ""]
    problemas = [a for a in d["anclajes"] if a["estado"] in ("ausente", "posterior")]
    md += ["## Prerrequisitos que no llegan a tiempo", "",
          "Conceptos de este grado cuyo prerrequisito la malla trabaja **después** o **nunca**.", ""]
    if problemas:
        md += ["| Concepto del grado | Prerrequisito | Estado | Primer grado SV | Confianza |", "|---|---|---|---|---|",
              *[f"| {nombre(a['concepto'])} | {nombre(a['prerrequisito'])} | {a['estado']} | "
                f"{a['primer_grado_sv'] or '—'} | {a['confianza'] or '—'} |" for a in problemas], ""]
    else:
        md += ["Ninguno.", ""]
    mismo = [a for a in d["anclajes"] if a["estado"] == "mismo_grado"]
    if mismo:
        md += [f"Además, {len(mismo)} prerrequisitos se enseñan en este mismo grado: "
               "hay que cuidar el orden de las unidades.", ""]
    md += ["## Lo que los países de referencia ya enseñan a esta altura", "",
          "Conceptos que la mediana de al menos dos países trabaja en este grado o antes, y que El Salvador "
          "todavía no trabaja.", ""]
    if d["faltantes_por_edad"]:
        md += ["| Concepto | Primer grado SV | Países (primer grado) |", "|---|---|---|",
              *[f"| {nombre(f['concepto'])} | {f['sv'] or 'nunca'} | "
                + ", ".join(f"{p} {k}" for p, k in sorted(f["paises"].items())) + " |"
                for f in d["faltantes_por_edad"]], ""]
    else:
        md += ["Ninguno.", ""]
    return "\n".join(md)


def _hallazgos(diags: list[dict], por_id: dict[str, Nodo], ev: dict) -> None:
    """grados/HALLAZGOS.md: una página con lo accionable de cada grado (para el equipo curricular)."""

    alto = paises_alto_desempeno()
    nombre = lambda i: por_id[i].etiqueta if i in por_id else i  # noqa: E731
    md = ["# Hallazgos por grado", "",
          "Resumen de los grafos por grado: lo que conviene revisar primero. Detalle en `G<grado>/ficha.md`.",
          "- **Secuencia**: prerrequisitos de confianza alta que la malla enseña después del concepto que los",
          "  necesita, o nunca.",
          "- **Alto desempeño**: conceptos que al menos dos países de alto desempeño (top 10 de TIMSS 2023 Ciencias",
          "  con datos en el grafo) ya enseñan a esta edad y El Salvador todavía no.",
          "",
          "> Son **candidatos a revisar**, no conclusiones: dependen de etiquetas y prerrequisitos propuestos por IA",
          "> (con su confianza) que el equipo de Ciencias debe validar (`asignaturas/<x>/revision/`).", ""]
    for d in diags:
        g = d["grado"]
        sec = [a for a in d["anclajes"] if a["estado"] in ("ausente", "posterior") and a["confianza"] == "alta"]
        faltan = [f for f in d["faltantes_por_edad"]
                  if sum(1 for p, gp in f["paises"].items() if p in alto and gp <= g) >= 2]
        md += [f"## {g}.° grado", "",
               f"{d['temas']} temas · {d['conceptos']} conceptos ({d['conceptos_nuevos']} nuevos) · "
               f"[ficha](G{g:02d}/ficha.md) · [visor](G{g:02d}/grafo.html)", ""]
        md += ["**Secuencia:** " + ("; ".join(
            f"{nombre(a['concepto'])} necesita {nombre(a['prerrequisito'])} ("
            + (f"{a['primer_grado_sv']}.°" if a["primer_grado_sv"] else "nunca") + ")" for a in sec[:6])
            + (f"; y {len(sec) - 6} más." if len(sec) > 6 else ".") if sec else "sin problemas de confianza alta."), ""]
        md += ["**Alto desempeño ya lo enseña:** " + ("; ".join(
            f"{nombre(f['concepto'])} (SV " + (f"{f['sv']}.°" if f["sv"] else "nunca") + ")" for f in faltan[:6])
            + (f"; y {len(faltan) - 6} más." if len(faltan) > 6 else ".") if faltan else "nada pendiente."), ""]
    (ruta("grados") / "HALLAZGOS.md").write_text("\n".join(md), encoding="utf-8")


def construir_grados(nodos: list[Nodo], aristas: list[Arista], version: str) -> list[dict]:
    ev = evidencia_orden(nodos, aristas)
    por_id = {n.id: n for n in nodos}
    resumen, diags = [], []
    for g in GRADOS:
        sn, sa, d = subgrafo(g, nodos, aristas, ev)
        guardar(sn, sa, f"{version}-G{g:02d}", directorio=f"data/grafo/grados/G{g:02d}")
        (ruta(f"data/grafo/grados/G{g:02d}") / "diagnostico.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        d["comunidades"] = comunidades_grado(g, nodos, aristas)
        (ruta(f"data/grafo/grados/G{g:02d}") / "comunidades.json").write_text(
            json.dumps(d["comunidades"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        p = ruta(f"grados/G{g:02d}")
        p.mkdir(parents=True, exist_ok=True)
        (p / "ficha.md").write_text(_ficha(d, por_id), encoding="utf-8")
        escribir_visor(g, sn, sa, d)
        diags.append(d)
        resumen.append({"grado": g, "nodos": len(sn), "aristas": len(sa), "temas": d["temas"],
                        "conceptos": d["conceptos"], "nuevos": d["conceptos_nuevos"],
                        "prerrequisitos_tarde": sum(a["estado"] in ("ausente", "posterior") for a in d["anclajes"]),
                        "faltantes_por_edad": len(d["faltantes_por_edad"]),
                        "comunidades": len(d["comunidades"])})
    _indice(resumen)
    _hallazgos(diags, por_id, ev)
    return resumen


def _indice(resumen: list[dict]) -> None:
    md = ["# Grafos por grado", "",
         "Abre [`index.html`](index.html) en el navegador para navegar todos los grados.",
         "Cada carpeta `G<grado>/` tiene",
         "la ficha del grafo de ese grado (`ficha.md`) y un visor interactivo (`grafo.html`). Se generan con",
         "`gskg grados construir`.", "",
         "| Grado | Temas | Conceptos | Nuevos | Prerrequisitos que llegan tarde | Faltantes frente a países "
         "| Nodos | Aristas |",
         "|---|---|---|---|---|---|---|---|",
         *[f"| [{r['grado']}.°](G{r['grado']:02d}/ficha.md) · [visor](G{r['grado']:02d}/grafo.html) | "
           f"{r['temas']} | {r['conceptos']} | {r['nuevos']} | "
           f"{r['prerrequisitos_tarde']} | {r['faltantes_por_edad']} | {r['nodos']} | {r['aristas']} |"
           for r in resumen],
         "", "Lo más accionable de cada grado, en una página: [`HALLAZGOS.md`](HALLAZGOS.md).",
         "Cómo leerlo: [`specs/09_grafos_por_grado.md`](../specs/09_grafos_por_grado.md).", ""]
    ruta("grados").mkdir(exist_ok=True)
    (ruta("grados") / "README.md").write_text("\n".join(md), encoding="utf-8")
    _indice_html(resumen)


NOTA_INDICE = ("Generado por gskg grados construir. Las relaciones propuestas por IA llevan confianza y están en "
               "revisión del equipo de Ciencias del MINED.")


def _indice_html(resumen: list[dict]) -> None:
    """grados/index.html: portada navegable de los grafos por grado (abre los visores)."""

    filas = "".join(
        f"<tr><td><a href='G{r['grado']:02d}/grafo.html'>{r['grado']}.° grado</a></td><td>{r['temas']}</td>"
        f"<td>{r['conceptos']}</td><td>{r['nuevos']}</td><td>{r['prerrequisitos_tarde']}</td>"
        f"<td>{r['faltantes_por_edad']}</td><td>{r['comunidades']}</td></tr>" for r in resumen)
    pagina = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Grafos de Ciencias por grado</title>
<style>:root{{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--borde:#e3e3dc;--verde:#1E4D3A}}
@media (prefers-color-scheme: dark){{:root{{--bg:#161614;--fg:#ececea;--muted:#a3a39c;--borde:#33332f;
--verde:#7fbf9f}}}}
body{{margin:0;padding:24px 16px;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--fg)}}
main{{max-width:880px;margin:auto}}h1{{font-size:22px}}p{{color:var(--muted);line-height:1.5}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:8px;border-bottom:1px solid var(--borde);text-align:right}}
th:first-child,td:first-child{{text-align:left}}th{{color:var(--verde)}}a{{color:var(--verde);font-weight:bold}}
.tabla{{overflow-x:auto}}</style></head><body><main>
<h1>Grafos de conocimiento de Ciencias por grado · El Salvador</h1>
<p>Cada grado muestra sus temas, los conceptos y prácticas que trabajan, los prerrequisitos que traen de grados
anteriores y la comparación con Uruguay, Colombia y Singapur. Haz clic en un grado para abrir su visor interactivo;
la ficha con el diagnóstico está en <code>G&lt;grado&gt;/ficha.md</code>.</p>
<div class="tabla"><table><thead><tr><th>Grado</th><th>Temas</th><th>Conceptos</th><th>Nuevos</th>
<th>Prerrequisitos que llegan tarde</th><th>Faltantes frente a países</th><th>Bloques temáticos</th></tr></thead>
<tbody>{filas}</tbody></table></div>
<p>{h.escape(NOTA_INDICE)}</p>
</main></body></html>"""
    (ruta("grados") / "index.html").write_text(pagina, encoding="utf-8")
