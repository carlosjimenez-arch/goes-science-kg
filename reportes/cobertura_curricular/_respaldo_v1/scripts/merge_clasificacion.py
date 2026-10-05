"""Paso 2 · Une la clasificación vigente (data/referencia/clasificacion_v1.json) con los temas extraídos.

El cruce es por (archivo, hoja, fila) y se verifica que el texto del procedimental no haya cambiado.
- Coincide → se reutiliza la clasificación.
- No coincide o es nuevo → va a data/interim/pendientes.json para clasificarlo (ver prompts/clasificar_lote.md).
Salida: data/interim/clasificacion.json (dict id_tema → {obj1, obj2, confianza, justificacion}).
Química y Biología de Bachillerato no se clasifican (no tienen marco TIMSS de contenido).
"""
import json, os

temas = json.load(open('data/interim/temas.json'))
ref = json.load(open('data/referencia/clasificacion_v1.json'))
extra = []
if os.path.exists('data/interim/clasificacion_nuevos.json'):
    extra = json.load(open('data/interim/clasificacion_nuevos.json'))  # misma estructura que clasificacion_v1
idx = {(r['archivo'], r['hoja'], r['fila']): r for r in ref + extra}

out, pend = {}, []
for t in temas:
    if t['asignatura'] in ('Química', 'Biología'):
        continue
    r = idx.get((t['archivo'], t['hoja'], t['fila']))
    if r and r['procedimental'] == t['procedimental']:
        out[t['id']] = {k: r[k] for k in ('obj1', 'obj2', 'confianza', 'justificacion')}
    else:
        pend.append(t)
json.dump(out, open('data/interim/clasificacion.json', 'w'), ensure_ascii=False, indent=0)
json.dump(pend, open('data/interim/pendientes.json', 'w'), ensure_ascii=False, indent=1)
print(f'reutilizados: {len(out)} · pendientes de clasificar: {len(pend)}')
