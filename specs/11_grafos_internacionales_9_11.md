# 11 · Grafos internacionales de 9.° a 11.° y contraste con la malla Versión 2

> Pedido del 2026-10-07: construir, por ciencia, grafos de conocimiento de países con educación científica de
> excelencia para 9.°–11.° y contrastarlos con las mallas sugeridas (Versión 2). Rol: especialista en educación
> científica. Trabajo con la cuenta GOES (git y GCP).

## Alcance
- **Asignaturas:** Biología, Física, Química y Ciencias de la Tierra y del Espacio. En El Salvador, 9.° es
  «Ciencias» integrada (12 unidades en V2) y 10.°–11.° son tres asignaturas separadas; Tierra y Espacio no existe
  en Bachillerato. Esa ausencia es un hallazgo estructural que se mide, no se omite.
- **Países (9):** Singapur, Japón, Corea del Sur, Inglaterra, Australia, Hong Kong, Taiwán, Estonia, Ontario.
  Hong Kong y Taiwán se agregaron a `config/referentes.yaml` con autorización del usuario (2026-10-07).
- **Malla a contrastar:** Versión 2 (`config/mallas_v2.yaml` → `data/fuentes/mined/Mallas sugeridas v2/`).
  El grafo principal sigue leyendo la Versión 1.

## Equivalencia de grados (por edad de ingreso; SV 1.° ≈ 7 años)
| País | SV 9.° (≈15) | SV 10.° (≈16) | SV 11.° (≈17) | Fuera de rango |
|---|---|---|---|---|
| Singapur | Sec 3 | Sec 4 | JC1 | JC2 |
| Hong Kong | S4 | S5 | S6 | — |
| Inglaterra | Year 11 | Year 12 | Year 13 | — |
| Australia | Year 10 | Year 11 (unidades 1–2) | Year 12 (unidades 3–4) | — |
| Japón / Corea / Taiwán | 高1 / 고1 / 高一 | 2.° año | 3.° año | — |
| Estonia | grado 9 | grado 10 | grado 11 | grado 12 |
| Ontario | Grade 10 | Grade 11 | Grade 12 | — |

Consecuencia crítica: en casi todos los referentes la escuela termina un año después que en El Salvador. Un
contenido que el país ubica en su último año puede quedar fuera del rango comparable; se marca como
`fuera_de_rango` y no cuenta como faltante de El Salvador.

## Dos niveles por país
- **núcleo:** lo que cursa la mayoría de los estudiantes, como Ciencia Integrada en Corea, los cursos 基礎 de
  Japón, Combined Science en Singapur e Inglaterra, Year 10 en Australia o Grade 10 en Ontario.
- **especialización:** la asignatura electiva, como A-level, H2, 物理/化学/生物, Senior Secondary o Grades 11–12 de Ontario.

El Bachillerato salvadoreño es general y obligatorio en las tres ciencias. Por eso **el contraste principal se
hace contra el núcleo**. La especialización funciona como **techo**: muestra hasta dónde llega un estudiante
que elige la ciencia, no lo que debería saber todo estudiante.

## Modelo
- `ObjetivoPais`: unidad mínima evaluable del documento. Lleva `pais`, `documento`, `pagina` o `localizador`,
  `curso`, `nivel`, `grado_sv_min`, `grado_sv_max`, `asignatura`, `texto` (paráfrasis en español de ≤30
  palabras), `tipo` (conocimiento, práctica o aplicación) y `demanda` (recordar, aplicar o razonar, la
  escala de TIMSS).
- Etiquetado `objetivo → concepto` con el vocabulario por asignatura (`data/interim/conceptos/vocabulario.json`).
  Cada etiqueta es principal o secundaria y lleva confianza, justificación (≤15 palabras) y versión.
  Los conceptos nuevos se proponen como `PROPUESTO:<nombre>` y pasan por triaje: no se inventan ids.
- **Grafo por país y asignatura:** objetivos, conceptos, `ENSEÑA` y la secuencia interna del país.
  Los prerrequisitos entre conceptos se toman del grafo existente (829) y se completan para los conceptos nuevos.
- **Grafo de consenso por asignatura:** por concepto guarda en cuántos países aparece (núcleo y
  especialización), el grado SV de primera aparición (mediana y rango) y la profundidad típica.

## Uso de la IA (Vertex AI, proyecto GOES)
Se siguen las convenciones de `goes-math-kg`: credenciales por defecto (ADC), sin claves en el código, y
**modelos distintos para extraer y para validar**.
| Paso | Modelo | Control |
|---|---|---|
| Extraer objetivos por página | `gemini-3.1-pro-preview` (región `global`) | Cada objetivo cita una página que existe |
| Validar la fidelidad de cada objetivo contra el texto de su página | `gemini-2.5-pro` | Si sale «no fiel», se descarta; si sale «parcial», va a revisión |
| Etiquetar conceptos (objetivos de países y temas de la malla V2) | `gemini-2.5-pro` | Ids validados contra el vocabulario |
| Revisión experta de los hallazgos | Claude (esta sesión) | Lectura crítica y muestreo manual |
Las respuestas se guardan en caché (`data/interim/internacional/cache/`, sin versionar) con la clave
sha256(modelo, prompt), para que reconstruir no cueste de nuevo y las corridas sean reproducibles.

## Contraste con la malla V2
Por asignatura y grado:
1. **Cobertura del núcleo:** conceptos que enseñan ≥ 5 de 9 países en el núcleo hasta el grado SV
   equivalente y que la malla no tiene.
2. **Momento:** conceptos que la malla ubica ≥ 2 grados antes o después de la mediana internacional.
3. **Excesos:** contenidos de la malla que ningún país tiene en el núcleo, o que solo aparecen en especialización.
4. **Secuencia:** temas de la malla cuyo concepto aparece antes que sus prerrequisitos.
5. **Profundidad:** distribución de la demanda cognitiva en la malla frente al núcleo de los países.
6. **Prácticas científicas:** indagación, modelación y argumentación frente a los objetivos de práctica de los países.
Cada hallazgo cita los objetivos de los países (documento y página) y los temas de la malla (archivo, hoja y fila).

## Entregables
- `data/interim/internacional/objetivos/<pais>.json` (objetivos validados) y los etiquetados.
- `data/grafo/internacional/` con los grafos por país y asignatura, y el consenso (JSONL y manifest).
- `internacional/` con un informe por asignatura, el contraste con la V2, un Excel con fórmulas y un visor HTML.
- CSV de revisión humana con lo que tenga confianza baja.

## Ajustes de método tras la revisión experta (2026-10-08)
La primera corrida produjo artefactos que la revisión manual detectó. El detalle y la validación están en
`internacional/README.md`.
- **Momento:** «adelantado» y «tardío» solo se juzgan para lo que la V2 introduce en 9.°–11.°. Los datos de los
  países no permiten fechar la primaria salvadoreña.
- **Clases nuevas:** «no retomado» (la V2 solo lo ve antes de 9.° y ≥ 5 países lo profundizan en su núcleo de
  9.°–11.°), «retomado» y «previo».
- **Consenso:** ≥ 5 países con núcleo, como dice esta spec. El código usaba ≥ 50 % y ≥ 3.
- **Presencia en la V2:** es la unión de dos etiquetados de 9.°–11.° (vocabulario de la asignatura y vocabulario
  completo) más las equivalencias revisadas entre asignaturas. Así, un hueco de El Salvador tiene que resistir el
  ruido de la IA.
- **Puntos 5 y 6:** la demanda se mide con un mismo clasificador por verbos (escala TIMSS) en los dos lados, y las
  prácticas por cobertura del catálogo.
- **Secuencia:** los errores automáticos son candidatos (2 de 4 falsos en la muestra) y solo se afirman los
  verificados.
