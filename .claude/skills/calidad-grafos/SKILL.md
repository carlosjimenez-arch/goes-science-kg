---
name: calidad-grafos
description: Verifica la calidad y la bidireccionalidad de los grafos (principal, por grado e internacional) y diagnostica cada falla de tests/test_calidad_grafos.py y tests/test_determinismo.py. Usar después de cambiar datos, vocabulario, prerrequisitos o código del grafo, o cuando el usuario pida auditar los grafos.
---

# Calidad de los grafos

1. `uv run pytest -q tests/test_calidad_grafos.py tests/test_determinismo.py`. Cada prueba responde a una pregunta:
   | Falla | Qué significa | Qué hacer |
   |---|---|---|
   | contrato de tipos | una arista une tipos de nodo que el modelo no permite | revisar el constructor o la capa que la agregó |
   | DAG sin ciclos ni redundancias | prerrequisito circular o transitivo | revisar `unir`, el triaje o las divisiones; nunca editar `data/grafo/` |
   | prerrequisitos entre equivalentes | contradicción (mismo concepto y prerrequisito) | decisión pedagógica: retirar la equivalencia o rechazar el prerrequisito, y registrarla |
   | sin nodos aislados | algo quedó sin relación | ver de dónde sale el nodo |
   | tema en su fila del Excel / sha256 / páginas | la fuente cambió o la cita es mala | no tocar la fuente: rehacer la ingesta o la extracción |
   | fuentes ↔ grafo 1 a 1 | algo se perdió o sobra al construir | comparar la fuente con el constructor |
   | grafo versionado al día | se cambió la entrada sin reconstruir | `uv run gskg grafo construir` (o `make todo`) |
   | determinismo | una salida depende del orden de un conjunto | ordenar en el origen, no al escribir |
2. Para una auditoría más amplia (o si el usuario pregunta «¿está bien el grafo?»): conteos por tipo, conceptos sin
   temas, cadena más larga del DAG y su sentido didáctico, proporción de prerrequisitos por orden observado y
   etiquetas de confianza baja. Revisa a mano lo que parezca raro antes de concluir.
3. Las decisiones de contenido (equivalencias, rechazos, divisiones) se registran en sus capas con justificación y
   `revisado_por`, y se exportan al MINED con la skill `decisiones-mined`.
