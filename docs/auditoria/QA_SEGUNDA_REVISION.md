# Segunda revisión QA independiente · GOEs · 2026-10-22

Corte histórico de QA anterior a la revisión de versionado y observabilidad HTTP. La referencia `eor-api` se pudo inspeccionar después; consultar la [comparación posterior](../REFERENCIA_EOR_API.md). Las cifras de este informe describen su árbol original.

## Estado de la revisión

Barrido independiente sobre la rama `feat/api`, solicitado expresamente por el usuario. La revisión fue de sólo lectura del repositorio; las reproducciones, exportaciones y copias auxiliares se guardaron bajo `/tmp/goes-qa-segunda`. El agente principal realizó las correcciones. Se confirmó el cierre de cinco hallazgos P2. No quedan hallazgos accionables abiertos dentro de los escenarios revisados; esto no certifica ausencia universal de defectos.

No se leyó `.env`, no se invocó GCP/proveedores reales, no se reanudaron campañas ni se modificaron corpus, snapshots o ledgers institucionales. Los embeddings de la reproducción usan un proveedor explícitamente falso y textos sintéticos. El ledger institucional conserva SHA-256 `3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae` antes y después de las consultas.

## Hallazgos

### P2-01 · El respaldo omitía los recursos de la aplicación — cerrado

- Localización inicial: `operacion/respaldo.py`, conjunto `EXTENSIONES` y filtro de `seleccionar_artefactos`.
- Prueba: el selector real incluía `index.html` pero omitía `producto.js`, `cliente.js`, `grafo.js`, `iconos.js`, ambos CSS y la fuente WOFF2. Una restauración del paquete conservaba la página sin su implementación ni su estilo.
- Evidencia: `backup-assets.json`.
- Corrección del principal: selección de extensiones de assets y de las herramientas/documentos de calidad (`scripts`, `.github`, archivos raíz pertinentes), con regresión de selección y restauración byte a byte.
- Verificación independiente posterior: todos los archivos estáticos reales aparecen ahora en la selección (`closure-verification.json`). Se inspeccionó la prueba de roundtrip sintético; no se creó ni subió un paquete real.

### P2-02 · Un brief tardío restablecía un formato obsoleto — cerrado

- Localización inicial: `interfaz/estaticos/producto.js`, rama de compilación y cambios de formato/selección.
- Reproducción determinista: iniciar POST de brief con `evaluacion`, cambiar el radio a `cinco_fases` y resolver el POST anterior. La interfaz mantenía `S.formato=cinco_fases` mientras mostraba y descargaba un brief `evaluacion`.
- Evidencia: `brief-race.cjs`; reproducción inicial con DOM mínimo y promesas diferidas.
- Corrección del principal: identidad de compilación, vista, formato y conjunto de filas; invalidación al cambiarlos; descarte de respuestas y errores antiguos; no modificar el botón de una compilación posterior.
- Verificación independiente posterior: inspección del guard y sus caminos de error/finally, más **6 pruebas Node aprobadas**, incluidas selección, vuelta a un formato previo, visitas sucesivas y error tardío. No quedan hallazgos abiertos en esos escenarios.

### P2-03 · Excel con los mismos datos tenía bytes distintos — cerrado

- Localización inicial: `producto/exportacion_mejoras.py`, `exportar_excel`, llamada `wb.save`.
- Reproducción con el mismo runtime real: dos archivos separados 1,2 s produjeron hashes diferentes; cambiaban `docProps/core.xml` y las fechas de diez entradas ZIP.
- Evidencia: `export-determinism.json`, `export1.xlsx`, `export2.xlsx`.
- Corrección del principal: usar `excel.guardar` para fijar metadata/ZIP, proteger todo el texto y comprobar todas las hojas. Se añadió además el control de fórmula en metadata de la hoja de control.
- Verificación independiente posterior: dos nuevas exportaciones reales son byte a byte idénticas, SHA `7f1209e231c9fcabe09553d36371c906660bd6f8259f49686f362cd48674ccf0`; inspección de las regresiones con reloj diferente y fórmula en hoja de control. Evidencia en `closure-verification.json` y `export3.xlsx`/`export4.xlsx`.

### P2-04 · La base alternativa leía alertas derivadas de otro checkout — cerrado

- Localización inicial: `producto/runtime.py`, carga global de `config/alertas_derivadas_v4.yaml`; `producto/lectura.py` no inyectaba ese archivo desde su base.
- Reproducción: copia aislada de publicación, originales enlazados sólo para lectura, y alerta derivada local con SHA deliberadamente incompatible. `LecturaProducto(base_alternativa)` aceptaba la carga porque usaba la configuración del checkout anfitrión. El validador aplicado directamente al archivo local rechazaba correctamente la edición de la fuente.
- Evidencia: `isolated-app/config/alertas_derivadas_v4.yaml`, `closure-verification.json`.
- Corrección del principal: argumento opcional `archivo_alertas_derivadas` e inyección explícita desde `LecturaProducto.base/config`, preservando el default del CLI.
- Verificación independiente posterior: `/health/ready` sobre esa base incompatible responde **503 / sin_datos**; la API sobre la base real sigue respondiendo **200**. Evidencia: `api-final.json`.

### P2-05 · Dos adaptadores de embeddings superaban un límite durable compartido — cerrado

- Localización inicial: `recuperacion/vertex_embeddings.py`, `_restaurar_ledger`, `_evento` y `_reservar` (líneas iniciales 82–133).
- Reproducción mediante API pública, con proveedor falso: crear dos instancias sobre el mismo JSONL antes de reservar, ambas con `max_requests=1`; vectorizar dos textos sintéticos distintos. Ambas instancias hicieron su solicitud: dos invocaciones al falso proveedor y dos reservas registradas frente al límite de una.
- Impacto: el `Lock` es por instancia; los contadores sólo se restauran al construirla. Adaptadores o procesos concurrentes sobre el mismo ledger pueden sobrepasar el presupuesto persistente configurado.
- Evidencia: `embedding-budget/reproduction.json` y `embedding-budget/ledger.jsonl`. **Cero solicitudes externas.**
- Corrección del principal: bloqueo exclusivo del propio ledger entre instancias/procesos; relectura durable dentro de cada reserva; todos los eventos se escriben con exclusión y `flush`/`fsync` antes de permitir la invocación. Se preservan eventos JSONL y reservas; no se migró un ledger histórico.
- Verificación independiente posterior: la reproducción pública original, ahora en `embedding-budget-after`, hace exactamente una llamada al proveedor falso y bloquea la segunda antes de invocarlo. Un tercer adaptador recupera una reserva y una finalización del archivo. También se confirmó que una excepción en el contexto cierra el descriptor y libera el bloqueo. Evidencia: `embedding-budget-after/verification.json`.
- **3 pruebas focales Python aprobadas**, incluidas concurrencia de instancias con límites de llamadas y USD y reserva entre dos procesos distintos. Se observó un `DeprecationWarning` de la dependencia `google.genai` sobre `_UnionGenericAlias` en Python 3.14; no es un fallo de estas pruebas ni del mecanismo de reserva. No se hizo ninguna solicitud remota.

## Alcance técnico del barrido

- Normas y arquitectura: `CLAUDE.md`, `docs/CALIDAD.md`, configuración del paquete, fronteras entre rutas, servicios, repositorio de publicación, índice de consulta y fuentes verificadas.
- APIs: salud/listados/detalles, filtros, límites, errores de ausencia, identidad del snapshot, exportaciones, procedencia e informes de actividad en modo de sólo lectura.
- Datos reales: smoke de `/app/`, live/ready, resumen, filas de grado 11, documentos, grafo hasta 800 nodos y administración: **200**. Snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`, **1.020 filas originales, 1.013 propuestas, 108 unidades, 35 documentos**.
- Datos ausentes: en raíz vacía, página y live **200**; ready, resumen V4 y rutas históricas de grados/RAG **503**. El HTML conserva la posibilidad de mostrar ausencia sin semilla.
- UI: renderizadores, confirmación atómica de datos/HTML, modal, filtros, paginación, compilación/descarga de briefs, links/escapado, cliente y grafo. El CSS principal continúa igual al `<style>` de la referencia HTML, SHA `a572956734a42bbd77ec1c787b7d0f748c8029f858fb8a35a6e996305ec719f1`.
- Integridad/procedencia: ambos extractores firmados siguen byte a byte iguales a HEAD. Se revisó la observación de firmas, invalidación del lector, rehidratación física y separación de alertas curriculares/derivadas. Los originales y los votos no se alteraron.
- SQLite y operación: lectura read-only de actividad, cierre/commit/rollback de los contextos, respaldo consistente, validación de nombres y miembros ZIP, restauración sin sobrescrituras, retirada condicionada a inventario, generaciones GCS fijadas y migración del vínculo físico del ledger. No se ensayó retiro real ni un proveedor externo.
- Presupuestos y CLI: configuración y límites de Vertex/embeddings, reserva antes de proveedor, cachés y recuperación de salidas; comandos de servir, respaldo y datos. Se identificó y verificó el cierre de P2-05 en la exclusión entre instancias del adaptador de embeddings.
- Empaquetado/CI/calidad: extras y entrypoints, inclusión de recursos del paquete, workflow portable Python 3.11/3.14, ejecución Node, generación de badges desde JUnit/XML, huella del código y sus denominadores; inventario de módulos/consumidores y límites de la limpieza histórica.
- Documentación: concordancia del README, calidad y auditorías con la API y las métricas. Los cambios de esta segunda revisión invalidan la huella de la medición anterior: la entrega debe actualizarla con la suite final coordinada.

## Límites y medición integral coordinada

El barrido combina inspección crítica de las fronteras y algoritmos con inventarios y reproducciones; no afirma una prueba formal de todas las líneas ni ausencia universal de defectos. No se duplicó la suite integral durante la revisión: la medición posterior del principal se registra al final de este documento. Las pruebas focales ejecutadas por el principal se distinguen de las verificaciones independientes detalladas arriba.

No se probó un despliegue remoto, GitHub Actions real, IAM/GCS real, llamadas pagas ni servicios de producción. La interfaz se comprobó aquí mediante código, contratos y regresiones deterministas; no se hizo una nueva inspección visual en navegador. La referencia estructural `eor-api` permanece fuera del alcance accesible por macOS. No se committeó ni publicó ningún cambio.

## Comprobaciones posteriores del agente principal

La suite portable actual pasó **149 pruebas** sobre una copia de código/configuración sin corpus ni credenciales, con `GSKG_RAIZ` y `PYTHONPATH` fijados a esa copia. Apareció una advertencia de deprecación del SDK `google.genai` sobre Python 3.17; no hubo fallos ni peticiones externas. Las seis regresiones JavaScript pasaron en Node.js.

Se comprobó además la interfaz en navegador: seleccionar un objetivo real, compilar el formato de evaluación, cambiar a cinco fases y comprobar que desaparece el resultado anterior antes de recompilar. [Evidencia visual](qa-briefs-2026.png). Esta comprobación visual pertenece al principal y se distingue del barrido independiente anterior.

La medición integral posterior pasó **1.408 pruebas Python**, sin fallos, errores, omisiones ni advertencias, en **413,19 s**. La cobertura de líneas es **79,37 %** (15.681/19.757). Los [badges y su medición](../badges/medicion.json) registran la huella `c3b71d6b2597fc4aad0c69cfa25cc07574d9bc9319a1cbc4902ac2745775c06d`. Ruff, formato, sintaxis JavaScript, integridad de extractores/CSS, inventario documental y empaquetado también se verificaron. La ejecución de GitHub Actions continúa pendiente de publicar la rama.

El proceso integral terminó con **código de salida 0**. Después de emitir JUnit/cobertura y el resumen de pytest, Python 3.14 tardó un tiempo adicional en finalizar la recolección de memoria. Un muestreo local observó el hilo principal en `finalize_modules` / `_PyGC_Collect`; el cierre concluyó sin intervención. Los 413,19 s anteriores corresponden al tiempo informado por pytest y no a toda la vida del proceso.
