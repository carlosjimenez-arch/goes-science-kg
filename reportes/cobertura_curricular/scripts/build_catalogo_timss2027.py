"""Catálogo TIMSS 2027 Ciencias (4.° y 8.°) → data/referencia/catalogo_timss2027.json

Uso:  python scripts/build_catalogo_timss2027.py            # construye y valida contra el PDF
      python scripts/build_catalogo_timss2027.py --check    # solo valida, no escribe
Fuente: data/referencia/externos/timss/TIMSS2027_Marcos_Evaluacion.pdf, cap. 2 (Science Framework).
- pagina_fuente = página IMPRESA del marco («TIMSS 2027 SCIENCE FRAMEWORK nn»); pagina_pdf = pagina_fuente + 2.
- Código a nivel de objetivo numerado: T4_27-B1.2 = 4.°, Biología, área I, objetivo 2.
  Letras de dominio: B Biología, P Ciencias físicas (4.°) / Física (8.°), C Química, E Ciencias de la Tierra.
- Sub-ítems (A, B, C…) como texto parafraseado. ambiental = algún sub-ítem lleva asterisco en el PDF;
  si el asterisco solo marca una parte del sub-ítem, se anota en 'ambiental_parcial'.
- titulo_en = título corto del objetivo en el PDF; sirve para verificar la página citada.
- Las paráfrasis son en español y no copian párrafos del marco.
La validación compara con el texto del PDF: metas de dominio y cognitivas, áreas por dominio,
título de cada objetivo en su página y patrón de asteriscos por sub-ítem.
"""
import json, re, subprocess, sys

PDF = 'data/referencia/externos/timss/TIMSS2027_Marcos_Evaluacion.pdf'
OUT = 'data/referencia/catalogo_timss2027.json'
OFFSET_PDF = 2  # página PDF = página impresa + 2

METAS_COG = {'T4_27': {'Conocer': 0.35, 'Aplicar': 0.40, 'Razonar': 0.25},
             'T8_27': {'Conocer': 0.35, 'Aplicar': 0.35, 'Razonar': 0.30}}

# Sub-ítem: (letra, paráfrasis, ambiental, nota_parcial)
S = lambda l, t, a=False, p='': (l, t, a, p)

DATOS = {
 'T4_27': [
  ('B', 'Biología', 'Biology', 0.45, [
   (1, 'Características y procesos vitales de los organismos', 'Characteristics and Life Processes of Organisms', [
    (1, 'Differences between living and nonliving things', 26,
     'Diferencias entre seres vivos y no vivos, y lo que los seres vivos necesitan para vivir',
     [S('A', 'Distinguir seres vivos de no vivos (se reproducen, crecen, responden a estímulos y mueren).'),
      S('B', 'Identificar lo que plantas y animales requieren para vivir: aire, alimento o luz, agua y un ambiente.', True)]),
    (2, 'Physical and behavioral characteristics of major groups', 26,
     'Rasgos físicos y de conducta de los grandes grupos de seres vivos',
     [S('A', 'Comparar y clasificar plantas y animales, y mamíferos, aves, peces, reptiles e insectos, por sus rasgos.'),
      S('B', 'Dar ejemplos de miembros de los grandes grupos de animales.')]),
    (3, 'Functions of major structures in living things', 27,
     'Funciones de las estructuras principales de animales y plantas',
     [S('A', 'Relacionar estructuras animales con su función (piel, huesos, pulmones, corazón, estómago, músculos).'),
      S('B', 'Relacionar estructuras de la planta con su función (raíz, hoja, tallo, pétalos, flor, semilla).')]),
    (4, 'Sustaining life and maintaining conditions under external changes', 27,
     'Obtención de alimento y respuesta de los seres vivos a cambios externos',
     [S('A', 'Reconocer que las plantas fabrican su alimento con luz, aire y agua; los animales comen plantas u otros animales.', True),
      S('B', 'Describir cómo animales y el cuerpo humano responden a cambios externos (temperatura, peligro) y al ejercicio.', True,
        'solo la parte sobre respuestas de los animales lleva asterisco')]),
   ]),
   (2, 'Ciclos de vida, reproducción y herencia', 'Life Cycles, Reproduction, and Heredity', [
    (1, 'Stages of life cycles and differences among the life cycles', 27,
     'Etapas y diferencias de los ciclos de vida de plantas y animales comunes',
     [S('A', 'Identificar etapas del ciclo de vida de las plantas (germinación, crecimiento, polinización, fruto, dispersión).'),
      S('B', 'Reconocer, comparar y contrastar ciclos de vida de animales comunes (humanos, ranas, mariposas).')]),
    (2, 'Inheritance and reproduction strategies', 27,
     'Herencia y estrategias de reproducción',
     [S('A', 'Reconocer que la descendencia se parece a sus progenitores; distinguir rasgos heredados de no heredados.'),
      S('B', 'Describir estrategias que aumentan la supervivencia de la descendencia (muchas semillas, cuidado de crías).')]),
   ]),
   (3, 'Diversidad y adaptación', 'Diversity and Adaptation', [
    (1, 'Physical features and behaviors of living things that help them survive', 27,
     'Rasgos físicos y conductas que ayudan a sobrevivir en el ambiente',
     [S('A', 'Asociar rasgos físicos de plantas y animales con su ambiente y su supervivencia (tallo grueso, camuflaje).', True),
      S('B', 'Asociar conductas animales con su ambiente y su supervivencia (migración, hibernación).', True)]),
   ]),
   (4, 'Ecosistemas', 'Ecosystems', [
    (1, 'Common ecosystems', 28,
     'Ecosistemas comunes',
     [S('A', 'Relacionar plantas y animales comunes con ecosistemas (bosque, selva, desierto, sabana, ártico, río, océano).', True)]),
    (2, 'Relationships in ecosystems', 28,
     'Relaciones en los ecosistemas',
     [S('A', 'Completar una cadena alimentaria lineal y describir el papel de cada organismo.', True),
      S('B', 'Identificar depredadores y presas.'),
      S('C', 'Reconocer que algunos seres vivos compiten por recursos (alimento, agua, luz, espacio).', True)]),
    (3, 'The impact of humans on ecosystems', 28,
     'Impacto humano en los ecosistemas',
     [S('A', 'Dar ejemplos de efectos de la contaminación en personas, plantas y animales.', True),
      S('B', 'Reconocer efectos negativos y positivos de la conducta humana sobre poblaciones de un ecosistema.', True)]),
   ]),
   (5, 'Salud humana', 'Human Health', [
    (1, 'Transmission and prevention of diseases', 28,
     'Transmisión y prevención de enfermedades',
     [S('A', 'Relacionar el contagio de enfermedades con el contacto humano; describir formas de prevención (vacunas, lavado de manos).')]),
    (2, 'Ways of maintaining good health', 28,
     'Hábitos para mantener una buena salud',
     [S('A', 'Describir hábitos de salud física y mental; identificar grupos de alimentos de una dieta balanceada.')]),
   ]),
   (6, 'Investigaciones biológicas', 'Biological Investigations', [
    (1, 'Features of and equipment used in biological investigations', 28,
     'Rasgos y equipo de una investigación biológica',
     [S('A', 'Reconocer rasgos de una investigación biológica (prueba justa, observación vs inferencia) y el uso de lupa o pinzas.')]),
   ]),
  ]),
  ('P', 'Ciencias físicas', 'Physical Science', 0.35, [
   (1, 'Propiedades y cambios de la materia', 'Properties of Matter and Changes in Matter', [
    (1, 'States of matter', 29,
     'Estados de la materia',
     [S('A', 'Identificar sólido, líquido y gas por su forma y volumen; reconocer el estado del agua según la temperatura.'),
      S('B', 'Reconocer cambios de estado al calentar o enfriar; describir fusión, congelación, evaporación y condensación del agua.')]),
    (2, 'Physical properties as a basis for classifying matter', 29,
     'Propiedades físicas para clasificar la materia',
     [S('A', 'Comparar y ordenar materiales por masa, volumen, estado, conducción, flotación y atracción magnética.'),
      S('B', 'Identificar propiedades de los metales (conducen calor y electricidad) y relacionarlas con sus usos.')]),
    (3, 'Physical and chemical changes observed in everyday life', 30,
     'Cambios físicos y químicos en la vida diaria',
     [S('A', 'Distinguir cambios que no producen materiales nuevos de los que sí (descomposición, combustión, oxidación).'),
      S('B', 'Describir mezclas y métodos físicos para separarlas (tamizado, filtración, evaporación, imán).'),
      S('C', 'Identificar cómo acelerar la disolución de un sólido; distinguir soluciones débiles y concentradas.')]),
   ]),
   (2, 'Energía y transferencia de energía', 'Energy and Energy Transfer', [
    (1, 'Uses of energy in everyday life', 30,
     'Usos de la energía en la vida diaria',
     [S('A', 'Reconocer que las personas usan energía para distintos fines y en distintas formas (calor, electricidad).')]),
    (2, 'Heating and cooling', 30,
     'Calentamiento y enfriamiento',
     [S('A', 'Describir que al contacto un objeto caliente se enfría y el frío o el entorno se calienta.')]),
   ]),
   (3, 'Luz y sonido', 'Light and Sound', [
    (1, 'Light in everyday life', 30,
     'La luz en la vida diaria',
     [S('A', 'Relacionar sombras, reflejos y arcoíris con el comportamiento de la luz.')]),
    (2, 'Sound in everyday life', 30,
     'El sonido en la vida diaria',
     [S('A', 'Relacionar objetos que vibran y ecos con la producción y el comportamiento del sonido.')]),
   ]),
   (4, 'Electricidad y magnetismo', 'Electricity and Magnetism', [
    (1, 'Electricity and simple electrical devices', 30,
     'Electricidad y dispositivos eléctricos sencillos',
     [S('A', 'Reconocer que la energía eléctrica se transforma en calor, luz o sonido.'),
      S('B', 'Explicar que un circuito necesita un camino completo; identificar diagramas de circuitos simples completos.')]),
    (2, 'Magnetic attraction and repulsion', 30,
     'Atracción y repulsión magnética',
     [S('A', 'Reconocer que los imanes tienen dos polos; iguales se repelen y opuestos se atraen.'),
      S('B', 'Reconocer que los imanes atraen la mayoría de objetos metálicos.')]),
   ]),
   (5, 'Movimiento y fuerzas', 'Motion and Forces', [
    (1, 'Common forces and the motion of objects', 31,
     'Fuerzas comunes y movimiento de los objetos',
     [S('A', 'Identificar la gravedad como la fuerza que atrae los objetos hacia la Tierra.'),
      S('B', 'Reconocer que empujar y halar cambian el movimiento; comparar fuerzas; la fricción y el aire se oponen al movimiento.')]),
    (2, 'Simple machines', 31,
     'Máquinas simples',
     [S('A', 'Reconocer que palancas, poleas, engranajes y rampas facilitan el movimiento (menos fuerza o cambio de dirección).')]),
   ]),
   (6, 'Investigaciones en ciencias físicas', 'Physical Science Investigations', [
    (1, 'Features of and use of equipment in physical science investigations', 31,
     'Rasgos y uso de equipo en una investigación de ciencias físicas',
     [S('A', 'Reconocer rasgos de una investigación (preguntas comprobables, repetir mediciones al comparar métodos).'),
      S('B', 'Reconocer el uso de equipo común (balanza, cronómetro) en una investigación.')]),
   ]),
  ]),
  ('E', 'Ciencias de la Tierra', 'Earth Science', 0.20, [
   (1, 'Rasgos, procesos e historia de la Tierra', 'Earth’s Physical Features, Processes, and History', [
    (1, 'Physical characteristics of the Earth’s surface', 32,
     'Características físicas de la superficie terrestre',
     [S('A', 'Reconocer que hay más agua que tierra y que el aire la rodea; describir dónde hay agua dulce y salada.', True)]),
    (2, 'Earth’s history', 32,
     'Historia de la Tierra',
     [S('A', 'Reconocer que viento y agua modifican el paisaje y que algunos relieves se forman muy lentamente.'),
      S('B', 'Reconocer fósiles en rocas y hielo y deducir cambios de la superficie terrestre por su ubicación.')]),
   ]),
   (2, 'La atmósfera terrestre', 'Earth’s Atmosphere', [
    (1, 'Weather and climates on Earth', 32,
     'Tiempo atmosférico y climas',
     [S('A', 'Describir cómo varía el tiempo (temperatura, humedad, lluvia, nubes, viento) por día y lugar.', True),
      S('B', 'Describir cambios estacionales de temperatura y lluvia; reconocer el calentamiento global y algunos efectos.', True)]),
   ]),
   (3, 'Recursos de la Tierra, uso y conservación', 'Earth’s Resources, their Use, and Conservation', [
    (1, 'Earth’s resources', 32,
     'Recursos de la Tierra',
     [S('A', 'Reconocer usos cotidianos de agua, viento, suelo, bosques, minerales y combustibles fósiles; cuáles no son renovables.', True),
      S('B', 'Explicar la importancia de usar responsablemente los recursos de la Tierra.', True)]),
   ]),
   (4, 'La Tierra en el sistema solar', 'Earth in the Solar System', [
    (1, 'Objects in the Solar System and their movements', 32,
     'Objetos del sistema solar y sus movimientos',
     [S('A', 'Describir el sistema solar (Sol y planetas que giran); la Luna gira alrededor de la Tierra y cambia de aspecto.')]),
    (2, 'Earth’s motion and related patterns observed on Earth', 32,
     'Movimientos de la Tierra y patrones observables',
     [S('A', 'Explicar el día y la noche por la rotación de la Tierra.'),
      S('B', 'Reconocer que la Tierra da una vuelta al Sol en un año.')]),
   ]),
   (5, 'Investigaciones en ciencias de la Tierra', 'Earth Science Investigations', [
    (1, 'Use of equipment in earth science investigations', 33,
     'Uso de equipo en investigaciones de ciencias de la Tierra',
     [S('A', 'Reconocer el uso de termómetro, brújula o pluviómetro en una investigación.')]),
   ]),
  ]),
 ],
 'T8_27': [
  ('B', 'Biología', 'Biology', 0.35, [
   (1, 'Características y procesos vitales de los organismos', 'Characteristics and Life Processes of Organisms', [
    (1, 'Differences among major taxonomic groups of organisms', 34,
     'Diferencias entre los grandes grupos taxonómicos',
     [S('A', 'Identificar rasgos que distinguen bacterias, hongos, plantas, animales y clases de vertebrados e insectos.'),
      S('B', 'Reconocer y clasificar organismos como ejemplos de esos grupos taxonómicos.')]),
    (2, 'Structures and functions of major organ systems', 34,
     'Estructura y función de los principales sistemas de órganos',
     [S('A', 'Ubicar sistemas respiratorio, digestivo, óseo y nervioso, y sus órganos, en el cuerpo humano.'),
      S('B', 'Comparar órganos y sistemas de humanos con los de otros vertebrados (pulmones vs branquias).'),
      S('C', 'Explicar el papel de órganos y sistemas en el sostenimiento de la vida (circulación, respiración).')]),
    (3, 'Physiological processes in plants and animals', 34,
     'Procesos fisiológicos en plantas y animales',
     [S('A', 'Explicar cómo los animales responden a cambios para mantener estables sus condiciones (homeostasis).'),
      S('B', 'Describir función y proceso básico de la fotosíntesis (luz, CO2, agua, clorofila → glucosa y oxígeno).', True),
      S('C', 'Describir función y proceso básico de la respiración celular (oxígeno y glucosa → energía, CO2 y agua).', True)]),
   ]),
   (2, 'Las células y sus funciones', 'Cells and Their Functions', [
    (1, 'The structures and functions of cells', 34,
     'Estructura y funciones de la célula',
     [S('A', 'Explicar que los seres vivos están formados por células que cumplen funciones vitales y se dividen.'),
      S('B', 'Identificar estructuras celulares principales y su función (pared, membrana, núcleo, cloroplasto, mitocondria…).'),
      S('C', 'Reconocer que pared, cloroplastos y vacuola distinguen la célula vegetal de la animal.'),
      S('D', 'Explicar que tejidos, órganos y sistemas se forman de células especializadas.')]),
   ]),
   (3, 'Ciclos de vida, reproducción y herencia', 'Life Cycles, Reproduction, and Heredity', [
    (1, 'Sexual reproduction and inheritance in plants and animals', 35,
     'Reproducción sexual y herencia en plantas y animales',
     [S('A', 'Reconocer la fecundación y que la descendencia es parecida pero no idéntica; herencia por material genético.'),
      S('B', 'Reconocer que los rasgos están codificados en el ADN de los cromosomas del núcleo.'),
      S('C', 'Distinguir rasgos heredados de rasgos adquiridos o aprendidos.')]),
   ]),
   (4, 'Diversidad, adaptación y selección natural', 'Diversity, Adaptation, and Natural Selection', [
    (1, 'Variation as the basis for natural selection', 35,
     'La variación como base de la selección natural',
     [S('A', 'Reconocer que la variación da ventajas de supervivencia y reproducción; relacionarla con extinción en ambientes cambiantes.')]),
    (2, 'Evidence for changes in life on Earth over time', 35,
     'Evidencias del cambio de la vida en la Tierra',
     [S('A', 'Sacar conclusiones sobre cuánto tiempo han existido grupos de organismos a partir de fósiles.'),
      S('B', 'Describir cómo semejanzas entre especies y fósiles evidencian cambio y ancestro común.')]),
   ]),
   (5, 'Ecosistemas', 'Ecosystems', [
    (1, 'Natural, urban, and rural ecosystems', 35,
     'Ecosistemas naturales, urbanos y rurales',
     [S('A', 'Comparar ecosistemas naturales, rurales y urbanos por sus rasgos y organismos.', True)]),
    (2, 'The flow of energy in ecosystems', 35,
     'Flujo de energía en los ecosistemas',
     [S('A', 'Describir el flujo de energía de productores a consumidores y descomponedores; construir e interpretar pirámides.', True)]),
    (3, 'The cycling of water, oxygen, and carbon in ecosystems', 35,
     'Ciclos del agua, el oxígeno y el carbono en los ecosistemas',
     [S('A', 'Describir el papel de los seres vivos en el ciclo del agua (transpiración, bebida, respiración, desechos).', True),
      S('B', 'Describir el papel de los seres vivos en los ciclos del oxígeno y el carbono.', True)]),
    (4, 'Relationships in ecosystems', 36,
     'Relaciones en los ecosistemas',
     [S('A', 'Dar ejemplos de productores, consumidores y descomponedores; construir e interpretar redes tróficas.', True),
      S('B', 'Describir y ejemplificar la competencia entre poblaciones u organismos.', True),
      S('C', 'Describir y ejemplificar la depredación.', True),
      S('D', 'Describir y ejemplificar mutualismo y parasitismo.', True)]),
    (5, 'Factors affecting population size in an ecosystem', 36,
     'Factores que afectan el tamaño de las poblaciones',
     [S('A', 'Identificar factores que limitan una población (depredadores, alimento, agua).', True),
      S('B', 'Predecir cómo cambios en el ecosistema afectan el equilibrio entre poblaciones.', True)]),
    (6, 'Human impact on ecosystems', 36,
     'Impacto humano en los ecosistemas',
     [S('A', 'Describir efectos de la contaminación del aire, agua y suelo en personas, plantas y animales.', True),
      S('B', 'Explicar efectos positivos y negativos de la conducta humana en los ecosistemas.', True)]),
   ]),
   (6, 'Salud humana', 'Human Health', [
    (1, 'Causes, transmission, prevention of, and resistance to diseases', 36,
     'Causas, transmisión, prevención y resistencia a enfermedades',
     [S('A', 'Describir causas, contagio y prevención de enfermedades virales, bacterianas y parasitarias.'),
      S('B', 'Describir el papel del sistema inmunitario (anticuerpos, glóbulos blancos).'),
      S('C', 'Reconocer qué hacen vacunas y antibióticos, y que los antibióticos pierden eficacia cuando las bacterias cambian.')]),
    (2, 'Ways of maintaining good health', 37,
     'Hábitos para mantener una buena salud',
     [S('A', 'Explicar la importancia de dieta, ejercicio y estilo de vida para prevenir enfermedades.'),
      S('B', 'Identificar fuentes y funciones de los nutrientes en una dieta sana.')]),
   ]),
   (7, 'Investigaciones biológicas', 'Biological Investigations', [
    (1, 'Features of and equipment used in biological investigations', 37,
     'Rasgos y equipo de una investigación biológica',
     [S('A', 'Explicar rasgos de una investigación biológica sólida (pregunta, variables control y tratamiento) y el uso del microscopio.')]),
   ]),
  ]),
  ('C', 'Química', 'Chemistry', 0.20, [
   (1, 'Composición de la materia', 'Composition of Matter', [
    (1, 'Structure of atoms and molecules', 38,
     'Estructura de átomos y moléculas',
     [S('A', 'Describir el átomo: electrones alrededor de un núcleo con protones y neutrones.'),
      S('B', 'Describir la materia como partículas; las moléculas como combinaciones de átomos (H2O, O2, CO2).'),
      S('C', 'Reconocer que el enlace químico es una atracción entre átomos en la que intervienen electrones.')]),
    (2, 'Elements, compounds, and mixtures', 38,
     'Elementos, compuestos y mezclas',
     [S('A', 'Diferenciar elementos, compuestos y mezclas; sustancias puras vs mezclas homogéneas y heterogéneas.')]),
    (3, 'The periodic table of elements', 38,
     'La tabla periódica',
     [S('A', 'Reconocer que la tabla periódica ordena los elementos por número de protones.'),
      S('B', 'Predecir propiedades de un elemento por su periodo y grupo; los del mismo grupo comparten propiedades.')]),
   ]),
   (2, 'Propiedades de la materia', 'Properties of Matter', [
    (1, 'Physical and chemical properties as a basis for classifying matter', 38,
     'Propiedades físicas y químicas para clasificar y usar materiales',
     [S('A', 'Distinguir propiedades físicas de propiedades químicas.'),
      S('B', 'Clasificar sustancias por propiedades físicas (densidad, puntos de fusión/ebullición, solubilidad, conductividad).'),
      S('C', 'Clasificar sustancias por propiedades químicas (reactividad, inflamabilidad) y relacionarlas con sus usos.')]),
    (2, 'Mixtures and solutions', 38,
     'Mezclas y disoluciones',
     [S('A', 'Explicar métodos físicos de separación de mezclas.'),
      S('B', 'Describir soluto y disolvente y relacionar la concentración con sus cantidades.'),
      S('C', 'Explicar cómo temperatura, agitación y superficie de contacto afectan la rapidez de disolución.')]),
    (3, 'Properties of acids and bases', 39,
     'Propiedades de ácidos y bases',
     [S('A', 'Reconocer ácidos y bases cotidianos por sus propiedades.'),
      S('B', 'Reconocer el pH de ácidos (<7) y bases (>7), la neutralización y el cambio de color de indicadores.')]),
   ]),
   (3, 'Reacciones químicas', 'Chemical Reactions', [
    (1, 'Characteristics of chemical reactions', 39,
     'Características de las reacciones químicas',
     [S('A', 'Reconocer que en una reacción se forman sustancias nuevas y describir evidencias (gas, precipitado, color, calor, luz).')]),
    (2, 'Matter and energy in chemical reactions', 39,
     'Materia y energía en las reacciones químicas',
     [S('A', 'Reconocer la conservación de la masa: los átomos se reordenan.'),
      S('B', 'Distinguir reacciones que liberan energía de las que la absorben.'),
      S('C', 'Reconocer que la rapidez de reacción depende de superficie, temperatura y concentración.')]),
   ]),
   (4, 'Investigaciones químicas', 'Chemistry Investigations', [
    (1, 'Features of and equipment used in chemistry investigations', 39,
     'Rasgos y equipo de una investigación química',
     [S('A', 'Explicar rasgos de una investigación química sólida (preguntas comprobables, cambiar una sola variable).'),
      S('B', 'Reconocer el uso adecuado y seguro de materiales y equipo de laboratorio (balanza, beaker, tubo de ensayo).')]),
   ]),
  ]),
  ('P', 'Física', 'Physics', 0.25, [
   (1, 'Estados físicos y cambios de la materia', 'Physical States and Changes in Matter', [
    (1, 'Motion of particles in solids, liquids, and gases', 40,
     'Movimiento de partículas en sólidos, líquidos y gases',
     [S('A', 'Reconocer el movimiento constante de las partículas y usarlo para explicar propiedades de cada estado.'),
      S('B', 'Relacionar la temperatura con movimiento y distancia de partículas, presión y volumen de gases y dilatación.')]),
    (2, 'Changes in states of matter', 41,
     'Cambios de estado',
     [S('A', 'Describir cambios de estado por ganancia o pérdida de energía térmica; temperatura y masa constantes.'),
      S('B', 'Relacionar la rapidez del cambio de estado con factores físicos (superficie, temperatura ambiente).')]),
   ]),
   (2, 'Transformación y transferencia de energía', 'Energy Transformation and Transfer', [
    (1, 'Forms of energy and the conservation of energy', 41,
     'Formas de energía y conservación de la energía',
     [S('A', 'Identificar formas de energía (cinética, potencial, luminosa, sonora, eléctrica, térmica, química).'),
      S('B', 'Describir transformaciones de energía en procesos comunes; la energía total de un sistema cerrado se conserva.')]),
    (2, 'Thermal energy transfer', 41,
     'Transferencia de energía térmica',
     [S('A', 'Relacionar el paso de energía térmica de lo caliente a lo frío con calentar y enfriar hasta el equilibrio.'),
      S('B', 'Relacionar la rapidez de transferencia térmica con la conductividad del material.')]),
   ]),
   (3, 'Luz y sonido', 'Light and Sound', [
    (1, 'Properties of light', 41,
     'Propiedades de la luz',
     [S('A', 'Describir propiedades de la luz (rapidez, reflexión, refracción, absorción, dispersión) y el color de los objetos.'),
      S('B', 'Resolver problemas con espejos planos y sombras; interpretar diagramas de rayos.')]),
    (2, 'Properties of sound', 41,
     'Propiedades del sonido',
     [S('A', 'Describir el sonido como onda (amplitud, frecuencia, medio, reflexión, rapidez) y relacionarlo con ecos y truenos.')]),
   ]),
   (4, 'Electricidad y magnetismo', 'Electricity and Magnetism', [
    (1, 'Conductors and the flow of electricity in electrical circuits', 41,
     'Conductores y corriente en circuitos eléctricos',
     [S('A', 'Identificar conductores y aislantes y los componentes que cierran un circuito.'),
      S('B', 'Reconocer circuitos completos e incompletos, en serie y en paralelo; interpretar sus diagramas.')]),
    (2, 'Properties and uses of permanent magnets and electromagnets', 42,
     'Propiedades y usos de imanes permanentes y electroimanes',
     [S('A', 'Relacionar propiedades de los imanes permanentes con usos cotidianos (brújula).'),
      S('B', 'Describir propiedades propias de los electroimanes y relacionarlas con usos (timbre, reciclaje).')]),
   ]),
   (5, 'Movimiento y fuerzas', 'Motion and Forces', [
    (1, 'Motion', 42,
     'Movimiento',
     [S('A', 'Reconocer la rapidez como cambio de posición en el tiempo y la aceleración como cambio de rapidez.')]),
    (2, 'Common forces and their characteristics', 42,
     'Fuerzas comunes y sus características',
     [S('A', 'Describir fuerzas mecánicas comunes (normal, fricción, elástica, empuje); el peso como fuerza de gravedad.'),
      S('B', 'Reconocer que las fuerzas tienen magnitud y dirección; acción y reacción.')]),
    (3, 'Effects of forces', 42,
     'Efectos de las fuerzas',
     [S('A', 'Describir el funcionamiento de máquinas simples.'),
      S('B', 'Explicar flotación por diferencias de densidad y fuerza de empuje.'),
      S('C', 'Describir la presión como fuerza sobre área y sus efectos.'),
      S('D', 'Predecir cambios cualitativos del movimiento según las fuerzas; efecto de la fricción y el aire.')]),
   ]),
   (6, 'Investigaciones en física', 'Physics Investigations', [
    (1, 'Features of and equipment used in physics investigations', 42,
     'Rasgos y equipo de una investigación en física',
     [S('A', 'Explicar rasgos de una investigación sólida en física (preguntas contestables, repetir mediciones).'),
      S('B', 'Reconocer el uso adecuado y seguro de equipo (balanza, amperímetro, dinamómetro).')]),
   ]),
  ]),
  ('E', 'Ciencias de la Tierra', 'Earth Science', 0.20, [
   (1, 'Rasgos, procesos e historia de la Tierra', 'Earth’s Physical Features, Processes, and History', [
    (1, 'Earth’s structure', 43,
     'Estructura de la Tierra y distribución del agua',
     [S('A', 'Describir corteza, manto y núcleos interno y externo y sus características.'),
      S('B', 'Describir la distribución del agua por estado y dulce/salada; métodos para obtener agua dulce (desalinizar, potabilizar).', True)]),
    (2, 'Geological processes', 43,
     'Procesos geológicos',
     [S('A', 'Describir el ciclo de las rocas.'),
      S('B', 'Describir grandes cambios de la superficie por glaciación, placas tectónicas, sismos, volcanes o asteroides.'),
      S('C', 'Explicar la formación de fósiles y combustibles fósiles; usar el registro fósil para inferir cambios ambientales.', True,
        'solo la formación de fósiles y combustibles fósiles lleva asterisco')]),
   ]),
   (2, 'La atmósfera terrestre', 'Earth’s Atmosphere', [
    (1, 'Components of Earth’s atmosphere and atmospheric conditions', 44,
     'Componentes de la atmósfera y condiciones atmosféricas',
     [S('A', 'Reconocer la atmósfera como mezcla de gases y la abundancia relativa de N2, O2, vapor de agua y CO2.', True),
      S('B', 'Relacionar cambios de temperatura y presión con la altitud.')]),
    (2, 'Earth’s water cycle', 44,
     'El ciclo del agua',
     [S('A', 'Describir los procesos del ciclo del agua, su papel en renovar el agua dulce y el Sol como fuente de energía.', True,
        'el papel del Sol como fuente de energía no lleva asterisco'),
      S('B', 'Reconocer que nubes y lluvia se forman por condensación al enfriarse el aire que asciende.')]),
    (3, 'Weather and climate', 44,
     'Tiempo atmosférico y clima',
     [S('A', 'Distinguir tiempo atmosférico de clima.', True),
      S('B', 'Interpretar datos para identificar tipos de clima; relacionarlos con hemisferio, latitud, altitud y geografía.')]),
    (4, 'Climate change', 44,
     'Cambio climático',
     [S('A', 'Identificar posibles causas del cambio climático global (gases de efecto invernadero, volcanes).', True),
      S('B', 'Interpretar datos que evidencian el cambio climático local y global.', True)]),
   ]),
   (3, 'Recursos de la Tierra, uso y conservación', 'Earth’s Resources, Their Use, and Conservation', [
    (1, 'Energy resources', 44,
     'Fuentes de energía',
     [S('A', 'Identificar fuentes de energía (solar, eólica, hídrica, geotérmica, biomasa, nuclear, fósil) y sus ventajas y desventajas.', True)]),
    (2, 'Managing Earth’s resources', 44,
     'Gestión de los recursos de la Tierra',
     [S('A', 'Dar ejemplos de recursos renovables y no renovables.', True),
      S('B', 'Explicar cómo agricultura, tala y minería afectan los recursos.', True),
      S('C', 'Explicar la conservación de recursos y comparar métodos, incluido el manejo de residuos (reducir, reutilizar, reciclar).', True)]),
   ]),
   (4, 'La Tierra en el sistema solar', 'Earth in the Solar System', [
    (1, 'Observable phenomena on Earth resulting from movements of Earth and the Moon', 45,
     'Fenómenos observables por los movimientos de la Tierra y la Luna',
     [S('A', 'Describir efectos de la rotación (día, noche, sombras) y de la traslación con eje inclinado (estaciones).'),
      S('B', 'Reconocer que la Luna causa las mareas; relacionar fases y eclipses con las posiciones de Tierra, Luna y Sol.')]),
    (2, 'The Sun, Earth, Moon, and planets', 45,
     'El Sol, la Tierra, la Luna y los planetas',
     [S('A', 'Reconocer el Sol como estrella que da luz y calor; planetas y lunas se ven por luz reflejada.'),
      S('B', 'Interpretar datos para comparar la Tierra, la Luna y otros planetas; la gravedad mantiene las órbitas.')]),
   ]),
   (5, 'Investigaciones en ciencias de la Tierra', 'Earth Science Investigations', [
    (1, 'Equipment used in earth science investigations', 45,
     'Equipo usado en investigaciones de ciencias de la Tierra',
     [S('A', 'Reconocer el uso de telescopio o brújula en una investigación.')]),
   ]),
  ]),
 ],
}

ROMANOS = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']


def construir():
    cat = []
    for marco, dominios in DATOS.items():
        for letra, dominio, dominio_en, meta, areas in dominios:
            for na, area, area_en, objetivos in areas:
                inv = area_en.endswith('Investigations')
                for no, titulo_en, pag, objetivo, subs in objetivos:
                    cat.append({
                        'codigo': f'{marco}-{letra}{na}.{no}',
                        'marco': marco,
                        'dominio': dominio,
                        'dominio_en': dominio_en,
                        'meta_dominio': meta,
                        'area_codigo': f'{marco}-{letra}{na}',
                        'area_romano': ROMANOS[na - 1],
                        'area': area,
                        'area_en': area_en,
                        'objetivo': objetivo,
                        'titulo_en': titulo_en,
                        'subitems': [{'letra': l, 'texto': t, 'ambiental': a, **({'ambiental_parcial': p} if p else {})}
                                     for l, t, a, p in subs],
                        'ambiental': any(a for _, _, a, _ in subs),
                        'es_investigacion': inv,
                        'pagina_fuente': pag,
                        'pagina_pdf': pag + OFFSET_PDF,
                    })
    return cat


# ---------------------------------------------------------------- validación contra el PDF
def pagina(n_pdf):
    return subprocess.run(['pdftotext', '-layout', '-f', str(n_pdf), '-l', str(n_pdf), PDF, '-'],
                          capture_output=True, text=True, check=True).stdout


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('’', "'")).strip().lower()


def asteriscos_por_subitem(txt):
    """Lista de (letra, tiene_asterisco) en el orden en que aparecen en la página."""
    out = []
    for blk in re.split(r'\n(?=\s+[A-D]\.\s)', txt)[1:]:
        m = re.match(r'\s+([A-D])\.\s', blk)
        assert m
        cuerpo = re.split(r'\n\s+\d+\.\s|\n[IVX]+\.\s', blk)[0]  # corta antes del siguiente objetivo/área
        out.append((m.group(1), '*' in cuerpo))
    return out


def validar(cat):
    errores = []
    cache = {}
    get = lambda p: cache.setdefault(p, pagina(p))
    # 1. metas de dominio (Exhibit 2.1, p. 23) y cognitivas (Exhibit 2.2, p. 24)
    t = norm(get(23 + OFFSET_PDF))
    i4, i8 = t.index('fourth grade content domains'), t.index('eighth grade content domains')
    for marco, ini, fin in (('T4_27', i4, i8), ('T8_27', i8, len(t))):
        for dom_en, meta in {(c['dominio_en'], c['meta_dominio']) for c in cat if c['marco'] == marco}:
            if f'{norm(dom_en)} {round(meta * 100)}%' not in t[ini:fin]:
                errores.append(f'meta {marco} {dom_en} {meta} no coincide con Exhibit 2.1')
    t = norm(get(24 + OFFSET_PDF))
    for en, es in (('knowing', 'Conocer'), ('applying', 'Aplicar'), ('reasoning', 'Razonar')):
        m = re.search(rf'{en} (\d+)% (\d+)%', t)
        if not m or (int(m.group(1)), int(m.group(2))) != (round(METAS_COG['T4_27'][es] * 100), round(METAS_COG['T8_27'][es] * 100)):
            errores.append(f'meta cognitiva {es} no coincide con Exhibit 2.2')
    # 2. áreas por dominio: la lista romana de cada dominio en el PDF
    for c in cat:
        if norm(c['area_en']) not in norm(get(c['pagina_pdf'])) and not any(
                norm(f"{c['area_romano']}. {c['area_en']}") in norm(get(p)) for p in range(26 + OFFSET_PDF, 46 + OFFSET_PDF)):
            errores.append(f"área {c['area_codigo']} «{c['area_en']}» no hallada")
    # 3. cada objetivo en su página, con sus sub-ítems y asteriscos en el mismo orden
    por_pag = {}
    for c in cat:
        txt = get(c['pagina_pdf'])
        if norm(c['titulo_en']) not in norm(txt):
            errores.append(f"{c['codigo']}: título «{c['titulo_en']}» no está en p. {c['pagina_fuente']}")
        por_pag.setdefault(c['pagina_pdf'], []).extend((s['letra'], s['ambiental']) for s in c['subitems'])
    for p, esperado in por_pag.items():
        # sub-ítems que empiezan en esta página (el primer bloque de la p. 33 impresa es de 4.°, el resto de 8.°)
        if asteriscos_por_subitem(get(p)) != esperado:
            errores.append(f'p. {p - OFFSET_PDF}: sub-ítems/asteriscos difieren\n  PDF {asteriscos_por_subitem(get(p))}\n  cat {esperado}')
    return errores


def resumen(cat):
    print(f"{'marco':6} {'dominio':22} {'meta':>5} {'áreas':>5} {'obj':>4} {'subít':>5} {'amb':>4} {'inv':>4}")
    for marco in ('T4_27', 'T8_27'):
        for dom in dict.fromkeys(c['dominio'] for c in cat if c['marco'] == marco):
            g = [c for c in cat if c['marco'] == marco and c['dominio'] == dom]
            print(f"{marco:6} {dom:22} {g[0]['meta_dominio']:>5.0%} {len({c['area_codigo'] for c in g}):>5} {len(g):>4} "
                  f"{sum(len(c['subitems']) for c in g):>5} {sum(c['ambiental'] for c in g):>4} {sum(c['es_investigacion'] for c in g):>4}")
        g = [c for c in cat if c['marco'] == marco]
        print(f"{marco:6} {'TOTAL':22} {'':>5} {len({c['area_codigo'] for c in g}):>5} {len(g):>4} "
              f"{sum(len(c['subitems']) for c in g):>5} {sum(c['ambiental'] for c in g):>4} {sum(c['es_investigacion'] for c in g):>4}")


if __name__ == '__main__':
    cat = construir()
    assert len({c['codigo'] for c in cat}) == len(cat), 'códigos repetidos'
    errores = validar(cat)
    resumen(cat)
    if errores:
        print('\nERRORES DE VALIDACIÓN:\n' + '\n'.join(errores))
        sys.exit(1)
    print('\nValidación contra el PDF: OK (metas, áreas, títulos por página, sub-ítems y asteriscos)')
    if '--check' not in sys.argv:
        json.dump(cat, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'Escrito {OUT} ({len(cat)} objetivos)')
