# Datos de Ciencias en GCS

El corpus, los PDF, las matrices, los grafos, los resultados de investigación, los checkpoints y
las entregas se conservan en `gs://goes-ai-kg-artefactos/ciencias/v4/repositorio/`. El código,
la configuración, las pruebas y la documentación de trabajo permanecen en Git. El `.env` sigue
siendo local y no forma parte del respaldo. La cuenta y el proyecto institucionales están en
`config/almacen_ciencias.yaml`; se usa la sesión de `gcloud`, sin copiar claves al repositorio.

`config/datos_ciencias.lock.json` fija las URI, las generaciones y los SHA-256 de los objetos.
El ZIP conserva las rutas originales y un manifiesto con el tamaño y el SHA-256 de cada archivo.
Hay también un inventario JSON y un recibo independientes en GCS. Los SQLite se respaldan mediante
su API de copia consistente, incluyendo las transacciones confirmadas en WAL; los locks, WAL,
SHM y cachés de Python no se restauran como archivos independientes.

## Todo desde el bucket

| Comando | Efecto |
|---|---|
| `make producto` | Instala, descarga lo que falte desde GCS y sirve la aplicación en `127.0.0.1:8010` |
| `gskg datos estado` | Compara corpus, biblioteca y guiones locales con sus recibos, sin descargar paquetes |
| `gskg datos verificar` | Cotejo por SHA del corpus local contra el inventario remoto (código 1 si algo difiere o falta) |
| `gskg datos sincronizar` | Descarga lo ausente; rechaza estados parciales o divergentes en vez de sobrescribir |
| `gskg datos publicar --trabajo <carpeta nueva>` | Empaqueta, sube, restaura en la carpeta, compara y sólo entonces adopta el recibo nuevo |
| `gskg servir --sincronizar` | Sincroniza antes de servir |

Las bases SQLite operativas en WAL se guardan como copia consistente y se cuentan aparte en la verificación.
Publicar un recibo nuevo es un cambio de código: se revisa y confirma con la identidad GOES.

## Recuperar y usar

Requisitos: Python 3.11+, el entorno del proyecto y `gcloud` autenticado con acceso de lectura al bucket.
Para reponer las rutas que esperan la CLI, las API, los informes y las pruebas:

```bash
uv sync --extra dev --extra pdf --extra rag --extra api --extra motor
uv run gskg datos restaurar --en-repo
uv run gskg producto validar
uv run pytest -q
```

La restauración es explícita: descargar no ejecuta modelos. Comprueba el SHA del paquete y todos los
archivos antes de incorporar las raíces. Rechaza cualquier raíz que ya exista para evitar perder
trabajo local. Los datos recuperados quedan ignorados por Git; no usar `git add -f` sobre esas rutas.
Al usar `--en-repo`, también verifica los bytes completos de todos los SQLite y migra únicamente
la identidad física del ledger en `checkpoint_presupuestos`: una copia descargada tiene otro inodo.
Conserva el contenido completo del ledger, las reservas, las respuestas y los mismos identificadores
de presupuesto. Registra las identidades anterior/nueva y los vínculos en
`data/operaciones/migraciones/restauracion-*.json`. Rechaza un checkpoint asociado a otra identidad
original o un SQLite cambiado después de restaurar. Las comprobaciones de entorno de los motores
siguen vigentes; esta operación no autoriza repetir llamadas ni reiniciar presupuestos.

Para examinar el corpus sin reponerlo en el proyecto:

```bash
uv run gskg datos inventario > /tmp/inventario-ciencias.json
uv run gskg datos restaurar --destino /tmp/ciencias-restauradas
```

`--destino` requiere una carpeta nueva o vacía. Los enlaces relativos de los reportes históricos se
reconstruyen dentro del corpus restaurado. Los tres enlaces históricos que siguen en Git apuntan
a las rutas originales y vuelven a funcionar después de `--en-repo`.

## Respaldo vigente · 25 de octubre de 2026

El recibo fija **13.919 archivos y 41 SQLite** (3.303.147.808 bytes originales), generación
`1792955294299402` del ZIP `06398b9e…`. Incluye el corte P11 y los derivados de la progresión 2.º–11.º. Se
restauró desde GCS en un checkout limpio y la aplicación completa funcionó con esos datos.
[Identidades y prueba del consumidor](VERIFICACION_GCS.md).

La biblioteca docente tiene además su recibo propio (`config/materiales_ciencias.lock.json`) para quien sólo
necesite los materiales. Tras restaurar el corpus con `--en-repo`, la biblioteca ya está en `data/materiales`
con sus bytes exactos; `gskg materiales restaurar` es para un checkout sin corpus.

## Migraciones posteriores

`config/datos_externos.yaml` declara las raíces y patrones. El plan fija la selección concreta,
incluidos los archivos no versionados; los bytes de código y las credenciales quedan fuera.
Antes de preparar, terminar las escrituras de los procesos que usan esas raíces.

```bash
uv run gskg datos preparar --destino /tmp/ciencias-nueva.zip
uv run gskg datos subir /tmp/ciencias-nueva.json --recibo /tmp/recibo-ciencias-nueva.json
uv run gskg datos restaurar --recibo /tmp/recibo-ciencias-nueva.json --destino /tmp/verificacion-ciencias
uv run gskg datos retirar /tmp/ciencias-nueva.json --recibo /tmp/recibo-ciencias-nueva.json
```

La subida crea objetos nuevos sin sobrescribir generaciones y comprueba la identidad del proyecto,
el acceso uniforme y la prevención efectiva de acceso público antes de cada escritura. Después
descarga y comprueba los bytes. El retiro realiza otra restauración real desde GCS y verifica que
ningún original, enlace, WAL o archivo de datos nuevo haya cambiado desde el plan. Ante cambios no
retira ningún archivo: hay que preparar un paquete nuevo. No ejecutar procesos escritores durante
la preparación y el retiro.

Para adoptar otra versión, guardar el nuevo recibo como `config/datos_ciencias.lock.json` en un
cambio de código revisado. El recibo anterior y sus objetos siguen disponibles por generación.
El inventario deja recuperar la procedencia exacta, pero no equivale a aprobación curricular.

Retirar estos archivos del checkout y del siguiente commit no borra los objetos de commits
anteriores. Esta migración no reescribe el historial de Git ni fuerza un push.

## Antecedente: respaldo de clases

El recibo del 23 de octubre fijaba **13.762 archivos y 41 SQLite**, con 3.293.032.617 bytes originales y
1.154.109.631 comprimidos. SHA del ZIP:
`a61846aa6948c8743f504fdfaf48ec1e815313724652df36d2c636ba61fa173b`;
generación `1792734820537079`. La restauración independiente verificó todos los archivos, 2.295
trazas históricas y 32 recuperaciones terminales sin llamar a modelos. Conserva 3.941 invocaciones
y USD 2.912,1834795 de reserva. El punto mínimo de consumo está incluido en el respaldo y su SHA
en la configuración pública; restaurar una versión anterior no habilita un contador menor.
[Generaciones y alcance](VERIFICACION_GCS.md). Los borradores pendientes no son clases liberadas.

La cota del respaldo es explícita, hasta 8 GiB sin comprimir; el recibo fija la cota aplicable a su
versión. El cliente del corpus adopta también una cota explícita de lectura de objetos de hasta 8 GiB.
El tamaño se valida antes de crear el objeto; se conserva la comprobación por generación, tamaño
y SHA incremental. El cliente general conserva su valor predeterminado de 1 GiB.
No se retiran los datos locales durante esta ampliación. Las nuevas operaciones requieren
otro respaldo actualizado antes del cierre.

## Antecedente: respaldo del cierre curricular del 22 de octubre

El recibo histórico fijaba **7.580 archivos y siete SQLite**, 1.658.473.975 bytes originales y
497.573.457 bytes comprimidos. La generación del paquete es `1792672061221417`, con SHA
`b6b84b511df95ee7d85f11c0c94d03286c05594308e084282e91ec23803de065`.
Se descargaron y verificaron todos los archivos y se reanudaron terminales reales P6/P7 con cero
llamadas nuevas, conservando 668 invocaciones, USD 731,1485125 reservados y el SHA completo del ledger.
El runtime restauró producto-4 con 108 unidades y 1.013 filas de Ciencias respaldadas, de 1.020
originales. Se migraron 15 vínculos de presupuesto; no se reinició ningún contador.
[Generaciones, ensayo y corrección de compatibilidad](VERIFICACION_GCS.md).

El paquete conserva también todos los protocolos anteriores. El retiro local se completó después del
cierre de escrituras, otra restauración real y la comparación exacta de originales/vínculos/WAL con el
plan: **7.580 archivos retirados de 61 rutas**, sin cambios posteriores al paquete.
La selección del recibo y la documentación están fuera del corpus para evitar una identidad circular.
El respaldo anterior sigue disponible por su generación; no se sobrescribe ni elimina.

## Antecedente: traslado del 21 de octubre

Se subieron y restauraron desde GCS **7.397 archivos**, incluidos **120 PDF y siete SQLite**:
946.322.945 bytes originales y 357.612.065 bytes de paquete. La restauración verificó todos los
SHA-256. El runtime y las rutas `/api/v4/salud` y `/api/v4/filas` respondieron correctamente con
las 1.020 filas V4. En la copia de ensayo se migraron 15 vínculos de presupuesto; el ledger
conservó exactamente sus bytes y la campaña mantuvo 50 llamadas, USD 50,6882185 reservados y
cero llamadas pendientes. El `.env` permaneció local. Se retiraron del seguimiento de Git
3.517 archivos de datos; los archivos nuevos no versionados también quedaron incluidos en GCS.

Las 31 pruebas de almacenamiento/migración pasan también después de retirar el corpus local.
Para ejecutar la suite completa en un checkout sin corpus hay que restaurar los datos primero.
