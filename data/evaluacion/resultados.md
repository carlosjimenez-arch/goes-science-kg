# Evaluación de la recuperación GraphRAG

Conjunto: `rag_preguntas.json`, con 40 preguntas «plata» (16 locales, 8 de prerrequisitos, 8 de comparación con
países y 8 de marco). Las redactó un subagente especialista mirando el grafo, sin ver el recuperador.
**Debe revisarlo el equipo de Ciencias** para volverlo «oro». Para repetirlo: `uv run gskg evaluar-rag`.

| Versión (2026-10-05) | MRR | recall@5 | recall@10 | recall@25 | acierto@10 |
|---|---|---|---|---|---|
| v1: BM25 + expansión 2 saltos + foco por grado | 0,761 | 0,380 | 0,568 | 0,749 | 0,975 |
| v2: + palabras vacías de pregunta, intención «prerrequisito» (sube por el DAG), peso de concepto 1,15 | 0,788 | — | 0,624 | 0,838 | 1,000 |
| v3: + intención «países» (prioriza objetivos de país; filtra si nombra uno) | 0,812 | — | 0,640 | 0,855 | 1,000 |
| v3 con 5 países (se suman 422 objetivos de Inglaterra y Australia y la revisión de asignaturas) | 0,774 | — | 0,592 | 0,849 | — |
| v3 con 52 preguntas (12 nuevas sobre Inglaterra, Australia y asignaturas revisadas) | **0,788** | — | **0,640** | **0,861** | — |

Ablación del peso de las semillas de tipo concepto (v2):

| Peso | MRR | recall@10 | recall@25 | MRR marco | MRR prerrequisito |
|---|---|---|---|---|---|
| 1,00 | 0,768 | 0,622 | 0,816 | 0,838 | 0,496 |
| **1,15** | **0,788** | 0,624 | 0,838 | 0,838 | 0,594 |
| 1,30 | 0,768 | 0,640 | 0,842 | 0,685 | 0,615 |
| 1,50 | 0,778 | 0,645 | 0,846 | 0,612 | 0,719 |

Se eligió 1,15: es el mejor MRR y no perjudica las preguntas de marco. Con 40 preguntas no conviene ajustar más
fino, porque se corre el riesgo de sobreajustar.

Por tipo en v3: comparación MRR 0,80 (antes 0,62), local 0,95, marco 0,78 (bajó de 0,84: algunas preguntas de
marco mencionan «internacional»), prerrequisito 0,59.

Pendiente: las preguntas de marco y de prerrequisitos son las más débiles. Próximos pasos: intención «marco»
(TIMSS/PISA/ACARA → priorizar `ObjetivoMarco`), búsqueda densa para sinónimos y revisión «oro» del conjunto (spec 10).

**Nota (2026-10-05, con 5 países):** el MRR baja de 0,81 a 0,77 porque los 422 objetivos nuevos de Inglaterra y
Australia compiten en la recuperación y las preguntas de comparación del conjunto solo citan los tres países
originales como relevantes. Hay que ampliar el conjunto con preguntas sobre los países nuevos antes de volver a
ajustar pesos.

**Ablación de la intención «marco» (2026-10-05, 52 preguntas):** priorizar `ObjetivoMarco` cuando la pregunta nombra
TIMSS, PISA o ACARA no mejora (MRR de las preguntas de marco: 0,69 con peso 1,0; 0,63 con 1,2; 0,69 con 1,4; 0,68 con
1,8), porque la mitad de los relevantes de esas preguntas son temas de la malla. Queda el peso en 1,0 y solo se conserva
el filtro que atenúa los marcos no nombrados.

**Japón e intención de país (2026-10-05, 60 preguntas).** Se sumaron 8 preguntas sobre Japón (Q53–Q60). Con ellas el
MRR bajó a 0,754, porque la intención de país solo reconocía Uruguay, Colombia y Singapur: «Japón», «japoneses»,
«Inglaterra» y «Australia» no activaban el peso ×2 ni el filtro por país nombrado. Ahora se reconocen el nombre y el
gentilicio, comparados sin tildes: MRR 0,789, recall@10 0,629, recall@25 0,839. Por tipo: comparación 0,84,
local 0,89, marco 0,63 y prerrequisito 0,61.

**Inglaterra KS4 (2026-10-05, 60 preguntas).** Los 149 objetivos del KS4 bajaron el MRR de 0,789 a 0,754. En cuatro
preguntas de comparación, objetivos del KS4 que sí responden (tabla periódica, separación de mezclas, selección
natural, respiración aerobia y anaerobia) aparecían arriba sin estar marcados como relevantes, porque el conjunto se
escribió antes. Se agregaron 5 ids del KS4 como relevantes; se descartó uno que no correspondía (Q48: energía en
reacciones, no conservación de la masa). Resultado: MRR 0,772, recall@10 0,622, recall@25 0,833. Las preguntas
locales bajaron de 0,89 a 0,87; conviene revisarlas en la próxima sesión.

**Objetivos de país sin intención de país (2026-10-05, 60 preguntas).** Con 1.265 objetivos de seis países, algunos
superaban a los temas de la malla en preguntas locales (Q12: un objetivo de Japón antes que los temas de 7.°). Se
atenúan los objetivos de país cuando la consulta no habla de países (`PESO_PAIS_SIN_INTENCION`):

| Peso | MRR | recall@10 | recall@25 | local | marco | comparación |
|---|---|---|---|---|---|---|
| 1,0 | 0,772 | 0,622 | 0,833 | 0,866 | 0,629 | 0,819 |
| **0,8** | **0,794** | 0,633 | 0,839 | 0,894 | 0,708 | 0,822 |
| 0,6 | 0,794 | 0,633 | 0,839 | 0,894 | 0,708 | 0,822 |
| 0,4 | 0,794 | 0,633 | 0,839 | 0,894 | 0,708 | 0,822 |

Se elige 0,8, el más suave entre los que alcanzan el máximo.

**Conceptos ante una consulta de prerrequisitos (2026-10-05, 60 preguntas).** En las preguntas de prerrequisitos,
temas y objetivos de marco desplazaban a los conceptos (Q20, Q22: los relevantes aparecían en los puestos 7–21).
Se pondera ×`PESO_CONCEPTO_PRERREQ` a los conceptos cuando la consulta pregunta por prerrequisitos:

| Peso | MRR | recall@10 | recall@25 | prerrequisito |
|---|---|---|---|---|
| 1,0 | 0,794 | 0,633 | 0,839 | 0,616 |
| 1,3 | 0,794 | 0,633 | 0,839 | 0,616 |
| **1,6** | **0,826** | 0,632 | 0,835 | 0,808 |
| 2,0 | 0,826 | 0,632 | 0,835 | 0,808 |
| 2,5 | 0,830 | 0,638 | 0,838 | 0,833 |

Se elige 1,6, el primer valor de la meseta: son solo 10 preguntas de prerrequisitos y no conviene sobreajustar.

**Marco frente a país (2026-10-05, 60 preguntas).** «Currículo australiano» activaba la intención de país (Australia
×2) aunque se refiere al marco ACARA, y «objetivos internacionales» activaba a la vez las intenciones de país y de
marco. Ahora, si la consulta habla de un marco, el refuerzo de país solo se aplica cuando se nombra un país, y
«currículo australiano» cuenta como ACARA. Preguntas de marco: MRR 0,708 → 0,854. Global: MRR 0,846, recall@10
0,632, recall@25 0,840 (comparación 0,82, local 0,89, marco 0,85, prerrequisito 0,81).
