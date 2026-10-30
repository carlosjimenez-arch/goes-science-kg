# Continuidad · GOEs AI · feat/api

Corte: 29 de octubre de 2026. Estado vigente en [README](README.md), [documentación](docs/README.md) y la
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

### Continuidad local · 29 de octubre de 2026

Se completó la [edición didáctica sucesora local](docs/ENTREGA_DIDACTICA_V2.md): R1–R5 con diagnóstico,
refuerzo y comprobación reservada en cuatro hojas, dos guiones de amenazas/vulnerabilidad corregidos,
un módulo de medición honesta y la evaluación de unidad revisada. Dictámenes asistidos finales favorables
anclados a los nueve JSON efectivos; sin aprobación institucional ni eficacia/carga cognitiva medidas.
La edición local conserva rúbricas completas, faltantes visibles y destinos de progresión navegables.
El alcance confirmado fue los cinco recorridos y casos identificados, sin producir 1.013 recorridos nuevos.
Suite final: 1.795 aprobadas, ninguna omitida; cobertura 79,81 %. Ruff, seis pruebas JavaScript y auditoría
independiente del ZIP aprobados. Se comprobaron 4.909 archivos, nueve JSON revisados, 949 criterios completos
y 4.816 enlaces internos. El detalle, las identidades y los límites están en el informe de la edición.

Artefactos en `data/clases_v4/mejora_didactica_20261029/`; entrada `entrega_final/INDICE.md` y ZIP
`ciencias_v4_mejora_didactica_final.zip`. Se mantienen los cinco recibos y las publicaciones anteriores.
No se usó Vertex ni se escribió en GCS. Las 713 observaciones, 54 retenidos y 151 objetivos sin guion
conservan sus estados; los otros 860 guiones reciben apoyos de diseño, sin declararlos revisados de nuevo.

**Destino de las entregas.** El usuario pide dejar todos los paquetes finales en su Escritorio.
`AGENTS.md` y `CONTRIBUTING.md` fijan el estándar para futuras salidas; `gskg entrega despachar` exige
edición/ZIP/dictámenes exactos, auditoría independiente y medición vigente de toda la suite antes de copiar.
Destino de esta edición: `$HOME/Desktop/Ciencias_V4_Entrega_20261029/`, con índice, materiales completos,
ZIP, evidencias y recibo verificable. [Procedimiento y controles](docs/DESPACHO_CIENCIAS_V4.md).
La suite con la capa de despacho pasó 1.819 pruebas sin omisiones; cobertura 79,83 %. La edición conserva
su identidad `1960ed24…` y el ZIP `a85d8250…`; no se modificaron guiones publicados ni presupuesto.

### Piloto de ampliación Vertex · 29 de octubre de 2026

El usuario amplió el horizonte a todos los objetivos y unidades, con autoría Vertex y verificación
por Codex/agentes. Autorizó un piloto separado de **18 llamadas y USD 40 de reserva**, con nueve
guiones candidatos y tres controles negativos sin llamada. Recibo literal, inventario de 1.013/108,
contextos, fuentes curadas y registros en `data/clases_v4/ampliacion_vertex_20261029/`.
[Método, límites y comandos](docs/AMPLIACION_VERTEX_CIENCIAS_V4.md).

Las dos primeras solicitudes recibieron `400 INVALID_ARGUMENT`; se conservaron consumo y fallos.
El transporte sucesor compacto conserva los validadores locales y las plazas restantes explícitas.
Las respuestas nuevas se revisan por SHA y no heredan aprobación. El piloto consumió las 18
solicitudes y USD 29,661560 de reserva conservadora, sin factura verificada. Produjo dieciséis
respuestas: ocho borradores y ocho correcciones. La selección revisada contiene ocho guiones de
seis unidades: dos respuestas finales Vertex íntegras y seis sucesores editoriales Codex con
dictamen independiente de sus bytes. Contiene 21 tareas, 54 criterios de rúbrica de tres niveles
y 88 comprobaciones aritméticas declaradas recalculadas. No son aún nuevos anexos, recorridos
de cuatro hojas ni guías/evaluaciones de unidad.

El caso municipal da854ca155 permanece retenido por materiales insuficientes; la existencia de
mapas oficiales no completa por sí sola el criterio. Tres controles negativos siguen bloqueados
sin llamada. La práctica química está condicionada a FDS vigente del producto real y protocolo
institucional revisado. El piloto no crea todavía 1.013 paquetes completos ni publica en GCS.

La suite del código de ampliación pasó **1.908 pruebas**, sin fallos ni omisiones; cobertura **79,93 %**.
Esa evidencia comprueba código y guardas, sin acreditar corrección científica ni aprendizaje de los guiones.
Los módulos congelados, los cinco recibos, los guiones publicados y el presupuesto histórico se conservan.

**Despacho cerrado del piloto.** Copia efectiva en
`$HOME/Desktop/Ciencias_V4_Piloto_Vertex_20261029/`, entrada `LEEME.md`: 296 archivos, incluidos
271 de materiales, ZIP, diagnóstico, pruebas y dictámenes. Verificación física independiente
favorable sin errores; los 4.923 archivos de la entrega anterior permanecen intactos.
Manifest `8b6b301a…006606`, ZIP `d5933d57…197f7e9`, recibo `c94b3346…90e9c10`.
La selección vigente es `catalogo_aprobado_002.json`; conserva como antecedentes los catálogos,
respuestas y dictámenes anteriores. Se cerraron el reparto por etapas de la predicción de suelo
y la representación gráfica reservada de resonancia. El navegador bloqueó `file://`; se revisaron
localmente HTML/Markdown/CSS, sin afirmar inspección visual ni paginación impresa.
Evidencia: `revision/verificacion_escritorio_piloto_independiente.json` dentro de la raíz privada
del piloto. El presupuesto de 18 llamadas está consumido; cualquier fase posterior exige su propia
autorización, sin reutilizar la reserva sobrante ni las plazas de la campaña histórica.

### Segunda fase autorizada · anexos y recorridos de ocho bases

El usuario autorizó después **hasta USD 70 de reserva y 32 llamadas adicionales**, para ocho
anexos docentes y ocho recorridos cerrados de cuatro hojas escritos por Vertex sobre las ocho
bases exactas entregadas. No incluye nuevas unidades, reescritura de guiones ni publicación en GCS.
La autorización literal está en
`data/clases_v4/ampliacion_vertex_20261029/fase2_ejecucion/autorizacion_usuario_global.json`.
Plan vigente `fase2_propuesta/plan.json`, SHA `82e22e61…09632`; preflight local de 16 componentes,
reserva conservadora calculada USD 66,494308 y revisión técnica independiente favorable003.

Se empieza con un anexo y un recorrido de vulnerabilidad de 4.º. La aceptación de API, identidad,
contrato y contenido se comprueba antes de continuar con el resto; cada fallo consume una plaza.
No se cambia la campaña histórica ni se transfieren las reservas sobrantes del piloto.
El ejecutor privado exigirá continuidad del historial, topes globales, máximo dos plazas por
componente, revisión de su versión exacta y guardas adicionales de identidad antes de caché.
Los resultados, correcciones, dictámenes y despacho de esta fase se registrarán en su carpeta nueva;
la entrega del piloto y la anterior del Escritorio permanecen como snapshots íntegros.

El primer par recibió dos respuestas con terminación STOP y consumió dos plazas/USD 3,101984 de
reserva. Ambas quedaron retenidas: el anexo excede cuatro campos y contradice su clasificación de
recursos; también faltan dos adaptaciones de acceso y hay ayudas que no deben llegar a la comprobación.
El recorrido trae `soluciones_docente={}` para cuatro ítems, sin respuestas, explicaciones ni rúbricas;
la validación semántica lo rechazó. El mapa vacío es legal en el esquema remoto elegido: no se demostró
que la API ignorase `additionalProperties`. Dictámenes y devolución conjunta en
`fase2_ejecucion/revision/feedback_unificado_d602c19904_ronda0.json`.

Se cierra el perfil inicial `82e22e61…09632`/ejecutor `78b6b837…8ac904` sin más llamadas. La corrección
técnica autorizada conserva el contrato de negocio y transporta las soluciones como una lista tipada,
con conversión local biyectiva a mapa y raw intacto. Requiere nuevas regresiones y revisión antes de usarla.
El sucesor se prepara en `fase2_sucesion_001/`: máximo **30 plazas y USD 66,898016**, más el consumo
anterior, siempre dentro de las 32/USD70 originales. A los dos componentes de 4.º les queda una plaza
global cada uno; a los otros catorce, dos. Los dos intentos anteriores y su autorización no se reinician
ni modifican. No hay todavía contenido aprobado ni entrega de materiales de fase 2.

El núcleo de transporte revisado pasó **1.937 pruebas**, cero fallos/errores/omisiones, con cobertura
**80,0237085 %**. Huella de código/políticas `697849dd…a7bb45`, medición UTC 30 de octubre 00:07
(29 de octubre local). Se añadieron 29 regresiones del formato y la conservación; el contrato de
negocio de los cinco tipos quedó idéntico. Las pruebas privadas del ejecutor/perfil se mantienen
fuera de ese denominador. La medición de 1.908 del piloto es su snapshot anterior, no la del código
sucesor. La revisión del nuevo ejecutor y su recibo operativo siguen siendo necesarios antes de API.

### Campaña existente

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
