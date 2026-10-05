Repo: <repo>. You are a senior science-curriculum designer. Revise the existing proposal for asignatura = ASIG, ciclo G10-G11,
following prompts/propuesta_curricular.md (Spanish). Files in asignaturas/ASIG/propuesta/: candidatos_G10-G11.json (REGENERATED),
propuesta_G10-G11.json and informe_G10-G11.md (previous version — read them first), simulacion_G10-G11.json (simulation of the
previous version against the CURRENT graph).
What changed: 14 concepts were added to the vocabulary after an expert triage (data/interim/conceptos/triaje_propuestos.json,
decision "nuevo"), with 32 suggested prerequisite edges (confianza media). Topics that had proposed those names now carry them.
As a result the simulation shows more sequence errors in this cycle than before (see "secuencia_alta_pendiente" in
simulacion_G10-G11.json and "corregir_secuencia" in the candidates).
Task: update propuesta_G10-G11.json and informe_G10-G11.md (bump "version" by one):
- Resolve the new high-confidence sequence errors where a sound design change exists (reorder within the cycle, revisar a topic,
  or record an open decision when the prerequisite edge itself looks wrong — say so explicitly; edges from the triage are
  "media" confidence and may be wrong).
- Keep the budget (total_temas_ciclo), the ≥15% rule, EXACT concept names from vocabulario.json plus the new triage concepts
  (names in triaje_propuestos.json "nombre"), and topic ids from temas_del_ciclo.
- In the informe add a short section «Qué cambió con el triaje de conceptos» (2–5 bullets).
Design by expert judgement; scripts only to validate. Put helper scripts in a unique subfolder of <scratchpad>/.
Reply only with: action counts by type, the sequence errors you resolved / left open (one line each), and any prerequisite edge you
consider wrong (origin → destination, reason).
