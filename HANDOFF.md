# Traspaso para la próxima sesión de Claude Code

> Sesión del 2026-10-05 (14:10–18:10; commits a las 14:59, 15:37, 16:25, 17:07 y al cierre). Rol: experto en educación científica e ingeniero de IA, grafos y GraphRAG.
> Objetivo de la sesión: construir los **grafos por grado** (lo que pidió el MINED) y dejar el proyecto listo para
> proponer una curricularización mejor, anclada en marcos internacionales y países de alto desempeño.

## Cómo retomar (5 minutos)
```bash
uv sync --extra dev --extra pdf --extra analisis --extra rag --extra api
uv run make todo        # grafo → validar → fichas → grados → brechas → pruebas → lint (todo en verde)
uv run make propuestas  # simula las 11 propuestas sobre el grafo actual y rehace PROPUESTAS.md
uv run gskg evaluar-rag # MRR y recall@k de GraphRAG
```
Lee, en orden: `CLAUDE.md` → este archivo → `specs/08_plan_de_implementacion.md` → `specs/09` y `specs/10`.

## Qué existe hoy
| Pieza | Dónde | Estado |
|---|---|---|
| Grafo completo | `data/grafo/` (JSONL + manifest) | 1.260 temas · 512 conceptos (14 del triaje) · 30 prácticas · 493 objetivos de marco · 1.265 objetivos de 6 países · 829 prerrequisitos (DAG) |
| **Grafos por grado** | `grados/` (index.html, G02…G11 con ficha.md + grafo.html) y `data/grafo/grados/` | Diagnóstico, bloques temáticos con resumen y visor interactivo |
| Países | `data/interim/paises/` (ENG, AU, JP) + legado (UY, CO, SG) | Inglaterra (KS1–KS4), Australia y Japón extraídos, etiquetados y alineados (Japón desde el texto oficial del MEXT, en japonés); desempeño TIMSS 2023 verificado y citado en `config/referentes.yaml` |
| GraphRAG | `src/goes_science_kg/rag.py`, `gskg rag` | Local y citado; `--global` (bloques); `--responder` (Claude, probado con un cliente simulado, nunca contra la API real). Conjunto de ajuste (60 preguntas): MRR 0,85. **Conjunto de prueba independiente (16): MRR 0,65**, sin mejora frente a antes de la sesión (ver `data/evaluacion/resultados.md`); la intención de país reconoce nombres y gentilicios |
| API de lectura | `src/goes_science_kg/api.py`, `gskg servir` | FastAPI: grados, conceptos, propuestas, rag |
| Mapas de progresión | `asignaturas/<x>/progresion.html` | Concepto × grado: SV frente a países, ordenado por el grafo de prerrequisitos |
| Brechas | `asignaturas/<x>/brechas/` | md + json + csv + Excel con fórmulas; mediana de todos los países y solo de los de alto desempeño (AU, ENG, JP, SG) |
| Propuestas | `asignaturas/<x>/propuesta/`, resumen en `asignaturas/PROPUESTAS.md` | 11 borradores 2.°–11.° (Química 2.°–4.° v1 es mínima) verificados con el simulador: errores de secuencia de confianza alta 54 → 3. Los 3 dependen de aristas discutibles: Catalizadores → Enzimas, Ondas sísmicas → Precursores de sismos, Efecto Doppler → Big Bang; decidir con el MINED si se mantienen |
| Revisión humana | `asignaturas/<x>/revision/` + `gskg revision exportar/importar` | CSV listos para el MINED (no se han devuelto) |
| Revisiones aplicadas | `data/interim/revisiones/` | 19 temas reasignados de asignatura (revisión experta, pendiente de validación del MINED) |

## Hallazgos curriculares más fuertes (para conversar con el MINED)
Conceptos que al menos dos países de alto desempeño (SG, ENG, AU, JP) enseñan 4 o más grados antes que El Salvador
(grado SV equivalente por edad; dependen de etiquetas de IA por validar). Hay 34 con 3 o más grados de diferencia;
los principales:
| Concepto | Primer grado en SV | Mediana de alto desempeño | Países |
|---|---|---|---|
| Gravedad: atracción hacia la Tierra | nunca como concepto | 3.° | AU 3, ENG 3, SG 6 |
| Nutrición mineral de las plantas | 11.° | 3.° | ENG 2, JP 4 |
| Conductores y aislantes eléctricos | 11.° | 3,5 | ENG 2, JP 2, AU 5, SG 5 |
| Adaptaciones conductuales | 11.° | 4.° | JP 3, AU 4, SG 6 |
| Fricción y resistencia del aire | 10.° | 3.° | ENG 2, AU 3, SG 6 |
| Reflexión de la luz | 10.° | 3.° | ENG 2, JP 2, AU 4, SG 4 |
| Calor y equilibrio térmico | 9.°–10.° | 4.°–5.° | AU, ENG, SG |
| Herencia de rasgos | 10.° | 5.° | ENG 4, SG 5, JP 8 |
| Tiempo atmosférico | 7.° | 2.° | AU 2, ENG 2, JP 3 |
Varios ya tienen acción en las propuestas (circuitos y conductores en Física 2.°–4.°, tiempo atmosférico en Tierra y
Espacio, herencia en Biología 5.°–8.°). Gravedad: Física 2.°–4.° (v5) la introduce de forma cualitativa en 3.°
(G03-1.4, AU 3 y ENG 3) y recupera «Masa y peso» en 3.° justo después (G03-1.5). Lista completa: `asignaturas/<x>/brechas/` y
`grados/HALLAZGOS.md`.

## Decisiones tomadas en esta sesión (y por qué)
1. **Conceptos con vocabulario por asignatura, derivado de los marcos** (TIMSS/PISA/ACARA) y completado con la malla. Así los conceptos tienen granularidad comparable entre países.
2. **Primer grado en El Salvador** = grado mínimo donde el concepto es principal, o secundario con confianza alta o media. Usar cualquier etiqueta inflaba falsos errores de secuencia; exigir confianza alta dejaba fuera temas reales (p. ej. G02-2.6, calentamiento).
3. **Conceptos equivalentes entre asignaturas** (11 pares revisados) comparten el primer grado.
4. **Países: etiquetado directo** de sus objetivos con conceptos. La herencia vía el objetivo TIMSS era demasiado gruesa (ej.: atribuía «herencia mendeliana» a 5.°).
5. **Equivalencia de grados por edad de ingreso** (`config/referentes.yaml`) y **punto medio** para objetivos por banda (KS3, Estándares de Colombia).
6. **Revisiones ganan sobre IA** (`revisiones.py`). Los archivos se nombran con fecha y gana el último.
7. **Resúmenes de bloques** ligados a sus conceptos con tolerancia Jaccard ≥ 0,75, porque Louvain cambia un poco cuando el grafo cambia.
8. **Simulador de propuestas**: cada propuesta se aplica al grafo y se mide antes y después. Gracias a él, la propuesta de Biología 5.°–8.° v1 se corrigió porque creaba 4 errores de secuencia nuevos. Cualquier acción puede llevar `quitar_conceptos` para retirar una etiqueta mal puesta. **Límite:** cada simulación aplica solo la propuesta de su asignatura; un cambio en Biología que arregla una secuencia de Química no se ve en la simulación de Química (próximo paso: simulación conjunta por ciclo).
9. **Capas sobre la IA**: revisiones (`data/interim/revisiones/`), triaje de conceptos (`triaje_propuestos.json`) y etiquetado de países del triaje se aplican al cargar; volver a correr `unir-*` no las borra.
10. **GraphRAG**: la intención de país reconoce nombres y gentilicios; sin intención de país, los objetivos de país pesan ×0,8; ante una consulta de prerrequisitos, los conceptos pesan ×1,6 (ablaciones en `data/evaluacion/resultados.md`).

## Revisión de código de esta sesión (17:15) y correcciones
Un agente revisó `git diff 166852b..HEAD -- src tests`. Se corrigieron los 10 hallazgos (agrupados):
1. **Simulador:** las quitas de otras asignaturas ya no contaminan el reporte con nombres sin resolver. Se aplican todas
   las que resuelven; solo se listan las que tocan conceptos de la asignatura o sus equivalentes.
2. **Simulador:** los nombres repetidos entre asignaturas («Cambios de estado») se resuelven prefiriendo la asignatura
   que propone la acción.
3. **GraphRAG:** una consulta con marco y países sin nombrarlos ya no penaliza a los objetivos de país.
4. **GraphRAG:** las intenciones usan palabras completas («compartimentos», «paisaje» y «en inglés» ya no son país;
   «australianos» es país y no el marco ACARA).
5. **Lotes de países:** `preparar-paises` es idempotente (no repite objetivos que ya están en un lote) y la
   regeneración completa borra los lotes viejos del país.
6. **Triaje:** las aristas del triaje que repitan un par o cierren un ciclo se descartan al cargar.
7. **Resúmenes de bloques:** conservan el conjunto de conceptos para el que se escribieron, así que no derivan entre
   reconstrucciones.
8. **Cachés:** se limpian tras reescribir el vocabulario y los etiquetados.
9. **Pruebas:** verifican el camino real del código (`etiquetas_retiradas` en la simulación, regex con límites de
   palabra).

## Qué sigue (en orden de valor)
1. **Revisión del MINED.** Enviar `asignaturas/*/revision/*.csv`, `asignaturas/PROPUESTAS.md` y los informes. Al recibirlos: `gskg revision importar <csv>` → `make todo` → volver a simular las propuestas.
2. **Más países de alto desempeño.**
   - ✅ **Japón** (188 objetivos, 2.°–8.° SV). Fuente: `jp-cos` (github.com/jp-cos/jp-cos.github.io), el texto oficial del
     Course of Study 2017 como datos enlazados, ítem por ítem, con código MEXT (`localizador`) y página del comentario oficial.
     Ciencias = carpetas `826` (primaria) y `836` (secundaria baja); copia local en `data/fuentes/externos/paises/japon/` con
     `manifest_jpcos.json` (sha256). Insumo intermedio: `data/interim/paises_insumos/japon.json`. En secundaria baja el
     contenido real está en las hojas ㋐㋑… de los .ttl, no en los encabezados (ア)(イ).
   - Corea (2.° en 4.° grado): sin traducción oficial encontrada.
   - Finlandia (6.° en 8.° grado): ePerusteet solo está en finés y sueco y por bandas (1–2, 3–6, 7–9); se descartó por ahora.
   - Flujo probado: skill `fuentes-descargar` → `pais-extraer-objetivos` → `gskg conceptos preparar-paises` (solo pendientes) → etiquetar con `prompts/subagentes/prompt_paises.md` → alinear con `reportes/cobertura_curricular/prompts/alinear_paises.md` → `unir-paises` → `make todo`.
3. **PISA 2022 Vol. I (OCDE)** para completar la evidencia de desempeño en `referentes.yaml`. El sitio de la OCDE
   devuelve 403 a `curl`/WebFetch. En el navegador el anexo B1 sí carga (…/full-report/component-25.html), pero la
   tabla I.B1.2.3 viene plegada como imagen: descargar su Excel desde el enlace «Statlink» de la tabla (lo hace una
   persona; requiere aprobar la descarga) o usar el PISA Data Explorer.
4. **Calidad de datos.**
   - 630 aristas de confianza baja (ver `gskg grafo validar`); van a revisión humana en los CSV de `asignaturas/*/revision/`.
   - 292 conceptos propuestos por el etiquetado: ✅ triados en `data/interim/conceptos/triaje_propuestos.json`
     (84 sinónimos de conceptos existentes, 167 descartes con motivo, 41 propuestas agrupadas en 15 conceptos nuevos:
     14 de Biología, p. ej. niveles de organización ecológica, tejidos animales, grupos de plantas, selección
     artificial; 1 de Física). **Ya aplicado como capa** (`conceptos.triaje()`): los 14 conceptos de confianza media o
     alta entran al vocabulario, 142 temas suman el concepto que propusieron y 32 prerrequisitos sugeridos entran con
     confianza media. Un especialista buscó esos 14 conceptos en los objetivos de los 6 países
     (`etiquetado_paises_triaje.json`, 32 objetivos); 4 no aparecen en ningún país (conservación de alimentos,
     eutrofización, genética humana, MCUA).
     Efecto: subieron los errores de secuencia de Física y Química 10.°–11.°; ✅ ya resueltos en sus propuestas v2
     (y la de Biología 10.°–11.° v2, que retira etiquetas de Química de los temas de biomoléculas).
   - **Decidir si el triaje entra al vocabulario base** (hoy es una capa). Si el MINED lo valida, mover los 14 conceptos a
     `vocabulario.json` y borrar la capa; si no, basta con borrar `triaje_propuestos.json`.
   - Algunos conceptos amplios mezclan niveles, por ejemplo «Ondas sísmicas, magnitud e intensidad»; conviene dividirlos.
5. **GraphRAG.**
   - **Prioridad: la detección de intención no generaliza.** En 16 preguntas de prueba independientes
     (`data/evaluacion/rag_preguntas_prueba.json`; ver `resultados.md`, «Conjunto de prueba independiente»), la MRR es
     0,65 antes y después de los ajustes del día; prerrequisito 0,34 y marco 0,49. Ninguna de esas preguntas activa
     las intenciones. Hacer más robusta la detección (léxico amplio o un clasificador con Claude) y medir con un
     conjunto de prueba nuevo. No ajustar con el de prueba.
   - Hoy, por tipo: comparación 0,82, local 0,89, marco 0,85, prerrequisito 0,81 (en esta sesión: marco 0,71 → 0,85 al
     separar «currículo australiano» del país; prerrequisito 0,62 → 0,81). El conjunto es «plata» (60 preguntas): ampliar
     antes de seguir ajustando pesos.
   - Búsqueda densa para sinónimos.
   - Pasar el conjunto de evaluación de «plata» a «oro» con el equipo de Ciencias.
   - Panel docente sobre la API de lectura que ya existe (`gskg servir`).
6. ✅ **Excel.** Los 15 libros (`Brechas_*.xlsx` y `Propuesta_*.xlsx`) se recalcularon con Numbers (osascript, copias en el scratchpad; última vez el 2026-10-05 a las 17:25): 0 errores y 173 fórmulas con valor. Repetir tras regenerar los libros.
7. **Bachillerato.** Las propuestas de 10.°–11.° no tienen comparación con países. Por edad, el KS4 inglés (ya en el grafo) equivale a 8.°–9.°, no a Bachillerato; 10.°–11.° (16–18 años) corresponde a A-level, que no es currículo nacional, y a Senior Secondary de Australia, que ya es el pivote (AUSS). Para comparar habría que sumar otro país con currículo nacional de 16–18 años (p. ej., Singapur H2, si el SEAB vuelve a publicar sus programas).

## Cuidado con
- `reportes/cobertura_curricular/` no se toca. Sus fuentes son enlaces simbólicos a `data/fuentes/`.
- Las propuestas son **borradores**. Ninguna quita temas; quitar requiere preguntar al usuario.
- Git tiene `core.autocrlf=input`. Las fuentes y los reportes se guardan byte a byte (`.gitattributes`). Los CSV generados usan LF.
- El sitio v8 de ACARA es muy lento (errores 524). La unidad 4 de Senior Secondary salió del Internet Archive.
- Los subagentes comparten el scratchpad. Pídeles subcarpetas únicas.
