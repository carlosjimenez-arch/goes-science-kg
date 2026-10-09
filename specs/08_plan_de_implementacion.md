# 08 · Plan de implementación

Fases en orden. Cada tarea tiene una definición de terminado (DdT). Al cerrar una fase se
muestra el resultado al usuario antes de seguir, se actualiza este archivo (✅) y se hace commit.

## Fase 0 · Base del repo ✅
- [x] Estructura del repo, `config/`, paquete `goes_science_kg`, pruebas.
- [x] Fuentes únicas en `data/fuentes/`; `reportes/cobertura_curricular` sigue funcionando por enlaces simbólicos.
- [x] Grafo v0 desde los datos previos (`gskg grafo construir`) y fichas por asignatura.

## Fase 1 · Fuentes y referentes
1. **Verificar los países de alto desempeño.** Descargar los informes internacionales de
   TIMSS 2023 (IEA) y PISA 2022 Vol. I (OCDE). Registrar en `config/referentes.yaml` la posición
   de cada país con documento y página. DdT: cada país tiene `evidencia_desempeno` citada.
   *Avance:* TIMSS 2023 ✅ (anexos 2.1.1 y 2.2.1, citados). PISA 2022 pendiente: la OCDE responde 403 a descargas automáticas.
2. **Descargar currículos** (skill `fuentes-descargar`): Chile (a mano si sigue bloqueado),
   Singapur Lower Secondary, Japón, Corea, Estonia, Inglaterra, Australia, Finlandia y Ontario.
   DdT: `estado.csv` con sha256; las faltantes, documentadas con su URL.
   *Avance:* Inglaterra KS1–KS4 ✅, Australia v9 F–10 ✅, Japón 2017 ✅ (texto oficial vía jp-cos). Finlandia y Corea
   descartados por ahora (idioma y bandas; ver spec 03). Pendientes: Chile, Singapur Lower Secondary, Estonia, Ontario.
3. ✅ **Pivote para Química y Biología de 10.°–11.°**: ACARA Senior Secondary v8.4 (spec 03). Catálogo y alineación de los 371 temas hechos.
4. Completar las páginas del catálogo TIMSS Advanced Física.
5. Módulos `ingesta/paises.py` e `ia/lotes.py` (preparar y unir lotes, validar códigos) con pruebas.

## Fase 2 · Alineación de países nuevos
1. Extraer los objetivos de cada país (skill `pais-extraer-objetivos`) → `data/interim/paises/<pais>.json`.
2. Hacer una muestra de control de 20 ítems por país y luego los lotes completos (skill `alinear-objetivos`).
3. Integrarlos al grafo (`construir.py` lee `data/interim/alineaciones/` además del legado).
   DdT: `gskg grafo validar` sin errores; una ficha por asignatura con ≥7 países.
   *Avance:* 6 países (1.265 objetivos), los 3 nuevos etiquetados con conceptos y alineados a TIMSS 2027.

## Fase 3 · Conceptos, prácticas y prerrequisitos ✅ (2026-10-05)
Hecho: 498 conceptos (vocabulario por asignatura, prompt `prompts/vocabulario_conceptos.md`), 30 prácticas,
1.245 temas y 506 objetivos de países etiquetados, 797 prerrequisitos (DAG), 11 equivalencias entre asignaturas,
los 49 temas sin asignatura resueltos (34 asignados y 15 fuera de alcance). Después: 292 conceptos propuestos
triados (14 nuevos, capa `triaje_propuestos.json`; hoy 512 conceptos y 829 prerrequisitos) y 1.265 objetivos de 6 países
etiquetados. Pendiente: revisión humana de las etiquetas de confianza baja y del triaje.
1. Skill `grafo-asignar-disciplina`: los 49 temas sin asignatura.
2. Skill `grafo-conceptos`: vocabulario canónico de conceptos por asignatura y aristas TRABAJA
   desde temas, objetivos de marco y objetivos de país.
3. Prácticas científicas a partir de TIMSS Investigations, PISA (procedimental y epistémico) y NGSS SEP.
4. Skill `grafo-prerrequisitos`: el DAG por asignatura. Evidencias: el orden observado en los
   países (primer grado), las Progresiones de Uruguay, las progresiones de NGSS y la dependencia
   lógica (con justificación). Agregar el invariante «sin ciclos».
   DdT: DAG validado y muestra revisada a mano.

## Fase 3-bis · Grafos por grado y GraphRAG ✅ (2026-10-05)
- `gskg grados construir`: subgrafo, diagnóstico, bloques temáticos (Louvain + resúmenes de especialista) y visor
  HTML por grado (spec 09).
- GraphRAG local y citado + búsqueda global por bloques + evaluación con 40 preguntas (spec 10).

## Fase 4 · Análisis de brechas por asignatura · 1.ª versión ✅ (2026-10-05)
`gskg brechas`: cobertura por ciclo, oportunidad por concepto y secuencia (md + json + csv). Falta el Excel con fórmulas.

- `analisis/`: cobertura, balance, profundidad, nivel cognitivo y oportunidad (todos los países
  y solo alto desempeño), por ciclo. Prerrequisitos que llegan tarde.
- Salida en `asignaturas/<x>/brechas/` (Excel con fórmulas + `brechas.md`).
- DdT: las cifras de cobertura de 2.°–8.° coinciden con el libro de `reportes/` cuando se usan
  solo los tres países previos (prueba de regresión).

## Fase 5 · Propuesta curricular por asignatura · borradores 2.°–8.° ✅ (2026-10-05)
7 borradores verificados con el simulador (`asignaturas/PROPUESTAS.md`). Falta Bachillerato y la revisión del MINED.

- `propuesta/` según la spec 06. Empezar por **Biología de 5.°–8.°**: es la brecha más clara del
  informe de países (llega un año tarde frente a los tres países).
- DdT: presupuesto cuadrado, DAG respetado, cada cambio con evidencia e informe por asignatura.

## Fase 5-bis · Grafos internacionales de 9.°–11.° y contraste con la malla V2 ✅ (2026-10-08)
Spec 11. 9 países, 62 documentos y 9.040 objetivos (con la secundaria baja de KR, TW y ON) (Vertex AI: un modelo extrae y otro valida), grafo y consenso en
`data/grafo/internacional/`, informes, Excel y CSV de revisión en `internacional/`, y hallazgos verificados en
`internacional/README.md`, y visor en `internacional/visor.html`. Falta la revisión del MINED.

## Fase 5-ter · Grafos internacionales de 2.°–8.° (spec 12) · lista para ejecutar
Código por tramo (`--tramo 2_8`), catálogo `config/internacional_2_8.yaml` y costo estimado (116 llamadas de
extracción). Pendiente: aprobación del gasto y descarga de HK y ON 1–8.

## Fase 6 · Revisión con el MINED y publicación
- CSV de revisión y reimportación de decisiones.
- Explorador HTML del grafo por asignatura (siguiendo el de `reportes/`).
- Opcional: API de lectura y exportación a Neo4j, como en `goes-math-kg`.
