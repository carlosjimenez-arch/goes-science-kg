---
name: grafo-asignar-disciplina
description: Asigna asignatura (biologia, fisica, quimica, ciencias_tierra_espacio) a los temas de 2.°–9.° que quedaron sin asignatura en el grafo, o los marca como tecnología fuera de alcance. Usar cuando gskg grafo validar avise "temas sin asignatura".
---

# Asignar disciplina a temas pendientes

1. Lista los temas: nodos `Tema` sin `asignatura` en `data/grafo/nodos.jsonl` (49 en v0).
2. Para cada uno, lee procedimental, unidad, contenido, subcontenido e indicador.
3. Decide:
   - `biologia`, `fisica`, `quimica` o `ciencias_tierra_espacio`, con justificación de 15 palabras como máximo
     y confianza;
   - o `fuera_de_alcance: tecnologia` (objetos técnicos, diseño tecnológico sin contenido científico),
     que se enlaza con goes-techonoly-kg;
   - o `fuera_de_alcance: transversal` (por ejemplo, medición genérica sin disciplina).
4. Guarda en `data/interim/asignacion_disciplina.json`: `{id, asignatura|null, fuera_de_alcance|null, confianza,
   justificacion, version: "disciplina-v1"}`.
5. Haz que `disciplinas.asignatura_de_tema` use ese archivo como regla 4 (`metodo = "ia"`). Agrega una prueba,
   reconstruye el grafo y vuelve a generar las fichas.
6. Muestra al usuario la tabla de decisiones de confianza media y baja.
