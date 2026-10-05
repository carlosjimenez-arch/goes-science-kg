"""Paso 2 · Une la clasificación vigente del marco elegido con los temas extraídos.

Uso:  python scripts/merge_clasificacion.py                 # = --marco 2023
      python scripts/merge_clasificacion.py --marco 2027
- 2023: data/referencia/clasificacion_v1.json (+ data/interim/clasificacion_nuevos.json)
        → data/interim/clasificacion.json y pendientes.json
- 2027: data/referencia/clasificacion_v2_timss2027.json (+ data/interim/clasificacion_nuevos_2027.json)
        → data/interim/clasificacion_2027.json y pendientes_2027.json

El cruce es por (archivo, hoja, fila) y se verifica que el texto del procedimental no haya cambiado.
- Coincide → se reutiliza la clasificación.
- No coincide o es nuevo → va a data/interim/pendientes.json para clasificarlo (ver prompts/clasificar_lote.md).
Salida: dict id_tema → {obj1, obj2, confianza, justificacion}.
Química y Biología de Bachillerato no se clasifican (no tienen marco TIMSS de contenido).
"""
import argparse, json, os

MARCOS = {
    '2023': ('data/referencia/clasificacion_v1.json', 'data/interim/clasificacion_nuevos.json',
             'data/interim/clasificacion.json', 'data/interim/pendientes.json'),
    '2027': ('data/referencia/clasificacion_v2_timss2027.json', 'data/interim/clasificacion_nuevos_2027.json',
             'data/interim/clasificacion_2027.json', 'data/interim/pendientes_2027.json'),
}
ap = argparse.ArgumentParser()
ap.add_argument('--marco', choices=sorted(MARCOS), default='2023')
REF, NUEVOS, OUT, PEND = MARCOS[ap.parse_args().marco]

temas = json.load(open('data/interim/temas.json'))
ref = json.load(open(REF))
extra = []
if os.path.exists(NUEVOS):
    extra = json.load(open(NUEVOS))  # misma estructura que la clasificación de referencia
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
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
json.dump(pend, open(PEND, 'w'), ensure_ascii=False, indent=1)
print(f'reutilizados: {len(out)} · pendientes de clasificar: {len(pend)}')
