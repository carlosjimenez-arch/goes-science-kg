# Continuidad · GOEs AI · feat/api

Corte: 25 de octubre de 2026. Estado vigente en [README](README.md), [documentación](docs/README.md) y la
[auditoría integral de producto](docs/auditoria/QA_PRODUCTO_20261025.md).

## Qué es la entrega

`feat/api` es **un solo producto local**: currículo V4 `producto-4` con propuestas revisadas, grafo con
progresión 2.º–11.º, biblioteca docente con **994 guiones de clase y 108 de unidad**, API y aplicación de diez
secciones. Integra `feat/ciencias-v4` (merge `ef411f3`); no queda otra línea de producto pendiente.

- Snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`: 1.020 originales, 1.013
  propuestas de Ciencias, 7 fuera de alcance, 108 unidades y 30 alertas que las propuestas no levantan.
- Progresión: [método, resultados y límites](docs/PROGRESION_2_11.md); sus listas son triaje para expertos.
- Guiones: [entrega, revisión directa y pendientes](docs/CLASES_V4.md). 19 objetivos declarados sin guion.

## Datos: todo desde el bucket

`gs://goes-ai-kg-artefactos/ciencias/v4/`, fuera de Git, con cuatro recibos:

| Recibo | Identidad |
|---|---|
| `config/datos_ciencias.lock.json` | Corpus `d812b22d…`, 28.330 archivos |
| `config/materiales_ciencias.lock.json` | Biblioteca ampliada `5b80b556…`, 3.969 registros |
| `config/clases_ciencias.lock.json` | Entrega de guiones `9d949257…` |
| `config/materiales_preparaciones.lock.json` | Biblioteca base `5b64ee…` que fijan las preparaciones |

`make producto` instala, sincroniza lo que falte y sirve. `gskg datos estado|verificar|sincronizar|publicar`
gestionan el ciclo; `publicar` sólo adopta un recibo tras restaurar y comparar. Un checkout limpio restauró
todo desde GCS y pasó 1.702 pruebas sin omisiones. Las generaciones anteriores siguen en el bucket.
Los respaldos locales de bibliotecas y SQLite reemplazados están fuera del repo en
`../_respaldos/goes-science-kg/`.

## Presupuestos

Campaña `ciencias_v4_curricularizacion_20261022`: tope acumulado ampliado por el usuario el 25 de octubre a
4.400 llamadas con USD 3.500 (recibo literal anclado por SHA). Consumo: **4.294 llamadas y USD 3.219,5365** de
reserva (no factura). Quedan 106 llamadas: no alcanzan para otra ronda de los 19 pendientes (hasta 190).
`clases/` mantiene bytes congelados en sus módulos con huella; los módulos sin huella se corrigieron
(ver [Calidad](docs/CALIDAD.md)).

## Pendientes

1. Revisión de especialistas por muestreo de los 968 guiones que sólo tienen respaldo automático (la cohorte
   recuperada tuvo 37 % de defectos materiales en revisión directa).
2. Decidir los 19 objetivos sin guion: nueva ampliación de presupuesto o redacción docente.
3. Revisión experta del triaje de prerrequisitos y de las observaciones de fuente para el MINED.
4. Vocabulario: 173 conceptos propuestos y el reparto de `configuracion-electronica`.
5. Identidad y control de acceso si la aplicación deja de ser local.

La aprobación del MINED, el piloto con usuarios y la eficacia de aprendizaje son procesos separados.
