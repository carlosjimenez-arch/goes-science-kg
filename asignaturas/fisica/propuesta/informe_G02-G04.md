# Propuesta de Física, 2.° a 4.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G02-G04.json`.

## En resumen
Proponemos 15 acciones: 4 temas nuevos, 1 división, 4 fusiones y 6 reformulaciones (`revisar`). No hay movimientos
entre grados. Casi todos los conceptos que El Salvador enseña tarde están hoy en 5.° a 11.°, fuera de este ciclo, así
que no se pueden mover gratis. El total del ciclo se mantiene en **34 temas** y no se quita ninguno. El cambio central
es redistribuir: se reducen las máquinas simples y la medición, que están repetidas, y se da espacio al **calor, el
sonido, los imanes, la luz y la electricidad**, que hoy tienen uno o ningún tema.

## Qué cambia y por qué

**1. Se refuerzan los tres objetivos de TIMSS 4.° que hoy tienen un solo tema.**
- *Calentamiento y enfriamiento* (P2.2). Nuevo tema en 4.°: medir con termómetro cómo un objeto caliente y uno frío
  llegan a la misma temperatura (CO 2, SG 4; equilibrio térmico SG 4, UY 5). Solo en grados Celsius: las escalas
  siguen en 6.°.
- *Sonido* (P3.2). El tema 2.5 de 2.° se **divide**. La vibración se queda en 2.° y el tono, la intensidad y el eco
  pasan a una unidad corta de sonido en 3.°.
- *Imanes* (P4.2). Nuevo tema en 3.° sobre polos, atracción y repulsión (CO 2, SG 3, UY 5). Va después de las
  fuerzas a distancia. Hoy los polos llegan en 6.°, después del campo magnético de 5.°.

**2. Llegan antes dos contenidos que los países enseñan en primaria:**
- La reflexión de la luz, en 4.° (CO 3, SG 4, UY 4). Hoy se enseña en 10.°.
- Los conductores y aislantes eléctricos, en 4.°, con un probador de pila y foco (CO 4, SG 5). Hoy se enseñan en 11.°.

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

Además, 1.1 de 3.° introduce las unidades básicas del SI (CO 2, UY 3). Hoy llegan en 5.°.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 19 | 18 | 52,9 % |
| 3.° | 6 | 8 | 23,5 % |
| 4.° | 9 | 8 | 23,5 % |
| **Total** | **34** | **34** | |

Todos los grados quedan por encima del 15 %. 2.° sigue concentrando la mitad de la Física del ciclo.

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
- calentamiento y enfriamiento (2.°) → temperatura → equilibrio térmico (4.°)
- fuerzas a distancia → imanes y polos (3.°)
- medición con instrumentos (2.°) → unidades del SI (3.°)
- gravedad (3.°) → masa y peso (fuera del ciclo)

Hay tres casos en el **mismo grado** donde importa el orden de las unidades:
- En 3.°, el tema de imanes va después de 1.4.
- En 4.°, la temperatura va antes que el equilibrio térmico, dentro del mismo tema.
- En 2.°, el tema 2.6 (calentar y enfriar) debería ir antes que el 1.8 de Química (cambios de estado del agua).

No se adelantan tres conceptos porque tienen bloqueos tardíos:
- La dilatación térmica y el calor como energía necesitan el modelo de partículas (6.°).
- Los electroimanes necesitan el circuito simple (6.°).

## Decisiones abiertas para el MINED
1. **Datos que conviene verificar.** Hay tres conceptos cuyo «primer grado» contradice un tema que ya existe. Los
   tratamos como dudosos y no como hechos:
   - El archivo ubica «Calentamiento y enfriamiento» en 10.°, pero G02-2.6 ya lo trabaja.
   - Ubica «Flotación y hundimiento» en 6.°, pero G02-1.10 (Química) ya la trabaja. Por eso **no** se propone un tema
     nuevo de flotación, aunque los tres países la enseñan en 3.° o 4.°.
   - Ubica «Imanes y polos» en 6.°, pero G03-1.4 está alineado con atracción magnética.
2. **Sonido.** El archivo no trae datos de países sobre tono, intensidad y eco. La división de 2.5 se apoya solo en el
   objetivo TIMSS débil. Conviene confirmarla con los currículos de CO, SG y UY.
3. **Efecto en 5.° a 8.°.** Al introducirse antes, estos temas podrían repetirse más adelante si no se ajustan:
   - el termómetro y las escalas (G06-2.2 y 2.3)
   - el equilibrio térmico (G09-2.6)
   - el SI (G05-1.1 a 1.6)
   - los conductores (G11-6.3)

   Conviene ajustar su profundidad en la propuesta de 5.° a 8.°. ¿Dónde se distingue masa de peso: 4.° o 5.°?
4. **Peso de las Ciencias Físicas frente a TIMSS 4.°.** El balance está levemente por debajo de la meta. Esta propuesta
   reparte mejor los temas dentro de Física, pero no aumenta su número. Subir la proporción exigiría tomar temas de
   otras asignaturas del ciclo, y esa decisión es entre asignaturas.
5. **Carga de 2.°.** Se podría pasar la unidad de movimiento (3.1 a 3.3) a 3.°, junto a las fuerzas, para equilibrar
   los grados. No lo proponemos porque rompería su vínculo con los movimientos de la Tierra (3.4 a 3.8). Queda a
   criterio del MINED.
