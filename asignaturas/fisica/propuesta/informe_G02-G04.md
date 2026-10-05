# Propuesta de Física, 2.° a 4.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G02-G04.json`.

## En resumen
Proponemos 15 acciones: 4 temas nuevos, 1 división, 4 fusiones y 6 reformulaciones (`revisar`). No hay movimientos
entre grados. Casi todos los conceptos que El Salvador enseña tarde están hoy en 5.° a 11.°, fuera de este ciclo, así
que no se pueden mover gratis. El total del ciclo se mantiene en **35 temas** y no se quita ninguno. En esta versión,
el tema G02-2.3 pasa a Física por la reasignación de disciplinas. El cambio central es redistribuir: se reducen las
máquinas simples y la medición, que están repetidas, y se da espacio al **calor, el sonido, los imanes, la fricción y
la luz**, que hoy tienen uno o ningún tema. **3.° gana peso:** pasa de 6 a 10 temas.

## Qué cambia y por qué

**1. Se refuerzan los tres objetivos de TIMSS 4.° que hoy tienen un solo tema.**
- *Calentamiento y enfriamiento* (P2.2). Nuevo tema en 3.°: medir con termómetro cómo un objeto caliente y uno frío
  llegan a la misma temperatura (AU 2, CO 2, ENG 6, SG 4; temperatura ENG 2, SG 4, UY 3). Solo en grados Celsius:
  las escalas siguen en 6.°.
- *Sonido* (P3.2). El tema 2.5 de 2.° se **divide**. La vibración se queda en 2.° y el tono, la intensidad y el eco
  pasan a una unidad corta de sonido en 3.°.
- *Imanes* (P4.2). Nuevo tema en 3.° sobre polos, atracción y repulsión, y materiales magnéticos (AU 3, CO 2, ENG 2,
  SG 3, UY 5). Va después de las fuerzas a distancia. Hoy los polos llegan en 6.°, después del campo magnético de 5.°.

**2. Llegan antes dos contenidos que los países enseñan en primaria:**
- La fricción y la resistencia del aire, en 3.°, dentro de la unidad de fuerzas (AU 3, ENG 2, SG 6). Hoy se enseñan en 10.°.
- La reflexión de la luz, en 4.° (AU 4, CO 3, ENG 2, SG 4, UY 4). Hoy se enseña en 10.°.

**3. Se pagan con fusiones de temas repetidos.**
- Las máquinas simples de 4.° pasan de 6 temas a 3: concepto y clasificación, palancas, y un proyecto de máquina compleja.
- Las fuentes y formas de energía de los objetos (4.°) pasan de 2 temas a 1.
- La introducción a la medición en 2.° pasa de 2 temas a 1.

Estas fusiones liberan 5 temas, los mismos que ocupan los 4 nuevos y la división.

**4. Se corrigen secuencias sin gastar presupuesto.** Las cinco secuencias invertidas del archivo de candidatos vienen
de etiquetas demasiado ambiciosas para 2.°. Se reformulan los temas:
- 2.6 (sol y sombra) trabaja solo calentar y enfriar, sin conducción, convección ni radiación.
- 5.4 (estructuras) compara diseños sin hablar del módulo de Young.
- 3.2 compara «más rápido o más lento» sin el concepto de velocidad.
- 5.2 mide masa con la balanza; el peso se deja para después de la gravedad.
- 1.4 de 3.° nombra la gravedad como fuerza a distancia. Hoy no aparece en ningún grado.

Además, 1.1 de 3.° introduce las unidades básicas del SI (CO 2, UY 3, ENG 6; destino 3.°). Hoy llegan en 5.°.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 20 | 19 | 54,3 % |
| 3.° | 6 | 10 | 28,6 % |
| 4.° | 9 | 6 | 17,1 % |
| **Total** | **35** | **35** | |

Todos los grados quedan por encima del 15 %. 4.° queda cerca del límite: sus temas de máquinas se concentran, pero
no se pierde ningún contenido. 2.° sigue concentrando más de la mitad de la Física del ciclo.

Cobertura de TIMSS 4.° en temas de Física:

| Objetivo | Antes | Después |
|---|---|---|
| Calentamiento y enfriamiento (P2.2) | 1 | 2 |
| Sonido (P3.2) | 1 | 2 |
| Imanes (P4.2) | 1 | 2 |
| Luz (P3.1) | 2 | 3 |
| Máquinas simples (P5.2) | 6 | 3 |

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Ningún concepto nuevo queda antes que sus bloqueos:
- calentamiento y enfriamiento (2.°) → temperatura → equilibrio térmico (3.°)
- fuerzas de contacto y a distancia → imanes y polos → materiales magnéticos (3.°)
- fuerzas de contacto y a distancia → fricción y resistencia del aire (3.°)
- medición con instrumentos (2.°) → unidades del SI (3.°)
- gravedad (3.°) → masa y peso (fuera del ciclo)

Hay tres casos en el **mismo grado** donde importa el orden de las unidades:
- En 3.°, los temas de imanes (1.7) y fricción (1.8) van después de 1.3 a 1.5.
- En 3.°, la temperatura va antes que el equilibrio térmico, dentro del mismo tema.
- En 2.°, el tema 2.6 (calentar y enfriar) debería ir antes que el 1.8 de Química (cambios de estado del agua).

No se adelantan tres conceptos porque tienen bloqueos tardíos:
- La dilatación térmica y el calor como energía necesitan el modelo de partículas (6.°).
- La ventaja mecánica (CO 4, ENG 3) necesita el torque (5.°). Por eso las máquinas de 4.° la tratan solo de forma
  cualitativa: «menos fuerza o cambio de dirección».

## Qué cambió con los países de alto desempeño
Inglaterra (ENG) y Australia (AU) ocupan los puestos 5 y 8 en TIMSS 2023. Su incorporación cambió lo siguiente:
- **Se confirman los cambios centrales.** Inglaterra y Australia respaldan los imanes (ENG 2, AU 3), la reflexión de
  la luz (ENG 2, AU 4) y el calentamiento y enfriamiento (AU 2). Ahora cada uno tiene 4 o 5 países.
- **Nuevo tema de fricción y resistencia del aire en 3.°.** Es un candidato nuevo (ENG 2, AU 3). Ocupa el lugar que
  dejan los conductores.
- **La temperatura baja de 4.° a 3.°.** El destino sugerido pasó a 3.° (ENG 2, UY 3), y así se equilibra 3.°, el
  grado con menos Física.
- **Los conductores y aislantes salen de este ciclo.** Con Australia (5.°) e Inglaterra la mediana queda en 5.°, así que
  pasan a la propuesta de 5.° a 8.°.
- **Se pierde una evidencia.** La ley de gravitación universal ya no figura entre los candidatos. La gravedad de 3.° se
  apoya ahora solo en la secuencia masa y peso → gravedad.
- **Presupuesto de 35 temas.** G02-2.3 (fuentes naturales de energía eléctrica) pasó a Física y se mantiene sin cambios.

## Decisiones abiertas para el MINED
1. **Datos que conviene verificar.** Hay tres conceptos cuyo «primer grado» contradice un tema que ya existe. Los
   tratamos como dudosos y no como hechos:
   - El archivo ubica «Calentamiento y enfriamiento» en 10.°, pero G02-2.6 ya lo trabaja.
   - Ubica «Flotación y hundimiento» en 6.°, pero G02-1.10 (Química) ya la trabaja. Por eso **no** se propone un tema
     nuevo de flotación, aunque los tres países la enseñan en 3.° o 4.°.
   - Ubica «Imanes y polos» en 6.°, pero G03-1.4 está alineado con atracción magnética.
2. **Sonido.** Ni siquiera con Inglaterra y Australia el archivo trae datos de países sobre tono, intensidad y eco. La división de 2.5 se apoya solo en el
   objetivo TIMSS débil. Conviene confirmarla con los currículos de CO, SG y UY.
3. **Efecto en 5.° a 8.°.** Al introducirse antes, estos temas podrían repetirse más adelante si no se ajustan:
   - el termómetro y las escalas (G06-2.2 y 2.3)
   - el equilibrio térmico (G09-2.6)
   - el SI (G05-1.1 a 1.6)
   - la fricción (10.°)

   Los conductores y aislantes eléctricos salieron de este ciclo (ver la sección anterior). Deben entrar en la
   propuesta de 5.° a 8.°, antes del circuito simple de 6.°.

   Conviene ajustar su profundidad en la propuesta de 5.° a 8.°. ¿Dónde se distingue masa de peso: 4.° o 5.°?
4. **Peso de las Ciencias Físicas frente a TIMSS 4.°.** El balance está levemente por debajo de la meta. Esta propuesta
   reparte mejor los temas dentro de Física, pero no aumenta su número. Subir la proporción exigiría tomar temas de
   otras asignaturas del ciclo, y esa decisión es entre asignaturas.
5. **Carga de 2.°.** Se podría pasar la unidad de movimiento (3.1 a 3.3) a 3.°, junto a las fuerzas, para equilibrar
   los grados. No lo proponemos porque rompería su vínculo con los movimientos de la Tierra (3.4 a 3.8). Queda a
   criterio del MINED.
