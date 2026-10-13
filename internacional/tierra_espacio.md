# Ciencias de la Tierra y del Espacio · contraste internacional de 9.°–11.° (malla V2)

> Generado por `gskg internacional construir`. Método y límites: `specs/11_grafos_internacionales_9_11.md` y `internacional/README.md`.
> Los datos de los países los extrajo y validó Gemini (Vertex AI, proyecto GOES), con un modelo para
> extraer y otro para validar. Las clases dependen de etiquetas de IA y requieren revisión del MINED.

## Resumen

| Clase | Conceptos | Qué significa |
|---|---|---|
| Faltantes del núcleo común | 0 | El consenso (≥ 5 países) lo enseña a todos los estudiantes hasta ese grado; la V2 no lo tiene en 2.°–11.°. |
| No retomados en 9.°–11.° | 0 | La V2 solo lo ve antes de 9.°; al menos 5 países lo profundizan en su núcleo de 9.°–11.°. |
| Llegan tarde | 0 | La V2 lo introduce en 9.°–11.°, dos o más grados después de que el núcleo alcanza el consenso. |
| Nivel de especialización en un curso obligatorio | 0 | La V2 lo introduce en 9.°–11.°, pero los países solo lo enseñan en cursos electivos. |
| Adelantados | 0 | La V2 lo introduce en 9.°–11.°, 1,5 grados o más antes que la mediana del núcleo de los países. |
| Sin referente | 3 | La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo. |
| Alineados | 1 | La V2 lo introduce en 9.°–11.° con un momento coherente con el consenso (± 1,5 grados). |
| Retomados | 43 | La V2 lo introduce antes de 9.° y lo vuelve a trabajar en 9.°–11.° (espiral). |
| Solo antes de 9.° | 28 | La V2 lo ve antes de 9.° y el núcleo internacional no lo exige en 9.°–11.°. |
| Inciertos (a revisión) | 0 | La lectura amplia y la estricta del etiquetado dan clases distintas: no se afirma nada hasta revisarlo (revision_clases.csv). |

Países con núcleo común por grado SV (denominador del consenso): 9.°: AU, EE, ENG, JP, KR, ON, SG, TW; 10.°: AU, EE, ENG, JP, KR, ON, SG, TW; 11.°: AU, EE, ENG, JP, KR, ON, SG, TW

Sensibilidad: con 4 países en lugar de 5, 4 conceptos más pasarían de «solo antes de 9.°» a «no retomados».

Revisión experta: 7 conceptos cambiaron de clase frente a la regla automática (`data/interim/internacional/revisiones.json`): Convección del manto y energía interna de la Tierra (incierto → no_aplica); Calentamiento global (incierto → retomado); Capas de la atmósfera y variación con la altitud (incierto → retomado); La atmósfera y su composición (incierto → retomado); Efecto invernadero (incierto → retomado); Acidificación del océano (incierto → sin_referente); Oleaje, dinámica costera y sedimentación marina (alineado → sin_referente).

## Sin referente (3)

La V2 lo enseña en 9.°–11.° y menos de 3 países lo tienen en su núcleo: no hay referente para fecharlo.

| Concepto | Grados SV (V2) | Consenso del núcleo | Países (grado de 1.ª aparición; esp. = solo electiva) | Evidencia |
|---|---|---|---|---|
| Acidificación del océano | 7.°–10.° | mediana 8.75; 1 con núcleo en 9.°–11.° | EE 10.5, HK 7 | SV: G07-CIE-U6-6.15 (Matriz_Ciencias_7mo_Grado_U1_U6.xlsx, hoja «Unidad 6 - Ambiente y energía», fila 17)<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 16): «Analiza los cambios ocurridos en el océano mundial, relacionándolos con el cambio climático y la actividad humana.»<br>Revisión experta: El «retomado» solo se apoya en una etiqueta secundaria suelta sobre la fila de 7.° (6.15), que no nombra el océano ni la acidificación: no hay mención lateral. La V2 la introduce en 9.° (4.17) y la retoma en 10.° Química. En los países solo es explícita en SG H1 (núcleo parcial, 11.°) y en electivas (AU, SG H2): menos de 3 núcleos. No es un exceso que retirar. |
| Oleaje, dinámica costera y sedimentación marina | 4.°–9.° | mediana 4.5; 2 con núcleo en 9.°–11.° | EE 10.5, ENG esp., JP esp., KR 2.5, TW 4.5 | SV: G04-CIE-U3-3.10 (Matriz_Ciencias_4to_Grado_U1_U6.xlsx, hoja «Unidad 3 - Naturaleza y sus int», fila 12)<br>EE · Gymnasium, cursos obligatorios [núcleo] (ee_gym, p. 16): «Explica los procesos costeros y analiza el impacto de la actividad humana en la costa con un ejemplo regional.»<br>ENG · A level Geology [esp.] (eng_alevel_geo, p. 6): «Explicar mediante modelos científicos los procesos sedimentarios infrecuentes o difíciles de observar, como las corrientes de turbidez, aplicando el uniformismo.»<br>Revisión experta: Cambio a sin_referente. En 4.° «oleaje» solo figura en la lista de manifestaciones del ciclón; indicador, producto y actividades tratan su formación y la alerta, sin trabajar olas ni costa. La mención lateral sirve para no afirmar ausencias, no para declarar una espiral: 9.° 4.8 lo introduce desde la definición. Con solo EE y TW en núcleo no hay referente para fecharlo; 9.° queda entre ambos. |
| Vulcanismo de El Salvador | 4.°–10.° | —; 0 con núcleo en 9.°–11.° |  | SV: G04-CIE-U3-3.14 (Matriz_Ciencias_4to_Grado_U1_U6.xlsx, hoja «Unidad 3 - Naturaleza y sus int», fila 16) |

## Profundidad: demanda cognitiva en 9.°–11.°

Mismo clasificador por verbos (escala TIMSS) para la V2 y para el núcleo de cada país; los enunciados sin verbo reconocible no entran en el porcentaje. Coincidencia del clasificador con la etiqueta de Gemini: 65% (la diferencia principal: TIMSS pone «explicar» en aplicar).

| Currículo | Enunciados | Recordar | Aplicar | Razonar | Sin verbo |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 27 | 58% | 42% | 0% | 1 |
| EE | 107 | 10% | 45% | 46% | 15 |
| ENG | 5 | 60% | 20% | 20% | 0 |
| KR | 19 | 9% | 18% | 73% | 8 |
| ON | 23 | 30% | 25% | 45% | 3 |
| TW | 42 | 53% | 33% | 14% | 6 |

## Prácticas científicas en 9.°–11.°

La V2 trae una columna procedimental en cada fila y los países separan prácticas de contenidos, así que la proporción de enunciados con práctica no es comparable. Se compara la cobertura del catálogo.

| Currículo | Indagación | Modelación | Argumentación | Naturaleza y contexto | Prácticas distintas |
|---|---|---|---|---|---|
| **El Salvador (V2)** | 10 | 6 | 14 | 1 | 13 |
| EE | 23 | 15 | 62 | 22 | 20 |
| ENG | 1 | 0 | 5 | 1 | 6 |
| KR | 5 | 1 | 9 | 3 | 11 |
| ON | 6 | 6 | 7 | 3 | 14 |
| TW | 7 | 1 | 12 | 2 | 8 |

Prácticas que exige el núcleo de ≥ 5 países y la V2 no nombra en 9.°–11.°: ninguna.

## Conceptos que el vocabulario no tiene (propuestos para triaje)

El vocabulario nació de la malla salvadoreña, así que un contenido que El Salvador no enseña puede no existir en él. Estos nombres los propuso el etiquetado en ≥ 3 países.

| Propuesto | Países | Con núcleo |
|---|---|---|
| Geología regional | EE, ENG, JP, TW | EE, TW |
| Naturaleza de la ciencia | AU, EE, ENG, KR | EE |
| Corrimiento al rojo | EE, ENG, KR | KR |
| Mapas meteorológicos | EE, KR, TW | EE |
| Marejada ciclónica | JP, KR, TW | TW |
| Estratigrafía | AU, ENG, JP, KR, ON, TW | — |
| Datación radiométrica | AU, ENG, JP, ON | — |
| Paleomagnetismo | AU, ENG, JP, ON | — |
| Teledetección | AU, EE, ENG, TW | — |
| Espectroscopía | EE, KR, ON | — |
| Estructura a gran escala del universo | EE, JP, KR | — |
| Isostasia | JP, ON, TW | — |
| Leyes de Kepler | JP, KR, ON | — |
| Medición de distancias astronómicas | KR, ON, TW | — |
| Metamorfismo | JP, KR, TW | — |

