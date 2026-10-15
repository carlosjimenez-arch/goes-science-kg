"""Proyección portátil del grafo y la autoría: recursos existentes y vacantes, nunca dominio del alumno."""

from __future__ import annotations

import copy
import hashlib
import os
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx

from goes_science_kg.config import cargar as configuracion
from goes_science_kg.config import ruta
from goes_science_kg.modelos import Nodo
from goes_science_kg.motor.archivos import canonico, decodificar, destino_seguro, firma, id_manifiesto, leer, sha
from goes_science_kg.motor.contrato import Componente, Relacion, Tema, clase_manifiesto
from goes_science_kg.motor.validacion import cargar_entrega
from goes_science_kg.motor.validacion import validar as validar_motor
from goes_science_kg.secuencias_ia import Secuencia

COLECCIONES = ('nodos', 'aristas', 'rutas', 'cola')
ARCHIVOS = {f'{k}.jsonl' for k in COLECCIONES} | {'resumen.json', 'manifiesto.json'}
TIPOS_COMPONENTE = {'actividad': 'Actividad', 'microtema': 'Microtema', 'dificultad': 'Dificultad',
                    'experimento': 'Experimento', 'refuerzo': 'RefuerzoCurricularPropuesto'}
PESO = {'baja': 0, 'media': 1, 'alta': 2}


def _exigir(condicion, mensaje):
    if not condicion:
        raise ValueError(mensaje)


def _indice(xs):
    d = {x['id']: x for x in xs}
    _exigir(len(d) == len(xs), 'ids duplicados')
    return d


def _ordenados(xs):
    return sorted(xs, key=lambda x: x['id'])


def _huellas(datos):
    return {k: firma(_ordenados(v)) for k, v in datos.items()}


def _procedencia(m, archivo, registro, campo):
    return {'id_entrega': m['id_entrega'], 'archivo': archivo, 'sha256': m['archivos'][archivo]['sha256'],
            'registro_id': registro, 'campo': campo}


def _proyectar(f, cfg):
    m = f['manifiesto']
    nodos, aristas = copy.deepcopy(f['nodos']), copy.deepcopy(f['relaciones'])

    def relacion(origen, destino, tipo, archivo, registro, campo, rol=None):
        r = {'origen': origen, 'destino': destino, 'tipo': tipo, 'rol': rol, 'metodo': 'proyeccion_explicita',
             'version': cfg['version'], 'procedencia': _procedencia(m, archivo, registro, campo)}
        aristas.append({'id': 'PROP:REL:' + firma(r), **r})

    for s in f['secuencias']:
        nodos.append({'id': s['id'], 'tipo': 'SecuenciaPropuesta', 'etiqueta': s['tema_id'], 'grado': s['grado'],
                      'props': {'registro': s, 'procedencia': _procedencia(m, 'secuencias.jsonl', s['id'], '$')}})
        relacion(s['id'], s['tema_id'], 'DESARROLLA', 'secuencias.jsonl', s['id'], 'tema_id')
        for i, texto in enumerate(s['criterios_evaluacion'], 1):
            cid = f"PROP:CRIT:{s['id']}:{i}"
            nodos.append({'id': cid, 'tipo': 'CriterioPropuesto', 'etiqueta': texto, 'grado': s['grado'],
                          'props': {'posicion': i, 'estado_mapeo': 'mapeo_pendiente', 'evalua': [],
                                    'procedencia': _procedencia(m, 'secuencias.jsonl', s['id'],
                                                               f'criterios_evaluacion[{i - 1}]')}})
            relacion(s['id'], cid, 'DEFINE_CRITERIO', 'secuencias.jsonl', s['id'], f'criterios_evaluacion[{i - 1}]')
    for c in f['componentes']:
        e = c['contenido']
        nodos.append({'id': c['id'], 'tipo': TIPOS_COMPONENTE[c['tipo']], 'etiqueta': e.get('titulo') or c['id'],
                      'props': {'registro': c, 'procedencia': _procedencia(m, 'componentes.jsonl', c['id'], '$')}})
        campos = [('objetivos', 'sirve_a'), ('evalua', 'evalua')]
        for campo, tipo in campos:
            for i, destino in enumerate(e.get(campo, [])):
                relacion(c['id'], destino, tipo, 'componentes.jsonl', c['id'], f'contenido.{campo}[{i}]')
        if c['tipo'] in ('microtema', 'dificultad'):
            relacion(c['id'], e['concepto'], 'refuerza' if c['tipo'] == 'microtema' else 'es_dificultad_de',
                     'componentes.jsonl', c['id'], 'contenido.concepto')
        if c['tipo'] == 'refuerzo' and e.get('tema_ancla'):
            relacion(c['id'], 'TEMA:' + e['tema_ancla'].removeprefix('TEMA:'), 'sirve_a',
                     'componentes.jsonl', c['id'], 'contenido.tema_ancla')
        for i, destino in enumerate(c['componentes_requeridos']):
            relacion(c['id'], destino, 'requiere_recurso', 'componentes.jsonl', c['id'],
                     f'componentes_requeridos[{i}]')
    rutas, cola = _rutas(f, cfg)
    resumen = {'version': cfg['version'], 'temas': len(rutas), 'alumno_sin_evidencia': True,
               'aula_habilitada': False, 'nodos_por_tipo': dict(sorted(Counter(n['tipo'] for n in nodos).items())),
               'aristas_por_tipo': dict(sorted(Counter(a['tipo'] for a in aristas).items())),
               'cola': len(cola), 'por_grado': []}
    for g in range(2, 12):
        rs = [r for r in rutas if r['grado'] == g]
        resumen['por_grado'].append({'grado': g, 'temas': len(rs),
                                    'secuencias_autoria': sum(r['secuencia']['autoria_asistida'] for r in rs),
                                    'con_evaluacion_cerrada_autoria': sum(
                                        bool(r['evaluacion_objetivo']['pareja_autoria']) for r in rs),
                                    'solo_practicas': sum(r['tipo_objetivo'] == 'practica_metodologica' for r in rs)})
    return {'nodos': _ordenados(nodos), 'aristas': _ordenados(aristas), 'rutas': rutas, 'cola': cola,
            'resumen': resumen}


def _rutas(f, cfg):
    temas, comps = _indice(f['temas']), _indice(f['componentes'])
    secuencias = {s['tema_id']: s for s in f['secuencias']}
    sal, ent, trabaja = defaultdict(list), defaultdict(list), defaultdict(list)
    equivalencias = nx.Graph()
    eq_ids = {}
    for a in f['relaciones']:
        sal[a['origen']].append(a)
        ent[a['destino']].append(a)
        if a['tipo'] == 'TRABAJA' and a['origen'] in temas:
            trabaja[a['destino']].append(a)
        if a['tipo'] == 'EQUIVALE_A' and a['origen'].startswith('CON:'):
            equivalencias.add_edge(a['origen'], a['destino'])
            eq_ids[frozenset((a['origen'], a['destino']))] = a['id']
    antecedentes = {}
    for cid in {n['id'] for n in f['nodos'] if n['tipo'] == 'Concepto'}:
        grupo = nx.node_connected_component(equivalencias, cid) if cid in equivalencias else {cid}
        filas = []
        for c in sorted(grupo):
            camino = nx.shortest_path(equivalencias, cid, c) if cid != c else [cid]
            via = [eq_ids[frozenset((a, b))] for a, b in zip(camino, camino[1:], strict=False)]
            for a in trabaja[c]:
                if a['rol'] == 'principal' or PESO.get(a.get('confianza'), -1) >= PESO[cfg['confianza_minima']]:
                    t = temas[a['origen']]
                    filas.append({'tema_id': t['id'], 'grado': t['grado'], 'orden': t['orden'],
                                  'fuente': t['fuente'], 'arista_id': a['id'], 'via_equivalencias': via})
        antecedentes[cid] = sorted(filas, key=lambda x: (x['grado'], x['orden'], x['arista_id']))
    cola = {}

    def pendiente(tipo, clave, tema, **evidencia):
        k = (tipo, clave)
        if k not in cola:
            cola[k] = {'id': 'PROP:PEND:' + firma(k), 'tipo': tipo, 'clave': clave, 'temas_afectados': [],
                       'evidencias': [], 'estado': 'candidato_a_revisar', 'recomendacion_firme': False}
        cola[k]['temas_afectados'].append(tema)
        cola[k]['evidencias'].append({'tema_id': tema, **evidencia})

    rutas = []
    for t in sorted(temas.values(), key=lambda x: x['orden']):
        if not t['en_alcance_ciencias']:
            continue
        tid, g, s = t['id'], t['grado'], secuencias[t['id']]
        conceptos, practicas, bases, materiales = [], [], [], set()

        def recursos(tipo, grado=g, **campos):
            return [c['id'] for c in f['componentes'] if c['tipo'] == tipo and grado in c['contenido'].get('grados', [])
                    and all((v in c['contenido'].get(k, []) if isinstance(c['contenido'].get(k), list)
                             else c['contenido'].get(k) == v) for k, v in campos.items())]

        for a in sal[tid]:
            if a['tipo'] != 'TRABAJA':
                continue
            reg = {'id': a['destino'], 'rol': a['rol'], 'confianza': a.get('confianza'), 'arista_id': a['id'],
                   'procedencia': _procedencia(f['manifiesto'], 'relaciones.jsonl', a['id'], '$')}
            (conceptos if a['destino'].startswith('CON:') else practicas).append(reg)
        for c in conceptos:
            for a in ent[c['id']]:
                if a['tipo'] != 'PRERREQUISITO_DE' or PESO.get(a.get('confianza'), -1) < PESO[cfg['confianza_minima']]:
                    continue
                cid, ant = a['origen'], antecedentes[a['origen']]
                mismo = [v for v in ant if v['grado'] == g]
                antes = [v for v in ant if v['grado'] < g or (v['grado'] == g
                         and v['fuente']['archivo'] == t['fuente']['archivo'] and v['orden'] < t['orden'])]
                estado = 'ausente' if not ant else 'previo' if antes else 'mismo_grado' if mismo else 'posterior'
                orden = ('previo' if antes else 'mismo_tema' if any(v['tema_id'] == tid for v in mismo) else
                         'posterior_en_archivo' if any(v['fuente']['archivo'] == t['fuente']['archivo'] for v in mismo)
                         else 'no_ordenable_mismo_grado' if mismo else estado)
                sondeos = recursos('actividad', evalua=cid, rol='sondeo')
                sondeos_autoria = [i for i in sondeos if comps[i]['usos']['autoria']
                                    and comps[i]['contenido']['formato'] in ('opcion_multiple', 'numerica')]
                microtemas = recursos('microtema', concepto=cid)
                completos = []
                for mid in microtemas:
                    mt = comps[mid]['contenido']
                    pp, cc = mt['practica'], mt['comprobacion']
                    if pp != cc and all(i in comps and comps[i]['tipo'] == 'actividad'
                                        and g in comps[i]['contenido'].get('grados', [])
                                        and cid in comps[i]['contenido'].get('evalua', []) for i in (pp, cc)):
                        completos.append({'microtema': mid, 'practica': pp, 'comprobacion': cc,
                                          'autoria': all(comps[i]['usos']['autoria'] for i in (mid, pp, cc)),
                                          'requiere_evaluador': any(comps[i]['contenido']['formato'] == 'abierta'
                                                                   for i in (pp, cc))})
                        materiales.update((pp, cc))
                materiales.update(sondeos + microtemas)
                bases.append({'concepto': cid, 'para_concepto': c['id'], 'arista_id': a['id'],
                              'confianza': a['confianza'], 'estado_relacion': 'propuesta_ia_pendiente'
                              if not a.get('props', {}).get('revisado_por') else 'revisada',
                              'estado_curricular': estado, 'orden_respecto_al_tema': orden, 'antecedentes': ant,
                              'sondeos': sondeos, 'sondeos_cerrados_autoria': sondeos_autoria,
                              'microtemas': microtemas, 'refuerzos_completos': completos})
                if len(sondeos_autoria) < cfg['sondeos_distintos_requeridos']:
                    pendiente('falta_sondeo', f'{g}:{cid}', tid, concepto=cid, arista_id=a['id'],
                              disponibles_consulta=len(sondeos), disponibles_cerrados_autoria=len(sondeos_autoria),
                              requeridos=cfg['sondeos_distintos_requeridos'])
                if not any(v['autoria'] and not v['requiere_evaluador'] for v in completos):
                    pendiente('falta_microtema', f'{g}:{cid}', tid, concepto=cid, arista_id=a['id'],
                              disponibles_consulta=len(completos),
                              disponibles_cerrados_autoria=sum(v['autoria'] and not v['requiere_evaluador']
                                                              for v in completos))
                if estado in ('ausente', 'posterior') or orden == 'posterior_en_archivo':
                    pendiente('base_' + ('posterior' if orden == 'posterior_en_archivo' else estado),
                              cid, tid, concepto=cid, para_concepto=c['id'], arista_id=a['id'], estado=estado)
        asociadas = recursos('actividad', objetivos=tid, rol='objetivo')
        objetivos = [i for i in asociadas if tid in comps[i]['contenido'].get('evalua', [])]
        cerradas = [i for i in objetivos if comps[i]['contenido']['formato'] in ('opcion_multiple', 'numerica')]
        abiertas = [i for i in objetivos if comps[i]['contenido']['formato'] == 'abierta']
        aptas = [i for i in cerradas if comps[i]['usos']['autoria']]
        pareja = {'objetivo': aptas[0], 'reevaluacion': aptas[1]} if len(aptas) >= 2 else None
        if not pareja:
            pendiente('falta_evaluacion_objetivo', tid, tid)
        if not s['autoria_asistida']:
            pendiente('retencion_secuencia', s['id'], tid, motivos=s['motivos_retencion'])
        pendiente('mapeo_criterios', str(g), tid, secuencia_id=s['id'])
        materiales.update(asociadas + recursos('experimento', objetivos=tid))
        focos = {c['id'] for c in conceptos} | {b['concepto'] for b in bases}
        materiales.update(c['id'] for c in f['componentes'] if c['tipo'] == 'dificultad'
                           and c['contenido']['concepto'] in focos)
        propuestas = [{k: c[k] for k in ('id', 'tipo', 'usos', 'calidad')} | {
                      'grados_destino': c['contenido'].get('grados_destino') or c['contenido'].get('grados', [])}
                      for c in f['componentes'] if c['tipo'] == 'refuerzo'
                      and c['contenido'].get('tema_ancla', '').removeprefix('TEMA:') == tid.removeprefix('TEMA:')]
        frontera = list(materiales)
        while frontera:
            nuevos = set(comps[frontera.pop()]['componentes_requeridos']) - materiales
            materiales.update(nuevos)
            frontera.extend(sorted(nuevos))
        obs = [o for o in cfg['observaciones_semanticas'] if o['tema_id'] == tid
               or any(v['tema_id'] == o['tema_id'] for b in bases for v in b['antecedentes'])]
        rutas.append({'id': 'PROP:RUTA:' + tid.removeprefix('TEMA:'), 'tema_id': tid, 'grado': g,
                      'asignatura': t['asignatura'], 'orden': t['orden'], 'fuente': t['fuente'],
                      'aliases': t['aliases'], 'alumno_sin_evidencia': True,
                      'tipo_objetivo': 'conceptual' if conceptos else 'practica_metodologica',
                      'secuencia': {k: s[k] for k in ('id', 'estado', 'autoria_asistida', 'motivos_retencion',
                                                     'tiempo_observado_min', 'aula_habilitada')},
                      'criterios': [f"PROP:CRIT:{s['id']}:{i}" for i in range(1, 4)],
                      'conceptos': conceptos, 'practicas': practicas,
                      'bases': sorted(bases, key=lambda b: b['arista_id']),
                      'materiales': [{k: comps[i][k] for k in ('id', 'tipo', 'usos', 'calidad')} | {
                          'grado_exacto': g in comps[i]['contenido'].get('grados', []),
                          'autoria_en_grado': comps[i]['usos']['autoria']
                          and g in comps[i]['contenido'].get('grados', [])} for i in sorted(materiales)],
                      'propuestas_curriculares': propuestas,
                      'evaluacion_objetivo': {'cerradas': cerradas, 'abiertas_requieren_evaluador': abiertas,
                                             'pareja_autoria': pareja}, 'observaciones_semanticas': obs})
    for v in cola.values():
        v['temas_afectados'] = sorted(set(v['temas_afectados']))
        v['impacto_estructural'] = len(v['temas_afectados'])
        v['grados'] = sorted({temas[i]['grado'] for i in v['temas_afectados']})
        v['evidencias'] = sorted({canonico(e): e for e in v['evidencias']}.values(), key=canonico)
    ordenada = sorted(cola.values(), key=lambda v: (-v['impacto_estructural'], v['id']))
    for i, v in enumerate(ordenada, 1):
        v['prioridad'] = i
    return rutas, ordenada


def compilar(entrega: Path) -> dict:
    """Valida el motor y construye en memoria; no consulta ni modifica la base del productor."""
    validar_motor(entrega)
    m, _ = cargar_entrega(entrega)
    _exigir(m.version_contrato == '1.1.0', 'se requiere contrato motor 1.1.0')
    f = {k: [decodificar(linea) for linea in (Path(entrega) / (k + '.jsonl')).read_text().splitlines()]
         for k in ('nodos', 'relaciones', 'temas', 'secuencias', 'componentes')}
    cfg = copy.deepcopy(configuracion('grafo_refuerzo'))
    meta = {'manifiesto_fuente': m.model_dump(mode='json'), 'configuracion': cfg, 'temas': f['temas'],
            'nodos_base_ids': sorted(n['id'] for n in f['nodos']),
            'aristas_base_ids': sorted(a['id'] for a in f['relaciones']), 'huellas_colecciones_fuente': _huellas(f),
            'orden_fuente': {k: [x['id'] for x in xs] for k, xs in f.items()},
            'insumos': {p: sha(ruta(p)) for p in
                        ('src/goes_science_kg/grafo_refuerzo.py', 'config/grafo_refuerzo.yaml')}}
    datos = {**_proyectar({**f, 'manifiesto': meta['manifiesto_fuente']}, cfg), 'metadatos': meta}
    validar(datos)
    return datos


def validar(datos: dict) -> None:
    """Reconstruye relaciones, rutas, permisos y cola exclusivamente desde los registros preservados."""
    try:
        _validar(datos)
    except (KeyError, TypeError, AttributeError, IndexError) as error:
        raise ValueError('proyección mal formada') from error


def _validar(datos):
    _exigir(set(datos) == {*COLECCIONES, 'resumen', 'metadatos'}, 'colecciones de proyección inválidas')
    meta = datos['metadatos']
    m = meta['manifiesto_fuente']
    clase_manifiesto(m['version_contrato']).model_validate(m)
    _exigir(id_manifiesto(m) == m['id_entrega'], 'id manifiesto fuente distinto')
    ns, ars = _indice(datos['nodos']), _indice(datos['aristas'])
    _exigir(all(a['origen'] in ns and a['destino'] in ns for a in ars.values()), 'extremo de arista inexistente')
    f = {'manifiesto': m, 'nodos': [ns[i] for i in meta['nodos_base_ids']],
         'relaciones': [ars[i] for i in meta['aristas_base_ids']], 'temas': meta['temas'],
         'secuencias': [n['props']['registro'] for n in ns.values() if n['tipo'] == 'SecuenciaPropuesta'],
         'componentes': [n['props']['registro'] for n in ns.values() if n['tipo'] in TIPOS_COMPONENTE.values()]}
    _exigir(_huellas({k: v for k, v in f.items() if k != 'manifiesto'}) == meta['huellas_colecciones_fuente'],
            'registros originales o aristas base modificados')
    for k, modelo in (('nodos', Nodo), ('relaciones', Relacion), ('temas', Tema),
                      ('secuencias', Secuencia), ('componentes', Componente)):
        indice = _indice(f[k])
        orden = meta['orden_fuente'][k]
        _exigir(len(orden) == len(indice) and set(orden) == set(indice), 'orden de fuente incompleto o duplicado')
        f[k] = [indice[i] for i in orden]
        contenido = ''.join(canonico(x) + '\n' for x in f[k]).encode('utf-8')
        ficha = m['archivos'][k + '.jsonl']
        _exigir(hashlib.sha256(contenido).hexdigest() == ficha['sha256'] and len(contenido) == ficha['bytes'],
                f'SHA de registros distinto de manifiesto fuente: {k}')
        for fila in f[k]:
            modelo.model_validate(fila)
        _exigir(len(f[k]) == m['metricas'][k], f'conteo distinto de la fuente: {k}')
    cfg = meta['configuracion']
    _exigir(cfg['confianza_minima'] == 'media' and cfg['criterios_por_secuencia'] == 3
            and cfg['sondeos_distintos_requeridos'] >= 2, 'política de proyección incompatible')
    temas = _indice(f['temas'])
    esperados = {t['id'] for t in f['temas'] if t['en_alcance_ciencias']}
    _exigir(len(esperados) == cfg['temas_esperados'] == 920, 'se requieren los 920 temas de Ciencias')
    _exigir(len(datos['rutas']) == len(esperados) and {r['tema_id'] for r in datos['rutas']} == esperados,
            'rutas no corresponden a los 920 temas')
    _exigir(len(f['secuencias']) == 920 and {s['tema_id'] for s in f['secuencias']} == esperados,
            'secuencias no corresponden a los temas')
    _exigir(sum(n['tipo'] == 'CriterioPropuesto' for n in ns.values()) == 2760, 'se requieren 2760 criterios')
    _exigir(all(ns[i]['grado'] == t['grado'] for i, t in temas.items()), 'grado distinto de atributo fuente')
    nuevo = _proyectar(f, cfg)
    _exigir(all(datos[k] == v for k, v in nuevo.items()), 'proyección, tipos, rutas, permisos o cola incoherentes')


def exportar(destino: Path, entrega: Path) -> Path:
    """Publica seis archivos inmutables; una repetición con bytes idénticos es idempotente."""
    _exigir(not Path(destino).is_symlink(), 'destino simbólico')
    destino = destino_seguro(Path(destino))
    fuente = Path(entrega).resolve()
    _exigir(not (destino == fuente or destino.is_relative_to(fuente) or fuente.is_relative_to(destino)),
            'el destino y la fuente no pueden contenerse')
    base = ruta('entregas/motor').resolve()
    _exigir(not (destino == base or destino.is_relative_to(base) or base.is_relative_to(destino)),
            'las entregas del motor son inmutables')
    datos = compilar(Path(entrega))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.grafo-refuerzo-', dir=destino.parent) as temporal:
        d = Path(temporal) / 'entrega'
        d.mkdir()
        for k in COLECCIONES:
            (d / f'{k}.jsonl').write_text(''.join(canonico(x) + '\n' for x in datos[k]), encoding='utf-8')
        (d / 'resumen.json').write_text(canonico({k: datos[k] for k in ('resumen', 'metadatos')}) + '\n',
                                      encoding='utf-8')
        m = {'formato': 'GOES Grafo Refuerzo', 'version': datos['resumen']['version'], 'version_contrato': '1.0.0',
             'id_entrega_fuente': datos['metadatos']['manifiesto_fuente']['id_entrega'],
             'version_fuente': datos['metadatos']['manifiesto_fuente']['version_contenido'],
             'insumos': datos['metadatos']['insumos'],
             'archivos': {p.name: {'sha256': sha(p), 'bytes': p.stat().st_size} for p in sorted(d.iterdir())}}
        m['id_entrega'] = id_manifiesto(m)
        (d / 'manifiesto.json').write_text(canonico(m) + '\n', encoding='utf-8')
        cargar(d)
        if destino.exists():
            _exigir(destino.is_dir() and {p.name for p in destino.iterdir()} == ARCHIVOS
                    and all(not (destino / n).is_symlink() and (destino / n).is_file()
                            and (destino / n).read_bytes() == (d / n).read_bytes() for n in ARCHIVOS),
                    'destino existente con contenido distinto: no se sobrescribe')
        else:
            os.rename(d, destino)
    return destino


def cargar(carpeta: Path) -> dict:
    """Lee y valida una proyección autónoma, sin necesitar la entrega fuente ni los Excel."""
    carpeta = Path(carpeta)
    _exigir(carpeta.is_dir() and not carpeta.is_symlink(), 'carpeta inexistente o simbólica')
    _exigir({p.name for p in carpeta.iterdir()} == ARCHIVOS
            and all(p.is_file() and not p.is_symlink() for p in carpeta.iterdir()), 'archivos inesperados o simbólicos')
    m = leer(carpeta / 'manifiesto.json')
    _exigir(isinstance(m, dict), 'manifiesto debe ser objeto')
    _exigir(m.get('formato') == 'GOES Grafo Refuerzo' and m.get('version_contrato') == '1.0.0'
            and m.get('id_entrega') == id_manifiesto(m) and set(m['archivos']) == ARCHIVOS - {'manifiesto.json'},
            'manifiesto inválido')
    for n, ficha in m['archivos'].items():
        p = carpeta / n
        _exigir(sha(p) == ficha['sha256'] and p.stat().st_size == ficha['bytes'], 'SHA o tamaño distinto: ' + n)
    datos = {k: [decodificar(linea) for linea in (carpeta / f'{k}.jsonl').read_text().splitlines()]
             for k in COLECCIONES}
    datos.update(leer(carpeta / 'resumen.json'))
    validar(datos)
    _exigir(m['id_entrega_fuente'] == datos['metadatos']['manifiesto_fuente']['id_entrega']
            and m['version_fuente'] == datos['metadatos']['manifiesto_fuente']['version_contenido']
            and m['version'] == datos['resumen']['version'] and m['insumos'] == datos['metadatos']['insumos'],
            'manifiesto no corresponde a metadatos')
    return datos


def consultar(datos: dict, identificador: str) -> dict:
    """Resuelve id estable, id sin prefijo o alias exacto y muestra recursos con sus permisos originales."""
    candidatas = [r for r in datos['rutas'] if identificador in (r['tema_id'], r['tema_id'].removeprefix('TEMA:'),
                                                              *r['aliases'])]
    _exigir(len(candidatas) == 1, 'tema de Ciencias o alias inexistente/ambiguo: ' + identificador)
    r = copy.deepcopy(candidatas[0])
    ns = _indice(datos['nodos'])
    r['detalle'] = {'secuencia': ns[r['secuencia']['id']]['props']['registro'],
                    'criterios': [ns[i] for i in r['criterios']],
                    'componentes': [ns[c['id']]['props']['registro'] for c in r['materiales']]}
    return copy.deepcopy(r)
