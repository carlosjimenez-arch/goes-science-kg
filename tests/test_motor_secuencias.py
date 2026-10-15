"""Aceptación de la entrega real de todos los grados y del consumidor de ambos contratos."""

from __future__ import annotations

import os
from pathlib import Path

from goes_science_kg import secuencias_ia
from goes_science_kg.motor import archivos
from goes_science_kg.motor.construccion import exportar
from goes_science_kg.motor.consumidor import activar, consultar, importar
from goes_science_kg.motor.validacion import cargar_entrega, validar

ENTREGA = Path(os.environ.get('GSKG_ENTREGA_SECUENCIAS', 'entregas/motor/0.2.0'))


def test_todos_los_grados_tienen_revision_completa_y_retenciones_visibles():
    rep = validar(ENTREGA)
    m, datos = cargar_entrega(ENTREGA)
    ejecucion = datos['catalogos']['secuencias_ia_ejecucion']
    assert ejecucion['alcance']['temas_ciencias'] == 920
    assert {'cierre_fisica', 'cierre_tierra_espacio', 'cierre_biologia', 'cierre_quimica'} <= ejecucion['roles'].keys()
    assert 'data/interim/secuencias_ia/EJECUCION.json' in m.insumos
    assert rep['metricas']['secuencias'] == 920
    assert {s.grado for s in datos['secuencias']} == set(range(2, 12))
    assert any(s.autoria_asistida for s in datos['secuencias'])
    assert any(not s.autoria_asistida for s in datos['secuencias'])
    assert all(s.revisado_por is None and s.tiempo_observado_min is None and not s.aula_habilitada
               for s in datos['secuencias'])
    assert all({'ciencia', 'psicopedagogia', 'refutacion', 'final'} <= s.revisiones.keys()
               for s in datos['secuencias'])


def test_consumidor11_portatil_retenciones_alias_e_idempotencia_y_reversion(tmp_path, monkeypatch):
    almacen = tmp_path / 'motor'
    anterior = importar('entregas/motor/0.1.0', almacen)
    m, datos = cargar_entrega(ENTREGA)
    def sin_productor(*args):
        raise FileNotFoundError('instalación sin el repositorio productor')
    monkeypatch.setattr(secuencias_ia, 'configuracion', sin_productor)
    monkeypatch.setattr(archivos, 'ruta', sin_productor)
    nueva = importar(ENTREGA, almacen)
    assert nueva['creada'] and not importar(ENTREGA, almacen)['creada']
    apta = next(s for s in datos['secuencias'] if s.autoria_asistida)
    retenida = next(s for s in datos['secuencias'] if not s.autoria_asistida)
    assert consultar(almacen, apta.tema_id, 'autoria')['secuencia']['id'] == apta.id
    tema = next(t for t in datos['temas'] if t.id == apta.tema_id)
    assert consultar(almacen, tema.aliases[0], 'autoria')['secuencia']['id'] == apta.id
    proyeccion = consultar(almacen, retenida.tema_id, 'autoria')
    assert proyeccion['secuencia'] is None
    assert any(o['id'] == retenida.id for o in proyeccion['omitidos'])
    assert consultar(almacen, retenida.tema_id)['secuencia']['motivos_retencion']
    activar(almacen, anterior['id_entrega'])
    assert 'secuencia' not in consultar(almacen, apta.tema_id)
    activar(almacen, m.id_entrega)
    assert consultar(almacen, apta.tema_id)['secuencia']['id'] == apta.id


def test_exportacion11_reproducible_con_insumos_y_base_git_registrados(tmp_path):
    m, _ = cargar_entrega(ENTREGA)
    nuevo = exportar(tmp_path / 'entrega', m.version_contenido, m.commit_base, incluir_secuencias=True)
    original = ENTREGA
    assert {p.name: archivos.sha(p) for p in nuevo.iterdir()} == {
        p.name: archivos.sha(p) for p in original.iterdir()}
