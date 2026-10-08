# Contraste internacional de 9.°–11.° con la malla V2

> Spec 11 (`specs/11_grafos_internacionales_9_11.md`). Revisión experta del 2026-10-08. Este README lo escribe el
> equipo; `<asignatura>.md`, `Contraste_<asignatura>.xlsx`, `contraste.json` y `revision_humana.csv` se generan con
> `uv run gskg internacional construir`.

## Qué hay aquí
- **9 países**: SG, JP, KR, ENG, AU, HK, TW, EE y ON. Son 60 documentos oficiales y **8.602 objetivos** validados:
  Gemini 3.1 Pro extrae y Gemini 2.5 Pro valida contra la página del PDF. 636 quedaron como «parciales» y 337 se
  descartaron por no fieles.
- **Grafo** en `data/grafo/internacional/`: país → curso → objetivo → concepto, más los prerrequisitos del repo.
  Son 9.205 nodos y 36.114 aristas.
- **Consenso** por concepto: 509 conceptos. Para cada uno, cuántos países lo enseñan en el núcleo y en la
  especialización, y el grado SV de su primera aparición.
- **Contraste** con la malla V2 de 9.°–11.°: un informe por asignatura y un Excel con fórmulas (hojas Datos,
  Contraste y Resumen).
- **Revisión humana**: `revision_humana.csv` con 1.157 objetivos parciales o con etiquetas de confianza baja.
  Tiene columnas `decision` y `revisado_por` para el MINED.

## Cómo leer las clases
El contraste principal se hace contra el **núcleo** (lo que cursa la mayoría). La especialización funciona como
techo. Para que haya consenso se exige que **≥ 5 países** tengan el concepto en su núcleo, tal como dice la spec.
Con 8 núcleos (HK no tiene), 4 países sería un empate. Con un umbral de 4, solo un concepto por asignatura
cambiaría de clase.

| Clase | Lectura |
|---|---|
| no retomado | La V2 solo lo ve antes de 9.° y ≥ 5 países lo profundizan en el núcleo de 9.°–11.°: es un **hueco de profundización** |
| tardío / adelantado | Solo se juzga lo que la V2 **introduce** en 9.°–11.° |
| solo especialización | La V2 lo pone en un curso obligatorio, pero en los países es contenido de electiva (≤ 1 núcleo y ≥ 3 electivas) |
| retomado / previo | Espiral normal (antes de 9.° y otra vez en 9.°–11.°) / solo antes de 9.°, sin exigencia internacional |

## Hallazgos estructurales
1. **El Bachillerato salvadoreño es más amplio que casi todos los referentes.** Después de los 16 años, solo JP,
   TW y EE tienen las ciencias obligatorias para todos (y SG con H1). En ENG, AU, HK y ON, y en KR desde 고2,
   Física, Química y Biología son electivas. HK no tiene ninguna ciencia común en S4–S6. Para 10.°–11.°, el
   contraste justo es contra **JP, TW y EE**. Todo lo que en los demás países es electivo funciona como techo.
2. **La V2 pone en cursos obligatorios mucho contenido que en los países es de especialización.**
   Proporción de temas de la V2 ligados al menos a un concepto de la clase «solo especialización»:

   | Malla | Temas | Ligados a especialización |
   |---|---|---|
   | 9.° Ciencias | 108 | 15 (14 %); en la Unidad 3 (Equilibrio químico), 10 de 20 |
   | 10.° Física / Química / Biología | 114 / 105 / 70 | 14 % / **28 %** / 19 % |
   | 11.° Física / Química / Biología | 146 / 97 / 92 | 17 % / **26 %** / 11 % |

   Química es la asignatura más cargada: Gibbs, entropía, orbitales moleculares, hibridación, ley de velocidad
   y Arrhenius, Kps y mecanismos de reacción.
3. **Tierra y Espacio no existe como asignatura en 10.°–11.°.** La V2 la concentra en 9.° (Unidades 4 y 5,
   Oceanografía y Geología de El Salvador, con 29 filas). En Bachillerato la reparte entre Biología (cambio
   climático, G11-BIO-U1-1.8), Química (ciclo del carbono, G10-QUI-U13-13.4) y Física (cosmología,
   G11-FIS-U20-20.6). JP (地学基礎) y TW (必修地球科學) la tienen en el núcleo.
4. **La demanda cognitiva es baja en Física y en Tierra y Espacio.** Se midió con el mismo clasificador por verbos
   (escala TIMSS) en los dos lados, comparando la V2 con la mediana de los países con ≥ 15 enunciados en su núcleo:

   | Asignatura | Razonar: V2 | Razonar: mediana de los países | Recordar: V2 | Recordar: mediana |
   |---|---|---|---|---|
   | Física | **10 %** | 31 % | 7 % | 22 % |
   | Química | 19 % | 17 % | 17 % | 30 % |
   | Biología | 11 % | 11 % | 24 % | 31 % |
   | Tierra y Espacio (9.°, 27 temas) | **0 %** | 45 % | **58 %** | 30 % |

   La Física de la V2 se concentra en *aplicar*: el 83 % de sus enunciados son de calcular y resolver. El contraste
   está entre EE, JP, KR y ON (31–43 % de razonar) y ENG y SG (6–7 %).
5. **Prácticas:** la V2 nombra todas las prácticas que exige el núcleo de ≥ 5 países, salvo «comunicar
   resultados» en Química. La proporción de enunciados con práctica no es comparable: la V2 tiene una columna
   procedimental en cada fila.

## Hallazgos por asignatura (verificados contra la fuente)
Formato de la evidencia: archivo de la V2, hoja y fila; país, documento y página.

### Química
- **Equilibrio cuantitativo en 9.°.** La Unidad 3 de 9.° incluye constante de equilibrio (G09-CIE-U3-3.6/3.7),
  Ka (3.13–3.14) y disoluciones amortiguadoras (3.15–3.17). En los países es especialización: ENG lo ve en
  A level (p. 10), JP en 化学, la electiva (p. 116–119), y SG en H1 y H2.
  **Matiz:** Le Châtelier **cualitativo** a los 15 años sí es estándar. ENG Combined pide «predict the effect of
  changing reaction conditions… on equilibrium» (p. 24). Lo que se adelanta es la parte cuantitativa.
- **Química de 10.°–11.° con nivel universitario inicial:** Gibbs y espontaneidad, entropía, OM y TEV, hibridación,
  resonancia y carga formal, ley de velocidad y Arrhenius, mecanismos de reacción, Kps y estereoquímica. Son
  19 conceptos que a lo sumo un país tiene en su núcleo (por lo general SG H1) y que ≥ 3 países tienen en electivas.
- **Secuencia:** la V2 reconoce isómeros (10.°, G10-QUI-U2-2.6, fila 22) antes de tener hidrocarburos (11.°).
  Además, usa estados de oxidación y poder oxidante en 10.° (G10-QUI-U13-13.3/13.7) antes de la unidad formal
  de redox de 11.° (G11-QUI-U11-11.2, fila 90).
- **Duplicación entre asignaturas:** las leyes de los gases están dos veces en 10.°, en Química (U6,
  Boyle-Charles, fila 56) y en Física (U14, pV = NkT, fila 98).

### Física
- **Física nuclear tarde:** fisión, fusión y radiación ionizante llegan en 11.°, y la V2 no las tiene en 9.°–10.°.
  La fisión y la energía nuclear están en el núcleo de los tres referentes justos para 10.°–11.°: TW 必修
  (PNc-Ⅴc-1 «原子核的分裂», p. 40), JP 物理基礎 («核分裂», p. 110) y EE básica (p. 21). KR 통합과학 tiene la fusión
  (p. 88). SG Combined y ENG Combined **no** tienen fisión; el conteo automático de 5 países se apoyaba en parte en
  etiquetas laxas. La radiación ionizante sí está en el núcleo de SG (p. 23), ENG (p. 36), JP y TW. **No** es tardía
  la desintegración radiactiva: la V2 la trabaja en 10.° (radiaciones α, β y γ, G10-QUI-U3-3.2; datación con vida
  media, G10-BIO-U5-5.3), aunque solo como historia del modelo atómico y no con detección, efectos y usos.
- **Física moderna de electiva en 11.°:** relatividad especial, modelo estándar, cuantización, cuerpo negro,
  Doppler y polarización. A lo sumo un país la tiene en el núcleo. TW es el caso típico y lo hace de forma
  **cualitativa**: 必修 Ⅴc, PKc y PKd, p. 39; el código Ⅴc = obligatorio se verificó en la p. 15.
- **Termodinámica en 9.° antes de las leyes de los gases:** G09-CIE-U2-2.4/2.5 (procesos termodinámicos en gases
  ideales y sus gráficas, filas 6–7) llegan antes que Boyle-Charles (10.°). Además, 10.° agrega procesos
  adiabáticos y la relación de Mayer (G10-FIS-U15-15.5/15.6), que es nivel de especialización.
- **Óptica:** interferencia, difracción y polarización en 10.° (G10-FIS-U16-16.2, fila 113) antes de la
  superposición de ondas (11.°).
- **Demanda:** es el hallazgo 4. Es la asignatura con la brecha más clara.

### Biología
- **Biotecnología técnica en 9.°:** PCR, secuenciación y perfiles genéticos (G09-CIE-U10-10.2, fila 4). Matiz: el
  indicador pide *argumentar una posición* sobre la biotecnología, que es algo común a los 15 años, no dominar la
  técnica. Conviene precisar el alcance más que mover el tema.
- **Metabolismo energético a nivel de electiva en 10.°:** glucólisis, Krebs y cadena respiratoria (G10-BIO-U2-2.12,
  G10-BIO-U7-7.2). Solo SG (H1) lo tiene en el núcleo.
- **Secuencia (revisión experta):** la V2 enseña Krebs y la cadena de transporte de electrones **sin haber
  presentado la mitocondria**. La célula de 9.° (G09-CIE-U8-8.1, fila 3) nombra membrana, citoplasma, núcleo,
  pared, cloroplastos y vacuola, pero no mitocondrias ni ribosomas. SG Combined las pide en el núcleo a partir de
  micrografías electrónicas (p. 43).
- **Desbalance en 9.°:** las cinco unidades de Biología suman 16 filas (Evolución 1, Biosfera 2), frente a 20 de
  Equilibrio químico.

### Ciencias de la Tierra y del Espacio
- **Efecto invernadero no retomado:** la V2 no lo menciona en 9.°–11.°, y los 8 países con núcleo lo tienen (JP
  地学基礎 «温室効果», p. 128; KR [10통과2-02-03], p. 90; TW ENb-Vc, p. 43; ON SNC2D, p. 73). La V2 trata las
  causas del cambio climático en Biología 11.° (G11-BIO-U1-1.8) **sin el mecanismo físico** que lo explica.
- **Atmósfera (capas y composición) no retomada:** la V2 la tiene solo en 3.°, y 5 países la tienen en el núcleo
  de 9.°–11.°.
- **Contextualización sin referente:** Geología y Vulcanismo de El Salvador (9.°) no tienen equivalente en otros
  países, y es esperable que así sea: es un acierto de pertinencia local, no un problema.

## Recomendaciones (para decidir con el MINED; ninguna quita temas)
1. **Química de 9.°:** dejar el equilibrio **cualitativo** (reversibilidad y Le Châtelier) y **reubicar** K, Ka y
   amortiguadoras en 11.°, o en una profundización optativa si se crea.
2. **Química y Física de 10.°–11.°:** marcar como *profundización* los 19 + 12 conceptos de especialización, para
   que el núcleo obligatorio se parezca al de JP, TW y EE. Otra opción es tratarlos de forma cualitativa, como
   hace TW con la física moderna.
3. **Física nuclear** (fisión, fusión y radiación ionizante): adelantarla a 9.° o 10.°.
4. **Secuencias:** gases (leyes antes de procesos termodinámicos), ondas (superposición antes de interferencia),
   redox (formal antes de sus aplicaciones), mitocondria antes del metabolismo e hidrocarburos antes de isomería.
   Hay que coordinar Física y Química de 10.° para no repetir las leyes de los gases.
5. **Tierra y Espacio en Bachillerato:** incluir el efecto invernadero y la atmósfera, por ejemplo en la
   Física 10.° de transferencia de calor y radiación, junto al cambio climático de Biología 11.°. JP y TW muestran
   que se puede tener una Tierra y Espacio común breve (2–4 créditos).
6. **Demanda en Física y Tierra y Espacio:** reescribir indicadores de *aplicar* como *razonar* (predecir,
   justificar con modelos, diseñar y evaluar investigaciones), sin agregar contenido.

## Validación manual (2026-10-08)
**Extracción:** se muestrearon 14 objetivos de 7 países (JP, TW, KR, EE, ENG, SG y ON). En los 14 la cita existe en
la página y la paráfrasis es fiel. Hay dos problemas de alcance que el validador no detecta porque juzga
fidelidad, no pertinencia: EE incluye geografía humana como Tierra y Espacio (51 objetivos; 24 sin concepto, el
resto en ambiente y recursos) y ON extrae las «Big Ideas» de los cursos.

**Hallazgos:** se verificaron 20 contra la V2 (fila) y el PDF (página).

| # | Hallazgo | Resultado |
|---|---|---|
| 1 | K, Ka y amortiguadoras en 9.°: especialización | ✅ Confirmado (V2 U3; JP 化学基礎 sin equilibrio, p. 116; ENG A level, p. 10) |
| 2 | Le Châtelier adelantado | ⚠️ Parcial: el cualitativo es núcleo en ENG (p. 24) |
| 3 | Cambio climático no retomado | ❌ Falso (G11-BIO-U1-1.8). Corregido: vocabulario completo |
| 4 | Big Bang no retomado | ❌ Falso (G11-FIS-U20-20.6). Corregido: equivalencias |
| 5 | Desintegración radiactiva tardía | ❌ Falso (G10-QUI-U3-3.2, G10-BIO-U5-5.3). Corregido: unión de etiquetados |
| 6 | Primera ley de Newton no retomada | ❌ Falso (G10-FIS-U5-5.2). Corregido: ids mal escritos y unión |
| 7 | Fisión y fusión tardías | ✅ Confirmado frente a JP, TW y EE (p. 110, p. 40, p. 21); ⚠️ SG y ENG Combined no tienen fisión: el conteo automático la sobreestima |
| 8 | Efecto invernadero no retomado | ✅ Confirmado (sin mención en V2 9.°–11.°; JP p. 128; KR p. 90; TW p. 43) |
| 9 | Organelos no retomados | ⚠️ Parcial: falta la mitocondria (SG p. 43) |
| 10 | Física moderna en el núcleo de TW | ✅ Confirmado (p. 39; código Ⅴc, p. 15) |
| 11 | Radiactividad en el núcleo de SG y ENG | ✅ Confirmado (SG sección 16; ENG p. 36) |
| 12 | Cambio climático en el núcleo de ON y KR | ✅ Confirmado (ON p. 73; KR p. 90) |
| 13 | Secuencia: conservación de la energía después de termodinámica | ❌ Falso (V2 5.° y 8.°) |
| 14 | Secuencia: isótopos después de desintegración | ❌ Falso (G10-QUI-U3-3.4) |
| 15 | Secuencia: interferencia antes de superposición | ✅ Confirmado |
| 16 | Secuencia: isómeros antes de hidrocarburos | ✅ Confirmado (peso menor) |
| 17 | Secuencia: procesos termodinámicos antes de las leyes de los gases | ✅ Confirmado |
| 18 | PCR y secuenciación en 9.°: especialización | ⚠️ Parcial: el indicador pide argumentar, no la técnica |
| 19 | Geografía humana de EE en Tierra y Espacio | Límite declarado |
| 20 | «Big Ideas» de ON extraídas como objetivos | Límite declarado |

Seis falsos se corrigieron con cambios de método, que se describen abajo. La tabla automática de secuencia
sigue teniendo falsos positivos (2 de 4 en la muestra), así que en los informes se presenta como «candidatos».

## Cambios de método en esta sesión
1. **El momento se juzga solo para lo que la V2 introduce en 9.°–11.°.** Antes, 285 de 286 «adelantados» eran
   temas de la primaria salvadoreña comparados contra datos de 9.°–11.°.
2. **Clases nuevas:** «no retomado», «retomado» y «previo».
3. **Umbral de la spec:** ≥ 5 países, en lugar de ≥ 50 % y ≥ 3.
4. **Etiquetado de la V2 de 9.°–11.° con dos vocabularios** (el de la asignatura y el completo). La presencia es
   la unión de los dos.
5. **Equivalencias revisadas entre asignaturas** (`conceptos.equivalencias()`, 16 pares) en los dos lados.
6. **Normalización de ids:** `CON:fisica:x` → `CON:fisica/x`, solo si el resultado existe. Se recuperaron 55
   etiquetas.
7. **Profundidad y prácticas** (puntos 5 y 6 de la spec), que no estaban implementados.
8. **CSV de revisión humana** y hoja Resumen en el Excel.

## Límites
- **Antecedente incompleto:** solo ENG, AU, JP y EE (básica, 7.°–9.°) tienen datos de antes de 9.°. KR, TW y ON
  tienen su secundaria baja en los mismos PDF, pero no se extrajo (son unas 50 ventanas). Por eso «no retomado»
  es conservador.
- **El vocabulario nació de la malla salvadoreña.** Lo que El Salvador no enseña puede no existir en él. Ningún
  concepto propuesto llega a 5 núcleos; el más cercano es «serie de reactividad de los metales» (EE, ENG y SG).
  Ver la tabla de propuestos en cada informe.
- **Estabilidad de la IA:** dos etiquetados del mismo modelo coinciden en un concepto principal en el 91–97 % de
  los temas, con un Jaccard de 0,80–0,83 sobre todos los conceptos. Los hallazgos de un solo concepto se
  verificaron a mano antes de afirmarlos.
- **Demanda:** el clasificador por verbos coincide en un 67 % con la etiqueta de Gemini, que pone «explicar» en
  *razonar*. Se usa el mismo clasificador en los dos lados, pero los países con pocos enunciados (KR, ON y JP en
  algunas asignaturas) son ruidosos.
- **Granularidad:** HK y SG tienen ~1.850 objetivos cada uno y JP 289. El consenso cuenta presencia por país, no
  conteos. El núcleo de AU (Year 10, 19 objetivos) es grueso y no tiene asignatura, así que no entra en
  profundidad ni en prácticas.
- **Grados:** HK no indica el año dentro de S4–S6 (punto medio 10). KR 고3 todavía cursa el currículo de 2015.
- **Excel:** la columna «Lectura» usa una regla simplificada (mediana en lugar de consenso) que coincide con la
  clase oficial en 494 de 512 conceptos. La clase oficial está en la columna de al lado. No se pudo automatizar
  el recálculo en Numbers. Las funciones usadas (IF, COUNT, MEDIAN, AND, OR, COUNTIF y SUM) son compatibles.
