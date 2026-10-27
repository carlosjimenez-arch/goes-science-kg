# Paquetes por indicador de logro · mallas finales

Se generan **1.019 paquetes individuales**, que cubren las **1.020 filas** de las mallas finales.
Un indicador literal se repite en dos filas de la misma unidad de 2.º; su paquete conserva ambas
preparaciones. No se pierde ninguna fila ni se modifica el insumo. Los paquetes se entregan también
en **14 colecciones ZIP por grado y asignatura**, con índice, guías, JSON y los Excel originales.

## Qué contiene cada paquete

Cada ZIP individual tiene `LEEME.md` con la guía completa, `indicador.json` con el indicador y sus
preparaciones íntegras, y `manifest.json` con tamaño y SHA-256 de cada archivo. Incluye actividades,
criterios, apoyos, casos cuando existen, seguridad, fuentes, celdas originales y lecturas de origen.
Los Excel físicos se incluyen en la colección de grado/asignatura y en la biblioteca, evitando
repetirlos dentro de cada ZIP individual. Los localizadores y SHA están en el JSON individual.

El indicador literal y el indicador docente de trabajo se distinguen. Cuando la revisión corrigió
una formulación científica, la guía utiliza las instrucciones docentes corregidas y conserva el
literal como procedencia. No se separan automáticamente las tres celdas con varios enunciados:
un salto de línea no demuestra que sean indicadores distintos.

Se agrupa sólo por texto con espacios normalizados, grado, asignatura, unidad, origen y captura.
No se agrupan textos diferentes por parecido ni por compartir código. Hay **ocho códigos ambiguos**
dentro de su ámbito; cada texto conserva su propio ID. Para solicitar un paquete usar siempre
`INDICADOR-FINAL:…`, no sólo el número. El código simple `23` se conserva como aparece; no se corrige
a `2.3`. **61 paquetes no tienen código prefijado**: 60 indicadores de 2.º y la completación de 3.º.
Una mención interna como «(2.8)» no asigna código al indicador.

La separación de mezclas de 3.º conserva el indicador de la completación derivada, con su origen
explícito. La celda original sigue vacía. No se presenta como una nueva celda oficial del MINED.

## Revisión y límites

**1.011 paquetes tienen todos sus contextos de origen con revisión completa; ocho conservan
contextos pendientes.** Son los mismos ocho objetivos pendientes de la biblioteca V3. Las siete
unidades pendientes continúan en la entrega por unidades; esta exportación incluye paquetes por
objetivo asociados al indicador y no vuelve a evaluar las unidades.

El reagrupamiento lleva siempre `estado_reagrupamiento: sin_revision_especifica`. Las cuatro lecturas
se refieren al contenido exacto de las preparaciones de origen; **no son votos nuevos sobre el
indicador ni prueban que cada actividad evalúe por separado ese logro**. Se conservan tareas y
criterios completos para no inventar correspondencias específicas. No hay desempeño observado,
eficacia en aula ni aprobación institucional. La compilación y las consultas consumen cero modelos;
el contador acumulado permanece en 3.999 llamadas.

## Descarga privada desde GCS

La biblioteca es `86119d8c1cc5732bdc3d31bb55a5c38184a68b34fcefc4a82d9fdcaa0b03fdb0`.
Usa el mismo bucket GOES y prefijo `gs://goes-ai-kg-artefactos/ciencias/v4/`. Los recibos son
`config/materiales_indicadores_ciencias.lock.json` y `config/paquetes_indicadores_ciencias.lock.json`.
Fijan generaciones, SHA, tamaños y protección verificada. Los objetos anteriores se conservan.

```bash
uv sync --extra api
uv run gskg indicadores descargar --destino /private/tmp/ciencias-indicadores-v4
```

La carpeta debe ser nueva. Las 14 colecciones contienen todos los ZIP individuales y tienen
`LEEME.md` con enlaces a cada guía y ZIP. El comando verifica generación, tamaño y SHA antes de
habilitar la descarga. La biblioteca SQLite contiene asimismo los 1.019 ZIP individuales, indexados
por SHA, para descargarlos directamente por API sin descomprimir las colecciones en el servidor.

Para servir la API en otra instalación, basta restaurar esta biblioteca, sin corpus ni ledger:

```bash
uv run gskg materiales restaurar \
  --recibo config/materiales_indicadores_ciencias.lock.json \
  --destino data/materiales_indicadores_v4
uv run gskg servir --puerto 8011
```

Conservar una carpeta existente antes de restaurar y reiniciar un servidor ya abierto.

## API

```bash
# Catálogo y filtros exactos; los códigos pueden tener más de un resultado.
curl 'http://127.0.0.1:8011/api/v4/produccion/indicadores/indice?grado=6&codigo=3.12'
curl 'http://127.0.0.1:8011/api/v4/produccion/indicadores/indice?estado_contextos=contextos_con_pendientes'
curl 'http://127.0.0.1:8011/api/v4/produccion/indicadores/catalogo.csv' -o indicadores.csv

# Ejemplo real: completación de mezclas de 3.º, con indicador original vacío.
curl 'http://127.0.0.1:8011/api/v4/produccion/indicadores/descarga/INDICADOR-FINAL:65fc3e03302b8e16acd0a62d13478fbf31b64436f10d471029f22a900efbcb6d?formato=zip' \
  -o mezclas-tercero.zip
```

El catálogo admite `codigo`, `grado`, `asignatura`, `unidad`, `fila_id`, `origen`, `estado_contextos`,
`q`, `limite` y `offset`. Detalle: `/detalle/{id}`. Descarga: `/descarga/{id}?formato=json|md|zip`.
El CSV es una vista para hojas de cálculo, protegida frente a fórmulas; los literales completos
están en JSON. `/auditoria` muestra cobertura y códigos ambiguos. `/salud` y `/manifest` identifican
la biblioteca. Los originales y ZIP se pueden descargar también por `/archivos/{sha256}`.
Los endpoints anteriores de materiales y preparaciones permanecen separados.

## Reproducir

Con la biblioteca V3 de preparaciones restaurada, sin necesidad de invocar modelos:

```bash
uv run gskg indicadores construir \
  --origen data/materiales_produccion_v4 \
  --destino data/materiales_indicadores_reconstruidos \
  --exportaciones data/indicadores_reconstruidos/paquetes
```

Los destinos deben ser nuevos e independientes. Se valida el contenido exacto de las preparaciones,
la procedencia y sus estados antes de agrupar. La fuente V3 y los originales se leen sin cambios.
Las fechas ZIP y el orden de archivos son fijos; los ID se derivan de la captura y el indicador en
su ámbito. Una corrección de la preparación puede cambiar la biblioteca sin fingir votos nuevos.

## Verificación de esta entrega

Pasaron **1.693 pruebas en la suite integral** y **46 en la pasada focal final**, incluida la
regresión que rechaza ZIP individuales para otros tipos de material. Ruff pasó en `src` y `tests`.
Se realizaron **1.033 consultas HTTP**, descargando y verificando los **1.019 ZIP individuales**
y sus manifiestos; el ledger conservó el mismo SHA. La descarga y el control de los ZIP tomó
8,131 s en esta ejecución local; es una observación de este entorno, no una garantía de servicio.

La compilación inicial tomó 5,894 s. Una segunda compilación en una raíz nueva, sin ledger ni
corpus adicional, produjo SQLite y 14 colecciones con bytes idénticos. Se restauraron por separado
desde GCS la biblioteca y todas las colecciones, y se comprobó cobertura, hashes y enlaces.
El orden de consulta es documental; no define una nueva secuencia pedagógica validada.
