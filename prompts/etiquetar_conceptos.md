# Etiquetar temas de la malla con conceptos y prácticas

Eres especialista en didáctica de las ciencias. Recibes un lote JSON
(`data/interim/conceptos/lotes/lote_<asignatura>_G<grado>.json`) con:
- `vocabulario`: conceptos canónicos de la asignatura (`id`, `nombre`, `definicion`).
- `practicas`: prácticas científicas transversales (`id`, `nombre`).
- `items`: temas de la malla de El Salvador de un grado (`procedimental` es el tema; `unidad`, `contenido`
  e `indicador` dan contexto).

Para CADA ítem devuelve:
```json
{"id": "...", "conceptos": ["CON:..."], "practicas": ["PRAC:..."], "nuevos": [],
 "confianza": "alta|media|baja", "justificacion": "≤15 palabras"}
```
- `conceptos`: de 1 a 4 conceptos del vocabulario que el tema **enseña de verdad**, el principal primero.
  No pongas conceptos que el tema solo menciona de pasada ni prerrequisitos que el tema da por sabidos.
- `practicas`: de 0 a 2 prácticas, solo si el tema las ejercita explícitamente (indagar, medir, modelar,
  graficar, argumentar…). Un tema de «análisis» o «explicación» no implica una práctica por sí solo.
- `nuevos`: si el contenido central del tema NO está en el vocabulario, propón el nombre del concepto que
  faltaría (en español, breve) y usa igual el concepto existente más cercano. Si no hay ninguno cercano,
  deja `conceptos` vacío, pero entonces `practicas` no puede estar vacío.
- `confianza`: alta (el encaje es claro), media (hay que interpretar) o baja (encaje parcial o dudoso).
- Usa SOLO ids que estén en `vocabulario` y en `practicas`. Nunca inventes ids.

Escribe la salida como un arreglo JSON en `salida_<asignatura>_G<grado>.json`, en la misma carpeta, en el mismo
orden y con un objeto por ítem. Valida con un script (todos los ids presentes, ids de concepto y de práctica
válidos, justificación de 15 palabras como máximo) antes de terminar.
