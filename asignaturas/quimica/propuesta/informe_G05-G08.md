# Propuesta de Química, 5.° a 8.° (borrador)

Versión `propuesta-v3`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 19 acciones: 8 temas nuevos, 8 fusiones, 1 movimiento (de dos temas) y 2 reformulaciones (`revisar`).
El total del ciclo se mantiene en **66 temas** y no se quita ninguno.

Química no llega tarde en 5.° y 6.°: esos grados ya trabajan estructura atómica y enlaces. Hay dos problemas:
- **Varios temas se enseñan antes que las ideas que los sostienen.**
- **Faltan la química de las reacciones que los países de alto desempeño enseñan entre 6.° y 8.°:** energía de las
  reacciones, oxidación y reducción, ácidos con indicadores y neutralización, y materiales.

## Qué cambió con Japón
- **Japón refuerza lo que ya se proponía.** Se suma a las sustancias puras (JP 7), a la composición del aire (JP 5,
  ahora con dos países de alto desempeño) y a la conservación de la masa (JP 2, desde primaria).
- **Las reacciones exotérmicas y endotérmicas pasan de 6.° a 7.°.** Con Japón, tres países de alto desempeño
  (AU 7, ENG 6, JP 7) las enseñan y la mediana es 7.°. Ahora cierran la unidad de reacciones de 7.°.
- **Tres temas nuevos con dos países de alto desempeño cada uno:**
  - oxidación y reducción en 7.° (ENG 6, JP 7);
  - indicadores y neutralización en 7.° (ENG 6 y JP 5; ENG 6 y JP 8);
  - metales, cerámicas y materiales compuestos en 8.° (ENG 6, JP 8).
- **Se retira el tema de combustión en 8.°.** Ya no es candidato: el grafo registra la combustión en 7.° (tema 6.5 de
  Física), así que dejó de llegar tarde frente a la mediana. Ver decisión abierta 2.
- **Siguen sin adoptarse los candidatos con un solo país de alto desempeño:**
  - electrólisis (JP 8, UY 5), que además requiere oxidación y reducción y electrolitos;
  - teoría cinética de los gases (ENG 6, CO 8.5).

## Qué cambia y por qué

**1. Las ideas básicas llegan antes que el átomo y las fórmulas (acciones 1, 4 y 5).**
- En 5.°, un tema nuevo sobre el modelo de partículas abre la unidad de estructura atómica.
- Las fórmulas y la interacción iónica (4.5 y 4.6 de 5.°) pasan a la unidad *Interacciones químicas* de 6.°.
- En esa unidad entra un tema nuevo sobre sustancias puras (AU 6, ENG 6, JP 7).

**2. La idea general precede a los casos particulares (acciones 6 y 7).**
- El tema 4.1 de 6.° explica qué es un enlace químico antes de los enlaces iónico, metálico y covalente.
- Un experimento en 6.° presenta la conservación de la masa antes del balanceo de ecuaciones de 7.°.

**3. 7.° pasa de nombrar compuestos a entender reacciones (acciones 8, 9 y 10).**
- Oxidación y reducción, a nivel cualitativo, después de la formación de óxidos.
- Reacciones exotérmicas y endotérmicas al cierre de la unidad 1.
- Ácidos y bases con indicadores y neutralización, después de la medición del pH (5.9).

**4. Menos abstracción en 5.° y química del aire y de los materiales (acciones 2, 3 y 11).**
- Los números cuánticos (3.10) se reformulan como niveles de energía, porque requieren el modelo mecanocuántico de 10.°.
- Se agrega un tema sobre la composición del aire y los contaminantes (CO 4.5, JP 5, SG 5, UY 5).
- En 8.°, después de los sólidos cristalinos, un tema relaciona la estructura de metales, cerámicas y materiales
  compuestos con sus propiedades.

**5. Ocho fusiones pagan los temas nuevos (acciones 12 a 19).** Cada una une dos temas que repiten el mismo contenido:
- en 8.°: propiedades coligativas; número de Avogadro; tipos de dispersiones; unidades físicas de concentración;
  unidades químicas de concentración; cálculo e interpretación estequiométrica; hábito y estructura cristalina;
- en 7.°: nomenclatura de hidróxidos, oxácidos y oxisales.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 18 | 18 | 27,3 % |
| 6.° | 10 | 14 | 21,2 % |
| 7.° | 13 | 15 | 22,7 % |
| 8.° | 25 | 19 | 28,8 % |
| **Total** | **66** | **66** | |

Todos los grados superan el 15 %. 6.° y 7.° suben; 8.° baja.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Ningún concepto queda antes que sus prerrequisitos y todos los conceptos están en el
vocabulario.
- La conservación de la masa (6.°) llega antes del balanceo (7.°).
- Las sustancias puras (6.°) llegan después del modelo de partículas (5.°).
- Los números cuánticos salen de 5.°.

En los demás casos, el prerrequisito queda en el **mismo grado**. Al ordenar las unidades hay que respetar este orden:
- modelo de partículas → átomo (5.°)
- sustancias puras → fórmulas y moléculas (6.°)
- enlace químico (4.1) → enlaces iónico, metálico y covalente → fórmulas iónicas (6.°)
- ácidos y bases (1.7) y balanceo (unidad 1) → escala de pH (5.9) → indicadores y neutralización (7.°)
- unidad 1 de reacciones → reacciones exotérmicas y endotérmicas (7.°), con el calor visto en Física de 6.°
- sólidos cristalinos (5.4 y 5.5) → materiales (8.°)

## Decisiones abiertas para el MINED
1. **Datos que conviene verificar.** Algunos conceptos aparecen en 10.° aunque ya se trabajan antes:
   - *Calor como energía en tránsito*: la unidad 2 de 6.°, de Física, ya lo trabaja.
   - *Catalizadores*: el tema de enzimas de 6.° (Biología 5.2) los usa sin energía de activación (10.°). Conviene
     tratarlos solo de forma cualitativa.
2. **Combustión.** Solo se trabaja como reacción química en 11.°. En 7.° aparece en un tema de Física (dispositivos de
   combustión), y la acción 9 la usa como ejemplo de oxidación. ¿Basta, o se quiere un tema propio en 8.°?
3. **Modelo de partículas.** Puede ir en 5.° como tema nuevo o adelantando el tema 2.1 de 6.° de Física. La segunda
   opción libera la fusión 12.
4. **Composición del aire.** Hay que coordinar con Ciencias de la Tierra para no duplicarla.
5. **Polaridad molecular en 6.°.** Con momento dipolar es exigente. ¿Se limita a la polaridad de enlace?
6. **Bachillerato y 9.°.** Varios temas se repetirían más adelante y deberían profundizarse, no repetirse:
   - indicadores naturales (G09 3.10);
   - enlace químico (G10 5.1);
   - conservación de la masa (G10 2.1);
   - oxidación y reducción (G11 6.1 a 6.3);
   - materiales (G11, unidad 1).
