# Operación local y reproducibilidad

## Instalación

```bash
uv sync --extra dev --extra pdf --extra rag --extra api --extra vertex --extra motor
uv run gskg --help
uv run pytest -q
uv run ruff check src tests .claude/hooks
```

Python mínimo 3.11; dependencias resueltas en `uv.lock`. En el sandbox de Codex, si la caché global de uv no es accesible, usa una caché temporal autorizada: `UV_CACHE_DIR=/tmp/goes-uv-cache uv run pytest -q`. No se desactivan hooks para hacer pasar pruebas. No se añade CI.

## Fuentes y versiones

`gskg investigacion inventariar <directorio> --version V4 --salida <archivo.json>` lee libros y registra SHA, hojas, dimensiones y cabeceras candidatas. No activa la versión. Las hojas ambiguas o auxiliares necesitan mapeo/exclusión explícitos. No se deduce el currículo por el nombre de una carpeta, su fecha de modificación o el número esperado de libros.

La activación requiere comparar versiones y reconstruir los artefactos dependientes. Un ID que persiste no demuestra que el contenido conserve la misma semántica. Etiquetas, prerrequisitos y propuestas de una fila modificada deben invalidarse o revisarse según el tipo de cambio.

## Producto V4

```bash
uv run gskg producto insumo
uv run gskg producto explorar
uv run gskg producto catalogar
# Tras obtener un catálogo completo autorizado:
uv run gskg producto construir --catalogo data/producto/V4/catalogo_disciplinas.json
uv run gskg producto validar
uv run gskg motor buscar "medición de temperatura" --grado 6 --asignatura fisica --version V4
```

Los tres primeros comandos son locales por defecto. `explorar` produce
`data/producto/explorador_v4.html` con filtros, fuentes, alertas y descarga Markdown sin conexión.
Puede mostrar un piloto mediante `--catalogo <archivo>` sin habilitar su publicación como completo.
El constructor exige piloto superado y catálogo completo, verifica celdas y crea una generación en
`data/producto/V4/snapshots/<sha>/`; solo después cambia `actual.json`. No modifica `data/grafo/`.

`motor` resuelve V4 exclusivamente desde esa publicación; una publicación ausente produce abstención
sin llamadas remotas. Las filas pendientes o fuera de alcance no entran como evidencia de una disciplina.
Las alertas científicas conocidas se revalidan y bloquean generación sobre las filas afectadas. El
diagnóstico conserva aparte lo declarado y lo realmente verificado; las 22 categorías documentales no
son 22 alineaciones curriculares. [Contrato y pruebas](investigacion/producto_v4.md).

El usuario autorizó la continuación de clasificación V4 el 21 de octubre de 2026. Se conserva
`catalogacion-v4-20261021`, con hasta 52 intentos nuevos, 76 acumulados y USD 8 acumulados.
El [registro del plan autorizado](../data/producto/V4/autorizacion_catalogacion_20261021.json)
fija el corpus y destino; no amplía el permiso a otros workflows.
[Procedimiento y contabilidad](investigacion/catalogacion_v4.md).

## Referencias internacionales verificadas

`data/referencias_2026/manifest.json` fija cuatro PDF (689 páginas): PISA 2025 final, resumen ejecutivo
ERCE 2019, TIMSS 2027 y reporte técnico ERCE 2019 publicado en 2025. Los objetos locales se restauran
con las dependencias fijadas:

```bash
uv run gskg investigacion referencias ingerir pisa_2025_marco_final erce_2019_marco_y_resultados_ciencias timss_2027_marco erce_2019_reporte_tecnico_2025 --descargar
uv run gskg investigacion referencias buscar "scientific competencies" --fuente pisa_2025_marco_final
uv run gskg investigacion referencias pagina erce_2019_marco_y_resultados_ciencias 19 --salida /tmp/erce-p19.json
uv run gskg investigacion referencias validar-dimensiones
```

La comprobación sin `--descargar` no hace red. La descarga permite solo hosts oficiales explícitos, valida redirecciones antes de seguirlas y no envía ADC ni datos del grafo a esos sitios. Cada PDF se limita a 32 MiB y 1000 páginas. Un bloqueo del sistema serializa las ingestas en macOS/Linux; el manifiesto se publica al terminar el lote. No hay presupuestos duros de CPU, memoria descomprimida ni duración total de extracción: se mantienen las fuentes seleccionadas y no se usa este adaptador como cargador de archivos arbitrarios.

La consulta localiza páginas; no aplica la calidad del benchmark histórico a este corpus nuevo ni acredita cobertura curricular. `pagina` vuelve a verificar los bytes del PDF original antes de extraer evidencia. Las dimensiones usan IDs `LOCAL:` y anclas breves: su validación prueba procedencia y presencia textual. La relación entre una tarea y una dimensión debe evaluarse por separado. La ingesta V4 ya conserva las 1.020 filas; sus alineaciones internacionales siguen pendientes.

## Alineación documental

```bash
uv run gskg alineacion listar-referentes --marco PISA
uv run gskg alineacion validar-referentes
uv run gskg alineacion preparar <fila-id> <referente-local-id> --salida /tmp/par-preparado.json
uv run gskg alineacion evaluar <fila-id> <referente-local-id> --salida /tmp/plan-alineacion.json
```

Los 29 criterios representan tres competencias, quince subcompetencias y tres tipos de conocimiento
PISA, más cinco dominios y tres procesos ERCE. La enumeración es exhaustiva para esas unidades,
no para todos los objetivos de ambos marcos. `PaginasConPerfil` usa las regiones auditadas de ERCE
PDF 11 y 19 con SHA, configuración y versión del extractor. No reemplaza la extracción raw.

Preparar y evaluar sin `--ejecutar` son operaciones locales. La ejecución explícita usa tres lecturas
ciegas, criterios obligatorios y fragmentos identificados de ambos lados. El consenso positivo produce
`respaldo_documental_automatico`; unanimidad negativa produce `no_respaldado`; discrepancias o evidencia
insuficiente producen `abstencion`. No crea `CUBRE`, ni acredita aprendizaje, equivalencia de edades o
cobertura internacional. La misma ejecución conserva el ledger y rechaza cambios de contexto o esquema.
Los comandos y el par real preparado están documentados en [alineación reproducible](alineacion.md).

La [colección de países](../data/referencias_paises_2026/README.md), seleccionada con `--coleccion paises`,
usa un manifiesto independiente y `config/curriculos_paises_2026.yaml`. Sus 12 PDF suman 2.028 páginas;
no son un catálogo de objetivos extraídos. El SHA previamente investigado se comprueba antes del parser
y de publicar un lote. La confianza TLS del sistema se amplía con `certifi` fijado en el lock; no se
desactiva la verificación. Los PDF abiertos sin clave con permiso EXTRACT se conservan sin reescribir.
La traducción japonesa de secundaria inferior inglesa que no habilita extracción queda excluida.

Enero 2026 y octubre 2022 de primaria MOE son ediciones diferentes de la cohorte P3 desde 2023. No se
convierten ponderaciones recomendadas escolares extranjeras en reglas de evaluación salvadoreña, ni se
infieren modalidades Foundation desde texto que perdió subrayados. Ver auditorías de
[Inglaterra](investigacion/curriculo_inglaterra_2026.md) y [Singapur/Japón](investigacion/curriculos_sg_jp_2026.md).

## Conocimiento y unidades

```bash
uv run gskg producto conocimiento --salida /tmp/candidatos-v4.json
uv run gskg producto conocimiento --politica config/politica_conocimiento_v4.yaml --salida /tmp/candidatos-ediciones-v4.json
uv run gskg producto juicios --help
uv run gskg producto unidades listar --grado 10 --asignatura-malla Física
uv run gskg producto unidades preparar --grado 10 --asignatura-malla Física --unidad "1. La física como ciencia" --catalogo data/evaluacion/v4/catalogo_piloto_referencia.json --destino /tmp/unidad-fisica --conectividad sin_conexion
uv run gskg producto unidades ejecutar /tmp/unidad-fisica/paquete.json --destino /tmp/unidad-fisica
```

El descubrimiento local utiliza alias completos y celdas originales, conserva todas las filas y devuelve
hipótesis, ambigüedades y bloqueos. Sus 6.901 candidatos iniciales no son enlaces aceptados: los objetivos
extranjeros históricos necesitan edición, edad/grado y evidencia; los prerrequisitos necesitan juicio de
dependencia y validación de progresión. Cero prácticas recuperadas por alias es una brecha del método,
no ausencia de prácticas en V4. [Resultados y límites](investigacion/conocimiento_v4.md).

La política opcional fija cuatro registros históricos cotejados por bytes con DfE/MOE. No certifica
traducción, modalidad o pertinencia de una relación. La hidratación estructurada usa el código oficial
completo y único, ubicación XML/DOM e identidad del parser; no inventa páginas ni ejecuta CSS/JavaScript.
La medición recuperó 46 unidades DOCX para 445 candidatos AU; hidratar sus fuentes no acepta una
hipótesis. Los localizadores japoneses históricos requieren una migración aparte de descargar MEXT.

`producto juicios evaluar <candidato-id>` prepara un expediente sin modelos por defecto. Exige la fila
completa, objetivo y evaluación local cuando existe, y fuentes primarias de los extremos/dependencia.
`--ejecutar` habilita cuatro lectores ciegos con límites en `config/juicios_conocimiento.yaml`; la
configuración no sustituye autorización para transferir el corpus. La consolidación es local, revalida
terminales y comprueba ciclos de la colección indicada. Exporta un archivo deduplicado que se incorpora
con `producto construir --conocimiento`. El snapshot `producto-2` exige ocho archivos, incluido
`conocimiento.json`; sus relaciones se limitan a una fila. La publicación local conserva quince juicios
reales en tres cohortes originales: dos respaldos, seis rechazos y siete abstenciones. No hay
prerrequisitos respaldados ni progresión verificada. Los rechazos también pueden auditarse por API.
`producto juicios medir-contexto` mide los grupos sin modelos. Los comandos, soportes y límites están
en [juicios de conocimiento](juicios_conocimiento.md).

La publicación actual usa `producto-3`: añade `alineaciones.json` con los cuatro casos originales
PISA/ERCE (un respaldo documental, un rechazo y dos abstenciones). Para reproducirla, `alineacion
coleccionar <ids-originales> --salida <archivo.json>` verifica checkpoints en modo sólo lectura y relee
fuentes; luego se pasa `--alineaciones <archivo.json>` junto a `--conocimiento` en `producto construir`.
No crea proveedores ni repone contadores. `GET /api/v4/alineaciones` lista todos los estados y
`GET /api/v4/alineaciones/{id}` los audita con sus fuentes. [Comandos exactos](investigacion/integracion_alineaciones_v4.md).
`--coleccion progresiones` en `investigacion referencias` consulta el almacén NGSS separado y fijado
por SHA. Descargarlo no admite relaciones curriculares. [Fuentes y límites](investigacion/progresiones_ngss_20261021.md).

El paquete incluye cada objetivo, indicador, evidencia, fase y alerta de la unidad. Una sesión por fila
es una organización propuesta, no carga horaria normativa. Tiempo, materiales, conectividad, apoyos y
seguridad se declaran como datos del aula. Preparar acepta un piloto identificado; ejecutar lo rechaza y
exige la misma publicación completa. `unidades ejecutar` muestra el plan sin GCP; `--ejecutar` comparte
un único presupuesto entre sesiones y reutiliza checkpoints terminales. Una respuesta que cita otra fila
no se cuenta como respaldo del objetivo solicitado. La solicitud incluye `fila_id`; el recuperador
comprueba identidad/grado/disciplina y el Motor veta otro anclaje antes de los jueces. Las evidencias
persistidas se rehidratan también al reanudar. [Contrato](investigacion/paquetes_unidad.md).

`unidades ejecutar --max-salida-tokens` fija la salida estructurada dentro de la huella de la ejecución.
No amplía automáticamente intentos ni USD. Antes de una ejecución remota debe comprobarse el acceso
de la identidad institucional; una verificación ADC no invoca modelos ni prueba disponibilidad de un modelo.
La reanudación de terminales sigue siendo local y no exige conectividad.
`motor responder` permite igualmente `--max-llamadas`, `--max-usd` y `--max-salida-tokens`, muestra esas
cotas en el plan y las incorpora al entorno durable. Aplica una copia de configuración por ejecución:
no muta el YAML ni la configuración cacheada de otros comandos. Cambiar límites no permite continuar
un checkpoint incompatible ni repone su contador.

`unidades recuperar-transporte <paquete-original.json> --destino <otro-directorio>` muestra un plan sin
GCP. Con `--ejecutar`, admite una sola recuperación cuando toda la unidad falló antes de recibir
propuestas o dictámenes, exclusivamente por `TransportError`. Revalida los checkpoints originales y
sus fuentes; conserva ID, ledger, configuración y límites. Exporta aparte, con hash del original y
anexo de consumo. No admite otro voto tras una respuesta, ni renovar presupuesto; si vuelve a fallar
el transporte, detiene los objetivos restantes. El módulo operativo fija su propio protocolo además
del entorno original del motor. [Contrato](investigacion/paquetes_unidad.md).

## Publicación de la API

La API fija y verifica el grafo por instancia. Los generadores `grados construir` y `propuesta simular` publican procedencia después de recalcular. Los diagnósticos y simulaciones históricos sin publicación no se presentan como resultados del grafo actual: devuelven `503` hasta regenerarlos. Una mutación de una propuesta no invalida otros artículos; un cambio del grafo requiere reiniciar. Los endpoints de listas señalan omisiones con `X-Articulos-No-Disponibles`. Comandos, contratos y límites están en [coherencia de la API](investigacion/coherencia_api.md).

## Recuperación y contexto

`gskg motor buscar ...` usa la referencia de recuperación seleccionada. El candidato híbrido está disponible como librería en `recuperacion/`, con embeddings opcionales y validación de huella de corpus, modelo y dimensión. No sustituye el baseline solo por ser más rápido.

`gskg motor responder "consulta" --grado 9 --asignatura biologia --version V3` prepara contexto sin GCP. El default de versión objetivo es V4: si falta, se abstiene y registra cero llamadas. La preparación hidrata fuentes soportadas desde su fila/página original, verifica SHA y conserva el texto completo que cabe en el presupuesto. Una fuente no soportada se omite con advertencia.

## Ejecución automática

Agregar `--ejecutar` llama a Vertex. `--ejecucion <id>` permite reanudar la misma solicitud con checkpoints y presupuesto persistentes. Si cambian corpus, modelos, prompts, contratos o configuración, no se continúa esa ejecución. Un resultado completado se devuelve sin repetir el trabajo. Los estados de abstención usan código de salida 2.

El ejecutor común mantiene un bloqueo por thread para impedir duplicar el mismo trabajo; threads distintos
conservan paralelismo. Si el proveedor expone Registro, vincula el ID a la ruta e identidad física del
ledger y rechaza su sustitución. La alineación rehidrata fuentes antes de cerrar, reanudar o mostrar un
terminal. Los otros motores deben comprobar sus fuentes antes de invocar el helper; la CLI y las unidades
lo hacen en su preparación. Un checkpoint no convierte sus propios bytes en evidencia verificada.

Configuración: `config/motor.yaml`. Las reservas predeterminadas limitan cada ejecución a 24 intentos pagados y USD 3 conservadores, 60 segundos por llamada, tres tareas simultáneas y una reparación. Una reserva no es costo facturado: se conserva ante timeout porque la facturación podría haberse producido. Los tokens devueltos por Vertex, incluido razonamiento cuando está disponible, se registran aparte.

Los fallos de permisos o contratos no se reintentan. Un error transitorio puede reintentarse dentro del mismo límite; el SDK no añade reintentos invisibles. El modelo solo devuelve datos estructurados: no puede ejecutar código, elegir un proyecto cloud ni escribir en fuentes.

## AIOps y almacenamiento

`data/operaciones/registro.sqlite` contiene reservas, estados, métricas y caché curricular. `checkpoints.sqlite` conserva estado del workflow. Los logs del producto salen por stderr con niveles verde/amarillo/rojo y tiempos de comandos; stdout conserva JSON utilizable en scripts. `NO_COLOR=1` desactiva colores. Los archivos operativos están excluidos de Git.

Solo se procesa contenido curricular en el nuevo motor. No introducir nombres, respuestas o identificadores de estudiantes en estos comandos/cachés. El tutor histórico y su política de datos son una superficie distinta; este trabajo no convierte sus salvaguardas experimentales en un servicio de estudiantes validado.

## Experimentos

`gskg investigacion recuperacion` compara localmente el baseline y candidatos, sin modelos ni gastos. Reporta relevantes ausentes en vez de borrarlos para mejorar cifras.

`gskg investigacion jueces <dataset> --salida <json>` muestra el plan sin gasto. Con `--ejecutar`, ejecuta las combinaciones fijadas y registra consumo; `--max-usd` acota la reserva. Las etiquetas esperadas, sus motivos y los IDs informativos no llegan al modelo. El conjunto inicial saturó y no selecciona un ganador. Los casos son sintéticos plata, no evidencia de eficacia educativa.

La vectorización de corpus es una operación diferente: conservar payload, destino, límites y autorización de transferencia en el registro del experimento. La corrida autorizada del 2026-10-21 permite 3.158 nodos V3 y hasta 98 consultas, en el proyecto institucional `g-edu-lxp-xai-dev-prj-976d`, `us-central1`, `gemini-embedding-001`, con 3.500 solicitudes y reserva máxima de USD 2. No ampliarla a otras fuentes/versiones automáticamente.

La continuación de clasificación V4 tiene un [plan local revisable](../data/producto/V4/plan_catalogacion_pendiente.json):
636 filas, Vertex `global`, Flash/Argon, mismo ledger y límite acumulado USD 8/76 intentos aplicados.
La revisión automática rechazó inicialmente esa transferencia porque el consentimiento registrado era
V3/embeddings. El usuario concedió después la autorización específica para este plan. El plan preserva 24 intentos y
USD 2,4163425 y permite como máximo 52 intentos nuevos. No constituye autorización para los
cuatro jueces, alineaciones o actividades; cada transferencia requiere su alcance correspondiente.
La continuación terminó con 52 intentos nuevos, 76 acumulados y USD 7,6109605 de reserva acumulada.
Hay una llamada 504 nueva y 68 abstenciones preservadas. [Resultados](investigacion/resultados_catalogacion_v4.json).
La publicación local se validó y el explorador muestra el catálogo completo. El usuario autorizó después
continuar lo pendiente de Ciencias hasta cerrar. Las ocho filas de Física 10.º se ejecutaron con un
presupuesto único de 64 intentos/USD 8: cuatro respaldadas y cuatro abstenciones, 58 intentos consumidos
y USD 7,4261195 reservados. La autorización concreta está junto al paquete. Reanudar recuperó los ocho
terminales con cero generación y cero gasto adicional; conservó también las abstenciones.
[Evidencia y límites](investigacion/resultados_unidad_fisica10_v4.md). No ampliar ese presupuesto ni
trasladar a Ciencias autorizaciones dirigidas expresamente a otro producto.

## Limpieza y compatibilidad

La CLI monolítica se reemplazó por un paquete; se conserva su entrypoint y los 74 comandos históricos. Las importaciones de aprendizaje son absolutas. Las fuentes, reportes previos y decisiones históricas se conservan porque siguen siendo entradas o evidencia. Un módulo sin import directo no se elimina si tiene consumidores dinámicos o una responsabilidad pendiente en la entrega. La auditoría explica los candidatos y las decisiones de retiro.

Se retiró del runtime la garantía de marco desactivada (`GARANTIA_MARCO=0` y su rama): la ablación histórica no mostró mejora y no tenía efecto sobre el ranking. Su resultado experimental se conserva en el historial de evaluación.

Última verificación global (2026-10-21): **1.161 pruebas aprobadas en 160,45 s**, con
`UV_CACHE_DIR=/tmp/goes-auditoria-uv-cache .venv/bin/pytest -q`; Ruff sobre `src`, `tests` y `.claude/hooks`,
y `git diff --check`, sin errores. La clave del planificador coincide con `planificador_recuperacion`;
no se ajustaron prompts o ranking del recuperador con el reservado. La primera corrida tras declarar certifi tuvo un fallo de resolución
de dependencias del hook: se sincronizó el editable sin red y pasaron los 32 tests del harness y después
la suite global. Las fuentes, reportes y grafo históricos no tienen
diferencias. La copia V4 se obtuvo del Drive institucional; el inventario y el mapeo de todas sus hojas
están implementados. El SDK de Google puede emitir un aviso de deprecación bajo Python 3.14; no provocó
fallo de ejecución.

Tras la catalogación y publicación reales pasaron **133 pruebas focales en 45,34 s**, `producto validar`
y el [smoke del runtime](investigacion/verificacion_runtime_v4.json): contexto CLI por fila exacta,
grado incompatible con cero llamadas, ocho sesiones con fuentes verificadas y 27 vetos científicos.

La revisión visual confirmó escritorio, filtros, teclado, fichas y alertas, y móvil a 390 × 844. Se corrigió
un desbordamiento del SHA del pie. La descarga real de Markdown sigue sin confirmar en Chrome; la
exportación tiene pruebas locales de contenido y sintaxis. Ver [evidencia y límites](investigacion/revision_visual_v4.md).

El plan aplica 76 intentos acumulados: 24 previos + hasta 52 nuevos, dentro del techo solicitado de 78.
