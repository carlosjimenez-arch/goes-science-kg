# Física · contraste internacional de 2.°–8.° (malla V2)

> Generado por `gskg internacional construir`. Método y límites: `specs/12_grafos_internacionales_2_8.md` y `internacional/2_8/README.md`.
> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para
> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.

## Resumen

| Clase | Conceptos | Qué significa |
|---|---|---|
| Faltantes del núcleo común | 0 | El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°. |
| Llegan tarde | 3 | La V2 lo introduce en 2.°–8.°, dos o más grados después de que el núcleo alcanza el consenso. |
| Solo después de 2.°–8.° | 17 | La V2 lo enseña después de 2.°–8.° y el núcleo internacional no lo exige antes. |
| Adelantados | 12 | La V2 lo introduce en 2.°–8.°, 1,5 grados o más antes que la mediana del núcleo de los países. |
| Sin referente | 9 | La V2 lo enseña en 2.°–8.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo. |
| Alineados | 36 | La V2 lo introduce en 2.°–8.° con un momento coherente con el consenso (± 1,5 grados). |
| Inciertos (a revisión) | 54 | La lectura amplia y la estricta del etiquetado dan clases distintas: no se afirma nada hasta revisarlo (revision_clases.csv). |

Países con núcleo común por grado SV (denominador del consenso): 2.°: AU, EE, ENG, HK, JP, KR, ON, TW; 3.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW; 4.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW; 5.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW; 6.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW; 7.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW; 8.°: AU, EE, ENG, HK, JP, KR, ON, SG, TW

Sensibilidad: con 4 países en lugar de 5, 0 conceptos más pasarían de «solo antes de 2.°» a «no retomados».

Revisión experta: 7 conceptos cambiaron de clase frente a la regla automática (`data/interim/internacional_2_8/revisiones.json`): Conservación de la energía (adelantado → alineado); Fricción y resistencia del aire (incierto → alineado); Fuerza magnética sobre corrientes y motor eléctrico (incierto → alineado); Conducción, convección y radiación (adelantado → alineado); Ley de Coulomb (incierto → posterior); Leyes de Kepler (incierto → posterior); Espejos planos e imágenes (incierto → tardio).

Inciertos: 54 conceptos tienen clases distintas en la lectura amplia y en la estricta; no se afirma nada de ellos hasta revisarlos (`revision_clases.csv`, con las dos clases).

## Llegan tarde (3)

La V2 lo introduce en 2.°–8.°, dos o más grados después de que el núcleo alcanza el consenso.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Ley de Ohm | 9.°–11.° | 7.° (67% de los países con núcleo); 8 con núcleo en 2.°–8.° | EE 8, ENG 6, HK 7, JP 7, KR 7, ON 8, SG 7.5, TW 7 | SV: G09-CIE-U6-6.8 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 6 - Electricidad», fila 10)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 20): «Aplicar fórmulas de la ley de Ohm, circuitos en serie y paralelo, resistencia, trabajo, potencia y calor de Joule.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 33): «Aplicar la relación entre corriente, resistencia y voltaje. Explicar cómo varía la resistencia y diseñar circuitos para explorar estos efectos en diversos componentes.»<br>⚠ Revisar: los objetivos de los países también enseñan CON:fisica/corriente-voltaje-resistencia, que la V2 da antes |
| Lentes delgadas e imágenes | 10.°–11.° | 8.° (56% de los países con núcleo); 5 con núcleo en 2.°–8.° | EE 8, HK 5, JP 6, KR 4.5, TW 4.5 | SV: G10-FIS-U16-16.11 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 122)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 19): «Aplicar el principio de refracción de la luz para explicar el funcionamiento de una lente y resolver problemas.»<br>HK · Science (P1–P6) [núcleo] (hk_primaria, p. 38): «Enumerar ejemplos de la vida diaria que aplican el principio de refracción de la luz, como gafas y lupas.» |
| Espejos planos e imágenes | 10.°–11.° | mediana 5.75; 4 con núcleo en 2.°–8.° | HK 3, KR 4.5, SG 7.5, TW 7 | SV: G10-FIS-U16-16.10 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 121)<br>HK · Science (P1–P6) [núcleo] (hk_primaria, p. 37): «Conocer algunos fenómenos de reflexión de la luz, como el reflejo en el agua y los espejos.»<br>KR · 중학교 과학 1~3학년군 (Ciencias, secundaria baja) [núcleo] (kr_jung, p. 55): «Explicar cualitativamente la formación de imágenes en espejos planos, clasificar espejos y lentes cotidianos y comparar las características de sus imágenes.»<br>Revisión experta: Reflexión en espejos en G04-CIE-U1-1.14, pero la formación de imágenes llega en 10.° (G10-FIS-U16-16.10); HK p. 38, KR p. 55, SG p. 37, TW, ENG KS3 p. 12 la dan en SV 5–8. |

## Solo después de 2.°–8.° (17)

La V2 lo enseña después de 2.°–8.° y el núcleo internacional no lo exige antes.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Ley de Coulomb | 9.°–11.° | 8.° (56% de los países con núcleo); 5 con núcleo en 2.°–8.° | EE 8, ENG 6, JP 7, KR 7, TW 7 | SV: G09-CIE-U6-6.2 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 6 - Electricidad», fila 4)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 20): «Explicar la electrización y la interacción eléctrica de los cuerpos.»<br>ENG · National Curriculum KS3 Science [núcleo] (eng_ks3, p. 12): «Separación de cargas al frotar objetos: transferencia de electrones y fuerzas entre objetos cargados.»<br>Revisión experta: Ningún núcleo de 2.°–8.° pide la ley cuantitativa (EE p. 20, ENG KS3 p. 12, KR p. 58, TW p. 32: electrostática cualitativa, que la V2 da en G05-CIE-U3-3.6). |
| Corriente alterna y transformador | 9.°–11.° | mediana 7; 3 con núcleo en 2.°–8.° | ENG 8.5, JP 7, TW 7 | SV: G09-CIE-U6-6.7 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 6 - Electricidad», fila 9)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 33): «Recordar las funciones y diferencias de potencial de los cables de red. Explicar los peligros de un cable de fase y su conexión a tierra.»<br>JP · 学習指導要領 理科 (小学校・中学校, 2017) [núcleo] (jp_cos_826, p. 49): «Mover una bobina o un imán genera corriente (inducción electromagnética); diferenciar corriente continua y alterna.» |
| Defecto de masa y energía de enlace nuclear | 11.° | mediana 8; 1 con núcleo en 2.°–8.° | EE 8 | SV: G11-FIS-U20-20.3 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 123)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Explicar el valor práctico de la fusión y fisión nucleares.» |
| Desintegración radiactiva | 10.°–11.° | mediana 8; 3 con núcleo en 2.°–8.° | AU 8, EE 8, ENG 8.5 | SV: G10-BIO-U5-5.3 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 50)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S9U06): «Explicar cómo cambió el modelo atómico tras descubrir electrones, protones y neutrones y describir cómo el decaimiento radiactivo natural produce átomos estables.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Caracterizar y comparar la radiación alfa, beta y gamma.» |
| Dualidad onda-partícula | 10.°–11.° | mediana 8; 1 con núcleo en 2.°–8.° | AU 8 | SV: G10-FIS-U16-16.7 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 118)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S9U04): «Usar modelos ondulatorio y de partículas para describir la transferencia de energía a través de distintos medios y evaluar la utilidad de cada modelo.» |
| Fisión y fusión nuclear | 11.° | mediana 7.5; 3 con núcleo en 2.°–8.° | EE 8, SG 7.5, TW 7 | SV: G11-FIS-U23-23.7 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 146)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Explicar el valor práctico de la fusión y fisión nucleares.»<br>SG · Lower Secondary Science G2/G3 (Sec 1–2) [núcleo] (sg_secundaria_baja, p. 42): «Apreciar los usos de diversas fuentes de energía (fósiles, solar, hidroeléctrica, eólica, geotérmica, nuclear) y su impacto ambiental.» |
| Fotón y efecto fotoeléctrico | 10.°–11.° | mediana 7; 2 con núcleo en 2.°–8.° | AU 8, ENG 6 | SV: G10-QUI-U3-3.5 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 27)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S9U04): «Usar modelos ondulatorio y de partículas para describir la transferencia de energía a través de distintos medios y evaluar la utilidad de cada modelo.»<br>ENG · National Curriculum KS3 Science [núcleo] (eng_ks3, p. 12): «La luz transfiere energía de la fuente al absorbente produciendo efectos químicos y eléctricos; material fotosensible en retina y cámaras.» |
| Fuerza electromotriz y leyes de Kirchhoff | 11.° | mediana 6.5; 2 con núcleo en 2.°–8.° | ENG 6, JP 7 | SV: G11-FIS-U9-9.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 46)<br>ENG · National Curriculum KS3 Science [núcleo] (eng_ks3, p. 12): «Corriente eléctrica en amperios en circuitos en serie y paralelo; las corrientes se suman en nodos; corriente como flujo de carga.»<br>JP · 学習指導要領 理科 (小学校・中学校, 2017) [núcleo] (jp_cos_826, p. 45): «Construir circuitos y medir corriente y voltaje para descubrir las regularidades de la corriente en cada punto y del voltaje en cada parte.» |
| Leyes de Kepler | 4.°–11.° | —; 0 con núcleo en 2.°–8.° |  | SV: G04-CIE-U4-4.1 (Matriz_Ciencias_4to_Grado_U1_U6.xlsx, hoja «Unidad 4 - Sistema solar», fila 3)<br>Revisión experta: G04-CIE-U4-4.1 trata modelos geocéntrico y heliocéntrico (como ENG Year 5, p. 30), no Kepler; Kepler solo en G11-FIS-U22-22.2, como TW y KR en bachillerato. |
| Núcleo atómico e isótopos | 11.° | mediana 8.25; 2 con núcleo en 2.°–8.° | EE 8, ENG 8.5 | SV: G11-FIS-U10-10.3 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 61)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Relacionar la composición de isótopos, la desintegración radiactiva y las reacciones nucleares con la estructura del núcleo atómico.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 35): «Describir el átomo con un núcleo positivo rodeado de electrones negativos, donde el radio nuclear es mucho menor al atómico y concentra casi toda la masa.» |
| Ondas de radio y telecomunicaciones | 11.° | mediana 7; 3 con núcleo en 2.°–8.° | ENG 8.5, HK 7, TW 4.5 | SV: G11-FIS-U12-12.7 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 74)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 32): «Recordar que las ondas de radio pueden ser producidas por oscilaciones en circuitos eléctricos o inducirlas.»<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 77): «Investigar el uso de radiaciones electromagnéticas y sus peligros potenciales relacionados.» |
| Radiación ionizante: detección, efectos y aplicaciones | 11.° | mediana 7.75; 4 con núcleo en 2.°–8.° | EE 8, ENG 8.5, HK 7, SG 7.5 | SV: G11-FIS-U21-21.4 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 130)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Caracterizar y comparar la radiación alfa, beta y gamma.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 33): «Dar ejemplos de usos prácticos de ondas electromagnéticas y describir los efectos peligrosos de las ondas ultravioleta, rayos X y rayos gamma en tejidos humanos.» |
| Radiación térmica y cuerpo negro | 10.°–11.° | mediana 7; 4 con núcleo en 2.°–8.° | HK 7, KR 7, ON 6, SG 7.5 | SV: G10-FIS-U13-13.3 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 96)<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 57): «Realizar trabajo práctico para probar la efectividad de las películas de control solar.»<br>KR · 중학교 과학 1~3학년군 (Ciencias, secundaria baja) [núcleo] (kr_jung, p. 48): «Comparar la conducción del calor en diferentes objetos utilizando una cámara termográfica.» |
| Rapidez de la luz | 11.° | mediana 7; 4 con núcleo en 2.°–8.° | ENG 6, HK 7, SG 7.5, TW 7 | SV: G11-FIS-U15-15.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 87)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 32): «Recordar que las ondas electromagnéticas son transversales, viajan a la misma velocidad en el espacio, y explicar que transfieren energía.»<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 74): «Reconocer que la luz puede viajar en el vacío.» |
| Semiconductores y electrónica básica | 9.° | mediana 7; 1 con núcleo en 2.°–8.° | KR 7 | SV: G09-CIE-U6-6.10 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 6 - Electricidad», fila 12)<br>KR · 중학교 과학 1~3학년군 (Ciencias, secundaria baja) [núcleo] (kr_jung, p. 58): «Explicar la diferencia de resistencia en materiales usando ejemplos de conductores y aislantes, e introducir los semiconductores.» |
| Superposición e interferencia de ondas | 11.° | mediana 6; 1 con núcleo en 2.°–8.° | ENG 6 | SV: G11-FIS-U5-5.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 23)<br>ENG · National Curriculum KS3 Science [núcleo] (eng_ks3, p. 11): «Ondas en el agua como ondulaciones transversales que pueden reflejarse y sumarse o cancelarse (superposición).» |
| Viscosidad y régimen de flujo | 9.°–11.° | mediana 7; 1 con núcleo en 2.°–8.° | ON 7 | SV: G09-CIE-U1-1.10 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 1 - Mecánica de fluidos», fila 12)<br>ON · Science and Technology, Grade 8 [núcleo] (on_st_g8, p. 174): «Comprender los factores que afectan la viscosidad y comparar la viscosidad de varios fluidos, incluyendo la tasa de flujo volumétrico.» |

## Adelantados (12)

La V2 lo introduce en 2.°–8.°, 1,5 grados o más antes que la mediana del núcleo de los países.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Densidad | 2.°–10.° | 7.° (78% de los países con núcleo); 8 con núcleo en 2.°–8.° | EE 8, ENG 6, HK 7, JP 2, KR 4.5, ON 5, SG 7.5, TW 7 | SV: G02-CIE-U1-1.10 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 1 - Materia», fila 12)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 12): «Medir o calcular el área de una forma, el volumen de un cuerpo, la velocidad de movimiento y la densidad.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 35): «Aplicar la relación entre densidad, masa y volumen en cambios donde la masa se conserva.» |
| Aceleración | 5.°–10.° | 8.° (67% de los países con núcleo); 6 con núcleo en 2.°–8.° | ENG 8.5, HK 4, JP 8, KR 7, SG 6, TW 4.5 | SV: G05-CIE-U2-2.9 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 11)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 31): «Aplicar la segunda ley de Newton en cálculos que relacionen fuerzas, masas y aceleraciones.»<br>HK · Science (P1–P6) [núcleo] (hk_primaria, p. 39): «Saber que la fuerza puede cambiar el estado de movimiento de un objeto, iniciándolo, deteniéndolo, acelerándolo, desacelerándolo o cambiando su dirección.» |
| Carga eléctrica y electrización | 5.°–11.° | 7.° (67% de los países con núcleo); 7 con núcleo en 2.°–8.° | EE 8, ENG 6, HK 7, JP 7, KR 7, ON 5, TW 7 | SV: G05-CIE-U3-3.6 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 3 - Estructura atómica», fila 8)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 20): «Conocer conceptos de carga, campo, corriente, conductores y aislantes, y aplicarlos para explicar fenómenos naturales.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 33): «Recordar los requisitos para el flujo de corriente en un circuito cerrado y aplicar la relación entre cantidad de carga, corriente y tiempo.» |
| Energía potencial gravitatoria y elástica | 5.°–8.° | 7.° (67% de los países con núcleo); 7 con núcleo en 2.°–8.° | AU 7, ENG 6, HK 4, JP 8, KR 7, ON 4, TW 7 | SV: G05-CIE-U2-2.13 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 15)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S8U05): «Clasificar formas de energía como cinética o potencial e investigar la transferencia y transformación de energía en sistemas simples.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 29): «Calcular la cantidad de energía asociada a un cuerpo en movimiento, un resorte estirado y un objeto elevado sobre el nivel del suelo.» |
| Circuito eléctrico simple | 2.°–9.° | 4.° (56% de los países con núcleo); 9 con núcleo en 2.°–8.° | AU 5, EE 8, ENG 2, HK 3, JP 2, KR 4.5, ON 5, SG 5, TW 2.5 | SV: G02-CIE-U2-2.2 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 2 - Energía», fila 5)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S6U03): «Investigar la transferencia y transformación de energía en circuitos eléctricos, incluido el papel de sus componentes, aislantes y conductores.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 20): «Nombrar las partes del circuito, explicar su propósito y dibujar diagramas eléctricos simples.» |
| Color y dispersión de la luz | 2.°–11.° | 6.° (56% de los países con núcleo); 8 con núcleo en 2.°–8.° | EE 8, ENG 6, HK 2, JP 2, KR 7, ON 3, SG 7.5, TW 4.5 | SV: G02-CIE-U2-2.10 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 2 - Energía», fila 13)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 19): «Relacionar el espectro de la luz reflejada con el color de los objetos.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 32): «Describir los grupos del espectro electromagnético, su variación en longitud de onda y frecuencia, y que el ojo humano detecta un rango limitado.» |
| Conservación de la energía mecánica | 5.°–8.° | 8.° (56% de los países con núcleo); 5 con núcleo en 2.°–8.° | ENG 8.5, JP 8, KR 7, ON 4, TW 7 | SV: G05-CIE-U2-2.15 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 17)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 29): «Describir los cambios en el almacenamiento de energía en situaciones comunes como lanzar un objeto, colisiones, aceleración por fuerza constante, frenado o hervir agua.»<br>JP · 学習指導要領 理科 (小学校・中学校, 2017) [núcleo] (jp_cos_826, p. 60): «Comprender trabajo y potencia, y que la energía mecánica de un cuerpo se mide por el trabajo que puede realizar sobre otro.» |
| Disipación de energía y eficiencia | 2.°–10.° | 7.° (56% de los países con núcleo); 9 con núcleo en 2.°–8.° | AU 8, EE 8, ENG 8.5, HK 7, JP 8, KR 4.5, ON 3, SG 6, TW 7 | SV: G02-CIE-U5-5.6 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 5 - Objetos técnicos», fila 8)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S9U05): «Aplicar la ley de conservación de la energía para analizar la eficiencia de un sistema según entradas, salidas, transferencias y transformaciones de energía.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 24): «Analizar el consumo de energía a nivel familiar y social, valorar el consumo sostenible y proponer soluciones.» |
| Energía cinética | 5.°–8.° | 7.° (56% de los países con núcleo); 6 con núcleo en 2.°–8.° | AU 7, ENG 6, HK 4, JP 8, KR 7, TW 4.5 | SV: G05-CIE-U2-2.12 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 14)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S8U05): «Clasificar formas de energía como cinética o potencial e investigar la transferencia y transformación de energía en sistemas simples.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 29): «Calcular la cantidad de energía asociada a un cuerpo en movimiento, un resorte estirado y un objeto elevado sobre el nivel del suelo.» |
| Formas de energía | 2.°–4.° | 4.° (56% de los países con núcleo); 8 con núcleo en 2.°–8.° | AU 2, EE 8, ENG 6, HK 2, KR 7, ON 3, SG 4, TW 4.5 | SV: G02-CIE-U2-2.1-f3 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 2 - Energía», fila 3)<br>AU · Australian Curriculum Science F–10 (v9) [núcleo] (au_f6_v9, AC9S2U02): «Explorar acciones para producir distintos sonidos y reconocer que la energía sonora hace vibrar los objetos.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 19): «Explicar los conceptos de trabajo mecánico, energía mecánica (potencial y cinética), potencia y eficiencia.» |
| Fuentes de energía renovables y no renovables | 2.°–7.° | 4.° (56% de los países con núcleo); 8 con núcleo en 2.°–8.° | EE 5, ENG 6, HK 3, JP 5, KR 4.5, ON 3, SG 4.5, TW 2.5 | SV: G02-CIE-U2-2.3 (Matriz_Ciencias_2do_Grado_U1_U6.xlsx, hoja «Unidad 2 - Energía», fila 6)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Explicar el valor práctico de la fusión y fisión nucleares.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 29): «Describir las principales fuentes de energía en la Tierra, comparar sus usos y distinguir entre fuentes renovables y no renovables.» |
| Caída libre | 5.°–11.° | mediana 7; 3 con núcleo en 2.°–8.° | ENG 8.5, HK 7, KR 7 | SV: G05-CIE-U2-2.14 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 16)<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 31): «Recordar velocidades típicas cotidianas, la aceleración en caída libre y estimar magnitudes de aceleraciones comunes.»<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 64): «Investigar el movimiento de caída libre de diferentes objetos.» |

## Sin referente (9)

La V2 lo enseña en 2.°–8.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Aceleración y fuerza centrípeta | 5.°–10.° | mediana 7; 1 con núcleo en 2.°–8.° | TW 7 | SV: G05-CIE-U2-2.7 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 9)<br>TW · 國民中學 第四學習階段 (grados 7–9) [núcleo] (tw_jh, p. 29): «El movimiento circular es un tipo de movimiento acelerado.» |
| Cinemática en dos dimensiones y proyectiles | 8.°–11.° | mediana 6; 1 con núcleo en 2.°–8.° | ENG 6 | SV: G08-CIE-U1-1.9 (Matriz_Ciencias_8vo_Grado_U1_U10.xlsx, hoja «Unidad 1 - Mecánica», fila 11)<br>ENG · National Curriculum KS3 Science [núcleo] (eng_ks3, p. 10): «Movimiento relativo: trenes y autos que se cruzan.» |
| Conservación del momento lineal | 8.°–11.° | —; 0 con núcleo en 2.°–8.° |  | SV: G08-CIE-U1-1.14 (Matriz_Ciencias_8vo_Grado_U1_U10.xlsx, hoja «Unidad 1 - Mecánica», fila 16) |
| Dinámica y energía de rotación | 5.°–10.° | —; 0 con núcleo en 2.°–8.° |  | SV: G05-CIE-U2-2.12 (Matriz_Ciencias_5to_Grado_U1_U6.xlsx, hoja «Unidad 2 - Mecánica», fila 14) |
| Hidrodinámica: continuidad y Bernoulli | 6.°–9.° | mediana 6; 2 con núcleo en 2.°–8.° | HK 7, ON 5 | SV: G06-CIE-U1-1.6 (Matriz_Ciencias_6to_Grado_U1_U6.xlsx, hoja «Unidad 1 - Fluidos», fila 8)<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 50): «Diseñar y construir un dispositivo de ahorro de agua para instalar en un grifo.»<br>ON · Science and Technology, Grade 6 [núcleo] (on_st_g6, p. 154): «Identificar las aplicaciones de las propiedades del aire relacionadas con el vuelo.» |
| Ley de gravitación universal | 8.°–11.° | mediana 7; 2 con núcleo en 2.°–8.° | HK 7, TW 7 | SV: G08-CIE-U8-8.8 (Matriz_Ciencias_8vo_Grado_U1_U10.xlsx, hoja «Unidad 8 - La Tierra en el univ», fila 10)<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 62): «Predecir si la gravedad experimentada por objetos con la misma masa diferiría en distintos planetas.»<br>TW · 國民中學 第四學習階段 (grados 7–9) [núcleo] (tw_jh, p. 32): «Explicar la ley de gravitación universal: la fuerza es proporcional a las masas de los objetos e inversamente proporcional al cuadrado de la distancia entre ellos.» |
| Movimiento armónico simple | 8.°–11.° | mediana 6; 2 con núcleo en 2.°–8.° | EE 8, JP 4 | SV: G08-CIE-U3-3.3 (Matriz_Ciencias_8vo_Grado_U1_U10.xlsx, hoja «Unidad 3 - Ondas mecánicas», fila 5)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 19): «Describir la oscilación basándose en un modelo, utilizando los conceptos de amplitud y período.»<br>JP · 学習指導要領 理科 (小学校・中学校, 2017) [núcleo] (jp_cos_826, p. 70): «El tiempo de una oscilación del péndulo no depende del peso de la masa sino de la longitud del péndulo.» |
| Ondas estacionarias y armónicos | 8.°–11.° | mediana 7; 2 con núcleo en 2.°–8.° | HK 7, TW 7 | SV: G08-CIE-U3-3.11 (Matriz_Ciencias_8vo_Grado_U1_U10.xlsx, hoja «Unidad 3 - Ondas mecánicas», fila 13)<br>HK · Science (S1–S3) [núcleo] (hk_s1_3, p. 77): «Usar una simulación para interpretar las diferentes formas de onda de las notas musicales.»<br>TW · 國民中學 第四學習階段 (grados 7–9) [núcleo] (tw_jh, p. 32): «Explicar que el oído distingue volumen, tono y timbre, pero no puede percibir los ultrasonidos.» |
| Tensión superficial y capilaridad | 6.°–11.° | mediana 2.5; 1 con núcleo en 2.°–8.° | TW 2.5 | SV: G06-CIE-U1-1.4 (Matriz_Ciencias_6to_Grado_U1_U6.xlsx, hoja «Unidad 1 - Fluidos», fila 6)<br>TW · 國民小學 第二、第三學習階段 (grados 3–6) [núcleo] (tw_primaria, p. 20): «El agua presenta cambios en tres estados y el fenómeno de capilaridad.» |

## Candidatos a error de secuencia en la V2 (13)

El prerrequisito llega después que el concepto que lo necesita (grafo de prerrequisitos del repo). Son candidatos: en la revisión manual de 2026-10-08, 2 de 4 resultaron falsos porque el etiquetado no vio el prerrequisito en primaria. Los confirmados están en `internacional/2_8/README.md`. Lectura prudente: el concepto con presencia sólida en la V2 y el prerrequisito sin ninguna etiqueta hasta después; la alerta marca los temas cuyo texto ya nombra el prerrequisito.

| Concepto (grado) | Prerrequisito que llega después (grado) | Confianza | Tema SV |
|---|---|---|---|
| Circuito eléctrico simple (2.°) | Conductores y aislantes eléctricos (4.°) | alta | G02-CIE-U2-2.2 |
| Esfuerzo, deformación y módulo de Young (2.°) | Fuerza elástica y ley de Hooke (5.°) | alta | G02-CIE-U5-5.4 |
| Esfuerzo, deformación y módulo de Young (2.°) | Presión (6.°) | media | G02-CIE-U5-5.4 |
| Masa y peso (2.°) | Gravedad: atracción hacia la Tierra (3.°) | alta | G02-CIE-U5-5.2 |
| Conducción, convección y radiación (2.°) | Modelo de partículas de la materia (6.°) | media | G02-CIE-U2-2.6 |
| Caída libre (5.°) | Movimiento con aceleración constante (8.°) | alta | G05-CIE-U2-2.14 |
| Expansión del universo y Big Bang (5.°) | Efecto Doppler (8.°) | alta | G05-CIE-U5-5.1 |
| Expansión del universo y Big Bang (5.°) | Ley de gravitación universal (8.°) | media | G05-CIE-U5-5.1 |
| Energía cinética (5.°) | Trabajo mecánico (8.°) | media | G05-CIE-U2-2.12 |
| Resistencia equivalente (6.°) | Ley de Ohm (9.°) | alta | G06-CIE-U3-3.5 |
| Absorción de radiación y efecto invernadero (7.°) | Ondas electromagnéticas y espectro (10.°) | alta | G07-CIE-U6-6.13 |
| Refracción de la luz (7.°) | Rapidez de la luz (10.°) | media | G07-CIE-U6-6.21 |
| Ondas estacionarias y armónicos (8.°) | Superposición e interferencia de ondas (10.°) | alta | G08-CIE-U3-3.11 |

## Profundidad: demanda cognitiva en 2.°–8.°

Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: 68% (la diferencia principal: TIMSS pone «explicar» en aplicar).

| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 135 | 21% | 77% | 2% | 31 |
| EE | 91 | 12% | 56% | 32% | 6 |
| ENG | 111 | 25% | 69% | 7% | 5 |
| HK | 298 | 41% | 36% | 23% | 71 |
| KR | 81 | 4% | 61% | 35% | 10 |
| ON | 163 | 33% | 39% | 29% | 16 |
| SG | 138 | 41% | 36% | 23% | 27 |
| TW | 163 | 33% | 47% | 21% | 56 |

## Prácticas científicas en 2.°–8.°

La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.

| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 87 | 39 | 24 | 10 | 19 |
| EE | 32 | 20 | 40 | 22 | 25 |
| ENG | 21 | 39 | 38 | 13 | 22 |
| HK | 95 | 45 | 51 | 56 | 29 |
| KR | 44 | 14 | 22 | 12 | 20 |
| ON | 24 | 27 | 39 | 66 | 20 |
| SG | 48 | 14 | 23 | 23 | 23 |
| TW | 43 | 19 | 28 | 28 | 28 |

Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 2.°–8.°: `PRAC:analizar-datos-con-estadistica`, `PRAC:argumentar-con-evidencia`, `PRAC:ciencia-como-empresa-colectiva`, `PRAC:evaluar-fuentes-de-informacion`, `PRAC:evaluar-implicaciones-y-decidir`

## Conceptos que el vocabulario no tiene (propuestos para triaje)

El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.

| Propuesto | Países | Con núcleo |
|---|---|---|
| Seguridad eléctrica | EE, HK, KR, SG, TW | EE, HK, KR, SG, TW |
| Ciencia, tecnología y sociedad | EE, KR, ON, TW | EE, KR, ON, TW |
| Propiedades de los materiales | HK, ON, SG, TW | HK, ON, SG, TW |
| Contaminación acústica | HK, ON, TW | HK, ON, TW |
| Método científico | EE, HK, KR | EE, HK, KR |
| Naturaleza de la ciencia | EE, HK, TW | EE, HK, TW |

