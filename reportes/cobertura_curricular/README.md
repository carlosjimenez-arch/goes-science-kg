# Kit · Cobertura TIMSS de las mallas de Ciencias (para Claude Code)

1. Las mallas ya están en `data/raw/` (y la copia de Drive en `input/`). Las fuentes externas en `data/referencia/externos/`.
2. Abre Claude Code en esta carpeta.
3. Pega el contenido de `prompts/00_prompt_para_claude_code.md`.

Claude Code lee `CLAUDE.md` (contexto, reglas y comandos), reutiliza la clasificación v1 de 889 temas,
clasifica solo lo nuevo, genera `outputs/Cobertura_TIMSS_Ciencias_SV.xlsx` y copias anotadas de cada malla en `outputs/mallas_anotadas/`.

Prompts (en orden):
- `prompts/00_prompt_para_claude_code.md` → cobertura TIMSS 2023 v1 (ya generada; sirve para regenerarla).
- `prompts/01_prompt_timss2027.md` → cobertura frente a TIMSS 2027, el marco principal.
- `prompts/02_prompt_paises.md` → comparación con Uruguay, Chile, Colombia y Singapur usando TIMSS 2027 como pivote.
