# Propuesta de Física, 5.° a 8.° (borrador, v2)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

Esta versión usa el archivo de candidatos regenerado. Ese archivo:
- suma a Inglaterra (ENG) y Australia (AU) como países de alto desempeño;
- pasa los temas 4.7 y 4.8 de 6.° (fuerzas intermoleculares) a Química.

## En resumen
Proponemos 20 acciones: 3 movimientos, 7 fusiones, 7 temas nuevos y 3 reformulaciones (`revisar`).
El total del ciclo se mantiene en **86 temas** y no se quita ninguno. Hay dos cambios centrales:
- **7.° vuelve a tener Física.** Hoy tiene 2 temas y pasaría a 15, con dos unidades que hoy están en 8.°:
  *Trabajo y energía* y *Ondas, sonido y luz*.
- **Entran al ciclo contenidos básicos que hoy llegan en Bachillerato:** la luz, los conductores eléctricos,
  la carga eléctrica, la fricción, el calor como energía, la gravedad, la eficiencia y el espectro electromagnético.

## Qué cambió con los países de alto desempeño
- **Más respaldo para lo que ya proponíamos.** Inglaterra, Australia y Singapur enseñan en primaria los imanes,
  los conductores eléctricos, la reflexión de la luz y el equilibrio térmico. Esos cambios se mantienen.
- **La fricción entra en 5.°** (AU 3, ENG 2, SG 6; hoy en 10.°). Se agrega al tema 2.8 de 5.° sin gastar presupuesto.
- **Se adelantan las ondas y la luz a 7.°.** Inglaterra y Uruguay enseñan en 6.° el sonido como onda y el
  espectro electromagnético. Se suben a 7.° las bases de las ondas y se crea un tema sobre el espectro. Ese tema
  corrige la secuencia del efecto invernadero (7.°) y refuerza el objetivo P3.1.
- **Espejos planos** (ENG 6, UY 4): se integran en el tema nuevo de reflexión de 5.°.
- **Se retira la división del tema de flotación** y la fusión de Bernoulli que la pagaba. Con los nuevos países, la
  flotación ya no es candidata a moverse.
- **Fuerzas, diagrama de cuerpo libre y trabajo:** Inglaterra, Australia y Singapur los enseñan en 6.°. Los dejamos
  en 7.° para equilibrar los grados (decisión abierta 2).

## Qué cambia y por qué

**1. Lo básico de primaria llega a 5.° y 6.° (acciones 1, 2, 4, 6, 8, 10 y 16).**
En 5.° entran:
- los imanes, que pasan desde 6.°;
- los conductores y aislantes eléctricos (hoy en 11.°);
- la gravedad y el peso (CO 4,5, ENG 6, UY 5; hoy en 10.°);
- la reflexión de la luz con espejos planos;
- la fricción.

En 6.° entran dos temas nuevos:
- la electrización (CO 6, ENG 6, UY 5; hoy en 9.°);
- el equilibrio térmico y el calor como energía en tránsito (hoy en 9.° y 10.°).

**2. 8.° se descarga y 7.° recupera Física (acciones 12 a 14 y 18 a 20).** Se crean dos unidades en 7.°:
- *Trabajo y energía*: el diagrama de cuerpo libre, el trabajo, la potencia y la conservación de la energía
  mecánica pasan desde 8.°. Cierra con un tema nuevo sobre conservación de la energía y eficiencia (AU 8, CO 8,5,
  ENG 6, UY 6; hoy en 10.°).
- *Ondas, sonido y luz*: los tipos de onda, sus gráficas y el sonido como onda pasan desde 8.°. Cierra con un tema
  nuevo sobre el espectro electromagnético (CO 8,5, ENG 6, UY 6; hoy en 10.°).

En 8.° siguen la cinemática, las leyes de Newton, el momento lineal, la rotación, el péndulo y el tono y las ondas
estacionarias.

**3. Presupuesto: siete fusiones de temas que repiten un contenido.** Medición (dos fusiones en 5.°), capilaridad
(6.°), momento lineal, péndulo, potencia y rotación (8.°). Cada una paga uno de los siete temas nuevos.

**4. Secuencias que se corrigen sin gastar presupuesto (acciones 15 a 17).** Se reformulan tres temas:
- el 3.2 de 6.° introduce la ley de Ohm (hoy en 11.°) antes de calcular resistencias equivalentes;
- el 2.8 de 5.° presenta con flechas la fuerza neta y la fricción antes de la inercia;
- el 1.8 de 8.° incluye la caída libre (hoy en 10.°) antes del tiro parabólico.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 23 | 25 | 29,1 % |
| 6.° | 24 | 24 | 27,9 % |
| 7.° | 2 | 15 | 17,4 % |
| 8.° | 37 | 22 | 25,6 % |
| **Total** | **86** | **86** | |

Todos los grados quedan por encima del 15 %.

## Prerrequisitos que se ordenan
Un script de validación comprobó tres cosas:
- el total del ciclo se conserva;
- los ids de los temas afectados existen;
- ningún tema queda antes que un prerrequisito que antes estaba en orden.

De las secuencias invertidas de Física en el ciclo, se corrigen 7:
- imanes → campo magnético;
- conductores → circuito;
- carga → corriente;
- ley de Ohm → resistencia equivalente;
- calor → calor específico;
- fricción → fuerzas mecánicas;
- caída libre → proyectiles.

El tema nuevo del espectro también ordena el efecto invernadero de 7.°. El diagrama de cuerpo libre queda a dos
grados de la inercia; antes estaba a tres.

Hay casos en que el tema y su prerrequisito quedan en el **mismo grado**. Al ordenar las unidades hay que respetar
este orden:
- en 5.°: imanes antes del tema actual 5.9;
- en 6.°: temperatura y modelo de partículas → equilibrio térmico; electrización → multímetro;
- en 7.°: diagrama de cuerpo libre → trabajo → potencia → conservación, y tipos de onda → longitud de onda →
  espectro.

## Decisiones abiertas para el MINED
1. **Bloque de calor:** Australia, Singapur y Uruguay enseñan temperatura y calor entre 2.° y 4.°. Proponemos dejar la
   unidad en 6.° y sumar el equilibrio térmico. ¿Prefieren pasarla completa a 5.°? Ese grado quedaría con 32 temas.
2. **Fuerzas y trabajo en 6.° o en 7.°:** Inglaterra, Australia y Singapur los enseñan en 6.°. Si se llevan a 6.°,
   7.° vuelve a quedar por debajo del 15 %.
3. **Candidatos que no se mueven por sus bloqueos:**
   - la refracción y las lentes, que necesitan la rapidez de la luz, hoy en 11.°; podrían seguir al tema del
     espectro en 7.°;
   - la potencia eléctrica y el efecto Joule, que necesitan la disipación, que pasa a 7.°;
   - el equilibrio estático, que necesita los vectores de 8.°;
   - la ventaja mecánica;
   - los materiales magnéticos (tema 3.8, que también necesita los circuitos de 6.°).
4. **Datos que conviene verificar:**
   - El archivo de candidatos ubica la presión hidrostática en 9.° y la conservación de la energía mecánica en 8.°,
     pero los temas 6.°-1.3 y 5.°-2.15 ya las trabajan.
   - «Calentamiento y enfriamiento» y «Disipación» aparecen como «primera vez en 10.°», pero hay temas de 2.° a 4.°
     que los tocan.
5. **Secuencias que siguen abiertas:**
   - *Ondas estacionarias* (8.°) necesita la *superposición*, que llega en 11.°.
   - *Big Bang* (5.°, Ciencias de la Tierra y del Espacio) necesita el efecto Doppler.
6. **Coordinación con Química:** la capilaridad (6.°) se explica con las fuerzas entre partículas que Química trabaja
   en los temas 4.7 y 4.8 de 6.°. Esos temas deben ir antes.
7. **Repeticiones en 9.° a 11.°:** al adelantarse, varios temas se repetirían más adelante. Conviene ajustar su
   profundidad:
   - la carga eléctrica (G09 6.1);
   - el equilibrio térmico (G09 2.6);
   - el calor (G10 12.6);
   - la gravitación (G10 5.7);
   - la fricción (G10 5.9);
   - las ondas electromagnéticas (G10 16.1);
   - los conductores (G11 6.3).
