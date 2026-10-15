"""Visor local y CSV de revisión a partir de una entrega ya validada; no cambia sus permisos."""

from __future__ import annotations

import argparse
import csv
import json
import unicodedata
from collections import Counter
from pathlib import Path

from goes_science_kg.motor.archivos import destino_seguro
from goes_science_kg.motor.validacion import cargar_entrega, validar
from goes_science_kg.secuencias_ia import ETAPAS


def preparar(entrega: Path, salida: Path) -> dict:
    validar(entrega)
    manifiesto, registros = cargar_entrega(entrega)
    if 'secuencias' not in registros:
        raise ValueError('la entrega no contiene la capa de secuencias')
    salida = destino_seguro(salida)
    salida.mkdir(parents=True, exist_ok=True)
    temas = {t.id: t for t in registros['temas']}
    filas, visor = [], []
    for s in sorted(registros['secuencias'], key=lambda s: temas[s.tema_id].orden):
        t = temas[s.tema_id]
        filas.append([s.tema_id, s.grado, s.asignatura, t.columnas['Unidad'], s.estado, s.autoria_asistida,
                      s.sesiones_sugeridas, ' / '.join(s.motivos_retencion), ' / '.join(s.pendientes),
                      t.fuente.archivo, t.fuente.hoja, t.fuente.fila])
        item = {'id': s.tema_id, 'grado': s.grado, 'asignatura': s.asignatura, 'autoria': s.autoria_asistida,
                'contenido': t.columnas['Contenido'], 'procedimental': t.columnas['Procedimental'],
                'unidad': t.columnas['Unidad'], 'sesiones': s.sesiones_sugeridas, 'motivo_tiempo': s.motivo_tiempo,
                'producto': s.producto_evaluable, 'criterios': s.criterios_evaluacion, 'salida': s.consigna_salida,
                'apoyos': s.apoyos, 'offline': s.alternativa_sin_internet, 'fuente': t.fuente.model_dump(),
                'momentos': [{'nombre': m.nombre, 'original': m.texto_malla, 'propuesta': m.propuesta_ia}
                             for m in s.momentos],
                'revisiones': [{'etapa': e, **{k: v for k, v in s.revisiones[e].model_dump().items()
                                             if k in ('rol', 'decision', 'confianza', 'justificacion',
                                                      'evidencia', 'pendientes')}}
                               for e in ETAPAS if e in s.revisiones]}
        texto = ' '.join([s.tema_id, item['contenido'], item['procedimental'], *s.pendientes])
        item['busqueda'] = ''.join(c for c in unicodedata.normalize('NFD', texto.lower())
                                  if unicodedata.category(c) != 'Mn')
        visor.append(item)
    # Los textos curriculares no se interpretan como HTML ni como código JavaScript.
    datos = json.dumps(visor, ensure_ascii=False)
    for caracter, seguro in (('&', '\\u0026'), ('<', '\\u003c'), ('>', '\\u003e')):
        datos = datos.replace(caracter, seguro)
    plantilla = (Path(__file__).parent / 'templates/secuencias_revision.html').read_text(encoding='utf-8')
    (salida / 'visor.html').write_text(plantilla.replace('__DATOS__', datos), encoding='utf-8')
    with (salida / 'pendientes_por_tema.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, lineterminator='\n')
        w.writerow(['tema_id', 'grado', 'asignatura', 'unidad_actual', 'estado_ia', 'autoria_ia',
                    'sesiones_sugeridas', 'motivos_retencion', 'pendientes', 'archivo', 'hoja', 'fila'])
        w.writerows([['\t' + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v
                      for v in fila] for fila in filas])
    return {'id_entrega': manifiesto.id_entrega, 'temas': len(visor),
            'estados': dict(Counter(s.estado for s in registros['secuencias'])), 'salida': str(salida)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('entrega', type=Path)
    p.add_argument('salida', type=Path)
    args = p.parse_args()
    print(json.dumps(preparar(args.entrega, args.salida), ensure_ascii=False, indent=2))
