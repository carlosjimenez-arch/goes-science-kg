"""Mapa de progresión por asignatura (asignaturas/<x>/progresion.html).

Filas: conceptos de la asignatura, ordenados por su nivel en el DAG de prerrequisitos (los de base arriba) y,
dentro del nivel, por el primer grado en El Salvador. Columnas: grados 2.°–11.°. Cada fila marca el primer grado
en El Salvador (■) y en cada país de referencia (letras), y colorea la distancia a la mediana de los países.
Es una página estática y autocontenida (sin librerías externas), con modo claro y oscuro.
"""

from __future__ import annotations

import html
import json

import networkx as nx

from goes_science_kg.config import cargar, ruta
from goes_science_kg.modelos import Arista, Nodo, TipoArista, TipoNodo
from goes_science_kg.prerrequisitos import evidencia_orden, paises_alto_desempeno

GRADOS = list(range(2, 12))


def _niveles(asig: str, nodos: list[Nodo], aristas: list[Arista]) -> dict[str, int]:
    ids = {n.id for n in nodos if n.tipo == TipoNodo.CONCEPTO and n.asignatura == asig}
    g = nx.DiGraph()
    g.add_nodes_from(ids)
    g.add_edges_from((a.origen, a.destino) for a in aristas
                     if a.tipo == TipoArista.PRERREQUISITO_DE and a.origen in ids and a.destino in ids)
    nivel = {}
    for n in nx.topological_sort(g):
        nivel[n] = max((nivel[p] + 1 for p in g.predecessors(n)), default=0)
    return nivel


def escribir(asig: str, nodos: list[Nodo], aristas: list[Arista], ev: dict) -> str:
    por_id = {n.id: n for n in nodos}
    nivel = _niveles(asig, nodos, aristas)
    alto = paises_alto_desempeno()
    filas = []
    for cid in sorted(nivel, key=lambda c: (nivel[c], ev[c]["sv"] or 99, por_id[c].etiqueta)):
        e = ev[cid]
        filas.append({"c": por_id[cid].etiqueta, "d": por_id[cid].props.get("definicion") or "", "n": nivel[cid],
                      "sv": e["sv"], "p": {k: v for k, v in e["paises"].items()}, "m": e["paises_mediana"]})
    nombre = cargar("asignaturas")["asignaturas"][asig]["nombre"]
    datos = json.dumps({"filas": filas, "grados": GRADOS, "alto": sorted(alto)}, ensure_ascii=False)
    pagina = PLANTILLA.replace("__TITULO__", html.escape(f"Progresión de conceptos · {nombre}")) \
                      .replace("__DATOS__", datos.replace("</", "<\\/"))
    p = ruta(cargar("asignaturas")["asignaturas"][asig]["carpeta"]) / "progresion.html"
    p.write_text(pagina, encoding="utf-8")
    return str(p.relative_to(ruta(".")))


def escribir_todas(nodos: list[Nodo], aristas: list[Arista]) -> list[str]:
    ev = evidencia_orden(nodos, aristas)
    return [escribir(a, nodos, aristas, ev) for a in cargar("asignaturas")["asignaturas"]]


PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITULO__</title>
<style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--borde:#e3e3dc;--sv:#1E4D3A;--tarde:#c0392b;--antes:#2e7d32;--celda:#f1f1ea}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ececea;--muted:#a3a39c;--borde:#33332f;--sv:#7fbf9f;--tarde:#ef7d6e;--antes:#8fd19e;--celda:#22221f}}
body{margin:0;padding:20px 16px;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--fg)}
h1{font-size:20px;margin:0 0 6px}p{color:var(--muted);font-size:13px;line-height:1.5;max-width:900px}
.controles{display:flex;gap:12px;flex-wrap:wrap;font-size:13px;margin:10px 0}
input[type=search]{padding:4px 8px;border:1px solid var(--borde);border-radius:6px;background:var(--bg);color:var(--fg)}
.tabla{overflow-x:auto}table{border-collapse:collapse;font-size:12px;min-width:760px}
th,td{border-bottom:1px solid var(--borde);padding:4px 6px;text-align:center}th{position:sticky;top:0;background:var(--bg)}
td.c{text-align:left;max-width:320px}td.g{width:34px;background:var(--celda)}
.sv{display:inline-block;width:12px;height:12px;background:var(--sv);border-radius:2px}
.p{font-size:10px;color:var(--muted)}.tarde{color:var(--tarde);font-weight:bold}.antes{color:var(--antes);font-weight:bold}
</style></head><body>
<h1>__TITULO__</h1>
<p>Cada fila es un concepto, ordenado desde los de base (nivel 0 del grafo de prerrequisitos) hasta los que dependen de
más ideas previas. <span class="sv"></span> marca el primer grado en El Salvador; las letras, el primer grado (equivalente
por edad) en cada país de referencia. «Desfase» es el grado de El Salvador menos la mediana de los países: en
<span class="tarde">rojo</span> si El Salvador llega 2 o más grados tarde, en <span class="antes">verde</span> si llega 2 o más
grados antes. Pasa el cursor sobre el concepto para ver su definición.</p>
<div class="controles"><input type="search" id="q" placeholder="Buscar concepto…">
<label><input type="checkbox" id="solo"> Solo los que llegan tarde</label></div>
<div class="tabla"><table><thead><tr><th>Nivel</th><th>Concepto</th><th>Desfase</th><th>Países</th></tr></thead>
<tbody id="cuerpo"></tbody></table></div>
<script>
const D = __DATOS__;
const esc = s => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
document.querySelector('thead tr').insertAdjacentHTML('beforeend', D.grados.map(g => `<th>${g}.°</th>`).join(''));
function pintar(){
  const q = document.getElementById('q').value.toLowerCase(), solo = document.getElementById('solo').checked;
  document.getElementById('cuerpo').innerHTML = D.filas.filter(f => {
    const des = (f.sv != null && f.m != null) ? f.sv - f.m : null;
    return (!q || f.c.toLowerCase().includes(q)) && (!solo || (des != null && des >= 2));
  }).map(f => {
    const des = (f.sv != null && f.m != null) ? f.sv - f.m : null;
    const cls = des == null ? '' : des >= 2 ? 'tarde' : des <= -2 ? 'antes' : '';
    const celdas = D.grados.map(g => {
      const ps = Object.entries(f.p).filter(([k, v]) => Math.round(v) === g).map(([k]) => k);
      return `<td class="g">${f.sv === g ? '<span class="sv" title="El Salvador"></span>' : ''}${ps.length ? `<div class="p">${esc(ps.join(' '))}</div>` : ''}</td>`;
    }).join('');
    return `<tr><td>${f.n}</td><td class="c" title="${esc(f.d)}">${esc(f.c)}</td><td class="${cls}">${des == null ? '—' : (des > 0 ? '+' : '') + des.toFixed(1)}</td><td class="p">${Object.keys(f.p).length}</td>${celdas}</tr>`;
  }).join('');
}
document.querySelectorAll('input').forEach(e => e.addEventListener('input', pintar)); pintar();
</script></body></html>
"""
