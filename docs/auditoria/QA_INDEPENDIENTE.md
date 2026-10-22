# QA independiente · GOEs · 2026-10-22

Este informe conserva el primer corte de QA y su revisión incremental SQLite. El barrido posterior,
con cinco hallazgos adicionales corregidos, está en [Segunda revisión QA](QA_SEGUNDA_REVISION.md).
Las cifras y comprobaciones siguientes describen aquel corte.

## Veredicto del alcance revisado

Sin hallazgos funcionales accionables abiertos después de corregir y volver a comprobar los dos problemas identificados durante esta auditoría. No equivale a certificar ausencia de todo defecto. La medición integral, integridad del corpus/ledger, documentación/badges y comprobación visual final se coordinan por el agente principal con el chat implementador.

La auditoría permaneció en modo solo lectura del repositorio. Las reproducciones auxiliares se guardaron exclusivamente en `/tmp/goes-qa-agent`. No se inspeccionó `.env`, no se ejecutaron proveedores reales, no se regeneraron publicaciones ni se modificó información del ledger/corpus.

## Hallazgos identificados y cerrados

### P2 · Puntero de publicación con JSON incompatible devolvía HTTP 500

- Archivo: `src/goes_science_kg/producto/lectura.py`, función `_observar`.
- Reproducción en raíz temporal aislada: escribir `actual.json` como `[]` o `{"snapshot_id":42}`; tanto `/health/ready` como `/api/v4/interfaz/resumen` devolvían 500 porque `AttributeError`/`TypeError` escapaban del contrato de disponibilidad.
- Impacto: una publicación corrupta rompía la respuesta documentada 503/sin_datos.
- Corrección implementada por el chat propietario: validar que el JSON sea un objeto y que `snapshot_id` sea string antes de usarlo.
- Verificación independiente posterior: `tests/test_api_operacion.py`, **9 passed**. El problema era previo a la extracción de `_LecturaProducto` desde `api_producto.py`; es un defecto vigente corregido, no una regresión nueva del refactor.

### P2 · Respuesta antigua de una vista sobrescribía los datos actuales

- Archivo: `src/goes_science_kg/interfaz/estaticos/producto.js`, renderizadores async y paginación.
- Reproducción determinista: solicitar Corpus, navegar a Curricularización, resolver primero sus filas y luego la respuesta antigua de Corpus. La respuesta descartada visualmente todavía sobrescribía `S.datosVista`; pulsar Siguiente producía `offset=NaN`, rechazado con 422 por la API.
- Reproducción auxiliar: `tests/js/producto.test.cjs (regresión incorporada)`, con promesas diferidas y DOM mínimo.
- Corrección implementada por el chat propietario: devolver `{html, datos}` desde los seis renderizadores y asignar datos/HTML únicamente después de comprobar `epoch`; proteger paginación sin límite entero.
- Verificación independiente posterior con la reproducción original: después de la respuesta antigua, el límite permanece en 25 y Siguiente usa `offset=25`. También pasan las dos pruebas nuevas de `tests/js/producto.test.cjs`.

## Verificaciones realizadas

- Lectura de todas las rutas HTTP V4/interfaz, servicios de aplicación, lector/cache y proyecciones indexadas; revisión de errores, filtros, límites, contratos de respuesta, trazabilidad, exportaciones y lecturas del ledger.
- Revisión de módulos JavaScript de aplicación, cliente y grafo: escapado y URLs, generación coherente de snapshots, estados sin datos, selección de objetivos, detalles y ciclo de vida del canvas.
- Comparación AST HEAD/árbol del barrido inicial, anterior a las correcciones SQLite, ignorando docstrings para limitar la revisión semántica del refactor: los cambios semánticos de módulos previamente existentes se concentran en las APIs y `interfaz/consulta.py`; el resto conserva su comportamiento sintáctico. Se revisaron los servicios nuevos y la eliminación sin consumidores de `refuerzo_excel.py`. Los cambios funcionales posteriores de SQLite se verificaron en la revisión incremental descrita al final; el inventario consolidado registra trece módulos existentes con cambios ejecutables.
- Comprobación de que los extractores certificados no presentan diff y de que el CLI sirve por defecto en `127.0.0.1`.
- Smoke contra corpus real: 35 documentos, revisión grado 2, grafo filtrado, filas grado 11, exportación Excel y CSV: **200**. Ambas exportaciones incluyen `X-Snapshot-ID` con `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`.
- Verificación de que `offset=NaN` se rechaza con 422, lo que confirmó el impacto de la carrera UI.
- `node --check` sobre `producto.js`, `cliente.js`, `grafo.js`, `iconos.js`: correcto.
- Ayuda del CLI principal y `servir`: ejecución correcta, sin iniciar servidor ni modelos.
- Revisión de instalación por extras, empaquetado de assets locales, workflow portable y documentación de límites de cobertura/pruebas. La suite integral y los hashes físicos se dejaron al agente coordinador para evitar cargas duplicadas.

## Problemas anteriores, fuera del recuento nuevo

El agente principal ya había identificado y comprobado las correcciones de: cambios de bytes en extractores firmados que invalidaban evidencia; nodos con `/` no direccionables; rutas locales filtradas en errores históricos. No se vuelven a contabilizar como hallazgos nuevos.

## Límites

- La referencia `eor-api` permanece inaccesible por permisos de macOS; no se declara inspeccionada.
- La revisión del UI aquí usó código y reproducciones deterministas; la comprobación visual en navegador corresponde al coordinador.
- No se ejecutó una segunda suite integral en paralelo; las cifras finales de cobertura y suite completa deben tomarse de la medición final coordinada.
- No se hicieron llamadas pagas ni pruebas sobre servicios externos de producción.

## Revisión incremental de ciclo de vida SQLite

Tras el cierre inicial se revisó, sin repetir la suite integral, el cambio de conexiones SQLite a `with closing(sqlite3.connect(...)) as db, db:`. Se inspeccionaron los contextos de `cli/alineacion.py`, `motor/ejecuciones.py`, `operacion/datos_externos.py`, `operacion/presupuestos_restaurados.py`, `operacion/recuperacion_unidad.py`, `operacion/respaldo.py`, `producto/lote_juicios.py` y `producto/unidades.py`; además se comprobaron las lecturas materializadas de `interfaz/servicio.py`, el cierre ya existente de `Registro.conexion` y las conexiones de las pruebas afectadas.

Resultado: **sin hallazgos accionables en este cambio localizado**. Los resultados usan `fetchone`/`fetchall` o estados materializados dentro del contexto; no escapan cursores o generadores que necesiten una conexión viva. `ejecutar_durable` devuelve un diccionario después de `invoke(..., durability="sync")`, y la recuperación termina de consultar el flujo antes de cerrar la conexión. La copia SQLite lee los bytes del receptor una vez cerrado.

El orden de salida de los contextos conserva primero el commit/rollback de `Connection.__exit__` y después ejecuta `closing.__exit__`. Una comprobación aislada con una base temporal confirmó persistencia de la transacción correcta, rollback ante excepción y cierre en ambos caminos. Las conexiones manuales restantes de los dos tests WAL conservan su `close()` explícito para poder mantener el escritor vivo durante el respaldo. No se ejecutaron proveedores, regeneraciones ni pruebas sobre los SQLite del corpus.
