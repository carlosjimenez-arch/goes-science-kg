# goes-science-kg

Grafo de conocimiento de **Ciencias** para El Salvador. Une la malla del MINED (2.° a 11.°) con los
marcos internacionales (TIMSS 2027, TIMSS Advanced, PISA 2025) y con los currículos de otros
países. El fin es **proponer, por asignatura, una curricularización mejor y con evidencia**.

Los datos, PDF y entregables se recuperan desde el bucket institucional con
`uv run gskg datos restaurar --en-repo`. Sus rutas están ignoradas por Git.
[Restauración, inventario y migración verificable](docs/DATOS_EXTERNOS.md).

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

Los datos y resultados están separados del código público. El respaldo final fija **7.580 archivos**
por generación y SHA, con restauración completa y reanudación de los once terminales P6/P7 sin nuevas
llamadas a Vertex. [Evidencia de recuperación](docs/VERIFICACION_GCS.md).
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
