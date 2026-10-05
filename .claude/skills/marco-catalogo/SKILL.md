---
name: marco-catalogo
description: Construye o completa el catálogo de objetivos de un marco internacional (TIMSS, TIMSS Advanced, PISA u otro pivote) desde su PDF oficial, con página por objetivo y metas validadas. Usar en la fase 1 (pivote de Bachillerato, páginas de TIMSS Advanced) o si aparece un marco nuevo.
---

# Catálogo de un marco pivote

Referencia de formato: `reportes/cobertura_curricular/data/referencia/catalogo_timss2027.json`
(campos `codigo, marco, dominio, meta_dominio, area_codigo, area, objetivo, titulo_en, subitems,
ambiental, es_investigacion, pagina_fuente, pagina_pdf`).

1. Extrae el texto con `pdfplumber` (`uv run --extra pdf python …`) página por página.
   Guarda la página impresa (`pagina_fuente`) y la del PDF (`pagina_pdf`).
2. Un objetivo por cada ítem **numerado** del marco. Los subítems (A, B, C…) van en `subitems`.
3. `objetivo`: **paráfrasis en español**, de 25 palabras como máximo. `titulo_en`: título literal corto.
4. Códigos: `<MARCO>-<Letra de dominio><área>.<n>` (p. ej. `T8_27-B1.2`). No reutilices códigos de otro marco.
5. Valida contra el PDF y escribe una prueba en `tests/` con:
   - metas por dominio y por nivel cognitivo (suman 100 %),
   - número de áreas por dominio,
   - códigos únicos y página presente en todos.
6. Guarda el catálogo en `data/referencia/catalogo_<marco>.json` y regístralo en `config/marcos.yaml`.
7. Muestra al usuario los conteos por dominio antes de usar el catálogo para alinear.
