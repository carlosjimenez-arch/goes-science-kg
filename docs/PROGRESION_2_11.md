# Progresión de conceptos de 2.º a 11.º · Ciencias V4

Corte: 25 de octubre de 2026. Publicación `producto-4`, snapshot
`e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`.

Este análisis responde cómo se **introducen** los conceptos de Ciencias en la malla V4 y en qué grados se
**vuelven a trabajar**. Hasta este corte, el grafo publicado sólo relacionaba filas, unidades, propuestas y
fuentes: tenía un nodo `Concepto` y dos `RelacionCurricular`, por lo que no podía describir la progresión
vertical. La capa de conceptos del grafo histórico V3 (513 conceptos, 822 prerrequisitos y 100 equivalencias)
no se había trasladado a V4. Los resultados son **hipótesis para revisión experta**, no hallazgos aprobados.

## Método

| Paso | Qué se hizo | Control |
|---|---|---|
| Etiquetado ciego | 1.314 ítems: 1.013 filas de Ciencias y 301 objetivos que la propuesta precisa | 76 lotes por grado y disciplina catalogada; 14 agentes de lote sin acceso al etiquetado V3 |
| Validación de la unión | Conceptos y prácticas del vocabulario del lote, justificación ≤15 palabras | Cada etiqueta exige un fragmento **literal** del ítem; la unión rechaza otro snapshot |
| Equivalencias | 76 clases `EQUIVALE_A` revisadas en V3 (p. ej. fósiles en Biología y en Tierra) | Una trayectoria no se fragmenta por cambiar de disciplina |
| Menciones léxicas | Nombres, sinónimos y segmentos con dos palabras de contenido, exclusivos de un concepto; siglas sólo en mayúsculas | Frases genéricas («seres vivos», «características») y «más»≠MAS no cuentan |
| Prerrequisitos | 822 aristas V3 con su confianza | El prerrequisito cuenta desde su primera etiqueta o mención |
| Verificación independiente | Agente de sólo lectura cotejó cada caso prioritario con `curriculo.json` | Resultado conservado junto al artefacto y anclado a su SHA |
| Revisión adversarial | Agente revisor del código y de la API viva | Corrigió falsos positivos léxicos, la definición de patrones y la atribución por disciplina |

Consumo: cero llamadas a Vertex. Los agentes de lote trabajaron dentro de la sesión de ingeniería.

**Acuerdo con V3.** En 491 filas cuyo objetivo coincide 1:1 con V3, el concepto principal coincide en el
82,3 %, con F1 0,833 (precisión 0,865; exhaustividad 0,804). V3 es otra pasada automática y revisada, no una
verdad de referencia: la cifra mide consistencia entre pasadas.

Confianza declarada de las 1.314 etiquetas: 963 alta, 310 media y 41 baja.

## Patrones de refuerzo

| Patrón | Definición | Sólo etiquetas | Con menciones |
|---|---|---:|---:|
| Aislado | Un solo grado | 160 | 119 |
| Concentrado | Dos grados, seguidos o con uno intermedio | 73 | 78 |
| Espiral | Tres o más grados con huecos de un grado como máximo | 33 | 47 |
| Intermitente | Vuelve tras dos o más grados sin tratarse | 202 | 224 |

Sobre 468 conceptos presentes (de 513). Cada concepto aparece en promedio en 2,05 grados.

- **El refuerzo existe, pero es intermitente.** La forma dominante es retomar un concepto tras dos o más grados
  de ausencia. Sólo el 7 % (etiquetas) o el 10 % (con menciones) sigue una espiral continua.
- **Química es la disciplina más fragmentada:** 67 conceptos aislados por etiqueta (52 con menciones) y 56 de
  sus 108 conceptos de bachillerato no tienen antecedente en 2.º–9.º.
- **Tierra y espacio termina en 9.º:** de 73 conceptos tratados en 2.º–9.º sólo 5 reaparecen en 10.º–11.º,
  porque el bachillerato no tiene esa asignatura.
- **Las prácticas científicas sí forman espiral.** Modelar y medir aparecen en los diez grados; interpretar datos
  y observar, en nueve. En cambio, «formular preguntas investigables» sólo se etiqueta en 10.º y comunicar
  resultados no aparece en bachillerato.
- **Las propuestas mejoran poco la continuidad vertical:** aumentan la espiral de 33 a 43 conceptos y reducen
  los aislados de 160 a 144, pero las prioridades por fila no optimizan la secuencia entre grados.

## Entrada a bachillerato

| Disciplina | Conceptos en 10.º–11.º | Con antecedente en 2.º–9.º | Nuevos en bachillerato |
|---|---:|---:|---:|
| Biología | 89 | 70 | 19 |
| Física | 125 | 82 | 43 |
| Química | 108 | 52 | 56 |
| Tierra y espacio | 5 | 5 | 0 |

Un concepto que agrupa equivalentes de varias disciplinas cuenta en cada una de ellas.

## Orden de prerrequisitos

De 747 prerrequisitos evaluables, 385 (51,5 %) se introducen en orden y 279 en el mismo grado; contando sólo
etiquetas, la proporción en orden es 48,2 %. En 83 casos el prerrequisito aparece **después** del concepto que
lo necesita: 10 son introducciones cualitativas tempranas (concepto de primaria), 28 son prioritarios
(concepto de mayor nivel, desfase ≥2 grados y arista de confianza alta) y 45 quedan para revisar.

La verificación independiente de los 28 prioritarios contra la fuente dio **3 confirmados, 18 parciales y
7 refutados**. Confirmados: acuíferos y sequía en 3.º antes del ciclo hidrológico (7.º), ciclo de las rocas en
3.º antes de erosión y sedimentación (5.º) y diagrama de cuerpo libre en 8.º sin rozamiento hasta 10.º. Los
parciales son tensiones reales de secuencia en las que el concepto temprano se trata de forma cualitativa (por
ejemplo, el Big Bang en 5.º antes del efecto Doppler o las enzimas en 6.º antes de catalizadores). Los
refutados se deben a etiquetas que no representan la fila o a contenidos tratados dentro de otra fila. La
lista es un **triaje para expertos**, no una lista de errores.

La medición tuvo dos correcciones documentadas. Una primera lista basada sólo en etiquetas refutaba 11 de 30
casos; se añadió la capa de menciones. Después, la revisión adversarial mostró que fragmentos genéricos
(«características») y la sigla MAS leída como «más» inflaban el orden; las claves se restringieron y la API
publica ambas proporciones.

## Observaciones de la fuente para el MINED

Detectadas por el escaneo determinista y por los agentes de etiquetado; requieren confirmación humana.

| Tipo | Ubicación | Observación |
|---|---|---|
| Objetivo duplicado | 2.º U6 filas 8–9; 3.º U2 filas 6–7; 8.º U4 filas 19–20 | Mismo objetivo en filas consecutivas |
| Fila incompleta | 3.º U2 fila 7 | Sin indicador, contenido, evidencia ni habilidad TIMSS |
| Indicador casi idéntico | 11.º Biología filas 7–8; 7.º U1 filas 5 y 17; 8.º U3 filas 6–7; 9.º U9 filas 7–8 | Objetivos distintos con indicador ≥85 % igual |
| Indicador ajeno | 11.º Física 4.3 | Repite el indicador de 4.2 (Ampère) en una fila de fuerza magnética |
| Contenido incongruente | 6.º 5.22; 10.º Física 7.3; 9.º 8.4 | Contenido, objetivo o indicador hablan de cosas distintas |
| Fuera de alcance | 9.º U6 6.13 | Compuertas lógicas: tecnología, no Ciencias |
| Nivel adelantado | 5.º (números cuánticos, configuración electrónica), 8.º (molaridad, estequiometría) | Conceptos de bachillerato en primaria/secundaria |
| Anotación TIMSS | Todas las hojas | 957 de 1.020 filas declaran dos o tres dominios; 21 filas de 2.º anotan «Razonar» |

Los agentes también propusieron 173 conceptos que faltan en el vocabulario (p. ej. máquinas compuestas,
transferencia genética horizontal, servicios ecosistémicos, carbohidratos y lípidos en Biología). El
vocabulario no se modificó.

## Límites

- Las etiquetas describen presencia documental en la malla: no secuencia oficial, carga horaria ni aprendizaje.
- Un concepto general (p. ej. «Enlace químico») puede parecer aislado cuando los grados posteriores trabajan sus
  conceptos específicos; el vocabulario no relaciona todos los niveles de granularidad.
- El vocabulario se entregó por disciplina catalogada: una fila de Biología no podía usar conceptos de
  Química (carbohidratos, redox). Las filas mixtas recibieron las cuatro disciplinas.
- El concepto dividido `configuracion-electronica` se usó en 10.º Química y 5.º sin registrar su reparto.
- Los prerrequisitos son hipótesis V3 inferidas por IA (454 de confianza alta, 361 media).
- Durante el etiquetado, un script auxiliar compartido reescribió las seis salidas de 4.º con el código de su
  propio agente; los identificadores y la validación coinciden y difiere una etiqueta de confianza.

## Reproducir y consultar

```bash
uv run gskg producto preparar-conceptos     # lotes ciegos en data/interim/conceptos/lotes_v4
uv run gskg lotes validar --agente etiquetador-conceptos
uv run gskg producto unir-conceptos         # data/producto/conceptos_v4/etiquetado.json
uv run gskg producto progresion             # data/producto/progresion_v4/progresion.json
```

En la aplicación: **Progresión 2.º–11.º**. API: `GET /api/v4/interfaz/progresion?vista=original|propuesta`,
`/progresion/conceptos` (filtros `disciplina`, `patron`, `q`) y `/progresion/conceptos/{id}`. Sin el artefacto,
o con otro snapshot, responden 503 «No hay datos disponibles». Los artefactos se respaldan en GCS con el corpus.
