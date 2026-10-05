"""Paso 3 (TIMSS 2027) · Traduce clasificacion_v1.json a 2027 y arma los lotes a reclasificar.

Uso:  python scripts/traducir_clasificacion_2027.py preparar   # traducción directa + lotes por grado
      python scripts/traducir_clasificacion_2027.py unir       # une traducción + salidas de subagentes
Reglas (acordadas con el equipo, ver data/referencia/cambios_timss_2023_2027.md):
- Traducción directa si obj1 Y obj2 tienen equivalencia «igual» o «fusionado» (destino 2027 único):
  conserva confianza y justificación, version «v2-2027-equivalencia».
- Se reclasifican con subagentes (prompts/clasificar_lote.md + catálogo 2027), un lote por grado:
  temas con obj1/obj2 «dividido» o «sin_equivalente», y TODOS los «FUERA» de v1.
  Tipos listados en TIPOS_RECLASIFICAR también se reclasifican completos (p. ej. si la muestra de control falla).
- Física 10.°–11.° (TA 2015) se conserva tal como está.
Salidas: data/interim/lotes_2027/lote_G{n}.json (entrada) y salida_G{n}.json (de los subagentes);
         data/referencia/clasificacion_v2_timss2027.json (lista, misma estructura que v1 + origen_2023).
"""
import csv, json, os, sys

V1 = 'data/referencia/clasificacion_v1.json'
CAT27 = 'data/referencia/catalogo_timss2027.json'
EQ = 'data/referencia/equivalencias_timss_2023_2027.csv'
TEMAS = 'data/interim/temas.json'
LOTES = 'data/interim/lotes_2027'
OUT = 'data/referencia/clasificacion_v2_timss2027.json'
DIRECTOS = ('igual', 'fusionado')
# Muestra de control (20 temas, semilla 2027, data/interim/lotes_2027/muestra_control.json): 3 mal > 2
# → se reclasifican también «igual» y «fusionado». La traducción directa se guarda como referencia.
TIPOS_RECLASIFICAR = ('igual', 'fusionado')
CAMPOS_TEMA = ('archivo', 'hoja', 'fila', 'grado', 'unidad', 'contenido', 'subcontenido',
               'procedimental', 'indicador', 'evidencia')


def cargar():
    v1 = json.load(open(V1))
    eq = {}
    for r in csv.DictReader(open(EQ)):
        if r['codigo_2023']:
            eq.setdefault(r['codigo_2023'], {'tipo': r['tipo'], 'destinos': []})
            if r['codigo_2027']:
                eq[r['codigo_2023']]['destinos'].append(r['codigo_2027'])
    temas = {(t['archivo'], t['hoja'], t['fila']): t for t in json.load(open(TEMAS))}
    return v1, eq, temas


def traduccion_directa(r, eq):
    """Destino 2027 principal de obj1/obj2 según las equivalencias ('' si no hay)."""
    d = [eq[o]['destinos'][0] if o and o != 'FUERA' and eq[o]['destinos'] else '' for o in (r['obj1'], r.get('obj2') or '')]
    return d[0], ('' if d[1] == d[0] else d[1])


def decidir(r, eq, tema):
    """→ ('ta', None) | ('directo', (obj1, obj2)) | ('reclasificar', motivo)"""
    o1, o2 = r['obj1'], r.get('obj2') or ''
    if tema['asignatura'] == 'Física':  # Física 10.°–11.°: TIMSS Advanced 2015, incluidos sus FUERA
        return 'ta', None
    if o1 == 'FUERA':
        return 'reclasificar', 'FUERA en v1'
    tipos = [eq[o]['tipo'] for o in (o1, o2) if o]
    malos = [f'{o}:{eq[o]["tipo"]}' for o in (o1, o2) if o and
             (eq[o]['tipo'] not in DIRECTOS or eq[o]['tipo'] in TIPOS_RECLASIFICAR)]
    if malos:
        return 'reclasificar', 'equivalencia ' + ', '.join(malos)
    n1, n2 = eq[o1]['destinos'][0], (eq[o2]['destinos'][0] if o2 else '')
    if n1 == n2:  # dos objetivos 2023 fusionados en el mismo 2027
        n2 = ''
    return 'directo', (n1, n2)


def preparar():
    v1, eq, temas = cargar()
    cat = json.load(open(CAT27))
    os.makedirs(LOTES, exist_ok=True)
    lotes, n = {}, {'ta': 0, 'directo': 0, 'reclasificar': 0}
    for r in v1:
        t = temas[(r['archivo'], r['hoja'], r['fila'])]
        accion, info = decidir(r, eq, t)
        n[accion] += 1
        if accion != 'reclasificar':
            continue
        pistas = sorted({d for o in (r['obj1'], r.get('obj2') or '') if o and o != 'FUERA' for d in eq[o]['destinos']})
        lotes.setdefault(t['grado'], []).append({
            **{k: t.get(k, '') for k in CAMPOS_TEMA},
            'v1': {'obj1': r['obj1'], 'obj2': r.get('obj2') or '', 'justificacion': r['justificacion']},
            'motivo': info, 'candidatos_2027': pistas,
            'traduccion_directa': dict(zip(('obj1', 'obj2'), traduccion_directa(r, eq)))})
    for g, ts in sorted(lotes.items()):
        marco = 'T4_27' if g <= 4 else 'T8_27'
        catalogo = [{k: c[k] for k in ('codigo', 'dominio', 'area', 'objetivo', 'es_investigacion')} |
                    {'subitems': [s['texto'] for s in c['subitems']]} for c in cat if c['marco'] == marco]
        json.dump({'grado': g, 'marco': marco, 'catalogo': catalogo, 'temas': ts},
                  open(f'{LOTES}/lote_G{g}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'lote_G{g}.json: {len(ts)} temas ({marco}) · FUERA v1: {sum(t["v1"]["obj1"] == "FUERA" for t in ts)}')
    print(f'Física TA conservada: {n["ta"]} · traducción directa: {n["directo"]} · a reclasificar: {n["reclasificar"]}')


def unir():
    v1, eq, temas = cargar()
    cat = {c['codigo']: c for c in json.load(open(CAT27))}
    salidas = {}
    for f in sorted(os.listdir(LOTES)):
        if f.startswith('salida_G'):
            for s in json.load(open(f'{LOTES}/{f}')):
                salidas[(s['archivo'], s['hoja'], s['fila'])] = s
    out, faltan, errores = [], [], []
    for r in v1:
        k = (r['archivo'], r['hoja'], r['fila'])
        accion, info = decidir(r, eq, temas[k])
        origen = {'obj1': r['obj1'], 'obj2': r.get('obj2') or ''}
        if accion == 'ta':
            out.append(dict(r))
            continue
        if accion == 'directo':
            assert info
            n1, n2 = info
            just = r['justificacion']
            out.append({**r, 'obj1': n1, 'obj2': n2, 'justificacion': just,
                        'version': 'v2-2027-equivalencia', 'origen_2023': origen})
            continue
        s = salidas.get(k)
        if not s:
            faltan.append(k)
            continue
        if s['procedimental'] != r['procedimental']:
            errores.append(f'{k}: procedimental distinto')
        grado = temas[k]['grado']
        pref = 'T4_27' if grado <= 4 else 'T8_27'
        for campo in ('obj1', 'obj2'):
            v = s.get(campo) or ''
            if v and v != 'FUERA' and (v not in cat or not v.startswith(pref)):
                errores.append(f'{k}: {campo}={v} inválido para {grado}.°')
        if (s.get('obj2') or '') == 'FUERA' or (s['obj1'] == s.get('obj2')):
            errores.append(f'{k}: obj2 inválido')
        if s['confianza'] not in ('alta', 'media', 'baja'):
            errores.append(f'{k}: confianza {s["confianza"]}')
        if len(s['justificacion'].split()) > 15:
            errores.append(f'{k}: justificación de más de 15 palabras')
        out.append({**{c: r[c] for c in ('archivo', 'hoja', 'fila', 'procedimental')},
                    'obj1': s['obj1'], 'obj2': s.get('obj2') or '', 'confianza': s['confianza'],
                    'justificacion': s['justificacion'], 'version': 'v2-2027-reclasificado',
                    'revisado_por': '', 'origen_2023': origen, 'motivo_reclasificacion': info,
                    'traduccion_directa': dict(zip(('obj1', 'obj2'), traduccion_directa(r, eq)))})
    if faltan or errores:
        print(f'FALTAN {len(faltan)} temas en las salidas; ERRORES {len(errores)}')
        for e in (errores + [str(f) for f in faltan])[:40]:
            print(' ', e)
        sys.exit(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Escrito {OUT}: {len(out)} temas')


if __name__ == '__main__':
    {'preparar': preparar, 'unir': unir}[sys.argv[1]]()
