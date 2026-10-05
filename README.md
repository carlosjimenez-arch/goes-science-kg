# goes-science-kg

Grafo de conocimiento de **Ciencias** para El Salvador. Une la malla del MINED (2.° a 11.°) con los
marcos internacionales (TIMSS 2027, TIMSS Advanced, PISA 2025) y con los currículos de otros
países. El fin es **proponer, por asignatura, una curricularización mejor y con evidencia**.

| Asignatura | Grados | Carpeta |
|---|---|---|
| Biología | 2.°–11.° | [`asignaturas/biologia`](asignaturas/biologia) |
| Física | 2.°–11.° | [`asignaturas/fisica`](asignaturas/fisica) |
| Química | 2.°–11.° | [`asignaturas/quimica`](asignaturas/quimica) |
| Ciencias de la Tierra y del Espacio | 2.°–9.° | [`asignaturas/ciencias_tierra_espacio`](asignaturas/ciencias_tierra_espacio) |

## Inicio rápido
```bash
uv sync --extra dev --extra pdf --extra analisis --extra rag --extra api
uv run gskg grafo construir    # arma el grafo en data/grafo/
uv run gskg grafo validar      # revisa invariantes
uv run gskg fichas             # genera asignaturas/<x>/ficha.md
uv run pytest -q
```

## Estado
**Grafo v1**: 3.286 nodos y 17.753 aristas.
- 1.260 temas de la malla (1.245 en alcance y 15 de tecnología o transversales fuera de alcance).
- **498 conceptos y 30 prácticas científicas**, con 797 prerrequisitos entre conceptos (un grafo sin ciclos por
  asignatura) y 11 equivalencias entre asignaturas.
- 493 objetivos de los marcos: TIMSS 2027, TIMSS Advanced, PISA 2025 y ACARA Senior Secondary
  (este último es el pivote de Biología y Química de 10.°–11.°).
- 928 objetivos de 5 países: Uruguay, Colombia, Singapur, **Inglaterra** y **Australia** (estos tres últimos en el
  top 10 de Ciencias de TIMSS 2023, verificado con los anexos oficiales), alineados a TIMSS 2027 y etiquetados con
  conceptos.

**Grafos por grado** (lo que pidió el MINED): [`grados/`](grados/README.md). Cada grado tiene una ficha
(conceptos nuevos y retomados, bloques temáticos, prerrequisitos que llegan tarde y faltantes frente a otros
países) y un **visor interactivo** (`grafo.html`).

**Por asignatura**: `asignaturas/<x>/` tiene la ficha, el **mapa de progresión** (`progresion.html`), las brechas
(md + Excel), las propuestas curriculares en borrador ([resumen](asignaturas/PROPUESTAS.md)) y los CSV de revisión.

**GraphRAG**: `uv run gskg rag "¿qué necesita saber un estudiante antes de genética?" --grado 7`
(recuperación local y citada; `--responder` genera la respuesta con Claude; `--global` busca bloques temáticos).
API de lectura: `uv run gskg servir` (FastAPI, `/docs`). La recuperación se mide con 52 preguntas: MRR 0,79 y recall@25 0,86 ([resultados](data/evaluacion/resultados.md)).

Lo que sigue (países de alto desempeño, conceptos y prerrequisitos, brechas y propuesta) está en
[`specs/08_plan_de_implementacion.md`](specs/08_plan_de_implementacion.md).

## Cómo continuar con Claude Code
Abre Claude Code en esta carpeta y pega [`prompts/00_montar_proyecto.md`](prompts/00_montar_proyecto.md).
Claude Code lee [`CLAUDE.md`](CLAUDE.md), las [specs](specs/) y las skills de `.claude/skills/`.

## Estructura
```
asignaturas/   una carpeta por asignatura (README + ficha generada; luego brechas y propuesta)
config/        reglas en YAML: mallas, asignaturas, marcos pivote, países de referencia
src/           paquete goes_science_kg (CLI gskg)
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
