# Experimento inicial de jueces

Corte: 2026-10-21. Conjunto sintético plata de 16 casos (8 pares correctos/errores), sin datos de estudiantes. Una llamada por combinación, orden aleatorizado con semilla fija; etiquetas y motivos esperados no se enviaron al modelo.

| Modelo/prompt | Aciertos | Aceptaciones incorrectas | Abstenciones | Latencia media ms |
|---|---:|---:|---:|---:|
| gemini-3.8-flash/directo | 100% | 0 | 0 | 6738 |
| gemini-3.8-flash/rubrica_evidencia | 100% | 0 | 0 | 7218 |
| gemini-4-argon/directo | 100% | 0 | 0 | 6312 |
| gemini-4-argon/rubrica_evidencia | 100% | 0 | 0 | 6072 |

Llamadas registradas: 64. Reserva conservadora acumulada: USD 2.2737; no es el importe facturado.

## Decisión

Los cuatro tratamientos acertaron todos los casos. La prueba saturó y no permite elegir modelo ni justificar el costo de un prompt o panel más complejo. Demuestra funcionamiento de la evaluación sobre estos casos conocidos; no generalización científica, calibración psicométrica ni eficacia educativa. Se conserva un conjunto posterior más difícil, creado sin consultar estos resultados ni los prompts, para una medición separada.

El JSON conserva decisiones por caso, huellas de dataset/prompts, configuración, uso de tokens y latencia. Tras esta comparación el conjunto inicial no se considera ciego para ajustes futuros.
