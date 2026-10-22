# Evaluación reservada de jueces

Fecha: 2026-10-21. Veinticuatro casos sintéticos plata creados sin consultar los prompts ni los resultados individuales del experimento inicial. Ocho aprobar, ocho rechazar y ocho abstenerse. Una evaluación por combinación, sin reajuste posterior de prompts.

| Modelo / prompt | Coincidencia esperada | Error ejecución | Abstenciones | Media ms |
|---|---:|---:|---:|---:|
| gemini-3.8-flash/directo | 66.7% | 0 | 0 | 7205 |
| gemini-3.8-flash/rubrica_evidencia | 70.8% | 0 | 1 | 8036 |
| gemini-4-argon/directo | 75.0% | 0 | 2 | 7661 |
| gemini-4-argon/rubrica_evidencia | 83.3% | 1 | 5 | 11428 |

La diferencia principal está en reconocer evidencia insuficiente: varios tratamientos rechazan afirmaciones que deberían dejar como indeterminadas. La rúbrica con Argon coincide en20/24 casos, incluido un fallo de ejecución en el denominador. No se elimina ese fallo para mejorar la cifra.

Ningún tratamiento aprobó los errores sembrados que llegó a evaluar; eso no prueba ausencia de aceptaciones incorrectas en otros casos. La suite tiene tamaño limitado, anotación sintética y no valida eficacia educativa. Además, los prompts de este experimento no son por sí mismos una validación integral del workflow curricular.

Se registraron 96 reservas y USD 3.4136 de reserva conservadora, no factura. Tokens y respuestas por caso están en el JSON. Tras esta medición el conjunto ya no puede tratarse como una nueva prueba ciega para ajustes posteriores.
