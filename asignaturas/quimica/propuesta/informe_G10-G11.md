# Propuesta de Química, 10.° y 11.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G10-G11.json`. Marco pivote: ACARA Senior Secondary
Chemistry (AUSS), unidades 1 y 2 ≈ 10.° y unidades 3 y 4 ≈ 11.°.

## En resumen
Proponemos 19 acciones: 5 temas nuevos, 6 fusiones, 1 movimiento, 1 división y 6 reformulaciones (`revisar`).
El total del ciclo se mantiene en **209 temas** y no se quita ninguno. Bachillerato ya cubre el 87 % de los
objetivos de contenido de ACARA y sigue su misma secuencia. Por eso la propuesta es acotada:
- corrige tres secuencias invertidas de la propia malla de Química;
- cubre con temas nuevos los faltantes de ACARA más importantes;
- paga esos temas con fusiones de contenidos que se repiten.

Para este ciclo, los candidatos solo traen países de referencia para la oxidación-reducción (Inglaterra en 6.°
y Japón en 7.°). En el resto, la evidencia son los objetivos AUSS sin cobertura o débiles y los prerrequisitos
del grafo.

## Qué cambió con el triaje de conceptos
- El triaje sumó 14 conceptos nuevos y 32 prerrequisitos sugeridos, pero **ninguno es de Química**. No hay
  aristas del triaje que afecten este ciclo, ni conceptos nuevos que usar en los temas.
- La simulación de la v1 contra el grafo actual dejó **3 secuencias de confianza alta** sin resolver. Una era de
  la v1: reformular 2.6 de 10.° no le quitaba la isomería. Por eso la acción 2 pasa a ser una **división** y el
  tema 2.6 se une con 2.5 (acción 19).
- Las otras dos (carbohidratos y lípidos) no vienen de la malla de Química. Las genera la unidad 1 de Biología
  de 10.° (*Biomoléculas*), cuyos temas también llevan los conceptos químicos. Se dejan como decisión abierta.
- Con la v2, las secuencias de confianza alta del ciclo bajan de 5 a 2.

## Qué cambia y por qué

**1. Cada concepto llega después de lo que necesita (acciones 1, 2, 6 y 19).**
- La unidad 13 de 10.° habla de agentes oxidantes (13.3 y 13.7) y de electrólisis (13.8). Sin embargo, la
  oxidación-reducción se define recién en 11.°. El tema 6.1 de 11.° baja a la unidad 9 de 10.° (*Reacciones
  químicas*) como 9.5: transferencia de electrones, números de oxidación y agentes oxidante y reductor.
- En 11.°, la unidad de Electroquímica abre con el balanceo por ion-electrón. Para eso se unen 6.2 y 6.3, que
  repetían ese contenido.
- El reconocimiento de isómeros sale de 2.6 de 10.°, porque supone las cadenas de hidrocarburos de 11.°. Pasa a
  un tema nuevo de 11.° (2.13): construir y nombrar isómeros de alcanos y alquenos, justo antes de 3.14. Lo que
  queda de 2.6 se une con 2.5, que ya calculaba las fórmulas empírica y molecular.

**2. Cinco faltantes de ACARA entran como temas nuevos (acciones 3, 5, 10, 11 y 12).**
- **10.°, 3.11:** espectrometría de masas para obtener la composición isotópica y la masa atómica relativa
  (ACSCH023 y 024). Va después de 3.4.
- **10.°, 12.15:** reversibilidad y equilibrio explicados con la teoría de colisiones y las energías de activación
  directa e inversa (ACSCH090, 092 y 094). Une la cinética (12.4) con el cálculo de K (12.8).
- **11.°, 3.15:** determinación de estructuras orgánicas con espectros infrarrojos y de masas (ACSCH130).
- **11.°, 9.8:** comparación de combustibles fósiles y biocombustibles (ACSCH038), después de 9.3.
- **11.°, 9.9:** diseño de una ruta de síntesis para un producto con propiedades específicas (ACSCH131 y 133).

**3. Seis fusiones de temas repetidos los pagan (acciones 4, 6, 7, 8, 9 y 19).**
- En 10.°, 1.11 y 7.1 explican los estados de la materia con el mismo modelo cinético. Quedan en 1.11.
- En 10.°, 2.5 y 2.6 calculan las mismas fórmulas; quedan en 2.5, con compuestos inorgánicos y orgánicos.
- En 11.°, la unidad 2 repetía la terna identificación-propiedades-nomenclatura para alquenos y para alquinos.
  Se trabajan juntos en 2.7, 2.8 y 2.9. ACSCH035 conserva una cobertura sólida.
- En 11.°, 6.2 y 6.3 trataban los dos el balanceo redox.

**4. Reformulaciones sin costo (acciones 13 a 16).** 6.9 de 11.° incluye las celdas de combustible y sus
nanocatalizadores (ACSCH109); 1.9 de 11.° pide la manufactura molecular (ACSCH138); 9.2 de 10.° agrega los
patrones de reacción de los ácidos (ACSCH066 y 067); 2.2 de 11.° aplica al carbono la hibridación de 10.° (5.7).

**5. Lo que va más allá de ACARA se conserva, pero se señala (acciones 17 y 18).** Son 15 temas: números
cuánticos, orbitales moleculares, Born-Haber, entropía y Gibbs, leyes de velocidad, mecanismos y van't Hoff en
10.°; quiralidad, precipitación selectiva, Nernst, series radiactivas y ruptura de enlaces en 11.°.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 10.° | 112 | 113 | 54,1 % |
| 11.° | 97 | 96 | 45,9 % |
| **Total** | **209** | **209** | |

10.° recibe el tema redox de 11.° y dos temas nuevos, y pierde dos por fusión. 11.° recibe el tema de isómeros.

## Prerrequisitos que se ordenan
Un script de validación confirma el total de 209 temas, que todos los ids afectados existen y que los conceptos
están en el vocabulario. La simulación sobre el grafo resuelve tres secuencias invertidas (oxidación-reducción →
agentes oxidantes; oxidación-reducción → electrólisis; hidrocarburos → isomería) y los temas nuevos no crean
otras. Al ordenar las unidades hay que respetar, dentro de cada grado:
- **10.°:** isótopos (3.4) → espectrometría de masas (3.11); clasificación de reacciones (9.2) → redox (9.5) →
  unidad 13; teoría de colisiones (12.4) → reversibilidad (12.15) → constante de equilibrio (12.8).
- **11.°:** nomenclatura de hidrocarburos (2.4 a 2.9) → isómeros (2.13) → estereoisómeros (3.14); grupos
  funcionales (3.4 a 3.12) → estructuras (3.15); combustión (9.3) → combustibles (9.8); reacciones orgánicas
  (9.2 a 9.6) → síntesis (9.9).

## Decisiones abiertas para el MINED
1. **Biomoléculas en Biología de 10.°.** La unidad 1 de Biología de 10.° trabaja carbohidratos y lípidos antes de
   que Química dé los grupos funcionales y la esterificación (11.°). Los prerrequisitos son correctos para el
   tratamiento químico, que sigue en la unidad 11 de 11.°. Proponemos que Biología los trate a nivel descriptivo
   (concepto *Biomoléculas*) y revisar su etiquetado, en vez de adelantar la química orgánica a 10.°.
2. **Nivel de 10.° y 11.°.** ¿Se mantienen los 15 temas de las acciones 17 y 18 con su profundidad
   universitaria? Si se aligeran (por ejemplo, uniendo 11.4 y 11.5 de 10.°), se podrían cubrir otros faltantes.
3. **Hidrocarburos en 10.°.** ACARA los ubica en la unidad 1 (ACSCH035). Si el MINED los adelanta, los
   combustibles (9.8), la isomería y la base de las biomoléculas podrían ir a 10.°.
4. **Equilibrio y datos por verificar.** El equilibrio dinámico aparece en 9.°, 10.° y 11.°: conviene revisar la
   progresión. ACSCH068 y la escala de pH figuran sin cobertura, pero se trabajan (12.1 a 12.7; 7.° y 9.°).
5. **Indagación.** Solo se cubre el 47 % de los objetivos de indagación de ACARA. Requiere una revisión aparte.
