# Revisión de paquetes de entrega de Ciencias V4 · 29 de octubre de 2026

La entrega se puede reconstruir con los mismos bytes, identidades y aprobaciones de los recibos vigentes.
No se detectó corrupción ni publicación de piezas retenidas como aprobadas. **El cierre didáctico sigue
teniendo defectos concretos:** las evaluaciones Markdown pierden un nivel de rúbrica, las unidades Markdown
incompletas ocultan sus faltantes y una lectura de muestra corrobora una observación de fundamentación
inadecuada en un guion publicado. Aprobar las pruebas de ingeniería no resuelve esos defectos.

Esta revisión conserva guiones, fuentes, revisiones, recibos y presupuesto. No ejecutó generación, nuevos
dictámenes de Vertex ni escrituras en GCS. Las correcciones siguientes son pendientes; no se aplicaron.

## Estado de partida y alcance

- Rama `feat/api`, `HEAD` `83c53f2`; coincide con el último cierre indicado. No había commits posteriores.
  El archivo no versionado `goes-science-kg.code-workspace` se conservó.
- Acceso directo al repositorio, sus archivos y Git: correcto. La enumeración del directorio padre
  (`find .. -name AGENTS.md -print`) devuelve `Operation not permitted`; no impide trabajar dentro del repositorio.
  No se encontró `AGENTS.md` accesible en el repositorio ni en los ancestros comprobados.
- Instrucciones consultadas: `CONTRIBUTING.md`, `HANDOFF.md`, `README.md`, `docs/README.md`,
  `docs/CLASES_V4.md`, `docs/VERIFICACION_GCS.md`, `docs/DATOS_EXTERNOS.md`, `docs/CALIDAD.md`,
  configuración y módulos de compilación, validación, lectura, revisión, fuentes y API.
- Recompilaciones y evidencias nuevas únicamente en
  `data/clases_v4/auditoria_entrega_20261029/`, ignorada por Git. Los originales no se reemplazaron.
- Auditoría poblacional determinista de paquetes y fuentes; lectura semántica nueva de seis guiones,
  uno por estrato, con selección reproducible. No equivale a una revisión científica especializada de
  todas las clases ni a aprobación del MINED. La muestra no permite estimar una tasa de defectos.

## Paquetes identificados mediante los cinco recibos

| Recibo versionado | Identidad | Contenido y ubicación local |
|---|---|---|
| `config/datos_ciencias.lock.json` | `2ceaf1f0541f09ae4749cc76c89578072dabb34e55d169d79c81b63d71cbdf56` | Corpus de 30.956 archivos; inventario remoto fijado por generación y SHA |
| `config/clases_ciencias.lock.json` | `e4b3278681cddc144d457dc7774f54a07a8721e72673d9564d2ed24add694de6` | 862 clases y 108 unidades; `data/clases_v4/entrega/guiones-ciencias-v4-20261025-v3.zip`; descarga operativa `data/descargas/clases-v4/` |
| `config/materiales_ciencias.lock.json` | `8af1b65d56ae4b5d4625316aed47554956522c674c2a9e1c3332eee80f5e2462` | Biblioteca vigente `data/materiales/`: 3.837 registros, incluidos los 970 guiones de la entrega |
| `config/complementos_ciencias.lock.json` | `f69e7739d570ecedda8d412ad7dece0b24311ac7abec56493e373dfed8b6c2ce` | `data/clases_v4/complementaria/publicacion/complementos-f69e7739d570eced.json`: 819 anexos y 97 evaluaciones aprobados; 54 piezas retenidas |
| `config/materiales_preparaciones.lock.json` | `5b64ee509613b25ef91a941bcdbb2cc6a271daef98a0ecbddbc279a3eba2f510` | Biblioteca base de 2.867 registros en `data/materiales_preparaciones/`, necesaria para recompilar |

El ZIP vigente contiene 11.187 archivos: catálogo, índice, instrucciones, JSON y Markdown docente/estudiante
de clase, JSON/Markdown de unidad, fuentes y expedientes. Las preparaciones y los paquetes históricos V3
de la biblioteca no se contaron como nuevos guiones V4. El ZIP anterior que también existe localmente no
se tomó como entrega vigente.

## Recompilación e integridad

| Comprobación | Resultado |
|---|---|
| Corpus frente al inventario descargado de GCS | 30.914 archivos idénticos por SHA; 42 SQLite operativos contados aparte; 0 diferencias y 0 faltantes |
| ZIP recompilado de guiones | 106.432.460 bytes, los 11.187 archivos idénticos; manifiesto idéntico |
| SHA del ZIP original, recompilado y recibo | `1a98f3fe04152bf1800b22189c5d324715f9a54d9cc3ac2c5e4e9a46609c74a4` en los tres |
| Biblioteca vigente recompilada | SQLite y `manifest.json` idénticos por SHA al original y al recibo; 3.837 registros |
| SQLite vigente | `0de615ab41ab8363402b8aa8e23935302fa252b01ceba9559987547b9d23b1df` |
| Biblioteca base | SQLite y manifiesto coinciden por bytes/SHA con su recibo; 2.867 registros |
| Complementos recompilados | Objeto y bytes idénticos; JSON de 20.593.370 bytes |
| SHA JSON complementario | `7710e8383cc6ecad2057911855a3c3f443c0790a6bf66606d6bafc536d475b7d` |
| Originales complementarios archivados | 970 archivos, CRC y SHA contra el plan sin diferencias |
| Informe de observaciones recompilado | 713 observaciones; JSON y Markdown idénticos al informe conservado |

Se descargó el inventario remoto para verificar el corpus actual; **no se repitió una restauración completa
desde cero de los 1,7 GB del respaldo**. Los SQLite operativos no se presentaron como 42 archivos idénticos
por SHA al respaldo: el comando los cuenta aparte. Las dos bibliotecas de entrega sí se cotejaron
explícitamente por SHA de sus objetos contra sus respectivos recibos.

## Contenido, soluciones, rúbricas y correspondencia con lo aprobado

Los 862 guiones superaron los contratos y la reconstrucción de sus expedientes: 1.349 sesiones,
1.727 tareas, 3.457 criterios de rúbrica y 4.155 cálculos declarados recomputados. Se comprobaron las
862 revisiones directas del guion exacto y los 3.448 dictámenes favorables de cuatro roles. La compilación
reconstruyó las claves de revisión y cotejó las respuestas reales del ledger; no se pidieron votos nuevos.
Los 8.381 originales archivados cotejados con sus archivos locales no presentaron diferencias.

Los 970 registros de guion del ZIP coinciden con la biblioteca vigente y con los detalles de la API.
Las 1.832 representaciones Markdown de clase/unidad coinciden con su renderizado y con sus descargas API,
incluidos los ETag. En guiones de clase, los tres niveles de rúbrica, tareas y solucionarios están presentes
en la vista docente; la hoja de estudiante conserva las tareas sin el solucionario.
La igualdad con el renderizador no prueba que éste imprima todos los campos: las omisiones detectadas
se detallan más adelante.

Se validaron los 862 anexos y las 108 evaluaciones de entrada, incluidos los que luego se retienen por
revisión semántica. Las 108 revisiones aplicables son verificables: 105 finales y tres iniciales sin
corrección necesaria. Se comprobaron anclajes SHA, cambios trazables y separación entre corrector y revisor.
Las 97 evaluaciones aprobadas contienen 1.340 ítems: 989 de opción múltiple y 351 de respuesta construida;
sus 1.783 cálculos declarados se recomputaron. Las comprobaciones de dominio y porcentajes operan sobre
las etiquetas declaradas; los dictámenes conservan los bloqueos por clasificación semántica incorrecta.

La comparación de 78.528 campos textuales de los 819 anexos y 97 evaluaciones aprobados detectó
las 948 omisiones de rúbrica descritas abajo. Los demás textos didácticos de materiales, sustituciones,
inclusión, reducción de tiempos, indagación, contexto, enunciados, opciones, claves y justificaciones
se conservan. Es una prueba de presencia textual, no de exactitud científica de todas las soluciones.

## Contenidos retenidos y cobertura incompleta

- Los 43 anexos y 11 evaluaciones retenidos están separados de los conjuntos aprobados. La API devolvió
  **200 para los 916 detalles aprobados y 404 para los 54 retenidos**, sin mezclas en listas ni detalles.
  Los payloads aprobados coinciden íntegramente con la publicación recompilada.
- Cada pieza retenida tiene identidad y motivo. La publicación usa categorías generales; el motivo
  específico está en el dictamen archivado. Se reunieron ambos en
  `complementos/retenidos-con-motivo.json` dentro de la auditoría nueva.
- Los 151 objetivos sin guion siguen declarados con estado, expediente y motivo; no figuran como clases
  aprobadas. Las 151 consultas de la API por su `fila_id` y tipo `guion_clase` devolvieron cero resultados.
- De los 108 **guiones de unidad**, 70 declaran `completa: false`. Por separado, en la **capa
  complementaria**, 70 unidades tienen todas sus piezas liberables y 38 tienen alguna retenida.
  Son métricas diferentes y no deben intercambiarse.
- Las correcciones R23 no se incorporaron a la entrega. Se mantiene su estado: 132 listas para cuatro
  lecturas, tres bloqueadas y 16 que requieren fuentes no registradas en el corpus fijado.

Ejemplos de retención verificada: la evaluación de la unidad corta `1c00155fc2`, ítem I14, conserva
el bloqueo por describir el ácido cítrico como una cadena continua de seis carbonos; la unidad
`24e530e581`, ítem I10, conserva el bloqueo por dominio mal clasificado, que dejaría sólo 18,75 % de
razonamiento. Son motivos de dictámenes existentes, no nuevos contenidos aprobados por esta auditoría.

## Fuentes y enlaces

- Verificados 890 módulos, cuatro licencias y cuatro colecciones base (898 referencias de archivo),
  21 versiones complementarias y 1.587 archivos complementarios. Las 4.711 referencias asignadas
  a las 862 clases usan 3.581 evidencias distintas; sin citas huérfanas. Se contrastaron por bytes
  2.486 originales de fuentes redistribuidos dentro del ZIP.
- Los 14 documentos nacionales conservan sus SHA. Una reextracción independiente de sus 1.317 páginas
  coincidió con el texto almacenado; los 177 pasajes son literales. La publicación usa 123 pasajes
  en 628 citas, sin referencias huérfanas ni cambios de metadatos.
- Parseo CommonMark: 1.833 enlaces internos del paquete resuelven a archivos existentes. La revisión
  evita tratar notación química entre corchetes como un enlace Markdown.
- HTTP de las 977 URLs distintas de metadatos: 969 accesibles (942 respuestas 206 y 27 respuestas 200),
  cero 404/410. Ocho accesos quedaron sin verificar: cinco 403 (cuatro CDC y uno USGS), dos errores
  de cadena TLS de Asamblea Legislativa y un timeout NRCS; persistieron en una segunda lectura acotada.
  Estos resultados no acreditan desaparición del documento ni invalidan el original local conservado.
- Los 49 vínculos adicionales incrustados en el Markdown docente amplían el total a **1.026 URLs**:
  1.007 accesibles, cuatro 404 confirmados dos veces, once 403, dos fallos TLS, un fallo DNS y un timeout.
  Los 404 y el fallo DNS se detallan como defectos de acceso más adelante; no son citas huérfanas del corpus.

Las licencias, atribuciones, commits, localizadores CNXML y rangos de bytes se conservaron. La integridad
de un pasaje y la disponibilidad de su URL no demuestran que sustente el concepto enseñado: el caso
de vulnerabilidad que sigue muestra esa diferencia.

## Fallos concretos y acciones pendientes

1. **Rúbrica incompleta en las 97 evaluaciones Markdown (948 criterios).**
   `src/goes_science_kg/clases/complementaria_publicacion.py:38` imprime `logrado` y `en_proceso`, omitiendo
   `requiere_apoyo`. El JSON estructurado conserva los tres niveles. Ejemplo: Ciencias, 6.º,
   **Unidad 5 - Célula**, ítem I02, criterio «Volumen y superficies accesibles». Inventario exhaustivo en
   `complementos/rubricas-omitidas-markdown.json`. Pendiente: reparar el renderizador y comprobar
   conservación de todos los niveles antes de preparar cualquier entrega sucesora. No se cambió el recibo.

2. **Las 70 unidades incompletas no advierten sus faltantes en Markdown ni en el índice.**
   `src/goes_science_kg/clases/lectura.py:135` y `:162` enumeran sólo guiones disponibles; omiten
   `completa` y `objetivos_sin_guion_liberado`. El JSON y el manifiesto sí conservan esa información.
   Ejemplo: **Unidad 5 - Célula**, Ciencias, 6.º, archivo
   `unidades/b8e517b3c0162228fc2dc7cdf293cf9e873d4305d86e5186b2576d7464efc1f5.md` del ZIP.
   Pendiente: mostrar condición de incompleta, objetivos ausentes y motivos también en las vistas legibles.
   No es una publicación de los guiones bloqueados; es pérdida de información sobre la cobertura.

3. **Fundamentación ajena al objetivo en un guion publicado, corroborada en la muestra.**
   Guion **Vulnerabilidad y capacidad familiar y comunitaria ante amenazas**, Ciencias, 4.º, fila
   `CURRICULO:V4:9c1460d823d05fa14be2b3ee9efe029a4ccbc448c29a801f06454ad602c19904`.
   Su sección `explicacion_docente` introduce redox, neutralización y propiedades de no metales; los cuatro
   pasajes asignados tratan química y energía celular y no sustentan vulnerabilidad/capacidad comunitaria.
   El resto del guion sí desarrolla la actividad de amenazas: el defecto está en la explicación y su
   fundamentación. Las cuatro lecturas y la revisión directa anterior lo habían aprobado.
   Está en `clases/972303522c70e599595e22e16e2cd30d3bf3b0bf65260e1ffa367843c0aee3e9.docente.md`.
   SHA-256 del guion con la serialización de revisión directa:
   `c4b40ac841932a062b74acef98a0e601970875031fdb3df8a2101b54343b63cf`.
   El informe de 713 ya lo señalaba por sufijo `d602c19904`, unidad corta `c959dd0d12`: esta auditoría
   corrobora esa observación y no la cuenta como un hallazgo nuevo. Pendiente: contraste especializado y
   decisión editorial conforme al protocolo, conservando la versión publicada. No se modificó el guion.

4. **Trazabilidad de progresión reducida en Markdown complementario.**
   Se omiten 2.106 identidades `fila_id` de destinos (1.081 ideas previas y 1.025 continuidades): quedan
   concepto, grado y explicación, pero no un destino navegable por identidad. JSON/API conservan los IDs.
   Pendiente: definir e incluir esos enlaces en la entrega legible. Otras omisiones son metadata de control
   (anclajes, versiones, fichas de cálculo); no se equiparan automáticamente a pérdida del solucionario.

5. **Cuatro enlaces externos devuelven 404; un dominio histórico no resuelve.**
   Se comprobaron dos veces, sin sustituir los originales. Tres son fotografías Flickr dentro de texto
   fuente Siyavula: [alimentación](http://www.flickr.com/photos/seeseecards/7209691478/in/set-72157629756301182/)
   en «Nuestro plato variado y los anuncios de comida» (2.º),
   [electricidad](http://www.flickr.com/photos/vhhammer/6567396763/) en «Efectos fisiológicos de la corriente
   eléctrica y protección en instalaciones» (11.º), y
   [artrópodos](http://www.flickr.com/photos/wheatfields/3409167144/) en «Esquemas de artrópodos y moluscos:
   contando patas y partes del cuerpo» (3.º). El cuarto es la
   [política/licencia ARS-USDA](https://www.ars.usda.gov/policies-and-links/), citada en «Cambios en la materia
   que forman nuevas sustancias» (2.º) y «Características físicas, horizontes y origen del suelo por
   meteorización» (5.º). `puzzling.caret.cam.ac.uk` tampoco resolvió por DNS.
   Son enlaces de fuentes redistribuidas/atribuciones, no instrucciones del campo `guion`; no se acreditó
   que impidan ejecutar una tarea. Las licencias y fuentes locales conservan su SHA. Pendiente: una nota
   separada de acceso/erratas y contraste de accesos 403/TLS/timeout. El mapa completo por URL, objetivo,
   archivo y línea está en `fuentes_http_md_afectados.json` y `fuentes_http_afectados.json` de la auditoría.

Las 713 observaciones originales permanecen archivadas con el estado `pendiente_de_contraste` y bytes
idénticos. Esta revisión no contrastó las 713 una por una ni las convirtió en 713 errores confirmados.
Continúan pendientes la calibración de especialistas del MINED y la decisión sobre los contenidos retenidos
y los objetivos sin guion. No se ejecutaron cuatro lecturas de R23 ni se amplió su presupuesto.
Una futura reparación de los módulos congelados de `clases/` debe seguir la migración explícita indicada
en `CONTRIBUTING.md`, conservando la evidencia anterior; no se deben cambiar hashes esperados para aprobarla.

## Comandos y comprobaciones ejecutados

Todos los comandos siguientes terminaron con código cero, salvo las limitaciones de acceso/HTTP ya
descritas. Los logs, duraciones, JUnit, cobertura, scripts auxiliares y JSON completos están en la carpeta
aislada de auditoría. Se usaron funciones puras para complementos porque el comando operativo puede
escribir el recibo original.

```sh
git status --short --branch
git log -8 --oneline --decorate
git diff --stat 83c53f2..HEAD
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/conservacion.py antes
uv run --frozen gskg datos estado
uv run --frozen gskg datos verificar
uv run --frozen gskg clases compilar \
  data/clases_v4/auditoria_contenido/seleccion_entrega_20261025_v3.json \
  --biblioteca data/clases_v4/auditoria_entrega_20261029/biblioteca_recompilada \
  --archivo data/clases_v4/auditoria_entrega_20261029/guiones_recompilados.zip \
  --biblioteca-origen data/materiales_preparaciones \
  --pendientes data/clases_v4/auditoria_contenido/pendientes_entrega_20261025_v3.json \
  --revision-directa data/clases_v4/auditoria_contenido/revision_directa_muestra_20261025.json \
  --revision-directa data/clases_v4/auditoria_contenido/revision_directa_recuperacion_20261025.json \
  --revision-directa data/clases_v4/auditoria_contenido/revision_directa_resto_20261025.json
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/comparar_recompilacion.py
uv run --frozen gskg clases validar data/clases_v4/auditoria_entrega_20261029/guiones_recompilados.zip
uv run --frozen gskg materiales validar
uv run --frozen gskg producto validar
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/auditar_guiones.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/auditar_guiones_api.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/auditar_complementos.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/auditar_campos_markdown_complementos.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/auditar_fuentes.py
uv run --frozen python data/clases_v4/complementaria/pasajes.py validar
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/reextraer_nacionales.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/verificar_urls.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/reintentar_urls.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/enlaces_visibles_md.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/verificar_urls_md.py
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/reintentar_urls_md.py
uv run --frozen pytest -q --cov=goes_science_kg \
  --cov-report=xml:data/clases_v4/auditoria_entrega_20261029/coverage.xml \
  --junitxml=data/clases_v4/auditoria_entrega_20261029/junit.xml
make lint
make pruebas-js
uv run --frozen python scripts/auditar_repo.py \
  --salida data/clases_v4/auditoria_entrega_20261029/inventario_repo.json
uv run --frozen python data/clases_v4/auditoria_entrega_20261029/conservacion.py despues
git diff --check
```

La suite protege los tests con proveedores simulados y prohíbe crear un cliente Vertex real.
Resultado suite: **1.740 aprobadas, cero fallos, cero errores y cero omitidas**, en 605,37 s de pytest.
Cobertura de líneas **79,63 % (19.427/24.396)** y de ramas 69,84 % (5.893/8.438).
Entorno: Python 3.14.3, uv 0.7.8 y Node.js 24.2.0. Ruff pasó (332 archivos con formato correcto), las seis
pruebas JavaScript pasaron y la auditoría del repositorio terminó correctamente. La validación del producto
conserva el snapshot `e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`.
No se regeneraron los badges históricos ni sus informes versionados.

## Conservación y evidencia de cierre

Tras terminar la suite, los **23.447 archivos originales fijados** de configuración, código, guiones,
fuentes y descarga previa conservaron sus SHA; cero alterados y cero archivos nuevos fuera de la carpeta
de auditoría en las raíces comprobadas. Las tablas completas del ledger (`llamadas`, `cache`, `salidas_llm`)
conservan sus recuentos y huellas lógicas. La biblioteca vigente, comprobada por separado, también
conserva sus bytes/SHA de recibo. El estado Git final sólo añade este diagnóstico y conserva el archivo
de workspace no versionado que existía al comenzar; no se modificó código ni documentación previa.
La campaña mantiene **4.294 llamadas y USD 3.219,5364705 de reserva**, con topes de 4.400 llamadas y
USD 3.500; quedan 106 llamadas dentro del tope existente, sin autorización para usarlas en esta revisión.
El balance conserva el baseline y el punto de continuidad. La reserva no equivale a una factura.

Evidencias principales, relativas a `data/clases_v4/auditoria_entrega_20261029/`:

- `recompilacion_comparacion.json`, `recompilar_guiones.comando.json` y `.log`: reproducción exacta.
- `datos_verificar.log`: inventario remoto y verificación local.
- `guiones_resultado.md`, `guiones_resultado.json`, `guiones_biblioteca_api.json`: población, muestra y API.
- `complementos_resultado.md`, `complementos/resultado.json`, `complementos/retenidos-con-motivo.json`:
  recompilación, dictámenes y exclusión de retenidos.
- `complementos/rubricas-omitidas-markdown.json`, `complementos/campos-markdown-exhaustivo.json`:
  diferencias de contenido renderizado.
- `fuentes_resultado.md`, `fuentes_resultado.json`, `fuentes_http.json`, `fuentes_reextraccion_nacional.json`:
  fuentes, HTTP y pasajes.
- `suite.comando.json`, `suite.log`, `junit.xml`, `coverage.xml`: ejecución integral nueva.
- `conservacion_antes.json`, `conservacion_despues.json`, `conservacion_resultado.json`, `presupuesto.json`:
  conservación de originales y ledger.

Estas evidencias nuevas son locales y no forman parte del respaldo GCS vigente. El informe versionable
no incorpora corpus, SQLite, PDF, Excel, credenciales ni los textos íntegros de guiones o dictámenes.
