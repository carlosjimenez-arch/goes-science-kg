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
      ├─▶ fichas.py / analisis/ / propuesta/    (por asignatura)
      ▼
asignaturas/<x>/       ENTREGABLES              ficha.md · brechas/ · propuesta/
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
| **reportes/ se conserva** | Es el trabajo previo y fuente de los catálogos. El paquete nuevo lo lee y nunca lo modifica. |

## Paquete `src/goes_science_kg/`
| Módulo | Responsabilidad | Estado |
|---|---|---|
| `config.py` | Raíz del repo y lectura de `config/*.yaml` | ✅ |
| `modelos.py` | Nodos, aristas, evidencia e invariantes | ✅ |
| `ingesta/mallas.py` | Excel MINED → temas con id estable | ✅ |
| `ingesta/legado.py` | Lee catálogos y clasificaciones de `reportes/` | ✅ |
| `disciplinas.py` | Tema u objetivo → asignatura | ✅ |
| `grafo/construir.py` | Arma el grafo v0 | ✅ |
| `grafo/validar.py` | Invariantes: errores y avisos | ✅ |
| `grafo/almacen.py` | JSONL ↔ objetos ↔ networkx | ✅ |
| `fichas.py` | `asignaturas/<x>/ficha.md` | ✅ |
| `ingesta/paises.py` | Objetivos de países nuevos → `data/interim/paises/` | ⏳ fase 1 |
| `ia/lotes.py` | Preparar y unir lotes de subagentes (genérico) | ⏳ fase 1 |
| `grafo/conceptos.py` | Capa de conceptos y prerrequisitos | ⏳ fase 3 |
| `analisis/` | Brechas por asignatura y ciclo | ⏳ fase 4 |
| `propuesta/` | Propuesta curricular por asignatura | ⏳ fase 5 |

## Convenciones
- Python 3.11+, `uv`, `ruff` (120 columnas), `pytest`. Código, datos y documentación en español.
- Rutas siempre relativas a la raíz (`config.ruta()`), nunca al directorio de trabajo.
- Salidas deterministas: ordenar antes de escribir. El mismo insumo debe dar el mismo SHA-256.
- Ningún módulo escribe en `data/fuentes/` ni en `reportes/`.
