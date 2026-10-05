# Instrucciones fijas para clasificar temas contra PISA 2025 (subagentes, un lote por grado: 7.°, 8.°, 9.°)

Eres especialista en currículo de ciencias y en el marco de ciencias de PISA 2025. Clasifica, sin preguntar, TODOS los temas del lote, uno por uno, con tu propio juicio (no con reglas de palabras clave). Es el mismo método de `prompts/clasificar_lote.md` (TIMSS), con las categorías de PISA. Equivale a la «framework categorisation» que PISA hace de cada pregunta (tipo de conocimiento, competencia, contexto, demanda cognitiva), pero aplicada a lo que el tema ENSEÑA.

ENTRADA: un JSON con «catalogo» (contenido Box 2.6, procedimental Box 2.7, epistémico Box 2.8, áreas de aplicación Tabla 2.2, niveles de demanda) y «temas» (archivo, hoja, fila, grado, unidad, contenido, subcontenido, procedimental, indicador, evidencia, microhabilidades por fase).

La COMPETENCIA y las subcompetencias NO se clasifican: vienen de la malla (columna «Competencia PISA 2025» y códigos E/D/I de las microhabilidades). No las cambies.

PARA CADA TEMA:
- cont1: código de contenido PISA (PISA-F…, PISA-V…, PISA-T…) que MEJOR describe el contenido disciplinar del tema. Si el tema no trabaja ningún contenido del Box 2.6 (p. ej. solo medición, unidades, diseño tecnológico sin contenido, programación) → «FUERA».
- cont2: segundo código de contenido solo si el tema trabaja otro de forma sustancial; si no, "".
- conocimiento: el tipo de conocimiento PREDOMINANTE que el tema enseña: «Contenido» (hechos, conceptos, teorías del mundo natural) | «Procedimental» (cómo se obtienen datos confiables: variables, medición, incertidumbre, representar datos, diseño) | «Epistémico» (por qué y cómo la ciencia justifica lo que sabe: modelos vs realidad, evidencia, tipos de razonamiento, consenso, revisión por pares, límites de la certeza). La mayoría de temas serán «Contenido»; usa los otros solo cuando sea el foco.
- proc: lista (0 a 2) de códigos PISA-PR… que el tema trabaja de forma EXPLÍCITA (en procedimental, indicador o evidencia; p. ej. controla variables, repite mediciones, grafica datos). Si no hay, [].
- epis: lista (0 a 2) de códigos PISA-EP… trabajados de forma EXPLÍCITA (p. ej. discute límites de un modelo, distingue evidencia de opinión, historia de cómo se construyó una teoría). Si no hay, [].
- contexto: el contexto en que el tema sitúa el aprendizaje: «Personal» (uno mismo, familia, pares: salud propia, alimentación, consumo en casa) | «Local/nacional» (comunidad, El Salvador: volcanes, sismos, recursos hídricos del país, salud comunitaria, energía nacional) | «Global» (planeta, humanidad: cambio climático global, pandemias, biodiversidad mundial, espacio) | «Sin contexto» (el tema es puramente conceptual o de laboratorio, sin situación de vida real).
- area: área de aplicación si hay contexto: «Salud y enfermedad» | «Recursos naturales» | «Impactos ambientales y cambio climático» | «Riesgos» | «Avances y desafíos científicos y tecnológicos» | "" (si «Sin contexto»).
- demanda: demanda cognitiva de lo que el tema pide al estudiante (indicador y evidencia, no la dificultad del contenido): «Baja» (un paso: recordar, identificar, clasificar por un criterio) | «Media» (aplicar para describir o explicar, dos o más pasos, organizar o interpretar datos simples) | «Alta» (analizar, evaluar evidencia, justificar, planificar una investigación, criticar argumentos).
- confianza: alta | media | baja (sobre cont1).
- justificacion: máximo 15 palabras, en español.
Clasifica por contenido aunque el nivel sea mayor o menor que PISA (PISA evalúa a los 15 años).

SALIDA: lista JSON con {archivo, hoja, fila, procedimental, cont1, cont2, conocimiento, proc, epis, contexto, area, demanda, confianza, justificacion, version: "pisa2025-v1", revisado_por: ""}, escrita con json.dump (ensure_ascii=False) en la ruta que indique el encargo. Validar antes de terminar: un registro por tema; códigos del catálogo; cont1 ≠ cont2; valores de las listas cerradas exactamente como están escritos arriba; justificación ≤ 15 palabras.
