# Baseline V4: medición local provisional

Captura histórica del piloto. La medición posterior con catálogo completo está en
[resultados del producto publicado](resultados_baseline_v4_catalogado.md); no reemplaza esta evidencia.

Estado: **provisional_catalogo_piloto**. Sin llamadas a GCP; sin ejecución del candidato AgenticRAG.

Muestra: 19 consultas; 57 ejecuciones locales. Mínimo predeclarado: 20; selección insuficiente.

Catálogo: 613 filas pendientes o en abstención sin disciplina utilizable (612 sin lecturas y 1 con lecturas). No se infirieron etiquetas.

| Grado | n | MRR filas | Recall filas | MRR celdas | Recall contexto |
|---|---:|---:|---:|---:|---:|
| Todos | 19 | 0.1645 | 0.2105 | 0.1184 | 0.1018 |
| 2 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 3 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 4 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 5 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 6 | 1 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 7 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 8 | 3 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 9 | 2 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 10 | 3 | 0.7083 | 1.0000 | 0.4167 | 0.3667 |
| 11 | 1 | 1.0000 | 1.0000 | 1.0000 | 0.8333 |

| Caso | Relevantes no resueltos en índice | Asignatura admitida en gold | Abstención contexto |
|---|---:|---|---|
| V4-R01 | 0 | False | True |
| V4-R02 | 0 | False | True |
| V4-R03 | 0 | False | True |
| V4-R04 | 0 | False | True |
| V4-R05 | 0 | False | True |
| V4-R06 | 0 | False | True |
| V4-R07 | 0 | False | True |
| V4-R08 | 4 | False | True |
| V4-R09 | 0 | False | True |
| V4-R10 | 0 | False | False |
| V4-R11 | 0 | False | False |
| V4-R12 | 0 | False | True |
| V4-R13 | 0 | False | True |
| V4-R14 | 0 | False | True |
| V4-R15 | 0 | False | False |
| V4-R16 | 0 | True | False |
| V4-R17 | 0 | True | False |
| V4-R18 | 0 | True | False |
| V4-R19 | 0 | True | False |

Latencia p50/p95: 1.009 / 187.634 ms. Errores: 0.

Los localizadores no resueltos, blancos y encabezados permanecen en los denominadores. Los hashes, rankings completos y diagnósticos por caso están en el JSON.

Se transcribieron las 115 celdas de los 20 localizadores, sin seleccionar sólo las favorables. Cuatro
celdas son la referencia adicional de encabezados de V4-R08, fila física 2; no representan una fila
curricular recuperable y se conservaron como ausentes. Esta heterogeneidad de labels limita la lectura
del recall. Ningún criterio privado de jueces se convirtió en instrucciones o reformulaciones.

Hay 12 contextos vacíos de 19. En R10, R11 y R15 existe contexto local, pero el objetivo marcado como
relevante sigue excluido por la clasificación parcial. Un contexto local no demuestra haber recuperado
el objetivo solicitado. La latencia mediana baja incluye abstenciones y no describe una respuesta
pedagógica completa.

El catálogo piloto se conserva únicamente como entrada de evaluación en
`data/evaluacion/v4/catalogo_piloto_referencia.json`, con SHA de origen. No se publicó ni activó un
snapshot de producto. Consultas y gold están separados en `consultas_publicas.json` y `gold_offline.json`
del mismo directorio; `congelacion_previa.json` fija código y gate antes de abrir el reservado.

## Límites

- Las 19 consultas y condiciones son sintéticas plata; no son eficacia educativa ni oro oficial.
- El clasificador parcial no se completa por reglas, nombres o inferencia del evaluador.
- Fuente y referencias adicionales se mantienen completas, incluso encabezados y celdas vacías.
- La latencia es local, incluye hidratación y reutiliza caché; no es latencia de generación cloud.
- Esta lectura expone el conjunto a análisis; no debe usarse para afinar prompts y llamarlo ciego.
