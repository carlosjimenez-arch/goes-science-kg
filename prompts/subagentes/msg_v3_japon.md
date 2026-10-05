Repo: <repo>. You are a senior science-curriculum designer. Revise the existing proposal for asignatura = ASIG, ciclo GXX-GYY,
following prompts/propuesta_curricular.md (Spanish). Files in asignaturas/ASIG/propuesta/: candidatos_GXX-GYY.json (REGENERATED),
propuesta_GXX-GYY.json and informe_GXX-GYY.md (your previous version — read them first).
What changed in the candidates:
1. Japan was added as a reference country (code JP; TIMSS 2023 science: 6th at grade 4, 3rd at grade 8), with 188 objectives from
   the official MEXT Course of Study 2017. Grade equivalence by school-entry age: Japan grade N = SV grade N−1 (primary 3–6 → SV 2–5;
   lower secondary 1–3 → SV 6–8). High-performing countries in the graph are now SG, ENG, AU and JP; the median of high performers
   moved for many concepts, so mover_antes candidates and their evidence changed.
Task: update propuesta_GXX-GYY.json and informe_GXX-GYY.md to a new version (bump "version" by one, e.g. -v2 → -v3):
- Keep actions that are still supported; drop or adjust those the new evidence no longer backs; add new strongly supported ones
  (prioritise those backed by ≥2 high-performing countries). Keep the prerequisite rule (bloqueos), the budget (total_temas_ciclo)
  and the ≥15% rule.
- Use EXACT concept names from data/interim/conceptos/vocabulario.json in "conceptos"; topic ids must exist in temas_del_ciclo.
- In the informe, add a short section «Qué cambió con Japón» (3–6 bullets).
Design by expert judgement; scripts only to validate. Put helper scripts in a unique subfolder of <scratchpad>/. Re-run validation.
Reply only with: action counts by type, temas_por_grado before/after, and the 3 most important changes vs your previous version.
