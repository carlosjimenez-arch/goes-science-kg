# Experimento real de recuperación con Vertex

Fecha: 2026-10-21T10:57:49.929661-05:00. Currículo: **V3**. Modelo: **gemini-embedding-001**, 768 dimensiones, us-central1.

Se usaron ADC y proyecto explícito. No se ajustaron pesos después de observar resultados. Los 98 casos históricos son regresión reutilizada; esta comparación no valida la V4.

Los archivos contienen 100 preguntas únicas. Se limitó el envío a las 98 autorizadas por orden de conjunto/id; dos casos se reportan sin ejecución y se excluyen por igual de todas las variantes.

| Variante / conjunto | MRR | recall@10 | Ausentes | p50 local ms | p95 local ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline / rag_preguntas.json | 0.840 | 0.619 | 10 | 1.820 | 2.300 |
| baseline / rag_preguntas_prueba.json | 0.671 | 0.668 | 5 | 2.260 | 3.399 |
| baseline / rag_preguntas_prueba2.json | 0.558 | 0.583 | 0 | 2.422 | 3.554 |
| baseline / rag_preguntas_prueba3.json | 0.682 | 0.610 | 0 | 2.149 | 2.574 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas.json | 0.706 | 0.468 | 10 | 0.307 | 0.403 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba.json | 0.721 | 0.423 | 5 | 0.304 | 0.367 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba2.json | 0.466 | 0.500 | 0 | 0.312 | 0.361 |
| hibrido_sin_embeddings_saltos0 / rag_preguntas_prueba3.json | 0.685 | 0.433 | 0 | 0.278 | 0.356 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas.json | 0.706 | 0.468 | 10 | 0.300 | 0.376 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba.json | 0.721 | 0.423 | 5 | 0.320 | 0.378 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba2.json | 0.466 | 0.500 | 0 | 0.322 | 0.374 |
| hibrido_sin_embeddings_saltos1 / rag_preguntas_prueba3.json | 0.685 | 0.433 | 0 | 0.293 | 0.374 |
| denso_768 / rag_preguntas.json | 0.620 | 0.468 | 10 | 0.290 | 0.421 |
| denso_768 / rag_preguntas_prueba.json | 0.574 | 0.350 | 5 | 0.275 | 0.413 |
| denso_768 / rag_preguntas_prueba2.json | 0.289 | 0.278 | 0 | 0.239 | 0.314 |
| denso_768 / rag_preguntas_prueba3.json | 0.515 | 0.357 | 0 | 0.302 | 0.424 |
| hibrido_768_saltos0 / rag_preguntas.json | 0.705 | 0.533 | 10 | 0.496 | 0.703 |
| hibrido_768_saltos0 / rag_preguntas_prueba.json | 0.666 | 0.447 | 5 | 0.500 | 0.711 |
| hibrido_768_saltos0 / rag_preguntas_prueba2.json | 0.463 | 0.444 | 0 | 0.455 | 0.541 |
| hibrido_768_saltos0 / rag_preguntas_prueba3.json | 0.556 | 0.530 | 0 | 0.495 | 0.739 |
| hibrido_768_saltos1 / rag_preguntas.json | 0.705 | 0.529 | 10 | 0.507 | 0.718 |
| hibrido_768_saltos1 / rag_preguntas_prueba.json | 0.666 | 0.463 | 5 | 0.519 | 0.727 |
| hibrido_768_saltos1 / rag_preguntas_prueba2.json | 0.467 | 0.444 | 0 | 0.467 | 0.566 |
| hibrido_768_saltos1 / rag_preguntas_prueba3.json | 0.556 | 0.530 | 0 | 0.504 | 0.757 |

Gate previo: MRR y recall@10 sin regresión en cada conjunto y rankings estables.

- hibrido_sin_embeddings_saltos0: no pasa.
- hibrido_sin_embeddings_saltos1: no pasa.
- denso_768: no pasa.
- hibrido_768_saltos0: no pasa.
- hibrido_768_saltos1: no pasa.

Mantener baseline; un benchmark histórico reutilizado no valida V4 ni eficacia educativa.

## Contabilidad

- Peticiones reservadas: 3140; completadas: 3136; errores: 1; cache hits: 403.
- Tokens reportados: 193520; reserva conservadora: 6427806.
- USD estimados por tokens reportados: **0.029028**; USD reservados: 0.964171; límite: 2.0.
- Tarifa consultada: [precios oficiales de Vertex](https://cloud.google.com/vertex-ai/generative-ai/pricing).
- Una petición por texto, RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY, truncamiento desactivado, SDK attempts=1, timeout 30 segundos, concurrencia 3 y caché incremental por contenido/configuración.

Los hashes, datos por consulta y ruta del ledger figuran en el JSON. Los vectores/cache operativos no se versionan en Git.

## Límites

- Conjuntos históricos plata, parcialmente usados para ajustar el baseline; no es un test ciego nuevo.
- Los relevantes ausentes se conservan en el denominador de recall y se reportan por separado.
- El grafo sigue la versión local detectada; no representa resultados de un currículo V4 ausente.
- Latencias locales con caché de archivos del sistema sin vaciar; no son un SLO cloud.
- El nuevo candidato tiene textos y filtros distintos; el estudio evalúa producto completo, no sólo BM25.
- Tres repeticiones por defecto no establecen significación estadística ni eficacia pedagógica.
- Sin embeddings ni generación: coste de llamadas cloud cero; no demuestra calidad del RAG completo.
- Las latencias locales densas excluyen la petición de embedding de consulta; ésta se reporta aparte.
- El ledger incluye el intento inicial sin red y sus reservas; no se afirma que esos tokens fueran facturados.
- USD se estima con tokens reportados y tarifa documentada; no representa una factura reconciliada.
- La API puede cambiar internamente el modelo: se conservan vectores y sus hashes para repetición.
- Los conjuntos suman 100 textos únicos, no 98. Se enviaron sólo los 98 primeros por conjunto/id; dos casos fuera del permiso no se enviaron ni se incluyeron en ninguna métrica de esta comparación.

## Reproducción

```python
from goes_science_kg.recuperacion.experimento_vertex import ejecutar_experimento
ejecutar_experimento(proyecto='g-edu-lxp-xai-dev-prj-976d')
```
