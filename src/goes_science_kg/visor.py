"""Visor HTML interactivo del grafo de cada grado (grados/G<gg>/grafo.html).

Un archivo autocontenido: los datos del subgrafo van incrustados como JSON y la librería vis-network
se carga desde unpkg. Muestra temas (por asignatura), conceptos, prácticas y prerrequisitos; resalta
en rojo los prerrequisitos que llegan tarde o nunca. Al hacer clic en un nodo se ve su detalle y su fuente.
"""

from __future__ import annotations

import html
import json

from goes_science_kg.config import relativa, ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo

COLOR_ASIG = {"biologia": "#2E7D32", "fisica": "#1565C0", "quimica": "#8E24AA", "ciencias_tierra_espacio": "#EF6C00"}
TIPOS_ARISTA = {TipoArista.TRABAJA, TipoArista.PRERREQUISITO_DE}


def _datos(g: int, nodos: list[Nodo], aristas: list[Arista], diagnostico: dict) -> dict:
    tarde = {(a["prerrequisito"], a["concepto"]) for a in diagnostico.get("anclajes", [])
             if a["estado"] in ("ausente", "posterior")}
    estado_ancla = {a["prerrequisito"]: a["estado"] for a in diagnostico.get("anclajes", [])}
    incluidos = {n.id for n in nodos if n.tipo in (TipoNodo.TEMA, TipoNodo.CONCEPTO, TipoNodo.PRACTICA)}
    temas = {n.id for n in nodos if n.tipo == TipoNodo.TEMA}
    del_grado = {a.destino for a in aristas if a.tipo == TipoArista.TRABAJA and a.origen in temas}
    vis_n = []
    for n in nodos:
        if n.id not in incluidos:
            continue
        f = n.fuente
        fuente = "" if not f else " ".join(str(x) for x in (f.documento, f.pagina and f"p.{f.pagina}",
                                                            f.hoja and f"hoja «{f.hoja}»", f.fila and f"fila {f.fila}") if x)
        ancla = n.tipo == TipoNodo.CONCEPTO and n.id not in del_grado
        vis_n.append({
            "id": n.id, "label": (n.etiqueta[:40] + "…") if len(n.etiqueta) > 40 else n.etiqueta,
            "tipo": n.tipo.value, "asignatura": n.asignatura or "", "titulo": n.etiqueta,
            "detalle": n.props.get("definicion") or n.props.get("unidad") or "", "fuente": fuente,
            "estado": estado_ancla.get(n.id, ""),
            "shape": {"Tema": "dot", "Concepto": "box", "Practica": "diamond"}[n.tipo.value],
            "color": COLOR_ASIG.get(n.asignatura or "", "#607D8B") if not ancla else "#9E9E9E",
            "size": 8 if n.tipo == TipoNodo.TEMA else 14,
        })
    vis_a = [{"from": a.origen, "to": a.destino, "tipo": a.tipo.value,
              "color": "#C62828" if (a.origen, a.destino) in tarde else
              ("#424242" if a.tipo == TipoArista.PRERREQUISITO_DE else "#B0BEC5"),
              "dashes": a.tipo == TipoArista.TRABAJA and a.rol != "principal",
              "arrows": "to" if a.tipo == TipoArista.PRERREQUISITO_DE else "",
              "width": 3 if (a.origen, a.destino) in tarde else 1}
             for a in aristas if a.tipo in TIPOS_ARISTA and a.origen in incluidos and a.destino in incluidos]
    return {"grado": g, "nodos": vis_n, "aristas": vis_a}


PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grafo de Ciencias · __GRADO__.° grado</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--panel:#fff;--borde:#e3e3dc}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ececea;--muted:#a3a39c;--panel:#1f1f1c;--borde:#33332f}}
body{margin:0;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:12px 16px;border-bottom:1px solid var(--borde)}h1{font-size:18px;margin:0 0 6px}
.controles{display:flex;flex-wrap:wrap;gap:10px;font-size:13px;align-items:center}
.controles input[type=search]{padding:4px 8px;border:1px solid var(--borde);border-radius:6px;background:var(--panel);color:var(--fg)}
main{display:flex;height:calc(100vh - 92px)}#red{flex:1}
aside{width:320px;max-width:40vw;padding:12px 16px;border-left:1px solid var(--borde);overflow:auto;font-size:13px;background:var(--panel)}
.leyenda span{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:4px;vertical-align:middle}
.muted{color:var(--muted)}@media (max-width:700px){main{flex-direction:column}aside{width:auto;max-width:none;border-left:0;border-top:1px solid var(--borde)}}
</style></head><body>
<header><h1>Grafo de Ciencias · __GRADO__.° grado (El Salvador)</h1>
<div class="controles">
<input type="search" id="buscar" placeholder="Buscar concepto o tema…">
<label><input type="checkbox" class="asig" value="biologia" checked> Biología</label>
<label><input type="checkbox" class="asig" value="fisica" checked> Física</label>
<label><input type="checkbox" class="asig" value="quimica" checked> Química</label>
<label><input type="checkbox" class="asig" value="ciencias_tierra_espacio" checked> Tierra y Espacio</label>
<label><input type="checkbox" id="temas"> Mostrar temas</label>
<span class="leyenda muted">● tema ■ concepto ◆ práctica · <span style="background:#C62828"></span>prerrequisito que llega tarde · <span style="background:#9E9E9E"></span>prerrequisito de otro grado</span>
</div></header>
<main><div id="red"></div><aside id="detalle"><p class="muted">Haz clic en un nodo para ver su detalle y su fuente.</p></aside></main>
<script>
const DATOS = __DATOS__;
// vis-network dibuja en canvas: los colores de texto se fijan aquí (no toma las variables CSS).
const oscuro = window.matchMedia('(prefers-color-scheme: dark)').matches;
const tinta = oscuro ? '#ececea' : '#1d1d1b';
DATOS.nodos.forEach(n => {
  n.font = n.shape === 'box' ? {color: '#ffffff', size: 13, face: 'Arial'} : {color: tinta, size: 11, face: 'Arial'};
  if (n.shape === 'box') n.margin = 6;
  n.hidden = n.tipo === 'Tema';  // vista inicial: mapa de conceptos y prácticas
});
const nodos = new vis.DataSet(DATOS.nodos), aristas = new vis.DataSet(DATOS.aristas);
const red = new vis.Network(document.getElementById('red'), {nodes: nodos, edges: aristas}, {
  physics: {solver: 'forceAtlas2Based', forceAtlas2Based: {gravitationalConstant: -90, springLength: 140},
            stabilization: {iterations: 400}},
  layout: {improvedLayout: false},
  nodes: {scaling: {label: {drawThreshold: 3}}}, interaction: {hover: true, tooltipDelay: 150}});
red.once('stabilizationIterationsDone', () => { red.setOptions({physics: false}); red.fit(); });
function filtrar(){
  const asigs = new Set([...document.querySelectorAll('.asig:checked')].map(e => e.value));
  const temas = document.getElementById('temas').checked, q = document.getElementById('buscar').value.toLowerCase();
  nodos.update(DATOS.nodos.map(n => ({id: n.id, hidden: (n.asignatura && !asigs.has(n.asignatura)) ||
    (!temas && n.tipo === 'Tema') || (q && !n.titulo.toLowerCase().includes(q) && n.tipo !== 'Practica' && q.length > 2)})));
}
document.querySelectorAll('input').forEach(e => e.addEventListener('input', filtrar));
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
red.on('click', p => {
  if (!p.nodes.length) return; const n = nodos.get(p.nodes[0]);
  const vec = red.getConnectedNodes(n.id).map(i => nodos.get(i)).filter(Boolean);
  document.getElementById('detalle').innerHTML = `<h3>${esc(n.titulo)}</h3><p class="muted">${esc(n.tipo)} · ${esc(n.asignatura || 'transversal')}${n.estado ? ' · prerrequisito ' + esc(n.estado) : ''}</p>
    <p>${esc(n.detalle)}</p>${n.fuente ? `<p class="muted">Fuente: ${esc(n.fuente)}</p>` : ''}
    <p><b>Conectado con (${vec.length})</b></p><ul>${vec.slice(0, 40).map(v => `<li>${esc(v.titulo)}</li>`).join('')}</ul>
    <p class="muted">${esc(n.id)}</p>`;
});
</script></body></html>
"""


def escribir_visor(g: int, nodos: list[Nodo], aristas: list[Arista], diagnostico: dict) -> str:
    datos = json.dumps(_datos(g, nodos, aristas, diagnostico), ensure_ascii=False).replace("</", "<\\/")
    p = ruta(f"grados/G{g:02d}") / "grafo.html"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(PLANTILLA.replace("__GRADO__", html.escape(str(g))).replace("__DATOS__", datos), encoding="utf-8")
    return relativa(p)
