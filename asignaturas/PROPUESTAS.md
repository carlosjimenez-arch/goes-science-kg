# Propuestas curriculares (borrador) · resumen

Borradores por asignatura y ciclo, generados con el grafo de conocimiento (spec 06). Estado: **borrador**, pendiente de la revisión del equipo de Ciencias del MINED. Ninguno quita temas y todos conservan el total de su ciclo.

**Verificación:** `gskg propuesta simular` aplica las acciones sobre el grafo (mover, fusionar, crear, reformular, dividir), recalcula el diagnóstico y compara antes y después:

- *Errores de secuencia (alta)*: prerrequisitos de confianza alta que la malla enseña después del concepto que los necesita.
- *Llegan ≥2 grados tarde*: conceptos del ciclo que El Salvador introduce dos o más grados después que la mediana de Uruguay, Colombia y Singapur. No aplica (n/a) en 10.°–11.°, porque los currículos de los países en el grafo llegan solo a 9.°.
- *Desfase medio*: promedio de |grado SV − mediana de países| de los conceptos comparables del ciclo.

| Asignatura | Ciclo | Acciones | Errores de secuencia (alta) | Llegan ≥2 grados tarde | Desfase medio | Documentos |
|---|---|---|---|---|---|---|
| Biología | 2.°–4.° | 14 (fusionar 3, mover 2, nuevo 3, revisar 6) | 6 → **5** | 9 → **4** | 2.15 → **1.76** | [informe](biologia/propuesta/informe_G02-G04.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G02-G04.xlsx) |
| Biología | 5.°–8.° | 20 (dividir 1, fusionar 5, mover 7, nuevo 4, revisar 3) | 3 → **0** | 14 → **6** | 2.14 → **1.66** | [informe](biologia/propuesta/informe_G05-G08.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G05-G08.xlsx) |
| Biología | 10.°–11.° | 20 (fusionar 8, mover 2, nuevo 8, revisar 2) | 1 → **0** | n/a | n/a | [informe](biologia/propuesta/informe_G10-G11.md) · [Excel](biologia/propuesta/Propuesta_Biologia_G10-G11.xlsx) |
| Tierra y Espacio | 2.°–4.° | 7 (fusionar 3, nuevo 3, revisar 1) | 10 → **3** | 5 → **2** | 2.27 → **1.9** | [informe](ciencias_tierra_espacio/propuesta/informe_G02-G04.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G02-G04.xlsx) |
| Tierra y Espacio | 5.°–8.° | 14 (fusionar 3, mover 6, nuevo 3, revisar 2) | 5 → **1** | 7 → **8** | 2.35 → **2.15** | [informe](ciencias_tierra_espacio/propuesta/informe_G05-G08.md) · [Excel](ciencias_tierra_espacio/propuesta/Propuesta_Ciencias_tierra_espacio_G05-G08.xlsx) |
| Física | 2.°–4.° | 15 (dividir 1, fusionar 4, nuevo 4, revisar 6) | 3 → **3** | 9 → **3** | 2.52 → **1.77** | [informe](fisica/propuesta/informe_G02-G04.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G02-G04.xlsx) |
| Física | 5.°–8.° | 20 (fusionar 7, mover 3, nuevo 7, revisar 3) | 10 → **3** | 19 → **12** | 2.43 → **1.86** | [informe](fisica/propuesta/informe_G05-G08.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G05-G08.xlsx) |
| Física | 10.°–11.° | 8 (mover 2, revisar 6) | 1 → **0** | n/a | n/a | [informe](fisica/propuesta/informe_G10-G11.md) · [Excel](fisica/propuesta/Propuesta_Fisica_G10-G11.xlsx) |
| Química | 5.°–8.° | 15 (fusionar 6, mover 1, nuevo 6, revisar 2) | 8 → **2** | 6 → **1** | 2.17 → **1.83** | [informe](quimica/propuesta/informe_G05-G08.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G05-G08.xlsx) |
| Química | 10.°–11.° | 18 (fusionar 5, mover 1, nuevo 5, revisar 7) | 3 → **1** | n/a | n/a | [informe](quimica/propuesta/informe_G10-G11.md) · [Excel](quimica/propuesta/Propuesta_Quimica_G10-G11.xlsx) |

Notas:
- **Química 2.°–4.°** no tiene propuesta: la malla no tiene Química en 4.° y no hay conceptos que lleguen tarde.
- **Tierra y Espacio 5.°–8.°** casi no reduce los conceptos que llegan tarde: a propósito mueve la unidad del espacio de 5.° a 6.° para que la gravedad y las órbitas vayan antes.
- Las propuestas de 2.°–8.° ya usan los 5 países (con Inglaterra y Australia, de alto desempeño); las de 10.°–11.° se basan en los marcos (ACARA y TIMSS Advanced).
- Los errores de secuencia que quedan se explican en cada informe (introducciones cualitativas o etiquetas por revisar). Cada informe lista sus **decisiones abiertas para el MINED**.
- Las propuestas de un ciclo afectan a los siguientes (por ejemplo, si un tema baja a 5.°, el de 9.° debe profundizar). Coordinarlas es parte de la revisión (ver `HANDOFF.md`).
