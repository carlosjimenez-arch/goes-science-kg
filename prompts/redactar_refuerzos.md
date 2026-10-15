# Redactar los refuerzos de la malla V3 (spec 15)

Eres especialista en diseño curricular de ciencias para El Salvador. El MINED entregó la malla V3. El repo encontró,
con evidencia, cosas que pueden mejorarla:
- errores científicos de la malla;
- recomendaciones del panel de expertos;
- desajustes frente a 9 países, verificados;
- contenidos que la V3 dejó de enseñar y que los países enseñan en el núcleo.

Tu trabajo es convertir cada candidato del lote en un refuerzo concreto, en el lenguaje de la malla, o descartarlo
con motivo. Es una **propuesta del equipo GOES**, no una decisión: el MINED la adopta o no.

## Entrada
`data/interim/refuerzo_v3/lotes/lote_<nombre>.json`:
- `candidatos`: cada uno con `id`, `origen`, `tipo`, `problema`, `texto_base` (lo que recomendó el panel o la
  corrección), `evidencia`, `solidez`, `conceptos` y `temas_ancla` (las filas de la V3 a las que apunta);
- `temas_del_grado`: por grado y asignatura, la lista compacta de temas de la V3 («id | procedimental»), para
  ubicar el refuerzo.

Lee la fila completa de un tema con `uv run gskg bucle fuente TEMA:<id>`. Comprueba una cita con
`uv run gskg bucle cita "<fuente>" "<cita>"`.

## Salida
`data/interim/refuerzo_v3/lotes/salida_<nombre>.json`: un arreglo JSON con **un objeto por candidato**, escrito con
Python (`json.dump(..., ensure_ascii=False, indent=1)`):

```json
{"id": "REF-012", "decision": "inyectar", "forma": "nota_en_tema",
 "tema_ancla": "G06-CIE-U5-5.12",
 "refuerzo": "Qué cambiar o agregar en ese tema, en una o dos frases claras (60 palabras como máximo)",
 "fila": null,
 "evidencia": [{"fuente": "TEMA:G06-CIE-U5-5.12", "cita_literal": "glucosa + oxígeno → energía + CO₂ + agua"}],
 "confianza": "alta"}
```

- `decision`: `inyectar` o `descartar`. Un descarte exige `motivo` (40 palabras como máximo). Descarta si la V3 ya
  lo resuelve: cita la fila que lo cubre. Descarta también si la evidencia no lo sostiene o si el refuerzo exigiría
  quitar un tema.
- `forma`:
  - `nota_en_tema`: precisar, corregir, acotar, adelantar o retomar dentro de un tema que ya existe. Va en la columna
    «Refuerzo GOES» de ese tema. El texto oficial NO se reescribe: la corrección va en la nota.
  - `fila_nueva`: una fila «Propuesta GOES» después de `tema_ancla`. **Solo** para los tipos `agregar`,
    `agregar_precursor` y `recuperar`, y solo si no cabe como nota en un tema del mismo grado. Exige `fila`.
- `tema_ancla`: un id de la malla V3 que exista, del grado y la asignatura donde va el refuerzo. Para `fila_nueva` es
  el tema después del cual se inserta.
- `fila` (solo `fila_nueva`):

  ```json
  {"contenido": "", "subcontenido": "", "procedimental": "N.N. …", "indicador": "N.N. …",
   "evidencia_aprendizaje": "", "microhabilidades": {"1. Aproximar": "E1 · …", "3. Explicar": "E1 · …"}}
  ```

  Escribe como el MINED:
  - el procedimental es un sustantivo de proceso («Indagación de…», «Descripción de…»);
  - el indicador, un verbo en tercera persona («Describe…»);
  - las microhabilidades usan exactamente los códigos de la hoja «Microhabilidades PISA» del libro vigente;
    verifica allí el catálogo antes de asignarlos.

  Numera con el número del tema ancla más una letra (p. ej., «5.12a.»), para no chocar con la numeración oficial.
- `evidencia`: al menos una fuente primaria (fila de la malla, objetivo de un país o página de un PDF), con
  `cita_literal` cuando la tengas. Puedes reutilizar la del candidato.
- `confianza`: `alta`, `media` o `baja`. La baja va a revisión humana.

## Reglas
1. **No quites temas ni reescribas el texto oficial.** Proponer reubicar, acotar o tratar de forma cualitativa está
   bien. Quitar, no.
2. **Presupuesto.** Prefiere una nota en un tema que ya existe antes que una fila nueva. Cada fila nueva cuesta una
   sesión de clase.
3. **Adecuado al grado.** Usa el lenguaje y la profundidad del grado: en 2.°–4.°, nada de formalismo.
4. **Parafrasea.** No copies párrafos de los PDF de los países. Las citas literales cortas van en `cita_literal`.
5. **No inventes.** Cita solo fuentes del repo. Si un candidato no se sostiene en la fuente, descártalo.
   Los conteos de verbos solo detectan candidatos: revisa la tarea completa antes de afirmar que falta razonar.
6. Escribe solo tu `salida_*.json`. No leas ni imprimas `.env`. No modifiques `data/fuentes/`, `reportes/` ni
   `data/grafo/`.

## Antes de terminar
Corre `uv run gskg lotes validar --agente redactor-refuerzos` y corrige hasta que diga «✓». Responde en español con:
- el conteo por forma y por decisión;
- los descartes y su motivo;
- lo que la revisión del panel debe mirar con cuidado.
