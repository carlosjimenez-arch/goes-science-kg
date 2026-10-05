"""Prompt 02 · Alinea los objetivos de otros países con el catálogo TIMSS 2027 (pivote común).

Uso:  python scripts/alinear_paises.py preparar   # lotes para subagentes (prompts/alinear_paises.md)
      python scripts/alinear_paises.py unir       # valida las salidas → data/interim/paises/alineacion.json
Entradas: data/interim/paises/<pais>.json (extraídos de data/referencia/externos/paises/, con página).
Reglas:
- Marco por grado, igual que El Salvador: grado_min ≤ 4 → T4_27; 5–9 → T8_27. Objetivos de 10.° en adelante
  no se alinean (no hay marco 2027 de Bachillerato).
- Nunca se alinea país contra país: todo pasa por los códigos TIMSS 2027.
Salidas: data/interim/paises/lotes/lote_<PAIS>_<MARCO>_<n>.json (entrada) y salida_<...>.json (de los subagentes);
         data/interim/paises/alineacion.json (lista: objetivo del país + obj1, obj2, confianza, justificacion, version).
"""
import glob, json, os, sys

DIR = 'data/interim/paises'
LOTES = f'{DIR}/lotes'
OUT = f'{DIR}/alineacion.json'
CAT27 = 'data/referencia/catalogo_timss2027.json'
PAISES = ('uruguay', 'colombia', 'singapur')
TAM_LOTE = 70
VERSION = 'paises-v1-2027'
CAMPOS = ('id', 'pais', 'documento', 'pagina', 'grado_o_tramo', 'eje', 'tipo', 'texto')


def marco(o):
    g = o['grado_min']
    return 'T4_27' if g <= 4 else 'T8_27' if g <= 9 else None


def cargar():
    objs = []
    for p in PAISES:
        f = f'{DIR}/{p}.json'
        if os.path.exists(f):
            objs += json.load(open(f))
        else:
            print(f'AVISO falta {f}')
    return objs, json.load(open(CAT27))


def preparar():
    objs, cat = cargar()
    os.makedirs(LOTES, exist_ok=True)
    grupos = {}
    for o in objs:
        m = marco(o)
        if m:
            grupos.setdefault((o['pais'], m), []).append(o)
    for (pais, m), lst in sorted(grupos.items()):
        catalogo = [{k: c[k] for k in ('codigo', 'dominio', 'area', 'objetivo', 'es_investigacion')} |
                    {'subitems': [s['texto'] for s in c['subitems']]} for c in cat if c['marco'] == m]
        for i in range(0, len(lst), TAM_LOTE):
            n = i // TAM_LOTE + 1
            nombre = f'lote_{pais[:2].upper()}_{m}_{n}.json'
            json.dump({'marco': m, 'catalogo': catalogo, 'objetivos': [{k: o.get(k, '') for k in CAMPOS} for o in lst[i:i + TAM_LOTE]]},
                      open(f'{LOTES}/{nombre}', 'w'), ensure_ascii=False, indent=1)
            print(f'{nombre}: {len(lst[i:i + TAM_LOTE])} objetivos')
    fuera = sum(marco(o) is None for o in objs)
    print(f'{len(objs)} objetivos · {fuera} de 10.° en adelante (no se alinean)')


def unir():
    objs, cat = cargar()
    cod = {c['codigo']: c['marco'] for c in cat}
    sal = {}
    for f in sorted(glob.glob(f'{LOTES}/salida_*.json')):
        for s in json.load(open(f)):
            sal[s['id']] = s
    out, faltan, errores = [], [], []
    for o in objs:
        m = marco(o)
        if not m:
            continue
        s = sal.get(o['id'])
        if not s:
            faltan.append(o['id']); continue
        o1, o2 = s['obj1'], s.get('obj2') or ''
        if o1 != 'FUERA' and cod.get(o1) != m:
            errores.append(f"{o['id']}: obj1={o1} no es de {m}")
        if o2 and (o2 == 'FUERA' or cod.get(o2) != m or o2 == o1):
            errores.append(f"{o['id']}: obj2={o2} inválido")
        if s['confianza'] not in ('alta', 'media', 'baja'):
            errores.append(f"{o['id']}: confianza {s['confianza']}")
        if len(s['justificacion'].split()) > 15:
            errores.append(f"{o['id']}: justificación > 15 palabras")
        out.append({**o, 'marco': m, 'obj1': o1, 'obj2': o2, 'confianza': s['confianza'],
                    'justificacion': s['justificacion'], 'version': VERSION, 'revisado_por': ''})
    if faltan or errores:
        print(f'FALTAN {len(faltan)}; ERRORES {len(errores)}')
        for e in (errores + faltan)[:40]:
            print(' ', e)
        sys.exit(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Escrito {OUT}: {len(out)} objetivos alineados')


if __name__ == '__main__':
    {'preparar': preparar, 'unir': unir}[sys.argv[1]]()
