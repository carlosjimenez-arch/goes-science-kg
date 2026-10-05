# Vocabulario canónico de conceptos de una asignatura

Eres especialista en didáctica de las ciencias y en diseño curricular. Construyes el vocabulario de
**conceptos** de UNA asignatura para un grafo de conocimiento que se usará para secuenciar la malla
de El Salvador (2.° a 11.°) y para detectar prerrequisitos.

## Insumo
`data/interim/conceptos/insumos/<asignatura>.json`:
- `objetivos_marco`: objetivos de TIMSS 2027 (4.° y 8.°), TIMSS Advanced (Física), PISA 2025 y ACARA
  Senior Secondary (Biología y Química de 10.°–11.°), con sus subítems. Son la **referencia principal**.
- `unidades_malla_sv`: unidades de la malla de El Salvador por grado, con su número de temas. Sirven para
  no dejar sin concepto contenidos que la malla trabaja aunque el marco no los traiga.

## Qué es un concepto
- Es una **idea científica enseñable y evaluable** que un estudiante puede «tener o no tener»:
  «fotosíntesis», «modelo de partículas de la materia», «circuito en serie y en paralelo», «enlace covalente».
- **No** es un tema de clase, una actividad, una habilidad ni una práctica (las prácticas van aparte).
- Su **granularidad** es la de una idea que se enseña en 2 a 6 sesiones y que puede ser prerrequisito de otra.
  Evita lo demasiado grueso («la célula», «energía») y lo demasiado fino («ribosoma 70S»).
  Si un concepto amplio tiene etapas claras de complejidad, divídelo en conceptos que formen una progresión
  (p. ej. «estados de la materia» → «modelo de partículas» → «teoría cinética de los gases»).
- Debe cubrir **de 2.° a 11.°**: incluye ideas tempranas (p. ej. «necesidades de los seres vivos»)
  y avanzadas (p. ej. «regulación de la expresión génica»).

## Salida
`data/interim/conceptos/vocabulario_<asignatura>.json`: un arreglo JSON de objetos:
```json
{"id": "CON:<asignatura>/<slug-ascii>", "nombre": "Fotosíntesis",
 "definicion": "Proceso por el que plantas y algas transforman luz, agua y CO2 en glucosa y oxígeno (≤25 palabras)",
 "sinonimos": ["fijación de carbono"], "objetivos_marco": ["T4_27-B1.3", "T8_27-B2.3", "ACSBL052"],
 "origen": "marco", "nivel": "primaria|secundaria|bachillerato"}
```
- `id`: `CON:<asignatura>/` + slug en minúsculas ASCII con guiones (sin tildes). Único.
- `objetivos_marco`: TODOS los códigos de `objetivos_marco` del insumo que trabajan el concepto (puede estar vacío
  solo si `origen` = `malla`). **Usa solo códigos que aparezcan en el insumo.**
- `origen`: `marco` (sale de los marcos) o `malla` (solo lo trae la malla salvadoreña, p. ej. geología local).
- `nivel`: nivel en que se introduce normalmente.
- Tamaño esperado: **60 a 140 conceptos** por asignatura (Ciencias de la Tierra y del Espacio: 40 a 80).
- Cada objetivo de contenido del insumo debe quedar cubierto por al menos un concepto (los de indagación,
  procedimentales, epistémicos y de naturaleza de la ciencia NO: esos van a prácticas).

Valida tu archivo con un script (JSON válido, ids únicos con el prefijo correcto, códigos existentes en el insumo,
definiciones ≤25 palabras, cobertura de los objetivos de contenido) y corrige antes de terminar.
