# Auditoría de QA y calidad de producto · 25 de octubre de 2026

Objetivo: dejar Ciencias V4 como **una sola entrega funcional y coherente** para evaluación de expertos y
usuarios reales, con todos los datos en el bucket institucional y verificables desde allí.

## Resumen ejecutivo

| Área | Estado al iniciar | Resultado |
|---|---|---|
| Producto | Dos ramas divergentes: `feat/api` (API y app) y `feat/ciencias-v4` (biblioteca docente y guiones P11) | Integradas en `feat/api`; una suite, un recibo y una aplicación |
| Datos | El código pinaba el corpus de 7.580 archivos; el bucket ya tenía la generación de 13.762 | Recibo y checkout adoptan la generación completa; datos derivados nuevos respaldados en GCS |
| Acceso a GCS | `gcloud` fallaba con Python 3.14 y la CLI limitaba descargas a 1 GiB | Selección de intérprete compatible; restauraciones verificadas desde el bucket |
| Grafo de conocimiento | V4 sin capa de conceptos: no podía describir introducción ni refuerzo 2.º–11.º | Capa de conceptos V4, trayectorias, prerrequisitos y verificación independiente |
| Aplicación | La biblioteca docente sólo era accesible por API | Vistas «Progresión 2.º–11.º» y «Materiales docentes»; diez secciones probadas en escritorio y teléfono |
| Calidad | Lint verde por rama; 1.462 pruebas en `feat/api` | Ver [Verificación final](#verificación-final) |

No se ejecutaron campañas pagadas. Consultado sobre ampliar la campaña de guiones (45 objetivos pendientes,
hasta 450 llamadas), el usuario **decidió no ampliar por ahora**; los guiones siguen como borradores.

## 1. Integración del producto

`origin/feat/ciencias-v4` (6 commits: materiales, clases P1–P11, respaldo P11) se fusionó en `feat/api`
(commit `ef411f3`). Siete conflictos, dos de código:

- `operacion/presupuestos_restaurados.py`: se adoptó la migración por copias verificadas con reversión. La
  versión de `feat/api` usaba `ATTACH` en una sola conexión y no admite más de diez bases (el corpus tiene 41).
- `operacion/almacen_gcs.py`: se combinaron los docstrings de `feat/api` con la cota explícita de objeto.

Defectos encontrados al integrar y corregidos con prueba:

| Defecto | Efecto | Corrección |
|---|---|---|
| `cli/materiales.py` importaba `_LecturaProducto`, renombrada en `feat/api` | `gskg materiales construir` fallaba | Usa `producto.lectura.LecturaProducto` |
| El empaquetado reescribía todo `.sqlite` con `backup()` | Restaurar el corpus dejaba una biblioteca docente que no coincide con su manifest | Copia los bytes exactos si no hay WAL ni journal pendientes; prueba de regresión |
| `gcloud` sólo probaba `python3.12` | Cualquier operación GCS fallaba en este equipo (Python 3.14 por defecto) | Usa `CLOUDSDK_PYTHON` o el primer Python 3.13/3.12/3.11 instalado |
| Filtro de disciplina de progresión trataba un `Literal` como `Enum` | 500 al filtrar | Corregido y cubierto por prueba de contrato |
| `.pill.blue` usado por Corpus sin definirse | Etiqueta sin estilo | Definido en `producto.css` |

`clases/` y `cli/clases.py` no se reformatearon: la campaña de guiones fija la huella de sus bytes. Se
documentó como excepción de estilo junto a los extractores ([Calidad](../CALIDAD.md)).

## 2. Datos en el bucket

Todo el corpus, los resultados y los derivados viven en `gs://goes-ai-kg-artefactos/ciencias/v4/`, fuera de
Git. El repositorio contiene sólo código, configuración, pruebas, documentación y recibos.

| Prefijo | Contenido | Recibo |
|---|---|---|
| `repositorio/objetos/` | Paquete ZIP del corpus por SHA | `config/datos_ciencias.lock.json` |
| `repositorio/inventarios/`, `recibos/`, `verificaciones/` | Inventario, descriptor y evidencia de restauración | Mismo recibo |
| `materiales/<biblioteca_id>/` | Biblioteca docente (SQLite + manifest) | `config/materiales_ciencias.lock.json` |

Recibo vigente: 13.919 archivos y 41 SQLite, ZIP `06398b9e…` (generación `1792955294299402`). Un
consumidor nuevo —`git worktree` limpio, entorno propio, sólo el recibo— restauró todo desde el bucket y
ejecutó la suite completa: **1.693 pruebas aprobadas, ninguna omitida**. El servicio levantado desde ese
checkout respondió en todas las rutas. Detalle en [Verificación GCS](../VERIFICACION_GCS.md).

## 3. Grafo de conocimiento: introducción y refuerzo 2.º–11.º

Resultados, método y límites en [Progresión 2.º–11.º](../PROGRESION_2_11.md). Puntos para la evaluación:

- El refuerzo es mayoritariamente **intermitente**; sólo 33 de 468 conceptos (47 con menciones) forman una
  espiral continua. Química es la más fragmentada y Tierra y espacio termina en 9.º.
- Las prácticas científicas sí forman espiral, salvo «formular preguntas investigables» (sólo 10.º).
- La lista de prerrequisitos tardíos es un triaje: de 28 casos prioritarios, la verificación independiente
  confirmó 3, consideró parciales 18 y refutó 7. Una primera versión basada sólo en etiquetas refutaba 11 de
  30; se añadió la capa de menciones léxicas y, tras la revisión adversarial, se restringieron sus claves.

## 4. Calidad de la fuente V4

Observaciones para el MINED (duplicados, fila incompleta, indicadores ajenos, contenido de tecnología y
anotación TIMSS no discriminante) en [Progresión 2.º–11.º](../PROGRESION_2_11.md#observaciones-de-la-fuente-para-el-mined).
No se modificaron los originales.

## 5. Aplicación y API

Se recorrieron las diez secciones con Chrome sin interfaz y el protocolo DevTools, en 1440 px y en un
teléfono emulado de 390 px. Ninguna vista mostró error ni desbordamiento horizontal; los diálogos de
concepto, unidad, fila y material abren su contenido real. La prueba en teléfono detectó un 500 al nombrar
prerrequisitos sólo mencionados, que se corrigió con prueba.

La API de progresión responde 503 «No hay datos disponibles» si falta el artefacto o pertenece a otra
publicación. La CSP `frame-ancestors 'none'` impide incrustar la aplicación, como se espera.

## 6. Revisión adversarial independiente

Un agente revisor sin acceso a mis conclusiones auditó el código nuevo y sondeó la API viva con entradas
hostiles (recorrido de rutas, barras codificadas, UTF-8 inválido, identificadores de 100.000 caracteres,
inyección en `q`). No encontró inyección SQL, recorrido de rutas, 500 ni fugas de rutas locales. Sus
hallazgos reproducidos se corrigieron con prueba:

| Hallazgo | Corrección |
|---|---|
| Menciones léxicas con falsos positivos («características», «seres vivos», MAS leído como «más») | Claves exclusivas, fragmentos con dos palabras de contenido, siglas en mayúsculas; API publica orden con y sin menciones |
| Copia exacta de SQLite podía incluir páginas sin confirmar (journal en memoria) o quedar bloqueada en `backup()` | Copia exacta bajo bloqueo SHARED con verificación de `stat`; `backup()` con plazo que falla cerrado |
| «Concentrado» no coincidía con su definición en la interfaz | Definición corregida |
| Clases de equivalencia atribuidas a una sola disciplina | Unión de disciplinas en filtros y en la entrada a bachillerato |
| El validador aceptaba salidas que la unión no podía procesar | Claves obligatorias; la unión exige el ítem idéntico al del producto; `progresion` comprueba huellas del vocabulario |
| Caché del documento leída fuera del bloqueo; verificación comparada con otro archivo | Documento y SHA de los bytes cargados se leen juntos |
| Valores numéricos sin `esc()`; patrón desconocido rompía la vista | Escapado completo y valores de reserva |
| `/api/v4/materiales` sin cabeceras de seguridad | Añadidas `nosniff`, CSP y `no-store` |
| Vista con propuestas mostraba el objetivo original | Muestra el objetivo precisado y el original como referencia |

Antes de esas correcciones se había subido una generación intermedia del corpus
(`59151f1e4b8faa72c575e661b39c640ae58e5c791de91a5100a0f42955fbfbd7`). No se adoptó y se conserva sin
sobrescribir; el recibo vigente apunta a la generación posterior.

## Verificación final

| Control | Antes (`5e8079a`) | Después (`1c445fc` + documentación) |
|---|---:|---:|
| `make lint` (Ruff, formato a 120) | verde | verde |
| `make cobertura`: pruebas aprobadas | 1.462 | **1.702 / 1.702**, ninguna omitida |
| Cobertura de líneas | 79,4 % | **79,1 %** |
| `make pruebas-js`, `make auditoria`, `git diff --check` | — | verde |
| Consumidor nuevo restaurado sólo desde GCS | — | 1.702 aprobadas |
| Diez vistas en 1440 px y 390 px | ocho vistas | sin errores ni desbordes |

La cobertura baja tres décimas porque el código de guiones integrado tiene menos líneas cubiertas. La medición
está en [medicion.json](../badges/medicion.json) con su huella de código. Las pruebas no acreditan
exactitud científica de cada propuesta ni eficacia educativa.

## 7. Segunda fase: guiones, sincronización y producto local

Tras autorizar el usuario la ampliación a 4.400 llamadas, R21 y R22 resolvieron 42 de los 45 pendientes
originales y el caso estelar. La revisión directa independiente de las 41 versiones recuperadas bloqueó 15 por
defectos materiales. Se publicaron **994 guiones y 108 unidades** con 19 objetivos declarados sin guion
([detalle](../CLASES_V4.md)). Consumo acumulado: 4.294 llamadas y USD 3.219,54 de reserva.

| Control | Resultado |
|---|---|
| Sincronización con GCS | `gskg datos estado|verificar|sincronizar|publicar`, `make producto`; 4 componentes por recibo |
| Corpus vigente | `d812b22d…`, 28.330 archivos; consumidor nuevo: 1.702 pruebas sin omisiones |
| Producto local | 10 vistas sin errores en 390 y 1440 px; 1.200 peticiones concurrentes sin error (p95 217 ms) |
| Auditoría de guiones | 409 resultados cotejados con el ledger tras corregir el esquema del editor P11 |

## 8. Tercera fase: revisión directa integral y producto sin rutas locales

| Control | Resultado |
|---|---|
| Muestra estratificada de 96 guiones (16 por estrato) | 20 con defecto material: 22 % ± 8 % ponderado |
| Revisión de los 872 restantes (109 revisores independientes) | 112 bloqueados (12,8 %); por estrato de 7,1 % a 19,0 % |
| Entrega vigente | 862 guiones y 108 unidades, **todos con revisión directa aprobada**; 151 objetivos declarados sin guion |
| Correcciones R23 | 34 de 39 listas con revisión directa favorable; sin ejecutar por decisión de no ampliar el tope |
| Rutas de la estación | Ninguna en archivos versionados ni en recibos (prueba `test_sin_rutas_locales.py`); identidad del ledger sin ruta; 14 registros operativos saneados con su bitácora; 7 evidencias ancladas por SHA se conservan intactas |
| Respaldos externos | Las copias que estaban fuera del repositorio se publicaron en `respaldos/` del bucket |
| Corpus vigente | `20c6e813…`, 29.086 archivos, restaurado y comparado antes de adoptar el recibo |

La diferencia entre la tasa de la muestra (22 %) y la del resto (12,8 %) indica variación entre revisores. Por
eso el contraste con especialistas del MINED (libro Excel de la muestra) es la siguiente calibración.

## Riesgos y decisiones pendientes

1. **Guiones de clase:** 862 publicados con revisión directa asistida y 151 objetivos sin guion. Falta el
   contraste con especialistas del MINED y decidir el presupuesto para las cuatro lecturas de las 34
   correcciones R23 (106 llamadas disponibles; cota 145–290).
2. **Aprobación institucional:** dictámenes automáticos y verificaciones por agentes no equivalen a una
   revisión del MINED ni a evidencia de aprendizaje. El piloto con usuarios es un proceso aparte.
3. **Despliegue:** la aplicación es de uso local, sin autenticación. Exponerla a usuarios reales fuera del
   equipo requiere identidad institucional y control de acceso.
4. **Bucket:** sin versionado de objetos; la inmutabilidad depende de nombres por SHA y precondiciones de
   generación. Valorar una política de retención sobre `ciencias/v4/` (cambio en un bucket compartido).
5. **Vocabulario:** 173 conceptos propuestos por los agentes y la división pendiente de
   `configuracion-electronica` requieren decisión experta antes de reetiquetar.
