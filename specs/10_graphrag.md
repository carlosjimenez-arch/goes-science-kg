# 10 · GraphRAG

Consulta en lenguaje natural sobre el grafo, para el equipo curricular y, más adelante, para docentes.
Por ejemplo: «¿qué necesita saber un estudiante de 7.° antes de genética?» o «¿cómo enseñan circuitos
los países de referencia y en qué grado?».

## Arquitectura (`src/goes_science_kg/rag.py`)
```
consulta ──► BM25 en español (nodos con texto) ──► semillas (filtradas por grado y asignatura)
                                                          │
                     expansión por el grafo (1–2 saltos: TRABAJA, PRERREQUISITO_DE, CUBRE, ALINEA_CON)
                                                          │
                                  contexto citable (nodos + fuente + relaciones)
                                                          │
                              (opcional) Claude genera una respuesta citando los ids
```
- **Recuperación determinista y local.** No necesita red ni claves, y las pruebas fijan su comportamiento.
- **Foco por grado.** Con `--grado`, los temas de ese grado pesan 1,5 veces más, lo de otros grados 0,5 veces,
  y los temas de otros grados se atenúan también en la expansión. TIMSS 2023 nunca entra al contexto.
- **Citas.** Cada nodo lleva su fuente: documento y página, código ACARA, u hoja y fila de la malla.
- **Generación.** `gskg rag "<consulta>" --grado 7 --responder` usa el SDK oficial de Anthropic con
  `claude-opus-5-5`, esfuerzo `medium` y caché del prompt de sistema. Tiene activado el respaldo del servidor
  (`fallbacks: "default"`) por si un clasificador de seguridad rechaza la solicitud. Requiere
  `uv sync --extra rag` y credenciales de Anthropic (`ANTHROPIC_API_KEY` o `ant auth login`).

## Próximos pasos
1. ✅ **Resúmenes de comunidades** (hecho: 95 bloques con resumen de especialista, `--global`; el «Global search» de GraphRAG): agrupar los conceptos de cada grado y asignatura
   con Louvain (`networkx.community.louvain_communities`) sobre el grafo concepto-concepto (co-ocurrencia en temas
   + prerrequisitos), y resumir cada comunidad con Claude en lotes. Sirve para preguntas globales
   («¿cuáles son los grandes bloques de 8.°?»).
2. **Búsqueda híbrida**: sumar embeddings densos al BM25 si la evaluación muestra fallas de vocabulario (sinónimos).
3. ✅ (versión «plata», 52 preguntas, `data/evaluacion/`) **Evaluación**: un conjunto de 30 a 50 preguntas con respuesta de referencia escrita por el equipo de Ciencias,
   con recall@k de la recuperación y fidelidad de las citas de la respuesta.
4. ✅ **API de lectura** (FastAPI; `gskg servir`): `/api/grados`, `/api/grados/{g}`, `/api/conceptos/{asig}/{slug}`,
   `/api/propuestas`, `/api/rag`, `/api/rag/global`. Siguiente: un panel docente que la consuma.
