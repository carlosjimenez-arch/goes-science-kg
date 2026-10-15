"""Vista del grafo compuesto y su cola; no inventa conexiones ni cambia permisos."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from goes_science_kg.grafo_refuerzo import cargar
from goes_science_kg.motor.archivos import destino_seguro, escribir, sha


def preparar(carpeta: Path, salida: Path) -> dict:
    datos = cargar(carpeta)
    salida = destino_seguro(salida)
    if salida == carpeta.resolve() or salida.is_relative_to(carpeta.resolve()):
        raise ValueError('el visor debe quedar fuera de la versión inmutable')
    salida.mkdir(parents=True, exist_ok=True)
    nodos = {n['id']: n for n in datos['nodos']}
    temas = {t['id']: t for t in datos['metadatos']['temas']}

    def etiqueta(n):
        if n['tipo'] == 'SecuenciaPropuesta':
            return 'Secuencia propuesta'
        contenido = n.get('props', {}).get('registro', {}).get('contenido', {})
        return contenido.get('titulo') or contenido.get('enunciado') or contenido.get('descripcion') or n['etiqueta']

    vistas = []
    for r in sorted(datos['rutas'], key=lambda r: r['orden']):
        t = temas[r['tema_id']]
        vistas.append({**r, 'titulo': t['columnas']['Contenido'],
                       'procedimental': t['columnas']['Procedimental'],
                       'detalle_secuencia': nodos[r['secuencia']['id']]['props']['registro'],
                       'criterios': [{'id': i, 'texto': nodos[i]['etiqueta']} for i in r['criterios']]})
    payload = {'rutas': vistas, 'cola': datos['cola'], 'resumen': datos['resumen'],
               'nodos': [{'id': n['id'], 'tipo': n['tipo'], 'etiqueta': etiqueta(n)} for n in nodos.values()],
               'componentes': {n['id']: n['props']['registro'] for n in nodos.values()
                               if n.get('props', {}).get('registro', {}).get('tipo') in
                               ('actividad', 'microtema', 'dificultad', 'experimento', 'refuerzo')},
               'aristas': [{k: a.get(k) for k in ('id', 'origen', 'destino', 'tipo', 'rol', 'confianza')}
                           for a in datos['aristas']]}
    texto = json.dumps(payload, ensure_ascii=False)
    for c, escape in (('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e')):
        texto = texto.replace(c, escape)
    plantilla = Path(__file__).with_name('templates') / 'grafo_refuerzo.html'
    (salida / 'visor.html').write_text(plantilla.read_text().replace('__DATOS__', texto), encoding='utf-8')
    with (salida / 'cola_autoria.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['id', 'prioridad', 'tipo', 'grados', 'temas_distintos_afectados', 'estado', 'temas'])
        for q in datos['cola']:
            fila = [q['id'], q['prioridad'], q['tipo'], ', '.join(map(str, q['grados'])),
                    q['impacto_estructural'], q['estado'], ' / '.join(q['temas_afectados'])]
            w.writerow(['\t' + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v
                        for v in fila])
    rep = {'fuente': datos['metadatos']['manifiesto_fuente']['id_entrega'], 'temas': len(vistas),
           'nodos': len(nodos), 'aristas': len(datos['aristas']), 'cola': len(datos['cola']),
           'sha_visor': sha(salida / 'visor.html'), 'sha_cola': sha(salida / 'cola_autoria.csv')}
    escribir(salida / 'VERIFICACION_GENERACION.json', rep)
    return rep


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('carpeta', type=Path)
    p.add_argument('salida', type=Path)
    args = p.parse_args()
    print(json.dumps(preparar(args.carpeta, args.salida), ensure_ascii=False, indent=2))
