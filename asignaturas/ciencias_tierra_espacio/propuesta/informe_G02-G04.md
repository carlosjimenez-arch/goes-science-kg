# Propuesta de Ciencias de la Tierra y el Espacio, 2.° a 4.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
El detalle de cada acción, con su evidencia, está en `propuesta_G02-G04.json`. Esta versión se recalculó con los
candidatos regenerados, que ahora incluyen a Inglaterra (ENG) y Australia (AU).

## En resumen
Proponemos 7 acciones: 3 fusiones, 3 temas nuevos y 1 reformulación (`revisar`). El total del ciclo se mantiene en
**46 temas**. El total bajó de 47 porque la revisión experta pasó el tema G02-2.3 a Física y sacó el G04-2.12 de la
asignatura, mientras que el G03-2.14 entró. No se quita ningún tema.

El cambio central es que **3.° pasa a ser el grado de los procesos de la Tierra**. Allí entran tres contenidos que
los países de alto desempeño enseñan en 2.° o 3.° y que El Salvador deja para 5.° o 7.°: el ciclo del agua, el suelo
y el tiempo atmosférico. 3.° es el primer grado posible, porque sus prerrequisitos (la hidrosfera, la atmósfera y los
descomponedores) se estudian en 3.°.

## Qué cambia y por qué

**1. El ciclo del agua entra en 3.° (acciones 1 y 2).** Lo enseñan Inglaterra en 2.°, Australia y Uruguay en 3.° y
Singapur en 5.°; El Salvador, en 7.°. Va después del tema de los océanos (3.1), que es su prerrequisito, y antes de
los temas de lagos, ríos y acuíferos, que lo necesitan. Se paga uniendo los dos temas de capas internas de la Tierra
(2.12 y 2.13).

**2. La meteorización, la erosión y el suelo entran en 3.° (acciones 3 y 4).** Inglaterra y Australia enseñan el
suelo en 2.° y Uruguay en 3.°; El Salvador, en 5.°. Proponemos un tema experimental en 3.° que empieza por la
meteorización, que es su bloqueo, y va justo antes de la formación de las rocas (2.8), que necesita la erosión. Se
paga uniendo las dos clasificaciones de volcanes (2.10 y 2.11).

**3. Medir el tiempo atmosférico desde 3.° (acciones 5 y 6).** Inglaterra y Australia lo enseñan en 2.°; El Salvador,
en 7.°. Hoy, los ciclones y los climas de 4.° se estudian sin esta base. El tema va en 3.°, después de la atmósfera, y
refuerza el objetivo TIMSS **E5.1** (uso de equipo en investigaciones), que tiene un solo tema débil. Se paga uniendo
la indagación y la simulación de fenómenos geológicos de 4.° (3.12 y 3.13).

**4. Recursos renovables antes del ahorro de energía (acción 7).** El tema 2.7 de 2.° se reformula para introducir la
diferencia entre recursos renovables y no renovables, que hoy llega en 7.°. No gasta temas del presupuesto.

## Qué cambió con los países de alto desempeño
- **El tiempo atmosférico se adelanta un grado más,** de 4.° (v1) a 3.°, porque Inglaterra y Australia lo enseñan en 2.°.
- **El suelo pasa de prerrequisito a candidato fuerte.** Lo respaldan ENG 2, AU 2 y UY 3. Ahora el tema nuevo trabaja
  la meteorización de forma explícita, que en v1 quedaba implícita.
- **El ciclo del agua gana respaldo:** ENG 2 y AU 3 se suman a UY 3 y SG 5. Se confirma 3.°.
- **Los minerales no se adelantan,** aunque AU los enseña en 2.° (ENG en 6.°), porque su prerrequisito, sustancias
  puras, llega en 10.°.
- **Las corrientes oceánicas y las mareas ya no son candidatas.** Solo las respaldaban CO y UY.
- **Cambios por la reasignación de disciplinas:** la reformulación de G02-2.3 (ahora es de Física) se traslada a G02-2.7.
  También se retira la de G03-2.15, porque el nuevo tema G03-2.14 ya presenta la composición de la atmósfera.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 10 | 10 | 21,7 % |
| 3.° | 16 | 17 | 37,0 % |
| 4.° | 20 | 19 | 41,3 % |
| **Total** | **46** | **46** | |

Todos los grados quedan por encima del 15 %. Además, el ciclo queda algo menos cargado en 4.°.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Las seis secuencias invertidas de esta asignatura quedan resueltas. Los temas
nuevos tampoco quedan antes que sus bloqueos. La simulación (`gskg propuesta simular`) da estos resultados:
- Las secuencias invertidas de confianza alta en el ciclo bajan de 8 a 1. La que queda es la geotermia, que ahora es
  de Física; ver la decisión 3.
- Los conceptos que llegan 2 grados o más tarde bajan de 4 a 1.
- El desfase medio baja de 2,12 a 1,78 grados. Varios pares quedan en el **mismo grado**, así que al ordenar los temas
hay que respetar este orden:
- océanos (3.1) → ciclo del agua → lagos, ríos y acuíferos (3.°)
- meteorización → erosión y suelo → formación de las rocas (3.°, en el mismo tema y en el siguiente)
- atmósfera (2.14) → tiempo atmosférico (3.°)
- recursos renovables → ahorro de energía y descarte de materiales (2.°)

## Decisiones abiertas para el MINED
1. **Temperatura (coordinar con Física):** el tema del tiempo atmosférico necesita leer un termómetro, y la temperatura
   y sus escalas llegan en 6.° en Física. Proponemos introducir solo la lectura en °C dentro del mismo tema. ¿Física
   prefiere adelantarlo?
2. **Descomponedores (coordinar con Biología):** el tema del suelo debe ir después del tema de 3.° sobre productores,
   consumidores y descomponedores.
3. **Temas que ahora son de Física:** dos secuencias del archivo quedan fuera de esta asignatura. La geotermia de 2.°
   (G02-2.3) necesita el calor interno de la Tierra, que no tiene tema. Las fuentes renovables de 2.3 van antes que el
   tema 2.7 reformulado. Hay que resolverlo con Física, sea reformulando 2.3 o reordenando la unidad 2.
4. **Minerales:** Australia los enseña en 2.°, pero depende de las sustancias puras (10.°). ¿Conviene tratar los
   minerales solo de forma descriptiva en 3.°, junto con las rocas (2.6)?
5. **Temas que se mantienen en grados superiores:** el ciclo del agua (G07-5.1), el tiempo atmosférico (G07-5.14 a 5.16)
   y el suelo y la meteorización (G05-6.14 a 6.19) siguen en su lugar. Conviene ajustar su profundidad para que no se
   repitan.
6. **Datos que hay que verificar:** el archivo ubica los recursos renovables por primera vez en 7.°, pero el tema
   G02-6.7 ya tiene la etiqueta. El tema G04-4.3 sigue etiquetado con «Mareas», cuyo prerrequisito (gravedad y órbitas)
   no tiene tema en la malla.
