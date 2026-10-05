# Propuesta de Química, 5.° a 8.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 13 acciones: 4 temas nuevos, 4 fusiones, 1 movimiento (de dos temas) y 4 reformulaciones (`revisar`).
El total del ciclo se mantiene en **67 temas** y no se quita ninguno. A diferencia de Biología, Química no llega
tarde en este ciclo. Al contrario, 5.° y 6.° ya trabajan estructura atómica y enlaces. El problema es otro:
**varios temas se enseñan antes que las ideas que los sostienen**. La propuesta ordena esas secuencias con el menor
cambio posible.

## Qué cambia y por qué

**1. Las ideas básicas llegan antes que el átomo y las fórmulas (acciones 1, 4 y 5).**
- En 5.° se enseña el átomo antes que el modelo de partículas, que hoy llega en 6.°. Se abre la unidad 3 de 5.°
  con un tema nuevo sobre el modelo de partículas.
- En 5.° se escriben fórmulas y se deduce la interacción iónica (4.5 y 4.6) sin saber qué es un compuesto ni qué es
  un enlace. Ambos temas pasan a la unidad *Interacciones químicas* de 6.°.
- En 6.° entra un tema nuevo sobre sustancias puras: elementos, compuestos y mezclas. Colombia y Uruguay lo enseñan en
  6.° y 5.°; El Salvador, en 10.°.

**2. La idea general precede a los casos particulares (acciones 6, 7, 8 y 13).**
- El tema 4.1 de 6.° (notación de Lewis) se reformula para explicar *por qué* se forma un enlace químico antes de los
  enlaces iónico, metálico y covalente. Colombia lo trabaja en 6.°.
- En 7.° se balancean ecuaciones en cuatro temas sin haber visto la conservación de la masa. Se agrega en 6.° un
  experimento sobre esa ley, después de las evidencias de reacción (4.9).
- El tema 5.2 de 6.° (enzimas) introduce de forma cualitativa la energía de activación para explicar qué hace un catalizador.
- El tema 4.17 de 8.° retoma las atracciones entre partículas antes de explicar la disolución.

**3. Se baja el nivel de abstracción en 5.° (acción 2).** Los números cuánticos (3.10) necesitan el modelo
mecanocuántico, que llega en 10.°. Se reformulan como distribución de electrones en niveles de energía (modelo de
capas). Eso basta para la tabla periódica y los enlaces.

**4. La química del aire entra en 5.° (acción 3).** Colombia, Singapur y Uruguay enseñan la composición del aire
y los contaminantes entre 4.° y 5.°. Aquí no hay un tema de química que lo trabaje. Se agrega en la unidad de Ciencias
de la Tierra de 5.°, junto a los procesos químicos del suelo (6.14). El tema empieza por la composición de la atmósfera,
su prerrequisito.

**5. 8.° se aligera con cuatro fusiones (acciones 9 a 12).** La unidad *Estequiometría y dispersiones* tiene 20 temas y
algunos repiten contenido:
- propiedades coligativas (4.18 y 4.19);
- número de Avogadro (4.4 y 4.5);
- tipos de dispersiones (4.12 y 4.14);
- unidades físicas de concentración (4.1 y 4.3).

Las cuatro fusiones pagan los cuatro temas nuevos.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 19 | 19 | 28,4 % |
| 6.° | 10 | 14 | 20,9 % |
| 7.° | 13 | 13 | 19,4 % |
| 8.° | 25 | 21 | 31,3 % |
| **Total** | **67** | **67** | |

Todos los grados quedan por encima del 15 %. La carga se reparte mejor: 6.° sube y 8.° baja.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Ya no aparece ningún concepto antes que sus prerrequisitos. Las diez secuencias
invertidas del archivo de candidatos quedan resueltas:
- La conservación de la masa (6.°) ya llega antes del balanceo (7.°).
- Los números cuánticos salen de 5.°.
- En los demás casos, el prerrequisito queda en el **mismo grado**. Al ordenar las unidades hay que respetar este orden:
  - modelo de partículas → átomo (5.°, unidad 3)
  - atmósfera → composición del aire (5.°, en el mismo tema)
  - sustancias puras → fórmulas y moléculas (6.°, al inicio de la unidad 4)
  - enlace químico (4.1) → enlaces iónico, metálico y covalente (4.2 a 4.4) → fórmulas iónicas (tema movido de 5.°)
  - modelos moleculares (4.5) → polaridad (4.6) (6.°)
  - energía de activación → catalizadores (6.°, en el mismo tema)
  - fuerzas intermoleculares → solvatación (8.°, en el mismo tema)

## Decisiones abiertas para el MINED
1. **Datos que conviene verificar.** Varias secuencias invertidas parecen errores de etiquetado. Puede que no sean vacíos reales:
   - *Fuerzas intermoleculares* figura en 10.°, pero los temas 4.7 y 4.8 de 6.° ya las trabajan (están etiquetados como Física).
   - *Geometría molecular* figura en 10.°, pero el tema 4.5 de 6.° la trabaja.
   - *Sustancias puras* figura en 10.°, pero el tema 5.3 de 8.° la menciona.

   Si se corrige el etiquetado, las acciones 5 y 13 podrían reducirse.
2. **Modelo de partículas.** Ya se enseña en 6.° (tema 2.1, Física). En lugar del tema nuevo de 5.°, se puede mover ese
   tema a 5.° en coordinación con Física. En ese caso, la fusión 9 queda libre.
3. **Composición del aire.** El archivo la ubica en 7.° pero sin tema asociado, y la atmósfera no tiene grado en El Salvador.
   Hay que coordinar con Ciencias de la Tierra para no duplicarla.
4. **Configuraciones electrónicas (3.11, 5.°).** Si se quitan los números cuánticos, conviene limitar también las
   configuraciones por subniveles al modelo de capas.
5. **Polaridad molecular en 6.°.** Con momento dipolar es exigente para la edad. ¿Se limita a la polaridad de enlace?
6. **Enlace químico en Bachillerato.** Al introducirse en 6.°, el tema 5.1 de 10.° (curva de energía potencial)
   debe profundizar y no repetir. Lo mismo vale para las sustancias puras (1.13 de 10.°).
