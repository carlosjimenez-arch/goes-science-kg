# Guiones completos de Ciencias V4

## Estado de esta ampliación

El alcance son los 1.013 objetivos de Ciencias del snapshot producto-4, agrupados en 108 unidades.
Los siete registros fuera de Ciencias se conservan fuera de generación. El piloto ampliado cubre
24 objetivos y ya tiene cuatro revisiones sobre cada guion exacto. Al iniciar la campaña P5 se
conservaron otros 40 respaldos y se resolvieron siete abstenciones; los 942 restantes están en
ejecución. No se presenta la biblioteca de preparaciones ya publicada como esta entrega nueva.
La publicación completa exige la cobertura exacta, sin promover vetos ni abstenciones.

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

| Revisión | Criterios |
|---|---|
| Ciencia | Exactitud, afirmaciones sustentadas y soluciones correctas |
| Currículo | Objetivo conservado, evaluación alineada y guion completo |
| Psicopedagogía | Adecuación al grado, tiempos y apoyos/accesibilidad |
| Adversarial | Seguridad, datos/fuentes y recursos factibles |

Los cuatro lectores reciben el mismo borrador y contexto; no reciben los votos de los demás.
Todos los criterios deben ser `si`. Las revisiones de la propuesta curricular anterior no son
votos de la clase. Compartir proveedor o modelo no da independencia estadística.
Los controles de desarrollo detectaron un error científico y una instrucción peligrosa introducidos
a propósito, conservando dos casos correctos. No son una evaluación independiente de eficacia.

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
El ZIP y la biblioteca conservan los expedientes, incluidos rechazos y abstenciones.

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
P1–P5 son protocolos del flujo de generación; el currículo sigue siendo V4. Los comentarios de
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
