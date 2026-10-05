# Propuesta de Química, 10.° y 11.° (borrador)

Versión `propuesta-v1`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G10-G11.json`. Marco pivote: ACARA Senior Secondary
Chemistry (AUSS), unidades 1 y 2 ≈ 10.° y unidades 3 y 4 ≈ 11.°.

## En resumen
Proponemos 18 acciones: 5 temas nuevos, 5 fusiones, 1 movimiento y 7 reformulaciones (`revisar`).
El total del ciclo se mantiene en **209 temas** y no se quita ninguno. Bachillerato ya cubre el 87 % de los
objetivos de contenido de ACARA y sigue su misma secuencia. Por eso la propuesta es acotada:
- corrige tres secuencias invertidas;
- cubre con temas nuevos los faltantes de ACARA más importantes;
- paga esos temas con fusiones de contenidos que se repiten.

Para este ciclo, el archivo de candidatos no trae países de referencia. La evidencia son los objetivos AUSS sin
cobertura o débiles y los prerrequisitos del grafo.

## Qué cambia y por qué

**1. La oxidación-reducción llega antes de usarse (acciones 1, 2 y 6).**
- La unidad 13 de 10.° habla de agentes oxidantes (13.3 y 13.7) y de electrólisis (13.8). Sin embargo, la
  oxidación-reducción se define recién en 11.°. El tema 6.1 de 11.° baja a la unidad 9 de 10.° (*Reacciones
  químicas*) como 9.5: transferencia de electrones, números de oxidación y agentes oxidante y reductor.
- En 11.°, la unidad de Electroquímica abre con el balanceo por ion-electrón. Para eso se unen 6.2 y 6.3, que
  repetían ese contenido.
- El tema 2.6 de 10.° deja el reconocimiento de isómeros para 11.° (3.14), porque supone las cadenas de
  hidrocarburos. Conserva el cálculo de fórmulas empírica y molecular.

**2. Cinco faltantes de ACARA entran como temas nuevos (acciones 3, 5, 10, 11 y 12).**
- **10.°, 3.11:** espectrometría de masas para obtener la composición isotópica y la masa atómica relativa
  (ACSCH023 y 024). Va después de 3.4.
- **10.°, 12.15:** reversibilidad y equilibrio explicados con la teoría de colisiones y las energías de activación
  directa e inversa (ACSCH090, 092 y 094). Une la cinética (12.4) con el cálculo de K (12.8).
- **11.°, 3.15:** determinación de estructuras orgánicas con espectros infrarrojos y de masas (ACSCH130). Retoma la
  espectrometría de 10.°.
- **11.°, 9.8:** comparación de combustibles fósiles y biocombustibles (ACSCH038). ACARA la ubica en la unidad 1,
  pero aquí la combustión y los hidrocarburos llegan en 11.°. Por eso va después de 9.3.
- **11.°, 9.9:** diseño de una ruta de síntesis para un producto con propiedades específicas (ACSCH131 y 133). Es el
  cierre de la unidad de reacciones orgánicas.

**3. Cinco fusiones de temas repetidos los pagan (acciones 4, 6, 7, 8 y 9).**
- En 10.°, 1.11 y 7.1 explican los estados de la materia con el mismo modelo cinético. Quedan en 1.11.
- En 11.°, la unidad 2 repetía la terna identificación-propiedades-nomenclatura para alquenos y para alquinos.
  Se trabajan juntos en 2.7, 2.8 y 2.9. ACSCH035 pasa de 13 a 10 temas en el ciclo, todavía con cobertura
  sólida.
- En 11.°, 6.2 y 6.3 trataban los dos el balanceo redox.

**4. Reformulaciones sin costo (acciones 13 a 16).**
- 6.9 de 11.° incluye las celdas de combustible y sus nanocatalizadores (ACSCH109).
- 1.9 de 11.° pide de forma explícita la manufactura molecular (ACSCH138).
- 9.2 de 10.° agrega los patrones de reacción de los ácidos con metales, carbonatos y bases (ACSCH066 y 067).
  Hoy 10.° no trabaja ácidos, y 11.° empieza ya en Kw, Ka y amortiguadores.
- 2.2 de 11.° deja de repetir la hibridación de 10.° (5.7) y la aplica al carbono de los hidrocarburos.

**5. Lo que va más allá de ACARA se conserva, pero se señala (acciones 17 y 18).**
Se marcan 15 temas para que el MINED revise su nivel. Ninguno se quita ni se mueve.
- 10.°: números cuánticos, orbitales moleculares, Born-Haber, entropía y Gibbs, leyes integradas de velocidad,
  mecanismos y van't Hoff.
- 11.°: quiralidad, precipitación selectiva, Nernst, series radiactivas y ruptura homolítica y heterolítica.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 10.° | 112 | 114 | 54,5 % |
| 11.° | 97 | 95 | 45,5 % |
| **Total** | **209** | **209** | |

10.° gana dos temas: uno por el tema redox que baja de 11.° y otro porque recibe dos temas nuevos y una sola
fusión. El desequilibrio entre los dos grados es leve.

## Prerrequisitos que se ordenan
Un script de validación confirma:
- el total de 209 temas;
- que todos los ids afectados existen;
- que se resuelven las tres secuencias invertidas de Química (oxidación-reducción → agentes oxidantes;
  oxidación-reducción → electrólisis; hidrocarburos → isomería);
- que los temas nuevos no crean secuencias invertidas.

Las cuatro inversiones que quedan en el ciclo son de Biología y Física.

Varios temas quedan en el mismo grado que su prerrequisito. Al ordenar las unidades hay que respetar:
- **10.°:**
  - isótopos y masa atómica (3.4) → espectrometría de masas (3.11);
  - clasificación de reacciones (9.2) → redox (9.5) → unidad 13;
  - teoría de colisiones (12.4) y catalizadores (12.7) → reversibilidad (12.15) → constante de equilibrio (12.8).
- **11.°:**
  - grupos funcionales (3.4 a 3.12) → estructuras orgánicas (3.15);
  - combustión de hidrocarburos (9.3) → combustibles (9.8);
  - reacciones orgánicas (9.2 a 9.6) → síntesis (9.9).

## Decisiones abiertas para el MINED
1. **Nivel de 10.° y 11.°.** ¿Se mantienen los 15 temas de las acciones 17 y 18 con su profundidad
   universitaria? Si se aligeran, por ejemplo uniendo 11.4 y 11.5 de 10.° (entropía), se podrían cubrir otros
   faltantes sin fusionar contenidos de ACARA.
2. **Hidrocarburos en 10.°.** ACARA los ubica en la unidad 1 (ACSCH035). Si el MINED los adelanta, los combustibles
   (9.8) y la isomería podrían volver a 10.°.
3. **Equilibrio en 9.° y 10.°.** El equilibrio dinámico ya aparece en 9.° y se retoma en 10.° y 11.° (ácido-base,
   Kps). Conviene revisar la progresión para no repetir el nivel introductorio.
4. **Datos que conviene verificar.**
   - ACSCH068 (las condiciones cambian la velocidad) figura sin cobertura, pero los temas 12.1 a 12.7 y el tema
     3.2 de 9.° la trabajan. Parece un efecto de la alineación, no un vacío real.
   - Lo mismo ocurre con la escala de pH, que se ve en 7.° y 9.°.
5. **Indagación.** Solo se cubre el 47 % de los objetivos de indagación y naturaleza de la ciencia de ACARA. Esta
   propuesta no los trata. Requieren una revisión aparte de los indicadores de logro.
