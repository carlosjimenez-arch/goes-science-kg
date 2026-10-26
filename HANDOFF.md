# Continuidad · GOEs AI · feat/api

Corte: 25 de octubre de 2026. Estado vigente en [README](README.md), [documentación](docs/README.md) y la
[auditoría integral de producto](docs/auditoria/QA_PRODUCTO_20261025.md).

## Qué es la entrega

`feat/api` es **un solo producto local**: currículo V4 `producto-4` con propuestas revisadas, grafo con
progresión 2.º–11.º, biblioteca docente con **862 guiones de clase (todos con revisión directa) y 108 de unidad**, API y aplicación de diez
secciones. Integra `feat/ciencias-v4` (merge `ef411f3`); no queda otra línea de producto pendiente.

- Snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`: 1.020 originales, 1.013
  propuestas de Ciencias, 7 fuera de alcance, 108 unidades y 30 alertas que las propuestas no levantan.
- Progresión: [método, resultados y límites](docs/PROGRESION_2_11.md); sus listas son triaje para expertos.
- Guiones: [entrega, revisión directa integral y pendientes](docs/CLASES_V4.md). 151 objetivos declarados sin guion:
  los 19 anteriores y 132 retirados por defectos materiales hallados al revisar los 968 sin revisión directa.

## Datos: todo desde el bucket

`gs://goes-ai-kg-artefactos/ciencias/v4/`, fuera de Git, con cuatro recibos:

| Recibo | Identidad |
|---|---|
| `config/datos_ciencias.lock.json` | Corpus `20c6e813…`, 29.086 archivos |
| `config/materiales_ciencias.lock.json` | Biblioteca `8af1b65d…`, 3.837 registros |
| `config/clases_ciencias.lock.json` | Entrega de guiones `e4b32786…` (862 + 108) |
| `config/materiales_preparaciones.lock.json` | Biblioteca base `5b64ee…` que fijan las preparaciones |

`make producto` instala, sincroniza lo que falte y sirve. `gskg datos estado|verificar|sincronizar|publicar`
gestionan el ciclo; `publicar` sólo adopta un recibo tras restaurar y comparar. Un checkout limpio restauró
todo desde GCS y pasó la suite completa sin omisiones. Las generaciones anteriores siguen en el bucket.
Ningún archivo versionado ni recibo guarda rutas de una estación de trabajo (`tests/test_sin_rutas_locales.py`);
la identidad del ledger es nombre, dispositivo e inodo.
Las copias de bibliotecas y SQLite reemplazadas también están en el bucket
(`respaldos/65f4ebeb….zip`, recibo `data/operaciones/respaldos/respaldos_locales_20261025.json`).

## Presupuestos

Campaña `ciencias_v4_curricularizacion_20261022`: tope acumulado ampliado por el usuario el 25 de octubre a
4.400 llamadas con USD 3.500 (recibo literal anclado por SHA). Consumo: **4.294 llamadas y USD 3.219,5365** de
reserva (no factura). Quedan 106 llamadas. El 25 de octubre el usuario decidió no ampliar el tope: las 34
correcciones R23 listas (cota de 145 a 290 llamadas) esperan esa autorización.
`clases/` mantiene bytes congelados en sus módulos con huella; los módulos sin huella se corrigieron
(ver [Calidad](docs/CALIDAD.md)).

## Pendientes

1. Contraste humano: especialistas del MINED revisan la muestra de 96
   (`data/clases_v4/revision_especialistas/revision_especialistas_muestra_20261025.xlsx`) para calibrar la revisión
   asistida (la muestra dio 22 %; el resto, 12,8 %).
2. Autorizar o no las cuatro lecturas de las 34 correcciones R23 (ver `docs/CLASES_V4.md`). Los 112 bloqueados del
   resto aún no tienen corrección preparada; 5 objetivos requieren registrar fuentes nuevas.
3. Revisión experta del triaje de prerrequisitos y de las observaciones de fuente para el MINED.
4. Vocabulario: 173 conceptos propuestos y el reparto de `configuracion-electronica`.
5. Identidad y control de acceso si la aplicación deja de ser local.

La aprobación del MINED, el piloto con usuarios y la eficacia de aprendizaje son procesos separados.
