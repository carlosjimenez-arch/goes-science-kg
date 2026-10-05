Repo: <repo>. You are a science-education specialist (didáctica de las ciencias).
Follow EXACTLY the instructions in prompts/etiquetar_conceptos.md (Spanish). Process these batch files in data/interim/conceptos/lotes/ (one output per batch, named salida_<same suffix>.json in the same folder):
LOTES
Judge every item individually by reading procedimental/unidad/contenido/indicador against the vocabulary definitions — do not assign concepts with keyword-matching scripts (scripts only to write/validate JSON). Use only ids present in each batch's vocabulario/practicas. Put your helper scripts in a unique subfolder of the scratchpad <scratchpad>/ (other agents share it).
Validate each output (all ids present once, valid concept/practice ids, confianza values, justificacion ≤15 words). Reply only with: per batch item count and confianza counts, and the 5 most frequent "nuevos" proposals.
