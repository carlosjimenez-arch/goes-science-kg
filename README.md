# goes-science-kg

Grafo de conocimiento de **Ciencias** para El Salvador. Une la malla del MINED (2.° a 11.°) con los
marcos internacionales (TIMSS 2027, TIMSS Advanced, PISA 2025) y con los currículos de otros
países. El fin es **proponer, por asignatura, una curricularización mejor y con evidencia**.

## Reconstrucción del producto (2026-10-21)

El producto y las evidencias V4 descritos aquí corresponden al entorno institucional local. La rama
pública distribuye el código y su documentación; los insumos nuevos se conservan aparte.
[Alcance del envío y reproducción](docs/PUBLICACION.md).

La entrega V4 es el objetivo de la reconstrucción. **El grafo histórico de este checkout sigue siendo V3**:
no se etiqueta como V4 ni se trasladan inferencias sin comparar las fuentes. La copia local de Descargas estaba
bloqueada por macOS; se recuperaron once matrices de la carpeta institucional V4 mediante el Drive conectado.
Los originales están en `insumos/v4/`, con procedencia y SHA en `insumos/procedencia_v4.json`. La ingesta
ya conserva las 126 hojas, 1.020 filas curriculares y sus campos/celdas. La continuación autorizada
produjo 384 asignaturas declaradas, 561 coincidencias, 68 abstenciones y siete fuera de alcance.
La [publicación V4 local](data/producto/V4/actual.json) ya está disponible para el runtime V4;
el grafo y la configuración históricos siguen siendo V3. [Contabilidad y límites](docs/investigacion/catalogacion_v4.md).

El [explorador V4 local](data/producto/explorador_v4.html) permite filtrar por grado, unidad y disciplina,
examinar fuentes y alertas y exportar Markdown sin conexión. Es una captura de revisión del insumo y del
catálogo completo, incluidas las abstenciones; no equivale a una currícula mejorada aprobada.
Se regenera con `gskg producto explorar --catalogo data/producto/V4/catalogo_disciplinas.json`.

La investigación y las decisiones están en [el roadmap](docs/ROADMAP.md), [la arquitectura](docs/ARQUITECTURA.md),
[la investigación educativa](docs/investigacion/educacion.md) y [la investigación de IA](docs/investigacion/arquitectura_ia.md).
El catálogo nuevo `config/referentes_2026.yaml` distingue fuentes verificadas, pendientes de ingesta y borradores.
PISA 2025 tiene marco final y resultados publicados; ERCE 2025 aún no tiene resultados al corte de investigación.
Cuatro PDF de marcos/resultados (689 páginas), incluido el reporte técnico ERCE 2019 publicado en 2025, están fijados
por SHA en [el almacén de referencias](data/referencias_2026/README.md). Hay 22 dimensiones de muestra y
[29 criterios operativos PISA/ERCE](docs/investigacion/referentes_operativos_2026.md) con anclas documentales;
su validación no acredita alineación de la V4.

Una [colección de países](data/referencias_paises_2026/README.md) fija otros 12 PDF y 2.028 páginas de
Inglaterra, Singapur y Japón, con ediciones, cohortes, modalidades y traducciones diferenciadas. Se cotejó
la revisión MOE enero 2026 con los bytes existentes. Los DOCX/HTML australianos ya aportan evidencia
por código oficial: quedan 602 candidatos históricos sin hidratador frente a 1.047 inicialmente;
ningún vínculo se acepta por esa mejora documental.

La ejecución de [una unidad real de Física de 10.º](data/producto/unidades/fisica-10-v4-catalogada/paquete.md)
conserva sus ocho objetivos, evidencias y contexto de aula: cuatro sesiones obtuvieron respaldo automático
y cuatro quedaron en abstención. Consumió 58 intentos y USD 7,4261195 de reserva; reanudar recuperó
los ocho checkpoints sin generar ni gastar. [Resultados y límites](docs/investigacion/resultados_unidad_fisica10_v4.md).
La [entrega experimental íntegra](data/producto/unidades/fisica-10-entrega-experimental/unidad.md)
conserva ocho objetivos y respaldo automático por objetivo en nueve encuentros propuestos de sesenta
minutos: mantiene siete propuestas de la cohorte completa y organiza el objetivo de seno/coseno en
dos encuentros. El escenario uniforme de sesenta minutos conserva su abstención y todos los estados
anteriores siguen auditables. [Verificación, presupuesto y límites](docs/investigacion/entrega_unidad_fisica10_20261021.md).
El [descubrimiento de conocimiento V4](docs/investigacion/conocimiento_v4.md) produjo 6.901 hipótesis
con evidencia localizada; son candidatos para cotejo, sin admisión automática ni prerrequisitos verificados.
El [flujo de juicios semánticos](docs/juicios_conocimiento.md) prepara cada enlace con fuentes rehidratadas,
cuatro lectores ciegos y vetos por criterio. La consolidación reconstruye dictámenes y comprueba ciclos entre
lotes. La publicación y la recuperación por fila ya incorporan esos archivos verificados, con evidencias
deduplicadas y relaciones limitadas al objetivo solicitado. La publicación actual conserva quince juicios
reales: dos respaldos, seis rechazos y siete abstenciones, sin progresiones verificadas. La composición
conserva los protocolos originales y comprueba ciclos entre cohortes. Falta calibración independiente.
La [medición de contexto](docs/investigacion/contexto_conocimiento_v4.md) pasó de 509 a 1.166 expedientes
preparables de 1.203 con el mismo límite, sin llamadas a modelos. Ese resultado es estructural, no educativo.

La base nueva incorpora inventario de Excel, CLI por grupos, importaciones absolutas, recuperación léxica/densa,
contratos de evidencia, un workflow LangGraph con tres revisores, presupuesto durable, checkpoints y abstención.
La comparación local conserva el recuperador anterior: el candidato más rápido perdió calidad en varias pruebas.
Los experimentos no equivalen a validación del aprendizaje.
La [medición del baseline V4 publicado](docs/investigacion/resultados_baseline_v4_catalogado.md)
registra cobertura y fallos sobre las mismas 19 consultas ya abiertas, sin cambiar ranking ni prompts.
La entrega experimental conserva ocho objetivos respaldados bajo su escenario de nueve encuentros.
La [continuación de Ciencias](docs/investigacion/continuacion_ciencias_20261021.md)
registra los juicios, comparación de formatos, lectura primaria completa, API V4, escenarios y consumo.
La API `/api/v4` consulta publicaciones verificadas y prepara unidades sin ejecutar modelos.

La publicación local `producto-3` incorpora los cuatro casos PISA/ERCE originales y conserva todos sus
estados. Un respaldo documental se limita a su fila; la API permite auditar fuentes y lectores.
El contexto reserva las páginas admitidas antes del relleno opcional o se abstiene si no caben.
[Contrato, reproducción y límites](docs/investigacion/integracion_alineaciones_v4.md).
La nueva [colección NGSS](docs/investigacion/progresiones_ngss_20261021.md) fija tres documentos oficiales
y 58 páginas; no afirma progresiones locales respaldadas ni equivalencias automáticas de grados.

| Asignatura | Grados | Carpeta |
|---|---|---|
| Biología | 2.°–11.° | [`asignaturas/biologia`](asignaturas/biologia) |
| Física | 2.°–11.° | [`asignaturas/fisica`](asignaturas/fisica) |
| Química | 2.°–11.° | [`asignaturas/quimica`](asignaturas/quimica) |
| Ciencias de la Tierra y del Espacio | 2.°–9.° | [`asignaturas/ciencias_tierra_espacio`](asignaturas/ciencias_tierra_espacio) |

## Inicio rápido
```bash
uv sync --extra dev --extra pdf --extra rag --extra api --extra vertex --extra motor
uv run gskg grafo construir    # arma el grafo en data/grafo/
uv run gskg grafo validar      # revisa invariantes
uv run gskg fichas             # genera asignaturas/<x>/ficha.md
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
