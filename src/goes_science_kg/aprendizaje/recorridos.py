"""Tres recorridos completos de ejemplo (spec 13), reproducibles: `gskg tutor recorridos` → aprendizaje/recorridos/.

Los estudiantes son SIMULADOS (un guion fija cada respuesta) y las actividades son «propuesta_pendiente»: los
recorridos demuestran que el ciclo funciona sobre datos reales del grafo, no que mejore el aprendizaje. Eso solo lo
puede mostrar un piloto con estudiantes.

El estado y la cola de propuestas de la demo se escriben en un directorio temporal: correr los recorridos no
modifica ninguna capa compartida (lo verifica tests/test_aprendizaje.py).
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from datetime import date
from pathlib import Path

from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.modelos import TipoArista

from .estudiante import Almacen, Perfil
from .pedagogia import Pedagogia, navegador_compartido
from .relaciones import Navegador, confianza
from .sesion import Guion, Sesion

FECHA = date(2026, 10, 12)

RECORRIDOS = [
    {"id": "R1", "archivo": "R1_difusion_osmosis.md", "estudiante": "EST-DEMO-1", "grado": 9,
     "objetivo": "TEMA:G09-CIE-U8-8.2",
     "titulo": "Difusión y ósmosis (Biología, 9.°): falta una base de grados anteriores",
     "muestra": "Una respuesta incorrecta abre hipótesis; dos sondeos confirman que falta «concentración» (3.°) y la "
                "membrana queda sin comprobar, no «en brecha». Refuerzo durante el aprendizaje y reevaluación con "
                "otra habilidad.",
     "guion": {"ACT:G09-CIE-U8-8.2/obj-1": "distractor",
               "ACT:quimica/concentracion-de-disoluciones/sondeo-1-G09": "distractor",
               "ACT:quimica/concentracion-de-disoluciones/sondeo-2-G09": "incorrecta"}},
    {"id": "R2", "archivo": "R2_procesos_termodinamicos.md", "estudiante": "EST-DEMO-2", "grado": 9,
     "objetivo": "TEMA:G09-CIE-U2-2.4",
     "titulo": "Procesos termodinámicos (Física, 9.°): la base llega después en la malla",
     "muestra": "Refuerzo PREVIO por la secuencia de la malla (no es un déficit del estudiante). Su comprobación "
                "falla, el diagnóstico baja a profundidad 2 (kelvin), se refuerza y se vuelve en orden: base → "
                "objetivo.",
     "guion": {"ACT:fisica/relaciones-presion-volumen-temperatura-gases/comprobacion-G09": "distractor",
               "ACT:fisica/temperatura-medicion-escalas/sondeo-1-G09": "distractor",
               "ACT:fisica/temperatura-medicion-escalas/sondeo-2-G09": "incorrecta"}},
    {"id": "R3", "archivo": "R3_constante_equilibrio.md", "estudiante": "EST-DEMO-3", "grado": 9,
     "objetivo": "TEMA:G09-CIE-U3-3.6",
     "titulo": "Constante de equilibrio (Química, 9.°): las bases están; la dificultad es del objetivo",
     "muestra": "Los sondeos DESCARTAN las dos bases (equilibrio dinámico y molaridad) y confirman la dificultad "
                "en el concepto del objetivo: se refuerza el objetivo, no sus prerrequisitos. Luego, "
                "«¿dónde ayudará?».",
     "guion": {"ACT:G09-CIE-U3-3.6/obj-1": "incorrecta",
               "ACT:quimica/constante-de-equilibrio/sondeo-1-G09": "distractor"}},
]


def errores_inversas(nav: Navegador) -> list[str]:
    """Cada arista se lee igual desde los dos extremos: A es_prerrequisito_de B ⇔ B requiere A; T trabaja C ⇔ C
    es_trabajado_en T. Devuelve las incoherencias (debe ser vacía)."""
    errores = []
    for a in nav.aristas:
        if a.tipo == TipoArista.PRERREQUISITO_DE:
            ida = a in nav.es_prerrequisito_de(a.origen, minima="baja")
            vuelta = a in nav.requiere(a.destino, minima="baja")
            if not (ida and vuelta):
                errores.append(f"PRERREQUISITO_DE {a.origen}→{a.destino}: ida {ida}, vuelta {vuelta}")
        elif a.tipo == TipoArista.TRABAJA and a.origen.startswith("TEMA:") and a.destino.startswith("CON:") \
                and a.rol == "principal" and a.origen not in {t.id for t in nav.temas_de_concepto(a.destino)}:
            errores.append(f"TRABAJA {a.origen}→{a.destino}: la inversa no lo encuentra")
    return errores


def correr(rec: dict, nav: Navegador, ped: Pedagogia, directorio: Path) -> tuple[Sesion, dict]:
    perfil = Perfil(rec["estudiante"], rec["grado"])
    sesion = Sesion(perfil, nav, ped, Guion(rec["guion"]), FECHA, cola=directorio / "propuestas.jsonl")
    resumen = sesion.ejecutar(rec["objetivo"])
    Almacen(directorio / "estudiantes").guardar(perfil)
    return sesion, resumen


def _tabla(encabezado: list[str], filas: list[list]) -> list[str]:
    limpiar = lambda x: str(x).replace("|", "/").replace("\n", " ")  # noqa: E731
    return ["| " + " | ".join(encabezado) + " |", "|" + "---|" * len(encabezado),
            *("| " + " | ".join(limpiar(x) for x in f) + " |" for f in filas)]


def _markdown(rec: dict, sesion: Sesion, resumen: dict, nav: Navegador) -> str:
    p, obj = sesion.perfil, nav.por_id[rec["objetivo"]]
    nombre = lambda c: nav.por_id[c].etiqueta if c in nav.por_id else c  # noqa: E731
    md = [f"# {rec['id']} · {rec['titulo']}", "",
          "> Recorrido generado por `uv run gskg tutor recorridos` (spec 13). Estudiante **simulado** con un guion de "
          "respuestas; actividades, dificultades y microtemas en estado **propuesta_pendiente** (redactados por un "
          "especialista IA, sin revisión del equipo de Ciencias). Muestra que el ciclo funciona sobre el grafo; no "
          "demuestra una mejora del aprendizaje.", "", f"**Qué muestra:** {rec['muestra']}", "",
          "## Objetivo curricular (malla V2, sin cambios)",
          f"- **{rec['objetivo'].removeprefix('TEMA:')}** ({obj.grado}.°, {obj.asignatura}): {obj.etiqueta}",
          f"- Indicador de logro: {obj.props.get('indicador')}",
          f"- Evidencia de aprendizaje: {obj.props.get('evidencia')}",
          f"- Fuentes: {'; '.join(sesion.contextos[0]['fuentes'])}", "",
          "## Bases: «¿qué necesita comprender?»", "",
          *_tabla(["Prof.", "Concepto", "Primer tema en la malla", "¿Antes del objetivo?", "Confianza", "Relación"],
                  [[b.profundidad, nombre(b.concepto), (b.primer_tema or "—").removeprefix("TEMA:"),
                    "sí" if b.antes_del_objetivo else "**no**", b.confianza, b.estado_relacion]
                   for b in nav.bases(rec["objetivo"])]), "",
          "## Recorrido paso a paso", "", *(f"{x.n}. **{x.fase}** · {x.texto}" for x in sesion.pasos), "",
          "## Hipótesis (se comprueban; no son conclusiones)", "",
          *_tabla(["Id", "Tipo", "Concepto", "Puntaje", "Estado", "Evidencias"],
                  [[h.id, h.tipo.replace("_", " "), nombre(h.concepto), h.puntaje, h.estado, ", ".join(h.evidencias)]
                   for h in p.hipotesis]), "",
          "## Refuerzos registrados", "",
          *_tabla(["Id", "Momento", "Objetivo", "Concepto", "Motivo", "Recurso (estado)", "Fuentes", "Min",
                   "Criterio de comprensión", "Condición para volver", "Prof.", "Resultado"],
                  [[i.id, i.momento, i.objetivo.removeprefix("TEMA:"), nombre(i.concepto), i.motivo,
                    f"{i.recurso} ({i.estado_recurso})", "; ".join(i.fuentes), i.duracion_min, i.criterio,
                    i.condicion_regreso, i.profundidad, i.resultado] for i in p.intervenciones]), "",
          "## Estado final del estudiante (solo su perfil; el grafo compartido no cambia)", "",
          *_tabla(["Concepto u objetivo", "P(dominio)", "Estado", "Previa", "Evidencias"],
                  [[nombre(e.id) if e.id in nav.por_id and e.id.startswith("CON:") else e.id.removeprefix("TEMA:"),
                    f"{e.p:.2f}", e.estado, e.previa, len(e.evidencias)]
                   for e in [*p.objetivos.values(), *sorted(p.conceptos.values(), key=lambda x: x.id)]]), "",
          f"Desvío de la sesión: {resumen['refuerzos']} refuerzos, {resumen['minutos_desvio']} min (límites: "
          f"{cargar('aprendizaje')['refuerzo']['max_por_sesion']} y "
          f"{cargar('aprendizaje')['refuerzo']['minutos_max_por_sesion']} min).", "",
          "## Repasos programados (posterior)", "",
          *([f"- {r.fecha} (+{r.intervalo} d)" for r in p.repasos] or ["—"]), ""]
    reforzados = sorted({i.concepto for i in p.intervenciones if i.momento != "posterior"})
    md += ["## «¿Dónde ayudará reforzar esto?» (recorrido inverso)", ""]
    for c in reforzados:
        filas = nav.apoya(c, grado=p.grado)[:8]
        md += [f"**{nombre(c)}** apoya, en {p.grado}.°–{p.grado + 2}.°:", "",
               *_tabla(["Distancia", "Grado", "Tema", "Por el concepto"],
                       [[f["distancia"], f["grado"], f"{f['tema'].removeprefix('TEMA:')} {f['tema_texto'][:70]}",
                         f["concepto_nombre"]] for f in filas]), ""]
    ref = sesion.contextos[0].get("referencia_internacional")
    md += ["## Contexto inyectado al tutor (primer paso, recortado)", "",
           "La referencia internacional entra como comparación para el docente, no como prerrequisito.", "",
           "```json", json.dumps({k: v for k, v in sesion.contextos[0].items() if k != "bases"}, ensure_ascii=False,
                                 indent=1)[:2500], "```", "",
           "## Evidencia, propuesta e hipótesis en este recorrido",
           "- **Evidencia verificada:** el objetivo, su fila de la malla V2 y los objetivos de marco que cubre.",
           "- **Inferencia de IA pendiente de revisión:** las relaciones de prerrequisito (ninguna revisada por una "
           "persona) y la clasificación del objetivo frente a los marcos.",
           "- **Propuesta pedagógica pendiente:** todas las actividades, dificultades y microtemas usados.",
           f"- **Referencia comparativa:** {ref or 'sin datos del consenso internacional para este concepto.'}",
           "- **Hipótesis de diseño:** los parámetros de config/aprendizaje.yaml (previas, desliz, umbrales, límites).",
           "", "## Notas para el docente y propuestas a revisión", "",
           *([f"- {n}" for n in resumen["notas_docente"]] or ["- —"]),
           *(f"- Propuesta: {x['tipo']} · {x['motivo']}" for x in resumen["propuestas"]), ""]
    return "\n".join(md)


def escribir_recorridos(destino: Path | None = None) -> list[str]:
    """Corre los tres recorridos y escribe un Markdown por recorrido y un JSON con los perfiles finales."""
    nav, ped = navegador_compartido(), Pedagogia.cargar()
    d = destino or ruta(cargar("aprendizaje")["rutas"]["recorridos"])
    d.mkdir(parents=True, exist_ok=True)
    escritos, perfiles = [], {}
    with tempfile.TemporaryDirectory() as tmp:
        for rec in RECORRIDOS:
            sesion, resumen = correr(rec, nav, ped, Path(tmp))
            (d / rec["archivo"]).write_text(_markdown(rec, sesion, resumen, nav), encoding="utf-8")
            escritos.append(relativa(d / rec["archivo"]))
            perfiles[rec["id"]] = {"resumen": resumen, "perfil": asdict(sesion.perfil)}
    (d / "recorridos.json").write_text(json.dumps(perfiles, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return [*escritos, relativa(d / "recorridos.json")]


def resumen_inversas() -> dict:
    """Conteo de aristas revisadas en los dos sentidos (para el informe)."""
    nav = navegador_compartido()
    pre = [a for a in nav.aristas if a.tipo == TipoArista.PRERREQUISITO_DE]
    return {"prerrequisitos": len(pre), "por_confianza": {c: sum(confianza(a) == c for a in pre)
                                                          for c in ("alta", "media", "baja")},
            "incoherencias": len(errores_inversas(nav))}
