# Física · contraste internacional de 9.°–11.° (malla V2)

> Generado por `gskg internacional construir`. Método y límites: `specs/11_grafos_internacionales_9_11.md` y `internacional/README.md`.
> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para
> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.

## Resumen

| Clase | Conceptos | Qué significa |
|---|---|---|
| Faltantes del núcleo común | 0 | El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°. |
| No retomados en 9.°–11.° | 0 | La V2 solo lo ve antes de 9.°; al menos 5 países lo profundizan en su núcleo de 9.°–11.°. |
| Llegan tarde | 0 | La V2 lo introduce en 9.°–11.°, dos o más grados después de que el núcleo alcanza el consenso. |
| Nivel de especialización en un curso obligatorio | 8 | La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos. |
| Adelantados | 0 | La V2 lo introduce en 9.°–11.°, 1,5 grados o más antes que la mediana del núcleo de los países. |
| Sin referente | 6 | La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo. |
| Alineados | 24 | La V2 lo introduce en 9.°–11.° con un momento coherente con el consenso (± 1,5 grados). |
| Retomados | 82 | La V2 lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.° (espiral). |
| Solo antes de 9.° | 3 | La V2 lo ve antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°. |
| Inciertos (a revisión) | 18 | La lectura amplia y la estricta del etiquetado dan clases distintas: no se afirma nada hasta revisarlo (revision_clases.csv). |

Países con núcleo común por grado SV (denominador del consenso): 9.°: AU, EE, ENG, JP, KR, ON, SG, TW; 10.°: AU, EE, ENG, JP, KR, ON, SG, TW; 11.°: AU, EE, ENG, JP, KR, ON, SG, TW

Sensibilidad: con 4 países en lugar de 5, 1 conceptos más pasarían de «solo antes de 9.°» a «no retomados».

Revisión experta: 4 conceptos cambiaron de clase frente a la regla automática (`data/interim/internacional/revisiones.json`): Relaciones presión-volumen-temperatura en gases (solo_especializacion → alineado); Superposición e interferencia de ondas (solo_especializacion → alineado); Absorción de radiación y efecto invernadero (incierto → retomado); La energía y sus usos (incierto → retomado).

Inciertos: 18 conceptos tienen clases distintas en la lectura amplia y en la estricta; no se afirma nada de ellos hasta revisarlos (`revision_clases.csv`, con las dos clases).

## Nivel de especialización en un curso obligatorio (8)

La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Fuerza magnética sobre cargas en movimiento | 11.° | mediana 10.75; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG 11, TW esp. | SV: G11-FIS-U10-10.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 59)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 4): «Comprender que el movimiento en campos gravitatorios, eléctricos y magnéticos puede explicarse utilizando las leyes del movimiento de Newton.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 11): «Visualiza el campo magnético con líneas de fuerza y determina la dirección de la fuerza de Lorentz sobre cargas móviles.» |
| Fuerza electromotriz y leyes de Kirchhoff | 11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., ON esp., SG 9.5, TW esp. | SV: G11-FIS-U9-9.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 46)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 2): «El análisis y diseño de circuitos implica calcular la diferencia de potencial, la corriente y la potencia suministrada a componentes en circuitos en serie, paralelo y mixtos.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 12): «Diseña y realiza un experimento para determinar la fuerza electromotriz y resistencia interna de una fuente, analizando resultados.» |
| Defecto de masa y energía de enlace nuclear | 11.° | mediana 9.25; 4 con núcleo en 9.°–11.° | AU esp., EE 8, ENG esp., HK esp., JP esp., KR 9, SG 11, TW 9.5 | SV: G11-FIS-U20-20.3 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 123)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 2): «La fusión nuclear libera más energía por nucleón que la fisión porque un mayor porcentaje de la masa se transforma en energía.»<br>EE · Escuela básica, III etapa (grados 7–9) [núcleo] (ee_basic, p. 21): «Explicar el valor práctico de la fusión y fisión nucleares.» |
| Polarización de la luz | 10.°–11.° | mediana 10.5; 1 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., KR esp., ON esp., SG esp. | SV: G10-FIS-U16-16.2 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 113)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 4): «Explicar fenómenos luminosos con un modelo ondulatorio (reflexión, refracción, dispersión, difracción, interferencia), y usar un modelo de onda transversal para explicar la polarización.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 12): «Relaciona las propiedades de la luz polarizada con sus aplicaciones en la naturaleza y la tecnología.» |
| Radiación térmica y cuerpo negro | 10.°–11.° | mediana 8.25; 1 con núcleo en 9.°–11.° | AU esp., EE esp., ENG esp., HK esp., KR 7, SG 9.5, TW esp. | SV: G10-FIS-U13-13.3 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 96)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis4, p. 1): «Comprender cómo la teoría cuántica explica la radiación de cuerpo negro, el efecto fotoeléctrico y los espectros atómicos de emisión y absorción.»<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 44): «Describir la generación de radiación, emisión espontánea y estimulada, láseres, espectros continuos y de líneas, análisis espectral y tipos de luz (IR, UV, rayos X).» |
| Relatividad especial | 11.° | —; 0 con núcleo en 9.°–11.° | AU esp., EE esp., HK esp., KR esp., ON esp. | SV: G11-FIS-U19-19.1 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 11.°», fila 116)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis4, p. 1): «Comprender las consecuencias para el espacio y el tiempo del principio de equivalencia para marcos de referencia inerciales.»<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 44): «Conocer la teoría de la relatividad: relatividad del tiempo y longitud, suma de velocidades, dependencia de la masa, equivalencia de masa y espacio-tiempo curvo.» |
| Procesos termodinámicos | 9.°–10.° | mediana 10.5; 1 con núcleo en 9.°–11.° | EE 10.5, JP esp., KR esp., SG esp. | SV: G09-CIE-U2-2.4 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 2 - Calor y temperatura», fila 6)<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 12): «Utiliza gráficos de isoprocesos para analizar procesos termodinámicos.»<br>JP · 物理 (Física) [esp.] (jp_35, p. 111): «Realizar experimentos sobre cambios de estado de un gas para comprender la relación entre calor, trabajo y energía interna.» |
| Viscosidad y régimen de flujo | 9.°–11.° | —; 0 con núcleo en 9.°–11.° | EE esp., HK esp., SG esp. | SV: G09-CIE-U1-1.10 (Matriz_Ciencias_9no_Grado_U1_U12.xlsx, hoja «Unidad 1 - Mecánica de fluidos», fila 12)<br>EE · Gymnasium, electivos de ciencias [esp.] (ee_gym_ele, p. 31): «Conocer la aerodinámica y fluidodinámica: fuerzas de resistencia, fuerzas en aeronaves, flujo en tuberías, circulación sanguínea (presión diastólica y sistólica) y turbinas hidráulicas.»<br>HK · HKDSE Physics (marco actualizado) [esp.] (hk_fis, p. 56): «Demostrar el efecto Coanda en superficies curvas bajo un fluido en movimiento, como viento sobre una taza o una cuchara bajo agua.» |

## Sin referente (6)

La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Difracción de ondas y de la luz | 10.°–11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG esp., TW 9.5 | SV: G10-FIS-U16-16.2 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 113)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 4): «Explicar fenómenos luminosos con un modelo ondulatorio (reflexión, refracción, dispersión, difracción, interferencia), y usar un modelo de onda transversal para explicar la polarización.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 11): «Aplica simulaciones para investigar reflexión, interferencia y difracción de ondas, dando ejemplos naturales y tecnológicos.» |
| Dualidad onda-partícula | 10.°–11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG esp., TW 9.5 | SV: G10-FIS-U16-16.7 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 118)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis4, p. 1): «Evaluar la evidencia experimental que apoya la relatividad, la dualidad onda-partícula, el modelo de Bohr, el Modelo Estándar y el Big Bang.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 12): «Explica la formación de espectros de líneas y la dualidad onda-partícula de la luz, ejemplificando el análisis espectral.» |
| Fotón y efecto fotoeléctrico | 10.°–11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG esp., TW 9.5 | SV: G10-QUI-U3-3.5 (Matriz_Bachillerato_Quimica_10_11.xlsx, hoja «Química 10.°», fila 27)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis4, p. 1): «Comprender cómo la teoría cuántica explica la radiación de cuerpo negro, el efecto fotoeléctrico y los espectros atómicos de emisión y absorción.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 12): «Explica la formación de espectros de líneas y la dualidad onda-partícula de la luz, ejemplificando el análisis espectral.» |
| Interferencia de la luz | 10.°–11.° | mediana 10; 2 con núcleo en 9.°–11.° | AU esp., EE 10.5, ENG esp., HK esp., JP esp., KR esp., ON esp., SG esp., TW 9.5 | SV: G10-FIS-U16-16.2 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 113)<br>AU · Senior Secondary Physics [esp.] (au_ss_fis, p. 4): «Explicar fenómenos luminosos con un modelo ondulatorio (reflexión, refracción, dispersión, difracción, interferencia), y usar un modelo de onda transversal para explicar la polarización.»<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 11): «Aplica simulaciones para investigar reflexión, interferencia y difracción de ondas, dando ejemplos naturales y tecnológicos.» |
| Momento angular y su conservación | 10.° | —; 0 con núcleo en 9.°–11.° | HK esp., TW esp. | SV: G10-FIS-U10-10.6 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 72)<br>HK · HKDSE Physics (marco actualizado) [esp.] (hk_fis, p. 67): «Distinguir entre aspectos cuánticos y clásicos en la cuantización de niveles de energía del modelo de Bohr.»<br>TW · 加深加廣選修: 生物、物理、化學、地球科學 [esp.] (tw_ele, p. 50): «Definir el momento angular como el producto cruz de la posición y el momento lineal, y su tasa de cambio como el torque aplicado.» |
| Movimiento circular uniformemente acelerado | 10.° | —; 0 con núcleo en 9.°–11.° |  | SV: G10-FIS-U9-9.2 (Matriz_Bachillerato_Fisica_10_11.xlsx, hoja «Física 10.°», fila 61) |

## Profundidad: demanda cognitiva en 9.°–11.°

Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: 65% (la diferencia principal: TIMSS pone «explicar» en aplicar).

| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 308 | 7% | 83% | 10% | 19 |
| EE | 147 | 4% | 62% | 34% | 5 |
| ENG | 111 | 25% | 69% | 7% | 5 |
| KR | 82 | 14% | 43% | 43% | 17 |
| ON | 32 | 22% | 41% | 37% | 5 |
| TW | 100 | 38% | 37% | 24% | 14 |

## Prácticas científicas en 9.°–11.°

La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.

| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 90 | 204 | 104 | 23 | 26 |
| EE | 36 | 58 | 53 | 16 | 25 |
| ENG | 22 | 43 | 25 | 10 | 22 |
| KR | 36 | 10 | 31 | 26 | 25 |
| ON | 15 | 8 | 9 | 9 | 19 |
| TW | 32 | 22 | 25 | 20 | 27 |

Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 9.°–11.°: ninguna.

## Conceptos que el vocabulario no tiene (propuestos para triaje)

El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.

| Propuesto | Países | Con núcleo |
|---|---|---|
| Seguridad eléctrica | EE, ENG, ON, SG, TW | EE, ENG, TW |
| Ciencia, Tecnología y Sociedad (CTS) | EE, ENG, KR | EE, ENG, KR |
| Método científico | EE, KR, TW | EE, KR, TW |
| Ciencia, tecnología y sociedad | AU, EE, JP, KR, ON | KR, ON |
| Naturaleza de la ciencia | AU, EE, HK, KR, ON | EE, KR |
| Carreras científicas | KR, ON, TW | KR, ON |
| Resonancia | AU, EE, HK, ON, TW | EE |
| Resistividad | EE, ENG, HK, SG | EE |
| Corriente continua | EE, ON, TW | EE |
| Energía interna | HK, SG, TW | TW |
| Relatividad general | AU, EE, HK, KR, ON | — |
| Flujo magnético | AU, HK, SG, TW | — |
| Campo gravitatorio | AU, HK, SG | — |
| Historia de la física | AU, HK, ON | — |
| Modelo atómico de Rutherford | HK, SG, TW | — |

