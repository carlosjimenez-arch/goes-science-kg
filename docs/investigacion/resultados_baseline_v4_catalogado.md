# Baseline V4: medición local provisional

Estado: **catalogo_completo**. Sin llamadas a GCP; sin ejecución del candidato AgenticRAG.

Muestra: 19 consultas; 57 ejecuciones locales. Mínimo predeclarado: 20; selección insuficiente.

Catálogo: 68 filas pendientes o en abstención sin disciplina utilizable (0 sin lecturas y 68 con lecturas). No se infirieron etiquetas.

| Grado | n | MRR filas | Recall filas | MRR celdas | Recall contexto |
|---|---:|---:|---:|---:|---:|
| Todos | 19 | 0.8421 | 0.8684 | 0.6996 | 0.6074 |
| 2 | 2 | 1.0000 | 1.0000 | 1.0000 | 0.7083 |
| 3 | 2 | 1.0000 | 1.0000 | 0.6000 | 0.6750 |
| 4 | 2 | 1.0000 | 1.0000 | 1.0000 | 0.8167 |
| 5 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 6 | 1 | 1.0000 | 0.5000 | 0.2000 | 0.4545 |
| 7 | 2 | 0.7500 | 1.0000 | 0.5714 | 0.7750 |
| 8 | 3 | 1.0000 | 1.0000 | 1.0000 | 0.7500 |
| 9 | 2 | 0.7500 | 1.0000 | 0.7500 | 0.4762 |
| 10 | 3 | 0.6667 | 0.6667 | 0.4167 | 0.3667 |
| 11 | 1 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |

| Caso | Relevantes no resueltos en índice | Asignatura admitida en gold | Abstención contexto |
|---|---:|---|---|
| V4-R01 | 0 | True | False |
| V4-R02 | 0 | True | False |
| V4-R03 | 0 | True | False |
| V4-R04 | 0 | True | False |
| V4-R05 | 0 | True | False |
| V4-R06 | 0 | True | False |
| V4-R07 | 0 | False | False |
| V4-R08 | 4 | True | False |
| V4-R09 | 0 | True | False |
| V4-R10 | 0 | True | False |
| V4-R11 | 0 | True | False |
| V4-R12 | 0 | True | False |
| V4-R13 | 0 | True | False |
| V4-R14 | 0 | True | False |
| V4-R15 | 0 | True | False |
| V4-R16 | 0 | True | False |
| V4-R17 | 0 | True | False |
| V4-R18 | 0 | True | False |
| V4-R19 | 0 | True | False |

Latencia p50/p95: 12.838 / 352.989 ms. Errores: 0.

Los localizadores no resueltos, blancos y encabezados permanecen en los denominadores. Los hashes, rankings completos y diagnósticos por caso están en el JSON.

## Límites

- Las 19 consultas y condiciones son sintéticas plata; no son eficacia educativa ni oro oficial.
- El clasificador parcial no se completa por reglas, nombres o inferencia del evaluador.
- Fuente y referencias adicionales se mantienen completas, incluso encabezados y celdas vacías.
- La latencia es local, incluye hidratación y reutiliza caché; no es latencia de generación cloud.
- Esta lectura expone el conjunto a análisis; no debe usarse para afinar prompts y llamarlo ciego.
- El mismo conjunto ya fue abierto con el catálogo piloto: regresión de cobertura, no evaluación ciega nueva ni ajuste de recuperación
- Las métricas de recuperación se conservan aunque exista alerta; los bloqueos de generación se informan aparte y el Motor sigue vetándolos
- Cambió la disponibilidad de filas por catalogación; no se atribuye la diferencia a un algoritmo nuevo ni a eficacia educativa

## Comparación con la captura piloto y límites actuales

La publicación real conserva 68 abstenciones y siete filas fuera de alcance. En estas mismas
19 consultas, MRR de filas pasó de 0,1645 a 0,8421 y recall@10 de 0,2105 a 0,8684 al ampliar las
filas disponibles. El recall de contexto pasó de 0,1018 a 0,6074. No se cambió ranking, prompts ni
labels. Esto describe cobertura de dos publicaciones diferentes; no prueba superioridad de un algoritmo.

En décimo, MRR de filas bajó de 0,7083 a 0,6667 y recall@10 de 1 a 0,6667; no se oculta esa regresión
en el promedio. R07, R08 y R16 mantienen recall de filas menor que uno. R08 conserva cuatro celdas de
encabezado no curriculares en el denominador. R16 también activa una alerta científica de generación;
la métrica de recuperación y el veto del Motor se informan por separado.

La carga única observada del runtime fue 1,1576 s. El p95 de contexto local fue 352,989 ms, con caché
compartida y otras comprobaciones locales concurrentes; no es latencia cloud ni comparación causal
de velocidad frente al piloto. Las medianas incluyen los casos sin contexto.

El conjunto ya había sido abierto en la medición piloto, sigue teniendo sólo 19 consultas y no cumple
el mínimo predeclarado de veinte. No se selecciona AgenticRAG, no se afina la recuperación con estos
resultados y no se atribuye adecuación pedagógica o aprendizaje a ninguna métrica. Las unidades usan
identidad de fila explícita; su verificación de fuentes no sustituye la revisión semántica de actividades.
