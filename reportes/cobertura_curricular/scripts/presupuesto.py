"""Presupuesto de temas: candidatos de INSERCIÓN, FUSIÓN y REUBICACIÓN por ciclo (propuestos por IA, priorizados).

Uso:  python scripts/presupuesto.py preparar   # lotes por ciclo (prompts/presupuesto_lote.md)
      python scripts/presupuesto.py unir       # valida → data/referencia/presupuesto_candidatos.json
Idea: el «presupuesto» es el número de temas del ciclo, que se mantiene. Para acercarse a las metas se FUSIONAN temas
del área sobrerrepresentada (libera espacio) y se INSERTAN temas del área subrepresentada (usa ese espacio).
- Cuántos: lo calcula el libro con fórmulas (brecha del ciclo en Balance_ciclo / PISA_contenido).
- Cuáles: lo proponen los subagentes, ordenados por prioridad; el libro marca «Entra» a los primeros N.
- Inserción por COBERTURA: objetivo no cubierto en un área que ya sobra; siempre entra y se paga con una fusión
  extra de la misma área (el balance no cambia). Las de BALANCE entran según la brecha.
- REUBICAR (mover un tema de grado dentro del ciclo) no cambia el total: se propone aparte, para el balance por grado
  y para el momento de introducción frente a otros países (hoja Comparacion_paises).
Ciclos: 2.°–4.° (TIMSS 2027 4.°), 5.°–8.° (TIMSS 2027 8.°), 7.°–9.° (PISA 2025, sistemas). 7.° y 8.° están en dos ciclos:
qué bloque seguir es la decisión de política de la hoja Escenarios_7_8.
"""
import collections as C, json, math, os, sys

TEMAS = 'data/interim/temas.json'
CLAS = 'data/interim/clasificacion_2027.json'
CLAS_PISA = 'data/referencia/clasificacion_pisa2025.json'
CAT27 = 'data/referencia/catalogo_timss2027.json'
CATP = 'data/referencia/catalogo_pisa2025.json'
ALIN = 'data/interim/paises/alineacion.json'
LOTES = 'data/interim/presupuesto'
OUT = 'data/referencia/presupuesto_candidatos.json'
CICLOS = {'2-4': ((2, 3, 4), 'T4_27'), '5-8': ((5, 6, 7, 8), 'T8_27'), '7-9': ((7, 8, 9), 'PISA')}
ACCIONES = ('insertar', 'fusionar', 'reubicar')
EXTRA = 3  # candidatos de más por área, por si el equipo descarta alguno o cambia la tolerancia


def datos():
    T = {t['id']: t for t in json.load(open(TEMAS))}
    R = json.load(open(CLAS))
    cat = {c['codigo']: c for c in json.load(open(CAT27))}
    P = {}
    if os.path.exists(CLAS_PISA):
        idx = {(t['archivo'], t['hoja'], t['fila']): i for i, t in T.items()}
        P = {idx[(r['archivo'], r['hoja'], r['fila'])]: r for r in json.load(open(CLAS_PISA))}
    catp = {e['codigo']: e for e in json.load(open(CATP))['elementos']}
    return T, R, cat, P, catp


def area(i, ciclo, R, cat, P, catp):
    if ciclo == '7-9':
        c = P[i]['cont1']
        return None if c == 'FUERA' else catp[c]['grupo']
    o = R[i]['obj1']
    return None if o in ('FUERA', 'PENDIENTE') else cat[o]['dominio']


def preparar():
    T, R, cat, P, catp = datos()
    os.makedirs(LOTES, exist_ok=True)
    primer_pais = C.defaultdict(dict)
    if os.path.exists(ALIN):
        for o in json.load(open(ALIN)):
            for c in (o['obj1'], o['obj2']):
                if c and c != 'FUERA':
                    primer_pais[c][o['pais']] = min(primer_pais[c].get(o['pais'], 99), max(2, o['grado_min']))
    for ciclo, (gs, m) in CICLOS.items():
        if m == 'PISA' and not P:
            print('lote 7-9: falta clasificacion_pisa2025.json (correr después de clasificar_pisa.py unir)')
            continue
        ids = [i for i, t in T.items() if t['asignatura'] == 'Ciencias' and t['grado'] in gs]
        ev = [i for i in ids if area(i, ciclo, R, cat, P, catp)]
        if m == 'PISA':
            metas = {k: v[0] for k, v in json.load(open(CATP))['metas']['sistema'].items()}
            objetivos = [{'codigo': c, 'area': e['grupo'], 'texto': e['texto']} for c, e in catp.items() if e['tipo'] == 'contenido']
            usa = lambda i: [x for x in (P[i]['cont1'], P[i]['cont2']) if x and x != 'FUERA']
        else:
            metas = {c['dominio']: c['meta_dominio'] for c in cat.values() if c['marco'] == m}
            objetivos = [{'codigo': c, 'area': v['dominio'], 'texto': v['objetivo'], 'primer_grado_paises': primer_pais.get(c, {})}
                         for c, v in cat.items() if v['marco'] == m]
            usa = lambda i: [x for x in (R[i]['obj1'], R[i]['obj2']) if x and x not in ('FUERA', 'PENDIENTE')]
        act = C.Counter(area(i, ciclo, R, cat, P, catp) for i in ev)
        brecha = {d: round(metas[d] * len(ev) - act[d], 1) for d in metas}
        por_grado = {g: {d: round(metas[d] * len([i for i in ev if T[i]['grado'] == g])
                                  - sum(1 for i in ev if T[i]['grado'] == g and area(i, ciclo, R, cat, P, catp) == d), 1)
                         for d in metas} for g in gs}
        cuenta = C.Counter(x for i in ids for x in usa(i))
        for o in objetivos:
            o['temas_en_el_ciclo'] = cuenta[o['codigo']]
        pedir = {d: {'insertar': math.ceil(b) + EXTRA if b > 0 else 0, 'fusionar': math.ceil(-b) + EXTRA if b < 0 else 0} for d, b in brecha.items()}
        temas = [{'id': i, 'grado': T[i]['grado'], 'unidad': T[i]['unidad'], 'contenido': T[i]['contenido'],
                  'procedimental': T[i]['procedimental'], 'objetivos': usa(i), 'area': area(i, ciclo, R, cat, P, catp)} for i in ids]
        json.dump({'ciclo': ciclo, 'marco': m, 'metas': metas, 'evaluables': len(ev), 'actual': dict(act), 'brecha_ciclo': brecha,
                   'brecha_por_grado': por_grado, 'pedir': pedir, 'objetivos': objetivos, 'temas': temas},
                  open(f'{LOTES}/lote_{ciclo}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'lote_{ciclo}.json: {len(ids)} temas · brecha {brecha} · pedir {pedir}')


def unir():
    T, R, cat, P, catp = datos()
    out, err = [], []
    for ciclo in CICLOS:
        f = f'{LOTES}/salida_{ciclo}.json'
        if not os.path.exists(f):
            print(f'AVISO falta {f}')
            continue
        lote = json.load(open(f'{LOTES}/lote_{ciclo}.json'))
        gs = CICLOS[ciclo][0]
        objs = {o['codigo'] for o in lote['objetivos']}
        for s in json.load(open(f)):
            e = lambda m: err.append(f"{ciclo} {s.get('id')}: {m}")
            if s['accion'] not in ACCIONES: e(f"acción {s['accion']}")
            if s['area'] not in lote['metas']: e(f"área {s['area']}")
            if s['grado'] not in gs: e(f"grado {s['grado']}")
            if any(t not in T or T[t]['grado'] not in gs for t in s['temas']): e('tema fuera del ciclo')
            if s['accion'] == 'fusionar' and (len(s['temas']) < 2 or len({T[t]['grado'] for t in s['temas']}) != 1): e('fusión: 2+ temas del mismo grado')
            if s['accion'] == 'insertar' and s['temas']: e('inserción sin temas de origen')
            if s['accion'] == 'insertar' and s.get('motivo') not in ('balance', 'cobertura'): e(f"motivo {s.get('motivo')}")
            if s['accion'] == 'reubicar' and len(s['temas']) != 1: e('reubicar: un tema')
            if any(o not in objs for o in s['objetivos']): e(f"objetivos {s['objetivos']}")
            if len(s['propuesta'].split()) > 40 or len(s['justificacion'].split()) > 25: e('texto largo')
            out.append({**s, 'ciclo': ciclo, 'libera': len(s['temas']) - 1 if s['accion'] == 'fusionar' else 0,
                        'version': 'presupuesto-v1', 'decision_equipo': ''})
    ids = [x['id'] for x in out]
    if len(set(ids)) != len(ids): err.append('ids repetidos')
    if err:
        print(f'ERRORES {len(err)}')
        for x in err[:40]:
            print(' ', x)
        sys.exit(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Escrito {OUT}: {len(out)} candidatos', C.Counter((x['ciclo'], x['accion']) for x in out))


if __name__ == '__main__':
    {'preparar': preparar, 'unir': unir}[sys.argv[1]]()
