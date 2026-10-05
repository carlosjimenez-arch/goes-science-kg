# Propuesta de Biología, 5.° a 8.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 20 acciones: 9 movimientos, 4 fusiones, 3 temas nuevos, 1 división y 3 reformulaciones (`revisar`).
El total del ciclo se mantiene en **108 temas** y no se quita ninguno. El cambio central es que **5.° vuelve a tener
Biología**: hoy tiene 2 temas y pasaría a 17, con contenidos que Colombia, Singapur y Uruguay enseñan entre 3.° y 6.°.

## Qué cambia y por qué

**1. 5.° recibe una base de Biología (acciones 1 a 3 y 5 a 10).** Se crean tres unidades en 5.°:
- *La célula y la organización de los seres vivos*:
  - la teoría celular y los niveles de organización (CO 4, SG 5, UY 4);
  - las biomoléculas de los alimentos y las partes básicas de la célula;
  - la difusión y la ósmosis, que se trabajan de forma experimental.
- *Funciones vitales de plantas y animales*:
  - reproducción asexual, fecundación en plantas con flor y germinación (SG 5, UY 3);
  - respiración y circulación (SG 5, UY 5);
  - estructura del sistema digestivo (SG 4, UY 4).
- *Interacciones en los ecosistemas*: competencia, depredación, simbiosis y redes tróficas (CO 3, UY 6).

Son temas que ya existen en 6.°, 7.° u 8.°. Se trasladan con redacción ajustada a la edad.

**2. Cada tema llega después de lo que necesita.**
- La difusión pasa a 5.° porque la necesitan el transporte en plantas y el intercambio de gases. Como la difusión
  supone la membrana celular, la acompañan, en un nivel básico, las biomoléculas y las partes de la célula.
- La propagación asexual va antes que la fecundación en plantas con flor.
- La competencia (4.1) se mueve junto con la simbiosis (4.2).
- Lo que tiene prerrequisitos tardíos se adelanta solo hasta donde puede:
  - El **transporte en plantas** sube de 8.° a 6.°, no a 5.°, porque los tejidos vegetales requieren diferenciación
    celular, mitosis y ADN, que están en 6.°.
  - El intercambio de gases en plantas sube a 6.° porque necesita fotosíntesis y respiración.
  - La digestión química sigue en 8.° porque depende de las enzimas.
  - El tema 6.8 de 6.° se **divide**: la fecundación de plantas con flor baja a 5.° y la división celular se queda en 6.°.

**3. Tres contenidos que hoy llegan tarde entran al ciclo como temas nuevos:**
- La comparación entre célula animal y célula vegetal, en 6.° (hoy solo en 11.°; CO 6, UY 7).
- El papel de los seres vivos en los ciclos del agua, el oxígeno y el carbono, en 7.° (TIMSS B5.3, débil; CO 6, SG 5).
- La homeostasis y la regulación hormonal, en 8.° (hoy en 10.°; CO 8, UY 8).

Se pagan con cuatro fusiones de temas que repiten el mismo contenido. La cuarta fusión paga la división del tema 6.8.
- Funciones de la hoja (8.°).
- Matriz extracelular (6.°).
- Replicación del ADN (7.°).
- Excreción (8.°).

**4. Secuencias que se corrigen sin gastar presupuesto:**
- El tema de biomoléculas, ya en 5.°, incorpora el carbono como base de las moléculas orgánicas (hoy en 11.°).
- 7.11 de 8.° presenta las enzimas como proteínas formadas por aminoácidos (hoy en 10.° y 11.°).
- 6.3 de 5.° presenta los fósiles como evidencia de la evolución, antes de la cladística de 7.°.
- 4.8 de 7.° trabaja explícitamente las pirámides de energía (objetivo B5.2, débil).

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 2 | 17 | 15,7 % |
| 6.° | 33 | 31 | 28,7 % |
| 7.° | 46 | 43 | 39,8 % |
| 8.° | 27 | 17 | 15,7 % |
| **Total** | **108** | **108** | |

Todos los grados quedan por encima del 15 %. 7.° sigue siendo el grado más cargado.

## Prerrequisitos que se ordenan
Un script de validación confirma que ningún concepto queda antes que sus bloqueos. También confirma que se ordenan las
secuencias invertidas del archivo de candidatos:
- carbono → biomoléculas;
- evidencias de la evolución → filogenia;
- aminoácidos → proteínas → enzimas.

En varios casos, el tema y su prerrequisito quedan en el **mismo grado**. Al ordenar las unidades hay que respetar este
orden:
- **5.°:** biomoléculas y partes de la célula → difusión → intercambio de gases.
- **6.°:**
  - ADN → mitosis → diferenciación → tejidos → transporte en plantas;
  - estructuras celulares → célula animal y vegetal;
  - fotosíntesis y respiración → intercambio de gases en hojas.
- **7.°:** ciclo del agua → ciclos biogeoquímicos.
- **8.°:** excreción → homeostasis.

## Verificación con el grafo
El equipo coordinador simuló la versión 1 sobre el grafo de conocimiento:
- Los conceptos que llegan 2 o más grados tarde en el ciclo bajaron de 15 a 4.
- El atraso medio bajó de 2,34 a 1,66 grados.

La simulación también detectó cuatro prerrequisitos nuevos de confianza alta que quedaban después del concepto que
los necesita. La versión 2 los corrige así:

| Problema en v1 | Corrección en v2 |
|---|---|
| Membrana celular (5.°) necesita estructuras celulares básicas (6.°) | El tema de partes básicas de la célula (G06-5.9) pasa a 5.° (acción 2) |
| Membrana celular (5.°) necesita biomoléculas (6.°) | El tema de biomoléculas (G06-5.1) pasa a 5.° con el carbono (acción 2) |
| Mitosis (5.°) necesita ADN y cromosomas (6.°) | La parte del tema 6.8 que baja a 5.° ya no incluye mitosis; la división celular queda en 6.° (acción 6) |
| Tejidos vegetales (5.°) necesitan diferenciación celular (6.°) | Tejidos y transporte en plantas suben de 8.° a 6.°, no a 5.° (acción 4) |

Para mantener 5.° sobre el 15 %, se suma a 5.° el tema de estructuras respiratorias y circulatorias (G08-7.8). La
acción 17 también incorpora los aminoácidos, que son prerrequisito de las proteínas. Nuestra simulación local de la
v2 no encuentra prerrequisitos de confianza alta invertidos dentro del ciclo. El equipo coordinador volverá a correr
la simulación.

## Decisiones abiertas para el MINED
1. **Carga de 5.°:** son 15 temas más, en tres unidades nuevas (numeración provisional 7, 8 y 9). En 6.° se crea la
   unidad provisional 7, sobre estructura y transporte en las plantas. Hay que confirmar el tiempo disponible.
2. **Transporte en plantas:** los países lo enseñan en 3.° a 5.°. Para bajarlo a 5.°, habría que introducir antes la
   diferenciación celular, que hoy depende de mitosis y ADN.
3. **Flujo de energía:** los tres países lo enseñan en 6.°. Proponemos reforzarlo en 7.° para no partir la unidad de
   Ecología. ¿Prefieren pasarlo a 6.°?
4. **Digestión química:** se adelantaría a 5.° solo si las enzimas se introducen antes de 8.°.
5. **Enfermedades (objetivo B6.1):** solo tienen un tema débil en el ciclo y el archivo no trae países que respalden un
   tema nuevo. Hay que revisarlo con la brecha de salud.
6. **Temas de 10.° y 11.°:** al introducirse antes, la célula vegetal (G11 3.3) y las hormonas (G10 3.7 a 3.9) podrían
   repetirse en Bachillerato. Conviene ajustar su profundidad allí.
7. **Selección natural y variación genética:** el grafo ubica «Variación genética en la descendencia» en 11.°, aunque
   el tema G07-2.8 ya la trabaja en 7.°. Hay que verificar el etiquetado antes de mover algo.
