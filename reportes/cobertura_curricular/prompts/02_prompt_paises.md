# Prompt 02 · Comparación con currículos de otros países (después del Prompt 01)

Lee CLAUDE.md. El pivote de comparación es el catálogo TIMSS 2027 (`data/referencia/catalogo_timss2027.json`): todos los países se alinean contra él, nunca país contra país.

0. Corre `python scripts/descargar_fuentes.py`. Si Chile, Colombia, Singapur o ERCE siguen en FALTA, dime cuáles y su URL para bajarlos a mano; avanza con los países disponibles (Uruguay ya está).
1. Por cada país en `data/referencia/externos/paises/`, extrae los objetivos de aprendizaje por grado/tramo a `data/interim/paises/<pais>.json`: pais, documento, pagina, grado_o_tramo, eje/área, texto (paráfrasis o literal corto ≤ 30 palabras), id estable.
   - Uruguay: programas EBI por tramo (3–6) + Progresiones. Chile: OA de Ciencias Naturales, Bases 1.°–6.° (p. 70+) y 7.°–2.° medio (p. 128+). Colombia: Estándares por grupo de grados y DBA por grado. Singapur: Primary Science 2023 (P3–P6).
2. Alinea cada objetivo de país con el catálogo 2027 (subagentes, mismo método: obj1/obj2/FUERA, confianza, justificación).
3. Agrega al libro 2027 la hoja `Comparacion_paises`: por objetivo TIMSS 2027, primer grado en que lo introduce cada país y El Salvador, y «oportunidad» = grado SV − mediana de los demás (positivo = El Salvador llega tarde).
4. Informe: los 10 objetivos donde El Salvador llega más tarde o no llega y los 10 donde va adelantado.

Pregunta antes de agregar países nuevos, cambiar metas o tocar clasificaciones revisadas por el equipo de Ciencias.
