# Prueba reservada del motor de jueces

Fecha: **21 de octubre de 2026**. Conjunto: `data/evaluacion/motor_casos_ciegos_2026.json`. Estado: **`sintetico_plata`**, sin ejecución cloud por el autor de los casos, sin anotación experta independiente y sin eficacia educativa medida.

## Independencia y límites

La autoría conoció únicamente el resultado agregado de saturación de la primera suite. No leyó los prompts del motor, su código de flujo, respuestas individuales ni `resultados_jueces.json`. Los casos nuevos se redactaron desde fuentes verificadas y condiciones sintéticas. Esa separación limita el ajuste directo al motor; no convierte el conjunto en patrón oro ni constituye revisión externa.

Contiene **24 casos** con tres posibles decisiones y roles científico, psicopedagógico y adversarial. Las situaciones no contienen datos reales del alumnado ni afirmaciones médicas. Las paráfrasis no son citas textuales, documentos íntegros ni un corpus primario certificado. Cada fuente conserva URL y localizador. Los campos de etiquetado y criterios son material del evaluador y no deben entregarse al juez.

Se conserva el esquema anterior; `par_id` agrupa ahora familias de contraste de tres casos. No asumir que la tercera clase equivale a rechazo. La decisión debe responder al alcance que se solicita: exactitud, respaldo documental, propiedad de un diseño o viabilidad no son la misma pregunta. La política de decisión está registrada en el JSON como especificación de anotación y no debe usarse para modificar retrospectivamente los prompts ya fijados.

## Una ejecución con condiciones congeladas

1. Guardar hashes de la suite, prompts y configuración antes de ejecutarlos. Congelar identificadores exactos de los dos modelos y los parámetros soportados. No leer las etiquetas para modificar un prompt, seleccionar ejemplos o cambiar políticas de salida.
2. Preparar una proyección de entrada con `id`, `rol`, `especialidad`, `contexto`, `contexto_fuente`, `propuesta` y metadatos de las fuentes referenciadas. Ocultar `esperado`, `variante`, `par_id`, `etiquetas`, `error_sembrado`, `motivo_evaluable` y `criterios`.
3. Las fuentes se presentan con título, URL y localizador. El contexto específico del caso determina qué fragmento está disponible; no agregar resúmenes globales ni navegación externa que repongan información deliberadamente ausente.
4. Enviar cada caso en una solicitud independiente, sin memoria entre casos ni respuestas de otro modelo. Usar orden aleatorio reproducible y registrar su semilla; el orden del archivo ya está mezclado. Los identificadores son opacos y no codifican una secuencia de respuestas.
5. Ejecutar una vez cada condición previamente fijada. Registrar errores, reintentos y salidas brutas. Una respuesta no parseable o una decisión fuera del contrato es inválida; no convertirla a la clase mayoritaria ni remapear una decisión diferente para producir un acierto.
6. Solo después de guardar las respuestas, unir los resultados con las etiquetas y criterios. Conservar los fallos y desacuerdos íntegros antes de interpretar causas.

No mostrar previews del archivo o sus etiquetas durante la preparación de los prompts. Una revisión posterior de los fallos convierte esta suite en conjunto de desarrollo para la siguiente iteración; cualquier mejora posterior necesita otro conjunto reservado.

## Medidas y reporte

Publicar la matriz de confusión de tres clases y conteos por rol. La exactitud debe incluir salidas inválidas en el denominador. Calcular exactitud balanceada, falsa aprobación de propuestas que deben rechazarse, falsa aprobación de casos no resolubles y rechazo injustificado de propuestas aceptables. Reportar también abstenciones innecesarias y familias resueltas completas.

Evaluar separadamente la decisión y el motivo: un acierto de etiqueta con una explicación contraria a la evidencia no demuestra un juicio correcto. Los criterios de la suite describen elementos semánticos verificables; no son una lista de palabras que baste mencionar. Si otro modelo puntúa los motivos, identificar ese resultado como evaluación asistida por IA y registrar sus desacuerdos, no como dictamen experto independiente.

Conservar tokens, costo disponible, latencia, identificadores del modelo, errores y trazas por condición. Si un prompt fijo no admite la tercera decisión, reportar la limitación del contrato; no alterar las etiquetas para ocultarla. No hay ejecución de estudiantes ni datos que permitan medir impacto de aprendizaje.

Una diferencia pequeña en 24 casos no justifica elegir ganador. El conjunto es deliberadamente diseñado, breve y sintético: no permite inferir tasas de seguridad o eficacia en producción. Si vuelve a saturarse, reportar el techo de la prueba y ampliar diversidad y dificultad sin afirmar superioridad. Si discrimina, interpretar los tipos de fallo además del promedio.

## Procedencia

Las referencias primarias de esta suite proceden de NASA, CUNY City Tech, University of Texas at Austin, OCDE, IES/What Works Clearinghouse y MINED de El Salvador. Las URL y localizadores se encuentran en el registro `fuentes` del JSON. Se verificaron durante la investigación al corte indicado. No se repiten aquí ejemplos ni anotaciones para conservar la separación entre la preparación experimental y el conjunto reservado.
