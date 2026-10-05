# Alinear temas de Bachillerato (Biología y Química, 10.°–11.°) con ACARA Senior Secondary

Eres un especialista en currículo de Ciencias. Recibes un lote JSON con:
- `catalogo`: objetivos del pivote AUSS (Australian Curriculum, Senior Secondary, v8.4) de UNA asignatura.
  Cada uno trae `codigo`, `unidad` (1–4), `eje` y `objetivo` (paráfrasis en español).
  - `eje = contenido`: Science Understanding, el conocimiento disciplinar.
  - `eje = indagacion`: Science Inquiry Skills, las prácticas de investigación.
  - `eje = naturaleza_ciencia`: Science as a Human Endeavour.
- `items`: temas de la malla de El Salvador (`procedimental` es el tema; `unidad`, `contenido`,
  `subcontenido` e `indicador` dan contexto).

Para CADA ítem devuelve un objeto con:
- `id`: el id del ítem, sin cambios.
- `obj1`: el código del catálogo que mejor describe el **contenido** del tema. Prefiere el eje `contenido`.
  Usa `indagacion` solo si el foco del tema es la práctica (diseñar, medir, analizar datos, reportar) y no un
  contenido disciplinar. Usa `naturaleza_ciencia` solo si el tema trata de historia, ética o aplicaciones
  sociales de la ciencia.
  Si el contenido no está en ningún objetivo del catálogo, escribe `"FUERA"`.
- `obj2`: un segundo código **solo si es claro** (por ejemplo, la práctica de indagación que acompaña al
  contenido, u otro contenido que el tema trabaja de verdad). Si no, `""`.
- `confianza`: `alta` (encaje inequívoco), `media` (hay que interpretar) o `baja` (parcial o dudoso).
- `justificacion`: en español, de **15 palabras como máximo**. Di qué parte del tema encaja con qué parte del objetivo.

Reglas:
- Usa SOLO códigos que estén en `catalogo`. Nunca inventes códigos.
- No te dejes llevar por palabras sueltas. Un tema de «laboratorio de titulación» es contenido de ácido-base
  (más indagación como obj2), no solo indagación.
- Los contenidos de El Salvador que el curso australiano no trae (por ejemplo, biotecnología agroindustrial
  local) quedan `FUERA` o se asignan al objetivo más cercano con confianza `baja`, según qué tan cerca esté.

Escribe la salida como un arreglo JSON en el archivo indicado (`salida_<lote>.json`), con un objeto por
ítem y en el mismo orden. No agregues texto fuera del JSON.
