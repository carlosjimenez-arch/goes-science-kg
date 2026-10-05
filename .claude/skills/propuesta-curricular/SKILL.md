---
name: propuesta-curricular
description: Produce la propuesta de malla mejorada de una asignatura (mantener, mover, nuevo, fusionar, dividir, quitar) con evidencia, presupuesto y prerrequisitos respetados, en asignaturas/<x>/propuesta/. Usar en la fase 5, una asignatura a la vez, empezando por Biología.
---

# Propuesta curricular de una asignatura

Especificación completa: `specs/06_propuesta_curricular.md`. Trabajo previo útil:
`reportes/cobertura_curricular/data/referencia/presupuesto_candidatos.json` y `prompts/presupuesto_lote.md`.

1. Lee `asignaturas/<x>/brechas/brechas.json` y el DAG de la asignatura.
2. Genera los candidatos con un script, no a mano:
   - `nuevo`: objetivos sin cobertura en el ciclo, con los países que los enseñan y su grado;
   - `mover`: oportunidad ≥ +1 con países de alto desempeño, comprobando que los prerrequisitos queden antes;
   - `fusionar`: objetivos con profundidad sólida (4+) en el ciclo.
3. Subagentes por ciclo: redactan cada tema nuevo o movido con el formato de la malla del MINED
   (Unidad, Contenido, Procedimental, Indicador de logro, Evidencia, Habilidad TIMSS), citando el
   objetivo pivote y al menos un país (documento y página).
4. Cuadra el presupuesto por ciclo: total de temas igual al actual; las fusiones pagan las inserciones.
5. Escribe `propuesta.json`, `Propuesta_<Asignatura>.xlsx` e `informe.md`, con las métricas antes y después
   (cobertura, balance, nivel cognitivo y oportunidad). Todos los temas van con `estado: borrador`.
6. Agrega los nodos PropuestaTema y las aristas PROPONE y REEMPLAZA al grafo, y valida.
7. **Pregunta al usuario** antes de proponer cualquier `quitar`.
