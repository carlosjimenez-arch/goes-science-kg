# Propuestas curriculares (borrador) · resumen

Borradores por asignatura y ciclo, generados con el grafo de conocimiento (spec 06). Estado: **borrador**, pendiente de la revisión del equipo de Ciencias del MINED. Ninguno quita temas y todos conservan el total de su ciclo.

**Verificación:** `gskg propuesta simular` aplica las acciones sobre el grafo (mover, fusionar, crear, reformular, dividir y retirar etiquetas que un tema reformulado deja de trabajar), recalcula el diagnóstico y compara antes y después. También aplica las etiquetas que retiran las propuestas de otras asignaturas del mismo ciclo (p. ej., Biología 10.° deja de tratar la química de los carbohidratos):

- *Errores de secuencia (alta)*: prerrequisitos de confianza alta que la malla enseña después del concepto que los necesita. Los que quedan son decisiones abiertas en cada informe.
- *Llegan ≥2 grados tarde*: conceptos del ciclo que El Salvador introduce dos o más grados después que la mediana de los seis países del grafo (Uruguay, Colombia, Singapur, Inglaterra, Australia y Japón), con grados equivalentes por edad. No aplica (n/a) en 10.°–11.°, porque los currículos de los países en el grafo llegan solo a 9.°.
- *Desfase medio*: promedio de |grado SV − mediana de países| de los conceptos comparables del ciclo.

| Asignatura | Ciclo | Acciones | Errores de secuencia (alta) | Llegan ≥2 grados tarde | Desfase medio | Documentos |
|---|---|---|---|---|---|---|
| Biología | 2.°–4.° | 14 (fusionar 1, mover 2, nuevo 1, revisar 10) | 5 → **0** | 6 → **3** | 2.27 → **1.99** | [informe](biologia/propuesta/informe_G02-G04.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G02-G04.xlsx) |
| Biología | 5.°–8.° | 19 (dividir 1, fusionar 5, mover 6, nuevo 6, revisar 1) | 3 → **1** | 16 → **6** | 1.99 → **1.64** | [informe](biologia/propuesta/informe_G05-G08.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G05-G08.xlsx) |
| Biología | 10.°–11.° | 21 (fusionar 8, mover 2, nuevo 8, revisar 3) | 0 → **0** | n/a | n/a | [informe](biologia/propuesta/informe_G10-G11.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G10-G11.xlsx) |
| Tierra y Espacio | 2.°–4.° | 9 (fusionar 3, nuevo 3, revisar 3) | 10 → **0** | 4 → **1** | 2.13 → **1.83** | [informe](ciencias_tierra_espacio/propuesta/informe_G02-G04.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G02-G04.xlsx) |
| Tierra y Espacio | 5.°–8.° | 17 (fusionar 4, mover 7, nuevo 4, revisar 2) | 5 → **1** | 6 → **6** | 2.24 → **1.98** | [informe](ciencias_tierra_espacio/propuesta/informe_G05-G08.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G05-G08.xlsx) |
| Física | 2.°–4.° | 19 (dividir 1, fusionar 5, nuevo 5, revisar 8) | 4 → **0** | 10 → **5** | 2.42 → **1.55** | [informe](fisica/propuesta/informe_G02-G04.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G02-G04.xlsx) |
| Física | 5.°–8.° | 21 (fusionar 7, mover 3, nuevo 7, revisar 4) | 9 → **1** | 22 → **16** | 2.26 → **1.76** | [informe](fisica/propuesta/informe_G05-G08.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G05-G08.xlsx) |
| Física | 10.°–11.° | 10 (mover 2, revisar 8) | 3 → **0** | n/a | n/a | [informe](fisica/propuesta/informe_G10-G11.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G10-G11.xlsx) |
| Química | 2.°–4.° | 3 (mover 1, revisar 2) | 2 → **0** | 0 → **1** | 2.37 → **2.5** | [informe](quimica/propuesta/informe_G02-G04.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G02-G04.xlsx) |
| Química | 5.°–8.° | 19 (fusionar 8, mover 1, nuevo 8, revisar 2) | 8 → **0** | 11 → **2** | 2.3 → **1.76** | [informe](quimica/propuesta/informe_G05-G08.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G05-G08.xlsx) |
| Química | 10.°–11.° | 19 (dividir 1, fusionar 6, mover 1, nuevo 5, revisar 6) | 5 → **0** | n/a | n/a | [informe](quimica/propuesta/informe_G10-G11.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G10-G11.xlsx) |

Notas:
- **Tierra y Espacio 5.°–8.°** casi no reduce los conceptos que llegan tarde: a propósito mueve la unidad del espacio de 5.° a 6.° para que la gravedad y las órbitas vayan antes.
- Las propuestas de 2.°–8.° usan los 6 países (Singapur, Inglaterra, Australia y Japón son de alto desempeño); las de 10.°–11.° se basan en los marcos (ACARA y TIMSS Advanced).
- Los errores de secuencia que quedan se explican en cada informe (introducciones cualitativas o etiquetas por revisar). Cada informe lista sus **decisiones abiertas para el MINED**.
- Las propuestas de un ciclo afectan a los siguientes (por ejemplo, si un tema baja a 5.°, el de 9.° debe profundizar). Coordinarlas es parte de la revisión (ver `HANDOFF.md`).
