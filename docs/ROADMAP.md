# Reconstrucción del producto curricular

Corte de investigación: 21 de octubre de 2026. Objetivo: reconstruir el producto sobre la entrega V4 del MINED, con progresiones de ciencias, experiencias de enseñanza y evaluación contextualizadas para El Salvador. La versión de un currículo, la del formato del grafo y la de una ejecución son identidades diferentes.

## Estado de ejecución del 22 de octubre

La entrega final producto-4 contiene 108 unidades respaldadas y 1.013 filas de Ciencias, con las siete
fuera de alcance conservadas. P6 resolvió las diez incidencias y P7 corrigió un falso positivo adicional
con nuevas fuentes y cuatro votos sobre otro borrador. La matriz comparada, la copia con cuatro
enmiendas de Biología y la vista sin conexión están verificadas. La suite pasó 1.360 pruebas.
La selección definitiva está publicada; el cierre operativo completó dos restauraciones del respaldo
final y retiró el corpus del checkout después de comparar todos los originales con el plan.
Las progresiones NGSS son documentales; no se afirman prerrequisitos locales ni eficacia de aprendizaje.
[Resultados actuales y reproducción](CURRICULARIZACION_V4.md).

Las fases siguientes conservan el plan y sus criterios; las descripciones del primer piloto son
antecedentes del 21 de octubre, ampliados por la campaña completa.

## Decisiones fundamentadas

1. El currículo nacional y la entrega V4 son la referencia local. PISA, ERCE y TIMSS son perspectivas de evaluación independientes; ningún ranking extranjero sustituye una decisión curricular salvadoreña.
2. La alineación debe considerar contenido, práctica científica, conocimiento procedimental y epistémico, demanda cognitiva y evidencia de aprendizaje. La coincidencia de un tema no acredita cobertura de una competencia.
3. PISA 2025 tiene marco final y resultados publicados en 2026. ERCE 2025 aún no tiene resultados al corte; se conserva ERCE 2019 como referencia histórica explícita de ciencias de sexto. TIMSS 2027 es un marco prospectivo, no resultados observados.
4. La selección de países debe usar resultados verificables, obligatoriedad, edad y disponibilidad de fuente curricular vigente. La segunda auditoría corrigió una inversión de columnas 2019/2023 en nuestra lectura de TIMSS; los puntajes del catálogo anterior eran correctos. Se conservan las notas y encabezados de las tablas para evitar repetir ese error.
5. El motor opera automáticamente: especialistas de ciencia, psicopedagogo y revisor adversarial evalúan por separado. La publicación técnica exige todos los criterios, evidencia verificable y ausencia de contradicciones; si falla, se repara de forma acotada o se abstiene. No exige aprobación humana como transición del workflow técnico.
6. El consenso de modelos no prueba eficacia educativa, independencia estadística, dificultad de ítems ni aprobación oficial. Estos estados no se infieren desde un dictamen automático.
7. Se conserva el recuperador anterior como referencia. El candidato léxico más rápido perdió recuperación en varias pruebas: no se adopta por velocidad. Se comparará con embeddings e intervención agentic acotada.
8. LangGraph orquesta los pasos con estado y checkpoints; la lectura de archivos, cálculo de métricas y validación de citas siguen siendo código determinista. No se usa un agente para decidir lo que una regla puede comprobar exactamente.

Fuentes y límites: [investigación educativa](investigacion/educacion.md), [investigación de IA](investigacion/arquitectura_ia.md), [auditoría técnica](investigacion/auditoria_repo.md).

## Fases y aceptación

| Fase | Resultado | Puerta de aceptación | Estado |
|---|---|---|---|
| 0. Investigación y línea base | Fuentes oficiales, auditoría, métricas iniciales y casos de error | Fuentes/versiones identificadas, supuestos y límites explícitos | Cuatro PDF de marcos/resultados, 689 páginas, y 29 criterios PISA/ERCE; colección separada de 12 PDF/2.028 páginas de países, con ediciones y poblaciones documentadas |
| 1. Identidad de V4 | Inventario de archivos, SHA, esquemas, exclusiones y correspondencia V3→V4 | Ninguna hoja curricular omitida; cambios/fusiones/separaciones sin identidad ambigua silenciosa | Once matrices y 126 hojas mapeadas; 506 coincidencias textuales únicas V3→V4; 429 registros V3 y 514 V4 sin correspondencia exacta, sin inferir eliminaciones/fusiones |
| 2. Modelo curricular y evidencia | Grafo V4, catálogos de competencias, prácticas y progresiones | Integridad de fuentes, DAG y contratos; trazabilidad de toda inferencia; diferencias frente a V3 explicadas | Ingesta de 126 hojas/1.020 filas; snapshots y 22 categorías; quince juicios reales, dos conceptos admitidos y trece estados no respaldados; catálogo con 68 abstenciones; doce expectativas y nueve enlaces documentales nativos, sin prerrequisitos locales verificados |
| 3. Motor automático y contexto | Workflow durable, presupuesto, citas verificadas, especialistas y reparación | Fallos provocados producen abstención; ningún dictamen de otro borrador se reutiliza; reinicio no resetea gasto | Implementado con LangGraph, lectura primaria completa y especialistas; actividades y juicios V4 ejecutados y reanudados sin generación, sin validación de eficacia |
| 4. Experimentos y selección | Comparación de prompts/modelos y recuperación local/densa/híbrida/agentic | Gate declarado antes de comparar; no regresión material de calidad; costo y latencia publicados | Léxico e híbrido con embeddings rechazados como sustitutos; jueces en 16+24 casos; wrapper agentic y harness implementados; regresión V4 sobre las mismas 19 consultas con catálogo completo, sin selección de candidato ni ajuste al reservado |
| 5. Producto curricular completo | Diagnóstico, prioridades, simulación viable y paquetes por unidad sobre V4 | Una unidad completa atraviesa ingesta→evidencia→propuesta→revisión→exportación, con tiempo/recursos de aula | 108 unidades y 1.013 filas de Ciencias respaldadas, siete fuera de alcance conservadas; cuatro enmiendas derivadas, matriz comparada y vista sin conexión; recursos condicionales, sin eficacia medida |
| 6. Operación y cierre | Documentación vigente, interfaz coherente, limpieza y pruebas locales | Instalación reproducible, fuentes intactas, comandos válidos, código retirado con evidencia, sin CI | Completado: API producto-4, CLI modular, 1.360 pruebas, Ruff; 7.580 archivos/siete SQLite restaurados dos veces, once terminales sin gasto y corpus local retirado |

El cotejo de países confirmó los bytes de tres programas DfE y de la revisión MOE enero 2026 de primaria;
no se rotulan como nuevas ediciones por la fecha de consulta. La revisión enero 2026 y la de octubre 2022
conviven con identidad distinta. Los originales MEXT, traducción y comentario se conservan separados.
DOCX/HTML por código aportan evidencia nativa a 445 candidatos AU: 602 hipótesis históricas siguen sin
hidratador, frente a 1.047 inicialmente. La política fija ediciones para 1.203 candidatos ENG/SG, pero las
6.901 hipótesis no reciben aceptación por disponer de un localizador. Los dos conceptos SI admitidos
proceden de nuevos expedientes con respaldo científico y límites por fila.
Ver [auditoría de conocimiento](investigacion/conocimiento_v4.md) y
[resultados actuales](investigacion/continuacion_ciencias_20261021.md).

El flujo semántico ya prepara relaciones de concepto, práctica, contraste y prerrequisito; usa cuatro
lecturas ciegas, criterios tipados, evidencia de objetivo/evaluación y respaldo primario de cada grupo.
Revalida terminales y comprueba ciclos entre lotes sin eliminar aristas. Hay pruebas locales con lectores
simulados y un expediente real sin modelos. La integración de archivos deduplicados, publicación
`producto-2` y recuperación por fila ya está implementada; la publicación conserva quince dictámenes
reales en tres cohortes completas. Faltan calibración independiente y ampliación de cobertura.
Reservar primero los grupos obligatorios permite preparar 1.166 de
1.203 contrastes con 24.000 caracteres, frente a 509 antes, sin modelos. Esto mide disponibilidad
estructural y no precisión de jueces. [Medición](investigacion/contexto_conocimiento_v4.md),
[operación y límites](juicios_conocimiento.md).

La V4 indicada por el usuario estaba en Descargas y macOS rechazó su lectura. Se encontró una alternativa en la [carpeta institucional «Versión 4»](https://drive.google.com/drive/folders/1x5XBTQUMcgEM1rHu27mzOgBeHby8cRIg), dentro de «2. MALLAS SUGERIDAS MODERNIZACIÓN C&T 2026», junto a las versiones 1–3. Sus once Excel se descargaron íntegros en `insumos/v4/`; `insumos/procedencia_v4.json` conserva IDs, URLs, modificación y SHA. No se pudo comparar contra los bytes de Descargas. El bloqueo de acceso quedó resuelto para esta fuente; no se necesita copia manual. La clasificación autorizada ya produjo un catálogo completo con 68 abstenciones y la publicación local V4 pasó su validación. El runtime V4 la consume sin cambiar el pipeline histórico V3. Siguen pendientes ampliar los juicios y las progresiones al conjunto del currículo. La primera unidad dispone de una [entrega experimental íntegra](investigacion/entrega_unidad_fisica10_20261021.md) bajo condiciones propuestas de tiempo y recursos; sus ensayos anteriores y abstenciones se conservan.

## Experimentos antes de elegir arquitectura

La integración `producto-3` conserva los cuatro pares PISA/ERCE originales dentro de la publicación:
un respaldo documental por fila, un rechazo y dos abstenciones, con auditoría HTTP y contexto primario
obligatorio. No cambia los quince juicios de conocimiento ni acredita cobertura global. Se incorporó
la colección oficial NGSS E/F/G (58 páginas), con bandas nativas y sin prerrequisitos locales inferidos.
Las progresiones verificadas y la calibración independiente siguen abiertas; completar la integración
técnica no permite declarar terminado el contenido educativo completo. Ver [integración](investigacion/integracion_alineaciones_v4.md)
y [decisión sobre progresiones](investigacion/progresiones_ngss_20261021.md).

La recuperación se compara sobre el mismo corpus y consultas, sin borrar del denominador los IDs que desaparecieron. Los conjuntos existentes son históricos y ya utilizados; sus resultados son regresiones, no una nueva prueba ciega. Se registran MRR, recall, cobertura por tipo, consultas fallidas, p50/p95, arranque, memoria cuando se mida y huellas de código/datos. El candidato se adopta solo si conserva calidad de forma consistente; un promedio favorable no oculta regresiones por grado o tipo de pregunta.

Para los jueces hay 16 casos sintéticos equilibrados, ocho correctos y ocho con errores sembrados, de cuatro ciencias, psicopedagogía, seguridad y razonamiento sobre fuentes. Se ocultan etiquetas, errores, IDs informativos y resultados esperados. Se comparan prompts directo y con rúbrica, dos modelos disponibles y solicitudes sin historial compartido. Se reportan aceptaciones incorrectas, rechazos incorrectos, abstenciones, fallos de contrato y latencia. Ningún resultado de este conjunto constituye validación educativa independiente.

La intervención agentic debe probarse después del baseline híbrido: como máximo una planificación de consulta y una recuperación adicional, con presupuesto idéntico de contexto. Se conserva solo si la mejora supera su costo, latencia y riesgo de introducir inferencias sin evidencia. No se declara "mejor workflow" antes de medirlo.

## Adaptación al aula salvadoreña

Cada propuesta deberá declarar grado/edad aplicable, objetivo observable, prerrequisitos, duración, recursos realmente disponibles, apoyo lector/matemático, seguridad, accesibilidad y una comprobación distinta de repetir la explicación. Agua, sismos, vulcanismo, biodiversidad o energía pueden ofrecer contextos locales; no se inventan estadísticas ni disponibilidad de laboratorio o conectividad. Se preservan variantes sin conexión y de materiales sencillos.

La simulación debe mostrar qué mejora, qué carga agrega y qué compromisos introduce. La prioridad no se reduce a cuántos países mencionan un concepto: incluye dependencia conceptual, robustez de evidencia, viabilidad y oportunidades de aprendizaje.
