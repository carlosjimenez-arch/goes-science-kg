# 01 · Arquitectura

## Capas
```
data/fuentes/          FUENTES (solo lectura)   mallas MINED, PDF de marcos y de países
      │
      ▼  ingesta/      mallas.py (Excel → temas) · legado.py (catálogos y clasificaciones previas)
data/interim/          INTERMEDIOS              temas.json, lotes de IA, objetivos de países
      │
      ▼  grafo/        construir.py → validar.py → almacen.py
data/grafo/            GRAFO (fuente de verdad) nodos.jsonl · aristas.jsonl · manifest.json
      │
      ├─▶ fichas.py · brechas.py · progresion.py · propuesta.py   (por asignatura)
      ├─▶ grados.py · rag.py · api.py                               (por grado y consultas)
      ▼
asignaturas/<x>/ · grados/   ENTREGABLES        ficha.md · brechas/ · propuesta/ · G<gg>/
```

## Decisiones
| Decisión | Motivo |
|---|---|
| El grafo vive en **JSONL en git** (`data/grafo/`) | Se puede revisar por diff, es reproducible y no necesita servidor. Neo4j o GraphML son proyecciones (`gskg grafo exportar`). |
| **Pydantic** define el contrato (`modelos.py`) | Valida al construir. La spec 02 y el código deben coincidir. |
| **Pivote = marcos internacionales** | Compara currículos con distinta estructura sin emparejar país contra país. |
| **IA con trazabilidad** | Toda arista inferida trae confianza, justificación (≤15 palabras) y versión. Las de confianza «baja» van a revisión humana. |
| **Subagentes por lote** para clasificar o alinear | Paralelismo controlado: un lote por grado, país o asignatura. Se unen con un script determinista. |
| **Config en YAML** (`config/`) | Las reglas de negocio se cambian sin tocar código. |
| **Malla vigente = V2** (`config/mallas.yaml`, desde el 2026-10-11) | Contiene los 1.260 temas de la V1 sin cambios (mismo id, hoja, fila y texto) y agrega 47. Etiquetas, revisiones y propuestas siguen valiendo; la V1 queda en `config/mallas_v1.yaml`. |
| **reportes/ se conserva** | Es el trabajo previo y fuente de los catálogos. El paquete nuevo lo lee y nunca lo modifica. |

## Paquete `src/goes_science_kg/`
| Módulo | Responsabilidad |
|---|---|
| `config.py` | Raíz del repo y lectura de `config/*.yaml` |
| `modelos.py` | Contrato del grafo: nodos, aristas, evidencia e invariantes |
| `ingesta/mallas.py` | Excel del MINED → temas con id estable (malla vigente: V2, `config/mallas.yaml`) |
| `ingesta/legado.py` | Catálogos y clasificaciones de `reportes/` (solo lectura), traducidos a la malla vigente |
| `ingesta/acara.py` | Catálogo de ACARA Senior Secondary (pivote de Biología y Química de 10.°–11.°) |
| `alineacion.py` | Lotes de alineación de temas contra un pivote (AUSS; TIMSS y PISA para los temas nuevos de la V2) |
| `disciplinas.py` | Tema u objetivo → asignatura |
| `conceptos.py` | Capa de conceptos y prácticas: vocabulario, etiquetado de temas y de países, triaje y divisiones |
| `prerrequisitos.py` | Prerrequisitos entre conceptos: un DAG por asignatura |
| `revisiones.py` | Revisiones humanas que ganan sobre la IA |
| `grafo/construir.py` · `validar.py` · `almacen.py` | Arma el grafo, verifica invariantes, JSONL ↔ objetos ↔ networkx |
| `fichas.py` · `brechas.py` · `progresion.py` | Lecturas por asignatura: ficha, brechas (md, csv y Excel) y mapa de progresión |
| `grados.py` · `comunidades.py` · `visor.py` | Grafo por grado, bloques temáticos y visor HTML (spec 09) |
| `propuesta.py` | Propuesta curricular por ciclo y simulador sobre el grafo (spec 06) |
| `rag.py` · `evaluacion.py` · `api.py` | GraphRAG citado, su evaluación y la API de lectura (spec 10) |
| `revision_humana.py` · `revision_decisiones.py` | Circuito de revisión con el MINED: etiquetas y decisiones de contenido (spec 07) |
| `excel.py` | Guardado determinista de libros de Excel |
| `internacional/` | Estudio internacional por tramo (`tramo.py`): Vertex (`vertex.py`), `extraer.py`, `etiquetar.py`, `consenso.py`, `contraste.py`, `profundidad.py`, `informe.py`, `visor.py` (specs 11 y 12) |
| `cli.py` | CLI `gskg`: un comando por etapa (spec 04) |

## Convenciones
- Python 3.11+, `uv`, `ruff` (120 columnas), `pytest`. Código, datos y documentación en español.
- Rutas siempre relativas a la raíz (`config.ruta()`), nunca al directorio de trabajo.
- Salidas deterministas: ordenar antes de escribir. El mismo insumo debe dar el mismo SHA-256.
- Ningún módulo escribe en `data/fuentes/` ni en `reportes/`.
