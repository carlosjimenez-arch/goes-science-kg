# Propuesta de Ciencias de la Tierra y del Espacio, 5.° a 8.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 13 acciones: 4 movimientos (9 temas), 3 temas nuevos, 3 fusiones y 3 reformulaciones (`revisar`). Son menos de las
habituales porque el archivo de candidatos trae pocos cambios fuertes. El total del ciclo se mantiene en **60 temas** y no
se quita ninguno. El cambio central es que **6.° vuelve a tener Ciencias de la Tierra y del Espacio**: hoy tiene 0 temas y
pasaría a 11. Recibe la unidad de espacio de 5.°, ordenada a partir de la gravedad, y el ciclo del agua de 7.°.

## Qué cambia y por qué

**1. La unidad de espacio pasa de 5.° a 6.° y empieza por la gravedad (acciones 1 a 5).** Hoy 5.° enseña la formación
del sistema solar y la vida de las estrellas sin haber visto la gravedad. Ningún tema antes de 10.° la trabaja como causa
de las órbitas. Se crea en 6.° la unidad provisional *7. La Tierra en el universo*, ordenada de lo cercano a lo lejano:
- un tema nuevo sobre la gravedad y las órbitas, tratado de forma cualitativa;
- las estrellas y su evolución (5.5 y 5.6), que presentan la fusión nuclear como fuente de energía del Sol sin ecuaciones;
- la formación del sistema solar (5.3) y la formación de la Tierra (5.8), que depende de la anterior;
- las escalas, las galaxias, el Big Bang y la exploración espacial (5.2, 5.4, 5.1 y 5.7).

Con esto, 5.° queda centrado en geología, fósiles y suelo, y gana espacio para las unidades nuevas de Biología.

**2. Llegan antes los fenómenos de la Tierra y la Luna, el ciclo del agua y las corrientes (acciones 4, 6 y 7).**
- *Fases de la Luna, eclipses y mareas* (tema nuevo en 6.°, después de la gravedad). El objetivo TIMSS E4.1 no tiene
  ningún tema en el ciclo. Hoy las mareas llegan en 9.°, mientras Colombia y Uruguay las enseñan en 4.° y 5.°.
- *Ciclo del agua* (G07 5.1 pasa a 6.°). Singapur lo enseña en 5.° y Uruguay en 3.°. Se ubica en la unidad de Calor y
  temperatura, después de los cambios de fase (2.4), que son su motor.
- *Calentamiento desigual de la Tierra, vientos y corrientes oceánicas superficiales* (tema nuevo en 7.°). Las
  corrientes y su bloqueo llegan hoy en 9.°, y Colombia y Uruguay las enseñan en 4.° y 5.°. El tema va antes de los
  ciclones tropicales, que también lo necesitan.

**3. Tres fusiones en 7.° pagan los temas nuevos (acciones 8 a 10).** Se unen temas seguidos que trabajan el mismo
contenido:
- registro y análisis de parámetros meteorológicos (5.14 y 5.16);
- energías renovables y no renovables (6.7 y 6.9);
- sostenibilidad y prácticas sostenibles (6.19 y 6.20).

**4. Tres temas se reformulan para corregir la secuencia sin gastar presupuesto (acciones 11 a 13).**
- 6.6 (5.°) introduce la convección del manto como motor de la deriva continental, antes de la tectónica (6.7 y 6.8).
- 6.9 (5.°) se centra en la intensidad, que es observable. La magnitud y las ondas sísmicas quedan en 9.°, después
  de las ondas mecánicas de 8.°.
- 5.15 (7.°) hace explícito el uso de los instrumentos de una estación meteorológica (objetivo E5.1, hoy sin cobertura).

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 27 | 19 | 31,7 % |
| 6.° | 0 | 11 | 18,3 % |
| 7.° | 29 | 26 | 43,3 % |
| 8.° | 4 | 4 | 6,7 % |
| **Total** | **60** | **60** | |

8.° queda por debajo del 15 %, como hoy. No se completa porque 8.° es el grado más cargado de la malla (93 temas entre
todas las asignaturas) y porque la asignatura se concentra en 9.°, con Oceanografía y Geología de El Salvador (27 temas).
Llevar contenidos a 8.° los retrasaría, y la evidencia indica que El Salvador ya llega tarde.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Se resuelven estas secuencias invertidas:
- gravedad → formación del sistema solar, evolución estelar y exploración espacial;
- convección del manto → tectónica de placas;
- calentamiento desigual → ciclones tropicales;
- ondas mecánicas → magnitud sísmica (la magnitud pasa a 9.°).

Ningún tema movido queda antes de un bloqueo del archivo de candidatos. Dentro de 6.°, el orden de la unidad debe
respetar la secuencia gravedad → estrellas → sistema solar → Tierra → fases, eclipses y mareas → galaxias → Big Bang.
El ciclo del agua debe ir después del tema 2.4 de Física.

Quedan avisos menores. Las ideas de fusión nuclear (6.°) y de calor interno de la Tierra (5.°) se presentan sin su base
de física nuclear de 11.°. Es una introducción cualitativa, no un cálculo.

## Decisiones abiertas para el MINED
1. **Ciclo del agua en 5.° o 6.°.** El archivo de candidatos sugiere 5.° y dice que no tiene bloqueos. Pero el grafo
   marca los cambios de estado de Física (6.°) como su prerrequisito, y hay un concepto duplicado en Química (2.°).
   Proponemos 6.°. Si el equipo considera suficiente lo visto en 2.°, puede ir a 5.°.
2. **Campo magnético terrestre (G05 5.9, Física).** Queda solo en la unidad de espacio de 5.° y necesita los imanes de
   6.° (3.8 y 3.9). Conviene que Física lo mueva a 6.° junto con la unidad.
3. **Calidad del aire.** Los países la enseñan entre 4.° y 5.°, pero sus bloqueos (combustibles fósiles y composición del
   aire) están en 7.°. Además, el archivo no le asigna temas, aunque G07 5.12 y 5.13 la trabajan con etiqueta de
   Biología. Hay que verificar el etiquetado antes de moverla.
4. **Gravedad y mareas en el grafo.** El archivo dice que «Gravedad y órbitas» no se enseña nunca, pero Física la trabaja
   en 10.° (G10 5.7 y 6.5). Al introducirla en 6.° hay que ajustar allí la profundidad. Lo mismo ocurre con las mareas de
   9.° (G09 4.10): conviene profundizarlas allí y no repetirlas.
5. **Equipo de investigación (E5.1).** El archivo lo marca sin cobertura, pero 5.15 ya construye instrumentos y G05 2.2
   usa GPS. Puede ser un problema de alineación más que de contenido.
6. **Carga de 7.°.** 7.° sigue con 26 temas de la asignatura (43 %) y es uno de los grados más cargados de la malla.
   Si se busca más equilibrio entre 7.° y 8.°, habría que decidirlo junto con el ciclo 9.°–11.°, porque el contenido que podría ir a 8.° (rocas, G09 5.1 y 5.2) hoy está fuera de este ciclo.
