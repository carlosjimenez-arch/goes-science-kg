# Propuesta de Biología, 2.° a 4.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G02-G04.json`.

## En resumen
Proponemos 14 acciones: 3 temas nuevos, 3 fusiones, 2 movimientos y 6 reformulaciones (`revisar`).
El total del ciclo se mantiene en **99 temas** y no se quita ninguno.

El total pasó de 98 a 99 temas por la reasignación de disciplinas:
- sale G03-2.14 (atmósfera), que ahora es de Ciencias de la Tierra;
- entran G03-6.8 (alimentos transformados por microorganismos) y G04-2.12 (tipos de cultivos).

Biología ya pesa más de lo esperado en el ciclo (52 % de los temas de Ciencias; TIMSS indica 45 %). Por eso no se
agregan temas: los tres nuevos se pagan con tres fusiones. El cambio central es cubrir el único objetivo sin
ningún tema, **T4_27-B2.2 Herencia y estrategias de reproducción**.

## Qué cambia y por qué

**1. Se cubren la reproducción y la herencia (acciones 1 a 6).**
- *3.°, Las plantas:* tema nuevo sobre polinización, semillas, frutos y propagación por esquejes. Inglaterra (2.°),
  Uruguay (3.°) y Singapur (5.°) lo enseñan antes; El Salvador, en 6.°. El tema introduce la reproducción
  sexual y asexual, que es su prerrequisito.
- *3.°, Los animales:* tema nuevo sobre estrategias de reproducción: huevos o crías vivas, número de crías y
  cuidado parental.
- *4.°, Cuerpo humano:* tema nuevo sobre los rasgos heredados. Hoy la herencia aparece en 10.°; Colombia la
  enseña en 2.°, Inglaterra en 4.° y Singapur en 5.°.
- Se pagan con tres fusiones de temas que repiten contenido:
  - en 3.°, vertebrados (5.12 y 5.13);
  - en 4.°, medidas antropométricas (2.9 y 2.10);
  - en 4.°, requerimientos y menús (2.4 y 2.7).

**2. Dos temas cambian de grado (acciones 7 y 8).**
- **Los sentidos bajan de 4.° a 2.°** (CO 2, ENG 2, UY 3). Van junto a la respuesta a estímulos (1.9) y a la
  relación entre las partes del cuerpo de un animal y su función (4.8, reformulado). Esto también alivia 4.°.
- **Las vacunas suben de 2.° a 3.°.** Pasan a la unidad de microorganismos, después de infección y patógenos.

**3. Se ordenan secuencias sin gastar presupuesto (acciones 9 a 13).**
- **2.° (4.8):** se hace explícita la relación entre la estructura del cuerpo animal y su función. Hoy no tiene
  grado en la malla y es prerrequisito de los sentidos y del sistema locomotor.
- **3.° (5.3):** el tema de taxismos se amplía a conductas que ayudan a sobrevivir. Hoy las adaptaciones
  conductuales aparecen en 11.° (CO 2, AU 4, SG 6).
- **4.°, unidad 3 (se reordena):**
  1. primero la cadena trófica;
  2. luego las interacciones, con la competencia (CO 3, ENG 6) y la depredación (ENG 2, CO 3) explícitas;
  3. al final el nicho, como «papel de la especie».
- **4.° (3.3):** se precisa como organización *ecológica*, de modo que no exige la célula.
- **3.° (6.7 y 6.8):** degradación y alimentos fermentados se quedan en lo observable. Los descomponedores se
  nombran en 4.° y el mecanismo de la fermentación sigue en Bachillerato.

**4. Temas señalados por si se quiere aligerar Biología (acción 14).** Hay dos grupos de temas que podrían
consolidarse:
- seis temas de invertebrados en 3.° (5.6 a 5.11);
- tres temas de tropismos y nastias (4.7 a 4.9).

## Qué cambió con los países de alto desempeño
- **Reproducción de plantas con flor:** Inglaterra (2.°) se suma a Uruguay y Singapur. Con ese respaldo, en v2
  pasa a ser tema nuevo en 3.° y deja de esperar a 5.°.
- **Órganos de los sentidos:** Inglaterra los enseña en 2.°. Pasa a ser candidato y se mueve de 4.° a 2.°.
- **Herencia de rasgos y adaptaciones conductuales:** Inglaterra (4.°) y Australia (4.°) confirman las acciones de v1.
  Herencia ya no depende solo de Colombia.
- **Competencia y depredación:** Inglaterra las respalda. Se nombran de forma explícita en 4.° y la unidad se reordena
  para que la cadena trófica vaya antes que la depredación.
- **Fósiles y evidencias de la evolución** (ENG 4, CO 2): **no** se agrega tema. La malla ya trabaja la formación de
  fósiles en 5.° (Ciencias de la Tierra, U6, 6.2 a 6.4), y la propuesta de 5.° a 8.° los presenta allí como
  evidencia de la evolución.
- **Digestión química** (ENG, SG y UY en 4.°) sigue bloqueada: necesita las enzimas, que llegan en 6.°.
  **Transporte en plantas** (ENG 2) también: necesita difusión y tejidos vegetales; se resuelve en 5.°.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 2.° | 27 | 27 | 27,3 % |
| 3.° | 32 | 34 | 34,3 % |
| 4.° | 40 | 38 | 38,4 % |
| **Total** | **99** | **99** | |

Todos los grados quedan por encima del 15 %. 4.° deja de crecer y baja dos temas.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación.

**Quedan en orden:**
- estructura y función del cuerpo animal (2.°) → sentidos (2.°) y sistema locomotor (4.°)
- reproducción sexual y asexual → plantas con flor (3.°, mismo tema)
- cadena alimentaria → depredación y descomponedores (4.°)
- competencia → relaciones intraespecíficas y nicho (4.°)
- niveles de organización ecológica (3.3) → relaciones intraespecíficas (4.°)

Cuando el tema y su prerrequisito quedan en el mismo grado, al ordenar las unidades hay que respetar este orden:
- en 2.°, 1.9 y 4.8 antes que los sentidos;
- en 3.°, la unidad 4 antes que la 5;
- en 4.°, la cadena trófica antes que las interacciones.

**Quedan pendientes dos secuencias.** Las dos dependen de cómo están etiquetados los conceptos (decisiones 2 y 3):
- vacunas (3.°) → sistema inmunitario (10.°)
- niveles de organización (4.°) → la célula (6.°; 5.° en la propuesta de 5.° a 8.°)

## Decisiones abiertas para el MINED
1. **Peso de Biología:** está siete puntos por encima de TIMSS. ¿Se consolidan los temas de la acción 14 para pasar
   horas a otras disciplinas?
2. **Vacunas:** el grafo exige el sistema inmunitario (10.°) antes de las vacunas. En 3.° proponemos solo la idea de
   «defensas del cuerpo». Hay dos opciones:
   - aceptar este nivel introductorio;
   - introducir las defensas del cuerpo como concepto propio en primaria.
3. **Datos que conviene verificar:**
   - Los candidatos ubican la competencia y la simbiosis en 7.°, pero G04-3.6 ya las trabaja.
   - G04-3.3 está etiquetado con un concepto que exige la célula.
   - «Fósiles y registro fósil» figura en 10.°, aunque 5.° ya trabaja la formación de fósiles.
   - G03-6.8 está etiquetado como «fermentación y respiración anaerobia», un concepto de Bachillerato.
4. **Coordinación con la propuesta de 5.° a 8.°:**
   - La fecundación de plantas con flor que esa propuesta lleva a 5.° pasa a ser una profundización del tema
     nuevo de 3.°.
   - La célula sigue en 5.° (Colombia y Uruguay la enseñan en 4.°).
5. **Herencia en Bachillerato:** conviene ajustar la profundidad de 10.° para que no repita el tema nuevo de 4.°.
