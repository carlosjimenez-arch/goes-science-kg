"""Sistema de apoyo al aprendizaje sobre el grafo de Ciencias (spec 13): prototipo.

Complementa la malla, no la modifica. Cuatro capas:
- curricular y científica (el grafo compartido de data/grafo/, solo lectura);
- pedagógica (data/pedagogia/: actividades, dificultades y microtemas; compartida, cambia solo por revisión);
- individual (data/estudiantes/: evidencia y estado de cada estudiante; nunca toca las capas compartidas).

Módulos: `relaciones` (relaciones con su inversa y navegador bidireccional), `pedagogia` (capa pedagógica, cola de
propuestas y lotes del subagente redactor-actividades), `estudiante` (estado y evidencia), `diagnostico`
(hipótesis que se comprueban), `planificador` (refuerzos con límites), `contexto` (lo que se inyecta al tutor),
`sesion` (el ciclo completo) y `recorridos` (tres recorridos de ejemplo reproducibles).
"""
