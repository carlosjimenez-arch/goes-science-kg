# Auditoría de versionado · GOEs · 22 de octubre de 2026

La revisión de `feat/api` complementa la entrega técnica del PR #1. `.gitignore` pasó de 280 a
118 líneas: conserva reglas del proyecto y retira bloques de frameworks y herramientas sin
consumidores configurados en este repositorio.

## Hallazgos y corrección

Las reglas anteriores dejaron **17 de los 49 escenarios de versionado** sin protección. Las
regresiones reprodujeron los fallos antes del cambio; las 49 pasan con las reglas nuevas.

| Familia | Política actual |
|---|---|
| Secretos | `.env`, `.env.*`, `*.env`, `.envrc.*`, directorios de credenciales y claves privadas |
| Plantillas | `.env.example` y `.env.template` permanecen visibles; sólo admiten valores ficticios al versionarlas |
| Operación | SQLite, WAL, SHM, journals, vectores y respaldos se ignoran también fuera de `data/` |
| Corpus | Se mantienen raíces privadas de datos, insumos, entregas y productos históricos |
| Herramientas | Configuración personal, entornos, cachés, temporales e informes generados |
| Contratos públicos | `uv.lock`, `config/*.lock.json`, YAML, código, pruebas, prompts, badges y assets siguen visibles |

No se excluyen JSON o archivos lock de forma general: ocultarían recibos y contratos necesarios.
Se preservan imágenes y fuentes que el paquete necesita distribuir. Las pruebas usan repositorios
Git temporales y nombres sintéticos; no leen secretos ni requieren corpus.

## Inventario y limpieza

`git ls-files -ci --exclude-standard` no encontró archivos ya versionados que coincidan con estas
reglas. La visibilidad de raíces y recibos se contrasta con `git check-ignore`. La exclusión no
elimina archivos existentes ni objetos del historial y no sustituye la revisión antes de publicar.
Se conservaron fuentes, snapshots, dictámenes, ledgers y el recibo de restauración.

El inventario conserva `cli/__main__.py` como entrada pública. No aparecieron nuevos módulos
demostrablemente prescindibles tras la retirada documentada de `refuerzo_excel.py`. Los antecedentes
se mantienen por sus decisiones y evidencia referenciada. La edad o la ausencia de imports entrantes
no bastan para eliminar un archivo.

## Reproducción

```bash
uv run --frozen pytest -q tests/test_gitignore.py
uv run --frozen pytest -q tests/test_observabilidad_http.py tests/test_metricas_calidad.py
make auditoria
git ls-files -ci --exclude-standard
git diff --check
```

La huella de métricas incluye `.gitignore`, `Makefile` y el workflow además de código, pruebas y
dependencias. Un cambio de política invalida su correspondencia con una medición anterior.
Resultados vigentes: [medicion.json](../badges/medicion.json).

## Validación de esta revisión

La suite integral pasó **1.462 pruebas**, sin fallos, omisiones ni advertencias, en 276,75 s.
La cobertura de líneas es **79,40 %** (15.711 / 19.787). La copia sin corpus aprobó **205 contratos**;
registró una advertencia de deprecación del SDK Google sobre Python 3.17. Las seis regresiones
JavaScript pasan. Ruff y formato comprueban 296 archivos Python.

Las consultas reales conservaron las 1.020 filas, 1.013 propuestas, 108 unidades y 35 documentos del
snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`. El ledger mantuvo
SHA `3ad9b798421a8b463f8d3dd924498330b42ddbd483ca4f774c5386bb74f722ae`. Los dos extractores
y el CSS principal conservan sus bytes. No se ejecutaron modelos, restauraciones o servicios cloud.
