# Propuestas curriculares (borrador) · resumen

Borradores por asignatura y ciclo, generados con el grafo de conocimiento (spec 06). Estado: **borrador**, pendiente de la revisión del equipo de Ciencias del MINED. Ninguno quita temas y todos conservan el total de su ciclo.

**Malla V2.** Las propuestas se escribieron sobre la V1 (2026-10-05). La V2 del MINED (2026-10-07) conserva la V1 y agrega 47 temas, varios de ellos acciones «nuevo» de estas propuestas. La simulación corre sobre la V2: el «antes» ya incluye lo que el MINED adoptó y las acciones adoptadas en el mismo grado no se vuelven a aplicar. La conciliación acción por acción está al final.

**Verificación:** `gskg propuesta simular` aplica las acciones sobre el grafo (mover, fusionar, crear, reformular, dividir y retirar etiquetas que un tema reformulado deja de trabajar), recalcula el diagnóstico y compara antes y después. También aplica las etiquetas que retiran las propuestas de otras asignaturas del mismo ciclo (p. ej., Biología 10.° deja de tratar la química de los carbohidratos):

- *Errores de secuencia (alta)*: prerrequisitos de confianza alta que la malla enseña después del concepto que los necesita. Los que quedan son decisiones abiertas en cada informe.
- *Llegan ≥2 grados tarde*: conceptos del ciclo que El Salvador introduce dos o más grados después que la mediana de los seis países del grafo (Uruguay, Colombia, Singapur, Inglaterra, Australia y Japón), con grados equivalentes por edad. No aplica (n/a) en 10.°–11.°, porque los currículos de los países en el grafo llegan solo a 9.°.
- *Desfase medio*: promedio de |grado SV − mediana de países| de los conceptos comparables del ciclo.

- *Ya en la V2*: de las acciones «nuevo», cuántas adoptó el MINED en el mismo grado + en otro grado + en parte.

| Asignatura | Ciclo | Acciones | Ya en la V2 | Errores de secuencia (alta) | Llegan ≥2 grados tarde | Desfase medio | Documentos |
|---|---|---|---|---|---|---|---|
| Biología | 2.°–4.° | 14 (fusionar 1, mover 2, nuevo 1, revisar 10) | 0 + 0 + 0 de 1 | 5 → **0** | 6 → **3** | 2.24 → **1.96** | [informe](biologia/propuesta/informe_G02-G04.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G02-G04.xlsx) |
| Biología | 5.°–8.° | 19 (dividir 1, fusionar 5, mover 6, nuevo 6, revisar 1) | 0 + 4 + 1 de 6 | 3 → **1** | 12 → **5** | 1.88 → **1.64** | [informe](biologia/propuesta/informe_G05-G08.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G05-G08.xlsx) |
| Biología | 10.°–11.° | 21 (fusionar 8, mover 2, nuevo 8, revisar 3) | 0 + 0 + 3 de 8 | 1 → **1** | n/a | n/a | [informe](biologia/propuesta/informe_G10-G11.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G10-G11.xlsx) |
| Tierra y Espacio | 2.°–4.° | 9 (fusionar 3, nuevo 3, revisar 3) | 1 + 0 + 1 de 3 | 10 → **1** | 3 → **1** | 2.04 → **1.88** | [informe](ciencias_tierra_espacio/propuesta/informe_G02-G04.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G02-G04.xlsx) |
| Tierra y Espacio | 5.°–8.° | 17 (fusionar 4, mover 7, nuevo 4, revisar 2) | 0 + 3 + 1 de 4 | 6 → **1** | 4 → **5** | 2.17 → **2.01** | [informe](ciencias_tierra_espacio/propuesta/informe_G05-G08.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G05-G08.xlsx) |
| Física | 2.°–4.° | 19 (dividir 1, fusionar 5, nuevo 5, revisar 8) | 4 + 0 + 0 de 5 | 4 → **0** | 6 → **5** | 1.92 → **1.55** | [informe](fisica/propuesta/informe_G02-G04.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G02-G04.xlsx) |
| Física | 5.°–8.° | 21 (fusionar 7, mover 3, nuevo 7, revisar 4) | 0 + 1 + 2 de 7 | 8 → **1** | 18 → **13** | 2.13 → **1.73** | [informe](fisica/propuesta/informe_G05-G08.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G05-G08.xlsx) |
| Física | 10.°–11.° | 10 (mover 2, revisar 8) | — | 3 → **0** | n/a | n/a | [informe](fisica/propuesta/informe_G10-G11.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G10-G11.xlsx) |
| Química | 2.°–4.° | 3 (mover 1, revisar 2) | — | 2 → **0** | 0 → **1** | 2.37 → **2.5** | [informe](quimica/propuesta/informe_G02-G04.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G02-G04.xlsx) |
| Química | 5.°–8.° | 19 (fusionar 8, mover 1, nuevo 8, revisar 2) | 0 + 0 + 0 de 8 | 8 → **0** | 11 → **2** | 2.3 → **1.76** | [informe](quimica/propuesta/informe_G05-G08.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G05-G08.xlsx) |
| Química | 10.°–11.° | 19 (dividir 1, fusionar 6, mover 1, nuevo 5, revisar 6) | 0 + 0 + 0 de 5 | 5 → **0** | n/a | n/a | [informe](quimica/propuesta/informe_G10-G11.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G10-G11.xlsx) |

Notas:
- **Tierra y Espacio 5.°–8.°** casi no reduce los conceptos que llegan tarde: a propósito mueve la unidad del espacio de 5.° a 6.° para que la gravedad y las órbitas vayan antes.
- Las propuestas de 2.°–8.° usan los 6 países (Singapur, Inglaterra, Australia y Japón son de alto desempeño); las de 10.°–11.° se basan en los marcos (ACARA y TIMSS Advanced).
- Los errores de secuencia que quedan se explican en cada informe (introducciones cualitativas o etiquetas por revisar). Cada informe lista sus **decisiones abiertas para el MINED**.
- Las propuestas de un ciclo afectan a los siguientes (por ejemplo, si un tema baja a 5.°, el de 9.° debe profundizar). Coordinarlas es parte de la revisión (ver `HANDOFF.md`).

## Acciones que la V2 ya incorporó

Conciliación de cada acción «nuevo» con los 47 temas que agregó la V2 (juicio de especialista IA, `data/interim/propuestas/adopcion_v2.json`; pendiente de confirmar con el MINED). Las demás acciones siguen pendientes.

| Propuesta | Acción | Grado propuesto | Tema propuesto | Estado | Tema de la V2 | Confianza |
|---|---|---|---|---|---|---|
| Biología 5.°–8.° | 9 | 6.° | 5.24. Comparación de la célula animal y la célula vegetal mediante observación al microsco | adoptada otro grado | G09-CIE-U8-8.1 | media |
| Biología 5.°–8.° | 11 | 6.° | 5.26. Explicación de los ciclos del carbono y del oxígeno a partir de la fotosíntesis y la | parcial | G08-CIE-U10-10.1, G09-CIE-U12-12.1 | media |
| Biología 5.°–8.° | 15 | 8.° | 7.16. Explicación de la homeostasis y de la regulación hormonal del medio interno. | adoptada otro grado | G09-CIE-U9-9.3 | alta |
| Biología 5.°–8.° | 16 | 5.° | 6.5. Explicación de los fósiles y de la comparación de estructuras como evidencias de los  | adoptada otro grado | G09-CIE-U11-11.1 | media |
| Biología 5.°–8.° | 18 | 5.° | 8.4. Descripción de la herencia de rasgos de progenitores a descendientes en plantas y ani | adoptada otro grado | G03-CIE-U5-5.14 | alta |
| Biología 10.°–11.° | 5 | 10.° | 9.3. Experimentación con la difusión y la ósmosis y con los factores que modifican el inte | parcial | G09-CIE-U8-8.2 | media |
| Biología 10.°–11.° | 12 | 11.° | 2.16. Análisis de la transmisión y la propagación regional y global de las enfermedades in | parcial | G09-CIE-U9-9.2 | media |
| Biología 10.°–11.° | 14 | 10.° | 4.8. Simulación de la PCR y de la electroforesis en gel para obtener perfiles de ADN. | parcial | G09-CIE-U10-10.2 | baja |
| Tierra y Espacio 2.°–4.° | 4 | 3.° | 2.8. Exploración de la meteorización, la erosión y la sedimentación de las rocas y de la f | parcial | G08-CIE-U5-5.10, G08-CIE-U9-9.3 | media |
| Tierra y Espacio 2.°–4.° | 6 | 3.° | 2.16. Medición y registro de las variables del tiempo atmosférico con instrumentos sencill | adoptada | G03-CIE-U2-2.17 | alta |
| Tierra y Espacio 5.°–8.° | 1 | 6.° | 7.1. Explicación de la gravedad como la fuerza que forma estrellas y planetas y mantiene s | adoptada otro grado | G08-CIE-U8-8.8 | media |
| Tierra y Espacio 5.°–8.° | 5 | 6.° | 7.7. Explicación de las fases de la Luna, los eclipses y las mareas a partir de los movimi | adoptada otro grado | G08-CIE-U8-8.4 | media |
| Tierra y Espacio 5.°–8.° | 8 | 7.° | 5.19. Explicación del calentamiento desigual de la Tierra y de su efecto en los vientos y  | parcial | G08-CIE-U10-10.3 | media |
| Tierra y Espacio 5.°–8.° | 13 | 7.° | 6.21. Modelación del ciclo del carbono entre la atmósfera, la biosfera, la hidrosfera y la | adoptada otro grado | G08-CIE-U10-10.1 | alta |
| Física 2.°–4.° | 1 | 3.° | 7.1. Medición con termómetro de la temperatura de objetos que se calientan o se enfrían. | adoptada | G03-CIE-U1-1.8 | alta |
| Física 2.°–4.° | 2 | 3.° | 1.7. Experimentación con imanes: polos, atracción y repulsión. | adoptada | G03-CIE-U1-1.7 | alta |
| Física 2.°–4.° | 4 | 4.° | 7.1. Experimentación con la reflexión de la luz en espejos y superficies brillantes. | adoptada | G04-CIE-U1-1.14 | alta |
| Física 2.°–4.° | 5 | 4.° | 1.9. Clasificación de materiales en conductores y aislantes y construcción de circuitos el | adoptada | G04-CIE-U1-1.11, G04-CIE-U1-1.15 | alta |
| Física 5.°–8.° | 2 | 5.° | 10.1. Construcción de un circuito eléctrico simple y clasificación experimental de materia | adoptada otro grado | G04-CIE-U1-1.11, G04-CIE-U1-1.15 | alta |
| Física 5.°–8.° | 4 | 5.° | 10.2. Experimentación con la reflexión de la luz y la formación de imágenes en espejos pla | parcial | G04-CIE-U1-1.14, G07-CIE-U6-6.21 | media |
| Física 5.°–8.° | 16 | 7.° | 8.6. Experimentación con la refracción de la luz y la formación de imágenes con lentes con | parcial | G07-CIE-U6-6.21 | media |
