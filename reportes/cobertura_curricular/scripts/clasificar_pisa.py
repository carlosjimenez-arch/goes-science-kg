"""Clasificación de los temas de 7.°, 8.° y 9.° contra PISA 2025 (contenido, conocimiento, contexto, demanda).

Uso:  python scripts/clasificar_pisa.py preparar   # lotes por grado (prompts/clasificar_lote_pisa.md)
      python scripts/clasificar_pisa.py unir       # valida salidas → data/referencia/clasificacion_pisa2025.json
Reglas:
- Grados con PISA: 7.° y 8.° (junto con TIMSS 8.°) y 9.° (solo PISA). PISA evalúa a los 15 años (≈ 9.° en El Salvador).
- La competencia y las subcompetencias NO se clasifican: salen de la malla («Competencia PISA 2025» y los códigos
  E1–E6, D1–D4, I1–I5 de las microhabilidades por fase, guardados por extract_temas.py).
Salidas: data/interim/lotes_pisa/lote_G{n}.json y salida_G{n}.json; data/referencia/clasificacion_pisa2025.json
(lista con archivo, hoja, fila, procedimental, cont1, cont2, conocimiento, proc, epis, contexto, area, demanda, confianza, justificacion, version).
"""
import json, os, sys

CAT = 'data/referencia/catalogo_pisa2025.json'
TEMAS = 'data/interim/temas.json'
LOTES = 'data/interim/lotes_pisa'
OUT = 'data/referencia/clasificacion_pisa2025.json'
GRADOS = (7, 8, 9)
VERSION = 'pisa2025-v1'
CONOCIMIENTO = ('Contenido', 'Procedimental', 'Epistémico')
CONTEXTO = ('Personal', 'Local/nacional', 'Global', 'Sin contexto')
DEMANDA = ('Baja', 'Media', 'Alta')
CAMPOS_TEMA = ('archivo', 'hoja', 'fila', 'grado', 'unidad', 'contenido', 'subcontenido', 'procedimental', 'indicador', 'evidencia')


def cargar():
    cat = json.load(open(CAT))['elementos']
    temas = [t for t in json.load(open(TEMAS)) if t['asignatura'] == 'Ciencias' and t['grado'] in GRADOS]
    return cat, temas


def preparar():
    cat, temas = cargar()
    os.makedirs(LOTES, exist_ok=True)
    catalogo = [{k: e[k] for k in ('codigo', 'tipo', 'grupo', 'texto')} for e in cat if e['tipo'] != 'subcompetencia']
    for g in GRADOS:
        ts = [{**{k: t[k] for k in CAMPOS_TEMA}, 'microhabilidades': t['micro_pisa'], 'competencia_malla': t['competencia_pisa']}
              for t in temas if t['grado'] == g]
        json.dump({'grado': g, 'catalogo': catalogo, 'temas': ts}, open(f'{LOTES}/lote_G{g}.json', 'w'), ensure_ascii=False, indent=1)
        print(f'lote_G{g}.json: {len(ts)} temas')


def unir():
    cat, temas = cargar()
    cod = {e['codigo']: e['tipo'] for e in cat}
    areas = {e['texto'] for e in cat if e['tipo'] == 'area_aplicacion'}
    sal = {}
    for g in GRADOS:
        f = f'{LOTES}/salida_G{g}.json'
        if os.path.exists(f):
            for s in json.load(open(f)):
                sal[(s['archivo'], s['hoja'], s['fila'])] = s
    out, faltan, err = [], [], []
    for t in temas:
        k = (t['archivo'], t['hoja'], t['fila'])
        s = sal.get(k)
        if not s:
            faltan.append(k); continue
        e = lambda m: err.append(f'{k}: {m}')
        if s['procedimental'] != t['procedimental']: e('procedimental distinto')
        if s['cont1'] != 'FUERA' and cod.get(s['cont1']) != 'contenido': e(f"cont1 {s['cont1']}")
        if s['cont2'] and (cod.get(s['cont2']) != 'contenido' or s['cont2'] == s['cont1']): e(f"cont2 {s['cont2']}")
        if s['conocimiento'] not in CONOCIMIENTO: e(f"conocimiento {s['conocimiento']}")
        if any(cod.get(x) != 'procedimental' for x in s['proc']) or len(s['proc']) > 2: e(f"proc {s['proc']}")
        if any(cod.get(x) != 'epistemico' for x in s['epis']) or len(s['epis']) > 2: e(f"epis {s['epis']}")
        if s['contexto'] not in CONTEXTO: e(f"contexto {s['contexto']}")
        if (s['area'] or '') not in areas | {''}: e(f"area {s['area']}")
        if s['contexto'] == 'Sin contexto' and s['area']: e('área con «Sin contexto»')
        if s['demanda'] not in DEMANDA: e(f"demanda {s['demanda']}")
        if s['confianza'] not in ('alta', 'media', 'baja'): e(f"confianza {s['confianza']}")
        if len(s['justificacion'].split()) > 15: e('justificación > 15 palabras')
        out.append({**{c: t[c] for c in ('archivo', 'hoja', 'fila', 'procedimental')},
                    **{c: s[c] for c in ('cont1', 'cont2', 'conocimiento', 'proc', 'epis', 'contexto', 'area', 'demanda', 'confianza', 'justificacion')},
                    'version': VERSION, 'revisado_por': ''})
    if faltan or err:
        print(f'FALTAN {len(faltan)}; ERRORES {len(err)}')
        for x in (err + [str(f) for f in faltan])[:40]:
            print(' ', x)
        sys.exit(1)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'Escrito {OUT}: {len(out)} temas')


if __name__ == '__main__':
    {'preparar': preparar, 'unir': unir}[sys.argv[1]]()
