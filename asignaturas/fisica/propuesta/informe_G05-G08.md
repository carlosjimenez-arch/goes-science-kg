# Propuesta de Física, 5.° a 8.° (borrador, v3)

Versión `propuesta-v3`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

Esta versión usa el archivo de candidatos regenerado, que suma a **Japón (JP)** como país de referencia. Los países
de alto desempeño del grafo son ahora Singapur (SG), Inglaterra (ENG), Australia (AU) y Japón.

## En resumen
Proponemos 20 acciones: 3 movimientos, 7 fusiones, 7 temas nuevos y 3 reformulaciones (`revisar`).
El total del ciclo se mantiene en **86 temas** y no se quita ninguno. Hay dos cambios centrales:
- **7.° vuelve a tener Física.** Hoy tiene 2 temas y pasaría a 16, con dos unidades: *Trabajo y energía* y
  *Ondas, sonido y luz*.
- **Entran al ciclo contenidos básicos que hoy llegan en Bachillerato:** la luz (reflexión, espectro y
  refracción), los conductores eléctricos, la carga eléctrica, la ley de Ohm, la fricción, el calor como energía,
  la ventaja mecánica y la conservación de la energía.

## Qué cambió con Japón
- **La refracción y las lentes entran en 7.°** (tema nuevo, acción 16). Con Japón, tres países de alto desempeño
  enseñan la refracción entre 4.° y 6.° (AU 4, ENG 6, JP 6) y dos, las lentes (ENG 6, JP 6). Su bloqueo, la rapidez
  de la luz, ya llega en 7.° con el tema del espectro. En v2 era una decisión abierta.
- **Sale el tema nuevo de gravitación.** Japón no la respalda y queda un solo país de alto desempeño (ENG 6). Su
  fusión de pago (medición, 5.°) ahora paga la refracción. La gravedad se trata, sin costo, como causa de la caída
  libre en el tema 1.8 de 8.° (decisión abierta 4).
- **Tres contenidos se suman a temas que ya cambiaban, sin gastar presupuesto:** el circuito simple, junto a los
  conductores en 5.° (AU, ENG, JP, SG); los materiales magnéticos, junto a los imanes en 5.° (ENG 2, JP 2, SG 3); y
  la ventaja mecánica, en el tema de máquinas simples de 7.° (ENG 3, JP 5).
- **Más respaldo para lo que ya proponíamos:** imanes, conductores y reflexión (JP 2), sonido como onda (JP 6),
  diagrama de cuerpo libre (JP 6), carga eléctrica y ley de Ohm (JP 7). La ley de Ohm pasa a ser candidata propia
  (ENG 6, JP 7).
- **Evidencia que se retira:** «Disipación de energía» y «Calentamiento y enfriamiento» ya no son candidatos a
  moverse. Los temas de conservación de la energía (7.°) y equilibrio térmico (6.°) se mantienen con el resto de su
  evidencia.

## Qué cambia y por qué

**1. Lo básico de primaria llega a 5.° y 6.° (acciones 1, 2, 4, 6, 8 y 19).**
En 5.° entran los imanes y los materiales magnéticos (desde 6.°), el circuito simple con los conductores y aislantes
(hoy en 11.°), la reflexión de la luz con espejos planos y la fricción. En 6.° entran la electrización (ENG 6, JP 7;
hoy en 9.°) y el equilibrio térmico con el calor como energía en tránsito (hoy en 9.° y 10.°).

**2. 8.° se descarga y 7.° recupera Física (acciones 10 a 16).** Se crean dos unidades en 7.°:
- *Trabajo y energía*: el diagrama de cuerpo libre, el trabajo con máquinas simples y ventaja mecánica, la potencia
  y la conservación de la energía mecánica pasan desde 8.°. Cierra con un tema nuevo sobre conservación de la
  energía y eficiencia (AU 8, CO 8,5, ENG 6, UY 6; hoy en 10.°).
- *Ondas, sonido y luz*: los tipos de onda, sus gráficas y el sonido como onda pasan desde 8.°. Siguen dos temas
  nuevos: el espectro electromagnético (CO 8,5, ENG 6, UY 6) y la refracción con lentes (AU, ENG, JP).

En 8.° siguen la cinemática, las leyes de Newton, el momento lineal, la rotación, el péndulo y el tono y las ondas
estacionarias.

**3. Presupuesto: siete fusiones de temas que repiten un contenido.** Medición (dos fusiones en 5.°), capilaridad
(6.°), momento lineal, péndulo, potencia y rotación (8.°). Cada una paga uno de los siete temas nuevos.

**4. Secuencias que se corrigen sin gastar presupuesto (acciones 18 a 20).** Se reformulan tres temas:
- el 3.2 de 6.° introduce la ley de Ohm (hoy en 11.°) antes de calcular resistencias equivalentes;
- el 2.8 de 5.° presenta con flechas la fuerza neta y la fricción antes de la inercia;
- el 1.8 de 8.° incluye la caída libre y la gravedad como su causa (hoy en 10.°) antes del tiro parabólico.

## Distribución por grado

| Grado | Antes | v2 | v3 | % del ciclo (v3) |
|---|---|---|---|---|
| 5.° | 23 | 25 | 24 | 27,9 % |
| 6.° | 24 | 24 | 24 | 27,9 % |
| 7.° | 2 | 15 | 16 | 18,6 % |
| 8.° | 37 | 22 | 22 | 25,6 % |
| **Total** | **86** | **86** | **86** | |

Todos los grados quedan por encima del 15 %.

## Prerrequisitos que se ordenan
Un script de validación comprobó que el total del ciclo se conserva, que los ids de los temas afectados existen y
que ningún tema queda antes que un prerrequisito que antes estaba en orden. De las secuencias invertidas de Física
en el ciclo se corrigen 7: imanes → campo magnético; conductores → circuito; carga → corriente; ley de Ohm →
resistencia equivalente; calor → calor específico; fricción → fuerzas mecánicas; caída libre → proyectiles.
El espectro también ordena el efecto invernadero de 7.°.

Cuando un tema y su prerrequisito quedan en el **mismo grado**, al ordenar las unidades hay que respetar:
- en 5.°: imanes antes del tema actual 5.9; torque (2.11) sigue en 5.°, antes de la ventaja mecánica de 7.°;
- en 6.°: temperatura y modelo de partículas → equilibrio térmico; electrización → multímetro;
- en 7.°: diagrama de cuerpo libre → trabajo → potencia → conservación; tipos de onda → longitud de onda →
  espectro (rapidez de la luz) → refracción y lentes.

## Decisiones abiertas para el MINED
1. **Bloque de calor y electricidad en 5.°:** con Japón, la dilatación (JP 3, SG 4, UY 3) y la corriente y el
   voltaje (ENG 4, JP 3) también se enseñan antes. Proponemos dejar ambas unidades en 6.°; pasarlas a 5.° dejaría
   ese grado con más de 30 temas.
2. **Fuerzas y diagrama de cuerpo libre en 6.° o en 7.°:** Australia, Inglaterra y Japón lo enseñan en 6.°. Pasar
   el tema 1.6 de 8.° a 6.° deja a 7.° con 15 temas (17 %); costaría una acción más.
3. **Candidatos que no se incluyen:**
   - la potencia eléctrica y el efecto Joule (CO 5, ENG 6, JP 7) y el motor eléctrico (ENG 6, JP 7), hoy en 9.°;
     podrían entrar en 6.° y 7.° con otra fusión;
   - el equilibrio estático (AU 6, ENG 6, JP 6), que necesita los vectores de 8.°;
   - el sonido podría bajar a 6.° (destino sugerido), pero sus bloqueos viajan juntos a 7.°.
4. **Gravitación:** la propuesta solo nombra la gravedad como causa de la caída libre (8.°). Si el MINED quiere
   adelantar la gravitación (CO 4,5, ENG 6, UY 5), puede reformular el tema 2.14 de 5.° sin costo.
5. **Secuencias que siguen abiertas:** *ondas estacionarias* (8.°) necesita la *superposición* (11.°); *Big Bang*
   (5.°, Ciencias de la Tierra y del Espacio) necesita el efecto Doppler (11.°).
6. **Coordinación con Química:** la capilaridad (6.°) se explica con las fuerzas entre partículas de los temas 4.7
   y 4.8 de Química de 6.°, que deben ir antes.
7. **Repeticiones en 9.° a 11.°:** conviene ajustar la profundidad de la carga eléctrica (G09 6.1), el equilibrio
   térmico (G09 2.6), el calor (G10 12.6), la fricción (G10 5.9), la refracción (G10 16.8), las ondas
   electromagnéticas (G10 16.1), los conductores (G11 6.3) y la ley de Ohm (G11 9.2).
