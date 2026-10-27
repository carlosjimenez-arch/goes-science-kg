# Revisión científica y pedagógica de las preparaciones finales

La entrega V3 del 26 de octubre de 2026 conserva 1.020 objetivos, 108 unidades y los once Excel
finales. Se materializó una edición docente derivada, se revisó desde cuatro perspectivas y se
publicaron los pendientes explícitos. **El proyecto completo aún no está cerrado**: la entrega técnica
de preparaciones se distingue de resolver sus observaciones y de producir guiones completos.

## Resultado y alcance

| Tipo | Cuatro lecturas favorables | Pendientes | Total |
|---|---:|---:|---:|
| Objetivo | 1.012 | 8 | 1.020 |
| Unidad | 101 | 7 | 108 |
| Total | 1.113 | 15 | 1.128 |

La biblioteca seleccionada es `2a5d347fa6bf9ddb579404741992ff7d3fc047f188b204f4bfbba9054bd6c4d2`,
`version_contenido: preparacion-malla-final-3`. Contiene 4.892 actividades efectivas y 14 casos
trabajados, uno por grupo de grado/asignatura. Son preparaciones con tareas, criterios, apoyos y
aplicación, **sin guion cronometrado ni desempeño observado**. Las etiquetas E/D/I y las tres macros
son una organización local; no acreditan niveles PISA, homologación internacional ni desarrollo de
habilidades por el solo hecho de aparecer en el documento.

`original`, `didactica` y `didactica_unidad` conservan los antecedentes. Las instrucciones efectivas
están en `edicion_docente`; los votos, hashes y pendientes en `revision_docente`. El Markdown muestra
la edición efectiva. Los JSON conservan el original para auditarlo, aunque contenga una actividad
reemplazada; no debe usarse como instrucción vigente. No se trasladan votos entre versiones.

## Fila completada sin alterar el original

La fila de 3.º «2.5. Experimentación con los métodos de separación de mezclas» tiene el ID
`CURRICULO:V4:135f86dc46b2f3a3cb4936d1b3cb1c4942e7e183fbf3a57189d73344ad907177`.
Las cuatro fases, el indicador y el producto originales continúan vacíos. La capa derivada recupera
el indicador 2.5 del programa MINED, página PDF 48, y propone cinco actividades y criterios propios.
**Pasó las cuatro lecturas de la segunda ronda**.

La propuesta anticipa, modela, diseña y ejecuta separación por tamaño y filtración de sólidos
insolubles; registra pérdidas y contrasta afirmaciones. Usa materiales provistos por la escuela,
papel de mayor tamaño que la grava limpia, agua fría del grifo y supervisión. No usa agua de ríos,
calor, vidrio ni ingestión. Distingue transparencia de potabilidad y análisis documental de práctica
real. Si faltan recursos, la competencia práctica queda pendiente; no se inventan observaciones.

Se conserva completa la guía metodológica MINED de 3.º, tomo 1: 193 páginas, 73.438.268 bytes,
SHA-256 `414613de33ab29f6bfb4fc87deffd8efe4028e911f6b129a9ceacf35d66f6499`.
Las páginas PDF 87–94 se comprueban por extracción literal y hash antes de preparar y compilar;
las instrucciones de separación están en las páginas 93–94. Configuración:
`config/completacion_mezclas_ciencias.yaml`.
[Programa MINED](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/1.%20Programas%20de%20estudio/Programas%20de%20estudio_Ciencia%20y%20Tecnolog%C3%ADa_2.%C2%B0%20a%206.%C2%B0%20grados.pdf),
[guía metodológica](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/guias/Gu%C3%ADa%20metodol%C3%B3gica%203.%C2%B0%20grado%2C%20tomo%201.pdf).

## Correcciones y transposición didáctica

La primera revisión dio lugar a 105 cambios de campos, con 14 conflictos conservados y 52 enmiendas
editoriales explícitas, vinculadas al hash de la edición inicial. Se corrigieron controles y límites
de PCR, orientación de la hebra molde, glándulas sudoríparas, ejes de la ley de Hooke, clasificación
de biomoléculas, fuerza magnética sobre electrones, GPS, palancas y condiciones de medida.

La derivación distingue datos sintéticos de datos medidos; una actividad documental no demuestra
experimentación. Se evitaron instrucciones con vidrio, calor, reactivos o electricidad sin un
protocolo verificable. Se corrigió la confusión de BTB con oxígeno disuelto, azul de metileno con
medición de oxígeno y velocidad catalítica con cambio del equilibrio. Las fuentes críticas incluyen
MINED, OpenStax, USGS, Harvard, UC Davis y CDC, con localizadores y naturaleza de captura explícitos.
No todas las páginas permitieron descarga HTTP: las seis citas breves de lectura web se identifican
como tales, con hash de su texto, sin fingir un hash del HTML original. Las tres citas USGS sí tienen
HTML conservado, texto visible, offsets y hash verificables.

Se conservan criterios observables por código, ayudas de lectura/representación, retroalimentación,
retirada gradual de apoyos y transferencia. Son propuestas de oportunidades de práctica; el sistema
no infiere errores, autonomía ni logro real de estudiantes. Una rúbrica documental no sustituye
observar la práctica cuando el objetivo exige medir o manipular.

## Método de revisión y controles

El flujo es finito: captura inmutable → cuatro lecturas → validación local → una reparación → cuatro
relecturas nuevas → compilación. Cinco lotes mantienen unidades y objetivos relacionados juntos:
227, 227, 226, 224 y 224 paquetes. Los perfiles son ciencia, currículo, psicopedagogía y adversarial.
No ven los votos de sus pares. Comparten proveedor y algunos modelos; **no se presupone independencia
estadística** ni se llama aprobación institucional a su resultado.

El contexto conserva tareas, criterios, apoyos, casos y textos de fuentes. La factorización es
reversible; los IDs extensos se sustituyen por alias. El modelo ve del original objetivo, contenido
y subcontenido, no todos los metadatos: las celdas completas se auditan aparte con los Excel.
La restricción de notación decimal exigió además un control editorial posterior; futuras capturas
deben incorporar explícitamente las restricciones operativas de notación. Hay 164 fuentes comunes
y 1.550 pasajes previos recuperados para 1.013 filas, verificados contra el corpus. Se reutilizan
documentos, no propuestas ni votos de la captura anterior. La selección lexical no prueba por sí sola
que una fuente respalde la afirmación: ésa es parte de la lectura.

Los modelos seleccionan fuente e índice; el código extrae las citas literalmente y obtiene el ancla
del campo exacto. Se rechazan índices inventados, campos protegidos, duplicados, ausencia de decisión
y aprobación con hallazgos materiales. Una aprobación psicopedagógica exige respaldo educativo.
La respuesta de transporte se valida otra vez localmente; un elemento inválido queda sin ese voto,
sin fabricar una abstención. Cada lectura se vincula con solicitud, mensaje, sistema, esquema,
modelo, razonamiento configurado, llamada real y SHA del texto recibido en el ledger.

La segunda ronda añade tres controles negativos por lote, separados de las clases y sin revelar su
clave: filtración que supuestamente vuelve potable agua salada; copia presentada como indagación;
y barreras de lectura usadas para excluir razonamientos correctos. Cada perfil debe localizar y
rechazar o abstenerse ante su control pertinente; fallarlo bloquea sus paquetes. **Los 20 controles
pertinentes (cinco por cada perfil) se superaron**. Las decisiones inválidas sobre otros controles
permanecen registradas. Es una prueba negativa pequeña, no una estimación poblacional de precisión,
sensibilidad o eficacia educativa.

Un paquete favorable exige cuatro lecturas válidas favorables sobre su edición exacta y controles
superados. Una unidad queda pendiente si cualquier objetivo está pendiente. Cambiar un campo
retira los votos actuales y conserva los anteriores como antecedente; no se heredan por parecido.

## Los 15 pendientes y el cierre

El [diagnóstico del 27 de octubre](CIERRE_INDICADORES_V4.md) distingue los códigos de indicador
de los números de objetivo, prepara la aclaración de metrología y calcula una campaña nueva.
No se consumieron llamadas ni se modificaron las bibliotecas publicadas. La ampliación de
4.000 a 4.010 llamadas sigue pendiente de autorización; el tope monetario actual alcanza.

Los ocho objetivos pendientes se distribuyen así:

- **Seis ediciones corregidas después de la relectura:** cinco ajustes sólo de separador decimal,
  verificados sin cambio de valor/precisión, y el producto de esterificación, que ahora declara
  expresamente datos sintéticos. Todos requieren cuatro lecturas nuevas del contenido corregido.
- **Un voto curricular inválido:** 9.º, fuerza eléctrica en una dimensión. Seleccionó una cita no
  verificable; no se fabricó una cita ni se reutilizó su aprobación.
- **Un veto de metrología discutible:** 5.º, magnitudes físicas. El lector confundió ser una magnitud
  derivada con no poder medirla directamente con un instrumento apropiado. Se conserva el veto y
  el estado pendiente; no se modificó física válida para satisfacerlo.

Las siete unidades pendientes dependen de esos objetivos; dos conservan también vetos propios de
la relectura. La lista completa, IDs, roles ausentes y hallazgos está en
`GET /api/v4/produccion/didactica/auditoria` y en `didactica/auditoria.json` de la biblioteca.

El arbitraje editorial de metrología se apoya en que NIST describe instrumentos volumétricos y su
lectura/calibración; que el volumen tenga unidad derivada no obliga a calcularlo siempre a partir
de longitudes. Es una inferencia editorial con fuentes, **no otro voto del modelo ni liberación del
paquete**. Se deben distinguir definición dimensional, procedimiento, calibración e incertidumbre.
[Instrumentos volumétricos, NIST HB 105-2](https://nvlpubs.nist.gov/nistpubs/hb/2022/NIST.HB.105-2e2021.pdf),
[ejemplos de mensurandos, NIST](https://www.nist.gov/system/files/documents/2021/07/06/TE%20measurands%20slides.pdf).

Para cerrar **esta entrega de preparaciones**, falta resolver esos ocho objetivos y revalidar sus
siete unidades, conservando los hashes y controles. Para cerrar **el producto completo**, falta
además finalizar la clasificación de las mallas finales y producir/revisar los guiones completos
sobre este insumo. Los 968 respaldos y 45 vetos/abstenciones de P11 pertenecen al insumo anterior;
no cierran los guiones de las mallas finales. Comprobar eficacia educativa requiere evidencia de uso
en aula; no existe en este repositorio y no se sustituye por pruebas de software.

## Presupuesto y trazabilidad del experimento

El máximo autorizado permanece en **4.000 invocaciones / USD 3.500 de reserva conservadora acumulada**.
Se partió de 3.941 / USD 2.912,1834795; esta revisión añadió 58 llamadas. El cierre conserva
**3.999 / USD 3.275,614266**: queda una llamada y USD 224,385734 de reserva. La reserva es una cota
operativa, no una factura. No se reembolsa por errores, se reinicia ni amplía el contador. No se
inicia otra ronda porque una llamada no cubre las cuatro perspectivas requeridas.

Los diagnósticos V4/V6/V7/V8 consumieron siete llamadas (cuatro rechazos 400, dos truncamientos y
una cita generada no literal). V9 consumió nueve: una lectura válida, cuatro 504 y cuatro solicitudes
y sus reservas ya en vuelo, interrumpidas sin respuesta recuperable. V10 consumió 42: 22 en la
primera ronda (20 lecturas y dos fallos técnicos) y 20 en la segunda. Los experimentos fallidos no
aportan votos favorables ni desaparecen del ledger.

V10 usa una sola solicitud SSE por intento, funciones automáticas deshabilitadas, salida de hasta
65.536 tokens, timeout explícito de 1.200 s y sin reintentos del SDK. Los errores de transporte
interrumpen trabajos en cola. El máximo permite una reparación y tres recuperaciones técnicas
para la campaña; se comprueba de nuevo el saldo antes de cada llamada nueva. La ejecución tiene
mutex de archivo y checkpoints exactos. Todas las relecturas usan razonamiento MEDIUM tras observar
que HIGH agotaba la salida. No se registra razonamiento interno; sí progreso de texto visible y uso.

Se recuperaron sin otra llamada una respuesta científica completa rechazada por la cota local de
citas (ampliada de 300 a 690 sin cambiar el esquema de transporte) y 168 decisiones completas de
un JSON científico truncado. No se inventaron sus 56 decisiones restantes. El estado `fallida`
original permanece en ambos casos. La segunda ronda vuelve a leer todo el contenido corregido.
Las 40 lecturas archivadas se vinculan al texto real del proveedor; una de las primeras es parcial.

El nuevo mínimo de continuidad está en
`data/revision_docente_20261026/continuidad_20261026_3999.json`, referenciado por SHA en
`config/presupuesto_clases_v4.json`. Un ledger anterior o alterado queda bloqueado.

## Bucket, API y recuperación

Los recibos principales son `config/materiales_produccion_ciencias.lock.json` y
`config/paquetes_produccion_ciencias.lock.json`; sus copias `_revision_v3.lock.json` fijan esta edición.
Los sufijos `_bases` y `_didactica_v2` preservan antecedentes. Las cargas son objetos nuevos con
precondición de generación cero, verificación actual de cuenta GOES, proyecto, UBLA y prevención
pública efectiva. Cada generación se relee y verifica por tamaño y SHA. No cambia IAM.

```bash
uv run gskg produccion descargar --destino /private/tmp/ciencias-preparaciones-v3
uv run gskg materiales restaurar \
  --recibo config/materiales_produccion_ciencias.lock.json \
  --destino data/materiales_produccion_v4
uv run gskg servir --puerto 8011
```

Las carpetas deben ser nuevas; conservar la biblioteca anterior antes de restaurar y reiniciar un
servidor existente. En macOS usar `/private/tmp` evita el enlace simbólico `/tmp`, rechazado por la
protección de rutas de la biblioteca. Cada ZIP tiene LEEME.md con enlaces comprobados a sus guías.

La API mantiene `/api/v4/produccion/materiales` para JSON, Markdown y blobs por SHA. El estado está en
`/api/v4/produccion/didactica/revision`; `/habilidades` filtra por código, macro, grado, asignatura,
`estado_revision` y `completacion_derivada`. El estado global con pendientes no se confunde con el
estado de los resultados filtrados. La consulta no invoca modelos. Alterar una biblioteca invalida
su lector con 503. `/api/v4/materiales` continúa mostrando el antecedente histórico.

El expediente incremental se fija en `config/expediente_revision_docente_ciencias.lock.json` y
conserva código, configuraciones, capturas, fuentes nuevas, diagnósticos pagados, lecturas, ledger
consistente y el nuevo punto mínimo. No duplica la biblioteca/ZIP publicados ni contiene credenciales.
Se restaura aparte del corpus previo:

```bash
uv run gskg artefactos restaurar config/expediente_revision_docente_ciencias.lock.json \
  --destino /private/tmp/ciencias-revision-v3-expediente
```

Para operar modelos en otra instalación, recuperar primero el corpus y después superponer desde el
expediente el ledger consistente, el punto mínimo y los contextos de esta revisión. No usar el ledger
de 3.941 del respaldo anterior. Servir o descargar preparaciones sólo necesita su biblioteca, sin
corpus ni ledger. El expediente registra un commit fuente; su propio recibo y la evidencia final de
restauración se versionan después, evitando una dependencia circular del archivo consigo mismo.

## Verificación de entrega

La entrega exige comparación de todas las celdas lógicas con Excel, once archivos fuente intactos,
regeneración de todos los votos desde sus selecciones, hash de contenido exacto, dependencias de
unidades, integridad del grafo y de los 14 ZIP, todos sus enlaces LEEME y cobertura única de 1.128
registros. Se comprueban además descarga independiente desde GCS, consultas HTTP reales, filtros,
contenido de mezclas y ausencia de consumo en consulta/reanudación. Las pruebas de ingeniería no
convierten un paquete pendiente en favorable ni demuestran eficacia de aula.

Resultado de la suite sobre la entrega V3: **1.675 pruebas aprobadas, sin omisiones, en 378,65 s**.
Ruff pasó en `src` y `tests`. Las pruebas de artefactos usan la biblioteca publicada y verifican
los 1.128 originales, los votos reproducidos, el grafo y todos los enlaces de los ZIP. Se hicieron
26 consultas HTTP reales y se reanudaron 20 checkpoints sin nuevas invocaciones.

La [evidencia estructurada de entrega](verificacion_revision_docente_v3.json) fija los resultados
y referencias. La restauración independiente verificó 1.128 registros y 172 archivos de biblioteca,
2.312 archivos y 2.148 enlaces internos de los 14 ZIP, y los 655 archivos del expediente incremental.
Se comprobó además el descriptor remoto y el mínimo de continuidad de las 3.999 llamadas restauradas.
La copia consistente de SQLite puede tener otro SHA físico que el archivo fuente; sus 3.999 filas
se verifican individualmente con el punto mínimo y el SHA propio del inventario restaurado.

El expediente tiene 166.960.146 bytes comprimidos, SHA-256
`0d38c529ca987acf5d90fcf6ff17abb8ad090a36002d048f25f7c96ebdc697a4`, generación
`1793064052369724`, y fija el commit fuente `7065ec5b07b6db83b64b8df4b15d32d9d54a519f`.
El recibo, esta evidencia final y el aviso del corpus base se versionan después del archivo; no
están incluidos en él. Las evidencias individuales anteriores sí se encuentran en el expediente.
