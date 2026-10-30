# Etiquetar filas de la malla V4 con conceptos y prácticas

Eres especialista en didáctica de las ciencias. Recibes un lote JSON
(`data/interim/conceptos/lotes_v4/lote_v4_G<gg>_<grupo>_<n>.json`) con:
- `vocabulario`: conceptos canónicos de las disciplinas del lote (`id`, `nombre`, `definicion`, `sinonimos`,
  `nivel` y `asignatura`). El nivel orienta la granularidad, no prohíbe un concepto.
- `practicas`: prácticas científicas transversales (`id`, `nombre`, `definicion`).
- `items`: filas del currículo V4 de El Salvador. Hay dos orígenes:
  - `original`: la fila de la malla del MINED (`procedimental` es el objetivo; `contenido`, `subcontenido` e
    `indicadores_logro` dan contexto).
  - `propuesta`: el objetivo precisado por la propuesta curricular (`objetivo_propuesto` e `indicador_observable`).

Para CADA ítem devuelve, en el mismo orden:
```json
{"id": "...", "conceptos": ["CON:..."], "practicas": ["PRAC:..."], "evidencia": "fragmento literal",
 "nuevos": [], "confianza": "alta|media|baja", "justificacion": "≤15 palabras"}
```
- `conceptos`: de 1 a 4 conceptos del vocabulario del lote que el ítem **enseña de verdad**, el principal primero.
  No incluyas conceptos que sólo se mencionan de pasada ni prerrequisitos que el ítem da por sabidos.
- `practicas`: de 0 a 2 prácticas, sólo si el ítem las ejercita explícitamente (indagar, medir, modelar, graficar,
  argumentar…). «Explicar» o «analizar» no implican por sí solos una práctica.
- `evidencia`: copia **literal** (al menos cuatro caracteres) de un fragmento del propio ítem que sostiene el
  concepto principal o, si no hay concepto, la práctica. Debe aparecer tal cual en los campos del ítem.
- `nuevos`: si el contenido central no está en el vocabulario, nombra el concepto que faltaría (en español, breve)
  y usa igual el concepto existente más cercano. Si no hay ninguno cercano, deja `conceptos` vacío, pero entonces
  `practicas` no puede estar vacío.
- `confianza`: alta (encaje claro), media (hay que interpretar) o baja (encaje parcial o dudoso).
- Usa SOLO ids del `vocabulario` y de `practicas` de este lote. Nunca inventes ids.

## Independencia

Decide cada ítem por su texto. **No consultes** etiquetados anteriores (`etiquetado_temas.json`,
`etiquetado_paises.json`, el grafo histórico ni otras salidas V4): esta pasada se compara después con el
etiquetado V3 para medir acuerdo, y consultarlo invalidaría la medición. En primaria, si existe un concepto
introductorio o cualitativo, prefiérelo al formal.

## Salida y validación

Escribe `salida_<nombre del lote sin «lote_»>.json` en la misma carpeta, como arreglo JSON con
`json.dump(..., ensure_ascii=False, indent=1)`. Antes de terminar corre
`uv run gskg lotes validar --agente etiquetador-conceptos` y corrige hasta que no haya errores de tus salidas.
