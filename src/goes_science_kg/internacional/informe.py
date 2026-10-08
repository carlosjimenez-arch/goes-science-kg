"""Informes del contraste internacional de 9.°–11.° (spec 11): internacional/<asignatura>.md, Excel con fórmulas y
CSV de revisión humana."""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict

from goes_science_kg.config import cargar, ruta
from goes_science_kg.internacional import contraste, profundidad, visor
from goes_science_kg.internacional.consenso import _cargar_etiquetas, objetivos, paises

DIR = "internacional"
NOMBRE = {"fisica": "Física", "quimica": "Química", "biologia": "Biología",
          "tierra_espacio": "Ciencias de la Tierra y del Espacio"}
CLASES = [
    ("faltante", "Faltantes del núcleo común",
     "El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°."),
    ("no_retomado", "No retomados en 9.°–11.°",
     "La V2 solo lo ve antes de 9.°; al menos 5 países lo profundizan en su núcleo de 9.°–11.°."),
    ("tardio", "Llegan tarde",
     "La V2 lo introduce en 9.°–11.°, dos o más grados después de que el núcleo alcanza el consenso."),
    ("solo_especializacion", "Nivel de especialización en un curso obligatorio",
     "La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos."),
    ("adelantado", "Adelantados",
     "La V2 lo introduce en 9.°–11.°, 1,5 grados o más antes que la mediana del núcleo de los países."),
    ("sin_referente", "Sin referente", "La V2 lo enseña en 9.°–11.° y ninguno de los 9 países lo tiene."),
    ("alineado", "Alineados", "La V2 lo introduce en 9.°–11.° con un momento coherente con el consenso (± 1,5 grados)."),
    ("retomado", "Retomados", "La V2 lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.° (espiral)."),
    ("previo", "Solo antes de 9.°", "La V2 lo ve antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°."),
]
SIN_TABLA = {"alineado", "retomado", "previo"}


def _cita(o: dict) -> str:
    lugar = f"p. {o['pagina']}" if o.get("pagina") else (o.get("localizador") or "")
    nivel = "núcleo" if o["nivel"] == "nucleo" else "esp."
    return f"{o['pais']} · {o['curso']} [{nivel}] ({o['documento']}, {lugar}): «{o['texto']}»"


def _tema(t: dict) -> str:
    return f"{t['id']} ({t['archivo'].split('/')[-1]}, hoja «{t['hoja']}», fila {t['fila']})"


def _grados_sv(f: dict, r: dict) -> str:
    if not f["sv_primer_grado"]:
        return "no está"
    gs = sorted({r["temas"][t]["grado"] for t in f["sv_temas"]})
    return f"{gs[0]}.°" if len(gs) == 1 else f"{gs[0]}.°–{gs[-1]}.°"


def _tabla(filas: list[dict], r: dict, objs: dict, max_filas: int = 40) -> list[str]:
    lineas = ["| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) "
              "| Evidencia |", "|---|---|---|---|---|"]
    for f in filas[:max_filas]:
        g = f["grado_consenso"]
        prop = f["proporcion_nucleo"].get(str(g)) if g else None
        med = f["mediana_primer_grado_nucleo"]
        cons = (f"{g}.° ({prop:.0%} de los países con núcleo)" if g else (f"mediana {med:g}" if med else "—"))
        cons += f"; {f['n_nucleo_9_11']} con núcleo en 9.°–11.°"
        ev = []
        if f["sv_temas"]:
            ev.append("SV: " + _tema(r["temas"][f["sv_temas"][0]]))
        citados = 0
        for d in f["paises"].values():
            if citados == 2:
                break
            if d["objetivos"] and d["objetivos"][0] in objs:
                ev.append(_cita(objs[d["objetivos"][0]]))
                citados += 1
        if f.get("revision"):
            ev.append(f"Revisión experta: {f['revision']['justificacion']}")
        lineas.append(f"| {f['nombre']} | {_grados_sv(f, r)} | {cons} | {contraste.evidencia_paises(f)} "
                      f"| {'<br>'.join(ev)} |")
    if len(filas) > max_filas:
        lineas.append(f"\n_… y {len(filas) - max_filas} más en el Excel._")
    return lineas


def _orden(f: dict) -> tuple:
    if f["clase"] in ("no_retomado", "faltante"):
        return (-f["n_nucleo_9_11"], f["nombre"])
    if f["clase"] == "solo_especializacion":
        return (-f["n_especializacion"], f["nombre"])
    g = f["grado_consenso"]
    return (-(f["proporcion_nucleo"].get(str(g), 0) if g else 0), f["nombre"])


def _sensibilidad(filas: list[dict]) -> str:
    """Cuántos conceptos cambiarían de clase con 4 países en lugar de 5 (empate en 8 núcleos)."""
    n4 = sum(f["clase"] == "previo" and f["n_nucleo_9_11"] == contraste.MIN_PAISES - 1 for f in filas)
    return (f"Sensibilidad: con 4 países en lugar de {contraste.MIN_PAISES}, {n4} conceptos más pasarían de «solo "
            f"antes de 9.°» a «no retomados».")


def _seccion_profundidad(asig: str, prof: dict) -> list[str]:
    d = prof["asignaturas"].get(asig)
    if not d:
        return []
    md = ["## Profundidad: demanda cognitiva en 9.°–11.°", "",
          "Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin "
          "verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: "
          f"{prof['acuerdo_con_ia']['proporcion']:.0%} (la diferencia principal: TIMSS pone «explicar» en aplicar).", "",
          "| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |", "|---|---|---|---|---|---|"]
    for quien in ["SV", *d["paises"]]:
        f = d["filas"].get(quien)
        if not f:
            continue
        con = sum(f["demanda"].get(n, 0) for n in profundidad.NIVELES) or 1
        pct = [f"{f['demanda'].get(n, 0) / con:.0%}" for n in profundidad.NIVELES]
        nombre = "**El Salvador (V2)**" if quien == "SV" else quien
        md.append(f"| {nombre} | {f['n']} | {' | '.join(pct)} | {f['demanda'].get('sin_verbo', 0)} |")
    return [*md, ""]


def _seccion_practicas(asig: str, prof: dict) -> list[str]:
    d = prof["asignaturas"].get(asig)
    if not d:
        return []
    md = ["## Prácticas científicas en 9.°–11.°", "",
          "La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la "
          "proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.", "",
          "| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |",
          "|---|---|---|---|---|---|"]
    for quien in ["SV", *d["paises"]]:
        f = d["filas"].get(quien)
        if not f:
            continue
        fam = [str(f["familias"].get(k, 0)) for k in ("indagacion", "modelacion", "argumentacion",
                                                      "naturaleza_y_contexto")]
        nombre = "**El Salvador (V2)**" if quien == "SV" else quien
        md.append(f"| {nombre} | {' | '.join(fam)} | {len(f['practicas'])} |")
    aus = d["practicas_ausentes"]
    md += ["", "Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 9.°–11.°: "
           + (", ".join(f"`{p}`" for p in aus) if aus else "ninguna."), ""]
    return md


def escribir() -> dict:
    r = contraste.clasificar()
    prof = profundidad.analizar()
    objs = {o["id"]: o for o in objetivos()}
    cfg = cargar("internacional")
    base = ruta(DIR)
    base.mkdir(parents=True, exist_ok=True)
    res = contraste.resumen(r)
    propuestos = _propuestos(objs)
    for asig in contraste.ASIGNATURAS:
        filas = [f for f in r["filas"] if f["asignatura"] == asig]
        md = [f"# {NOMBRE[asig]} · contraste internacional de 9.°–11.° (malla V2)", "",
              "> Generado por `gskg internacional construir`. Método y límites: `specs/11_grafos_internacionales_9_11.md`"
              " y `internacional/README.md`.",
              "> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para",
              "> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.", "",
              "## Resumen", "", "| Clase | Conceptos | Qué significa |", "|---|---|---|"]
        for clave, titulo, desc in CLASES:
            md.append(f"| {titulo} | {res[asig].get(clave, 0)} | {desc} |")
        md += ["", "Países con núcleo común por grado SV (denominador del consenso): "
               + "; ".join(f"{g}.°: {', '.join(r['paises_con_nucleo'][str(g)])}" for g in contraste.GRADOS), "",
               _sensibilidad(filas), ""]
        rev = [f for f in filas if f.get("revision")]
        if rev:
            md += [f"Revisión experta: {len(rev)} conceptos cambiaron de clase frente a la regla automática "
                   "(`data/interim/internacional/revisiones.json`): "
                   + "; ".join(f"{f['nombre']} ({f['clase_ia']} → {f['clase']})" for f in rev) + ".", ""]
        for clave, titulo, desc in CLASES:
            if clave in SIN_TABLA:
                continue
            sel = sorted((f for f in filas if f["clase"] == clave), key=_orden)
            if sel:
                md += [f"## {titulo} ({len(sel)})", "", desc, "", *_tabla(sel, r, objs), ""]
        sec = [s for s in r["secuencia"] if s["concepto"] in {f["concepto"] for f in filas}]
        if sec:
            md += [f"## Candidatos a error de secuencia en la V2 ({len(sec)})", "",
                   "El prerrequisito llega después que el concepto que lo necesita (grafo de prerrequisitos del repo). "
                   "Son candidatos: en la revisión manual de 2026-10-08, 2 de 4 resultaron falsos porque el etiquetado "
                   "no vio el prerrequisito en primaria. Los confirmados están en `internacional/README.md`.",
                   "", "| Concepto (grado) | Prerrequisito que llega después (grado) | Confianza | Tema SV |",
                   "|---|---|---|---|"]
            for s in sec:
                md.append(f"| {s['nombre_concepto']} ({s['grado_concepto']}.°) | {s['nombre_prerrequisito']} "
                          f"({s['grado_prerrequisito']}.°) | {s['confianza']} | {s['tema_concepto']} |")
            md.append("")
        md += _seccion_profundidad(asig, prof) + _seccion_practicas(asig, prof)
        top = [p for p in propuestos.get(asig, []) if p["n_paises"] >= 3][:15]
        if top:
            md += ["## Conceptos que el vocabulario no tiene (propuestos para triaje)", "",
                   "El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no "
                   "existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.", "",
                   "| Propuesto | Países | Con núcleo |", "|---|---|---|"]
            md += [f"| {p['nombre']} | {', '.join(p['paises'])} | {', '.join(p['nucleo']) or '—'} |" for p in top]
            md.append("")
        (base / f"{asig}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        _excel(asig, filas, base)
    revision = _revision(objs, base)
    visor.escribir(r, CLASES + [("no_aplica", "Sin exigencia", "Ni la V2 ni el núcleo internacional lo exigen.")],
                   NOMBRE, base)
    (base / "contraste.json").write_text(json.dumps(
        {"resumen": res, "filas": r["filas"], "secuencia": r["secuencia"], "profundidad": prof,
         "propuestos": propuestos}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"resumen": res, "paises": list(cfg["paises"]), "secuencia": len(r["secuencia"]),
            "revision_humana": revision}


def _norma(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))
    return " ".join(re.sub(r"\b(de|del|la|las|los|el|y|en|sus)\b", " ", s).split())


def _propuestos(objs: dict) -> dict[str, list[dict]]:
    """Nombres propuestos por el etiquetado de los países (no son ids), agrupados por asignatura."""
    por: dict[tuple[str, str], dict] = {}
    for i, e in _cargar_etiquetas("pais_").items():
        o = objs.get(i)
        if not o or not o["asignatura"]:
            continue
        for p in e["propuestos"]:
            if p.startswith(("CON:", "PRAC:")):
                continue
            d = por.setdefault((o["asignatura"], _norma(p)), {"nombre": p, "paises": set(), "nucleo": set()})
            d["paises"].add(o["pais"])
            if o["nivel"] == "nucleo":
                d["nucleo"].add(o["pais"])
    salida: dict[str, list[dict]] = defaultdict(list)
    for (asig, _), d in sorted(por.items()):
        salida[asig].append({"nombre": d["nombre"], "paises": sorted(d["paises"]), "nucleo": sorted(d["nucleo"]),
                             "n_paises": len(d["paises"])})
    for v in salida.values():
        v.sort(key=lambda d: (-len(d["nucleo"]), -d["n_paises"], d["nombre"]))
    return dict(sorted(salida.items()))


def _revision(objs: dict, base) -> dict:
    """CSV de revisión humana: objetivos «parcial» y etiquetas de confianza baja."""
    etq = _cargar_etiquetas("pais_")
    filas = []
    for i, o in sorted(objs.items()):
        e = etq.get(i, {})
        motivos = []
        if o["validacion"]["veredicto"] == "parcial":
            motivos.append(f"extracción parcial: {o['validacion']['motivo']}")
        if e.get("confianza") == "baja":
            motivos.append(f"etiqueta de confianza baja: {e.get('justificacion', '')}")
        if motivos:
            filas.append({"id": i, "pais": o["pais"], "documento": o["documento"], "pagina": o.get("pagina") or "",
                          "curso": o["curso"], "nivel": o["nivel"], "texto": o["texto"], "cita": o["cita"],
                          "conceptos": " ".join(e.get("principales", []) + e.get("secundarios", [])),
                          "motivo": " | ".join(motivos), "decision": "", "revisado_por": ""})
    with (base / "revision_humana.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]) if filas else ["id"])
        w.writeheader()
        w.writerows(filas)
    return {"filas": len(filas)}


def _excel(asig: str, filas: list[dict], base) -> None:
    """Hoja Datos (valores), Contraste (todo número es fórmula sobre Datos) y Resumen (conteos por clase)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter as col

    ps = paises()
    n = len(ps)
    wb = Workbook()
    d = wb.active
    d.title = "Datos"
    d.append(["Concepto", "Clase (IA)", "Grado SV V2", "Grado SV en 9-11", *[f"{p} nucleo" for p in ps],
              *[f"{p} nucleo 9-11" for p in ps], *[f"{p} esp" for p in ps]])
    for f in filas:
        fp = [f["paises"].get(p, {}) for p in ps]
        d.append([f["nombre"], f["clase"], f["sv_primer_grado"], f.get("sv_9_11"),
                  *[x.get("primer_grado_nucleo") for x in fp], *[1 if x.get("nucleo_9_11") else None for x in fp],
                  *[1 if x.get("en_especializacion") else None for x in fp]])
    a0, a1 = col(5), col(4 + n)
    b0, b1 = col(5 + n), col(4 + 2 * n)
    c0, c1 = col(5 + 2 * n), col(4 + 3 * n)
    c = wb.create_sheet("Contraste")
    c.append(["Concepto", "Grado SV V2", "Paises con nucleo", "Mediana nucleo", "Paises con especializacion",
              "Diferencia SV - mediana", "Grado SV en 9-11", "Paises con nucleo en 9-11", "Lectura (regla simplificada)",
              "Clase oficial"])
    for i in range(2, len(filas) + 2):
        c.append([f"=Datos!A{i}", f"=IF(Datos!C{i}=\"\",\"\",Datos!C{i})", f"=COUNT(Datos!{a0}{i}:{a1}{i})",
                  f'=IF(C{i}=0,"",MEDIAN(Datos!{a0}{i}:{a1}{i}))', f"=COUNT(Datos!{c0}{i}:{c1}{i})",
                  f'=IF(OR(B{i}="",D{i}=""),"",B{i}-D{i})', f"=IF(Datos!D{i}=\"\",\"\",Datos!D{i})",
                  f"=COUNT(Datos!{b0}{i}:{b1}{i})",
                  f'=IF(B{i}="",IF(C{i}>=5,"falta en SV",""),IF(G{i}="",IF(H{i}>=5,"no retomado en 9-11","previo"),'
                  f'IF(B{i}<9,"retomado",IF(AND(C{i}<=1,E{i}>=3),"solo especializacion",IF(F{i}="","coherente",'
                  f'IF(F{i}<=-1.5,"SV adelantado",IF(F{i}>=2,"SV tarde","coherente")))))))',
                  f"=Datos!B{i}"])
    r = wb.create_sheet("Resumen")
    r.append(["Clase", "Conceptos"])
    ultima = len(filas) + 1
    for clave, _, _ in CLASES:
        fila = r.max_row + 1
        r.append([clave, f"=COUNTIF(Datos!B2:B{ultima},A{fila})"])
    r.append(["Total", f"=SUM(B2:B{r.max_row})"])
    verde = PatternFill("solid", fgColor="1E4D3A")
    for hoja in (d, c, r):
        for celda in hoja[1]:
            celda.fill, celda.font = verde, Font(color="FFFFFF", bold=True)
        hoja.column_dimensions["A"].width = 48
        hoja.freeze_panes = "B2"
    wb.save(base / f"Contraste_{asig}.xlsx")
