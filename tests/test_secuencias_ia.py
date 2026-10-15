"""La revisión IA es una cadena de candidatas citadas, no una firma humana ni una votación."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
from typer.testing import CliRunner

from goes_science_kg import secuencias_ia as si
from goes_science_kg.cli import app
from goes_science_kg.motor.archivos import canonico, decodificar, firma, leer
from goes_science_kg.motor.contrato import Tema, archivos_para, esquemas
from goes_science_kg.motor.validacion import validar


@pytest.fixture()
def tema():
    filas = (Path('entregas/motor/0.1.0') / 'temas.jsonl').read_text().splitlines()
    return Tema.model_validate(decodificar(filas[0]))


def dictamen(t, etapa, rs, **campos):
    entrada = si.entrada_etapa(t, etapa, rs)
    rol = ('psicopedagogo' if etapa == 'psicopedagogia' else 'refutador' if etapa.startswith('refutacion')
           else si.ROLES_CIENCIA[t.asignatura])
    d = {'tema_id': t.id, 'rol': rol, 'decision': 'sin_objecion_en_lectura', 'confianza': 'media',
         'justificacion': 'Registro sintético para comprobar la cadena, sin aprobar contenido real.',
         'evidencia': [{'campo': 'Procedimental', 'cita': t.columnas['Procedimental']}],
         'cambios': [], 'pendientes': [], 'sha_entrada': firma(entrada)}
    if etapa == 'final' and len(entrada['columnas'].get('Indicador avanzado', '')) >= 20:
        d['evidencia'].append({'campo': 'Indicador avanzado',
                              'cita': ' '.join(entrada['columnas']['Indicador avanzado'].split()[:30])})
    if etapa == 'psicopedagogia':
        d.update(criterios_evaluacion=['Elige el instrumento para la magnitud.', 'Registra una lectura con su unidad.',
                                      'Explica cómo comparar dos lecturas.'],
                 consigna_salida='Muestra cómo medirías un objeto y explica el instrumento elegido.',
                 apoyos=['Permitir respuesta oral o dibujo con apoyo.'],
                 alternativa_sin_internet='Usar instrumentos del aula y registrar en papel.',
                 sesiones_sugeridas=1, motivo_tiempo='Hipótesis de planificación, pendiente de observación.')
    d.update(campos)
    return si.Dictamen.model_validate(d)


def cadena(t):
    rs = {}
    for e in si.ETAPAS[:4]:
        rs[e] = dictamen(t, e, rs)
    return rs


def test_contrato_anterior_sigue_validando_y_sus_esquemas_no_cambian():
    assert validar('entregas/motor/0.1.0')['resultado'] == 'valido'
    assert leer(Path('entregas/motor/0.1.0/esquemas.json')) == esquemas('1.0.0')
    assert archivos_para('1.1.0') - archivos_para('1.0.0') == {'secuencias.jsonl'}
    assert 'secuencias' in esquemas('1.1.0')


def test_cadena_conserva_fuentes_y_no_inventa_ensayo_o_firma(tema):
    rs = cadena(tema)
    s = si.secuencia_de(tema, rs)
    assert s.autoria_asistida and s.estado == 'revisado_multiagente_ia'
    assert s.revisado_por is None and s.tiempo_observado_min is None and not s.aula_habilitada
    assert not s.presupuesto_demostrado
    assert sum(m.minutos_planificados for m in s.momentos) + s.minutos_transiciones == 55
    assert s.fuente_sha_columnas == firma(tema.columnas)
    assert s.momentos[0].texto_malla == tema.columnas[si.MOMENTOS[0]]
    si.validar_secuencias([s], {tema.id: tema}, si.configuracion())


def test_cita_inventada_y_cambio_de_campo_oficial_se_rechazan(tema):
    e = si.entrada_ciencia(tema)
    d = dictamen(tema, 'ciencia', {})
    d.evidencia[0].cita = 'Una cita que no aparece en el documento oficial.'
    with pytest.raises(ValueError, match='cita no encontrada'):
        si.comprobar_dictamen(d, e, 'ciencia', tema.asignatura)
    d = dictamen(tema, 'ciencia', {}, decision='corregir', cambios=[{
        'campo': 'Procedimental', 'antes': tema.columnas['Procedimental'], 'despues': 'Otro objetivo curricular.',
        'motivo': 'Prueba de un cambio no autorizado.'}])
    with pytest.raises(ValueError, match='no permitido'):
        si.comprobar_dictamen(d, e, 'ciencia', tema.asignatura)


def test_correccion_conserva_original_y_exige_lectura_de_candidata_exacta(tema):
    campo = si.MOMENTOS[0]
    nuevo = tema.columnas[campo] + ' Explica tu elección usando un ejemplo.'
    rs = {'ciencia': dictamen(tema, 'ciencia', {}, decision='corregir', cambios=[{
        'campo': campo, 'antes': tema.columnas[campo], 'despues': nuevo, 'motivo': 'Precisa el producto.'}])}
    ps = dictamen(tema, 'psicopedagogia', rs)
    entrada = si.entrada_etapa(tema, 'psicopedagogia', rs)
    assert entrada['columnas'][campo] == nuevo
    alterada = deepcopy(entrada)
    alterada['columnas'][campo] += ' Modificación posterior.'
    with pytest.raises(ValueError, match='candidata distinta'):
        si.comprobar_dictamen(ps, alterada, 'psicopedagogia', tema.asignatura)
    assert tema.columnas[campo] != nuevo


def test_retencion_no_se_borra_por_mayoria_y_baja_confianza_retiene(tema):
    rs = cadena(tema)
    rs['refutacion'].decision = 'retener'
    # Reconstruye el hash de lectura final tras la objeción; el dictamen final favorable no borra el desacuerdo.
    rs['final'] = dictamen(tema, 'final', rs)
    s = si.secuencia_de(tema, rs)
    assert not s.autoria_asistida and s.motivos_retencion
    rs = cadena(tema)
    rs['final'].confianza = 'baja'
    assert not si.secuencia_de(tema, rs).autoria_asistida


def test_correccion_final_exige_nueva_refutacion(tema):
    rs = cadena(tema)
    entrada = si.entrada_etapa(tema, 'final', rs)
    campo = 'criterio_1'
    nuevo = 'Elige el instrumento y justifica la magnitud que mide.'
    rs['final'] = dictamen(tema, 'final', rs, decision='corregir', cambios=[{
        'campo': campo, 'antes': entrada['columnas'][campo], 'despues': nuevo,
        'motivo': 'Precisa el criterio de elección.'}])
    assert not si.secuencia_de(tema, rs).autoria_asistida
    rs['refutacion_final'] = dictamen(tema, 'refutacion_final', rs)
    s = si.secuencia_de(tema, rs)
    assert s.autoria_asistida and s.criterios_evaluacion[0] == nuevo


@pytest.mark.parametrize('campo,valor', [('autoria_asistida', False), ('producto_evaluable', 'Una invención.'),
                                       ('fuente_sha_columnas', '0' * 64)])
def test_alterar_contenido_o_permiso_no_elude_reconstruccion(tema, campo, valor):
    s = si.secuencia_de(tema, cadena(tema)).model_copy(update={campo: valor})
    with pytest.raises(ValueError, match='no corresponden'):
        si.validar_secuencias([s], {tema.id: tema}, si.configuracion())


def test_validacion_portatil_no_lee_configuracion_productor(tema, monkeypatch):
    cfg = si.configuracion()
    s = si.secuencia_de(tema, cadena(tema))
    def sin_productor(*args):
        raise AssertionError('el consumidor no tiene archivos del productor')
    monkeypatch.setattr(si, 'configuracion', sin_productor)
    si.validar_secuencias([s], {tema.id: tema}, cfg)


def test_no_se_puede_inventar_aula_o_omitir_revision(tema):
    s = si.secuencia_de(tema, cadena(tema))
    with pytest.raises(ValueError, match='aula_habilitada'):
        si.Secuencia.model_validate({**s.model_dump(), 'aula_habilitada': True})
    del s.revisiones['psicopedagogia']
    with pytest.raises(ValueError, match='etapas de revisión'):
        si.validar_secuencias([s], {tema.id: tema}, si.configuracion())


def test_cli_etapa_inexistente_no_inicia_trabajo():
    resultado = CliRunner().invoke(app, ['secuencias', 'preparar', '--etapa', 'inventada'])
    assert resultado.exit_code == 1 and 'etapa desconocida' in resultado.output


def test_refutacion_final_completa_no_oculta_correcciones_sin_revisar(tema, monkeypatch):
    rs = cadena(tema)
    rs['final'].decision = 'corregir'
    monkeypatch.setattr(si, '_temas', lambda: [tema])
    monkeypatch.setattr(si, 'dictamenes', lambda etapa: {} if etapa == 'refutacion_final' else {tema.id: rs[etapa]})
    with pytest.raises(ValueError, match='incompleta'):
        si.validar_dictamenes('refutacion_final', exigir_completo=True)


def test_refutacion_final_no_esta_completa_si_falta_el_cierre_cientifico(tema, monkeypatch):
    rs = cadena(tema)
    monkeypatch.setattr(si, '_temas', lambda: [tema])
    monkeypatch.setattr(si, 'dictamenes', lambda etapa: {} if etapa in ('final', 'refutacion_final')
                        else {tema.id: rs[etapa]})
    with pytest.raises(ValueError, match='etapas anteriores'):
        si.validar_dictamenes('refutacion_final', exigir_completo=True)


def test_citas_demasiado_largas_no_cuentan_como_evidencia(tema):
    d = dictamen(tema, 'ciencia', {})
    e = si.entrada_ciencia(tema)
    e['columnas']['Procedimental'] = ' '.join(['Una', 'palabra'] * 21)
    d.evidencia[0].cita = e['columnas']['Procedimental']
    d.sha_entrada = firma(e)
    with pytest.raises(ValueError, match='cita no encontrada'):
        si.comprobar_dictamen(d, e, 'ciencia', tema.asignatura)


def test_cierre_no_declara_cobertura_del_indicador_avanzado_sin_evidencia(tema):
    rs = cadena(tema)
    rs['final'].evidencia = [e for e in rs['final'].evidencia if e.campo != 'Indicador avanzado']
    with pytest.raises(ValueError, match='indicador avanzado'):
        si.secuencia_de(tema, rs)


def test_serializar_no_reordena_motivos_y_pendientes_de_los_pases(tema):
    rs = {}
    for etapa in si.ETAPAS[:4]:
        rs[etapa] = dictamen(tema, etapa, rs, decision='retener', pendientes=[f'Reparar el alcance de {etapa}.'])
    original = si.secuencia_de(tema, rs)
    # El JSON canónico ordena las claves del diccionario; el orden pedagógico de las listas debe conservarse.
    recibida = si.Secuencia.model_validate(decodificar(canonico(original.model_dump(mode='json'))))
    si.validar_secuencias([recibida], {tema.id: tema}, si.configuracion())
    assert recibida.motivos_retencion == original.motivos_retencion
    assert recibida.pendientes == original.pendientes
