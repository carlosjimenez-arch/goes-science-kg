"""Equivalencias TIMSS 2023 → 2027 (Ciencias 4.° y 8.°) → data/referencia/equivalencias_timss_2023_2027.csv

Uso:  python scripts/build_equivalencias_timss.py
Fuentes: TIMSS2023_Marco_Ciencias.pdf (cap. 2; página impresa = página PDF + 18) y
         TIMSS2027_Marcos_Evaluacion.pdf (cap. 2; página impresa = página PDF + 2).
Cada objetivo del catálogo 2023 se relaciona con el/los objetivos 2027 que reciben su contenido
(el primero listado es el destino principal). El TIPO no se asigna a mano: se deriva de las relaciones.
- igual:           el objetivo 2023 va a UN objetivo 2027 que no recibe nada más.
- dividido:        el objetivo 2023 se reparte entre VARIOS objetivos 2027.
- fusionado:       el objetivo 2023 va a UN objetivo 2027 que también recibe otros objetivos 2023.
- sin_equivalente: el contenido 2023 ya no está en el marco 2027 del mismo grado.
- nuevo_2027:      objetivo 2027 que no recibe ningún objetivo 2023 (fila con codigo_2023 vacío).
Solo se registra una relación cuando se mueve una parte sustantiva (un sub-ítem o más), no un ejemplo.
"""
import csv, json

CAT23 = 'data/referencia/catalogo_timss.json'
CAT27 = 'data/referencia/catalogo_timss2027.json'
OUT = 'data/referencia/equivalencias_timss_2023_2027.csv'

# codigo_2023: (página impresa 2023, [destinos 2027, el primero = principal], nota)
REL = {
 # ---------------- 4.° Ciencias de la vida → Biología
 'T4-V1.1': (23, ['T4_27-B1.1'], 'Mismo contenido; «lo que necesitan para vivir» pasa a ser ambiental.'),
 'T4-V1.2': (23, ['T4_27-B1.2'], 'Mismo contenido; deja de citar plantas con flor y vertebrados/invertebrados.'),
 'T4-V1.3': (23, ['T4_27-B1.3'], 'Mismo contenido (estructura-función en animales y plantas).'),
 'T4-V2.1': (23, ['T4_27-B2.1'], 'Mismo contenido; ciclo de la planta agrega polinización y fruto.'),
 'T4-V2.2': (23, ['T4_27-B2.2'], 'Mismo contenido (herencia y estrategias reproductivas).'),
 'T4-V3.1': (23, ['T4_27-B3.1'], 'Mismo contenido; el área se renombra «Diversidad y adaptación».'),
 'T4-V3.2': (24, ['T4_27-B1.4'], 'Respuestas de animales y cuerpo humano pasan al área I; se elimina la respuesta de las plantas.'),
 'T4-V3.3': (24, ['T4_27-B4.3'], 'Impacto humano pasa al área Ecosistemas; se separa en contaminación y conducta humana.'),
 'T4-V4.1': (24, ['T4_27-B4.1'], 'Mismo contenido; lista cerrada de ecosistemas (bosque, selva, desierto, sabana…).'),
 'T4-V4.2': (24, ['T4_27-B4.2', 'T4_27-B1.4'], 'Cadena alimentaria y depredador-presa siguen en B4.2; «plantas fabrican su alimento, animales comen» pasa a B1.4.'),
 'T4-V4.3': (24, ['T4_27-B4.2'], 'Competencia se integra a «Relaciones en los ecosistemas».'),
 'T4-V5.1': (25, ['T4_27-B5.2'], 'Mismo contenido; agrega salud mental.'),
 'T4-V5.2': (25, ['T4_27-B5.1'], 'Mismo contenido (contagio y prevención).'),
 # ---------------- 4.° Ciencias físicas
 'T4-F1.1': (25, ['T4_27-P1.1'], 'Estados de la materia; en 2027 el mismo objetivo incluye los cambios de estado.'),
 'T4-F1.2': (25, ['T4_27-P1.2', 'T4_27-P1.3'], 'Propiedades y metales siguen en P1.2; mezclas y su separación pasan a P1.3.'),
 'T4-F1.3': (26, ['T4_27-P4.2'], 'Imanes pasan de «materia» a la nueva área Electricidad y magnetismo.'),
 'T4-F1.4': (26, ['T4_27-P1.3', 'T4_27-P1.1'], 'Cambios físicos van a P1.3; cambios de estado por calor/frío van a P1.1.'),
 'T4-F1.5': (26, ['T4_27-P1.3'], 'Cambios químicos y rapidez de disolución se reúnen en P1.3 con los cambios físicos.'),
 'T4-F2.1': (26, ['T4_27-P2.1', 'T4_27-E3.1'], 'Usos de la energía siguen en P2.1; las FUENTES (sol, agua, viento, combustibles) pasan a recursos de la Tierra (E3.1).'),
 'T4-F2.2': (26, ['T4_27-P3.1', 'T4_27-P3.2'], 'Nueva área Luz y sonido: la luz (P3.1) y el sonido (P3.2) son objetivos separados.'),
 'T4-F2.3': (26, ['T4_27-P2.2'], 'Mismo contenido (calentamiento y enfriamiento por contacto).'),
 'T4-F2.4': (26, ['T4_27-P4.1'], 'Pasa a la nueva área Electricidad y magnetismo; agrega identificar diagramas de circuitos.'),
 'T4-F3.1': (27, ['T4_27-P5.1'], 'Mismo contenido; agrega la resistencia del aire.'),
 'T4-F3.2': (27, ['T4_27-P5.2'], 'Mismo contenido (máquinas simples).'),
 # ---------------- 4.° Ciencias de la Tierra
 'T4-T1.1': (27, ['T4_27-E1.1'], 'Mismo contenido; pasa a ser ambiental.'),
 'T4-T1.2': (27, ['T4_27-E3.1'], 'Recursos pasan a un área propia (III); en 2027 recibe también las fuentes de energía.'),
 'T4-T1.3': (28, ['T4_27-E1.2'], 'Mismo contenido (paisaje y fósiles).'),
 'T4-T2.1': (28, [], 'Se elimina «aplicar cambios de estado del agua al tiempo atmosférico». Lo más cercano: T4_27-P1.1 (cambios de estado del agua).'),
 'T4-T2.2': (28, ['T4_27-E2.1'], 'Variación del tiempo por día y lugar; el área se renombra «La atmósfera terrestre».'),
 'T4-T2.3': (28, ['T4_27-E2.1'], 'Estaciones y calentamiento global se reúnen con la variación del tiempo en E2.1.'),
 'T4-T3.1': (28, ['T4_27-E4.1'], 'Mismo contenido (sistema solar y Luna).'),
 'T4-T3.2': (28, ['T4_27-E4.2'], 'Día y noche se mantiene; en 4.° se elimina explicar las estaciones por la inclinación del eje (queda en 8.°, T8_27-E4.1).'),
 # ---------------- 8.° Biología
 'T8-B1.1': (30, ['T8_27-B1.1'], 'Mismo contenido; agrega bacterias.'),
 'T8-B1.2': (30, ['T8_27-B1.2'], 'Mismo contenido (sistemas de órganos).'),
 'T8-B1.3': (30, ['T8_27-B1.3'], 'Homeostasis; en 2027 el mismo objetivo incluye fotosíntesis y respiración.'),
 'T8-B2.1': (30, ['T8_27-B2.1'], 'Mismo contenido; la vacuola también distingue la célula vegetal.'),
 'T8-B2.2': (31, ['T8_27-B1.3'], 'Fotosíntesis y respiración celular pasan de «Células» a «Procesos vitales» y son ambientales.'),
 'T8-B3.1': (31, [], 'Se elimina «ciclos de vida y patrones de desarrollo» en 8.° (en 2027 solo está en 4.°, T4_27-B2.1).'),
 'T8-B3.2': (31, ['T8_27-B3.1'], 'Mismo contenido (reproducción sexual, ADN, rasgos heredados).'),
 'T8-B4.1': (31, ['T8_27-B4.1'], 'Mismo contenido; los dos sub-ítems 2023 se unen en uno.'),
 'T8-B4.2': (31, ['T8_27-B4.2'], 'Mismo contenido (fósiles y ancestro común).'),
 'T8-B5.1': (31, ['T8_27-B5.2', 'T8_27-B5.4'], 'Flujo de energía y pirámides quedan en B5.2; productores/consumidores/descomponedores y redes tróficas pasan a B5.4.'),
 'T8-B5.2': (32, ['T8_27-B5.3'], 'Mismo contenido (ciclos del agua, oxígeno y carbono).'),
 'T8-B5.3': (32, ['T8_27-B5.4'], 'Competencia, depredación y simbiosis se reúnen con redes tróficas en B5.4.'),
 'T8-B5.4': (32, ['T8_27-B5.5'], 'Mismo contenido (factores limitantes y predicción).'),
 'T8-B5.5': (32, ['T8_27-B5.6'], 'Mismo contenido (impacto humano positivo y negativo).'),
 'T8-B6.1': (32, ['T8_27-B6.1'], 'Mismo contenido; agrega explícitamente el papel de las vacunas.'),
 'T8-B6.2': (33, ['T8_27-B6.2'], 'Mismo contenido; agrega salud mental.'),
 # ---------------- 8.° Química
 'T8-Q1.1': (33, ['T8_27-C1.1'], 'Átomos y moléculas; en 2027 el mismo objetivo incluye el enlace químico.'),
 'T8-Q1.2': (33, ['T8_27-C1.2'], 'Mismo contenido (elementos, compuestos, mezclas).'),
 'T8-Q1.3': (33, ['T8_27-C1.3'], 'Mismo contenido (tabla periódica).'),
 'T8-Q2.1': (34, ['T8_27-C2.1'], 'Propiedades físicas vs químicas y usos se reúnen con la clasificación en C2.1.'),
 'T8-Q2.2': (34, ['T8_27-C2.1'], 'Clasificar por propiedades se reúne en C2.1.'),
 'T8-Q2.3': (34, ['T8_27-C2.2'], 'Mismo contenido (mezclas y disoluciones).'),
 'T8-Q2.4': (34, ['T8_27-C2.3'], 'Mismo contenido; el pH pasa a un sub-ítem con neutralización e indicadores.'),
 'T8-Q3.1': (34, ['T8_27-C3.1'], 'Mismo contenido; el área se renombra «Reacciones químicas».'),
 'T8-Q3.2': (35, ['T8_27-C3.2'], 'Mismo contenido (conservación, energía, rapidez).'),
 'T8-Q3.3': (35, ['T8_27-C1.1'], 'El enlace químico pasa del área de cambio químico a «Composición de la materia».'),
 # ---------------- 8.° Física
 'T8-F1.1': (36, ['T8_27-P1.1'], 'Mismo contenido (partículas y propiedades).'),
 'T8-F1.2': (36, ['T8_27-P1.2'], 'Cambios de estado; en 2027 el mismo objetivo incluye la temperatura constante en el cambio de fase.'),
 'T8-F2.1': (36, ['T8_27-P2.1'], 'Mismo contenido (formas, transformación y conservación).'),
 'T8-F2.2': (36, ['T8_27-P2.2', 'T8_27-P1.2'], 'Transferencia y conductividad quedan en P2.2; temperatura constante en cambios de fase pasa a P1.2.'),
 'T8-F3.1': (36, ['T8_27-P3.1'], 'Mismo contenido (propiedades de la luz).'),
 'T8-F3.2': (37, ['T8_27-P3.2'], 'Mismo contenido (propiedades del sonido).'),
 'T8-F4.1': (37, ['T8_27-P4.1'], 'Mismo contenido; agrega distinguir circuitos en serie y en paralelo.'),
 'T8-F4.2': (37, ['T8_27-P4.2'], 'Mismo contenido (imanes y electroimanes).'),
 'T8-F5.1': (37, ['T8_27-P5.1'], 'Mismo contenido (rapidez y aceleración).'),
 'T8-F5.2': (37, ['T8_27-P5.2'], 'Mismo contenido; se elimina la gravedad en distintos planetas.'),
 'T8-F5.3': (37, ['T8_27-P5.3'], 'Mismo contenido; agrega resistencia del aire.'),
 # ---------------- 8.° Ciencias de la Tierra
 'T8-T1.1': (38, ['T8_27-E1.1'], 'Capas y agua; en 2027 el mismo objetivo incluye desalinización y potabilización.'),
 'T8-T1.2': (38, ['T8_27-E2.1'], 'Pasa a la nueva área Atmósfera; se elimina la relación con procesos vitales.'),
 'T8-T2.1': (39, ['T8_27-E1.2'], 'Mismo contenido; agrega el impacto de asteroides.'),
 'T8-T2.2': (39, ['T8_27-E2.2'], 'Pasa a la nueva área Atmósfera; agrega formación de nubes por enfriamiento del aire.'),
 'T8-T2.3': (39, ['T8_27-E2.3', 'T8_27-E2.4'], 'Tiempo vs clima queda en E2.3; evidencias del cambio climático pasan a E2.4 (objetivo propio, con CAUSAS nuevas).'),
 'T8-T3.1': (39, ['T8_27-E3.2', 'T8_27-E3.1'], 'Renovables y conservación van a E3.2; fuentes de energía a E3.1 (objetivo propio).'),
 'T8-T3.2': (39, ['T8_27-E3.2', 'T8_27-E1.1'], 'Uso del suelo va a E3.2; métodos para obtener agua dulce pasan a E1.1.'),
 'T8-T4.1': (40, ['T8_27-E4.1'], 'Mismo contenido; agrega efectos de la rotación y quita constelaciones.'),
 'T8-T4.2': (40, ['T8_27-E4.2'], 'Mismo contenido; se quitan las otras estrellas.'),
}

# Objetivos 2027 sin ningún objetivo 2023 que los alimente: por qué importan para la malla
NUEVOS = {
 'T4_27-B6.1': 'Área nueva Investigaciones biológicas: prueba justa, observación vs inferencia, uso de lupa.',
 'T4_27-P6.1': 'Área nueva Investigaciones en ciencias físicas: preguntas comprobables, mediciones repetidas, balanza, cronómetro.',
 'T4_27-E5.1': 'Área nueva Investigaciones en ciencias de la Tierra: termómetro, brújula, pluviómetro.',
 'T8_27-B5.1': 'Contenido nuevo: comparar ecosistemas naturales, rurales y urbanos (ambiental).',
 'T8_27-B7.1': 'Área nueva Investigaciones biológicas: pregunta investigable, variables control/tratamiento, microscopio.',
 'T8_27-C4.1': 'Área nueva Investigaciones químicas: preguntas comprobables, una variable a la vez, equipo y seguridad.',
 'T8_27-P6.1': 'Área nueva Investigaciones en física: preguntas contestables, repetir mediciones, amperímetro, dinamómetro.',
 'T8_27-E5.1': 'Área nueva Investigaciones en ciencias de la Tierra: telescopio, brújula.',
}

# Contenido NUEVO dentro de objetivos 2027 que sí tienen equivalente: posibles vacíos parciales
CONTENIDO_NUEVO = {
 'T4_27-P3.1': 'Área nueva Luz y sonido (antes dentro de Energía); el contenido existía.',
 'T4_27-P3.2': 'Área nueva Luz y sonido (antes dentro de Energía); el contenido existía.',
 'T4_27-P4.1': 'Agrega identificar diagramas de circuitos completos.',
 'T4_27-B5.2': 'Agrega salud mental.',
 'T8_27-E2.2': 'Agrega formación de nubes y lluvia por enfriamiento del aire que asciende.',
 'T8_27-E2.4': 'Objetivo propio de cambio climático; agrega CAUSAS (gases de efecto invernadero, volcanes).',
 'T8_27-P4.1': 'Agrega distinguir circuitos en serie y en paralelo.',
 'T8_27-B6.1': 'Agrega cómo las vacunas entrenan al sistema inmunitario.',
 'T8_27-E4.1': 'Agrega efectos de la rotación (día, noche, sombras) en 8.°.',
}


def main():
    c23 = {c['codigo']: c for c in json.load(open(CAT23)) if c['marco'] in ('T4', 'T8')}
    c27 = {c['codigo']: c for c in json.load(open(CAT27))}
    assert set(REL) == set(c23), f'faltan/sobran códigos 2023: {set(c23) ^ set(REL)}'
    destinos = [d for _, ds, _ in REL.values() for d in ds]
    assert set(destinos) <= set(c27), f'códigos 2027 inexistentes: {set(destinos) - set(c27)}'
    for k, (_, ds, _) in REL.items():
        assert all(d.startswith(k[:2] + '_27') for d in ds), f'{k} cruza de grado'
    recibe = {}
    for k, (_, ds, _) in REL.items():
        for d in ds:
            recibe.setdefault(d, []).append(k)
    sin_origen = set(c27) - set(recibe)
    assert sin_origen == set(NUEVOS), f'nuevos mal declarados: {sin_origen ^ set(NUEVOS)}'
    assert set(CONTENIDO_NUEVO) <= set(recibe)

    filas = []
    for k, (pag, ds, nota) in REL.items():
        if not ds:
            tipo = 'sin_equivalente'
        elif len(ds) > 1:
            tipo = 'dividido'
        elif len(recibe[ds[0]]) > 1:
            tipo = 'fusionado'
        else:
            tipo = 'igual'
        for i, d in enumerate(ds or ['']):
            otros = [o for o in recibe.get(d, []) if o != k]
            filas.append({
                'codigo_2023': k, 'codigo_2027': d, 'tipo': tipo,
                'principal': 'sí' if i == 0 and d else ('no' if d else ''),
                'nota': nota + (f' Recibe también: {", ".join(otros)}.' if otros and tipo == 'fusionado' else ''),
                'objetivo_2023': c23[k]['objetivo'], 'objetivo_2027': c27[d]['objetivo'] if d else '',
                'area_2027': c27[d]['area'] if d else '',
                'pagina_2023': pag, 'pagina_2027': c27[d]['pagina_fuente'] if d else '',
                'novedad_2027': CONTENIDO_NUEVO.get(d, ''),
            })
    for d, nota in NUEVOS.items():
        filas.append({'codigo_2023': '', 'codigo_2027': d, 'tipo': 'nuevo_2027', 'principal': '',
                      'nota': nota, 'objetivo_2023': '', 'objetivo_2027': c27[d]['objetivo'],
                      'area_2027': c27[d]['area'], 'pagina_2023': '', 'pagina_2027': c27[d]['pagina_fuente'],
                      'novedad_2027': 'objetivo nuevo'})
    with open(OUT, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

    from collections import Counter
    por_obj = {}
    for r in filas:
        por_obj.setdefault((r['codigo_2023'] or r['codigo_2027']), r['tipo'])
    print(f'Escrito {OUT}: {len(filas)} filas')
    for marco in ('T4', 'T8'):
        cnt = Counter(t for k, t in por_obj.items() if k.startswith(marco))
        print(f'  {marco}: ' + ', '.join(f'{t}={n}' for t, n in sorted(cnt.items())))


if __name__ == '__main__':
    main()
