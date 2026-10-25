# Guiones completos de Ciencias V4

## Entrega publicada · 25 de octubre de 2026

**994 guiones de clase y 108 guiones de unidad publicados**, con 19 objetivos declarados sin guion
liberado. Entrega `9d949257f6752960333349a56cfad4f2da855041f45a97470655226b06ed493d`
(`config/clases_ciencias.lock.json`) y biblioteca ampliada `5b80b556…` con 3.969 registros
(`config/materiales_ciencias.lock.json`), ambas en el bucket y restauradas desde él.

| Paso | Resultado |
|---|---|
| Autorización | El usuario amplió el tope acumulado a 4.400 llamadas con USD 3.500 sin cambio (recibo literal anclado por SHA en `config/presupuesto_clases_v4.json`) |
| R21 (plan congelado de 45 pendientes) | 283 llamadas: 34 respaldados, 6 vetos y 5 abstenciones |
| R22 (12: los 11 negativos y el caso estelar bloqueado por revisión directa) | 70 llamadas: 8 respaldados, 3 vetos y 1 abstención |
| Consumo acumulado | 4.294 llamadas y USD 3.219,5365 de reserva; contador sin reinicio |
| Revisión directa de las 41 versiones recuperadas | 26 aprobadas y 15 bloqueadas por defectos materiales |
| Compilación | 409 resultados cotejados con el ledger; ningún guion liberado tiene un bloqueo conocido |

La revisión directa la hicieron agentes revisores independientes de sólo lectura, que recalcularon cifras y
contrastaron afirmaciones con las fuentes (`data/clases_v4/auditoria_contenido/revision_directa_*`). Los 15
bloqueos incluyen datos reales erróneos (temperatura a 100 km, «694 veces» la distancia a Plutón), una cita
oficial inventada, afirmaciones falsas heredadas literalmente de OpenStax convertidas en criterio evaluado
(sin PSII no hay ATP, la codeína como anestésico local) y cláusulas del objetivo sin enseñar. **El respaldo de
cuatro lectores automáticos no basta para liberar sin revisión:** en esta cohorte de recuperación el 37 % tenía
un defecto material. Cada guion liberado declara `revision_directa`: «aprobada» (26) o «no_realizada» (968,
respaldados por cuatro lectores en P5–P11; la muestra de 32 y sus seguimientos están en el expediente).

Los 19 objetivos sin guion conservan su preparación por objetivo, su último resultado y su motivo; su unidad se
marca `completa: false`. Una tercera ronda no cabía en el tope autorizado (quedan 106 llamadas).

Dos correcciones de ingeniería, en módulos sin huella de protocolo: la auditoría admite la familia
`clases-p11-recuperacion-rNN` y verifica el parche del editor con el esquema que envía el código P11 (el
esquema archivado en su ZIP difiere; la clave recalculada coincide con el ledger). La compilación acepta
objetivos declarados sin guion, siempre anclados a su resultado real o a la revisión que los bloqueó.

## Estado de la ampliación al 23 de octubre (antecedente)

El alcance son los 1.013 objetivos de Ciencias del snapshot producto-4, agrupados en 108 unidades.
Los siete registros fuera de Ciencias se conservan fuera de generación. El corte de la campaña P11
del 23 de octubre registra 968 guiones respaldados automáticamente, 27 con veto y 18 con abstención,
sin objetivos pendientes de primera generación. El denominador permanece en 1.013. El inventario privado
`data/clases_v4/auditoria_contenido/inventario_trabajo.json` fija el orden de versiones y conserva el
último resultado incluso si es desfavorable; no elige retrospectivamente el voto más favorable.

Se completó la lectura directa de los 32 casos de la muestra. Los hallazgos conocidos bloquean las
versiones afectadas aunque tengan cuatro votos favorables. La entrega completa exige cobertura
exacta, resolución de todos los hallazgos y cuatro lecturas reales sobre cada versión seleccionada.
No se presenta la biblioteca de preparaciones ya publicada como esta entrega nueva.

La biblioteca anterior contiene 2.867 registros y 316 originales. Sus 1.013 `paquete_objetivo` y
108 `paquete_unidad` son preparaciones curriculares. Las clases nuevas usan los tipos `guion_clase`
y `guion_unidad`, conservando los materiales anteriores, sus revisiones y sus pendientes históricos.

## Contenido utilizable en clase

Cada objetivo aceptado se conserva literalmente y tiene una propuesta de una a tres sesiones de
60 minutos. El guion desarrolla las cinco fases, acciones docentes y estudiantiles, evidencia
observable, explicación científica con citas, tareas completas con datos o instrucciones de dibujo,
soluciones, rúbricas de tres niveles, apoyos, retroalimentación y seguridad.

La hoja de estudiante contiene las tareas y la atribución; el documento docente agrega el
solucionario y las revisiones. Se distingue un dato simulado de una observación real. La duración
y los recursos son propuestas condicionadas. Una representación en papel no acredita una destreza
instrumental cuando falta el instrumento. No se afirma aprobación institucional ni eficacia en aula.
Las unidades agrupan guiones en orden documental; no declaran una carga oficial ni una secuencia
pedagógica nueva por el hecho de reunirlos.

## Fuentes y alcance de la revisión

Se congelaron 890 módulos oficiales CNXML y 27.736 párrafos de cuatro libros de OpenStax / Rice
University: Biology 2e, Chemistry 2e, College Physics 2e y Astronomy 2e. Se conservan commit, URL,
SHA, localizador XML, colecciones y licencias. MathML se conserva en la evidencia. Las consultas
bilingües sirven para recuperar texto; no crean hechos ni equivalencias entre grados.

El contenido adaptado de esas fuentes conserva atribución y CC BY-NC-SA 4.0. Esta condición no se
extiende al código ni a las mallas originales del MINED. El corpus y sus fuentes completas están
fuera de Git. El manifest privado es `data/referencias_clases_2026/manifest.json`.

Los complementos conservan bytes originales y extractos literales con rangos de bytes, manifest,
SHA, versión, URL y atribución. El registro adicional fija también el código del extractor y el
corpus anterior; no sustituye los párrafos usados en ejecuciones históricas. Incluye la escala
ICS 2026/06 y texto institucional USDA sobre oscurecimiento de alimentos. Sus licencias propias
se conservan; no se extiende automáticamente la licencia de OpenStax a las fuentes adicionales.
El registro `data/referencias_complementarias_clases/registro.json` permite reconstruir cada
versión anterior por huella y reunir sus originales. Se añadieron leyendas, tablas y descripciones
accesibles de los mismos módulos CNXML; una descripción no acredita una observación.
Los extractos NPS sirven para jerarquía y eventos geológicos; las edades
numéricas se atribuyen a la edición correspondiente y se distinguen de los límites ICS actuales.

Un insumo histórico de dengue conserva tres notificaciones semanales de sospechas de MINSAL
de 2022, fechas y recibos literales breves. El servidor no permitió descargar los PDF originales;
la evidencia disponible es su vista textual primaria indexada. La tabla declara esa limitación,
no presenta casos confirmados ni estadísticas actuales y no demuestra causalidad con las lluvias.
La compilación comprueba semana, fechas, indicador, valores y correspondencia exacta con las filas.

| Revisión | Criterios |
|---|---|
| Ciencia | Exactitud, afirmaciones sustentadas y soluciones correctas |
| Currículo | Objetivo conservado, evaluación alineada y guion completo |
| Psicopedagogía | Adecuación al grado, tiempos y apoyos/accesibilidad |
| Adversarial | Seguridad, datos/fuentes y recursos factibles |

Los cuatro lectores reciben el mismo borrador y contexto; no reciben los votos de los demás.
Todos los criterios deben ser `si`. Las revisiones de la propuesta curricular anterior no son
votos de la clase. Compartir proveedor o modelo no da independencia estadística.
Los primeros controles detectaron errores introducidos a propósito. Los controles P6/P7 también
detectaron cuatro defectos concretos de contenido conservando dos casos sin defecto material.
Son controles de desarrollo conocidos, sin independencia respecto al diseño de los prompts;
no estiman precisión poblacional ni eficacia educativa.

## Auditoría del contenido y cierre de defectos

El plan privado `data/clases_v4/auditoria_contenido/plan.json` fija 32 casos con semilla 20261022:
dos por estrato de grado/asignatura y cuatro casos dirigidos. Es una muestra de desarrollo asistida
por Codex; no estima una tasa poblacional de precisión ni demuestra eficacia en aula. Se revisan
explicaciones, sesiones, datos de tareas, soluciones, apoyos y límites de ejecución.

Los hallazgos incluyen confundir concentración final de animales con movimiento dirigido,
carga iónica con número de oxidación y ácido carbónico con bicarbonato; también se comprobaron
conclusiones causales que excedían los datos. Se conserva el guion observado con su SHA. La
revisión no cambia sus cuatro dictámenes anteriores ni los presenta como una norma oficial.

La compilación completa exige los 32 casos revisados. Cada defecto necesita contenido distinto,
cuatro revisiones reales y una resolución que identifique el resultado, su SHA y los hallazgos
atendidos. Cambiar sólo el título, conservar el contenido señalado o cambiar después una versión
revisada bloquea la entrega. El expediente completo se incorpora al paquete descargable.
`seguimiento.json` conserva hallazgos adicionales sobre versiones corregidas y otros objetivos
revisados de forma dirigida. También retiene esas versiones aunque sus cuatro lectores anteriores
hayan sido positivos. Una corrección no se considera resuelta sólo por cambiar el texto.

La recuperación documental reforzada limita libros por disciplina, descarta preguntas aisladas y
combina la consulta completa con su concepto principal. Es un control de selección de contexto;
el puntaje léxico no demuestra que un pasaje respalde una afirmación. Ese respaldo se debe revisar.
El selector documental ofrece hasta dos decisiones; la campaña R4 se limitó a una por lote y
127 llamadas en total. Busca pasajes completos, devuelve sus identidades y declara lagunas.
Una segunda búsqueda requiere evidencia nueva. La conciliación R4 releyó las respuestas del ledger
sin llamadas adicionales: recuperó 210 selecciones y conservó 223 objetivos con lagunas. Una
referencia inválida se rechaza por fila y se conserva la respuesta original; no invalida las otras
filas ni convierte una abstención en una clase lista para impartir.

## Flujo y controles de ingeniería

`clases/` separa contratos, fuentes, consultas, preparaciones, proveedor, grafo, validación,
presupuesto, campaña, auditoría, compilación, lectura, ZIP y publicación. El grafo LangGraph tiene
redacción, cuatro lectores paralelos y consolidación por objetivo. Se permite una reparación por
lote, sólo de las filas pendientes. Un contenido sin cambios no recibe otra ronda de votos.

Los fallos de esquema de transporte, formato y truncamiento de los pilotos se conservan en P1–P4.
P5 conserva el guion y los dictámenes válidos cuando sólo falta un lector por fallo técnico y no
hay vetos ni fallos estructurales. Recupera únicamente los roles sin dictamen, una vez, con una
salida de hasta 32.768 tokens. Si existe un veto semántico se necesita otro contenido y las cuatro
revisiones. La cota toma el mayor coste entre ambos caminos y sigue limitada a dos rondas.
P8 añade un editor de formato únicamente cuando los defectos restantes son longitudes excesivas
en tres campos de tareas. El parche enumera exactamente los campos y conserva todo lo demás;
sustituye al segundo redactor y requiere cuatro lecturas nuevas del resultado exacto. No modifica
soluciones, datos o contenido silenciosamente ni habilita una tercera ronda. Un control real de
una llamada verificó el contrato del parche; sus textos no se publican como clases.
La prueba de ingeniería en Vertex completó dos casos sintéticos con cuatro llamadas reales;
el fallo inicial era simulado y no se repitieron votos válidos. Los casos no se publican como clases.
Los campos docentes admiten hasta 2.000 caracteres; la cota del lote sigue siendo 120.000 bytes.
Los errores de una fila se aíslan si el JSON está completo y sus identidades son exactas. No se
reconstruye JSON truncado ni se corrige silenciosamente la salida. Un borrador recuperado de un
fallo técnico debe coincidir con el antecedente fijado por SHA y carecer de dictámenes anteriores;
requiere sus cuatro lecturas. Se conserva también el texto rechazado.

La aritmética usa un AST con operaciones y funciones permitidas, sin evaluación de código.
El redondeo se expresa con `round`; la tolerancia máxima del control es 1e-6 relativo y una
tolerancia absoluta nunca puede ocultar una magnitud pequeña errónea. Se verifican también los
objetivos literales, tiempos, identidades y las fuentes asignadas a cada fila.

La compilación reconstruye los dictámenes y, además, vuelve a calcular la clave de cada revisión
con el prompt, contexto, borrador, esquema, modelo y parámetros congelados. Coteja la respuesta
real y su SHA en el ledger. Cambiar juntos el histórico y la etiqueta terminal no fabrica un voto.
El ZIP y la biblioteca conservan los expedientes, incluidos rechazos y abstenciones y las respuestas
crudas de los lectores. El ZIP incluye `INDICE.md` y enlaces relativos de unidad a hojas docentes
y de estudiante, además de comprobar que cada objetivo aparece exactamente en su unidad.

## Presupuesto y reanudación

Autorización del 22 de octubre: máximo acumulado de 4.000 invocaciones y USD 3.500 de reserva
conservadora. Las 668 llamadas anteriores y su reserva de USD 731,1485125 se mantienen. El recibo
literal es `data/operaciones/clases_v4_20261022/autorizacion.json`; la configuración versionada está
en `config/presupuesto_clases_v4.json`. Se comprueban las 668 filas históricas completas por hash
antes de usar el proveedor. No se admite un ledger vacío o reiniciado.

El preflight cubre dos rondas para todo lo pendiente; cada llamada hace una reserva atómica en
el mismo ledger. No hay reintentos del SDK. Los terminales se verifican y reutilizan sin gasto.
La reserva no es una factura de Google. El proyecto, identidad y modelos siguen siendo los
autorizados de GOES; no se incluyen datos de estudiantes ni credenciales.

El orden inicial está congelado en `data/clases_v4/protocolos/completo_p5.json`. Tras dos bloques
de 24, la continuación fija sólo los lotes aún sin terminal en `completo_p5_continuacion.json`,
con bloques de 96 para reducir esperas. El control cambia concurrencia entre bloques cerrados; no cambia
los modelos, el contenido, los checkpoints ni los dictámenes.

```bash
uv sync --python 3.13 --extra dev --extra motor --extra api
uv run gskg clases campana data/clases_v4/preparaciones \
  --plan data/clases_v4/protocolos/completo_p5_continuacion.json \
  --destino data/clases_v4/ejecuciones/completo_p5_continuacion \
  --control data/clases_v4/control_completo_p5_continuacion.json
# El comando anterior sólo calcula la cota. Añadir --confirmar ejecuta la autorización vigente.
```

Para un bloque concreto se usa `clases ejecutar` con `--plan` apuntando a su `protocolo.json`,
el mismo `--protocolo`, directorio y preparaciones. No se crean nombres nuevos para repetir votos.
Los logs están en `data/operaciones/clases_v4_20261022/` y conservan los estados VERDE, AMARILLO
y ROJO; la campaña diferencia lotes terminados de objetivos respaldados.
P1–P11 son protocolos del flujo de generación; el currículo sigue siendo V4. Los comentarios de
un juez no crean una norma institucional ni una equivalencia de grados sin una fuente oficial.

## Publicación y consumo

La publicación completa añadirá un recibo `config/clases_ciencias.lock.json` para el ZIP y actualizará
`config/materiales_ciencias.lock.json` para la biblioteca ampliada. Hasta que se verifique ese hito,
los comandos de descarga siguientes describen el contrato de entrega, no una publicación terminada.

```bash
# JSON, Markdown docente/estudiante, catálogo, fuentes y auditorías en un directorio nuevo:
uv run gskg clases descargar --destino data/descargas/clases-v4
# Biblioteca SQLite indexada para consumir mediante API, sin restaurar todo el corpus:
uv run gskg materiales restaurar
uv run gskg materiales validar
uv run gskg servir --puerto 8011
```

Los objetos estarán bajo `gs://goes-ai-kg-artefactos/ciencias/v4/clases/<entrega_id>/` y
`ciencias/v4/materiales/<biblioteca_id>/`. Se crean objetos nuevos y se relee cada generación.
Cada escritura verifica identidad, proyecto, UBLA y PAP efectiva; la heredada requiere enforced.
No se cambia IAM. La restauración verifica generación, SHA e inventario, y sólo habilita el
directorio cuando todos los archivos están verificados. Nunca sobrescribe una carpeta en servicio.

```http
GET /api/v4/materiales?tipo=guion_clase&grado=10
GET /api/v4/materiales?tipo=guion_unidad&grado=10
GET /api/v4/materiales/detalle/{id}
GET /api/v4/materiales/descarga/{id}?formato=md
GET /api/v4/materiales/descarga/{id}?formato=md&audiencia=estudiante
GET /api/v4/materiales/archivos/{sha256}
```

La hoja de estudiante requiere `guion_clase` y Markdown. Las peticiones no llaman a Vertex.
El respaldo final del corpus debe incluir el ledger actualizado y los checkpoints; restaurar un
respaldo anterior no recupera el consumo posterior. La biblioteca anterior sigue siendo histórica.

El respaldo completo admite una cota explícita de hasta 8 GiB sin comprimir, fijada en su recibo;
las entregas anteriores conservan su cota de 2 GiB. La migración de vínculos de presupuesto usa
copias verificadas y reversión, sin adjuntar todas las bases a una sola conexión SQLite. Se probaron
20 checkpoints, fallos de instalación e interrupciones; el ledger y los estados se conservan.

## Referencias técnicas

El ajuste del esquema conserva la validación local completa. Google documenta el límite de
complejidad de los esquemas y que algunos límites de cadenas no se aplican en la decodificación:
[salida estructurada](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output)
y [subconjunto de JSON Schema](https://ai.google.dev/gemini-api/docs/structured-output).
Licencias: [información oficial de OpenStax](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks).

## Verificación del flujo de lectura por capítulos

El piloto documental de cuatro objetivos obtuvo cuatro respaldos automáticos, pero la lectura
directa señaló tres casos con dimensiones ambiguas o afirmaciones específicas sin respaldo
en el contexto entregado. No se amplía ese piloto con base sólo en sus votos favorables.
Los cuatro expedientes, los hallazgos y las versiones señaladas permanecen en la auditoría.
La prueba completa de ingeniería pasó 1.581 casos (265,52 s); Ruff pasó sobre `src` y `tests`.
Estas comprobaciones no miden exactitud científica poblacional.

## Correcciones editoriales y contexto de trabajo

P9 introduce parches explícitos: SHA del antecedente, valores completos antes/después y motivo.
Conserva el objetivo literal y todas las partes sin cambio; no edita resultados ni dictámenes antiguos.
El candidato requiere cuatro lecturas nuevas y una resolución posterior de los hallazgos. El control
real de análisis dimensional obtuvo cuatro lecturas nuevas con cero redacciones de Vertex en la
primera ronda. La revisión directa comprobó SI, equivalencia comercial redondeada, datos simulados y
soluciones. No se declara eficacia en aula ni aprobación institucional.

P10 separa alertas, justificaciones y búsquedas históricas del contexto de los agentes. Mantiene íntegros
objetivo, indicador, criterios, apoyos, seguridad, datos contextualizados y pasajes científicos. El
historial sigue en la preparación inmutable. Las auditorías reconstruyen el contexto histórico de
P2–P9 y el contexto filtrado de P10; no recalculan votos antiguos con el contexto nuevo.

La lectura por capítulos tiene controles de desarrollo, no una validación de eficacia. El primer piloto
dio cuatro votos favorables por objetivo y la revisión directa encontró tres defectos; no se amplió
sobre esos votos. El experimento adicional de fundamentación acertó cinco de ocho controles conocidos
y dejó `safe_to_expand=false`, incluido un error no detectado de masa. No es un gate de liberación.
Las respuestas inválidas y el único intento documental incompleto se conservan. La conciliación de
frases de búsqueda recuperó una respuesta real del ledger sin nuevas llamadas ni supresión de datos.

El extractor de párrafos distingue `<p/>` de un párrafo abierto y conserva rangos literales verificables.
Las ampliaciones incorporan textos de Siyavula con licencia expresa y fuentes específicas de salud y
seguridad con su propia atribución; no se copian imágenes. Un pasaje de una fuente registrada también
puede contener errores: la revisión científica sigue siendo necesaria. El cargador comparte corpus
aditivos sólo tras verificar metadatos, rangos, bytes y manifests de todas las versiones; ante conflictos
reconstruye la colección separada. No se elimina evidencia histórica para ahorrar memoria.

## Fuentes ampliadas y revisión P11

P11 conserva el código del flujo por SHA y los contextos completos usados en cada voto. La curación
documental combina consultas, elimina redundancia y conserva pasajes enteros dentro de la cota;
el agrupador mide el contexto que reciben los agentes. Esos controles no acreditan suficiencia
científica. Una salida truncada no se reconstruye como si hubiera sido un guion válido. La edición
de una ronda tipada sin terminal conserva su antecedente y exige cuatro lecturas nuevas.

La campaña de 57 lotes cubrió 202 objetivos: 157 respaldados, 27 con veto y 18 con abstención.
Con las versiones anteriores, los 1.013 objetivos tienen un resultado. Los 45 negativos conservan
sus hallazgos y no se sustituyen por un resultado favorable anterior. La recuperación R21 congela
45 preparaciones con fuentes ampliadas: mínimo 225 llamadas, máximo 450 con una reparación por
lote y reserva máxima USD 548,04604. El plan V2 añade también los hallazgos directos previos
del caso estelar y conserva íntegro el plan anterior. No cabe en el saldo autorizado de 4.000 llamadas; la
ampliación solicitada a 4.400 sigue pendiente y no habilita ejecución.

Las versiones documentales conservan las tablas literales de equilibrio ácido-base, CDC y EPA
para aire e higiene, UniProt y MeSH para catalasa, NIST para dispersión, USGS y NASA para geología,
NHC para escala de viento, cono y registros históricos de Dora, y NASA para datos planetarios y
evolución estelar. Son fuentes congeladas con sus condiciones, fechas y licencias propias.
La versión R20 corrige de forma aditiva 98 títulos de Siyavula cuyo extractor había incluido cuerpo
del documento; no reescribe las referencias históricas ni declara infalible su contenido.

El informe MARN 2017 autoriza reproducción educativa o no comercial con atribución. Sus nueve
parámetros y usos diferenciados se recuperan del PDF; los cinco rangos ICA se cotejaron en la
leyenda del mapa de la página 8 y se conserva el facsímil y una transcripción visual identificada.
Los porcentajes de sitios de la tabla próxima no son rangos ICA. Un ICA general no certifica
potabilidad ni autoriza un uso concreto del agua. Los textos CDC, NOAA y NRCS recuperados mediante
navegación cuando falló HTTP se identifican como capturas textuales, con localizadores propios.

La revisión directa de los cuatro guiones de lagunas detectó nuevos defectos en tres versiones:
textura mineral frente a humus, cociente muestral frente a parámetros Poisson y una constante
antigua de K-40 añadida como dato actual. Las tres correcciones obtuvieron cuatro lecturas nuevas
y resolución exacta tras comprobar que la salida coincidía con el borrador editorial revisado.
Se conservan 34 expedientes de resolución y todos los seguimientos; su número no es una tasa de
precisión. La precisión de dilución conserva el veto a su alternativa sin calculadora y una única
reparación posterior, con cuatro nuevas lecturas y revisión directa de los cambios.

El corte final local conserva 3.941 llamadas y USD 2.912,1834795 de reserva: quedan 59 llamadas.
Se verificaron 2.060 trazas en 369 resultados seleccionados. El único caso de la revisión directa
que sigue sin resolución es el estelar, incluido en los 45 negativos; esto no elimina los demás
vetos. La solicitud de 4.400 llamadas sigue pendiente. El plan de recuperación no se ha ejecutado.

## Respaldo de continuidad verificado

El respaldo P11 del 23 de octubre fijaba 13.762 archivos y 41 SQLite (el recibo vigente, del 25 de octubre, fija 13.919 y los incluye), incluidos ledger,
checkpoints, originales, respuestas y archivos de código de los protocolos. Se restauró desde GCS,
se comprobaron 2.295 trazas históricas y se recuperaron 32 terminales sin generación. El respaldo
fija 3.941 llamadas/USD 2.912,1834795 de reserva. El punto mínimo de continuidad tiene hash por cada
llamada: rechaza restauraciones que pierdan consumo posterior a las 668 iniciales. Su incorporación
no amplía ni reinicia el presupuesto. El cliente del corpus usa una cota explícita de lectura de
hasta 8 GiB; se validan tamaño antes de subir, generación y SHA. El intento inicial de este respaldo
quedó en un objeto creado pero sin recibo por la antigua cota de 1 GiB: se recuperó por relectura
exacta, sin sobrescribirlo. Las operaciones posteriores requieren un nuevo respaldo al cierre.
[Recibo, generaciones y reproducción](VERIFICACION_GCS.md).
