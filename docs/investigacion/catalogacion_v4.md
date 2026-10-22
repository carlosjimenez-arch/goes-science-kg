# Catalogación disciplinar V4

Corte: 21 de octubre de 2026. Clasificar una disciplina permite filtrar y navegar; no verifica
la ciencia, los prerrequisitos, la demanda de una tarea ni su alineación internacional.

La ingesta conserva 1.020 filas: 384 de Bachillerato tienen asignatura explícita en el libro y
636 proceden de Ciencias integradas. Estas últimas necesitan decisiones nuevas; no se heredan las
etiquetas de V3 por posición, grado o semejanza superficial.

## Procedimiento

Dos lectores, `gemini-3.8-flash` y `gemini-4-argon`, reciben por separado el mismo lote de hasta 24
objetivos con grado, unidad, contenido, subcontenido e indicadores. No ven el dictamen del otro.
El payload no incluye fases, datos personales, credenciales ni campos reservados de evaluación.
Los alias numéricos del lote se resuelven a las identidades completas mediante código; no se pide
al modelo copiar hashes extensos. El conjunto de alias devuelto debe coincidir exactamente: omisiones,
duplicados o IDs ajenos invalidan el lote completo.

Los estados del lector son `en_alcance`, `fuera_alcance` e `insuficiente`; se admiten varias ciencias
cuando el aprendizaje las integra. Solo la coincidencia exacta de estado y conjunto de disciplinas
produce una clasificación automática. Una discrepancia conserva ambas lecturas y se abstiene.
La coincidencia de dos modelos del mismo proveedor no demuestra independencia estadística.

Se valida primero un lote piloto. Un fallo de transporte, contrato o identidad impide despachar el
resto. Un catálogo piloto nunca se publica como una generación completa. El materializador comprueba
versión, huella, todas las identidades y soporte de las decisiones en las dos lecturas.

## Experimento de formato

La primera implementación consumió intentos con JSON truncado en Flash. Se conservaron las reservas
y los fallos; no se convirtieron en clasificaciones. Acortar los IDs no bastó: un piloto Flash registró
4.081 tokens de salida con límite 4.096, sin JSON válido. Configurar `LOW` produjo contrato válido con
1.166 tokens y 8,69 segundos de llamada para ese lote. Argon reutilizó una respuesta validada en caché.
El resultado parcial tiene 384 filas declaradas, 23 coincidencias y 613 abstenciones; 612 de ellas no
recibieron las dos lecturas y una corresponde a discrepancia. No se usa ese piloto para afirmar calidad
del catálogo completo.

La documentación oficial admite `LOW`, `MEDIUM` y `HIGH` para estos modelos; `MINIMAL` no está soportado.
La recomendación de razonamiento bajo incluye clasificación y extracción de metadatos:
[guía Flash](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-3-8-flash),
[guía Argon](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/guides/gemini-4-argon?hl=en).
La medición anterior es un piloto de formato y eficiencia, no una ablación de exactitud científica.

## Contabilidad y autorización

Antes de la continuación, `catalogacion-v4-20261021` conservaba 24 reservas por USD 2,4163425: 12 completadas,
10 fallidas y dos interrumpidas sin confirmación del proveedor. Las dos últimas siguen reservadas;
no se supone que una interrupción evitó la facturación. La reserva no es el importe facturado.
El uso de tokens se registra también cuando la respuesta llega pero falla el contrato.

La revisión automática rechazó ampliar esta ejecución a 78 intentos porque la autorización explícita
disponible identificaba V3 y las consultas del experimento de embeddings. Se solicitó autorización
concreta para las 636 filas V4, proyecto institucional `g-edu-lxp-xai-dev-prj-976d`, región `global`,
ambos modelos y el mismo techo acumulado de USD 8. El usuario respondió «Autorizo» el 21 de octubre
de 2026. La continuación está autorizada con hasta 52 intentos nuevos y 76 acumulados: se aplica
el límite más estrecho del plan, dentro del techo inicialmente solicitado de 78.
El alcance no incluye otros workflows de modelos. La evidencia de autorización y huella del plan
se conserva en `data/producto/V4/autorizacion_catalogacion_20261021.json`.

La continuación autorizada terminó en 256,857 s: 52 intentos nuevos, 51 completados y un error 504
de Argon, sin reintento. Reservó USD 5,194618 adicionales. El total de esa ejecución es 76 intentos y
USD 7,6109605 reservados: 63 completados, 11 fallidos y las dos reservas interrumpidas previas.
No se reinició el ledger ni se consumieron los límites de otros workflows.

| Estado de fila | Cantidad |
|---|---:|
| Asignatura declarada en Bachillerato | 384 |
| Coincidencia automática entre los lectores | 561 |
| Abstención | 68 |
| Fuera de alcance de las cuatro ciencias | 7 |
| Total preservado | 1.020 |

Hay 65 filas multidisciplinares. De las 636 filas integradas, 612 tienen ambas lecturas; 24 conservan
una sola por el 504. Las abstenciones se distribuyen en 24 por ese fallo y 44 por discrepancia o
insuficiencia. «Catálogo completo» significa que cada fila conserva un estado y que se intentaron todos
los lotes; no significa que todas las filas tengan disciplina aceptada ni que la clasificación sea exacta.
[Resultados por grado, huellas y consumo](resultados_catalogacion_v4.json).

El catálogo se materializó en una publicación `producto-2` y pasó `producto validar`, 133 pruebas focales
y la [verificación real del runtime](verificacion_runtime_v4.json), con cero llamadas adicionales para
publicar o consultar. El explorador se regeneró con el catálogo completo; el grafo V3 no se modificó.

El plan sin red y el piloto son reproducibles mediante `gskg producto catalogar` y
`gskg producto catalogar --piloto`; añadir `--ejecutar` realiza solicitudes remotas y requiere que el
payload y los límites estén autorizados. Reutilizar `--ejecucion` conserva gastos anteriores.

## Límites y siguiente comprobación

Después de catalogar deben medirse recuperación por grado, localizadores y celdas, conservando en el
denominador lo no recuperado. El reservado V4 tiene 19 consultas; no satisface el mínimo predeclarado de
20 para seleccionar un recuperador experimental. El baseline continúa hasta que exista evidencia suficiente.
La [regresión local posterior](resultados_baseline_v4_catalogado.md) ejecutó esas mismas 19 consultas
tres veces, sin cambiar ranking ni prompts. Registra mejor disponibilidad global, pero conserva fallos
y una regresión en décimo. No constituye una nueva prueba ciega ni un resultado de eficacia educativa.
Las alertas científicas de la malla son independientes de la etiqueta disciplinar y bloquean la generación
de propuestas cuando sus filas forman parte del contexto seleccionado.
