# Propuesta de Química, 5.° a 8.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G05-G08.json`.

## En resumen
Proponemos 15 acciones: 6 temas nuevos, 6 fusiones, 1 movimiento (de dos temas) y 2 reformulaciones (`revisar`).
El total del ciclo se mantiene en **66 temas** y no se quita ninguno.

Química no llega tarde en 5.° y 6.°: esos grados ya trabajan estructura atómica y enlaces. Hay dos problemas:
- **Varios temas se enseñan antes que las ideas que los sostienen.**
- **Faltan la energía de las reacciones y la combustión**, que los países de alto desempeño enseñan entre 6.° y 8.°.

## Qué cambió con los países de alto desempeño
- **Inglaterra y Australia respaldan las sustancias puras en 6.°.** Coinciden con Colombia y Uruguay, así que la acción 5
  ya no depende de un solo país.
- **La conservación de la masa se mantiene en 6.°.** Inglaterra la enseña en ese grado. El destino sugerido (8.°) llegaría
  después del balanceo de 7.°.
- **Dos temas nuevos:** reacciones exotérmicas y endotérmicas en 6.° (ENG 6, AU 7) y combustión en 8.° (ENG 6, AU 8, CO 8.5).
  Para pagarlos hacen falta dos fusiones más en 8.°.
- **Se retiran dos acciones de la v1.** La reasignación de disciplina dejó el tema de enzimas (G06 5.2) fuera de Química.
  Además, las fuerzas intermoleculares ya son de Química en 6.° (4.7 y 4.8), y con eso se resuelve la solvatación de 8.°
  sin reformular 4.17.
- **No se adoptan dos candidatos con un solo país de alto desempeño:**
  - La teoría cinética de los gases en 7.° (ENG 6, CO 8.5).
  - Los procesos industriales en 6.°: necesitan estequiometría (8.°), y en 8.° ya existe el tema 4.11.

## Qué cambia y por qué

**1. Las ideas básicas llegan antes que el átomo y las fórmulas (acciones 1, 4 y 5).**
- En 5.°, un tema nuevo sobre el modelo de partículas abre la unidad de estructura atómica.
- Las fórmulas y la interacción iónica (4.5 y 4.6 de 5.°) pasan a la unidad *Interacciones químicas* de 6.°.
- En esa unidad entra un tema nuevo sobre sustancias puras.

**2. La idea general precede a los casos particulares (acciones 6 y 7).**
- El tema 4.1 de 6.° explica qué es un enlace químico antes de los enlaces iónico, metálico y covalente.
- Un experimento en 6.° presenta la conservación de la masa antes del balanceo de ecuaciones de 7.°.

**3. La energía de las reacciones entra en el ciclo (acciones 8 y 9).**
- En 6.°, la clasificación de reacciones suma el criterio energético (exotérmicas y endotérmicas), después de la
  unidad *Calor y temperatura*.
- En 8.°, la combustión une estequiometría, energía y los contaminantes del aire.

**4. Menos abstracción en 5.° y química del aire (acciones 2 y 3).**
- Los números cuánticos (3.10) se reformulan como niveles de energía, porque requieren el modelo mecanocuántico de 10.°.
- Se agrega un tema sobre la composición del aire y los contaminantes (CO 4.5, SG 5, UY 5).

**5. 8.° se aligera con seis fusiones (acciones 10 a 15).** Cada una une dos temas que repiten el mismo contenido:
- propiedades coligativas;
- número de Avogadro;
- tipos de dispersiones;
- unidades físicas de concentración;
- cálculo e interpretación estequiométrica;
- hábito y estructura cristalina.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 5.° | 18 | 18 | 27,3 % |
| 6.° | 10 | 15 | 22,7 % |
| 7.° | 13 | 13 | 19,7 % |
| 8.° | 25 | 20 | 30,3 % |
| **Total** | **66** | **66** | |

Todos los grados superan el 15 %. 6.° sube y 8.° baja.

## Prerrequisitos que se ordenan
Lo comprobó un script de validación. Ningún concepto queda antes que sus prerrequisitos y todos los conceptos están en el
vocabulario.
- La conservación de la masa (6.°) llega antes del balanceo (7.°).
- Las reacciones exotérmicas y endotérmicas (6.°) llegan antes de la combustión (8.°).
- Los números cuánticos salen de 5.°.

En los demás casos, el prerrequisito queda en el **mismo grado**. Al ordenar las unidades hay que respetar este orden:
- modelo de partículas → átomo (5.°)
- sustancias puras → fórmulas y moléculas (6.°)
- enlace químico (4.1) → enlaces iónico, metálico y covalente → fórmulas iónicas (6.°)
- modelos moleculares (4.5) → polaridad (4.6) (6.°)
- unidad *Calor y temperatura* → reacciones exotérmicas y endotérmicas (6.°)
- estequiometría (4.7) → combustión y procesos industriales (4.11) (8.°)

## Decisiones abiertas para el MINED
1. **Datos que conviene verificar.** Algunos conceptos aparecen en 10.° aunque ya se trabajan en el ciclo:
   - *Calor como energía en tránsito*: la unidad 2 de 6.°, de Física, ya lo trabaja.
   - *Geometría molecular*: el tema 4.5 de 6.° ya la trabaja.
   - *Procesos de la industria química*: el tema 4.11 de 8.° ya los trabaja; el archivo los ubica en 11.°.
2. **Modelo de partículas.** Puede ir en 5.° como tema nuevo o adelantando el tema 2.1 de 6.° de Física. La segunda
   opción libera la fusión 10.
3. **Composición del aire.** Hay que coordinar con Ciencias de la Tierra para no duplicarla.
4. **Configuraciones electrónicas (3.11, 5.°).** Conviene limitarlas al modelo de capas.
5. **Polaridad molecular en 6.°.** Con momento dipolar es exigente. ¿Se limita a la polaridad de enlace?
6. **Bachillerato.** Varios temas se repetirían en 10.° y 11.°, que deberían profundizarlos:
   - enlace químico (G10 5.1);
   - sustancias puras (G10 1.13);
   - conservación de la masa (G10 2.1);
   - combustión.
