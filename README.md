# goes-science-kg

Grafo de conocimiento de **Ciencias** para El Salvador. Une la malla del MINED (2.° a 11.°) con los
marcos internacionales (TIMSS 2027, TIMSS Advanced, PISA 2025) y con los currículos de otros
países. El fin es **proponer, por asignatura, una curricularización mejor y con evidencia**.

Los datos, PDF y entregables se recuperan desde el bucket institucional con
`uv run gskg datos restaurar --en-repo`. Sus rutas están ignoradas por Git.
[Restauración, inventario y migración verificable](docs/DATOS_EXTERNOS.md).

## Paquetes por indicador de logro

Disponibles **1.019 ZIP individuales**, agrupados también en **14 colecciones por grado/asignatura**.
Cubren las 1.020 filas: un indicador repetido conserva las dos preparaciones asociadas. Los ocho
códigos ambiguos se mantienen separados por texto y ámbito. Hay 1.011 paquetes con contextos completos y
ocho con pendientes; el reagrupamiento no añade revisión ni consume Vertex.

```bash
uv run gskg indicadores descargar --destino /private/tmp/ciencias-indicadores-v4
```

Consulta: `/api/v4/produccion/indicadores/indice`. Descarga individual:
`/api/v4/produccion/indicadores/descarga/{id}?formato=zip`.
[Contenido, filtros, restauración y ejemplo real](docs/PAQUETES_INDICADORES_V4.md).

El [diagnóstico de los ocho pendientes](docs/CIERRE_INDICADORES_V4.md) prepara una revisión acotada
sin consumir Vertex. Requiere autorización para elevar el máximo acumulado de 4.000 a 4.010
llamadas; el tope monetario de USD 3.500 alcanza. Esa ampliación aún no está autorizada.

## Preparaciones de las mallas finales · 26 de octubre de 2026

La entrega V3 contiene **1.128 paquetes: 1.020 objetivos y 108 unidades**, agrupados en **14 ZIP**.
Incluye 4.892 actividades derivadas, criterios, apoyos, aplicación y 14 casos trabajados. Tras cuatro
perspectivas de revisión y una reparación, **1.113 paquetes tienen cuatro lecturas automáticas
favorables y 15 siguen pendientes**: ocho objetivos y siete unidades. El estado se consulta por paquete;
no equivale a eficacia en aula ni aprobación institucional. Son preparaciones, no guiones cronometrados.

La fila de separación de mezclas de 3.º está completada en `edicion_docente`, con fuente MINED,
actividades y criterios específicos; pasó las cuatro lecturas. Los once Excel, sus celdas y los
campos `original` permanecen intactos. [Resultados, crítica y pendientes de cierre](docs/REVISION_DOCENTE_CIENCIAS_V4.md).

Para descargar todos los paquetes del bucket privado aprobado:

```bash
uv sync --extra api
uv run gskg produccion descargar \
  --recibo config/paquetes_produccion_ciencias.lock.json \
  --destino /private/tmp/ciencias-preparaciones-v3
```

El destino debe ser nuevo. Cada ZIP tiene un **LEEME.md** con enlaces a las guías por unidad y objetivo,
JSON de procedencia, Excel original y manifiesto SHA-256. El comando verifica todas las generaciones,
tamaños y SHA; los objetos están en `gs://goes-ai-kg-artefactos/ciencias/v4/`. Requiere acceso GOES.

Para servirlos por API, restaurar en un proyecto sin biblioteca seleccionada:

```bash
uv run gskg materiales restaurar \
  --recibo config/materiales_produccion_ciencias.lock.json \
  --destino data/materiales_produccion_v4
uv run gskg servir --puerto 8011
curl 'http://127.0.0.1:8011/api/v4/produccion/didactica/revision'
curl 'http://127.0.0.1:8011/api/v4/produccion/didactica/habilidades?estado_revision=revision_automatica_completa'
curl 'http://127.0.0.1:8011/api/v4/produccion/didactica/habilidades?completacion_derivada=true'
```

Si ya existe esa carpeta, conservarla con otro nombre antes de restaurar y reiniciar el servidor.
La consulta y las descargas consumen **cero llamadas a modelos**. Detalle JSON, Markdown y ZIP por SHA:
`/api/v4/produccion/materiales`. El contrato está en `/docs`.
Los recibos `_bases.lock.json` y `_didactica_v2.lock.json` conservan las entregas anteriores.

El máximo autorizado sigue en **4.000 llamadas / USD 3.500 de reserva conservadora acumulada**.
El contador vigente es **3.999 / USD 3.275,614266**; queda una llamada, insuficiente para otra revisión
completa. El expediente privado de esta revisión conserva el ledger actualizado y su nuevo punto de
continuidad. Restaurar sólo el corpus histórico recupera un contador anterior y **no habilita gasto**.
No se autorizó la ampliación a 5.200. [Operación y recuperación de V3](docs/REVISION_DOCENTE_CIENCIAS_V4.md).

Validación V3: **1.675 pruebas aprobadas**, Ruff y recuperación independiente desde GCS. Se verificaron
las 26 consultas HTTP y la reanudación de los 20 checkpoints sin llamadas nuevas.

Los resultados descritos a continuación son antecedentes con sus propios insumos y contadores.

## Producto V4 · 22 de octubre de 2026

La entrega de revisión conserva once matrices, 126 hojas, **1.020 filas y 108 unidades** de 2.º a 11.º.
Propone objetivos, indicadores, productos evaluables, criterios, orientaciones y apoyos para El Salvador.
**108 unidades y 1.013 filas de Ciencias tienen respaldo automático completo**; se conservan las
siete filas fuera de Ciencias. La entrega final está seleccionada como producto-4.
[Resultados y reproducción](docs/CURRICULARIZACION_V4.md).

`producto-4` añade propuestas, evidencias y cuatro revisiones sobre el texto exacto. La entrega incluye
Excel y CSV comparados, vista sin conexión y cuatro enmiendas en una copia derivada de Biología.
Los originales, sus alertas, las fases ausentes y todos los resultados anteriores se conservan.
La consulta ofrece `/api/v4/propuestas`, `/api/v4/progresiones` y exportación CSV.

El flujo LangGraph usa ciencia, currículo, psicopedagogía y revisión adversarial, con veto por criterio,
una reparación por protocolo, validación de fuentes, checkpoints y presupuesto acumulativo. Los
especialistas que comparten modelo/proveedor no se consideran estadísticamente independientes.
Las referencias PISA/ERCE, países y NGSS informan el diseño; no se homologan grados ni se afirma
eficacia de aprendizaje. Las doce expectativas NGSS conservan sus bandas nativas.

Los datos y resultados están separados del código público. El respaldo vigente fija **13.762 archivos**
y **41 SQLite** por generación y SHA. Se restauró en una carpeta vacía, se verificaron 2.295 trazas de
lectores y se reanudaron 32 terminales de clases sin nuevas llamadas a Vertex. [Evidencia de recuperación](docs/VERIFICACION_GCS.md).
[Estado de continuidad](docs/CONTINUIDAD_CIENCIAS_V4.md), [operación](docs/OPERACION.md) y
[alcance de publicación](docs/PUBLICACION.md).

La investigación documenta [criterios educativos](docs/investigacion/educacion.md),
[arquitectura de IA](docs/investigacion/arquitectura_ia.md), [roadmap](docs/ROADMAP.md) y
[arquitectura implementada](docs/ARQUITECTURA.md). El recuperador conserva el baseline que ganó la
comparación previa. La expansión terminológica del índice científico mejoró un diagnóstico pequeño;
no se presenta como prueba de superioridad de Agentic RAG.

Las carpetas siguientes corresponden al grafo histórico V3 y se recuperan desde GCS. V4 usa su propia
publicación: las relaciones y propuestas del histórico no se heredan por coincidencias de vocabulario.

| Asignatura | Grados | Carpeta |
|---|---|---|
| Biología | 2.°–11.° | [`asignaturas/biologia`](asignaturas/biologia) |
| Física | 2.°–11.° | [`asignaturas/fisica`](asignaturas/fisica) |
| Química | 2.°–11.° | [`asignaturas/quimica`](asignaturas/quimica) |
| Ciencias de la Tierra y del Espacio | 2.°–9.° | [`asignaturas/ciencias_tierra_espacio`](asignaturas/ciencias_tierra_espacio) |

## Aplicación web y API

La interfaz adapta el diseño HTML aportado al producto real de Ciencias: ocho secciones, filtros,
grafo 3D, revisión de especialistas, comparación curricular, exportaciones y briefs documentales.
Tras restaurar el corpus, iniciar `uv run gskg servir --puerto 8010` y abrir
`http://127.0.0.1:8010/app/`. La API está en `/api/v4/interfaz` y su contrato en `/docs`.
No se consumen modelos para navegar o compilar briefs. [Uso y límites](docs/APLICACION_CIENCIAS.md).


La biblioteca docente está disponible en `/api/v4/materiales`: **1.013 paquetes V4 por objetivo y
108 por unidad**, junto a 150 paquetes V3 y los bancos históricos con sus estados originales.
Se recupera sin descargar todo el corpus con `uv run gskg materiales restaurar`.
[Contenido, procedencia y ejemplos de consulta](docs/MATERIALES_DOCENTES.md).

La ampliación de **guiones completos por objetivo** continúa en revisión. El corte de la campaña P11
del 23 de octubre cubre los 1.013 objetivos: **968 respaldos automáticos y 45 vetos/abstenciones**,
sin objetivos pendientes de primera generación. La revisión directa conserva además hallazgos sobre
versiones con votos favorables y exige una resolución exacta. La entrega completa de 1.013 guiones
y 108 unidades aún no está publicada. Las pruebas de ingeniería pasaron **1.581 casos** y Ruff;
esas pruebas no acreditan exactitud científica o eficacia educativa de todos los guiones.

**Descarga disponible:** preparaciones curriculares con `uv run gskg materiales restaurar`; corpus,
guiones en desarrollo y checkpoints con `uv run gskg datos restaurar --destino /tmp/ciencias-restauradas`.
Ambos comandos verifican las generaciones y SHA fijados en `config/*ciencias.lock.json` y requieren
acceso GOES al bucket `gs://goes-ai-kg-artefactos/ciencias/v4/`. Usar una carpeta nueva; para restaurar
las rutas del proyecto vacío, usar `uv run gskg datos restaurar --en-repo`.

El máximo autorizado sigue siendo acumulado: 4.000 invocaciones/USD 3.500 de reserva. El respaldo
histórico de P11 conserva 3.941 llamadas y un punto mínimo verificable de consumo; no reinicia el contador.
Incluye las fuentes, los resultados y los checkpoints de este corte. El plan documental de
los 45 pendientes necesita hasta 450 llamadas; su preflight queda bloqueado por el límite vigente.
La solicitud anterior de 4.400 llamadas para P11 no amplió el límite ni autoriza reanudarlo.
El 26 de octubre se resolvió conservar el límite actual y entregar las bases de las mallas finales
con revisión pendiente; la ampliación propuesta a 5.200 llamadas/USD 5.500 no fue autorizada.
El corte histórico de P11 conserva 3.941 llamadas, sin reinicio; 34 resoluciones exactas y 2.060 trazas verificadas
en 369 resultados seleccionados. El caso estelar de la muestra sigue bloqueado dentro de los 45 pendientes.
Los borradores conservan tareas, soluciones y expedientes de desarrollo; los resultados pendientes no son
clases liberadas. El recibo del ZIP docente completo se añadirá después de cubrir todos los objetivos y
resolver los defectos. [Estado, operación y contrato de descarga](docs/CLASES_V4.md).

## Inicio rápido
```bash
uv sync --extra dev --extra pdf --extra rag --extra api --extra vertex --extra motor
uv run gskg datos restaurar --en-repo
uv run gskg producto validar
uv run pytest -q
```

Nuevos comandos (sin llamadas a modelos salvo `--ejecutar`):

```bash
uv run gskg motor estado
uv run gskg producto insumo
uv run gskg producto explorar
uv run gskg producto catalogar  # plan local; no envía el corpus
uv run gskg producto unidades listar --grado 10 --asignatura-malla Física
uv run gskg producto conocimiento --salida /tmp/candidatos-v4.json
uv run gskg producto juicios --help
uv run gskg alineacion validar-referentes
uv run gskg investigacion inventariar insumos/v4 --version V4 --salida data/interim/mallas/inventario_v4.json
uv run gskg investigacion recuperacion --salida docs/investigacion/recuperacion_local.json
uv run gskg investigacion jueces data/evaluacion/motor_casos_2026.json --salida /tmp/jueces.json
uv run gskg investigacion referencias estado
uv run gskg investigacion referencias estado --coleccion paises
uv run gskg investigacion referencias validar-dimensiones
uv run gskg motor responder "¿Cómo enseñar la membrana celular?" --grado 9 --asignatura biologia --version V3
```

El motor verifica las citas contra la fuente original y su SHA. Devuelve `abstencion` si falta la versión,
la evidencia o una revisión válida. `respaldado_automaticamente` es un estado técnico, no una confirmación del MINED.
Las llamadas, cachés y checkpoints viven en `data/operaciones/`, fuera de Git. [Operación y límites](docs/OPERACION.md).

## Estado
**Formato del grafo v1**, materializado sobre la **malla V3** del MINED: 3.303 nodos y 18.177 aristas.
- 935 temas de la malla V3. La V3 consolida especialmente Bachillerato; una fila desaparecida no significa que
  desaparezca el concepto. La correspondencia y sus límites están en `specs/15_refuerzo_v3.md`.
- Las versiones anteriores se conservan como evidencia histórica; no describen automáticamente la V4.
- **513 conceptos y 30 prácticas científicas**, con 822 prerrequisitos entre conceptos (un grafo sin ciclos por
  asignatura) y equivalencias entre asignaturas. 14 conceptos vienen del triaje de los que propuso el etiquetado.
- 493 objetivos de los marcos: TIMSS 2027, TIMSS Advanced, PISA 2025 y ACARA Senior Secondary
  (este último es el pivote de Biología y Química de 10.°–11.°).
- 1.265 objetivos de 6 países: Uruguay, Colombia, Singapur, **Inglaterra**, **Australia** y **Japón** (estos cuatro
  últimos en el top 10 de Ciencias de TIMSS 2023, verificado con los anexos oficiales), alineados a TIMSS 2027 y etiquetados con
  conceptos.

**Grafos por grado** (lo que pidió el MINED): [`grados/`](grados/README.md). Cada grado tiene una ficha
(conceptos nuevos y retomados, bloques temáticos, prerrequisitos que llegan tarde y faltantes frente a otros
países) y un **visor interactivo** (`grafo.html`).

**Por asignatura**: `asignaturas/<x>/` tiene la ficha, el **mapa de progresión** (`progresion.html`), las brechas
(md + Excel), las propuestas curriculares en borrador ([resumen](asignaturas/PROPUESTAS.md)) y los CSV de revisión.
Las 11 propuestas (escritas sobre la V1) se conciliaron con la V2: de sus 47 acciones «nuevo», el MINED adoptó 5 en
el mismo grado, 8 en otro grado y 8 en parte. Simuladas sobre la V2, bajan los errores de secuencia de confianza alta
de 55 a 5 (decisiones abiertas para el MINED en cada informe).

**Contraste internacional de 9.°–11.°** (malla V2): [`internacional/`](internacional/README.md). Hay grafos de
9 países de alto desempeño (SG, JP, KR, ENG, AU, HK, TW, EE y ON; 9.040 objetivos extraídos y validados con Vertex
AI), un consenso por concepto y un informe por asignatura con los hallazgos verificados contra las fuentes.
Se construye con `uv run gskg internacional extraer | etiquetar | construir`.

**Apoyo al aprendizaje (prototipo, spec 13)**: un tutor que complementa la malla sin cambiarla: revisa las bases de
un objetivo, comprueba hipótesis con preguntas breves, refuerza, reevalúa con otra actividad y programa repasos.
Tres recorridos de ejemplo en [`aprendizaje/`](aprendizaje/README.md) (`uv run gskg tutor recorridos`); el
contenido pedagógico es propuesta pendiente de revisión y la mejora del aprendizaje requiere un piloto.

**GraphRAG**: `uv run gskg rag "¿qué necesita saber un estudiante antes de genética?" --grado 7`
(recuperación local y citada; `--responder` genera la respuesta con Claude; `--global` busca bloques temáticos).
API de lectura: `uv run gskg servir` (FastAPI, `/docs`). El grafo se verifica y fija por instancia; diagnósticos y simulaciones necesitan publicación de procedencia desde sus generadores. Los derivados históricos sin esa procedencia devuelven `503` hasta regenerarlos; [operación de la API](docs/investigacion/coherencia_api.md). La recuperación se mide con 60 preguntas de ajuste (MRR 0,85) y dos conjuntos de prueba independientes (MRR 0,66 y 0,55) ([resultados](data/evaluacion/resultados.md)).

Lo que sigue (países de alto desempeño, conceptos y prerrequisitos, brechas y propuesta) está en
[`specs/08_plan_de_implementacion.md`](specs/08_plan_de_implementacion.md).

## Secuencia del proceso
Cada paso usa lo que deja el anterior. `make todo` corre los automáticos en este orden y deja el repo sin diferencias si
todo está al día (las salidas son deterministas y una prueba verifica que `data/grafo/` corresponde a las fuentes).

| # | Paso | Comando | Entrada → salida |
|---|---|---|---|
| 1 | Mallas | `gskg temas` | Excel del MINED → `data/interim/temas.json` |
| 2 | Conceptos (con revisión) | `gskg conceptos preparar-* / unir-*` | lotes de subagentes → vocabulario, etiquetado, prerrequisitos |
| 3 | Grafo | `gskg grafo construir` y `validar` | temas, conceptos, marcos y países → `data/grafo/` |
| 4 | Lecturas del grafo | `gskg fichas`, `grados construir`, `brechas`, `progresion` | grafo → `asignaturas/`, `grados/` |
| 5 | Propuestas (con revisión) | `make propuestas` | propuestas → simulación, Excel y `asignaturas/PROPUESTAS.md` |
| 6 | Internacional | `make internacional` (o `make internacional-ia` con Vertex) | países y malla V2 → `internacional/` |

## Cómo continuar con Claude Code
El repo trae su propio harness: hooks que protegen `.env` y las fuentes, piden aprobación antes de gastar en Vertex y
exigen la cuenta GOES y pruebas en verde para hacer commit; además, un subagente verificador y skills por proceso
(`.claude/hooks/README.md`).
Abre Claude Code en esta carpeta y pega [`prompts/00_montar_proyecto.md`](prompts/00_montar_proyecto.md).
Claude Code lee [`CLAUDE.md`](CLAUDE.md), las [specs](specs/) y las skills de `.claude/skills/`.

## Estructura
```
asignaturas/   una carpeta por asignatura (README + ficha generada; luego brechas y propuesta)
config/        reglas en YAML: mallas, asignaturas, marcos pivote, países de referencia
src/           paquete goes_science_kg (CLI gskg)
docs/          investigación, decisiones de arquitectura, roadmap y operación actual
data/fuentes/  mallas del MINED y PDF de marcos y países (solo lectura)
data/grafo/    el grafo versionado (JSONL + manifest)
specs/         especificación y plan
reportes/      trabajo previo: cobertura TIMSS/PISA y comparación con países
prompts/       instrucciones para Claude Code
```

## Reportes
- [`reportes/cobertura_curricular/`](reportes/cobertura_curricular): trabajo previo (antes `goes-science-kg-II`).
  Mide la cobertura de las mallas frente a TIMSS 2027/2023, TIMSS Advanced 2015 y PISA 2025, y la compara
  con Uruguay, Colombia y Singapur. Sus scripts se ejecutan desde esa carpeta (ver su `CLAUDE.md`).

## Fuentes y licencias
El código es del equipo GOES. Los documentos de `data/fuentes/` pertenecen a sus autores (ver [`NOTICE`](NOTICE)).
