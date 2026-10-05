# Instrucciones fijas para alinear objetivos de otros países con TIMSS 2027 (subagentes, un lote por archivo)

Eres especialista en currículo de ciencias y en los marcos TIMSS. Alinea, sin preguntar, TODOS los objetivos del lote, uno por uno, con tu propio juicio (no con reglas de palabras clave). Es el mismo método que se usó con los temas de El Salvador (`prompts/clasificar_lote.md`), para que las dos cosas sean comparables.

ENTRADA: un JSON con «marco» (T4_27 para objetivos de 1.° a 4.°, T8_27 para 5.° a 9.°), «catalogo» (objetivos del marco con sub-ítems) y «objetivos» (id, pais, documento, pagina, grado_o_tramo, eje, tipo, texto).

PARA CADA OBJETIVO:
- obj1: código del objetivo TIMSS que MEJOR describe lo que el estudiante aprende. Si no corresponde a ningún objetivo → «FUERA».
  FUERA típico: competencias generales sin contenido científico (comunicación, convivencia, emociones, ciudadanía); tecnología y programación; unidades y conversiones aisladas; geografía humana o cartografía sin contenido de ciencias de la Tierra del catálogo.
- obj2: segundo código solo si el objetivo trabaja otro objetivo TIMSS de forma sustancial; si no, "".
- Áreas de «Investigaciones»: úsalas como obj1 SOLO si el foco es la práctica científica (preguntas comprobables, planificar, controlar variables, medir y repetir mediciones, registrar, analizar datos, concluir, usar instrumentos). Si la práctica es genérica (sin disciplina), elige el área de Investigaciones cuyo dominio corresponda al «eje» o al documento; si tampoco se deduce, la de Ciencias físicas/Física cuando el foco es medir con instrumentos y la de Biología cuando es observar seres vivos. Si el objetivo trabaja un contenido mediante indagación: obj1 = contenido y obj2 = área de Investigaciones.
- Clasifica por contenido aunque el nivel sea mayor o menor que TIMSS (p. ej. un objetivo de 3.° muy sencillo sobre fuerzas va igual a T4_27-P5.1).
- Un objetivo amplio que enumera varios contenidos: obj1 = el más central, obj2 = el siguiente. No hay obj3.
- confianza: alta | media | baja.
- justificacion: máximo 15 palabras, en español.
Solo códigos del catálogo del lote o «FUERA».

SALIDA: lista JSON con {id, obj1, obj2, confianza, justificacion}, escrita con json.dump (ensure_ascii=False) en la ruta que indique el encargo. Validar antes de terminar: un registro por objetivo del lote, mismos id, códigos válidos, obj1 ≠ obj2, justificación ≤ 15 palabras.
