# Kit · Cobertura TIMSS de las mallas de Ciencias (para Claude Code)

1. Copia las 11 mallas .xlsx a `data/raw/` (ver `prompts/00_prompt_para_claude_code.md`).
2. Abre Claude Code en esta carpeta.
3. Pega el contenido de `prompts/00_prompt_para_claude_code.md`.

Claude Code lee `CLAUDE.md` (contexto, reglas y comandos), reutiliza la clasificación v1 de 889 temas,
clasifica solo lo nuevo, genera `outputs/Cobertura_TIMSS_Ciencias_SV.xlsx` y copias anotadas de cada malla en `outputs/mallas_anotadas/`.
