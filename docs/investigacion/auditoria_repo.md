# Auditoría del repositorio para la reconstrucción del producto

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha: 2026-10-21. Alcance: código, configuración, contratos, documentación y fuentes locales del repositorio. No se leyeron secretos, no se ejecutaron llamadas a modelos ni se aprovisionó infraestructura. Las cifras describen el estado anterior a la reorganización de la CLI realizada en esta misma intervención.

## Hallazgo sobre el insumo V4

**La malla V4 no está disponible en este checkout.** `config/mallas.yaml` fija `version: V3` y el directorio `data/fuentes/mined/Mallas sugeridas v3`, con once libros. También existen las mallas anteriores en `Mallas sugeridas` y `Mallas sugeridas v2`. No hay configuración `mallas_v4.yaml` ni carpeta local de mallas V4.

La búsqueda de «V4» encontró códigos de objetivos como `PISA-V4` y versiones de propuestas `propuesta-v4`; ninguno identifica una nueva entrega del MINED. No se deben interpretar como la V4 solicitada. Un intento de listar el directorio padre fue rechazado por el sandbox; no se reintentó con escalación. La ubicación y el manifiesto de los nuevos libros siguen siendo un insumo externo pendiente.

Para activarla se requiere, como mínimo: ubicación de los once libros o lista real de archivos; versión y fecha de entrega; SHA-256 por archivo; hojas y columnas detectadas; comparación V3→V4; y catálogo de correspondencias con estados explícitos para temas idénticos, modificados, fusionados, separados, nuevos y retirados. La nueva arquitectura debe poder prepararse y verificarse sin afirmar que procesó una V4 ausente.

## Reglas y activos que condicionan la migración

No se encontró `AGENTS.md` aplicable en el checkout ni en los ancestros comprobados. Se leyó `CLAUDE.md` raíz y las especificaciones 01, 04, 07 y 15. Estas protegen `data/fuentes/`, `reportes/`, PDF, decisiones humanas y procedencia de cada inferencia. El usuario ha autorizado reconstruir el producto y usar GCP; esto no permite convertir dictámenes de IA en confirmaciones del MINED ni destruir evidencia histórica.

Activos que se deben conservar:

- Fuentes oficiales y manifiestos de descarga, con sus SHA-256.
- Identificadores curriculares y correspondencias entre versiones.
- Catálogos, vocabulario, prácticas científicas y reglas de asignación.
- Reglas deterministas de unión y validación de lotes; salida estructurada antes de publicar.
- DAG de prerrequisitos, equivalencias y regresiones científicas específicas.
- Decisiones institucionales, revisiones y rechazo documentado de hipótesis.
- Conjuntos de evaluación y su historial de contaminación; no reiniciar artificialmente una prueba ciega.
- Reportes históricos, entregables y snapshots que permiten explicar una decisión anterior.

## Inventario técnico

El paquete inicial tiene **61 archivos Python y 14.064 líneas**, más 28 archivos de pruebas. El entrypoint es `gskg = goes_science_kg.cli:app`; ofrece 74 comandos en la raíz y trece grupos. Los 25 scripts Python dentro de `reportes/` pertenecen al trabajo previo y están protegidos como histórico; su mera antigüedad no demuestra que sean código muerto.

| Área | Archivos principales | Responsabilidad actual | Cambio recomendado |
|---|---|---|---|
| Contratos y configuración | `modelos.py`, `config.py` | Pydantic, nodos, aristas, confianza, YAML, rutas globales | Mantener contratos; introducir versión de esquema y configuración explícita de ejecución |
| Ingesta | `ingesta/mallas.py`, `legado.py`, `acara.py` | Excel, identidad estable, traducción de clasificaciones antiguas | Adaptadores por tipo de fuente y reconciliación declarativa entre versiones |
| Grafo | `grafo/construir.py`, `validar.py`, `almacen.py` | Construcción, invariantes, JSONL determinista, proyección NetworkX | Conservar formato portable; añadir manifiesto completo de insumos y publicación atómica |
| Semántica curricular | `conceptos.py`, `disciplinas.py`, `alineacion.py`, `prerrequisitos.py` | Catálogo, etiquetas, alineaciones y DAG | Separar dominio, casos de uso e infraestructura; evitar lecturas ocultas desde cálculos |
| Análisis y propuestas | `brechas.py`, `propuesta.py`, `refuerzo.py`, `grados.py` | Brechas, simulación, presupuesto y entregables | Casos de uso comunes por versión y resultado tipado |
| Expertos y revisión adversarial | `panel.py` (882 líneas), `bucle.py` (1.322) | Expedientes, unanimidad, deliberación, citas y réplicas | Contratos compartidos, estados persistentes, límites y eventos de ejecución |
| Internacional | `internacional/` | Ventanas PDF/HTML, Vertex, validación, etiquetas, consenso | Registro unificado de fuentes y tareas incrementales por huella |
| Recuperación | `rag.py`, `evaluacion.py` | BM25, intención por regex, expansión del grafo y métricas | Baseline preservado, índice eficiente y evaluación de alternativas antes de adoptarlas |
| Tutoría | `aprendizaje/` | Perfil, diagnóstico, planificación, refuerzos, tutor y evaluador | Mantener detrás de un límite de producto; validar por separado contenido y aprendizaje |
| Interfaz | `cli.py` (976 líneas), `api.py` | CLI completa y API de lectura | CLI por grupos y servicios reutilizables; API enlazada a una versión inmutable |
| Entregas | `excel.py`, `visor.py`, `progresion.py`, visores internacionales | Excel determinista, HTML y fichas | Exportadores separados de los cálculos, plantillas y contratos de publicación |
| Harness local | `.claude/hooks/`, `.claude/agents/`, `lotes.py`, `agentes_vertex.py` | Guardas, prompts de rol, validación y reparación | Llevar garantías esenciales al runtime, independientemente del editor |

### Dependencias declaradas

Producción: Pydantic, PyYAML, openpyxl, NetworkX y Typer. Extras: `pdf` (pdfplumber), `rag` (Anthropic), `api` (FastAPI, Uvicorn, HTTPX), `vertex` (google-genai, python-dotenv, pypdf), `dev` (pytest y Ruff). Hay lockfile `uv.lock` y Python declarado `>=3.11`; el entorno comprobado usa Python 3.14.

El inicio rápido anterior omite el extra `vertex` aunque la suite prueba código que usa `pypdf` y `google.genai`. `Makefile instalar` sí incorpora todos los extras. Documentación, extras de desarrollo y aceptación de pruebas deben declarar una única instalación reproducible. No hace falta CI en esta fase.

### Grafo materializado

`data/grafo/manifest.json` registra 3.303 nodos y 18.177 aristas: 935 temas, 513 conceptos, 30 prácticas, 493 objetivos de marco, 1.265 objetivos de países y 822 prerrequisitos. El manifiesto del grafo conserva `version: v1`, que identifica un formato/artefacto, no la versión curricular. Deben distinguirse `schema_version`, `curriculum_version`, `source_manifest_hash`, `pipeline_version`, modelo, prompt y fecha de ejecución.

Las salidas internacionales se guardan en grafos separados. ERCE19 aparece como fuente descargada en `config/referentes.yaml`, pero **no es un marco pivote configurado** en `config/marcos.yaml`. Tener el PDF no equivale a incorporar sus dominios, niveles de desempeño o evidencia a las alineaciones.

## Comandos públicos que debe preservar la migración

| Superficie | Comandos |
|---|---|
| Raíz | `temas`, `malla-correspondencia`, `rag`, `evaluar-rag`, `brechas`, `progresion`, `servir`, `fichas` |
| `grafo` | `construir`, `validar`, `exportar` |
| `refuerzo` | `errores`, `candidatos`, `preparar`, `snapshot`, `unir` |
| `catalogo` | `acara` |
| `alinear` | `preparar-bachillerato`, `unir-bachillerato`, `preparar-temas`, `unir-temas` |
| `conceptos` | `preparar-vocabulario`, `consolidar`, `preparar-etiquetado`, `unir-etiquetado`, `preparar-paises`, `unir-paises`, `preparar-prerrequisitos`, `unir-prerrequisitos` |
| `grados` | `construir`, `resumenes` |
| `propuesta` | `candidatos`, `simular`, `preparar-adopcion`, `unir-adopcion`, `resumen`, `excel` |
| `tutor` | `bases`, `apoya`, `alinear`, `contexto`, `turno`, `evaluar`, `paquete`, `preparar-actividades`, `unir-actividades`, `validar`, `recorridos` |
| `lotes` | `validar`, `vertex` |
| `revision` | `exportar`, `exportar-decisiones`, `importar-decisiones`, `importar` |
| `panel` | `preparar`, `consolidar`, `aplicar`, `informe`, `resumen` |
| `bucle` | `anclar`, `impugnar`, `sonda`, `cerrar-impugnacion`, `replicar`, `cerrar-replica`, `solidez`, `snapshot`, `cita`, `fuente` |
| `internacional` | `extraer`, `etiquetar`, `congelar-catalogo`, `corregir-metadatos`, `construir` |

La CLI mantiene controles de gasto y verificación de cuenta ADC. La autorización de esta tarea permite usar recursos; no se deben eliminar los límites de presupuesto del producto para sus siguientes usuarios.

## API y límites actuales

`api.py` expone siete rutas GET: `/api/salud`, `/api/grados`, `/api/grados/{grado}`, `/api/conceptos/{asignatura}/{slug}`, `/api/propuestas`, `/api/rag` y `/api/rag/global`. Es de lectura y consume artefactos del filesystem; no incluye un servicio de ejecución o edición curricular.

`_grafo()` tiene caché sin parámetro de versión y los demás endpoints leen otros archivos directamente. Si se regeneran ficheros mientras el proceso sigue vivo, el servicio puede mezclar un grafo antiguo con diagnósticos nuevos. La migración necesita un único `PublishedSnapshot` verificado y seleccionado por huella, con cambio atómico y carga coherente de todos los índices. El endpoint de concepto recorre repetidamente todas las aristas; se deben precalcular índices por tipo/origen/destino.

No se necesita exponer un servidor a Internet para implementar y probar estas mejoras. El despliegue requiere además decisión de usuarios, permisos y persistencia; no es una propiedad que ya tenga la API.

## Deuda priorizada y evidencia

1. **Versionado incompleto.** README y specs 01/04 describen V2; configuración usa V3; varios nombres de funciones internacionales siguen diciendo V2 y leen el insumo vigente mediante adaptaciones. El producto nuevo debe separar contrato de esquema, versión de currículo y ejecución. Evidencia: `README.md`, `config/mallas.yaml`, `internacional/etiquetar.py:204`, `grafo/almacen.py:38`.
2. **Orquestación basada en archivos y editor.** Preparar→salida→validar→unir es verificable, pero no hay un runtime común que persista transiciones de todos los agentes. Las guardas de `.claude` no se ejecutan por usar directamente la librería. Evidencia: `.claude/hooks/README.md`, `lotes.py`, `agentes_vertex.py`.
3. **Dependencias circulares de dominio.** `bucle` importa `panel`; `panel` importa `bucle` localmente. `panel` y `refuerzo` también se importan mutuamente. Las importaciones locales aplazan el ciclo pero no separan responsabilidades. Extraer contratos y repositorios de expedientes antes de mover funciones por estilo.
4. **Estado global mutable.** `internacional/tramo.py` usa `_activo` de proceso y `config.cargar` tiene caché por nombre. Son aceptables para CLI secuencial, pero un servicio o fan-out concurrente puede mezclar tramos o versiones. Pasar configuración inmutable por ejecución.
5. **Importaciones relativas.** El AST detectó 28 sentencias de importación relativa en `aprendizaje/`, incluida una importación local en el evaluador. Convertirlas a absolutas responde a la norma solicitada sin cambiar comportamiento.
6. **Cliente de modelos insuficientemente instrumentado.** `internacional/vertex.py` ya tiene caché por prompt/esquema/adjuntos, tope compartido con lock y reintentos. Faltan uso real de tokens, coste monetario, latencia, trazas por paso, invalidación por versión y clasificación de errores reintentables; actualmente reintenta excepciones genéricas. La escritura de caché no es atómica. `VERTEX_MAX_CALLS=0` significa sin tope y no constituye un presupuesto seguro por defecto.
7. **Contexto y modelos dispersos.** Los prompts se construyen en varios módulos; `_fuentes` recorta a 7.000 caracteres por fuente. No hay presupuesto de tokens con selección explícita de evidencias ni inventario común de contextos. `rag.py` usa otro proveedor y modelo fijo; comprobar disponibilidad real antes de un experimento, no inferirla del identificador escrito.
8. **Búsqueda dependiente de léxico y regex.** `rag.py` puntúa cada documento para cada consulta y reconstruye el índice global por consulta; tiene heurísticas ajustadas sobre un conjunto pequeño. El historial en `data/evaluacion/resultados.md` reconoce qué pruebas dejaron de ser ciegas. Comparar BM25 indexado, recuperación densa/híbrida y expansión de grafo bajo el mismo presupuesto antes de adoptar Agentic RAG.
9. **Observabilidad limitada.** La CLI usa `typer.echo`; no hay un sistema común de eventos correlacionados por ejecución ni logs semafóricos. El único `logging` del dominio suprime avisos de pypdf. Introducir loggers estructurados con colores solo cuando la salida sea terminal y mantener JSON consumible por programas.
10. **Pruebas de integridad fuertes; validación educativa incompleta.** Hay contratos de tipos, DAG, SHA de fuentes, fila del Excel, correspondencia fuente→grafo y determinismo. No prueban eficacia de aprendizaje ni independencia epistémica de jueces que comparten un modelo. Las métricas deben separar integridad, recuperación, fidelidad científica, adecuación psicopedagógica y resultados educativos.

## Eficiencia: qué optimizar y cómo demostrarlo

Ya hay concurrencia de seis hilos por defecto en extracción y etiquetado internacional. No debe añadirse otro paralelismo externo sin coordinar concurrencia, cuota y presupuesto; duplicar fan-out puede aumentar 429, latencia y coste.

Prioridades medibles:

- Claves de caché y dependencias para reprocesar solo fuentes/filas que cambian.
- Lectura de cada libro una vez por etapa y reutilización de catálogos por ejecución.
- Índice invertido BM25 o representación dispersa para evitar escanear todos los documentos.
- Índices de adyacencia compartidos en consultas del grafo.
- Límites independientes por ejecución: llamadas, tokens, coste, tiempo, concurrencia y ciclos de reparación.
- Perfilar CPU y memoria antes de vectorizar; la escala local actual no justifica introducir un motor distribuido por defecto.

Benchmark requerido: conjunto fijo y versionado; tiempo de carga e índice, p50/p95 de consulta, throughput de lotes, llamadas pagadas y tokens, tasa de caché, errores/reintentos, recuperación y fidelidad. Registrar hardware, versión de datos, prompts y modelo. Una mejora de velocidad sin calidad comparable no demuestra eficiencia del producto.

## Código muerto: conclusiones sustentadas

No se justificó borrar módulos activos ni históricos completos a partir de una búsqueda de imports.

| Candidato | Evidencia | Decisión segura |
|---|---|---|
| CLI monolítica | 976 líneas, 74 comandos y trece grupos en un archivo | Sustituir por paquete de grupos manteniendo `goes_science_kg.cli:app`; eliminar el antiguo `cli.py` al verificar compatibilidad |
| Importaciones relativas | 28 sentencias detectadas con AST | Reescribirlas a absolutas; no retirar funcionalidad |
| `refuerzo_excel.py` | Ningún import interno/CLI/prueba; la spec 15.6 pide ese entregable | Función desconectada o pendiente, no muerto demostrable. Integrar y probar o retirar al cerrar explícitamente ese alcance |
| `_garantizar_marco` | Solo se llama bajo `GARANTIA_MARCO=0`; la evaluación ciega 3 no encontró mejora | Rama inactiva de un experimento documentado. Puede retirarse de runtime al conservar resultado de ablación, si el nuevo recuperador reemplaza ese baseline |
| `aprendizaje/planificador.py` | Un análisis ingenuo de imports absolutos no lo encuentra; sí tiene imports relativos consumidores | Activo; no eliminar |
| `reportes/` y configs V1/V2 | `ingesta/legado.py` y `config/marcos.yaml` los consumen | Conservar; migrar con manifiesto y comparación si se independiza el producto |
| Cachés y `__pycache__` | Artefactos recreables e ignorados | No versionar; su limpieza no es una mejora funcional ni sustituye la auditoría de código |

No añadir compatibilidad mediante un segundo monolito o shims que mantengan dos implementaciones de la CLI. Los nombres públicos son comandos y el objeto `app`; los helpers privados deben vivir junto a su grupo.

## Baseline de verificación

Con todos los extras disponibles, `.venv/bin/ruff check src tests .claude/hooks` terminó sin errores. `.venv/bin/pytest -q` completó 272 pruebas aprobadas y una fallida en 83,01 s. La fallida (`test_harness.py::test_validar_lotes_bloquea_una_salida_invalida_y_deja_pasar_las_validas`) lanzaba `uv` desde el hook y recibía un mensaje de imposibilidad de validación en el sandbox, no un rechazo de lote.

Al repetir únicamente esa prueba con `UV_CACHE_DIR=/tmp/goes-auditoria-uv-cache` pasó (0,60 s). Esto identifica un requisito de entorno: el hook necesita un directorio de caché accesible. El baseline completo final debe ejecutarse con esa variable, sin desactivar la guarda. Apareció un aviso deprecado del SDK Google al usar Python 3.14; no fue un fallo de comportamiento.

## Secuencia de migración recomendada

1. Congelar baseline de comandos, hashes, métricas y decisiones; mantener lectura histórica.
2. Normalizar estructura, imports, logging y configuración sin cambiar resultados.
3. Introducir registro de fuentes versionado y contratos de evidencia/ejecución; preparar V4 sin falsificar su presencia.
4. Implementar un recorrido vertical: ingesta de unidad→alineación→jueces→verificación determinista→grafo→resultado revisable.
5. Evaluar prompts, jueces y recuperación mediante experimentos comparables y datos separados por versión/documento.
6. Añadir checkpoints y publicación por snapshot; usar GCP para tareas justificadas por volumen, presupuesto y resultados.
7. Reprocesar V4 cuando exista el insumo, reconciliar identidades y decisiones; después retirar rutas antiguas solo con mapa de consumidores y prueba de equivalencia.

La eliminación segura de código es el final de una migración verificada. Los reportes, fuentes y decisiones son datos de procedencia del producto y no basura técnica.

## Limpieza estructural aplicada

Se sustituyó `src/goes_science_kg/cli.py` por un paquete `cli/`: `__init__.py` compone los trece grupos, `principales.py` conserva los comandos de raíz, y cada grupo tiene un módulo propio. `__main__.py` conserva `python -m goes_science_kg.cli`; el entrypoint `goes_science_kg.cli:app` permanece igual. Los helpers privados se ubican junto a su grupo y los imports de dependencias opcionales siguen siendo locales al comando. No hay una segunda implementación ni shim del monolito.

La comparación del catálogo capturado antes y después dio **74 comandos conservados, ninguno perdido**. `tests/contracts/cli_v1.txt` guarda el contrato histórico y `tests/test_cli.py` comprueba su disponibilidad y la resolución de toda la ayuda pública; el contrato admite ampliar comandos nuevos. Se reescribieron las 28 importaciones relativas del subsistema de aprendizaje a importaciones absolutas. La búsqueda AST posterior encontró cero imports relativos en el paquete. No se eliminaron fuentes, decisiones, históricos ni módulos de funcionalidad pendiente.

Verificación posterior de esta migración: **362 pruebas aprobadas** en 81,87 s con `UV_CACHE_DIR=/tmp/goes-auditoria-uv-cache`, incluido el contrato CLI y la suite histórica completa. Ruff pasó sobre los módulos reorganizados y las importaciones corregidas. Esta cifra corresponde a ese punto de integración; los módulos nuevos de motor y recuperación necesitan su propia validación posterior.

También se implementó `ingesta/inventario.py`: `inventariar(directorio: Path, version: str)` devuelve un `InventarioCurricular` tipado. Detecta libros OOXML en subcarpetas, sus SHA-256 y bytes, hojas, dimensiones reales y filas candidatas de cabecera sin suponer once archivos, nombres de hojas ni posiciones de columnas. Las etiquetas semánticas son sugerencias explícitas; las columnas ambiguas y las hojas no reconocidas exigen mapeo. Los formatos incompatibles o corruptos y directorios sin libros se rechazan. La inspección es de lectura, no guarda el manifiesto ni modifica configuración o fuentes; el consumidor debe elegir un destino de reporte fuera de las fuentes.

`listo_inspeccion` indica que el manifiesto puede revisarse y no equivale a activación de la malla ni a validación educativa. `incompleto` informa los problemas que requieren resolución. Una prueba local sobre la V3 leyó once libros, 120 hojas y 2.982 filas con valor en 0,701 s; identificó 48 observaciones de esquema, principalmente hojas auxiliares pendientes de exclusión explícita. No se clasificó esa entrega como V4. Los dieciséis tests del inventario verifican no modificación, determinismo, cabeceras fuera de las primeras filas, columnas reordenadas, esquemas ambiguos, rechazo de entradas ilegibles y propagación de permisos denegados. El recorrido usa `os.scandir` para no confundir una carpeta inaccesible con una vacía; los enlaces simbólicos se registran como omisiones pendientes y no se siguen.

`tests/test_motor_integracion.py` añade pruebas adversariales con libros temporales y proveedor simulado: hidratación desde el original frente a resúmenes manipulados, citas y anclajes falsos, fuentes fuera del directorio autorizado, cambios de SHA durante el uso, jueces incompletos, presupuesto durable y reintentos, caché de respuestas, reanudación real de SQLite y rechazo de checkpoints cuyo entorno cambió. No usan credenciales ni red. La revisión detectó y motivó corregir la reutilización de fuentes modificadas y la comparación de solicitudes cuyos recursos cambiaban de tupla a lista al persistir el checkpoint.

Tras integrar el contrato `Borrador`, los modelos simulados seleccionan únicamente IDs del registro de fragmentos y el código resuelve el literal; los ataques de citas desconocidas se abstienen antes de gastar en jueces. La prueba unitaria de fuentes autodeclaradas confirma que un marcador `contenido_fuente` sin repositorio verificador no autoriza ninguna generación. Verificación focal posterior: **51 pruebas aprobadas** entre `test_motor.py`, `test_motor_integracion.py` y `test_inventario.py`, con Ruff y formato correctos. La regresión que cambia la configuración a V4 conservando el grafo legado también está aprobada.
