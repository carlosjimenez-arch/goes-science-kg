# Paquetes de las mallas finales · 26 de octubre de 2026

Se construyeron **1.128 paquetes base** de la entrega local final: **1.020 por objetivo y 108 por
unidad**, con **14 ZIP por grado y asignatura**. Conservan los once Excel originales, las 126 hojas,
los valores y coordenadas de todas las filas. Incluyen JSON, lectura docente Markdown, manifiestos
SHA-256 y comparación contra la captura anterior.

**Estado: integridad documental comprobada; revisión de contenido de esta edición pendiente.**
Estos paquetes base no contienen las propuestas mejoradas ni los votos de la edición anterior.
El campo `propuesta` es `null`, `revisiones` está vacío y `estado_revision` indica
`pendiente_revision_nueva_edicion`. La API y cada descarga muestran este límite.

La biblioteca anterior conserva sus propuestas y revisiones, disponible en `/api/v4/materiales`.
El grafo producto-4 seleccionado corresponde a esa captura anterior; no se ha presentado como un
grafo reconstruido y revisado con las mallas finales.

## Comparación y correcciones del lector

- Los 11 archivos finales tienen SHA diferentes de los anteriores. La captura independiente está en
  `insumos/v4_produccion_20261026`, con procedencia propia.
- Los 1.020 objetivos procedimentales coinciden literalmente en sus localizadores anteriores.
  Cambiaron los campos lógicos de **884 filas**: fases en 884, subcontenidos en seis y habilidad del
  siglo XXI en una. Las cifras se solapan. No hubo filas retiradas ni filas sin paquete.
- **1.018 filas tienen cuatro fases**. Las dos de «Unidad 11 - Biosfera y sostenib», de 9.º, conservan
  cinco. Las fases ausentes se declaran y no se completan artificialmente.
- En varias hojas «Explorar» tiene un encabezado combinado sobre dos columnas. Se incorporan ambas
  **únicamente por esa combinación explícita de Excel**, conservando cada coordenada. Si los datos
  también comparten ancla, su texto se incorpora una sola vez. Dos encabezados separados con el mismo
  campo siguen siendo un error. Esta opción no altera la ingesta de la captura anterior.
- Treinta objetivos tienen incidencias señaladas. Persisten anclas de alertas anteriores sobre
  citosina, biomoléculas, pendiente de un resorte y evidencia de disolución. Hay además una fila con
  las cuatro fases vacías. Los conteos por alerta incluyen paquetes que comparten una celda combinada;
  no son treinta errores científicos independientes ni una auditoría completa de esta edición.

PISA/TIMSS/MEN/DigComp se conservan como declaraciones del insumo. Los 1.020 paquetes no equivalen a
1.020 objetivos clasificados y respaldados como Ciencias: tampoco se heredan sin evaluación las siete
exclusiones del catálogo previo. El antecedente de una fila sólo permite consultar el histórico por
archivo, hoja y fila; no acredita equivalencia semántica.

## Descarga desde el bucket

Requiere acceso GOES a `gs://goes-ai-kg-artefactos/ciencias/v4/`.

```bash
uv sync --extra api
uv run gskg produccion descargar --destino /tmp/paquetes-mallas-finales
```

El destino debe ser nuevo. El comando usa `config/paquetes_produccion_ciencias.lock.json`, descarga
las generaciones fijadas y comprueba tamaño y SHA-256. Son 14 ZIP: Ciencias de 2.º a 9.º y Biología,
Física y Química de 10.º y 11.º. Cada `manifest.json` verifica los JSON, Markdown y Excel del ZIP.
El orden es documental, sin afirmar una secuencia pedagógica validada.

Para consultar o descargar paquetes individuales:

```bash
uv run gskg materiales restaurar \
  --recibo config/materiales_produccion_ciencias.lock.json \
  --destino data/materiales_produccion_v4
uv run gskg servir --puerto 8010
curl 'http://127.0.0.1:8010/api/v4/produccion/materiales/salud'
curl 'http://127.0.0.1:8010/api/v4/produccion/materiales?tipo=paquete_objetivo&grado=2&limite=40'
curl 'http://127.0.0.1:8010/api/v4/produccion/materiales?tipo=paquete_unidad&grado=10&asignatura=F%C3%ADsica'
```

Con el `id` devuelto, usar `/api/v4/produccion/materiales/detalle/{id}` o
`/api/v4/produccion/materiales/descarga/{id}?formato=md`. El manifiesto está en
`/api/v4/produccion/materiales/manifest`. Los Excel y ZIP incluidos se descargan también por
`/api/v4/produccion/materiales/archivos/{sha256}`; sus SHA figuran en `originales` del manifiesto.
Ninguna petición invoca Vertex. Una modificación de biblioteca invalida la instancia del lector.

## Reproducción y revisión pendiente

Con ambas capturas y la biblioteca anterior restauradas:

```bash
uv run gskg produccion construir \
  --destino data/materiales_produccion_reconstruida \
  --exportaciones data/produccion_reconstruida/paquetes
uv run gskg materiales validar --directorio data/materiales_produccion_reconstruida
uv run gskg produccion preparar --destino data/produccion_reconstruida/preparaciones
```

La configuración final es `config/mallas_v4_produccion.yaml`; no modifica `config/mallas_v4.yaml`.
La expansión de encabezados de fases combinadas es explícita en cada hoja final.

Se prepararon los contextos completos de las **108 unidades**, con fuentes PISA, ERCE, países,
progresiones y definiciones científicas previamente verificadas, sin llamadas nuevas. El preflight
está en `data/produccion_v4_20261026/preparaciones_p2/preflight.json`. Conserva celdas adicionales y
excepciones de fases. Su catálogo provisional declara las asignaturas explícitas de Bachillerato y
mantiene pendiente Ciencias; **no es un plan ejecutable ni una publicación de catálogo aprobado**.
Tras catalogar hay que regenerar y fijar los contextos definitivos antes de ejecutar los lectores.

El contador sigue en **3.941 llamadas y USD 2.912,1834795 de reserva acumulada**. El límite vigente
es 4.000/USD 3.500; quedan 59 llamadas. La primera pasada de redacción y cuatro revisiones por unidad
requiere 540; la cota con una reparación es 1.080 y USD 2.192,843796 para esas revisiones. Se añaden
hasta 54 llamadas de catalogación y 20 controles adversariales, con su propia reserva.
El preflight está bloqueado y esta entrega consumió **cero invocaciones nuevas**.

Se solicitó ampliar el máximo acumulado a **5.200 llamadas/USD 5.500**. La solicitud no modifica
los límites ni constituye autorización. El siguiente paso es completar la nueva catalogación,
reconstruir las propuestas y someterlas a ciencia, currículo, psicopedagogía y revisión adversarial.
Una propuesta negativa no se promoverá a entrega revisada por completar pruebas de ingeniería.

## Verificación

Las pruebas reales cotejan todas las celdas de las 1.020 filas contra los once Excel incluidos,
sus anclas y encabezados. Comprueban cobertura exacta de las 108 unidades y de los 14 ZIP, sus SHA,
la descarga JSON/Markdown de cada paquete y todos los originales por API. Hay regresiones para
encabezados separados y combinados, datos combinados, publicación reanudable sin sobrescritura,
URI ajena y alteraciones de biblioteca.

La publicación crea objetos nuevos y relee cada generación. Antes de cada escritura comprueba
cuenta, proyecto, UBLA y PAP; `inherited` exige comprobar la política efectiva enforced en ese momento.
Los recibos contienen las generaciones y hashes para recuperar la entrega independientemente.

La suite completa pasó **1.593 pruebas en 314,59 segundos** y Ruff. La recuperación real desde GCS
reconstruyó los 1.128 registros y 30 archivos incluidos con igualdad exacta frente al original local.
La biblioteca anterior conserva su identidad. Estas comprobaciones verifican ingeniería y
procedencia; no convierten los paquetes base en propuestas mejoradas revisadas.
También se recuperaron los 14 ZIP y su índice directamente de GCS: los quince archivos coinciden
byte a byte. Una segunda compilación desde los insumos produjo el mismo ID y SHA de biblioteca.

La biblioteca final es `9a697bdbdab8f6f044254d399a8ace06d9b9b7430dfbede695f38cae95daceae`.
Su SQLite tiene SHA `13670275b08013ad583cfd9b1346d4c1b0b1906b8dc3ac0f208914ccec4c0058`,
64.839.680 bytes y generación GCS `1793045084985593`. El manifiesto tiene SHA
`2ae66b4904f8f5f2decf2dceab105616fec45994b4bfb2b10bc2de8472cdb494` y generación
`1793045098167779`. La huella del currículo final es
`0b92f8016bdae2b12a687bd5b3384c4c8ab9bde538fb5b475fcb3fecb926a78f`.
