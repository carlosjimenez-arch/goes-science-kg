# Prompt 01 · Siguiente fase: TIMSS 2027 + currículos de otros países (después del Prompt 00)

Lee CLAUDE.md. Ya existe la cobertura v1 frente a TIMSS 2023. Ahora:

## A. Catálogo TIMSS 2027 (el próximo ciclo; publicado en 2025)
1. Del PDF `data/referencia/externos/timss/TIMSS2027_Marcos_Evaluacion.pdf` construye `data/referencia/catalogo_timss2027.json` con el mismo esquema que `catalogo_timss.json` (codigo, marco T4_27/T8_27, dominio, meta_dominio, area, objetivo parafraseado, pagina_fuente).
2. Ojo con los cambios ya detectados: 4.° grado cambia el cognitivo a Conocer 35 / Aplicar 40 / Razonar 25 (en 2023 era 40/40/20), el dominio de vida se llama Biology, hay áreas nuevas (en 4.°: Light and Sound, Electricity and Magnetism como áreas propias) y áreas de «Investigations». Verifícalo en el PDF y documenta cada diferencia con 2023 en `data/referencia/cambios_timss_2023_2027.md`.
3. Haz una tabla de equivalencias código 2023 → código 2027 (`equivalencias_timss_2023_2027.csv`). Reclasifica SOLO los temas cuyo objetivo 2023 no tenga equivalente directo (subagentes + `prompts/clasificar_lote.md`, cambiando el catálogo).
4. Genera `outputs/Cobertura_TIMSS2027_Ciencias_SV.xlsx` con el mismo `build_cobertura.py` (parametriza el catálogo y las metas cognitivas por argumento, sin duplicar el script).

## B. Currículos de otros países (Uruguay, Chile, Colombia, Singapur)
1. Por cada país en `externos/paises/`, extrae los objetivos de aprendizaje por grado/tramo a `data/interim/paises/<pais>.json` con: pais, documento, pagina, grado_o_tramo, eje/área, texto_objetivo (literal corto ≤ 30 palabras o paráfrasis), id estable.
   - Uruguay: programas EBI por tramo (3–6) + Progresiones. Chile: Objetivos de Aprendizaje (OA) de Ciencias Naturales en Bases Curriculares 1.°–6.° (p. 70+) y 7.°–2.° medio (p. 128+). Colombia: Estándares por grupo de grados (1–3, 4–5, 6–7, 8–9, 10–11) y DBA por grado. Singapur: Primary Science 2023 (P3–P6).
2. Alinea cada objetivo de país con el catálogo TIMSS (mismo método: objetivo principal/secundario/FUERA, confianza, justificación) → así todos los países se comparan contra el mismo pivote, nunca país contra país.
3. Agrega al libro una hoja `Comparacion_paises`: por objetivo TIMSS, en qué grado lo introduce cada país y El Salvador (columna «primer grado»), y una métrica de «oportunidad» = grado SV − mediana de grado de los demás (positivo = El Salvador llega tarde).
4. Informe: 10 objetivos donde El Salvador llega más tarde o no llega, y 10 donde va adelantado.

Pregunta antes de: agregar países nuevos, cambiar metas, o tocar la clasificación v1 revisada por el equipo de Ciencias.
