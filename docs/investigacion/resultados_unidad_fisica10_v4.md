# Ejecución real de la unidad de Física 10.º

Fecha: 21 de octubre de 2026. Se ejecutaron las ocho sesiones propuestas de `1. La física como ciencia`
sobre la publicación V4 con catálogo completo. Cuatro obtuvieron respaldo automático y cuatro quedaron
en abstención. Este resultado no cierra la reconstrucción del producto ni acredita la unidad completa.

La autorización posterior del usuario fue «Adelante con lo pendiente hasta cerrar o finalizar el
proyecto». Su [recibo local](../../data/producto/unidades/fisica-10-v4-catalogada/autorizacion_generacion_20261021.json)
fija el plan y el paquete por SHA, proyecto `g-edu-lxp-xai-dev-prj-976d`, región `global`, modelos
`gemini-3.8-flash` y `gemini-4-argon`, máximo 64 intentos y USD 8 nuevos. Se conservó un único contador
`unidad-fisica10-v4-20261021`, incluyendo la llamada fallida. No se usó ninguna ampliación de Matemáticas.

## Resultado y consumo

| Sesión propuesta | Desempeño | Resultado |
|---|---|---|
| 1 | Preguntas, variables, hipótesis y predicciones | Respaldo automático |
| 2 | Diseños experimentales y control de variables | Respaldo automático |
| 3 | Dispersión, ajuste lineal e interpretación | Abstención |
| 4 | Linealización y validez del modelo | Respaldo automático |
| 5 | Análisis dimensional y conversiones | Respaldo automático |
| 6 | Representación y operaciones gráficas con vectores | Abstención |
| 7 | Operaciones vectoriales con leyes del seno y coseno | Abstención |
| 8 | Componentes y operaciones vectoriales | Abstención por fallo de redacción |

Se registraron **58 intentos: 57 completados y uno fallido**. La reserva acumulada es **USD 7,4261195**;
es una cota contable y no un importe facturado. El tiempo del orquestador fue 594,81 segundos, aproximadamente
9 minutos y 55 segundos. Quedan seis intentos y USD 0,5738805 dentro de ese límite; no se consumieron
automáticamente para volver a intentar los terminales rechazados.

Los resultados incluyen un máximo de una reparación por sesión y revisión posterior por ciencia,
psicopedagogía y adversarial. El JSON y Markdown conservan las ocho filas originales, decisiones,
fuentes y abstenciones; sólo presentan actividades respaldadas como propuestas utilizables.

## Hallazgos que impiden dar la unidad por terminada

- En la sesión 3, el revisor adversarial objetó afirmaciones sin respaldo suficiente en los fragmentos
  citados y el uso de una pizarra ausente del contexto declarado. El juicio sobre los fragmentos necesita
  calibración: este resultado por sí solo no demuestra que todas sus objeciones sean correctas.
- En la sesión 6, dos revisores detectaron atribución institucional injustificada y omisión de resta y
  del método del paralelogramo requeridos por el objetivo. La reparación no resolvió el problema.
- En la sesión 7, psicopedagogía y adversarial rechazaron la viabilidad de medir discrepancias gráficas
  sin regla ni transportador y de completar todas las operaciones en 40 minutos sin calculadora.
- En la sesión 8, la segunda redacción no produjo JSON válido. El ledger conserva el intento fallido.
  La telemetría guardada no incluye `finish_reason`; no permite establecer la causa exacta del JSON inválido.

Los 40 minutos, papel/lápiz y conectividad sin confirmar son un escenario de preparación; no describen
recursos comprobados en una escuela. Debe resolverse explícitamente la relación entre objetivo, número
de sesiones y recursos, conservando el desempeño completo. No corresponde quitar exigencias del
currículo, rebajar el gate ni repetir dictámenes hasta obtener acuerdo. Un nuevo experimento debe fijar
antes su modificación, alcance, presupuesto y criterio de comparación; el resultado anterior permanece.

## Reanudación y reproducibilidad

La CLI real se volvió a ejecutar con `Vertex.generar` sustituido **sólo en memoria** por un puerto que
registra y rechaza cualquier intento de generación. Se conservaron configuración, código, publicación,
ID de ejecución y ledger. Recuperó los ocho terminales, mantuvo la cobertura 4/4 y consumió **cero
intentos y cero USD adicionales**, en 382,74 ms del orquestador. No se modificaron los originales de la
primera ejecución: la exportación de comprobación está en `data/producto/unidades/fisica-10-v4-reanudada/`.

- [Resultado verificable y huellas](resultados_unidad_fisica10_v4.json).
- [Comprobación local de reanudación](reanudacion_unidad_fisica10_v4.json).
- [Paquete ejecutado](../../data/producto/unidades/fisica-10-v4-catalogada/paquete.md).

El JSON de resultados también registra las huellas de 174 archivos de código, configuración pública,
dependencias y documentación capturados antes de cambios posteriores. La copia local está en
`data/operaciones/archivos_codigo/unidad-fisica10-v4-20261021.zip`, SHA-256
`91f770d6d470903b25e0d399025f8fb0be67f2d16c0e12e875416cd0a5981275`.
No contiene credenciales, `.env`, datos de estudiantes ni bases de operación. Archivar el código permite
identificar la ejecución; aún no acredita una instalación nueva desde ese archivo.

El consenso automático no prueba eficacia educativa, aprobación del MINED ni adecuación de todas las
sesiones al aula. Las pruebas de software y la reanudación acreditan controles y contabilidad; la mitad
de la unidad sigue sin respaldo y no se publica como completa.
