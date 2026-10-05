# Evaluación de la recuperación GraphRAG

Conjunto: `rag_preguntas.json`, con 40 preguntas «plata» (16 locales, 8 de prerrequisitos, 8 de comparación con
países y 8 de marco). Las redactó un subagente especialista mirando el grafo, sin ver el recuperador.
**Debe revisarlo el equipo de Ciencias** para volverlo «oro». Para repetirlo: `uv run gskg evaluar-rag`.

| Versión (2026-10-05) | MRR | recall@5 | recall@10 | recall@25 | acierto@10 |
|---|---|---|---|---|---|
| v1: BM25 + expansión 2 saltos + foco por grado | 0,761 | 0,380 | 0,568 | 0,749 | 0,975 |
| v2: + palabras vacías de pregunta, intención «prerrequisito» (sube por el DAG), peso de concepto 1,15 | 0,788 | — | 0,624 | 0,838 | 1,000 |
| v3: + intención «países» (prioriza objetivos de país; filtra si nombra uno) | **0,812** | — | **0,640** | **0,855** | **1,000** |

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
