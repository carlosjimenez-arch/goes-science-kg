# Continuidad · GOEs AI · feat/api

Corte: 27 de octubre de 2026. Estado vigente en [README](README.md), [documentación](docs/README.md) y la
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
- Complementos: **819 anexos y 97 evaluaciones aprobados y publicados**; 43 anexos y 11
  evaluaciones retenidos con motivo. Las 108 unidades tienen revisión verificable; 105 recibieron una
  corrección y revisión final por otro agente. Informe de 713 observaciones sobre guiones, pendientes de contraste,
  en `data/clases_v4/complementaria/informes/observaciones_guiones.json` y `.md`. No se modificaron los guiones
  publicados ni se invocó Vertex para esta continuidad. [Cierre y límites](docs/CLASES_V4.md).

## Datos: todo desde el bucket

`gs://goes-ai-kg-artefactos/ciencias/v4/`, fuera de Git, con cinco recibos:

| Recibo | Identidad |
|---|---|
| `config/datos_ciencias.lock.json` | Corpus `2ceaf1f0…`, 30.956 archivos |
| `config/materiales_ciencias.lock.json` | Biblioteca `8af1b65d…`, 3.837 registros |
| `config/clases_ciencias.lock.json` | Entrega de guiones `e4b32786…` (862 + 108) |
| `config/complementos_ciencias.lock.json` | Complementos `f69e7739…` (819 anexos + 97 evaluaciones) |
| `config/materiales_preparaciones.lock.json` | Biblioteca base `5b64ee…` que fijan las preparaciones |

`make producto` instala, sincroniza lo que falte y sirve. `gskg datos estado|verificar|sincronizar|publicar`
gestionan el ciclo; `publicar` sólo adopta un recibo tras restaurar y comparar. Un consumidor aislado sin datos restauró
el recibo vigente desde GCS y verificó el inventario, la salud y los complementos; la suite local completa pasó
1.740 pruebas sin omisiones. [Evidencia de recuperación](docs/VERIFICACION_GCS.md). Las generaciones anteriores siguen en el bucket.
Ningún archivo versionado ni recibo guarda rutas de una estación de trabajo (`tests/test_sin_rutas_locales.py`);
la identidad del ledger es nombre, dispositivo e inodo.
Las copias de bibliotecas y SQLite reemplazadas también están en el bucket
(`respaldos/65f4ebeb….zip`, recibo `data/operaciones/respaldos/respaldos_locales_20261025.json`).

## Presupuestos

Campaña `ciencias_v4_curricularizacion_20261022`: tope acumulado ampliado por el usuario el 25 de octubre a
4.400 llamadas con USD 3.500 (recibo literal anclado por SHA). Consumo: **4.294 llamadas y USD 3.219,5365** de
reserva (no factura). Quedan 106 llamadas. El usuario decidió no ampliar el tope ni buscar una vía más barata: las
132 correcciones R23 listas (63 lotes, cota de 315 a 630 llamadas y hasta USD 758 de reserva) quedan así hasta una
autorización explícita.
`clases/` mantiene bytes congelados en sus módulos con huella; los módulos sin huella se corrigieron
(ver [Calidad](docs/CALIDAD.md)).

## Pendientes

1. Contraste humano: especialistas del MINED revisan la muestra de 96 en el libro autónomo
   `data/clases_v4/revision_especialistas/revision_especialistas_guiones_ciencias_20261026.xlsx` (incluye el texto
   íntegro de cada guion; lo genera `libro_especialistas_escritorio_20261026.py`) para calibrar la revisión asistida
   (la muestra dio 22 %; el resto, 12,8 %).
2. R23 (ver `docs/CLASES_V4.md`): 132 correcciones con revisión directa favorable esperan, si algún día se
   autorizan, sus cuatro lecturas. 16 objetivos necesitan registrar fuentes oficiales salvadoreñas o sanitarias que
   el corpus fijado para R23 no tiene (MARN, MINSAL, MAG, OMS, SGA, ley minera) y 3 correcciones quedaron bloqueadas.
3. Revisión experta del triaje de prerrequisitos y de las observaciones de fuente para el MINED, incluido el
   informe de 713 observaciones de la capa complementaria. Son posibles defectos, no errores confirmados.
4. Vocabulario: 173 conceptos propuestos y el reparto de `configuracion-electronica`.
5. Identidad y control de acceso si la aplicación deja de ser local.

La aprobación del MINED, el piloto con usuarios y la eficacia de aprendizaje son procesos separados.
