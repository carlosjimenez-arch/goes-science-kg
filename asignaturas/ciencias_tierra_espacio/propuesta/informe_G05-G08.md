# Propuesta de Ciencias de la Tierra y del Espacio, 5.° a 8.° (borrador)

Versión `propuesta-v4`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 17 acciones: 7 movimientos (13 temas), 4 temas nuevos, 4 fusiones (una de ellas también pasa a 6.°) y 2
reformulaciones (`revisar`). El total del ciclo se mantiene en **64 temas** y no se quita ninguno. El cambio central
sigue siendo que **6.° vuelve a tener Ciencias de la Tierra y del Espacio**: hoy tiene 0 temas y pasaría a 13. Recibe la
unidad de espacio de 5.°, ordenada a partir de la gravedad, y una unidad de tiempo atmosférico que viene de 7.°. Esta
versión añade en 7.° el **ciclo del carbono**, que hoy llega en 10.°.

## Qué cambió con Japón
Japón (TIMSS 2023: 6.° lugar en 4.° grado y 3.° en 8.° grado) entra como país de referencia. Los países de alto
desempeño son ahora Singapur, Inglaterra, Australia y Japón.
- **Ciclo del carbono, candidato nuevo (acciones 13 y 14).** Japón lo enseña en 5.°, Inglaterra en 6.° y Australia en
  8.°; El Salvador, en 10.°. Se crea un tema en 7.°, después de la combustión, pagado con la fusión de los dos temas de
  cambio climático.
- **Calidad del aire, ahora con dos países de alto desempeño (acción 15).** Japón y Singapur la enseñan en 5.°. Su
  bloqueo, los combustibles fósiles, está en 7.°, así que no cambia de grado, pero se reubica dentro de 7.° después de
  los combustibles, porque hoy se enseña antes que ellos.
- **Más respaldo para lo que ya se proponía.** Japón enseña el ciclo del agua y el tiempo atmosférico en 3.°. El ciclo
  del agua (acción 7) queda respaldado por los cuatro países de alto desempeño; el tiempo atmosférico (acciones 9 y 10),
  por tres.
- **Las mareas dejan de ser candidato a adelantarse.** Ya no figuran en el archivo de candidatos. El tema nuevo de fases,
  eclipses y mareas (acción 5) se mantiene porque cubre el objetivo E4.1, que no tiene temas en el ciclo.
- **Los minerales siguen en 8.°.** Su bloqueo (sustancias puras) aparece ahora en 8.°, como sospechábamos. Ya no
  pueden adelantarse, así que la decisión abierta de la v2 queda resuelta.

## Qué cambia y por qué

**1. La unidad de espacio pasa de 5.° a 6.° y empieza por la gravedad (acciones 1 a 6).** Hoy 5.° enseña la formación
del sistema solar y la vida de las estrellas sin haber visto la gravedad. Se crea en 6.° la unidad provisional
*7. La Tierra en el universo*, ordenada de lo cercano a lo lejano:
- 7.1: un tema nuevo sobre la gravedad;
- 7.2 y 7.3: las estrellas y su evolución, con la fusión nuclear presentada de forma cualitativa;
- 7.4 y 7.5: la formación del sistema solar y la de la Tierra;
- 7.6: el campo magnético terrestre, ya después de los imanes de 6.°;
- 7.7: un tema nuevo sobre fases de la Luna, eclipses y mareas, que cubre el objetivo E4.1 (hoy sin temas);
- 7.8 a 7.11: escalas, galaxias, Big Bang y exploración espacial.

**2. El agua y el tiempo atmosférico llegan antes (acciones 7 a 10).**
- El ciclo del agua (G07 5.1) pasa a 5.°, antes del suelo y la erosión.
- En 6.° se crea la unidad provisional *8. El tiempo atmosférico*: construcción y uso de instrumentos (5.15,
  reformulado para cubrir el objetivo E5.1, hoy sin cobertura) y registro y análisis de datos (fusión de 5.14 y 5.16).
- En 7.° entra un tema nuevo sobre el calentamiento desigual de la Tierra, los vientos y las corrientes oceánicas
  superficiales, que hoy llegan en 9.°. Va antes de los ciclones tropicales, que lo necesitan.

**3. En 7.°, la unidad *Ambiente y energía* sigue una cadena de causas (acciones 13 a 15).** Queda así:
combustibles y combustión (6.4 a 6.6) → ciclo del carbono (nuevo) → calidad del aire (5.12 y 5.13, que vienen de la
unidad 5) → efecto invernadero (6.13) → cambio climático (6.14 y 6.15 fusionados).

**4. Cuatro fusiones pagan los cuatro temas nuevos (acciones 10, 11, 12 y 14):** registro y análisis meteorológico;
energías renovables y no renovables; sostenibilidad y prácticas sostenibles; causas y efectos del cambio climático.

**5. Dos temas de 5.° se reformulan sin gastar presupuesto (acciones 16 y 17):** 6.6 introduce la convección del manto
antes de la tectónica; 6.9 se centra en la intensidad sísmica, que es observable, y deja la magnitud para 9.°. En la v4, 6.9 deja de
llevar la etiqueta de ondas sísmicas (`quitar_conceptos`): el concepto se introduce en 9.° (G09 5.8 y 5.9), después de
las ondas mecánicas de 8.°.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 29 | 21 | 32,8 % |
| 6.° | 0 | 13 | 20,3 % |
| 7.° | 31 | 26 | 40,6 % |
| 8.° | 4 | 4 | 6,3 % |
| **Total** | **64** | **64** | |

La distribución no cambia respecto de la v2: el tema nuevo del ciclo del carbono y su fusión están en 7.°. 8.° queda
por debajo del 15 %, como hoy: es el grado más cargado de la malla, y su único candidato, los minerales, ya está en su
grado mínimo por el bloqueo.

## Prerrequisitos que se ordenan
Un script de validación comprobó que el total se conserva, que los ids y los conceptos existen y que ningún tema movido
queda antes de un bloqueo del archivo de candidatos. Se resuelven estas secuencias invertidas:
- gravedad → sistema solar, estrellas y exploración;
- imanes → campo magnético terrestre;
- convección del manto → tectónica;
- calentamiento desigual → ciclones;
- ondas mecánicas (8.°) → ondas sísmicas y magnitud (9.°), al retirar esa etiqueta del tema 6.9 de 5.°;
- combustibles fósiles → calidad del aire (dentro de 7.°);
- fotosíntesis y combustión → ciclo del carbono → cambio climático.

Órdenes que hay que respetar dentro de cada grado:
- en 6.°, la unidad 7 sigue la secuencia gravedad → estrellas → sistema solar → Tierra → campo magnético → Luna →
  galaxias → Big Bang, y la unidad 8 va después de las escalas de temperatura (G06 2.3);
- en 7.°, el ciclo del carbono y la calidad del aire van después de 6.6 y antes de 6.13.

Avisos menores: la fusión nuclear (6.°) y el calor interno de la Tierra (5.°) se presentan de forma cualitativa; los
sistemas terrestres, que hoy no se enseñan, se introducen dentro del tema del ciclo del carbono.

## Decisiones abiertas para el MINED
1. **Tiempo atmosférico en 5.°.** Tres países de alto desempeño lo trabajan entre 2.° y 3.°. Solo lo impide la
   temperatura y sus escalas (Física, G06 2.3). Si Física la adelantara a 5.°, la unidad de tiempo atmosférico podría
   pasar a 5.°.
2. **Calidad del aire antes de 7.°.** Japón y Singapur la enseñan en 5.°. Adelantarla exigiría llevar a 6.° los
   combustibles fósiles y la combustión; lo dejamos para una revisión conjunta con Física y Química.
3. **Ciclo del agua y cambios de estado.** El concepto está duplicado en el grafo (Física en 6.°, Química en 2.°).
   Conviene unificarlo.
4. **Datación de fósiles (G05 6.3).** Hay que acordar con Biología quién mantiene la reformulación que presenta los
   fósiles como evidencia de la evolución.
5. **Bachillerato.** Con la gravedad en 6.° y el ciclo del carbono en 7.°, conviene ajustar la profundidad de G10 5.7 y
   6.5 y del ciclo del carbono de 10.°, y que las mareas de 9.° (G09 4.10) se profundicen, no se repitan.
6. **Carga de 7.°.** 7.° sigue con 26 temas (41 %). Equilibrarlo con 8.° debe decidirse junto con el ciclo de 9.° a 11.°.
7. **Arista «Ondas sísmicas, magnitud e intensidad» → «Precursores, monitoreo y alerta de sismos y erupciones».**
   Es la única secuencia de confianza alta que queda: 5.° enseña los sismos precursores y la vigilancia volcánica
   (G05 6.10 y 6.12) antes de las ondas sísmicas (9.°). No la corregimos porque creemos que la arista es demasiado
   fuerte: reconocer réplicas y precursores y vigilar gases, temperatura y deformación de un volcán no exige la teoría
   de las ondas; solo la exigen los sistemas de alerta temprana (G09 5.11). Proponemos debilitarla o retirarla del grafo.
