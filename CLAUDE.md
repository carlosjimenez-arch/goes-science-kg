# goes-science-kg · Grafo de conocimiento de Ciencias (El Salvador)

## Qué es
Grafo de conocimiento de **Biología, Física, Química y Ciencias de la Tierra y del Espacio**
(2.°–11.°) que une la malla del MINED con los marcos internacionales (TIMSS 2027, TIMSS Advanced,
PISA 2025) y los currículos de otros países. Su propósito es **proponer una curricularización
mejor, con evidencia**, por asignatura. Visión completa: `specs/00_vision_y_alcance.md`.

Contexto: el MINED (equipo de Ciencias) entregó las mallas y el equipo GOES diseña la nueva
currícula. El trabajo previo de cobertura está en `reportes/cobertura_curricular/`.

## Antes de implementar
1. Lee `specs/README.md` y las specs que tocan la tarea. El plan con las fases está en `specs/08_plan_de_implementacion.md`.
2. Revisa si hay una skill en `.claude/skills/` para la tarea y síguela.
3. Trabaja por fase. Al cerrar una, muestra el resultado, marca ✅ en la spec 08 y haz commit.

## Estructura
- `grados/G<gg>/`: grafo de cada grado (ficha + visor HTML). Es el entregable que pidió el MINED (spec 09).
- `asignaturas/<asignatura>/`: una carpeta por disciplina. El `README.md` lo escribe el equipo;
  `ficha.md`, `brechas/` y `propuesta/` se generan.
- `config/`: reglas en YAML (mallas, asignaturas, marcos, referentes). Se cambian aquí, no en el código.
- `src/goes_science_kg/`: el paquete (ver la tabla de módulos en la spec 01).
- `data/fuentes/`: mallas del MINED y PDF externos. **SOLO LECTURA.**
- `data/interim/`: intermedios, como lotes de IA y objetivos de países.
- `data/grafo/`: el grafo (`nodos.jsonl`, `aristas.jsonl`, `manifest.json`). Se versiona.
- `reportes/cobertura_curricular/`: trabajo previo, autocontenido. **No se modifica.** Sus `input/`,
  `data/raw` y `data/referencia/externos` son enlaces simbólicos a `data/fuentes/`.
- `specs/`, `.claude/skills/`, `prompts/`.

## Reglas (no cambiarlas sin preguntar)
- Nunca modificar `data/fuentes/`, `reportes/` ni los PDF.
- **Pivote:** todo currículo se alinea contra los marcos, nunca país contra país.
- **Evidencia:** cada nodo trae su fuente (documento y página, o archivo, hoja y fila). Cada inferencia de IA
  trae confianza, justificación (≤15 palabras) y versión. Las de confianza baja van a revisión humana.
- **No inventar códigos.** Al unir lotes de IA se validan contra el catálogo.
- **Parafrasear** en español. No copiar párrafos de los PDF.
- Las reglas de cobertura, balance, profundidad, nivel cognitivo y presupuesto de
  `reportes/cobertura_curricular/CLAUDE.md` siguen vigentes.
- Las decisiones humanas (`revisado_por`) ganan sobre la IA y no se reclasifican sin preguntar.
- Pregunta antes de: agregar países fuera de `config/referentes.yaml`, cambiar el pivote de
  Química y Biología de Bachillerato (hoy ACARA Senior Secondary, spec 03), o proponer quitar temas.
- Alcance: solo ciencias. Los temas de tecnología se marcan fuera de alcance y se enlazan con `goes-techonoly-kg`.

## Convenciones
- Español en código, datos y documentos. Python 3.11+, `uv`, `ruff` (120), `pytest`.
- Rutas relativas a la raíz con `config.ruta()`. Salidas deterministas (ordenadas).
- Subagentes por lote para clasificar o alinear. La unión se hace con un script que valida.
- Excel: todo número de análisis es una fórmula. Compatible con Numbers (sin «·» en pestañas, sin CHAR(10),
  sin XLOOKUP/FILTER). Estilo 2027: encabezado verde bosque 1E4D3A y sin azul.
- Commits: `tipo(ámbito): resumen` en español. `pytest -q` en verde antes de cada commit.
- El remoto usa el alias SSH `github-goes` (`git@github-goes:carlosjimenez-arch/goes-science-kg.git`).

## Comandos
```bash
uv sync --extra dev --extra pdf --extra analisis --extra rag --extra api
uv run gskg temas                 # mallas → data/interim/temas.json
uv run gskg grafo construir       # grafo → data/grafo/ (falla si hay errores)
uv run gskg grafo validar         # invariantes + avisos + métricas
uv run gskg fichas                # asignaturas/<x>/ficha.md
uv run gskg grafo exportar        # data/grafo/export/grafo.graphml
uv run gskg grados construir      # grafos por grado: data/grafo/grados/ + grados/G<gg>/{ficha.md,grafo.html}
uv run gskg rag "<consulta>" --grado 7 [--asignatura biologia] [--responder] [--global]
uv run gskg evaluar-rag           # recall@k y MRR sobre data/evaluacion/rag_preguntas.json (ajuste)
uv run gskg evaluar-rag --conjunto data/evaluacion/rag_preguntas_prueba.json   # prueba independiente: no ajustar con él
uv run gskg servir                # API de lectura en http://127.0.0.1:8010/docs (grados, conceptos, propuestas, rag)
# Capa de conceptos (cada paso «preparar» genera lotes para subagentes; «unir» valida):
uv run gskg conceptos preparar-vocabulario | consolidar | preparar-etiquetado | unir-etiquetado
uv run gskg conceptos preparar-paises | unir-paises | preparar-prerrequisitos | unir-prerrequisitos
uv run gskg grados resumenes      # títulos y resúmenes de bloques temáticos (subagentes)
uv run gskg brechas               # asignaturas/<x>/brechas/
uv run gskg progresion            # asignaturas/<x>/progresion.html
uv run gskg revision exportar|importar <csv>   # circuito de revisión con el MINED
uv run gskg propuesta candidatos|simular|excel <asig> <g0> <g1>   # propuesta por ciclo (spec 06)
uv run gskg internacional extraer|etiquetar|construir   # spec 11 (Vertex AI con ADC; caché en data/interim/internacional/cache)
uv run pytest -q
make todo                         # temas → grafo → validar → fichas, grados, brechas, progresión → internacional → pruebas + lint
make internacional-ia             # extraer + etiquetar (Vertex, con caché) + construir
make propuestas                   # simula las 11 propuestas, rehace sus Excel y asignaturas/PROPUESTAS.md
```
