# Traspaso para la próxima sesión de Claude Code

> Sesión del 2026-10-05 (14:10–18:10). Rol: experto en educación científica e ingeniero de IA, grafos y GraphRAG.
> Objetivo de la sesión: construir los **grafos por grado** (lo que pidió el MINED) y dejar el proyecto listo para
> proponer una curricularización mejor, anclada en marcos internacionales y países de alto desempeño.

## Cómo retomar (5 minutos)
```bash
uv sync --extra dev --extra pdf --extra analisis --extra rag
uv run make todo        # grafo → validar → fichas → grados → brechas → pruebas → lint (todo en verde)
uv run gskg evaluar-rag # MRR y recall@k de GraphRAG
```
Lee, en orden: `CLAUDE.md` → este archivo → `specs/08_plan_de_implementacion.md` → `specs/09` y `specs/10`.

## Qué existe hoy
| Pieza | Dónde | Estado |
|---|---|---|
| Grafo completo | `data/grafo/` (JSONL + manifest) | 1.260 temas · 512 conceptos (14 del triaje) · 30 prácticas · 493 objetivos de marco · 1.265 objetivos de 6 países · 829 prerrequisitos (DAG) |
| **Grafos por grado** | `grados/` (index.html, G02…G11 con ficha.md + grafo.html) y `data/grafo/grados/` | Diagnóstico, bloques temáticos con resumen y visor interactivo |
| Países | `data/interim/paises/` (ENG, AU, JP) + legado (UY, CO, SG) | Inglaterra (KS1–KS4), Australia y Japón extraídos, etiquetados y alineados (Japón desde el texto oficial del MEXT, en japonés); desempeño TIMSS 2023 verificado y citado en `config/referentes.yaml` |
| GraphRAG | `src/goes_science_kg/rag.py`, `gskg rag` | Local y citado; `--global` (bloques); `--responder` (Claude, probado con un cliente simulado, nunca contra la API real); 60 preguntas (8 de Japón): MRR 0,77 y recall@25 0,83 (ver `data/evaluacion/resultados.md`); la intención de país reconoce nombres y gentilicios |
| API de lectura | `src/goes_science_kg/api.py`, `gskg servir` | FastAPI: grados, conceptos, propuestas, rag |
| Mapas de progresión | `asignaturas/<x>/progresion.html` | Concepto × grado: SV frente a países, ordenado por el grafo de prerrequisitos |
| Brechas | `asignaturas/<x>/brechas/` | md + json + csv + Excel con fórmulas; mediana de todos los países y solo de los de alto desempeño (AU, ENG, JP, SG) |
| Propuestas | `asignaturas/<x>/propuesta/`, resumen en `asignaturas/PROPUESTAS.md` | Borradores 2.°–11.° verificados con el simulador |
| Revisión humana | `asignaturas/<x>/revision/` + `gskg revision exportar/importar` | CSV listos para el MINED (no se han devuelto) |
| Revisiones aplicadas | `data/interim/revisiones/` | 19 temas reasignados de asignatura (revisión experta, pendiente de validación del MINED) |

## Decisiones tomadas en esta sesión (y por qué)
1. **Conceptos con vocabulario por asignatura, derivado de los marcos** (TIMSS/PISA/ACARA) y completado con la malla. Así los conceptos tienen granularidad comparable entre países.
2. **Primer grado en El Salvador** = grado mínimo donde el concepto es principal, o secundario con confianza alta o media. Usar cualquier etiqueta inflaba falsos errores de secuencia; exigir confianza alta dejaba fuera temas reales (p. ej. G02-2.6, calentamiento).
3. **Conceptos equivalentes entre asignaturas** (11 pares revisados) comparten el primer grado.
4. **Países: etiquetado directo** de sus objetivos con conceptos. La herencia vía el objetivo TIMSS era demasiado gruesa (ej.: atribuía «herencia mendeliana» a 5.°).
5. **Equivalencia de grados por edad de ingreso** (`config/referentes.yaml`) y **punto medio** para objetivos por banda (KS3, Estándares de Colombia).
6. **Revisiones ganan sobre IA** (`revisiones.py`). Los archivos se nombran con fecha y gana el último.
7. **Resúmenes de bloques** ligados a sus conceptos con tolerancia Jaccard ≥ 0,75, porque Louvain cambia un poco cuando el grafo cambia.
8. **Simulador de propuestas**: cada propuesta se aplica al grafo y se mide antes y después. Gracias a él, la propuesta de Biología 5.°–8.° v1 se corrigió porque creaba 4 errores de secuencia nuevos.

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
   devuelve 403 a `curl`/WebFetch; abrir el anexo B1 (tabla I.B1.2.3) en el navegador o usar el PISA Data Explorer.
4. **Calidad de datos.**
   - 534 aristas de confianza baja (ver `gskg grafo validar`).
   - 292 conceptos propuestos por el etiquetado: ✅ triados en `data/interim/conceptos/triaje_propuestos.json`
     (84 sinónimos de conceptos existentes, 167 descartes con motivo, 41 propuestas agrupadas en 15 conceptos nuevos:
     14 de Biología, p. ej. niveles de organización ecológica, tejidos animales, grupos de plantas, selección
     artificial; 1 de Física). **Ya aplicado como capa** (`conceptos.triaje()`): los 14 conceptos de confianza media o
     alta entran al vocabulario, 142 temas suman el concepto que propusieron y 32 prerrequisitos sugeridos entran con
     confianza media. Los países no están etiquetados con esos 14 conceptos (no tienen comparación internacional).
     Efecto: Física 10.°–11.° pasa de 1→0 a 3→2 errores de secuencia y Química 10.°–11.° de 3→1 a 5→3; revisar
     esas dos propuestas con `prompts/subagentes/msg_v3_japon.md` adaptado.
   - Algunos conceptos amplios mezclan niveles, por ejemplo «Ondas sísmicas, magnitud e intensidad»; conviene dividirlos.
5. **GraphRAG.**
   - Intención «marco» (priorizar `ObjetivoMarco` cuando se nombra TIMSS, PISA o ACARA).
   - Búsqueda densa para sinónimos.
   - Pasar el conjunto de evaluación de «plata» a «oro» con el equipo de Ciencias.
   - Panel docente sobre la API de lectura que ya existe (`gskg servir`).
6. **Excel.** Recalcular `Brechas_*.xlsx` y `Propuesta_*.xlsx` con Numbers (ver el `CLAUDE.md` de reportes) para verificar que las fórmulas den 0 errores. No se hizo en esta sesión.
7. **Bachillerato.** Las propuestas de 10.°–11.° no tienen comparación con países. Por edad, el KS4 inglés (ya en el grafo) equivale a 8.°–9.°, no a Bachillerato; 10.°–11.° (16–18 años) corresponde a A-level, que no es currículo nacional, y a Senior Secondary de Australia, que ya es el pivote (AUSS). Para comparar habría que sumar otro país con currículo nacional de 16–18 años (p. ej., Singapur H2, si el SEAB vuelve a publicar sus programas).

## Cuidado con
- `reportes/cobertura_curricular/` no se toca. Sus fuentes son enlaces simbólicos a `data/fuentes/`.
- Las propuestas son **borradores**. Ninguna quita temas; quitar requiere preguntar al usuario.
- Git tiene `core.autocrlf=input`. Las fuentes y los reportes se guardan byte a byte (`.gitattributes`). Los CSV generados usan LF.
- El sitio v8 de ACARA es muy lento (errores 524). La unidad 4 de Senior Secondary salió del Internet Archive.
- Los subagentes comparten el scratchpad. Pídeles subcarpetas únicas.
