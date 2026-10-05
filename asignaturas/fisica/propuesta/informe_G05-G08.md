# Propuesta de Física, 5.° a 8.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 19 acciones: 2 movimientos, 7 fusiones, 6 temas nuevos, 1 división y 3 reformulaciones (`revisar`).
El total del ciclo se mantiene en **87 temas** y no se quita ninguno. Hay dos cambios centrales:
- **7.° vuelve a tener Física.** Hoy tiene 2 temas y pasaría a 10, con una unidad de trabajo y energía que
  hoy está en 8.°.
- **Entran al ciclo contenidos básicos que hoy llegan en Bachillerato:** la luz, los conductores eléctricos,
  la carga eléctrica, el calor como energía, la gravedad y la eficiencia energética.

## Qué cambia y por qué

**1. Lo básico que los países enseñan en primaria llega a 5.° y 6.° (acciones 1, 2, 4, 6, 8, 10 y 12).**
En 5.° entran cinco contenidos:
- los imanes (CO 2, SG 3, UY 5), que pasan desde 6.°;
- los conductores y aislantes eléctricos (CO 4, SG 5; hoy en 11.°);
- la gravedad y el peso (CO 4, UY 5; hoy en 10.°);
- la flotación (CO 4, SG 3, UY 4), separada del principio de Arquímedes;
- la reflexión de la luz (CO 3, SG 4, UY 4).

En 6.° entran dos temas nuevos:
- la electrización (CO 6, UY 5; hoy en 9.°);
- el equilibrio térmico y el calor como energía en tránsito (SG 4, UY 3 a 5; hoy en 9.° y 10.°).

**2. Se cubre el objetivo TIMSS que faltaba.** *Propiedades de la luz* (P3.1) no tiene hoy ningún tema entre 5.° y
8.°. El tema nuevo de reflexión en 5.° le da cobertura (acción 8).

**3. 8.° se descarga y 7.° recupera Física (acciones 14 a 16).** Ocho temas de 8.° pasan a una unidad nueva
*Trabajo y energía* en 7.°: el diagrama de cuerpo libre (ahora con la fricción), el trabajo, el teorema del trabajo y la
energía, la potencia y la conservación de la energía mecánica. La unidad cierra con un tema nuevo: la conservación
de la energía y la eficiencia (CO 7 y 8, UY 6; hoy en 10.°). Así conecta con los temas 6.5 y 6.6 de 7.°
(combustibles y electricidad). La rotación, el péndulo y el momento lineal siguen en 8.°.

**4. Presupuesto: siete fusiones de temas que repiten un contenido.** Medición (dos fusiones en 5.°), capilaridad y
Bernoulli (6.°), momento lineal, péndulo y potencia (8.°). Cada una paga un tema nuevo o la división del tema de
flotación.

**5. Secuencias que se corrigen sin gastar presupuesto (acciones 17 a 19).** Se reformulan tres temas:
- el 3.2 de 6.° introduce la ley de Ohm antes de calcular resistencias equivalentes (hoy en 11.°);
- el 2.8 de 5.° presenta la suma de fuerzas con flechas antes de la inercia;
- el 1.8 de 8.° incluye la caída libre antes del tiro parabólico (hoy en 10.°).

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 23 | 26 | 29,9 % |
| 6.° | 25 | 24 | 27,6 % |
| 7.° | 2 | 10 | 11,5 % |
| 8.° | 37 | 27 | 31,0 % |
| **Total** | **87** | **87** | |

7.° sigue por debajo del 15 % (13 temas), pero pasa de 2 a 10. No proponemos más por dos motivos. Primero, 7.° ya es
el grado con más temas de Ciencias si se suman las cuatro asignaturas. Segundo, lo que queda en 8.° (péndulo,
oscilaciones, ondas, rotación) depende del movimiento armónico simple o de los vectores, que se enseñan en 8.°.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación:
- el total del ciclo se conserva;
- los ids existen;
- ningún tema queda antes que un prerrequisito que antes estaba en orden.

De las 14 secuencias invertidas de Física en el ciclo, se corrigen 8:
- imanes → campo magnético terrestre;
- conductores → circuito;
- carga → corriente;
- ley de Ohm → resistencia equivalente;
- fuerzas intermoleculares → capilaridad;
- calor → calor específico;
- fricción → fuerzas mecánicas;
- caída libre → proyectiles.

Una más se reduce: el diagrama de cuerpo libre queda a dos grados de la inercia, antes eran tres.

Hay casos en que el tema y su prerrequisito quedan en el **mismo grado**. Al ordenar las unidades hay que respetar
este orden:
- en 5.°: imanes antes de 5.9;
- en 6.°: temperatura y modelo de partículas → equilibrio térmico; electrización → multímetro; presión (1.3) →
  empuje (1.2); fuerzas intermoleculares (4.7 y 4.8) → capilaridad;
- en 7.°: diagrama de cuerpo libre → trabajo → potencia → conservación.

## Decisiones abiertas para el MINED
1. **Bloque de calor:** los países enseñan temperatura, dilatación y calor en 3.° y 4.°. Proponemos dejar la unidad
   en 6.° y sumar el equilibrio térmico. ¿Prefieren pasar la unidad completa a 5.°? Ese grado quedaría con 33 temas.
2. **Carga de 7.°:** ¿se acepta llegar a 10 temas, o se suben más temas de 8.°, como los de ondas?
3. **Datos que conviene verificar:**
   - El archivo de candidatos ubica la presión hidrostática en 9.° y la conservación de la energía mecánica en 8.°.
     Sin embargo, los temas 6.°-1.3 y 5.°-2.15 ya las trabajan.
   - «Calentamiento y enfriamiento» y «Disipación de energía» aparecen como «primera vez en 10.°», pero hay temas
     de 2.° a 4.° que las tocan.
   - Los temas 4.7 y 4.8 de 6.° tratan las fuerzas intermoleculares, aunque no están etiquetados con ese concepto.

   Estas acciones no se apoyan en esos datos. Hay que corregir el etiquetado.
4. **Secuencias que siguen abiertas:**
   - *Ondas estacionarias* (8.°) necesita *superposición*, que llega en 11.°.
   - *Efecto invernadero* (7.°) y *Big Bang* (5.°) necesitan las ondas electromagnéticas y el efecto Doppler.
     Ambos temas pertenecen a Ciencias de la Tierra y del Espacio. Proponemos resolverlo en esa asignatura o con un tema
     sobre el espectro electromagnético al final de la unidad de ondas de 8.°, que este archivo no puede pagar.
   - *Densidad* (9.°) es prerrequisito de la presión (6.°).
5. **Repeticiones en 9.° a 11.°:** al adelantarse, varios temas se repetirían más adelante. Conviene ajustar su
   profundidad:
   - la carga eléctrica (G09 6.1);
   - el equilibrio térmico (G09 2.6);
   - el calor (G10 12.6);
   - la gravitación (G10 5.7);
   - los conductores (G11 6.3).
