# Continuidad · GOEs AI · feat/api

Corte: 25 de octubre de 2026. Estado vigente en [README](README.md), [documentación](docs/README.md) y la
[auditoría integral de producto](docs/auditoria/QA_PRODUCTO_20261025.md).

## Qué es la entrega

`feat/api` es **un solo producto**. Integra la API y la aplicación homogeneizadas con la biblioteca docente,
el código de guiones P1–P11 y el respaldo de `feat/ciencias-v4` (merge `ef411f3`). Añade la capa de
conceptos V4 y la progresión 2.º–11.º con sus vistas. La rama `feat/ciencias-v4` queda contenida en
`feat/api`; no hay otra línea de producto pendiente de integrar.

- Publicación `producto-4`, snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`:
  1.020 originales, 1.013 propuestas de Ciencias, 7 fuera de alcance, 108 unidades y 30 alertas que las
  propuestas corregidas no levantan.
- Aplicación con diez secciones, incluidas **Progresión 2.º–11.º** y **Materiales docentes**.
- Biblioteca docente `5b64ee…` con 2.867 registros; no equivale a guiones cronometrados.
- Progresión: [método, resultados y límites](docs/PROGRESION_2_11.md). Sus listas son triaje para expertos.

## Datos

Todo el corpus y los derivados están en `gs://goes-ai-kg-artefactos/ciencias/v4/`, fuera de Git.
`config/datos_ciencias.lock.json` fija el ZIP `06398b9e…` (13.919 archivos, 41 SQLite). Un checkout limpio
restauró todo desde el bucket y pasó 1.693 pruebas sin omisiones. [Verificación](docs/VERIFICACION_GCS.md).
La generación intermedia `59151f1e…` se subió antes de la revisión adversarial y no se adoptó.

El corpus local está restaurado y es idéntico al recibo, salvo las bases operativas en WAL que el paquete
guarda como copia consistente. Los SQLite locales reemplazados al adoptar el corte P11 quedaron respaldados en
`../_respaldos/goes-science-kg/20261025_previo_a61846/`, fuera del repositorio. No repetir restauraciones
sobre rutas existentes.

Para producir datos derivados nuevos: generar, respaldar con `gskg datos preparar|subir`, restaurar en un
checkout limpio y sólo entonces adoptar el recibo en un commit revisado.

## Presupuestos y campañas

El ledger registra 4.442 invocaciones (reserva conservadora USD 2.961,97, no factura); la campaña de guiones
`ciencias_v4_curricularizacion_20261022` conserva 3.941 de su máximo acumulado de 4.000 llamadas y USD 3.500.
Quedan 45 objetivos sin guion liberable (27 vetos y 18 abstenciones). **El usuario decidió el 25 de octubre
no ampliar a 4.400 llamadas por ahora**: los guiones siguen como borradores y no se publican. Esta sesión
no consumió Vertex; el etiquetado V4 lo hicieron agentes de lote validados por reglas.

`clases/` y `cli/clases.py` tienen bytes congelados por la campaña abierta (excepción de estilo documentada,
como los extractores). Reanudarla exige autorización explícita y el mismo código.

## Pendientes

1. Decisión sobre la ampliación de guiones y, si se aprueba, auditoría de los 45 pendientes antes de compilar.
2. Revisión experta del triaje de prerrequisitos (28 prioritarios: 3 confirmados, 18 parciales, 7 refutados)
   y de las observaciones de fuente para el MINED.
3. Decisión sobre los 173 conceptos que faltan en el vocabulario y el reparto de `configuracion-electronica`.
4. Identidad institucional y control de acceso antes de exponer la aplicación fuera del equipo.
5. Política de retención en el prefijo `ciencias/v4/` del bucket compartido (requiere su responsable).

La aprobación del MINED, el piloto con usuarios y la eficacia de aprendizaje son procesos separados.
