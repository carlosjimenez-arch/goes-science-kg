# Propuesta de Ciencias de la Tierra y el Espacio, 2.° a 4.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
El detalle de cada acción, con su evidencia, está en `propuesta_G02-G04.json`.

## En resumen
Proponemos 8 acciones: 3 fusiones, 3 temas nuevos y 2 reformulaciones (`revisar`). No hay movimientos. El total del
ciclo se mantiene en **47 temas**, no se quita ninguno y cada grado conserva su número de temas.

El archivo de candidatos trae pocos cambios fuertes. En cambio, muestra varias **secuencias invertidas**: temas de 2.° a
4.° que usan ideas que la malla presenta en 5.° o 7.°, o que no presenta. Por eso la propuesta corrige el orden
dentro de cada grado y no mueve temas entre grados.

## Qué cambia y por qué

**1. El ciclo del agua entra en 3.° (acciones 1 y 2).** Hoy se estudia en 7.°, pero en 3.° ya se trabajan los
océanos, lagos, ríos, glaciares y acuíferos sin el ciclo que los conecta. Uruguay lo enseña en 3.° y Singapur en 5.°.
El candidato sugería 4.°. Lo ubicamos en 3.°, al inicio de la unidad «El agua», porque los temas 3.2, 3.3 y 3.5 lo
necesitan. Se paga uniendo los dos temas de capas internas de la Tierra (2.12 y 2.13). Ese tema unido deja la
composición química, que es demasiado para 3.°.

**2. Erosión y formación del suelo antes de las rocas y los cultivos (acciones 3 y 4).** El tema 2.8 de 3.° (procesos
de formación de las rocas) y el 2.12 de 4.° (cultivos y uso del suelo) necesitan la erosión, la sedimentación y la
formación del suelo, que hoy llegan en 5.°. Un tema nuevo y experimental en 3.° las introduce justo antes del 2.8.
Se paga uniendo las dos clasificaciones de volcanes (2.10 y 2.11). Los volcanes conservan cinco temas en el ciclo.

**3. Medir el tiempo antes de estudiar climas y ciclones (acciones 5 y 6).** En 4.° se estudian ciclones, tormentas y
climas tropicales, pero el tiempo atmosférico y sus variables llega en 7.°. Proponemos un tema nuevo de medición con
termómetro, pluviómetro y veleta al inicio del bloque hidrometeorológico. Además, refuerza el objetivo TIMSS **E5.1**
(uso de equipo en investigaciones), que hoy tiene un solo tema débil. Se paga uniendo la indagación y la simulación
de fenómenos geológicos (3.12 y 3.13).

**4. Dos reformulaciones que ordenan prerrequisitos sin gastar temas (acciones 7 y 8).**
- El tema 2.3 de 2.° introduce la diferencia entre recursos renovables y no renovables y el calor interno de la
  Tierra. Así llegan antes del ahorro de energía (2.7), del descarte de materiales (6.7) y de la geotermia.
- El tema 2.15 de 3.° presenta la composición del aire antes de las capas de la atmósfera.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 11 | 11 | 23,4 % |
| 3.° | 15 | 15 | 31,9 % |
| 4.° | 21 | 21 | 44,7 % |
| **Total** | **47** | **47** | |

Todos los grados quedan por encima del 15 %. 4.° sigue concentrando casi la mitad del ciclo.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Las 11 secuencias invertidas del archivo de candidatos quedan resueltas: en
ningún caso un concepto aparece antes que su prerrequisito. En estos casos, el tema y su prerrequisito quedan en el
**mismo grado**, así que al ordenar las unidades hay que respetar este orden:
- ciclo del agua → lagos, ríos y acuíferos (3.°, unidad 3)
- meteorización y erosión → formación de las rocas (3.°, unidad 2)
- composición del aire → capas de la atmósfera (3.°, mismo tema)
- recursos renovables y calor interno → ahorro de energía y descarte de materiales (2.°)
- tiempo atmosférico → fenómenos hidrometeorológicos, ciclones y climas (4.°, unidad 3)

## Decisiones abiertas para el MINED
1. **Corrientes oceánicas (CO 4, UY 5):** no se adelantan. Su prerrequisito, el calentamiento desigual de la Tierra,
   está en 9.°. Además, traerlas desde 9.° costaría temas del ciclo. ¿Se adelantan junto con su prerrequisito en el
   ciclo de 5.° a 8.°?
2. **Mareas, un dato que hay que verificar:** el archivo ubica las mareas por primera vez en 9.°, pero el tema G04-4.3
   ya tiene la etiqueta «Mareas». Además, su prerrequisito, gravedad y órbitas, no tiene tema en la malla. Hay que
   confirmar si 4.3 trabaja las mareas. Si lo hace, hay que decidir si se mantiene sin la gravedad o si se quita la
   etiqueta.
3. **Recursos renovables, otro dato que hay que verificar:** el archivo ubica este concepto por primera vez en 7.°,
   pero el tema G02-6.7 ya tiene la etiqueta. La acción 7 lo hace explícito en 2.° de todas formas.
4. **Temas que se mantienen en grados superiores:** el ciclo del agua (G07-5.1), la erosión y el suelo (5.°) y el
   tiempo atmosférico (7.°) siguen allí. Conviene ajustar su profundidad para que no se repitan.
5. **Carga de 4.°:** tiene 21 temas, el 45 % del ciclo, y casi todos los de astronomía. ¿Prefieren pasar a 3.° algún
   tema de 4.° sin prerrequisitos, por ejemplo la precesión y la nutación (4.7)?
