# Guiones completos de Ciencias V4

## Entrega vigente · revisión directa integral (25 de octubre de 2026)

**862 guiones de clase y 108 guiones de unidad publicados, todos con revisión directa aprobada**; 151 objetivos
declarados sin guion liberado, cada uno con su motivo. Entrega `e4b3278681cddc144d457dc7774f54a07a8721e72673d9564d2ed24add694de6`
(`config/clases_ciencias.lock.json`) y biblioteca `8af1b65d…` con 3.837 registros
(`config/materiales_ciencias.lock.json`), publicadas en el bucket y descargadas desde él con `gskg datos sincronizar`.
70 de las 108 unidades quedan marcadas `completa: false`.

| Paso | Resultado |
|---|---|
| Muestra estratificada de los 968 guiones sin revisión directa (16 por estrato, semilla = id de la entrega) | 96 revisados: 20 bloqueados; tasa ponderada 22 % ± 8 % |
| Revisión directa de los 872 restantes (109 revisores, 8 casos cada uno) | 760 liberables y 112 bloqueados (12,8 %) |
| Total de la cohorte publicada sólo con lectores automáticos | 132 de 968 con defecto material (13,6 %); por estrato entre 7 % (2.º–4.º) y 19 % (Biología 10.º–11.º) |
| Retiro | Los 132 se declaran `bloqueado_revision_directa`, anclados al SHA exacto del guion revisado |
| Corrección editorial R23 | 151 objetivos (19 pendientes, 20 bloqueados de la muestra y 112 del resto): **132 correcciones con revisión directa independiente favorable**, 3 bloqueadas y 16 imposibles sin fuentes que no están en el corpus |
| Bloqueados del resto (112) | 98 corregidos y liberables, 1 bloqueado (cobertura del suelo sin datos del país) y 13 sin fuente registrada |
| Cuatro lecturas de R23 | **No ejecutadas.** La cota (63 lotes, 315–630 llamadas, hasta USD 758) no cabe en las 106 restantes; el usuario decidió dejarlo así |

Protocolo, diseño y expedientes: `data/clases_v4/revision_especialistas/` (`PROTOCOLO_REVISION_DIRECTA.md`,
`muestra_20261025.json`, `expedientes_*`) y los consolidados `data/clases_v4/auditoria_contenido/revision_directa_muestra_20261025.json`
y `revision_directa_resto_20261025.json`. Defectos típicos: atribuciones históricas erróneas (teoría celular),
vectores virales mal descritos (adenovirus en ADA-SCID, error que viene de OpenStax), datos institucionales
inventados (boletines del MARN, datos de OMI/NOAA), cláusulas del criterio sin enseñar, errores conceptuales
(paralaje, glucagón en el músculo, polos magnéticos) y datos simulados incoherentes con la termodinámica.

**Límites.** Es una revisión asistida por IA, con un solo revisor por guion. La muestra (22 %) y el resto (12,8 %)
dieron tasas distintas: la diferencia sugiere variación entre revisores, así que el 12,8 % puede subestimar los
defectos. La validación de especialistas del MINED sigue pendiente. El libro autónomo
`data/clases_v4/revision_especialistas/revision_especialistas_guiones_ciencias_20261026.xlsx` contiene la muestra,
el dictamen asistido y el texto docente íntegro de cada guion (verificado por SHA-256 contra la entrega de 994), de
modo que los especialistas no necesitan descargar la entrega. Lo genera `libro_especialistas_escritorio_20261026.py`;
sólo escribe texto literal (ninguna celda se interpreta como fórmula).

Las correcciones R23 (`data/clases_v4/ediciones_editoriales/r23/`, estado en `estado_r23.json`) son parches
editoriales sobre la última versión válida. Cada una tiene su expediente, su versión materializada y su revisión
directa independiente, anclada al SHA-256 de la versión exacta (`revision_directa/grupo_*.json`). Las 98
correcciones de los bloqueados del resto las redactaron 29 editores por disciplina y las revisaron 15 revisores
distintos; una versión bloqueada se corrigió de nuevo y volvió a revisarse. Para publicarlas hace falta autorizar
la ampliación del tope: `ensamblar_r23.py --escribir` agrupa por biblioteca, snapshot y escenario, prepara parches,
preparaciones y plan con su cota, y la campaña se ejecuta con el protocolo `clases-p11-editorial-r23-001`.

Objetivos que necesitan una fuente nueva registrada antes de corregirse: legislación minera y yacimientos del país,
mapa oficial de suelos (MAG/MARN), plantas del corredor seco, presión por estación del MARN, inventarios de carbono
en manglares, balance global de carbono, Guías Alimentarias y datos del MINSAL/OPS, documentos de la OMS sobre
priones y sobre diagnóstico bacteriológico, SGA y fichas de datos de seguridad, sueño e inmunidad, y riesgos del
carburo de calcio en alimentos.

## Capa complementaria de implementación (26 de octubre de 2026)

Sin modificar ningún guion liberado (eso exigiría cuatro lecturas nuevas), cada clase publicada recibe un **anexo de
implementación** y cada unidad una **evaluación**. Ambos se anclan al SHA-256 del guion exacto
(`src/goes_science_kg/clases/complementaria.py`).

| Componente | Qué aporta | Control determinista |
|---|---|---|
| Recursos | Nivel (sin materiales, caseros, laboratorio), sustitutos caseros, requisitos de agua, electricidad, exterior y conectividad | Sin materiales imprescindibles en clases «sin materiales» |
| Versión mínima | 30–50 minutos efectivos por sesión: conservar, acortar u omitir cada bloque, con compensación | Decide sobre cada bloque, suma exacta de minutos, conserva explicación y exploración o indagación |
| Progresión | Ideas previas de grados anteriores y continuidad, con cómo usarlas | Sólo enlaces `(concepto, fila)` registrados en la capa de progresión 2.º–11.º |
| Inclusión | Ajustes para discapacidad visual, auditiva, motora y dificultad lectora; multigrado; escuela rural; hoja en lectura fácil | Las cuatro discapacidades básicas son obligatorias |
| Indagación | Paso hacia indagación más abierta: preguntas propias, variables, diseño, error y repetición | No reduce la autonomía del guion |
| Contexto nacional | Datos salvadoreños parafraseados de pasajes literales oficiales | Sólo cita pasajes registrados para el grado |
| Evaluación de unidad | 6–24 ítems tipo TIMSS/PISA, distractores ligados a concepciones alternativas, rúbricas | ≥20 % razonar, ≤40 % conocer, un ítem por objetivo, cálculos recomputados |

**Fuentes nacionales.** Con aprobación del usuario se descargaron 14 documentos oficiales (Asamblea Legislativa,
MARN, INS/MINSAL, OPS, FAO, OMS, ONU-SGA, USGS y programas de estudio del MINED). Se registraron con SHA-256, URL e
institución en `data/clases_v4/complementaria/fuentes_nacionales/registro.json`, junto con su texto por página. De
ellos se extrajeron 177 pasajes literales verificados contra su página
(`data/clases_v4/complementaria/pasajes.py validar`). Los sitios del MINSAL rechazan la descarga automática, y
faltan fuentes oficiales para yacimientos, taxonomía de suelos, cultivos del corredor seco y carburo de calcio.

**Proceso.** Un piloto de 6 unidades (una por estrato) se redactó y se revisó con independencia. Bloqueó 5 de 42
anexos y 2 de 6 evaluaciones. Las fallas repetidas pasaron a ser reglas de redacción y de revisión
(`INSTRUCCIONES_REDACTOR.md`, `PROTOCOLO_REVISION.md`):

- lo reducido no recorta lo evaluado;
- la inclusión no relaja la seguridad;
- la indagación debe ser físicamente realizable;
- los dominios declarados deben ser honestos;
- los distractores deben ser inequívocos.

Las 108 unidades completaron la revisión inicial independiente; 105 necesitaron una pasada acotada de
corrección y una revisión final por otro agente. No quedan revisiones pendientes. Los defectos persistentes
se retienen con su motivo; no se repiten rondas hasta obtener aprobación.

**Continuidad del 27 de octubre.** Al retomar el trabajo ya existían los 862 anexos y las 108 evaluaciones.
El estado de éxito del workflow anterior no acreditaba la revisión: había resultados vacíos contabilizados
como terminados. Se conserva una copia de los 970 originales y sus hashes en `continuidad/`, y el avance se
reconstruye desde los archivos y dictámenes. No se regeneran los guiones publicados ni se reinicia el ledger.

Cada revisión nueva declara el SHA del expediente, de todos los anexos y de la evaluación. Una corrección
conserva los hashes anterior y posterior y el dictamen que la motivó; su revisión final exige un revisor distinto
del corrector. Hay una pasada de corrección y una revisión final independiente: un defecto que persiste queda
retenido con su motivo. Los dominios se contrastan también con ejercicios, ampliaciones e indagaciones ya
enseñados; los porcentajes se comprueban sin redondear. Cambiar los archivos revisados invalida la aprobación.

```bash
uv run --frozen gskg clases complementaria-estado
uv run --frozen gskg clases complementaria-informe
uv run --frozen gskg clases complementaria
```

El informe reúne las observaciones sobre guiones originales de todas las rondas, con archivo y SHA de cada
evidencia; sólo une textos idénticos normalizados por unidad. Se mantienen como posibles defectos pendientes
de contraste, sin modificar esos guiones. Los dictámenes y el informe completos permanecen fuera de Git y se
incluyen en el respaldo de corpus. La revisión asistida por agentes distintos no da independencia estadística
ni sustituye la revisión de especialistas del MINED.

**Publicación.** `gskg clases complementaria` compila sólo lo que supera la validación y cuya última revisión aplicable es
liberable; un anexo omitido en el dictamen o sin aprobación explícita también queda retenido. La compilación
verifica las huellas de revisión, la trazabilidad de correcciones y los pasajes y metadatos exactos citados.
Lo demás queda retenido con su motivo. Escribe la publicación con identidad SHA-256 y su recibo
`config/complementos_ciencias.lock.json`. La API la sirve en `/api/v4/complementos` (resumen, `/clases`,
`/clases/{fila_id}`, `/unidades/{unidad_id}`, `/fuentes`) y responde «No hay datos disponibles» si falta o fue
alterada. Es una propuesta asistida por IA: no es aprobación del MINED ni evidencia de eficacia en aula.

<!-- inicio-cierre-local -->
**Cierre local verificado · 27 de octubre.** Se compilaron **819 anexos y 97 evaluaciones**; quedaron retenidos
43 anexos y 11 evaluaciones con sus dictámenes. Las 108 unidades tienen revisión aplicable verificable:
105 finales y tres iniciales sin corrección necesaria. Setenta unidades tienen todas sus piezas liberables;
38 conservan alguna pieza retenida. Los 862 guiones publicados y los 108 expedientes conservaron su identidad.

La compilación local es `f69e7739d570ecedda8d412ad7dece0b24311ac7abec56493e373dfed8b6c2ce`, con 123 pasajes
citados. La auditoría completa verificó los 14 documentos y 177 pasajes registrados, la trazabilidad de las
105 correcciones y los 970 originales archivados. El informe conserva 713 observaciones de todas las rondas,
con sus evidencias; son posibles defectos pendientes de contraste, no 713 errores distintos confirmados.

La suite completa pasó **1.740 pruebas sin fallos ni omisiones**, además de Ruff, auditoría y seis pruebas
JavaScript. Otra auditoría confirmó que la compilación coincide exactamente con los dictámenes y sus SHA.
El paquete local contiene 30.956 archivos (4.699.352.020 bytes; ZIP de 1.710.639.459 bytes), SHA
`2ceaf1f0541f09ae4749cc76c89578072dabb34e55d169d79c81b63d71cbdf56`; restauró sus 30.956 archivos con
huella de inventario `64e02c763887f1cce7ac216f87fbdeee8bae94633a8351234e95e35a20350a85`.
La API sobre esa restauración local verificó salud, resumen, lista y fuentes; sirvió los 916 detalles aprobados
con código 200 y rechazó los 54 retenidos con 404, sin invocar modelos. No fue una restauración desde GCS.

**Publicación pendiente.** La revisión automática bloqueó la transferencia del corpus completo y requiere
autorización explícita del usuario para ese payload y `gs://goes-ai-kg-artefactos/ciencias/v4/`. No se subió el
paquete ni se reemplazó el recibo vigente de GCS. El recibo de complementos permanece local hasta publicar,
restaurar desde el bucket y verificar un consumidor sin datos. Las correcciones R23 y sus cuatro lecturas
conservan el estado y presupuesto descritos arriba; no hubo nuevas llamadas a Vertex en esta continuidad.
<!-- fin-cierre-local -->

## Antecedentes

El alcance son los 1.013 objetivos de Ciencias de `producto-4`, agrupados en 108 unidades; los siete registros
fuera de Ciencias no se generan. Las campañas P1–P11 (22–23 de octubre) dejaron 968 guiones respaldados por
cuatro lectores automáticos, 27 vetos y 18 abstenciones; P9 introdujo parches editoriales con SHA del antecedente
y cuatro lecturas nuevas, P10 separó alertas e historial del contexto de los agentes y P11 amplió las fuentes
congeladas. La muestra de desarrollo de 32 casos (semilla 20261022) y sus seguimientos bloquearon versiones con
defectos aunque tuvieran cuatro votos favorables. Tras ampliar el tope a 4.400 llamadas, R21 y R22 obtuvieron 42
respaldos automáticos nuevos y una entrega intermedia publicó 994 guiones (`9d949257…`), reemplazada por la vigente cuando la revisión
directa integral retiró 132. La biblioteca de preparaciones (2.867 registros: 1.013 `paquete_objetivo`, 108
`paquete_unidad` y material histórico) sigue separada de la biblioteca vigente. El detalle de cada corte, con sus
cifras y expedientes, está en el historial de Git (commit `022efed`) y en los protocolos de `data/clases_v4/`.

## Contenido utilizable en clase

Cada objetivo aceptado se conserva literalmente y tiene una propuesta de una a tres sesiones de
60 minutos. El guion desarrolla las cinco fases, acciones docentes y estudiantiles, evidencia
observable, explicación científica con citas, tareas completas con datos o instrucciones de dibujo,
soluciones, rúbricas de tres niveles, apoyos, retroalimentación y seguridad.

La hoja de estudiante contiene las tareas y la atribución; el documento docente agrega el
solucionario y las revisiones. Se distingue un dato simulado de una observación real. La duración
y los recursos son propuestas condicionadas. Una representación en papel no acredita una destreza
instrumental cuando falta el instrumento. No se afirma aprobación institucional ni eficacia en aula.
Las unidades agrupan guiones en orden documental; no declaran una carga oficial ni una secuencia
pedagógica nueva por el hecho de reunirlos.

## Fuentes y alcance de la revisión

Se congelaron 890 módulos oficiales CNXML y 27.736 párrafos de cuatro libros de OpenStax / Rice
University: Biology 2e, Chemistry 2e, College Physics 2e y Astronomy 2e. Se conservan commit, URL,
SHA, localizador XML, colecciones y licencias. MathML se conserva en la evidencia. Las consultas
bilingües sirven para recuperar texto; no crean hechos ni equivalencias entre grados.

El contenido adaptado de esas fuentes conserva atribución y CC BY-NC-SA 4.0. Esta condición no se
extiende al código ni a las mallas originales del MINED. El corpus y sus fuentes completas están
fuera de Git. El manifest privado es `data/referencias_clases_2026/manifest.json`.

Los complementos conservan bytes originales y extractos literales con rangos de bytes, manifest,
SHA, versión, URL y atribución. El registro adicional fija también el código del extractor y el
corpus anterior; no sustituye los párrafos usados en ejecuciones históricas. Incluye la escala
ICS 2026/06 y texto institucional USDA sobre oscurecimiento de alimentos. Sus licencias propias
se conservan; no se extiende automáticamente la licencia de OpenStax a las fuentes adicionales.
El registro `data/referencias_complementarias_clases/registro.json` permite reconstruir cada
versión anterior por huella y reunir sus originales. Se añadieron leyendas, tablas y descripciones
accesibles de los mismos módulos CNXML; una descripción no acredita una observación.
Los extractos NPS sirven para jerarquía y eventos geológicos; las edades
numéricas se atribuyen a la edición correspondiente y se distinguen de los límites ICS actuales.

Un insumo histórico de dengue conserva tres notificaciones semanales de sospechas de MINSAL
de 2022, fechas y recibos literales breves. El servidor no permitió descargar los PDF originales;
la evidencia disponible es su vista textual primaria indexada. La tabla declara esa limitación,
no presenta casos confirmados ni estadísticas actuales y no demuestra causalidad con las lluvias.
La compilación comprueba semana, fechas, indicador, valores y correspondencia exacta con las filas.

| Revisión | Criterios |
|---|---|
| Ciencia | Exactitud, afirmaciones sustentadas y soluciones correctas |
| Currículo | Objetivo conservado, evaluación alineada y guion completo |
| Psicopedagogía | Adecuación al grado, tiempos y apoyos/accesibilidad |
| Adversarial | Seguridad, datos/fuentes y recursos factibles |

Los cuatro lectores reciben el mismo borrador y contexto; no reciben los votos de los demás.
Todos los criterios deben ser `si`. Las revisiones de la propuesta curricular anterior no son
votos de la clase. Compartir proveedor o modelo no da independencia estadística.
Los primeros controles detectaron errores introducidos a propósito. Los controles P6/P7 también
detectaron cuatro defectos concretos de contenido conservando dos casos sin defecto material.
Son controles de desarrollo conocidos, sin independencia respecto al diseño de los prompts;
no estiman precisión poblacional ni eficacia educativa.

## Flujo y controles de ingeniería

`clases/` separa contratos, fuentes, consultas, preparaciones, proveedor, grafo, validación,
presupuesto, campaña, auditoría, compilación, lectura, ZIP y publicación. El grafo LangGraph tiene
redacción, cuatro lectores paralelos y consolidación por objetivo. Se permite una reparación por
lote, sólo de las filas pendientes. Un contenido sin cambios no recibe otra ronda de votos.

Los fallos de esquema de transporte, formato y truncamiento de los pilotos se conservan en P1–P4.
P5 conserva el guion y los dictámenes válidos cuando sólo falta un lector por fallo técnico y no
hay vetos ni fallos estructurales. Recupera únicamente los roles sin dictamen, una vez, con una
salida de hasta 32.768 tokens. Si existe un veto semántico se necesita otro contenido y las cuatro
revisiones. La cota toma el mayor coste entre ambos caminos y sigue limitada a dos rondas.
P8 añade un editor de formato únicamente cuando los defectos restantes son longitudes excesivas
en tres campos de tareas. El parche enumera exactamente los campos y conserva todo lo demás;
sustituye al segundo redactor y requiere cuatro lecturas nuevas del resultado exacto. No modifica
soluciones, datos o contenido silenciosamente ni habilita una tercera ronda. Un control real de
una llamada verificó el contrato del parche; sus textos no se publican como clases.
La prueba de ingeniería en Vertex completó dos casos sintéticos con cuatro llamadas reales;
el fallo inicial era simulado y no se repitieron votos válidos. Los casos no se publican como clases.
Los campos docentes admiten hasta 2.000 caracteres; la cota del lote sigue siendo 120.000 bytes.
Los errores de una fila se aíslan si el JSON está completo y sus identidades son exactas. No se
reconstruye JSON truncado ni se corrige silenciosamente la salida. Un borrador recuperado de un
fallo técnico debe coincidir con el antecedente fijado por SHA y carecer de dictámenes anteriores;
requiere sus cuatro lecturas. Se conserva también el texto rechazado.

La aritmética usa un AST con operaciones y funciones permitidas, sin evaluación de código.
El redondeo se expresa con `round`; la tolerancia máxima del control es 1e-6 relativo y una
tolerancia absoluta nunca puede ocultar una magnitud pequeña errónea. Se verifican también los
objetivos literales, tiempos, identidades y las fuentes asignadas a cada fila.

La compilación reconstruye los dictámenes y, además, vuelve a calcular la clave de cada revisión
con el prompt, contexto, borrador, esquema, modelo y parámetros congelados. Coteja la respuesta
real y su SHA en el ledger. Cambiar juntos el histórico y la etiqueta terminal no fabrica un voto.
El ZIP y la biblioteca conservan los expedientes, incluidos rechazos y abstenciones y las respuestas
crudas de los lectores. El ZIP incluye `INDICE.md` y enlaces relativos de unidad a hojas docentes
y de estudiante, además de comprobar que cada objetivo aparece exactamente en su unidad.

## Presupuesto y reanudación

El tope acumulado es de **4.400 invocaciones y USD 3.500 de reserva conservadora**, incluidas las 668 previas
(recibos literales anclados por SHA en `config/presupuesto_clases_v4.json`). El ledger registra 4.294 llamadas y
USD 3.219,54 de reserva: quedan 106 llamadas y el usuario no autorizó otra ampliación. Antes de usar el proveedor
se comprueban por hash las filas históricas y el punto mínimo de consumo; no se admite un ledger vacío, reiniciado
o restaurado desde un respaldo anterior. La reserva no es una factura de Google.

El preflight cubre dos rondas para todo lo pendiente; cada llamada hace una reserva atómica en el mismo ledger. No
hay reintentos del SDK y los terminales se verifican y reutilizan sin gasto.

```bash
uv run --frozen gskg clases campana data/clases_v4/preparaciones \
  --plan <protocolo.json> --destino <ejecucion> --control <control.json>
# Sólo calcula la cota. Añadir --confirmar ejecuta dentro de la autorización vigente.
```

Para un bloque concreto se usa `clases ejecutar` con el mismo `--protocolo`, directorio y preparaciones. No se
crean nombres nuevos para repetir votos. Los logs conservan los estados VERDE, AMARILLO y ROJO. P1–P11 y R21–R23
son protocolos del flujo de generación; el currículo sigue siendo V4.

## Publicación y consumo

La entrega vigente está fijada en `config/clases_ciencias.lock.json` y la biblioteca en
`config/materiales_ciencias.lock.json`; `gskg datos sincronizar` trae ambas desde el bucket.

```bash
# JSON, Markdown docente/estudiante, catálogo, fuentes y auditorías en un directorio nuevo:
uv run --frozen gskg clases descargar --destino data/descargas/clases-v4
# Sólo la biblioteca SQLite indexada, sin el corpus completo:
uv run --frozen gskg materiales restaurar
uv run --frozen gskg materiales validar
```

Los objetos están bajo `gs://goes-ai-kg-artefactos/ciencias/v4/clases/<entrega_id>/` y
`ciencias/v4/materiales/<biblioteca_id>/`. Cada escritura crea objetos nuevos, verifica identidad, proyecto, UBLA
y prevención pública efectiva, y relee la generación; no cambia IAM. La restauración verifica generación, SHA e
inventario y nunca sobrescribe una carpeta en servicio.

```http
GET /api/v4/materiales?tipo=guion_clase&grado=10
GET /api/v4/materiales?tipo=guion_unidad&grado=10
GET /api/v4/materiales/detalle/{id}
GET /api/v4/materiales/descarga/{id}?formato=md
GET /api/v4/materiales/descarga/{id}?formato=md&audiencia=estudiante
GET /api/v4/materiales/archivos/{sha256}
```

La hoja de estudiante requiere `guion_clase` y Markdown. Las peticiones no llaman a Vertex.

## Referencias técnicas

El ajuste del esquema conserva la validación local completa. Google documenta el límite de
complejidad de los esquemas y que algunos límites de cadenas no se aplican en la decodificación:
[salida estructurada](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output)
y [subconjunto de JSON Schema](https://ai.google.dev/gemini-api/docs/structured-output).
Licencias: [información oficial de OpenStax](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks).
