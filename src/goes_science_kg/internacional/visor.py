"""Visor del contraste internacional de 9.°–11.° (internacional/visor.html, spec 11).

Una pestaña por asignatura. Cada fila es un concepto con su clase, los grados de la V2 y, por país, el grado SV de
primera aparición (resaltado si es núcleo; «e» si solo está en especialización). Al hacer clic se ve la evidencia:
temas de la V2 (archivo, hoja y fila) y objetivos de los países (documento y página). Página estática y
autocontenida (sin librerías externas), con modo claro y oscuro, como `progresion.html`.
"""

from __future__ import annotations

import html
import json
from typing import TYPE_CHECKING

from goes_science_kg.config import relativa
from goes_science_kg.internacional.consenso import objetivos, paises

if TYPE_CHECKING:
    from pathlib import Path

POR_PAIS = 2   # objetivos citados por país en el detalle


def escribir(r: dict, clases: list[tuple[str, str, str]], nombres: dict[str, str], destino: Path) -> str:
    """Escribe `destino`/visor.html con las filas del contraste `r`, una pestaña por asignatura de `nombres`.
    Devuelve la ruta relativa."""
    objs = {o["id"]: o for o in objetivos()}
    ps = paises()
    filas = []
    for f in r["filas"]:
        celdas, evidencia = {}, []
        for p in ps:
            d = f["paises"].get(p)
            if not d:
                continue
            celdas[p] = [d["primer_grado_nucleo"], d["en_especializacion"], d["nucleo_9_11"]]
            evidencia.extend([p, o["curso"], o["nivel"], o["documento"], o.get("pagina") or "", o["texto"]]
                             for i in d["objetivos"][:POR_PAIS] if (o := objs.get(i)))
        temas = []
        for t in f["sv_temas"][:6]:
            x = r["temas"][t]
            temas.append([t, x["archivo"].split("/")[-1], x["hoja"], x["fila"], x["grado"],
                          f"{x['contenido']}. {x['indicador']}"[:260]])
        filas.append({"a": f["asignatura"], "c": f["nombre"], "k": f["clase"], "sv": f["sv_primer_grado"],
                      "s9": f.get("sv_9_11"), "n9": f["n_nucleo_9_11"], "ne": f["n_especializacion"],
                      "p": celdas, "t": temas, "e": evidencia})
    datos = {"filas": filas, "paises": ps, "clases": [[k, t, d] for k, t, d in clases],
             "asignaturas": [[k, v] for k, v in nombres.items()]}
    pagina = PLANTILLA.replace("__DATOS__", json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")) \
                      .replace("__TITULO__", html.escape("Contraste internacional 9.°–11.°"))
    p = destino / "visor.html"
    p.write_text(pagina, encoding="utf-8")
    return relativa(p)


PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITULO__</title>
<style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--borde:#e3e3dc;--sv:#1E4D3A;--celda:#f1f1ea;--nuc:#d7e8dd;
--falta:#c0392b;--esp:#b9770e;--ok:#2e7d32;--neutro:#6b6b66}
@media (prefers-color-scheme: dark){:root{--bg:#161614;--fg:#ececea;--muted:#a3a39c;--borde:#33332f;--sv:#7fbf9f;
--celda:#22221f;--nuc:#2a3d32;--falta:#ef7d6e;--esp:#f0b75e;--ok:#8fd19e;--neutro:#a3a39c}}
body{margin:0;padding:20px 16px;font-family:Arial,Helvetica,sans-serif;background:var(--bg);color:var(--fg)}
h1{font-size:20px;margin:0 0 6px}p{color:var(--muted);font-size:13px;line-height:1.5;max-width:960px}
.pestanas{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
.pestanas button,.chips button{border:1px solid var(--borde);background:var(--bg);color:var(--fg);border-radius:6px;
padding:5px 10px;font-size:13px;cursor:pointer}
.pestanas button.on{background:var(--sv);color:var(--bg);border-color:var(--sv)}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 10px}.chips button.on{outline:2px solid var(--sv)}
input[type=search]{padding:5px 8px;border:1px solid var(--borde);border-radius:6px;background:var(--bg);color:var(--fg);
min-width:220px}
.tabla{overflow-x:auto}table{border-collapse:collapse;font-size:12px;min-width:820px;width:100%}
th,td{border-bottom:1px solid var(--borde);padding:5px 6px;text-align:center;vertical-align:top}
th{position:sticky;top:0;background:var(--bg)}td.c{text-align:left;max-width:300px;cursor:pointer}
td.g{width:38px;background:var(--celda)}td.g.n{background:var(--nuc);font-weight:bold}
.k{font-size:11px;padding:2px 6px;border-radius:10px;border:1px solid currentColor;white-space:nowrap}
.k.faltante,.k.no_retomado,.k.tardio{color:var(--falta)}.k.solo_especializacion,.k.adelantado{color:var(--esp)}
.k.alineado,.k.retomado{color:var(--ok)}.k.previo,.k.sin_referente,.k.no_aplica{color:var(--neutro)}
tr.det td{text-align:left;background:var(--celda);font-size:12px;line-height:1.45}
tr.det b{color:var(--sv)}.leyenda{font-size:12px;color:var(--muted)}
</style></head><body>
<h1>__TITULO__</h1>
<p>Malla V2 de El Salvador frente al núcleo común (lo que cursa la mayoría) de 9 países: SG, JP, KR, ENG, AU, HK, TW,
EE y ON. En cada país, la celda muestra el grado SV equivalente en que aparece el concepto por primera vez; en
<b>negrita y fondo verde</b> si está en su núcleo de 9.°–11.° y con «e» si solo está en cursos electivos. Haz clic en
un concepto para ver la evidencia. Método, hallazgos verificados y límites: <code>internacional/README.md</code>.</p>
<div class="pestanas" id="asigs"></div>
<input type="search" id="q" placeholder="Buscar concepto…">
<div class="chips" id="chips"></div>
<div class="leyenda" id="desc"></div>
<div class="tabla"><table><thead><tr id="cab"><th>Concepto</th><th>Clase</th><th>Grados V2</th>
<th>Núcleo 9.°–11.°</th><th>Electivas</th></tr></thead><tbody id="cuerpo"></tbody></table></div>
<script>
const D = __DATOS__;
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const titulo = Object.fromEntries(D.clases.map(([k, t]) => [k, t]));
const desc = Object.fromEntries(D.clases.map(([k, t, d]) => [k, d]));
let asig = D.asignaturas[0][0], clase = null, abierto = null;
document.getElementById('cab').insertAdjacentHTML('beforeend', D.paises.map(p => `<th>${p}</th>`).join(''));
document.getElementById('asigs').innerHTML = D.asignaturas.map(([k, n]) =>
  `<button data-a="${k}">${esc(n)}</button>`).join('');
function grados(f){
  const gs = [...new Set(f.t.map(t => t[4]))].sort((a, b) => a - b);
  return gs.length ? gs.map(g => g + '.°').join(', ') : 'no está';
}
function detalle(f){
  const t = f.t.map(x => `<div><b>SV ${esc(x[0])}</b> (${esc(x[1])}, hoja «${esc(x[2])}», fila ${esc(x[3])}): ${esc(x[5])}</div>`).join('');
  const e = f.e.map(x => `<div><b>${esc(x[0])}</b> · ${esc(x[1])} [${x[2] === 'nucleo' ? 'núcleo' : 'electiva'}] (${esc(x[3])}${x[4] ? ', p. ' + esc(x[4]) : ''}): «${esc(x[5])}»</div>`).join('');
  return `<tr class="det"><td colspan="${5 + D.paises.length}">${desc[f.k] ? `<div><i>${esc(desc[f.k])}</i></div>` : ''}${t || '<div>La V2 no lo tiene en 2.°–11.°.</div>'}${e}</td></tr>`;
}
function pintar(){
  document.querySelectorAll('#asigs button').forEach(b => b.classList.toggle('on', b.dataset.a === asig));
  const deAsig = D.filas.filter(f => f.a === asig);
  const cuenta = {}; deAsig.forEach(f => cuenta[f.k] = (cuenta[f.k] || 0) + 1);
  document.getElementById('chips').innerHTML = D.clases.filter(([k]) => cuenta[k]).map(([k, t]) =>
    `<button data-k="${k}" class="${clase === k ? 'on' : ''}"><span class="k ${k}">${esc(t)}</span> ${cuenta[k]}</button>`).join('');
  document.querySelectorAll('#chips button').forEach(b => b.onclick = () => { clase = clase === b.dataset.k ? null : b.dataset.k; pintar(); });
  document.getElementById('desc').textContent = clase ? desc[clase] : '';
  const q = document.getElementById('q').value.toLowerCase();
  const orden = Object.fromEntries(D.clases.map(([k], i) => [k, i]));
  const filas = deAsig.filter(f => (!clase || f.k === clase) && (!q || f.c.toLowerCase().includes(q)))
    .sort((a, b) => (orden[a.k] ?? 99) - (orden[b.k] ?? 99) || b.n9 - a.n9 || a.c.localeCompare(b.c));
  document.getElementById('cuerpo').innerHTML = filas.map((f, i) => {
    const celdas = D.paises.map(p => {
      const x = f.p[p]; if (!x) return '<td class="g"></td>';
      const [g, esp, n9] = x;
      return `<td class="g${n9 ? ' n' : ''}">${g != null ? (+g).toFixed(g % 1 ? 1 : 0) : (esp ? 'e' : '')}</td>`;
    }).join('');
    const fila = `<tr><td class="c" data-i="${i}">${esc(f.c)}</td><td><span class="k ${f.k}">${esc(titulo[f.k] || f.k)}</span></td><td>${grados(f)}</td><td>${f.n9}</td><td>${f.ne}</td>${celdas}</tr>`;
    return fila + (abierto === f.c ? detalle(f) : '');
  }).join('');
  document.querySelectorAll('td.c').forEach(td => td.onclick = () => {
    const f = filas[+td.dataset.i]; abierto = abierto === f.c ? null : f.c; pintar();
  });
}
document.querySelectorAll('#asigs button').forEach(b => b.onclick = () => { asig = b.dataset.a; clase = null; abierto = null; pintar(); });
document.getElementById('q').addEventListener('input', pintar);
pintar();
</script></body></html>
"""
