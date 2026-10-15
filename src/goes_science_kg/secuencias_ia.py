"""Autoría V3 con revisión IA independiente por tema; evidencia exacta y ninguna firma humana implícita."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from goes_science_kg.config import cargar, relativa, ruta
from goes_science_kg.motor.archivos import canonico, destino_seguro, escribir, firma, leer, sha
from goes_science_kg.motor.contrato import SHA, Registro, Tema, Texto

MOMENTOS = ('1. Aproximar', '2. Explorar', '3. Explicar', '4. Indagar', '5. Reforzar')
EDITABLES = {*MOMENTOS, 'Evidencia de aprendizaje'}
CRITERIOS = ('criterio_1', 'criterio_2', 'criterio_3')
EDITABLES_FINAL = EDITABLES | {*CRITERIOS, 'consigna_salida', 'alternativa_sin_internet'}
CIENTIFICOS = ('Procedimental', 'Contenido', 'Subcontenidos', 'Indicadores de logro',
              'Evidencia de aprendizaje', *MOMENTOS)
ETAPAS = ('ciencia', 'psicopedagogia', 'refutacion', 'final', 'refutacion_final')
ROLES_CIENCIA = {'biologia': 'experto-biologia', 'fisica': 'experto-fisica', 'quimica': 'experto-quimica',
                'ciencias_tierra_espacio': 'experto-tierra-espacio'}


class Evidencia(Registro):
    campo: Texto
    cita: Texto


class Cambio(Registro):
    campo: Texto
    antes: Texto
    despues: Texto
    motivo: Texto


class Dictamen(Registro):
    tema_id: Texto
    rol: Literal['experto-biologia', 'experto-fisica', 'experto-quimica', 'experto-tierra-espacio',
                 'psicopedagogo', 'refutador']
    decision: Literal['sin_objecion_en_lectura', 'corregir', 'retener']
    confianza: Literal['alta', 'media', 'baja']
    justificacion: Texto
    evidencia: list[Evidencia] = Field(min_length=1)
    cambios: list[Cambio]
    pendientes: list[Texto]
    # El primer pase lee la fila oficial inmutable. Los siguientes enlazan la candidata exacta que recibieron.
    sha_entrada: SHA | None = None
    criterios_evaluacion: list[Texto] | None = None
    consigna_salida: Texto | None = None
    apoyos: list[Texto] | None = None
    alternativa_sin_internet: Texto | None = None
    sesiones_sugeridas: int | None = Field(default=None, ge=1, le=12)
    motivo_tiempo: Texto | None = None

    @model_validator(mode='after')
    def coherente(self):
        if len(self.justificacion.split()) > 70:
            raise ValueError('justificación de más de 70 palabras')
        if self.decision == 'corregir' and not self.cambios:
            raise ValueError('corregir exige cambios concretos')
        if self.decision != 'corregir' and self.cambios:
            raise ValueError('cambios sin decisión corregir')
        if self.rol == 'refutador' and self.cambios:
            raise ValueError('el refutador objeta, no reescribe al panel')
        if len({c.campo for c in self.cambios}) != len(self.cambios):
            raise ValueError('cambios duplicados en un campo')
        return self


class Momento(Registro):
    nombre: Texto
    texto_malla: Texto
    propuesta_ia: Texto
    minutos_planificados: int = Field(ge=1)


class Secuencia(Registro):
    id: Texto
    tema_id: Texto
    grado: int = Field(ge=2, le=11)
    asignatura: Texto
    version: Literal['secuencias-ia-v1'] = 'secuencias-ia-v1'
    fuente_sha_columnas: SHA
    momentos: list[Momento] = Field(min_length=5, max_length=5)
    producto_evaluable: Texto
    criterios_evaluacion: list[Texto] = Field(min_length=3, max_length=3)
    consigna_salida: Texto
    apoyos: list[Texto] = Field(min_length=1)
    alternativa_sin_internet: Texto
    sesiones_sugeridas: int = Field(ge=1, le=12)
    motivo_tiempo: Texto
    minutos_transiciones: int = Field(ge=0)
    duracion_sesion_min: Literal[55] = 55
    tiempo_observado_min: None = None
    distribucion_tiempo: Literal['hipotesis_para_adaptar_cada_sesion'] = 'hipotesis_para_adaptar_cada_sesion'
    presupuesto_demostrado: Literal[False] = False
    revisiones: dict[str, Dictamen]
    entradas_revision: dict[str, SHA]
    columnas_efectivas: dict[str, str]
    estado: Literal['revisado_multiagente_ia', 'retenido_por_panel_ia']
    motivos_retencion: list[Texto]
    pendientes: list[Texto]
    autoria_asistida: bool
    revisado_por: None = None
    aula_habilitada: Literal[False] = False
    competencias: dict[str, str]
    evidencia_competencias: Literal['declaradas_en_malla_no_certificadas_por_etiqueta'] = (
        'declaradas_en_malla_no_certificadas_por_etiqueta')


def configuracion() -> dict:
    return cargar('secuencias_ia')


def _base() -> Path:
    return destino_seguro(ruta(configuracion()['directorio']))


def _temas() -> list[Tema]:
    from goes_science_kg.motor.validacion import cargar_entrega, validar

    p = ruta(configuracion()['entrega_base'])
    validar(p)
    return [t for t in cargar_entrega(p)[1]['temas'] if t.en_alcance_ciencias]


def dictamenes(etapa: str) -> dict[str, Dictamen]:
    if etapa not in ETAPAS:
        raise ValueError('etapa desconocida')
    resultado = {}
    for p in sorted((_base() / 'dictamenes').glob(f'{etapa}_*.json')):
        # refutacion_final no pertenece al pase refutacion.
        if etapa == 'refutacion' and p.name.startswith('refutacion_final_'):
            continue
        for x in leer(p):
            d = Dictamen.model_validate(x)
            if d.tema_id in resultado:
                raise ValueError(f'dictamen repetido en {etapa}: {d.tema_id}')
            resultado[d.tema_id] = d
    return resultado


def _campos_psico(d: Dictamen) -> dict[str, str]:
    if (d.criterios_evaluacion is None or len(d.criterios_evaluacion) != 3 or not d.consigna_salida
            or not d.alternativa_sin_internet or not d.apoyos or not d.sesiones_sugeridas or not d.motivo_tiempo):
        raise ValueError(f'psicopedagogía sin evaluación, adaptación o presupuesto: {d.tema_id}')
    return {**dict(zip(CRITERIOS, d.criterios_evaluacion, strict=True)), 'consigna_salida': d.consigna_salida,
            'alternativa_sin_internet': d.alternativa_sin_internet}


def comprobar_dictamen(d: Dictamen, entrada: dict, etapa: str, asignatura: str) -> dict[str, str]:
    """Verifica citas contra el texto leído y cambios contra valores completos, antes de aplicarlos."""
    rol = ('psicopedagogo' if etapa == 'psicopedagogia' else 'refutador' if etapa.startswith('refutacion')
           else ROLES_CIENCIA[asignatura])
    if d.tema_id != entrada['id'] or d.rol != rol:
        raise ValueError(f'rol o identidad ajenos al lote: {d.tema_id}')
    if etapa != 'ciencia' and d.sha_entrada != firma(entrada):
        raise ValueError(f'revisión de una candidata distinta: {d.tema_id}/{etapa}')
    if etapa == 'ciencia' and d.sha_entrada not in (None, firma(entrada)):
        raise ValueError(f'SHA de lectura científica distinto: {d.tema_id}')
    columnas = dict(entrada['columnas'])
    for e in d.evidencia:
        if (len(e.cita) < 20 or len(e.cita.split()) > 30 or e.campo not in columnas
                or e.cita not in columnas[e.campo]):
            raise ValueError(f'cita no encontrada en el campo declarado: {d.tema_id}/{e.campo}')
    if (etapa == 'final' and len(columnas.get('Indicador avanzado', '')) >= 20
            and not any(e.campo == 'Indicador avanzado' for e in d.evidencia)):
        raise ValueError(f'cierre sin evidencia del indicador avanzado de unidad: {d.tema_id}')
    permitidos = EDITABLES_FINAL if etapa == 'final' else EDITABLES
    for c in d.cambios:
        if c.campo not in permitidos or columnas.get(c.campo) != c.antes or c.antes == c.despues:
            raise ValueError(f'cambio no permitido, vacío u obsoleto: {d.tema_id}/{c.campo}')
        columnas[c.campo] = c.despues
    if etapa == 'psicopedagogia':
        columnas.update(_campos_psico(d))
    elif any(getattr(d, k) is not None for k in ('criterios_evaluacion', 'consigna_salida', 'apoyos',
                                               'alternativa_sin_internet', 'sesiones_sugeridas', 'motivo_tiempo')):
        raise ValueError(f'campos de adaptación fuera de la revisión psicopedagógica: {d.tema_id}')
    return columnas


def entrada_ciencia(t: Tema) -> dict:
    return {'id': t.id, 'grado': t.grado, 'fuente': t.fuente.model_dump(), 'sha_columnas': firma(t.columnas),
            'columnas': {k: t.columnas.get(k, '') for k in CIENTIFICOS}}


def entrada_etapa(t: Tema, etapa: str, revisiones: dict[str, Dictamen]) -> dict:
    e = entrada_ciencia(t)
    if etapa == 'ciencia':
        return e
    c = comprobar_dictamen(revisiones['ciencia'], e, 'ciencia', t.asignatura)
    # Psicopedagogía también ve recursos digitales y etiquetas para revisar acceso/carga, sin avalarlos por nombre.
    e = {'id': t.id, 'grado': t.grado, 'fuente': t.fuente.model_dump(), 'sha_columnas': firma(t.columnas),
         'columnas': {**t.columnas, **c}, 'revisiones': {'ciencia': revisiones['ciencia'].model_dump(mode='json')}}
    if etapa == 'psicopedagogia':
        return e
    c = comprobar_dictamen(revisiones['psicopedagogia'], e, 'psicopedagogia', t.asignatura)
    e = {**e, 'columnas': c,
         'revisiones': {**e['revisiones'], 'psicopedagogia': revisiones['psicopedagogia'].model_dump(mode='json')}}
    if etapa == 'refutacion':
        return e
    comprobar_dictamen(revisiones['refutacion'], e, 'refutacion', t.asignatura)
    e = {**e, 'revisiones': {**e['revisiones'], 'refutacion': revisiones['refutacion'].model_dump(mode='json')}}
    if etapa == 'final':
        return e
    c = comprobar_dictamen(revisiones['final'], e, 'final', t.asignatura)
    return {**e, 'columnas': c,
            'revisiones': {**e['revisiones'], 'final': revisiones['final'].model_dump(mode='json')}}


def preparar(etapa: str) -> dict:
    if etapa not in ETAPAS:
        raise ValueError('etapa desconocida')
    cfg = configuracion()
    temas = _temas()
    anteriores = {e: dictamenes(e) for e in ETAPAS[:ETAPAS.index(etapa)]}
    lotes = _base() / 'lotes'
    lotes.mkdir(parents=True, exist_ok=True)
    por_asignatura = etapa in ('ciencia', 'final', 'refutacion_final')
    grupos = cfg['roles_ciencia'] if por_asignatura else cfg['particiones']
    total = 0
    for grupo in grupos:
        ts = [t for t in temas if (t.asignatura == grupo if por_asignatura
                                  else t.grado in cfg['particiones'][grupo])]
        candidatos = []
        if any(t.id not in ds for t in ts for ds in anteriores.values()):
            continue  # Un grupo se prepara completo: así la llegada de dictámenes no desplaza lotes ya revisados.
        for t in sorted(ts, key=lambda t: t.orden):
            rs = {e: ds[t.id] for e, ds in anteriores.items() if t.id in ds}
            if etapa == 'refutacion_final' and rs['final'].decision != 'corregir':
                continue
            candidatos.append(entrada_etapa(t, etapa, rs))
        archivos = []
        for inicio in range(0, len(candidatos), cfg['tamano_lote']):
            p = lotes / f'lote_{etapa}_{grupo}_{inicio // cfg["tamano_lote"] + 1:02}.json'
            rs = candidatos[inicio:inicio + cfg['tamano_lote']]
            if p.exists() and leer(p) != rs:
                raise ValueError(f'lote existente distinto; usar una nueva serie: {p}')
            escribir(p, rs)
            archivos.append({'archivo': relativa(p), 'sha256': sha(p), 'temas': len(rs)})
        escribir(lotes / f'indice_{etapa}_{grupo}.json', {'etapa': etapa, 'grupo': grupo,
                                                        'temas': len(candidatos), 'archivos': archivos})
        total += len(candidatos)
    return {'etapa': etapa, 'temas_preparados': total}


def validar_dictamenes(etapa: str, exigir_completo: bool = False) -> dict:
    temas = {t.id: t for t in _temas()}
    ds = dictamenes(etapa)
    anteriores = {e: dictamenes(e) for e in ETAPAS[:ETAPAS.index(etapa)]}
    if exigir_completo and any(set(registros) != set(temas) for registros in anteriores.values()):
        raise ValueError(f'revisión incompleta en etapas anteriores a {etapa}')
    if not set(ds) <= temas.keys():
        raise ValueError('dictamen de tema fuera de alcance o inexistente')
    for tid, d in ds.items():
        rs = {e: datos[tid] for e, datos in anteriores.items() if tid in datos}
        if len(rs) != len(anteriores):
            raise ValueError(f'revisión sin etapas anteriores: {tid}/{etapa}')
        entrada = entrada_etapa(temas[tid], etapa, rs)
        comprobar_dictamen(d, entrada, etapa, temas[tid].asignatura)
    esperado = ({tid for tid, d in anteriores['final'].items() if d.decision == 'corregir'}
                if etapa == 'refutacion_final' else set(temas))
    if exigir_completo and set(ds) != esperado:
        raise ValueError(f'revisión incompleta en {etapa}: {len(ds)} de {len(esperado)}')
    return {'etapa': etapa, 'dictamenes': len(ds), 'decisiones': dict(Counter(d.decision for d in ds.values()))}


def retenciones(revisiones: dict[str, Dictamen]) -> list[str]:
    motivos = []
    for etapa in ETAPAS:
        if etapa not in revisiones:
            continue
        d = revisiones[etapa]
        # Un dictamen posterior no convierte un desacuerdo previo en consenso por mayoría.
        if d.decision == 'retener' or d.confianza == 'baja':
            motivos.append(f'{etapa}: {d.decision}, confianza {d.confianza}')
    if revisiones['final'].decision == 'corregir' and 'refutacion_final' not in revisiones:
        motivos.append('correccion_final_sin_nueva_refutacion')
    return motivos


def secuencia_de(t: Tema, rs: dict[str, Dictamen], reglas: dict | None = None) -> Secuencia:
    cfg = reglas if reglas is not None else configuracion()
    entrada = entrada_etapa(t, 'final', rs)
    finales = comprobar_dictamen(rs['final'], entrada, 'final', t.asignatura)
    entradas = {e: firma(entrada_etapa(t, e, rs)) for e in ETAPAS[:4]}
    if 'refutacion_final' in rs:
        e = entrada_etapa(t, 'refutacion_final', rs)
        comprobar_dictamen(rs['refutacion_final'], e, 'refutacion_final', t.asignatura)
        entradas['refutacion_final'] = firma(e)
    ps = rs['psicopedagogia']
    motivos = retenciones(rs)
    return Secuencia(id='SEC:' + t.id.removeprefix('TEMA:'), tema_id=t.id, grado=t.grado, asignatura=t.asignatura,
                     fuente_sha_columnas=firma(t.columnas),
                     momentos=[Momento(nombre=m, texto_malla=t.columnas[m], propuesta_ia=finales[m],
                                       minutos_planificados=n) for m, n in zip(MOMENTOS, cfg['minutos_momentos'],
                                                                             strict=True)],
                     producto_evaluable=finales['Evidencia de aprendizaje'],
                     criterios_evaluacion=[finales[c] for c in CRITERIOS], consigna_salida=finales['consigna_salida'],
                     apoyos=ps.apoyos, alternativa_sin_internet=finales['alternativa_sin_internet'],
                     sesiones_sugeridas=ps.sesiones_sugeridas, motivo_tiempo=ps.motivo_tiempo,
                     minutos_transiciones=cfg['minutos_transiciones'], revisiones=rs, entradas_revision=entradas,
                     columnas_efectivas=finales,
                     estado='retenido_por_panel_ia' if motivos else 'revisado_multiagente_ia',
                     motivos_retencion=motivos, autoria_asistida=not motivos,
                     pendientes=list(dict.fromkeys(p for e in ETAPAS if e in rs for p in rs[e].pendientes)),
                     competencias={k: v for k, v in t.columnas.items() if 'Competencia' in k or 'Habilidad' in k})


def validar_secuencias(secuencias: list[Secuencia], temas: dict[str, Tema], reglas: dict) -> None:
    if (reglas.get('version') != 'secuencias-ia-v1' or tuple(reglas.get('momentos', [])) != MOMENTOS
            or reglas.get('roles_ciencia') != ROLES_CIENCIA or reglas.get('duracion_sesion') != 55):
        raise ValueError('reglas de secuencias incompatibles con el contrato')
    esperados = {t.id for t in temas.values() if t.en_alcance_ciencias}
    if len(secuencias) != len(esperados) or {s.tema_id for s in secuencias} != esperados:
        raise ValueError('secuencias no cubren exactamente los temas de Ciencias')
    for s in secuencias:
        t = temas[s.tema_id]
        if not set(ETAPAS[:4]) <= s.revisiones.keys() or not set(s.revisiones) <= set(ETAPAS):
            raise ValueError(f'etapas de revisión ausentes o ajenas: {s.id}')
        # No lee estado del productor: reconstruye la candidata exclusivamente con esta entrega y sus dictámenes.
        reconstruida = secuencia_de(t, s.revisiones, reglas)
        if s != reconstruida:
            raise ValueError(f'secuencia, permisos o evidencia no corresponden a sus revisiones: {s.id}')
        if [m.nombre for m in s.momentos] != list(MOMENTOS):
            raise ValueError('secuencia con momentos desordenados')
        if sum(m.minutos_planificados for m in s.momentos) + s.minutos_transiciones != 55:
            raise ValueError('presupuesto orientativo distinto de 55 minutos')


def compilar(temas: list[Tema]) -> tuple[list[Secuencia], dict[str, str]]:
    ds = {e: dictamenes(e) for e in ETAPAS}
    esperado = {t.id for t in temas if t.en_alcance_ciencias}
    for e in ETAPAS[:4]:
        if set(ds[e]) != esperado:
            raise ValueError(f'cobertura de {e} incompleta: {len(ds[e])}/{len(esperado)}')
    if not set(ds['refutacion_final']) <= esperado:
        raise ValueError('refutación final con tema ajeno')
    resultado = [secuencia_de(t, {e: datos[t.id] for e, datos in ds.items() if t.id in datos})
                 for t in temas if t.en_alcance_ciencias]
    validar_secuencias(resultado, {t.id: t for t in temas}, configuracion())
    insumos = {relativa(p): sha(p) for p in sorted((_base() / 'dictamenes').glob('*.json'))}
    insumos['config/secuencias_ia.yaml'] = sha(ruta('config/secuencias_ia.yaml'))
    return sorted(resultado, key=lambda s: s.id), insumos


def construir() -> dict:
    temas = _temas()
    resultado, insumos = compilar(temas)
    p = _base() / 'secuencias.jsonl'
    p.write_text(''.join(canonico(s.model_dump(mode='json')) + '\n' for s in resultado), encoding='utf-8')
    informe = {'version': configuracion()['version'], 'temas': len(resultado),
               'por_grado': dict(sorted(Counter(s.grado for s in resultado).items())),
               'por_asignatura': dict(Counter(s.asignatura for s in resultado)),
               'estados': dict(Counter(s.estado for s in resultado)), 'insumos': insumos,
               'sha_secuencias': sha(p), 'aula_habilitada': False, 'tiempo_observado': False}
    escribir(_base() / 'resumen.json', informe)
    return informe
