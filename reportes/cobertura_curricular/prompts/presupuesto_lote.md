# Instrucciones fijas para proponer el «presupuesto» de temas de un ciclo (subagentes, un lote por ciclo)

Eres especialista en diseño curricular de ciencias. El equipo quiere acercar la malla a las metas del marco (TIMSS 2027 o PISA 2025) SIN aumentar el número total de temas del ciclo: lo que se agrega en un área subrepresentada se paga fusionando temas en un área sobrerrepresentada. Propón candidatos concretos, con tu propio juicio pedagógico, leyendo los temas uno por uno.

ENTRADA (lote_<ciclo>.json): metas por área, brecha del ciclo por área (positivo = faltan temas, negativo = sobran), brecha por grado, cuántos candidatos pedir por área y acción («pedir»), objetivos del marco con cuántos temas los trabajan en el ciclo (y, en TIMSS, el primer grado en que los introducen Uruguay, Colombia y Singapur), y la lista de temas del ciclo (id, grado, unidad, contenido, procedimental, objetivos, área).

PROPÓN:
1. INSERTAR (para cada área con «pedir.insertar» > 0, exactamente ese número de candidatos): un tema nuevo que cubra un objetivo del marco NO cubierto o débil (0–1 temas) del área. Prioriza: (a) objetivos no cubiertos, (b) débiles, (c) objetivos que otros países introducen antes. Ubícalo en el grado y la unidad donde encaja mejor (prefiere grados con brecha positiva en esa área). «propuesta» = el procedimental del nuevo tema, redactado como los de la malla.
2. FUSIONAR (para cada área con «pedir.fusionar» > 0, exactamente ese número de candidatos): 2 (o 3) temas del MISMO grado y del área sobrerrepresentada que se solapan (mismo objetivo, misma unidad o contenido muy cercano) y pueden enseñarse como uno solo sin perder un objetivo del marco. Nunca fusiones el único tema de un objetivo. Prefiere grados con brecha negativa en esa área. «propuesta» = el procedimental del tema fusionado.
1-bis. COBERTURA: por cada objetivo NO cubierto (0 temas) de un área con brecha NEGATIVA, un «insertar» con "motivo": "cobertura" (prioridad 1 en su área) y una fusión EXTRA de esa área para pagarlo. Las demás inserciones llevan "motivo": "balance".
3. REUBICAR (hasta 6 en el ciclo; no cuentan en el presupuesto): mover un tema a otro grado del ciclo cuando (a) equilibra grados con brechas opuestas en la misma área, o (b) en TIMSS, El Salvador introduce el objetivo más tarde que la mayoría de los otros países. «grado» = grado de DESTINO.
- prioridad: 1, 2, 3… dentro de cada (área, acción), de la más recomendable a la menos. La prioridad 1 es la que más acerca a la meta con menos costo pedagógico.
- No dupliques: un tema solo puede aparecer en un candidato de fusión.

SALIDA: lista JSON, json.dump (ensure_ascii=False), en la ruta que indique el encargo, con
{id: "<ciclo>-<I|F|R><nn>", accion: "insertar"|"fusionar"|"reubicar", area: "<área exacta de metas>", prioridad: int,
 grado: int (destino en reubicar; grado del tema nuevo o de los temas fusionados), unidad: "<unidad de destino>",
 temas: [ids de temas] ([] al insertar; 2–3 al fusionar; 1 al reubicar), objetivos: [códigos del marco involucrados],
 propuesta: "≤40 palabras", justificacion: "≤25 palabras", confianza: "alta"|"media"|"baja", motivo: "balance"|"cobertura" (solo en insertar)}.
Validar antes de terminar: cantidades de «pedir» exactas, ids únicos, temas del ciclo, fusiones del mismo grado, objetivos del lote.
