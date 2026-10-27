# Cierre de los ocho indicadores · diagnóstico del 27 de octubre de 2026

Los **ocho paquetes siguen pendientes en la API y en GCS**. Se preparó una campaña nueva sin
consumir Vertex ni alterar las bibliotecas publicadas, los Excel o el presupuesto autorizado.
La propuesta editorial preparada no es una aprobación. [Resumen verificable](preflight_cierre_indicadores_v4.json).

## Diagnóstico individual

Los números siguientes son los códigos de **indicador**, que pueden diferir del número del objetivo.
Los IDs completos y su relación con las filas están fijados en la captura de preparación.

| Grado y asignatura | Indicador | Qué falta | Acción preparada |
| --- | --- | --- | --- |
| 5.º Ciencias | 1.1, medición | Veto adversarial sobre magnitudes derivadas; la consigna necesita mayor precisión instrumental. | Aclarar lectura de escalas, cálculo, limitaciones e instrumentos escolares; cuatro lecturas nuevas. |
| 8.º Ciencias | 1.11, movimiento circular | La corrección de separador decimal dejó sin vigencia los votos anteriores. | Revisar la edición publicada, sin trasladar los votos antiguos. |
| 8.º Ciencias | 1.12, impulso | Igual: cambio de notación, con valor y precisión conservados. | Cuatro lecturas nuevas de la edición exacta. |
| 9.º Ciencias | 1.8, Torricelli | Igual: cambio de notación después de la relectura. | Cuatro lecturas nuevas de la edición exacta. |
| 9.º Ciencias | 6.3, fuerza eléctrica | El lector curricular seleccionó `R0116`, inexistente en el banco de esa respuesta. | Revisión con fuentes recuperadas y referencias validadas localmente; no corregir el ID por conjetura. |
| 10.º Física | 2.8, proyectiles | Cambio de notación posterior a los votos. | Cuatro lecturas nuevas de la edición exacta. |
| 11.º Física | 6.5, efecto fotoeléctrico | Cambio de notación posterior a los votos. | Cuatro lecturas nuevas de la edición exacta. |
| 11.º Química | 9.5, esterificación e hidrólisis | El producto corregido declara datos sintéticos; faltan votos sobre ese texto nuevo. | Revisar la distinción entre análisis de un modelo y síntesis efectivamente realizada. |

Además hay **siete unidades pendientes**, dos con vetos propios. El contexto nuevo incluye sus
**63 objetivos completos**, de los cuales ocho son los pendientes anteriores y 55 aportan contexto
de unidad. Son **70 registros reales**, más **tres controles negativos sintéticos** que nunca se
publican como material docente. Si aparece un hallazgo nuevo en esos 55 objetivos, se registra;
la cota de gasto no garantiza que todos terminen aprobados.

## Propuesta de metrología y contexto

La enmienda de 5.º cambia seis campos de la capa docente. Distingue la definición dimensional de
la elección del procedimiento: en la tarea se lee volumen con una probeta apropiada y se calcula
el área rectangular a partir de longitudes. Evita la generalización de que una magnitud derivada
siempre se obtiene por cálculo. Distingue mediciones propias, etiquetas, fotografías y datos
sintéticos; si faltan instrumentos, la ejecución práctica sigue pendiente. Prevé agua a temperatura
ambiente, probeta plástica, supervisión y ausencia de ingestión.

Es una inferencia editorial a partir de fuentes primarias, no un voto ni una norma escolar nueva:

- [NIST HB 105-2](https://nvlpubs.nist.gov/nistpubs/hb/2022/NIST.HB.105-2e2021.pdf),
  páginas **10 y 13 del PDF**, sobre volumen contenido, graduaciones y unidades.
- [BIPM, SI Brochure, 9.ª edición, versión 4.01](https://www.bipm.org/documents/20126/41483022/SI-Brochure-9.pdf),
  páginas **134 y 135 del PDF** —numeración impresa 132 y 133— sobre dimensiones y unidades derivadas.

Se descargaron y verificaron los PDF y se inspeccionaron esas páginas. Los SHA y fragmentos
literales quedan en la captura. Las especificaciones industriales del NIST no se transfieren como
protocolo escolar. El contexto mantiene, por separado y literalmente, la notación exigida por las
mallas finales para cada uno de los 63 objetivos. No convierte esa preferencia curricular en una
prohibición universal del SI sobre otros separadores decimales.

El banco contiene **293 fuentes**, con 181 comunes y los pasajes recuperados para las filas elegidas,
además de las cuatro páginas de metrología incluidas en ese total. El mensaje factorizado ocupa
**750.983 bytes** y mantiene el contenido docente completo. Las claves de los controles, los votos
anteriores y los identificadores instrumentales largos quedan fuera del mensaje del lector.

## Presupuesto: propuesta pendiente de autorización

| Concepto | Valor |
| --- | ---: |
| Límite acumulado vigente | 4.000 llamadas / USD 3.500 de reserva |
| Consumo acumulado verificado | 3.999 llamadas / USD 3.275,614266 |
| Saldo vigente | 1 llamada / USD 224,385734 |
| Primera pasada, cuatro perfiles en un lote | 4 llamadas |
| Relectura después de una reparación como máximo | 4 llamadas |
| Recuperaciones técnicas como máximo | 3 llamadas |
| Cota total de la campaña | **11 llamadas nuevas / USD 43,6629726** |
| Máximo acumulado propuesto | **4.010 llamadas** |
| Ampliación respecto del máximo autorizado | **10 llamadas** |
| Reserva acumulada máxima prevista | USD 3.319,2772386 |

**No se necesita aumentar el tope monetario de USD 3.500.** Sí se necesita autorización para ampliar
las llamadas: el saldo actual no cubre siquiera las cuatro iniciales. El mínimo aritmético de
primera pasada sería 4.003, pero no cubre una reparación ni la recuperación técnica acotada.
El preflight vigente devuelve `safe_to_start: false` y la ejecución se bloquea antes de construir
el cliente de Vertex. La propuesta mantiene la misma cuenta GOES, proyecto, ledger y modelos;
no reinicia las 3.999 llamadas ni devuelve reservas por fallos.

Destino previsto: cuenta `carlos.jimenez@goes.gob.sv`, proyecto
`g-edu-lxp-xai-dev-prj-976d`, región `global`; `gemini-4-argon` para ciencia, currículo y adversarial,
y `gemini-3.8-flash` para psicopedagogía. El futuro respaldo mantiene
`gs://goes-ai-kg-artefactos/ciencias/v4/`, creando objetos nuevos y comprobando su protección.

La cota se calcula con las tarifas configuradas, el tamaño de entrada en bytes como cota conservadora
y 65.536 tokens máximos de salida por lectura. Incluye crecimiento máximo del contexto reparado del
5 %. La reserva es un control operativo, no una factura. Se conservan los límites de una reparación,
una recuperación por lectura y tres recuperaciones globales; ningún permiso habilita reintentos
ilimitados. Tres perfiles comparten modelo: las cuatro lecturas no constituyen independencia
estadística ni aprobación institucional.

## Preparación reproducible, sin gasto

```bash
uv run gskg indicadores cierre-preparar \
  --destino data/cierre_indicadores_20261027/campana_nueva \
  --referencias data/cierre_indicadores_20261027/fuentes
```

El destino debe ser nuevo. La captura `campana_p1` contiene `candidato_1.json`, `ronda_1.json`,
`enmiendas_preparadas.json`, `referencias_verificadas.json`, `indicadores_pendientes.json` y
`preflight.json`. La configuración versionada está en `config/cierre_indicadores_ciencias.yaml`;
fija las dos bibliotecas de origen y el SHA de la edición de medición. Los datos privados y PDF
siguen fuera de Git. El resumen versionado fija los SHA de los seis archivos preparados.

La preparación sólo produce una candidatura nueva y su cálculo de gasto. No cambia el límite de
`config/presupuesto_clases_v4.json` ni ejecuta la revisión. El ledger conserva el SHA
`c54ef34bd4378a143e1ad217b4ee014b758b8c5f75a12ea503908f2c2ac561d1`.

Validación del diagnóstico: **62 pruebas focales aprobadas**, Ruff en `src` y `tests` y comprobación
de la CLI. Se reprodujeron los cinco JSON de candidatura, contexto y evidencias con bytes idénticos;
el preflight se recalculó con el saldo vigente. Se probó el rechazo antes de construir el cliente
de Vertex, la ocultación de claves de control, la notación literal y la conservación de originales
e historial. Son verificaciones del flujo; todavía no son resultados de la nueva revisión.

## Condiciones de cierre y publicación posterior

Tras una autorización explícita se recalcula el preflight y se conservan esta captura y el recibo
de autorización como antecedentes. Cada registro liberado debe tener cuatro lecturas favorables
válidas sobre su edición exacta, citas verificables y controles negativos superados. No se retira
un veto para conseguir un resultado verde. Las siete unidades deben pasar su revisión propia y
la de todos sus objetivos. Una reparación exige otra captura y nuevas lecturas del texto cambiado.

La ejecución de rondas existente conserva checkpoints y presupuesto. La adaptación de reparación
y publicación para esta campaña debe trabajar desde V3: los comandos de reparación históricos
parten de V2 y **no deben reutilizarse directamente**. Hay que separar controles sintéticos, mantener
originales, historial y vínculos al proveedor, y fusionar sólo los resultados validados.

Después se recompilan la biblioteca de preparaciones y los 1.019 paquetes por indicador, se
verifican cobertura, archivos, estados y respuestas de API; se publican objetos nuevos en el mismo
bucket privado, se releen por generación y se prueban descargas independientes. Hasta entonces
las bibliotecas publicadas conservan los ocho contextos pendientes. El reagrupamiento por indicador
continúa sin revisión específica: no se inventan votos sobre la agrupación.

Este hito cierra los pendientes de **las preparaciones entregadas**. La clasificación final y la
producción/revisión de guiones completos sobre las mallas finales siguen siendo otro alcance.
No acredita eficacia en aula ni sustituye la aprobación pedagógica institucional.
