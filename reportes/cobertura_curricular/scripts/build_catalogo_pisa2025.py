"""Catálogo PISA 2025 Ciencias → data/referencia/catalogo_pisa2025.json

Uso:  python scripts/build_catalogo_pisa2025.py            # construye y valida contra el PDF
      python scripts/build_catalogo_pisa2025.py --check    # solo valida, no escribe
Fuente: data/referencia/externos/pisa/PISA2025_Marco_Evaluacion_2026.pdf (OECD 2026, versión final, cap. 2 Science).
- pagina = página del PDF (coincide con la impresa en esta edición).
- titulo_en = frase corta del PDF que identifica el elemento; la validación comprueba que esté en su página.
- Las metas (Tablas 2.3 y 2.4, contextos 1:2:1) son iguales en el borrador de 2023 (Tablas 3 y 4); solo cambia la numeración.
Tipos de elemento:
  contenido    · Box 2.6: 3 sistemas (físicos, vivos, Tierra y espacio) con sus categorías → PISA-F1…, PISA-V1…, PISA-T1…
  procedimental· Box 2.7 → PISA-PR1…PR8
  epistemico   · Box 2.8 (rasgos generales, modelos, datos y evidencia, razonamiento, naturaleza colectiva) → PISA-EP1…
  competencia  · Boxes 2.3–2.5: 3 competencias y sus 15 subcompetencias con los MISMOS códigos de la malla (E1–E6, D1–D4, I1–I5)
  contexto     · Tabla 2.2: personal, local/nacional, global; y 5 áreas de aplicación
  demanda      · Figura 2.2 y p. 50: baja, media, alta (profundidad del conocimiento)
"""
import json, subprocess, sys

PDF = 'data/referencia/externos/pisa/PISA2025_Marco_Evaluacion_2026.pdf'
OUT = 'data/referencia/catalogo_pisa2025.json'

# ---------------------------------------------------------------- metas (Tablas 2.3 y 2.4, p. 53)
# Rango del marco y punto medio normalizado (lo que se usa como meta en el libro).
METAS = {
    'sistema': {'Sistemas físicos': (0.37, 0.37), 'Sistemas vivos': (0.37, 0.37), 'Sistemas de la Tierra y el espacio': (0.26, 0.26)},
    'conocimiento': {'Contenido': (0.38, 0.48), 'Procedimental': (0.27, 0.33), 'Epistémico': (0.24, 0.30)},
    'competencia': {'C1': (0.36, 0.44), 'C2': (0.24, 0.36), 'C3': (0.24, 0.36)},
    'contexto': {'Personal': (0.25, 0.25), 'Local/nacional': (0.50, 0.50), 'Global': (0.25, 0.25)},  # 1:2:1, p. 53
}
# Tabla 2.3: contenido/procedimental/epistémico × sistema (rangos)
TABLA_2_3 = {
    'Contenido': {'Sistemas físicos': (0.15, 0.20), 'Sistemas vivos': (0.15, 0.20), 'Sistemas de la Tierra y el espacio': (0.10, 0.15)},
    'Procedimental': {'Sistemas físicos': (0.10, 0.13), 'Sistemas vivos': (0.10, 0.13), 'Sistemas de la Tierra y el espacio': (0.07, 0.10)},
    'Epistémico': {'Sistemas físicos': (0.08, 0.11), 'Sistemas vivos': (0.08, 0.11), 'Sistemas de la Tierra y el espacio': (0.07, 0.10)},
}

# (codigo, sistema/grupo, paráfrasis, titulo_en, página)
CONTENIDO = [
 ('PISA-F1', 'Sistemas físicos', 'Estructura y propiedades de la materia (modelo de partículas, enlaces, cambios de estado, conductividad térmica y eléctrica)', 'Structure and properties of matter', 38),
 ('PISA-F2', 'Sistemas físicos', 'Cambios químicos de la materia (reacciones químicas, transferencia de energía, ácidos y bases)', 'Chemical changes of matter', 38),
 ('PISA-F3', 'Sistemas físicos', 'Movimiento y fuerzas (velocidad, fricción) y acción a distancia (fuerzas magnéticas, gravitatorias y electrostáticas)', 'Motion and forces', 38),
 ('PISA-F4', 'Sistemas físicos', 'La energía y su transferencia (conservación, disipación, reacciones químicas)', 'Energy and its transfer', 38),
 ('PISA-F5', 'Sistemas físicos', 'Interacciones entre energía y materia (luz y ondas de radio, sonido y ondas sísmicas, absorción de radiación por el CO2)', 'Interactions between energy and matter', 38),
 ('PISA-V1', 'Sistemas vivos', 'El concepto de organismo (animales, plantas y microorganismos como virus y bacterias)', 'The concept of organism', 38),
 ('PISA-V2', 'Sistemas vivos', 'Genes (expresión, herencia, biotecnología) y su interacción con el ambiente', 'Genes', 38),
 ('PISA-V3', 'Sistemas vivos', 'Células: estructura y función, energía, respiración, fotosíntesis, crecimiento', 'Cells (including structure and function', 38),
 ('PISA-V4', 'Sistemas vivos', 'Sistemas de plantas y animales, su salud y mantenimiento (circulación, reproducción, respiración, excreción, nutrición)', 'Plant and animal systems', 38),
 ('PISA-V5', 'Sistemas vivos', 'Evolución biológica (biodiversidad, variación genética, adaptación y selección natural)', 'Biological evolution', 38),
 ('PISA-V6', 'Sistemas vivos', 'Ecosistemas (flujo de materia y energía, cadenas alimentarias, hábitat, perturbaciones como la contaminación)', 'Ecosystems (e.g. matter and energy flow', 38),
 ('PISA-V7', 'Sistemas vivos', 'La biosfera (sostenibilidad del ecosistema global)', 'The biosphere', 38),
 ('PISA-V8', 'Sistemas vivos', 'Interacciones de los seres humanos y su impacto en el ambiente, otras especies y la sostenibilidad', 'Interactions of humans and their impact', 38),
 ('PISA-T1', 'Sistemas de la Tierra y el espacio', 'Estructura de los sistemas terrestres (atmósfera, hidrosfera, geosfera; tectónica de placas, sismología)', "Structures of the Earth’s systems", 38),
 ('PISA-T2', 'Sistemas de la Tierra y el espacio', 'Carácter finito de los recursos minerales, su uso y los efectos ambientales de su explotación', 'The finite nature of mineral resources', 38),
 ('PISA-T3', 'Sistemas de la Tierra y el espacio', 'Energía en los sistemas terrestres (fuentes, calentamiento global, tectónica, ciclos geológicos, ciclo del agua)', 'Energy in the Earth systems', 38),
 ('PISA-T4', 'Sistemas de la Tierra y el espacio', 'Agua: abastecimiento y conservación (agua dulce, acuíferos)', 'Water, supply and conservation', 38),
 ('PISA-T5', 'Sistemas de la Tierra y el espacio', 'Interacciones y cambios entre sistemas terrestres (cambio climático, ciclos geoquímicos, fuerzas tectónicas, acidificación del océano)', 'Interactions and change among Earth systems', 38),
 ('PISA-T6', 'Sistemas de la Tierra y el espacio', 'Historia de la Tierra (fósiles, origen y evolución, erosión y sedimentación)', 'Earth’s history', 38),
 ('PISA-T7', 'Sistemas de la Tierra y el espacio', 'La Tierra en el espacio (fases de la Luna, sistema solar, galaxias)', 'Earth in space', 38),
 ('PISA-T8', 'Sistemas de la Tierra y el espacio', 'Origen del universo y del sistema solar (evolución estelar, formación de planetas, Big Bang)', 'The origin of the Universe', 38),
]
PROCEDIMENTAL = [
 ('PISA-PR1', 'Variables dependientes, independientes y de control', 'The concept of variables', 40),
 ('PISA-PR2', 'Conceptos de medición: cuantitativa y cualitativa, uso de escalas, variables categóricas y continuas', 'Concepts of measurement', 40),
 ('PISA-PR3', 'Formas de estimar y reducir la incertidumbre (repetir mediciones y promediar)', 'Ways of assessing and minimising uncertainty', 40),
 ('PISA-PR4', 'Mecanismos para asegurar la precisión y la exactitud de los datos', 'Mechanisms to ensure the precision', 40),
 ('PISA-PR5', 'Formas de representar datos en tablas, gráficos y diagramas, y su uso adecuado', 'Common ways of abstracting and representing data', 40),
 ('PISA-PR6', 'Estrategia de control de variables en el diseño experimental (o ensayos aleatorizados) para identificar causas', 'The control of variables strategy', 40),
 ('PISA-PR7', 'Diseño adecuado para una pregunta (experimental, de campo, búsqueda de patrones) y papel de los controles', 'Given a scientific question, what might be an appropriate design', 40),
 ('PISA-PR8', 'Procesos de revisión entre pares que hacen confiables las afirmaciones', 'What processes of peer vetting', 40),
]
EPISTEMICO = [  # (codigo, grupo, paráfrasis, titulo_en, página)
 ('PISA-EP1', 'Rasgos de la ciencia', 'Naturaleza de observaciones, hechos, hipótesis, modelos y teorías', 'The nature of scientific observations', 42),
 ('PISA-EP2', 'Rasgos de la ciencia', 'Propósito de la ciencia (explicar y predecir) frente al de la tecnología (soluciones óptimas)', 'The purpose and goals of science', 42),
 ('PISA-EP3', 'Rasgos de la ciencia', 'Valores de la ciencia: publicación revisada por pares, objetividad, eliminar sesgos', 'The values of science', 42),
 ('PISA-EP4', 'Modelos', 'Uso de modelos físicos, conceptuales, de sistemas y matemáticos para comprender el mundo', 'How understanding of the material world is constructed', 42),
 ('PISA-EP5', 'Modelos', 'Distinción entre modelo y realidad', 'The distinction between a model and reality', 42),
 ('PISA-EP6', 'Modelos', 'Cómo los modelos permiten predecir y explicar', 'How models enable predictions and explanations', 42),
 ('PISA-EP7', 'Modelos', 'Cómo las limitaciones de un modelo restringen su uso', 'How the limitations of models', 42),
 ('PISA-EP8', 'Datos y evidencia', 'Cómo los datos, métodos y razonamientos sustentan las afirmaciones científicas', 'How scientific claims are supported by data', 42),
 ('PISA-EP9', 'Datos y evidencia', 'Cómo se genera la evidencia científica (prácticas de los científicos)', 'How scientific evidence is generated', 42),
 ('PISA-EP10', 'Datos y evidencia', 'Cómo el error de medición afecta la confianza en el conocimiento', 'How measurement error affects the degree of confidence', 42),
 ('PISA-EP11', 'Razonamiento científico', 'Formas de indagación empírica: experimento, trabajo de campo, búsqueda de patrones', 'Some of the different forms of empirical enquiry', 42),
 ('PISA-EP12', 'Razonamiento científico', 'Tipos de razonamiento (deducción, abducción, inducción, probabilidad) y su finalidad', 'The types of reasoning', 42),
 ('PISA-EP13', 'Razonamiento científico', 'Dilemas éticos de la práctica científica', 'The ethical dilemmas raised in scientific practice', 42),
 ('PISA-EP14', 'Razonamiento científico', 'Papel y límites del conocimiento científico, junto con otros saberes, ante problemas sociales y tecnológicos', 'The role of scientific knowledge, along with other forms of knowledge', 42),
 ('PISA-EP15', 'Naturaleza colectiva', 'Cómo se financia y apoya la investigación', 'How specific scientific research is funded', 42),
 ('PISA-EP16', 'Naturaleza colectiva', 'Importancia del consenso', 'The importance of consensus in warranting belief', 42),
 ('PISA-EP17', 'Naturaleza colectiva', 'La revisión por pares y la comunidad científica dan confianza a las afirmaciones', 'How peer review helps to establish confidence', 43),
 ('PISA-EP18', 'Naturaleza colectiva', 'Prácticas científicas clave para producir conocimiento compartido y su carácter colaborativo', 'Key scientific practices undertaken by scientists', 43),
 ('PISA-EP19', 'Naturaleza colectiva', 'Límites de la certeza, cómo se expresa y cómo evoluciona', 'The limits to certainty and confidence', 43),
 ('PISA-EP20', 'Naturaleza colectiva', 'Cómo se comunican los hallazgos a la comunidad y al público', 'How scientific findings are communicated', 43),
]
COMPETENCIAS = [  # (código de la malla, competencia, paráfrasis, titulo_en, página)
 ('E1', 'C1', 'Recordar y aplicar el conocimiento científico apropiado', 'Recall and apply appropriate scientific knowledge', 34),
 ('E2', 'C1', 'Usar distintas representaciones y pasar de una a otra', 'Use different forms of representations', 34),
 ('E3', 'C1', 'Hacer y justificar predicciones y soluciones científicas', 'Make and justify appropriate scientific predictions', 34),
 ('E4', 'C1', 'Identificar, construir y evaluar modelos', 'Identify, construct and evaluate models', 34),
 ('E5', 'C1', 'Reconocer y desarrollar hipótesis explicativas', 'Recognise and develop explanatory hypotheses', 34),
 ('E6', 'C1', 'Explicar las implicaciones del conocimiento científico para la sociedad', 'Explain the potential implications of scientific knowledge', 34),
 ('D1', 'C2', 'Identificar la pregunta de un estudio científico', 'Identify the question in a given scientific study', 34),
 ('D2', 'C2', 'Proponer un diseño experimental apropiado', 'Propose an appropriate experimental design', 34),
 ('D3', 'C2', 'Evaluar si un diseño es el más adecuado para la pregunta', 'Evaluate whether an experimental design is best suited', 34),
 ('D4', 'C2', 'Interpretar datos en distintas representaciones y sacar y evaluar conclusiones', 'Interpret data presented in different representations', 34),
 ('I1', 'C3', 'Buscar, evaluar y comunicar el valor de distintas fuentes de información', 'Search, evaluate and communicate the relative merits', 36),
 ('I2', 'C3', 'Distinguir afirmaciones con evidencia sólida, de expertos o no expertos, y opiniones', 'Distinguish among claims based on strong scientific evidence', 36),
 ('I3', 'C3', 'Construir un argumento a partir de datos', 'Construct an argument to support an appropriate scientific conclusion', 36),
 ('I4', 'C3', 'Criticar fallas comunes en argumentos científicos', 'Critique standard flaws in science-related arguments', 36),
 ('I5', 'C3', 'Justificar decisiones con argumentos científicos, individuales o comunitarios', 'Justify decisions using scientific arguments', 36),
]
NOMBRE_COMP = {'C1': ('Explicar fenómenos científicamente', 'Box 2.3. PISA 2025 Science Competency 1', 34),
               'C2': ('Construir y evaluar diseños de indagación e interpretar datos y evidencia críticamente', 'Box 2.4. PISA 2025 Science Competency 2', 34),
               'C3': ('Investigar, evaluar y usar información científica para decidir y actuar', 'Box 2.5. PISA 2025 Science Competency 3', 36)}
AREAS = [  # Tabla 2.2, pp. 32–33
 ('Salud y enfermedad', 'Health & Disease', 32),
 ('Recursos naturales', 'Natural Resources', 32),
 ('Impactos ambientales y cambio climático', 'Environmental Impacts', 33),
 ('Riesgos', 'Hazards', 33),
 ('Avances y desafíos científicos y tecnológicos', 'Contemporary Scientific and', 33),
]
DEMANDA = [('Baja', 'Low (L): Carrying out a one-step procedure', 50, 'Un paso: recordar un dato o concepto, ubicar un dato, clasificar por un criterio'),
           ('Media', 'Medium (M): Use an application', 50, 'Aplicar conocimiento para describir o explicar, dos o más pasos, organizar o interpretar datos simples'),
           ('Alta', 'High (H): Analyse more complex information', 50, 'Analizar información compleja, sintetizar o evaluar evidencia, justificar, planificar una investigación, criticar argumentos')]


def construir():
    cat = []
    for cod, sis, txt, en, p in CONTENIDO:
        cat.append(dict(codigo=cod, tipo='contenido', grupo=sis, meta_grupo=METAS['sistema'][sis][0], texto=txt, titulo_en=en, pagina=p))
    for cod, txt, en, p in PROCEDIMENTAL:
        cat.append(dict(codigo=cod, tipo='procedimental', grupo='Conocimiento procedimental', texto=txt, titulo_en=en, pagina=p))
    for cod, g, txt, en, p in EPISTEMICO:
        cat.append(dict(codigo=cod, tipo='epistemico', grupo=g, texto=txt, titulo_en=en, pagina=p))
    for cod, comp, txt, en, p in COMPETENCIAS:
        cat.append(dict(codigo=cod, tipo='subcompetencia', grupo=comp, competencia=NOMBRE_COMP[comp][0],
                        meta_grupo=METAS['competencia'][comp], texto=txt, titulo_en=en, pagina=p))
    for nom, en, p in AREAS:
        cat.append(dict(codigo='AREA-' + str(AREAS.index((nom, en, p)) + 1), tipo='area_aplicacion', grupo='Áreas de aplicación', texto=nom, titulo_en=en, pagina=p))
    for nom, en, p, desc in DEMANDA:
        cat.append(dict(codigo='DEM-' + nom.upper(), tipo='demanda', grupo='Demanda cognitiva', texto=f'{nom}: {desc}', titulo_en=en, pagina=p))
    return {'fuente': PDF, 'edicion': 'OECD (2026), PISA 2025 Assessment and Analytical Framework, cap. 2 Science',
            'metas': {k: {kk: list(vv) for kk, vv in v.items()} for k, v in METAS.items()},
            'tabla_2_3': {k: {kk: list(vv) for kk, vv in v.items()} for k, v in TABLA_2_3.items()},
            'competencias': {k: {'nombre': v[0], 'pagina': v[2]} for k, v in NOMBRE_COMP.items()},
            'elementos': cat}


# ---------------------------------------------------------------- validación contra el PDF
def pagina(n):
    t = subprocess.run(['pdftotext', '-layout', '-f', str(n), '-l', str(n), PDF, '-'], capture_output=True, text=True).stdout
    return ' '.join(t.replace('’', "'").split())


def validar(c):
    err = []
    cache = {}
    for e in c['elementos']:
        p = e['pagina']
        cache.setdefault(p, pagina(p))
        if e['titulo_en'].replace('’', "'") not in cache[p]:
            err.append(f"{e['codigo']}: «{e['titulo_en']}» no está en la p. {p}")
    for comp, (_, en, p) in NOMBRE_COMP.items():
        if en not in pagina(p):
            err.append(f'{comp}: título no está en la p. {p}')
    t53 = pagina(53)
    for frag in ('Content 15-20% 15-20% 10-15% 38-48%', 'Procedural 10-13% 10-13% 7-10% 27-33%',
                 'Epistemic 8-11% 8-11% 7-10% 24-30%', '37% 37% 26% 100%', '36-44%', 'ratio 1:2:1'):
        if frag not in t53:
            err.append(f'p. 53: falta «{frag}»')
    if ' '.join(pagina(53).split()).count('24-36%') < 2:
        err.append('p. 53: las competencias 2 y 3 deben ser 24-36%')
    # conteos del PDF: viñetas de cada recuadro
    n = {t: sum(e['tipo'] == t for e in c['elementos']) for t in ('contenido', 'procedimental', 'epistemico', 'subcompetencia')}
    if n != {'contenido': 21, 'procedimental': 8, 'epistemico': 20, 'subcompetencia': 15}:
        err.append(f'conteos {n}')
    codigos = [e['codigo'] for e in c['elementos']]
    if len(set(codigos)) != len(codigos):
        err.append('códigos repetidos')
    return err


if __name__ == '__main__':
    cat = construir()
    errores = validar(cat)
    for e in errores:
        print('ERROR', e)
    if errores:
        sys.exit(1)
    if '--check' not in sys.argv:
        json.dump(cat, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    n = {}
    for e in cat['elementos']:
        n[e['tipo']] = n.get(e['tipo'], 0) + 1
    print('OK', n, '' if '--check' in sys.argv else f'→ {OUT}')
