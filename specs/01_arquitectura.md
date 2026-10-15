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
      ├─▶ aprendizaje/ · panel · refuerzo_v3                         (componentes y revisión)
      └─▶ motor/ + insumos de cobertura V3                         (contrato, exportación, validación)
      ▼
asignaturas/<x>/ · grados/   ENTREGABLES        ficha.md · brechas/ · propuesta/ · G<gg>/
entregas/motor/<versión>/    ENTREGA MOTOR     JSONL · catálogos · esquemas · manifiesto SHA-256
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
| **Malla vigente = V3** (`config/mallas.yaml`, desde el 2026-10-13) | 935 temas; los heredados conservan su id por correspondencia. Grado, unidad y orden actuales se leen como atributos, nunca desde el id. V1 y V2 quedan como historia. |
| **reportes/ se conserva** | Es el trabajo previo y fuente de los catálogos. El paquete nuevo lo lee y nunca lo modifica. |
| **Entrega independiente del motor** (spec 16) | Catálogo, grafo, análisis y componentes conservan sus procedencias. Se importan por identidad de entrega; activar o revertir cambia solo un puntero. Aula no está habilitada en v0.1. |

## Paquete `src/goes_science_kg/`
| Módulo | Responsabilidad |
|---|---|
| `config.py` | Raíz del repo y lectura de `config/*.yaml` |
| `modelos.py` | Contrato del grafo: nodos, aristas, evidencia e invariantes |
| `ingesta/mallas.py` | Excel del MINED → temas con id estable (malla vigente: V3, `config/mallas.yaml`) |
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
| `motor/` | Puente exacto de identidades V3, contrato, exportador, permisos por componente, validador portátil y consumidor de referencia (spec 16) |
| `secuencias_ia.py` | Candidatas de los 920 temas, cadena de dictámenes con citas y huellas, adaptación psicopedagógica y retenciones por desacuerdo (spec 17) |
| `cli.py` | CLI `gskg`: un comando por etapa (spec 04) |

## Convenciones
- Python 3.11+, `uv`, `ruff` (120 columnas), `pytest`. Código, datos y documentación en español.
- Rutas siempre relativas a la raíz (`config.ruta()`), nunca al directorio de trabajo.
- Salidas deterministas: ordenar antes de escribir. El mismo insumo debe dar el mismo SHA-256.
- Ningún módulo escribe en `data/fuentes/` ni en `reportes/`.
