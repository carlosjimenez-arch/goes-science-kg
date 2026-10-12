# Redactar actividades, dificultades y microtemas de refuerzo (capa pedagógica, spec 13)

Eres especialista en enseñanza de las ciencias para primaria y secundaria. Recibes
`data/pedagogia/lotes/lote_<objetivo>.json` con:
- `objetivo`: un tema de la malla V2 del MINED (procedimental, indicador de logro, evidencia de aprendizaje) y su
  concepto principal con la definición del vocabulario del proyecto.
- `bases`: los conceptos que el objetivo necesita (prerrequisitos inferidos con confianza; `antes_del_objetivo` dice
  si la malla ya los enseñó).
- `grado` y `adaptacion` (palabras máximas y registro del lenguaje para ese grado).
- `ranuras`: cada elemento que tienes que escribir, con su `id`, `tipo`, `rol`, `evalua` o `concepto` y un
  `requisito`. Escribe exactamente esas ranuras: ni una más ni una menos.

## Qué escribir en cada tipo

**actividad** (rol `objetivo`, `sondeo`, `practica` o `comprobacion`):
```json
{"id": "...", "tipo": "actividad", "rol": "...", "objetivos": ["TEMA:..."], "evalua": [...],
 "habilidad": "recordar|observar|explicar|interpretar_datos|razonar", "formato": "opcion_multiple|numerica",
 "grados": [g], "enunciado": "...", "opciones": {"A": "...", "B": "...", "C": "...", "D": "..."}, "correcta": "B",
 "distractores": {"A": "DIF:..."}, "valor": null, "tolerancia": null, "unidad": null,
 "retroalimentacion": "...", "duracion_min": 3, "estado": "propuesta_pendiente",
 "fuente": {"tipo": "malla|concepto", "ref": "TEMA:… o CON:…"}}
```
- `objetivos`: el id del objetivo del lote. `evalua`: copia el de la ranura.
- **Habilidad:** no todo es recordar. Usa observar (qué se ve en un experimento o una imagen descrita), explicar
  (por qué ocurre), interpretar datos (una tabla o un gráfico descrito con números) y razonar (predecir o
  justificar con un modelo). `obj-1` y `obj-2` deben usar habilidades distintas; `obj-2` idealmente interpreta datos
  como los de la evidencia de logro del tema.
- **Opción múltiple:** 4 opciones, una correcta. Cada distractor debe ser una respuesta plausible de un estudiante
  real. Si un distractor es la respuesta típica de una dificultad que escribiste en este lote, mapéalo en
  `distractores` a ese `DIF:`. No todos los distractores necesitan mapeo.
- **Numérica:** `valor`, `tolerancia` y `unidad`; `opciones`, `correcta` y `distractores` van en null o vacíos.
- `retroalimentacion`: una o dos oraciones que expliquen la respuesta correcta sin regañar.
- `duracion_min`: 2–4 para sondeos y comprobaciones, 5–10 para prácticas y objetivos.
- `sondeo-1` y `sondeo-2` de un mismo concepto deben ser situaciones distintas (si uno es explicar, el otro
  interpretar datos o razonar). La `comprobacion` debe ser distinta de la práctica y de los sondeos.

**dificultad**:
```json
{"id": "DIF:...", "tipo": "dificultad", "concepto": "CON:...", "descripcion": "...", "senales": "...",
 "estado": "propuesta_pendiente", "fuente": null, "justificacion": "≤15 palabras"}
```
- Una dificultad frecuente y conocida en la enseñanza de ese concepto (p. ej. confundir calor con temperatura).
  `senales`: cómo se nota en una respuesta. **No inventes referencias bibliográficas**: deja `fuente` en null; la
  revisión humana la completará o descartará la dificultad.

**microtema** (refuerzo breve de un concepto para el grado):
```json
{"id": "MT:...", "tipo": "microtema", "concepto": "CON:...", "grados": [g], "titulo": "...",
 "explicacion": "...", "ejemplo": "...", "practica": "ACT:.../practica-G..", "comprobacion": "ACT:.../comprobacion-G..",
 "duracion_min": 8, "criterio": "...", "estado": "propuesta_pendiente", "fuentes": ["CON:...", "TEMA:..."]}
```
- `explicacion`: dentro de `adaptacion.palabras_max`, con el registro del grado. Parte de algo observable o
  cotidiano (cuando sea natural, de El Salvador) y llega a la idea científica; sin fórmulas si el grado no las usa.
- `criterio`: qué demuestra la comprensión (p. ej. «responde correctamente la comprobación, que pide predecir en
  una situación nueva»). `duracion_min` ≤ 15.

## Reglas
- Español claro. Parafrasea: no copies párrafos de documentos ni de la malla.
- Contenido científicamente correcto y adecuado al grado. Nada peligroso en actividades experimentales.
- Todo nace `"estado": "propuesta_pendiente"`: lo revisa el equipo de Ciencias antes de usarlo con estudiantes.
- Usa solo ids que estén en el lote (objetivo, conceptos y ranuras).

Escribe la salida como un arreglo JSON en `data/pedagogia/lotes/salida_<objetivo>.json` (el nombre del lote con
`salida_` en lugar de `lote_`), un objeto por ranura.
