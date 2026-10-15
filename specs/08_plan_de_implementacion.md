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

## Fase 5-quater · El grafo principal pasa a la malla V2 ✅ (2026-10-11)
La V2 del MINED contiene los 1.260 temas de la V1 sin cambios (mismo id, hoja, fila y texto; lo verifica
`tests/test_mallas.py`) y agrega 47 en 2.°–9.°. `config/mallas.yaml` lee la V2 y la V1 queda en `config/mallas_v1.yaml`.
- Las clasificaciones previas TIMSS/PISA se traducen al nombre de archivo de la V2 (`legado` en la config); los 47 temas
  nuevos se alinearon con los mismos prompts (`gskg alinear preparar-temas | unir-temas`) y se etiquetaron con conceptos
  (`preparar-etiquetado` solo prepara pendientes). Cuatro cambian de asignatura por coherencia con su unidad
  (`revisiones/2026-10-11_coherencia_asignatura_v2.json`, pendiente del MINED).
- Grafo: 1.307 temas (1.292 en alcance), 3.675 nodos y 20.538 aristas; objetivos de marco cubiertos 306 → 317. La V2
  cubre «Herencia y estrategias de reproducción» (TIMSS 4.°), el único objetivo de Biología 4.° sin tema en la V1.
- Grados: 29 bloques temáticos nuevos con resumen (ronda R4). GraphRAG sin cambios (MRR 0,849 / 0,661 / 0,544 / 0,734).
- **Conciliación de las propuestas** (`data/interim/propuestas/adopcion_v2.json`): de 47 acciones «nuevo», el MINED adoptó
  5 en el mismo grado (Física y Tierra y Espacio de 3.°–4.°), 8 en otro grado y 8 en parte; 26 siguen pendientes. Las
  adoptadas no se vuelven a simular y `asignaturas/PROPUESTAS.md` lista la conciliación. Falta confirmarla con el MINED.

## Fase 5-ter · Grafos internacionales de 2.°–8.° (spec 12) ✅ (2026-10-11; método v2 el 2026-10-12)
Código por tramo (`--tramo 2_8`), catálogo `config/internacional_2_8.yaml`. HK P1–6 y S1–3 y ON 1–8 descargados
(2026-10-09). 9 países, 3.615 objetivos, 448 conceptos en consenso; `internacional/2_8/`. La verificación de 24
hallazgos dio 7 confirmados, 6 parciales y 11 falsos (etiquetado de la V2): se corrigió la regla de «tardío» después del
tramo (≥ 2 grados) y se registraron 11 correcciones expertas. Solo se presentan los hallazgos verificados del README.
**Método v2 (2026-10-12):**
- doble lectura (amplia y estricta; si difieren, «incierto»);
- segundo etiquetado de la V2 (el del grafo principal) y búsqueda de texto como frase en toda la fila;
- mínimo de 3 países para «adelantado»;
- 7 relaciones «parte de»;
- secuencias prudentes;
- metadatos de EE, SG y HK corregidos sin Vertex.

Una muestra nueva al azar de 24 hallazgos dio 13 confirmados, 5 parciales y 6 falsos (25 %, antes 46 %). En total hay
19 correcciones expertas, 150 inciertos y ningún gasto en Vertex. Pendiente: la confirmación del MINED y revisar los
inciertos.

## Fase 7 · Apoyo al aprendizaje (spec 13) · prototipo ✅ (2026-10-11; tutor y evaluador el 2026-10-12)
`src/goes_science_kg/aprendizaje/`, `gskg tutor …`, `config/aprendizaje.yaml`. Relaciones con inversa explícita (una
arista, dos lecturas), diagnóstico por hipótesis que se comprueban, refuerzo previo/durante/posterior con límites,
estado por estudiante fuera de las capas compartidas, cola de propuestas a revisión. Capa pedagógica de 3 objetivos de
9.° (55 actividades, 13 dificultades, 13 microtemas; todo propuesta pendiente) y tres recorridos reproducibles en
`aprendizaje/recorridos/`.

**2026-10-12:**
- **Tutor conversacional** (`tutor.py`) con guardas deterministas.
- **Evaluador de respuestas abiertas** (`evaluador.py`): separado del tutor, con citas literales y revisión docente.
- **Modelos intercambiables** (`llm.py`): Vertex sin caché, solo con `--confirmar`.
- **Formato «abierta»** con rúbrica en la capa pedagógica.
- **Contenido de 3.°, 5.° y 7.°:** 96 actividades, 21 dificultades y 21 microtemas en total.
- **Recorridos R4 y R5:** primaria y revisión docente.
- **Propuesta de piloto y de política de datos:** `aprendizaje/PILOTO.md`.

Pendiente: revisión del contenido, prueba con el modelo real (requiere aprobación del gasto), interfaz y las
decisiones del piloto.

**Paquetes de clase, corte 2026-10-15:**
- [x] 230 paquetes ligeros de Física y Química de 9.°–11.°, en `entregas/paquetes_clase/`.
- [x] Continuación del panel interrumpido: 152 vistos buenos cerrados con Codex (47 aprobar, 105 corregir), sin
  llamadas nuevas a Vertex. Se conservan los dictámenes previos de Claude y las redacciones de Gemini.
- [ ] Seis elementos sin consenso, compartidos por 12 paquetes, esperan decisión humana; los datos de referencia
  de los 230 paquetes siguen pendientes de fuente citable. La revisión IA no sustituye la firma docente.

## Fase 8 · Panel de expertos IA (spec 14) ✅ (2026-10-12)
`panel.py`, `gskg panel …`, `config/panel.yaml`, cinco agentes en `.claude/agents/` y el hook SubagentStop. Es una
revisión técnica interina mientras no haya un equipo del MINED.
- **Alcance:** 510 expedientes en 3 rondas, con 32 subagentes.
- **Resultados:** 493 resueltos, 17 sin consenso (para una persona) y lo resuelto ya aplicado en las capas, con su
  procedencia.
- **Lo que corrigió:**
  - 69 elementos de la capa pedagógica;
  - 135 clases del contraste de 2.°–8.°;
  - 7 asignaciones de concepto;
  - las etiquetas de 4 temas.
- **Decisiones del piloto:** `aprendizaje/PILOTO.md`, sección 0.
- **Lo que se construyó a partir de sus dictámenes:**
  - salvaguardas para menores;
  - opciones barajadas;
  - respuestas numéricas tolerantes;
  - límites de refuerzo para primaria;
  - el verificador de fidelidad, obligatorio.

## Fase 8.1 · Bucle de fortalecimiento del panel (spec 14, sección 7) ✅ (2026-10-13)
`bucle.py`, `gskg bucle …`, el subagente `refutador` y su validación de citas por código. Convergió en 2 vueltas:
- 24 dictámenes corregidos;
- 820 anclas literales;
- de 486 dictámenes resueltos, 468 sólidos, 17 respaldados y 1 frágil (más 17 sin consenso del panel original).

Corrigió hallazgos (efecto invernadero, potencia eléctrica, leyes de los gases, fuerzas intermoleculares) y siete
errores del contenido de 7.° y 9.°. Snapshots por ciencia en `panel/bucle/`.

## Fase 9 · Entrega V3 del MINED y refuerzo por tema (spec 15)
Decisiones del responsable (2026-10-13): la V3 es la malla vigente, el refuerzo va en copias de las matrices del MINED
con filas «Propuesta GOES» y se inyectan correcciones, recomendaciones del panel, hallazgos del contraste y lo que la
V3 quitó.
- [x] 15.0 Ingesta de la V3 y correspondencia V2 → V3 ✅
- [x] 15.1 Migración de las capas por la correspondencia ✅
- [x] 15.2 Etiquetado de los temas nuevos y parecidos (Vertex con aprobación) ✅
- [ ] 15.3 Grafo y contraste recalculados sobre la V3; inciertas nuevas al panel y al bucle
- [ ] 15.4 Catálogo de refuerzos por tema
- [ ] 15.5 Redacción (`redactor-refuerzos`) y revisión del panel y del bucle
- [ ] 15.6 Matrices reforzadas y resumen por grado

## Fase 6 · Revisión con el MINED y publicación
- CSV de revisión y reimportación de decisiones.
- Explorador HTML del grafo por asignatura (siguiendo el de `reportes/`).
- Opcional: API de lectura y exportación a Neo4j, como en `goes-math-kg`.
