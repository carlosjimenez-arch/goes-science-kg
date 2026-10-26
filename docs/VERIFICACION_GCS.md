# Verificación de recuperación de Ciencias V4

## Respaldo vigente: revisión directa integral y rutas retiradas, 25 de octubre de 2026

Generación publicada con `gskg datos publicar` (empaqueta, sube, restaura en una carpeta de trabajo y compara
antes de adoptar el recibo). Agrega la revisión directa de los 968 guiones, las correcciones R23, el libro para
especialistas, los checkpoints revinculados a la identidad del ledger sin ruta y los registros operativos con
rutas de la estación sustituidas por rutas del repositorio (`data/operaciones/redaccion_rutas_locales_20261025.json`).

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 29.086 / 44 |
| Bytes originales / comprimidos | 4.530.002.344 / 1.604.162.276 |
| SHA del ZIP | `20c6e813fc23ff123387c08a4525fbaff8b63071b144510297956cfe129bda81` |
| Generaciones ZIP / inventario / descriptor | `1792987241757698` / `1792987298254823` / `1792987307641831` |
| Huella del inventario | `e9e75a3fcb13a53860d179343f0ac903da79aefc7d88cf1df09e1dbd44d48ddb` |
| Identidad del ledger en el recibo | nombre, dispositivo e inodo; sin ruta |

Recibos complementarios: biblioteca `8af1b65d…` (3.837 registros), entrega de guiones `e4b32786…` (862 guiones
y 108 unidades, todos con revisión directa aprobada) y biblioteca de preparaciones `5b64ee…`. Las copias
locales de la biblioteca y la entrega se retiraron y se descargaron del bucket con `gskg datos sincronizar`.
Las copias de bibliotecas y SQLite reemplazadas que estaban fuera del repositorio se subieron como
`respaldos/65f4ebeb….zip`; su manifiesto se verificó tras descargarlo.

## Antecedente: producto con 994 guiones, 25 de octubre de 2026

Generación publicada con `gskg datos publicar`, que empaqueta, sube, restaura desde GCS en una carpeta de
trabajo, compara y sólo entonces adopta el recibo. Incluye el ledger con las campañas R21 y R22, sus
preparaciones, resultados y revisiones directas, la biblioteca ampliada, la de preparaciones y la entrega
de guiones descomprimida.

| Elemento | Identidad comprobada |
|---|---|
| Archivos | 28.330 |
| Bytes originales / comprimidos | 4.396.168.714 / 1.489.918.355 |
| SHA del ZIP | `d812b22d21fef61c774d42972259ec9a3fdd9ac1cd4ef1104acf7aa71b315c6c` |
| Generaciones ZIP / inventario / descriptor | `1792967167842706` / `1792967226648808` / `1792967235380780` |
| Huella del inventario | `079eca603d440f3cd7a46b893d210e4183e55ea496cb2fd8f4891f53d418b8f9` |
| Ledger | 4.294 llamadas de la campaña de guiones; USD 3.219,5365 de reserva |

Recibos complementarios: biblioteca ampliada `5b80b556…` (`config/materiales_ciencias.lock.json`), entrega
de guiones `9d949257…` (`config/clases_ciencias.lock.json`) y biblioteca de preparaciones `5b64ee…`
(`config/materiales_preparaciones.lock.json`).

**Consumidor nuevo.** En un `git worktree` limpio, con su propio entorno y sólo los recibos, `gskg datos
sincronizar` restauró todo en 68 s; `gskg datos verificar` encontró 28.288 archivos idénticos por SHA y 42
SQLite operativos, sin diferencias ni faltantes. La suite completa pasó **1.702 pruebas sin omisiones** y el
servicio respondió en readiness, resumen, progresión, biblioteca (994 guiones y 108 unidades), exportación y
aplicación.

## Antecedente: producto integrado antes de los guiones, 25 de octubre de 2026

`config/datos_ciencias.lock.json` fija la generación que acompaña a la integración de `feat/api` y
`feat/ciencias-v4`. Contiene el corte P11 completo y los datos derivados nuevos: lotes y salidas del
etiquetado de conceptos V4, etiquetas unidas, progresión 2.º–11.º, su verificación y el registro de la
migración de vínculos. Mismo bucket, prefijo, proyecto y cuenta GOES; PAP efectiva comprobada antes de cada
escritura, precondición de objeto nuevo y relectura por generación.

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 13.919 / 41 |
| Bytes originales / comprimidos | 3.303.147.808 / 1.156.479.224 |
| SHA del ZIP | `06398b9ee906eafa2bc6e64e273f4163d27a412f002b982fc22d45eb7a403101` |
| Generaciones ZIP / inventario / descriptor | `1792955294299402` / `1792955354275666` / `1792955365147936` |
| Huella del inventario | `935ad33c5839cf006d28422cf4b66a2d836cfd69817e932c631938910e46580c` |
| Consumo conservado en el ledger | 4.442 llamadas registradas (3.941 de la campaña de guiones); sin reinicio |

El empaquetador conserva ahora los bytes exactos de una base sin WAL leída bajo bloqueo SHARED: la biblioteca
docente del paquete coincide con el SHA de su recibo propio. Las 40 bases operativas en WAL usan la copia
consistente de SQLite. Una generación intermedia (`59151f1e…`), subida antes de la revisión adversarial, se
conserva sin adoptar.

**Consumidor nuevo.** En un `git worktree` limpio de `feat/api`, sin datos, con su propio entorno `uv`, se
adoptó sólo este recibo y se ejecutó `gskg datos restaurar --en-repo`: 13.919 archivos verificados por SHA y
48 vínculos de presupuesto migrados con auditoría. `gskg materiales validar` (2.867 registros) y `gskg producto
validar` pasaron. El servicio respondió 200 en readiness, resumen, filas, progresión, trayectorias, biblioteca,
exportación Excel y aplicación; la progresión restaurada adjunta su verificación, lo que prueba que sus bytes
son idénticos. Suite completa en ese checkout: **1.693 pruebas aprobadas, ninguna omitida ni fallida**, en 283 s.

Reproducción, sin Vertex:

```bash
git worktree add --detach /tmp/ciencias-consumidor feat/api && cd /tmp/ciencias-consumidor
uv sync --frozen --all-extras
uv run gskg datos restaurar --en-repo        # corpus, derivados y biblioteca exacta
uv run gskg materiales validar && uv run gskg producto validar
uv run gskg servir --puerto 8010
```

## Antecedente: respaldo P11 del 23 de octubre de 2026

El recibo actual `config/datos_ciencias.lock.json` fija el corte de desarrollo completo en el mismo
bucket, prefijo, proyecto y cuenta GOES. Se creó el ZIP con precondición de generación cero y PAP
efectiva comprobada. Su primera relectura falló por la antigua cota local de 1 GiB, después de crear
el objeto. Se corrigió la cota del cliente de corpus a un máximo explícito de 8 GiB y se recuperó
ese mismo objeto por generación y bytes; no se sobrescribió. El inventario y descriptor son nuevos,
con protección comprobada y relectura independiente antes de emitir el recibo.

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 13.762 / 41 |
| Bytes originales / comprimidos | 3.293.032.617 / 1.154.109.631 |
| SHA del ZIP | `a61846aa6948c8743f504fdfaf48ec1e815313724652df36d2c636ba61fa173b` |
| Generación ZIP | `1792734820537079` |
| Huella del inventario | `a10226f2dd23b1edd4d8f834ddab28befd51281765bf42274d9e009f59119c2b` |
| Generaciones inventario / descriptor | `1792735204296104` / `1792735212147712` |
| Consumo conservado | 3.941 llamadas; USD 2.912,1834795 de reserva |
| SHA del punto mínimo de consumo | `92c19991b944cf33d68c8c86d3584aa4af41e906cb20ed054f64a0dfe9e68dfc` |

Se restauró la generación exacta en una carpeta vacía, se cotejaron todos los archivos y la integridad
de las 41 bases. La migración de vínculos conservó el ledger. Se verificaron **2.295 trazas históricas**
y se reanudaron **32 terminales** con un proveedor que rechaza generar: cero llamadas nuevas y
consumo idéntico. Sólo después se adoptaron el recibo y el punto de continuidad. El ensayo está en
`data/clases_v4/protocolos/verificacion_restauracion_p11_20261023.json`.

La auditoría del corte seleccionado es distinta: comprueba 2.060 trazas en 369 resultados y conserva
34 resoluciones exactas. Hay 968 respaldos automáticos y 45 negativos; la entrega de guiones sigue
pendiente. La suite completa pasó **1.581 pruebas en 265,52 s**, incluidas seis regresiones nuevas
de la cota de almacenamiento. Ruff pasó sobre `src` y `tests`.

La evidencia posterior al respaldo también está en GCS: informe de restauración, auditoría del
corte, logs de pruebas, incidencia conservada y código exacto de almacenamiento y verificación.
SHA del ZIP de evidencia: `ee16f12243bd1d2bd82c33c4f292d52d1b365766844a664ebbd1f71a7d853f4f`;
generación `1792735609314398`, 53.552 bytes. Se creó como objeto nuevo y se releyó por generación.
El recibo privado es `data/clases_v4/protocolos/evidencia_respaldo_p11_gcs.json`; el informe generado
después del ZIP principal se conserva en este objeto complementario:

```bash
gcloud storage cp \
  'gs://goes-ai-kg-artefactos/ciencias/v4/repositorio/verificaciones/a61846aa6948c8743f504fdfaf48ec1e815313724652df36d2c636ba61fa173b/ee16f12243bd1d2bd82c33c4f292d52d1b365766844a664ebbd1f71a7d853f4f.zip#1792735609314398' \
  /tmp/evidencia-ciencias-p11.zip
shasum -a 256 /tmp/evidencia-ciencias-p11.zip
```

Para descargar este corte, sin Vertex:

```bash
uv run gskg datos restaurar --destino /tmp/ciencias-restauradas
# En un checkout sin corpus:
uv run gskg datos restaurar --en-repo
```

La biblioteca anterior de preparaciones conserva su recibo independiente. Este respaldo incluye
las versiones con veto, las fuentes y los planes aún sin ejecutar; no es la publicación final de
1.013 guiones. El límite acumulado sigue en 4.000 llamadas/USD 3.500, con 59 llamadas disponibles;
el plan de 45 pendientes está bloqueado hasta responder la ampliación solicitada a 4.400.

## Antecedente: primer respaldo de la ampliación de clases

El recibo histórico fijó un objeto nuevo en el bucket GOES de Ciencias.
Cada escritura verificó identidad, proyecto, UBLA y PAP heredada con política efectiva `enforced`;
se usó precondición de generación cero y relectura por generación. No se cambió IAM.

| Elemento | Identidad comprobada |
|---|---|
| Archivos / bases SQLite | 12.640 / 27 |
| Bytes originales / comprimidos | 2.929.446.834 / 1.062.223.923 |
| SHA del ZIP | `7f759821cce24d08c029dd1460201f1bf27d94b5701e57402a111750ec2382f5` |
| Generación ZIP | `1792723241759606` |
| Huella del inventario | `72630b7acc157560cd3414ea8a77a5e67a049e69320a1b41fdf40d1ab2091d1d` |
| Generaciones inventario / descriptor | `1792723276602426` / `1792723284410915` |
| Consumo conservado | 3.227 llamadas; USD 2.340,8786235 de reserva |

Se descargó de GCS a una carpeta vacía, se verificó cada archivo y la integridad de las 27 bases.
La migración de vínculos de presupuesto mantuvo intacto el ledger. Se cotejaron 1.756 trazas de
lectores con sus respuestas reales y contexto congelado. Se reanudó un terminal por cada uno de
18 bloques de clases con un proveedor que rechaza cualquier generación: cero llamadas nuevas y
el mismo consumo al terminar. El ensayo usa la versión exacta del corpus de cada preparación.

`config/presupuesto_clases_v4.json` adopta un punto mínimo de continuidad sólo después de esa
verificación. El archivo privado incluido en el respaldo fija el hash de las 3.227 filas completas;
se conservan además las 668 iniciales. Un respaldo anterior ya no habilita gasto nuevo bajo esta
configuración. No se borran reservas ni se amplía el máximo de 4.000 llamadas/USD 3.500.

Reproducción, sin Vertex:

```bash
uv run gskg datos restaurar --destino /tmp/ciencias-restauradas
# Para reponer rutas en un checkout sin corpus:
uv run gskg datos restaurar --en-repo
```

El respaldo conserva borradores, vetos y abstenciones: no constituye la publicación completa de los
1.013 guiones. Las operaciones posteriores a ese punto necesitan otro respaldo antes de cerrar.
La biblioteca docente de preparaciones mantiene su recibo independiente. La suite completa pasó
1.567 pruebas en 272,64 s; Ruff pasó en `src` y `tests`. El ensayo detallado queda en
`data/clases_v4/protocolos/verificacion_restauracion_20261023.json` (fecha UTC del ensayo).

## Antecedente: respaldo del cierre curricular

La generación del cierre curricular se creó en el mismo bucket, prefijo, proyecto y cuenta GOES aprobados. Cada escritura
volvió a comprobar UBLA activo y prevención pública heredada con política efectiva enforced. Se usó
precondición de generación cero; no se sobrescribieron objetos ni se cambió IAM. Se descargó y verificó
cada generación. El recibo histórico permanece en Git y el objeto sigue recuperable por su generación.

| Elemento | Identidad comprobada |
|---|---|
| Archivos | 7.580, incluidos siete SQLite |
| Bytes originales | 1.658.473.975 |
| Bytes del paquete | 497.573.457 |
| SHA del ZIP | `b6b84b511df95ee7d85f11c0c94d03286c05594308e084282e91ec23803de065` |
| Generación del ZIP | `1792672061221417` |
| Huella del inventario | `83433867057bc8aadd676cb8e4e70d3ffcd479398cbbb44447246c72ffdec776` |
| Generación del inventario | `1792672084503133` |
| Generación del descriptor | `1792672093385592` |
| Snapshot producto-4 | `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008` |

Los 7.580 archivos se restauraron desde GCS en otra carpeta y se verificaron sus SHA. Se migraron
15 vínculos de presupuesto a la identidad física de esa copia, sin modificar el ledger. El runtime
recuperó 108 unidades, 1.020 filas originales y 1.013 propuestas de Ciencias; las siete fuera de alcance
siguen presentes. Los diez terminales reales de P6 y el de P7 se recuperaron con una guarda que
rechaza cualquier intento de llamar a un modelo: **cero llamadas nuevas**. El contador se mantuvo en
668 y la reserva en USD 731,1485125. SHA del ledger, idéntico antes y después:
`3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae`.

El ensayo detectó que una alerta derivada de P7 activaba referencias específicas de otra errata al
reconstruir contexto. La corrección separa `bloqueos_curriculares` de `bloqueos_derivados` y aplica su
unión en `bloqueos_efectivos` para generación, consulta, API y preparación de sesiones. El contexto de
cada protocolo mantiene sus alertas de origen, fuentes, identidad y votos. Los dos errores originales
de Hooke y evidencias de cambio químico, corregidos en las propuestas P6, también se revalidan por
SHA/celda/ancla desde config/alertas_derivadas_v4.yaml. Hay 30 filas originales bloqueadas: las 27
iniciales y tres derivadas; las propuestas corregidas conservan su respaldo. No se cambiaron checkpoints,
huellas guardadas, rúbricas, bytes de fuentes primarias ni presupuestos. Tras corregir, los once terminales volvieron a validar
exactamente el contexto físico y su resultado. Los archivos de datos y el paquete no requirieron cambios.

La API conserva los cuatro expedientes históricos PISA/ERCE y señala que uno tiene un veto científico
posterior: sigue siendo auditable, pero no habilita generación nueva. Una prueba de regresión verifica
esta separación entre el dictamen histórico y los permisos actuales. Las rutas de salud, filas,
propuestas, progresiones y `/api/v4/exportaciones/mejoras.csv` respondieron 200 desde la copia restaurada.

El respaldo anterior sigue recuperable por su generación:
`gs://goes-ai-kg-artefactos/ciencias/v4/repositorio/objetos/76c1a0e38b38884c5f55aac91b616be7f47d3810e1752fe4082fbe1c82f36523.zip#1792642807234664`.
Su SHA es el del nombre del objeto. No se borró ni se reescribió la historia de GCS o de Git.

La retirada local terminó tras una **segunda restauración real** de los 7.580 archivos y los siete SQLite.
La comparación exacta con el plan comprobó originales, vínculos y WAL antes de retirar 7.580 archivos de
61 rutas. El código y el recibo permanecen en Git; los datos vuelven a las mismas rutas con
`gskg datos restaurar --en-repo`. [Procedimiento operativo](DATOS_EXTERNOS.md).

La batería integral pasó **1.360 pruebas en 262,79 segundos**, antes de retirar el corpus. Ruff comprobó
`src`, `tests` y `.claude/hooks`. Desde el checkout público sin corpus pasaron además **86 pruebas**
de contratos, recuperación, presupuesto, propuestas, exportación y seguridad de archivos. Las 18 pruebas
de calidad/determinismo del grafo también pasaron. El wheel final contiene 194 archivos, incluida la
plantilla y la rectificación, sin PDF, Excel, SQLite ni credenciales. SHA-256 del wheel:
`77c8ab1ee40cd2a1aa514e9b303cc5ba4efe83dfb08af17954a3842d0d84e4f5`.

Después del retiro local volvieron a pasar las 31 pruebas de almacenamiento/migración. El contrato
histórico `tests/contracts/cli_v1.txt` permanece en la rama pública: sus **89 pruebas** comprueban la
disponibilidad de comandos y su ayuda sin necesitar corpus ni red. Se compararon los árboles completos
preparados del checkout local y de la rama pública y resultaron idénticos, sin incorporar ancestros privados.
