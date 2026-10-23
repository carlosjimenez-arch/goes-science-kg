# Física 10.º: escenario de sesenta minutos

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha: 21 de octubre de 2026. Se conservaron los ocho objetivos de la primera unidad V4 y se
declararon sesiones de sesenta minutos, regla, transportador, calculadora científica, pizarra,
marcador y trabajo sin conexión. Es un escenario propuesto: no establece carga oficial ni confirma
que una escuela dispone de estos recursos. Siete sesiones obtuvieron respaldo y una quedó en abstención.

| Sesión | Objetivo | Estado |
|---|---|---|
| 1 | Preguntas, variables, hipótesis y predicciones | Respaldada |
| 2 | Diseño experimental y control | Respaldada |
| 3 | Dispersión y ajuste lineal | Respaldada |
| 4 | Linealización y validez | Respaldada |
| 5 | Análisis dimensional y conversiones | Respaldada |
| 6 | Operaciones gráficas con vectores | Respaldada |
| 7 | Operaciones mediante leyes del seno y coseno | Abstención psicopedagógica |
| 8 | Componentes vectoriales | Respaldada |

La séptima propuesta dedica los sesenta minutos a los pasos y deja fuera la comprobación individual.
El psicopedagogo también objetó la carga de hacer trazado a escala, suma, resta, leyes trigonométricas
y discrepancias en ese tiempo. Ciencia y adversarial aprobaron, pero el gate conservó el veto. No se
vuelve a votar este mismo contexto ni se elimina una exigencia curricular para aprobarlo.

El ensayo anterior de cuarenta minutos conserva cuatro respaldos y cuatro abstenciones. La diferencia
es descriptiva: cambian conjuntamente tiempo, materiales, lectura primaria y límite de salida; no
identifica qué cambio causó los nuevos estados ni mide eficacia de aprendizaje.

## Incidente y contabilidad

La primera ejecución no recibió propuestas ni dictámenes: dieciséis reservas terminaron en
`TransportError`, USD 1,526286. Se comprobó después el acceso ADC institucional y se ejecutó una única
recuperación de transporte con el mismo ID `unidad-fisica10-60min-20261021`, ledger y límites originales.
Los checkpoints y el archivo inicial permanecen intactos. Otro fallo de transporte habría detenido
el resto de la recuperación; no se admiten recuperaciones de votos o propuestas ya recibidos.

La recuperación completó 48 llamadas y reservó USD 8,991638. El total acumulado es **64 intentos y
USD 10,517924**, dentro del techo 64/USD 16; no quedan intentos en ese protocolo. Las reservas son
cotas conservadoras, no factura. Los fallos sin telemetría no se declaran gratuitos. La recuperación
tardó 517.045 ms, aproximadamente ocho minutos y 37 segundos.

La comprobación con `Vertex.generar` prohibido sólo en memoria reutilizó ocho terminales, mantuvo el
resultado 7/1 y consumió cero intentos y cero USD adicionales en 79,65 ms del orquestador.

- [Resultados, consumo y huellas](resultados_unidad60_20261021.json).
- [Reanudación sin generación](reanudacion_unidad60_20261021.json).
- [Incidente y protocolo de recuperación](incidente_transporte_unidad60_20261021.json).
- [Paquete con fuentes y actividades](../../data/producto/unidades/fisica-10-60min-recuperada/paquete.md).

El código original y el de recuperación tienen archivos ZIP y SHA distintos en
`data/operaciones/archivos_codigo/`. La recuperación fija además su propio hash de protocolo. Se
preserva la configuración utilizada; una modificación incompatible exige otro protocolo explícito.
La unidad de sesenta minutos sigue incompleta y no acredita aprobación del MINED.
