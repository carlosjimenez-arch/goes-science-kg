Repo: <repo>. You are a senior science-curriculum designer. Revise asignaturas/ASIG/propuesta/propuesta_GXX-GYY.json and
informe_GXX-GYY.md (read both first) following prompts/propuesta_curricular.md, which now documents the optional
"quitar_conceptos" field: exact vocabulary names whose tag the simulator removes from the action's topics.
The current simulation (asignaturas/ASIG/propuesta/simulacion_GXX-GYY.json, field "secuencia_alta_pendiente") still lists
high-confidence sequence errors: a concept taught in this cycle before its prerequisite. Several come from a topic carrying a
concept tag at a level it does not really teach (e.g., an observational early-grade topic tagged with an advanced concept).
Task: for each pending error decide, by expert judgement, between (a) the tag is wrong or too advanced for that topic → add a
«revisar» action (or extend an existing action on that topic) with "quitar_conceptos" and, if useful, a simpler concept in
"conceptos"; (b) the order is really wrong → reorder within the budget; (c) the prerequisite edge itself is wrong → leave it,
and record it as an open decision for the MINED naming the edge. Find the topics that carry each concept with
data/interim/conceptos/etiquetado_temas.json (topics of this subject and cycle only). Keep version unchanged if you only add
quitar_conceptos to existing actions; otherwise bump it by one. Keep budget, ≥15% rule, valid topic ids and exact names.
Then run `uv run gskg propuesta simular ASIG G0 G1` and reply in ≤5 lines: each error → decision (a/b/c), and
secuencia_alta_en_ciclo before → after. Edit only the two proposal files. Helper scripts in a unique subfolder of <scratchpad>/.
