# Biología · contraste internacional de 9.°–11.° (malla V2)

> Generado por `gskg internacional construir`. Método y límites: `specs/11_grafos_internacionales_9_11.md` y `internacional/README.md`.
> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para
> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.

## Resumen

| Clase | Conceptos | Qué significa |
|---|---|---|
| Faltantes del núcleo común | 0 | El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°. |
| No retomados en 9.°–11.° | 0 | La V2 solo lo ve antes de 9.°; al menos 5 países lo profundizan en su núcleo de 9.°–11.°. |
| Llegan tarde | 0 | La V2 lo introduce en 9.°–11.°, dos o más grados después de que el núcleo alcanza el consenso. |
| Nivel de especialización en un curso obligatorio | 7 | La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos. |
| Adelantados | 0 | La V2 lo introduce en 9.°–11.°, 1,5 grados o más antes que la mediana del núcleo de los países. |
| Sin referente | 2 | La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo. |
| Alineados | 13 | La V2 lo introduce en 9.°–11.° con un momento coherente con el consenso (± 1,5 grados). |
| Retomados | 104 | La V2 lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.° (espiral). |
| Solo antes de 9.° | 16 | La V2 lo ve antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°. |
| Inciertos (a revisión) | 10 | La lectura amplia y la estricta del etiquetado dan clases distintas: no se afirma nada hasta revisarlo (revision_clases.csv). |

Países con núcleo común por grado SV (denominador del consenso): 9.°: AU, EE, ENG, JP, KR, ON, SG, TW; 10.°: AU, EE, ENG, JP, KR, ON, SG, TW; 11.°: AU, EE, ENG, JP, KR, ON, SG, TW

Sensibilidad: con 4 países en lugar de 5, 2 conceptos más pasarían de «solo antes de 9.°» a «no retomados».

Revisión experta: 2 conceptos cambiaron de clase frente a la regla automática (`data/interim/internacional/revisiones.json`): Inmunidad adaptativa (solo_especializacion → alineado); Inmunidad innata (solo_especializacion → alineado).

Inciertos: 10 conceptos tienen clases distintas en la lectura amplia y en la estricta; no se afirma nada de ellos hasta revisarlos (`revision_clases.csv`, con las dos clases).

## Nivel de especialización en un curso obligatorio (7)

La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Regulación de la expresión génica | 9.°–11.° | 11.° (62% de los países con núcleo); 5 con núcleo en 9.°–11.° | AU esp., EE 8, ENG 8.5, HK esp., JP 9.5, KR 9, ON esp., SG 11, TW esp. | SV: G09-CIE-U10-10.3 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 10 - Genética y biotecno», fila 5)<br>AU · Senior Secondary Biology [esp.] (au_ss_bio, p. 4): «Comprender que la expresión génica diferencial controla la diferenciación celular para la formación de tejidos y los cambios estructurales durante el crecimiento.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 17): «Explicar la conexión entre el ADN, los genes y los cromosomas, y su papel en la herencia y la expresión de los genes.» |
| Secuenciación del ADN y perfiles genéticos | 9.°–11.° | mediana 8.5; 1 con núcleo en 9.°–11.° | AU esp., ENG 8.5, HK esp., JP esp., ON esp., SG esp., TW esp. | SV: G09-CIE-U11-11.1 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 11 - Evolución», fila 3)<br>AU · Senior Secondary Biology [esp.] (au_ss_bio, p. 1): «Comprender que la clasificación biológica es jerárquica y se basa en similitudes de características físicas, métodos de reproducción y secuencias moleculares.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 16): «Discutir la importancia potencial para la medicina de nuestra creciente comprensión del genoma humano.» |
| Glucólisis, ciclo de Krebs y cadena respiratoria | 10.° | mediana 11; 1 con núcleo en 9.°–11.° | ENG esp., HK esp., KR esp., ON esp., SG 11, TW esp. | SV: G10-BIO-U2-2.10 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 23)<br>ENG · A level Biology / Chemistry / Physics [esp.] (eng_alevel, p. 7): «Asociar la síntesis de ATP con la cadena de transferencia de electrones en las membranas de mitocondrias y cloroplastos.»<br>HK · HKDSE Biology (marco actualizado) [esp.] (hk_bio, p. 26): «Describir los pasos principales de la vía aeróbica: conversión de piruvato, ciclo de Krebs y fosforilación oxidativa para producir ATP en la mitocondria.» |
| Termorregulación | 10.° | mediana 8.25; 1 con núcleo en 9.°–11.° | AU esp., EE 8, ENG 8.5, HK esp., ON esp., SG esp. | SV: G10-BIO-U6-6.3 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 58)<br>AU · Senior Secondary Biology [esp.] (au_ss_bio4, p. 1): «Comprender los mecanismos de homeostasis que utilizan plantas y animales para controlar su entorno interno frente a cambios en el entorno externo.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 14): «Dar ejemplos de formas de sobrevivir a condiciones de vida adversas en animales de sangre caliente y fría.» |
| Nutrición mineral de las plantas | 11.° | mediana 6; 3 con núcleo en 9.°–11.° | EE 8, ENG 2, HK esp., JP 4, ON esp., SG 9.5 | SV: G11-BIO-U3-3.13 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 11.°», fila 42)<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 24): «Caracterizar las condiciones de crecimiento, cultivo y uso de ciertas plantas cultivadas utilizando fuentes de información.»<br>ENG · GCSE Combined Science [núcleo] (eng_gcse_comb, p. 11): «Explicar la absorción de agua e iones minerales en plantas, relacionando la estructura de las células de los pelos radiculares con su función.» |
| Capacidad de carga | 11.° | mediana 9; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., KR 9, ON esp., TW 7 | SV: G11-BIO-U7-7.3 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 11.°», fila 83)<br>AU · Senior Secondary Biology [esp.] (au_ss_bio, p. 2): «Reconocer que los ecosistemas tienen capacidades de carga que limitan las poblaciones y que estas pueden verse afectadas por cambios en factores bióticos, abióticos y climáticos.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 8): «Explica el desarrollo de la autorregulación en un ecosistema y los factores que la amenazan.» |
| Presión y flujo de fluidos en los seres vivos | 11.° | mediana 8.25; 1 con núcleo en 9.°–11.° | HK esp., ON esp., SG 9.5, TW 7 | SV: G11-BIO-U6-6.1 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 11.°», fila 75)<br>HK · HKDSE Biology (marco actualizado) [esp.] (hk_bio, p. 39): «Describir el mecanismo de ventilación, incluyendo la inhalación y la exhalación.»<br>ON · Biology, Grade 11 (SBI3U) [esp.] (on_sbi3u, p. 59): «Utilizar la terminología adecuada relacionada con la anatomía animal, incluyendo términos como sistólica, diastólica, gradiente de difusión, entre otros.» |

## Sin referente (2)

La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Adaptaciones fisiológicas | 10.°–11.° | mediana 8; 1 con núcleo en 9.°–11.° | AU esp., EE 8, ENG esp. | SV: G10-BIO-U7-7.5 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 10.°», fila 65)<br>AU · Senior Secondary Biology [esp.] (au_ss_bio4, p. 1): «Explicar cómo los cambios en la actividad metabólica, características estructurales, procesos fisiológicos y comportamiento permiten a un organismo mantener su entorno interno dentro de los límites de tolerancia.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 12): «Asociar las adaptaciones biológicas con las condiciones ambientales físicas y químicas.» |
| Equilibrio de Hardy-Weinberg | 11.° | —; 0 con núcleo en 9.°–11.° | SG esp., TW esp. | SV: G11-BIO-U5-5.3 (Matriz_Bachillerato_Biologia_10_11.xlsx, hoja «Biología 11.°», fila 65)<br>SG · A-Level H2 Biology [esp.] (sg_h2_bio, p. 16): «Usar la prueba de chi-cuadrado para evaluar la significancia de las diferencias entre los resultados observados y esperados.»<br>TW · 加深加廣選修: 生物、物理、化學、地球科學 [esp.] (tw_ele, p. 48): «Conocer la genética de poblaciones.» |

## Profundidad: demanda cognitiva en 9.°–11.°

Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: 65% (la diferencia principal: TIMSS pone «explicar» en aplicar).

| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 182 | 24% | 66% | 11% | 21 |
| EE | 172 | 3% | 51% | 46% | 21 |
| ENG | 112 | 31% | 63% | 6% | 12 |
| KR | 26 | 7% | 40% | 53% | 11 |
| ON | 17 | 7% | 47% | 47% | 2 |
| TW | 45 | 68% | 26% | 5% | 7 |

## Prácticas científicas en 9.°–11.°

La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.

| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 58 | 53 | 92 | 18 | 24 |
| EE | 13 | 14 | 110 | 36 | 20 |
| ENG | 16 | 21 | 49 | 9 | 16 |
| KR | 4 | 4 | 10 | 6 | 9 |
| ON | 6 | 3 | 7 | 6 | 12 |
| TW | 3 | 0 | 11 | 9 | 16 |

Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 9.°–11.°: ninguna.

## Conceptos que el vocabulario no tiene (propuestos para triaje)

El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.

| Propuesto | Países | Con núcleo |
|---|---|---|
| Bioética | EE, ENG, HK, KR, ON, SG, TW | EE, ENG, KR |
| Naturaleza de la ciencia | AU, EE, ENG, HK, KR, ON, TW | EE, ENG, TW |
| Arco reflejo | EE, ENG, KR, SG | EE, ENG, KR |
| Cáncer | ENG, HK, ON, SG | ENG, ON |
| Metabolismo | EE, HK, KR | EE, KR |
| Células madre | EE, ENG, KR, ON, SG | ON |
| Historia de la ciencia | AU, KR, ON, TW | TW |
| Servicios ecosistémicos | EE, HK, ON, SG | EE |
| Biotecnología | HK, KR, TW | TW |
| Clonación | EE, HK, ON | ON |
| Código genético | EE, HK, KR | EE |
| Determinación cromosómica del sexo | ENG, SG, TW | TW |
| Factores limitantes | ENG, HK, SG | ENG |
| Regulación de la glucosa | ENG, JP, SG | ENG |
| Tecnologías de reproducción asistida | ENG, ON, TW | ENG |

