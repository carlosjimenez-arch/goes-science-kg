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

**Revisión de código y nueva ablación del peso de marco (2026-10-05, 17:20).** Las intenciones ahora usan palabras
completas («compartimentos», «paisaje» y «en inglés» ya no cuentan como país) y una consulta con marco y países sin
nombrar no penaliza a los objetivos de país. Resultado: MRR 0,846, recall@10 0,632, recall@25 0,835. Repetida sin la
interferencia del refuerzo de país, la ablación de `PESO_MARCO` confirma 1,0: con 1,2 y 1,4 no cambia nada, y con 1,8
las preguntas de marco bajan de 0,854 a 0,792.

## Conjunto de prueba independiente (2026-10-05, 17:20)
Los pesos de este día (`PESO_PAIS_SIN_INTENCION`, `PESO_CONCEPTO_PRERREQ`, la separación marco/país) se ajustaron con
las 60 preguntas de `rag_preguntas.json`. Para medir el sobreajuste, un agente que no vio `rag.py` ni este archivo
escribió 16 preguntas nuevas con redacción variada (`rag_preguntas_prueba.json`, 4 por tipo).
**No se usa para ajustar.**

| Versión | MRR | recall@10 | recall@25 | local | comparación | marco | prerrequisito |
|---|---|---|---|---|---|---|---|
| Antes de la sesión (commit 166852b) | 0,647 | 0,470 | 0,801 | 1,00 | 0,76 | 0,48 | 0,34 |
| Al cierre de la sesión | 0,647 | 0,516 | 0,799 | 1,00 | 0,76 | 0,49 | 0,34 |

**Lectura honesta:** las mejoras de marco y prerrequisito del conjunto de ajuste **no se generalizan**. Ninguna de las
8 preguntas nuevas de esos tipos activa su intención, porque las expresiones regulares solo reconocen frases
como «antes de» o «TIMSS» en ciertas formas: «¿sobre qué conceptos se apoya…?», «¿qué base conceptual necesita…?» o
«¿qué tendría que haberse trabajado antes…?» pasan sin detectarse. Próximo paso: detectar la intención de forma más
robusta (léxico más amplio, o un clasificador pequeño con Claude) y medirla en un conjunto de prueba **nuevo**. Si se
ajusta con este, deja de ser independiente.

## Conjunto de prueba ciego 2: prerrequisitos (2026-10-05, 17:30)
Para atacar la falla de la detección de intención sin sobreajustar:
1. Un agente que no vio `rag.py`, `resultados.md` ni la prueba 1 escribió 12 preguntas de prerrequisitos con
   redacción variada (`rag_preguntas_prueba2.json`).
2. **Antes de abrirlas**, la intención de prerrequisito se amplió con un léxico armado por conocimiento del idioma:
   verbos de requisito, «bases», «fundamentos», «se apoya en», «haberse trabajado», etc.
3. Se midió **una sola vez**:

| Versión | MRR | recall@5 | recall@10 | recall@25 |
|---|---|---|---|---|
| Antes de la sesión (166852b) | 0,257 | 0,333 | 0,528 | 0,667 |
| Pesos del día, léxico viejo | 0,470 | 0,417 | 0,611 | 0,694 |
| **Pesos del día, léxico ampliado** | **0,547** | 0,472 | 0,583 | 0,694 |

El léxico ampliado reconoce 8 de las 12 preguntas. En este conjunto ciego, los cambios del día sí se generalizan
para prerrequisitos (MRR 0,26 → 0,55). En la prueba 1 no se notaban porque ninguna de sus preguntas activaba la
intención; esa prueba ya quedó contaminada para el léxico, porque se leyeron sus preguntas antes de ampliarlo. Con el
léxico ampliado, el conjunto de ajuste sigue en MRR 0,846. **La prueba 2 ya se usó una vez: la próxima mejora necesita
un conjunto nuevo.**
Hueco conocido del léxico: «¿de qué depende…?» (orden invertido) no se reconoce. No se corrigió después de medir,
para que la cifra corresponda al código.

## Conjunto de prueba ciego 3: marco (2026-10-05, 17:31)
Hipótesis: los `ObjetivoMarco` quedan abajo cuando la consulta nombra un marco. Se implementó `GARANTIA_MARCO`, que
sube los 3 objetivos más pertinentes del marco nombrado justo debajo de la mejor semilla, y se amplió el léxico de
marco («metas internacionales», «marcos de referencia», «descriptores»…). Regla fijada **antes** de medir: adoptarla
si en la prueba 3 sube recall@10 y la MRR no cae más de 0,02. Un agente que no vio el código ni las otras pruebas
escribió 12 preguntas de marco (`rag_preguntas_prueba3.json`); el léxico reconoce las 12. Medición única:

| Versión | MRR | recall@5 | recall@10 | recall@25 |
|---|---|---|---|---|
| Antes de la sesión (166852b) | 0,738 | 0,356 | 0,583 | 0,839 |
| Cierre, sin garantía | 0,734 | 0,372 | 0,600 | 0,872 |
| Cierre, con garantía (3) | 0,734 | 0,372 | 0,600 | 0,872 |

**Decisión:** no se adopta (`GARANTIA_MARCO = 0`); no cambia nada en la prueba ciega. Lectura: con preguntas de marco
redactadas por otra persona, la recuperación ya es razonable (MRR 0,73). El 0,49 de la prueba 1 se debía a pocas
preguntas difíciles. Frente a antes de la sesión: MRR igual y recall@25 de 0,84 a 0,87.
