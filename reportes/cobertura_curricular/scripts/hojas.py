"""Nombres visibles de las pestañas del libro TIMSS 2027 + PISA 2025 (una sola fuente para el libro, el explorador y las pruebas).

El script construye las hojas con nombres internos cortos y al final las renombra con estos (fórmulas y textos incluidos).
El prefijo dice qué marco mide cada hoja: «TIMSS -» = TIMSS 2027 (2.°–8.°) o Advanced (Física); «PISA -» = PISA 2025 (7.°–9.°);
sin prefijo = hoja que junta los dos marcos (lo dice su recuadro); «Datos -» = trazabilidad.
"""
NOMBRES = {
    'Leeme': 'Inicio',
    'Resumen': 'Resumen TIMSS y PISA',
    'Apego_escenarios': 'Apego TIMSS y PISA',
    'Presupuesto': 'Presupuesto de temas',
    'Balance_ciclo': 'TIMSS - Balance por ciclo',
    'Balance_grado': 'TIMSS - Balance por grado',
    'Cobertura_objetivos': 'TIMSS - Semáforo de objetivos',
    'PISA_contenido': 'PISA - Contenidos',
    'PISA_competencias': 'PISA - Competencias',
    'PISA_conocimiento': 'PISA - Tipos de conocimiento',
    'PISA_contextos': 'PISA - Contextos',
    'Ambiental': 'TIMSS - Medio ambiente',
    'Investigaciones': 'TIMSS - Investigación',
    'Cognitivo_grado': 'TIMSS - Conocer-Aplicar-Razonar',
    'Comparacion_paises': 'TIMSS - Otros países',
    'Temas': 'Datos - Temas',
    'Catalogo_TIMSS': 'Datos - Catálogo TIMSS',
    'Catalogo_PISA': 'Datos - Catálogo PISA',
    'Paises_objetivos': 'Datos - Objetivos de países',
    'Referencia_2023': 'Datos - TIMSS 2023',
    'Fuentes': 'Fuentes',
}
# Sin «·»: Numbers no resuelve referencias a hojas con ese carácter (probado). Guion, espacios y tildes sí funcionan.
assert all(len(v) <= 31 and not set(v) & set(':\\/?*[]·') for v in NOMBRES.values())
