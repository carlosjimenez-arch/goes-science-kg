Please revise your proposal: the candidates file was REGENERATED and now includes two high-performing countries.
What changed in asignaturas/<asig>/propuesta/candidatos_<ciclo>.json (same path you used):
1. Two TIMSS-2023 top-10 countries were added to the graph: England (5th in science at grades 4 and 8) and Australia (8th at grade 4). Country codes ENG and AU appear in "paises". Grade equivalence is by school-entry age (England Year N = SV grade N−2; KS3 = 5–7, counted at its midpoint 6; Australia Year N = SV N−1).
2. An expert review reassigned the discipline of 19 integrated-curriculum topics (e.g., intermolecular forces G06-4.7/4.8 are now Chemistry), so "temas_del_ciclo" and "total_temas_ciclo" may differ from v1.
Task: update your proposal_*.json and informe_*.md to a new version (bump "version", e.g. "propuesta-v2" or "-v3" if already v2):
- Budget = the NEW total_temas_ciclo; drop from temas_afectados any topic that is no longer in temas_del_ciclo (it now belongs to another subject) and adjust.
- Consider the NEW mover_antes candidates, prioritising those backed by high-performing countries (ENG, AU, SG); keep the prerequisite rule (bloqueos) and the ≥15% rule.
- Keep using EXACT concept names from data/interim/conceptos/vocabulario.json in "conceptos".
- In the informe, add a short section «Qué cambió con los países de alto desempeño» (3–6 bullets).
Re-run your validation script. Reply with: action counts by type, temas_por_grado before/after, and the 3 most important changes vs your previous version.
