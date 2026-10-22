# Comparación local de recuperación

Fecha: 2026-10-21T10:40:37.617475-05:00. Currículo detectado: **V3**.

Benchmark sin ajuste de pesos, sin embeddings y sin llamadas cloud. Ambos candidatos conservan sus diferencias de texto, filtros y navegación; el baseline permanece disponible.

| Variante / conjunto | n | MRR | recall@10 | Ausentes | p50 ms | p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline / rag_preguntas.json | 60 | 0.840 | 0.619 | 10 | 1.892 | 2.435 |
| baseline / rag_preguntas_prueba.json | 16 | 0.671 | 0.668 | 5 | 2.167 | 2.496 |
| baseline / rag_preguntas_prueba2.json | 12 | 0.558 | 0.583 | 0 | 2.529 | 3.055 |
| baseline / rag_preguntas_prueba3.json | 12 | 0.735 | 0.600 | 0 | 2.183 | 2.610 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas.json | 60 | 0.706 | 0.468 | 10 | 0.308 | 0.412 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba.json | 16 | 0.721 | 0.423 | 5 | 0.310 | 0.416 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba2.json | 12 | 0.466 | 0.500 | 0 | 0.323 | 0.368 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba3.json | 12 | 0.696 | 0.467 | 0 | 0.282 | 0.383 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas.json | 60 | 0.706 | 0.468 | 10 | 0.302 | 0.379 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba.json | 16 | 0.721 | 0.423 | 5 | 0.314 | 0.380 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba2.json | 12 | 0.466 | 0.500 | 0 | 0.330 | 0.373 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba3.json | 12 | 0.696 | 0.467 | 0 | 0.292 | 0.374 |

| Variante | Carga p50 ms | Índice p50 ms | Gate sin regresión |
| --- | ---: | ---: | --- |
| baseline | 49.482 | 29.605 | Referencia |
| hibrido_sin_embeddings_saltos0 | 68.342 | 121.277 | No pasa |
| hibrido_sin_embeddings_saltos1 | 68.342 | 121.277 | No pasa |

Gate fijado antes de medir: no disminuir MRR ni recall@10 en ninguno de los conjuntos y conservar rankings entre repeticiones. Es una regla de regresión, no validación educativa.

La velocidad por sí sola no justifica sustituir el baseline. Conservar el nuevo sistema como candidato hasta medir embeddings y un test vigente e independiente de V4.

Los hashes, IDs ausentes, métricas por consulta, carga/índice p95 y parámetros se conservan en el JSON.

## Límites

- Conjuntos históricos plata, parcialmente usados para ajustar el baseline; no es un test ciego nuevo.
- Los relevantes ausentes se conservan en el denominador de recall y se reportan por separado.
- El grafo sigue la versión local detectada; no representa resultados de un currículo V4 ausente.
- Latencias locales con caché de archivos del sistema sin vaciar; no son un SLO cloud.
- El nuevo candidato tiene textos y filtros distintos; el estudio evalúa producto completo, no sólo BM25.
- Tres repeticiones por defecto no establecen significación estadística ni eficacia pedagógica.
- Sin embeddings ni generación: coste de llamadas cloud cero; no demuestra calidad del RAG completo.

## Reproducción

```python
from goes_science_kg.recuperacion.evaluacion import comparar_recuperacion, escribir_comparacion
datos = comparar_recuperacion(repeticiones=3)
escribir_comparacion(datos, salida_json='docs/investigacion/resultados_recuperacion.json',
                     salida_md='docs/investigacion/resultados_recuperacion.md')
```
