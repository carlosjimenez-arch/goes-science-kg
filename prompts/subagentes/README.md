# Plantillas para subagentes

Encargos en inglés que se usaron el 2026-10-05 para lanzar subagentes en paralelo. Cada una remite a un prompt
en español de `prompts/`. Reemplaza `<repo>` por la raíz del repo, `<scratchpad>` por el directorio temporal de la
sesión y los marcadores en MAYÚSCULAS (LOTES, ASIG, G0–G1, XX-YY, LOTE).

| Plantilla | Uso | Prompt base |
|---|---|---|
| `prompt_etiquetar.md` | Etiquetar temas de la malla con conceptos | `prompts/etiquetar_conceptos.md` |
| `prompt_paises.md` | Etiquetar objetivos de un país con conceptos | `prompts/etiquetar_conceptos.md` |
| `prompt_prerreq.md` | Prerrequisitos por asignatura | `prompts/prerrequisitos.md` |
| `prompt_comunidades.md` | Título y resumen de bloques temáticos | (autocontenido) |
| `prompt_propuesta.md` | Propuesta curricular por ciclo | `prompts/propuesta_curricular.md` |
| `msg_v2.md` | Pedir la revisión de una propuesta tras regenerar candidatos | — |
| `msg_v3_japon.md` | Revisión de las propuestas al sumar Japón (encargo autocontenido) | `prompts/propuesta_curricular.md` |
