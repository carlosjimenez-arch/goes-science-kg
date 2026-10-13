# Reforzamiento de los dictámenes por ciencia

Este folder guarda los **snapshots del bucle de fortalecimiento** del panel de expertos IA. El método está en
[`specs/14_panel_expertos.md`](../../specs/14_panel_expertos.md), sección 7. Este README lo escribe el equipo; los
demás archivos los genera `uv run gskg bucle snapshot --etapa "<etapa>"` en cada etapa del bucle, y cada corte queda
en el historial de git.

| Archivo | Qué trae |
|---|---|
| [`RESUMEN.md`](RESUMEN.md) | totales por ciencia: impugnados, cambiados y solidez |
| [`biologia.md`](biologia.md), [`fisica.md`](fisica.md), [`quimica.md`](quimica.md), [`tierra-espacio.md`](tierra-espacio.md) | por ciencia: solidez por tipo, lo que el bucle cambió y por qué, lo mantenido frente a contraevidencia, lo frágil y los patrones de error |
| [`SNAPSHOT_9-11.md`](SNAPSHOT_9-11.md) | **de 11.° a 9.°** en un solo documento: por grado, lo que el bucle cambió, lo reabierto y mantenido, lo frágil y el detalle de cada dictamen con su cita literal verificada |
| [`SNAPSHOT_2-8.md`](SNAPSHOT_2-8.md) | **de 8.° a 2.°** en un solo documento, con la misma estructura e incluidos los dictámenes sin consenso, que decide una persona |
| [`grados/`](grados/RESUMEN.md) | un archivo por grado, de 11.° a 2.° (`G11.md` … `G02.md`), con la misma estructura, y un resumen por grado |

**Cómo leer la solidez:**
- **sólido:** sobrevivió al revisor adversarial y tiene una cita literal verificada por el código en una fuente
  primaria (en contenido: el revisor no encontró errores);
- **respaldado:** sobrevivió, pero con una fuente parafraseada, o la réplica lo mantuvo frente a contraevidencia
  anclada o a una discrepancia de la sonda ciega;
- **frágil:** sin fuente primaria verificable o cambiado en la última vuelta;
- **sin consenso:** decide una persona.

> Son dictámenes del panel de expertos IA, **no confirmaciones del MINED**. Usar contenido con estudiantes exige
> además la firma de un docente (`aprendizaje/PILOTO.md`).

## Primera corrida (2026-10-12 y 13): convergió en 2 vueltas
| Etapa | Resultado |
|---|---|
| Línea base (código, sin IA) | solo 91 de 360 dictámenes traían una cita literal en una fuente primaria; 165 evidencias eran circulares (README, contraste u otro dictamen) |
| Vuelta 1: impugnación | 486 dictámenes revisados por el refutador; 820 anclas literales nuevas; 35 reabiertos con contraevidencia anclada o por la sonda ciega |
| Vuelta 1: sonda ciega | 56 de 63 coinciden sin ver la resolución (89 %) |
| Vuelta 1: réplica | 24 cambiados y 11 mantenidos, todos por unanimidad |
| Vuelta 2 | de los 24 cambios, 21 se sostienen; 3 se reabren y la réplica los mantiene: el bucle se detiene |
| Solidez final | de los 486 resueltos: 468 sólidos, 17 respaldados y 1 frágil (organelos: el panel citó una página que no existe); además, 17 sin consenso del panel original (503 en total) |

**Lo que cambió y llega al MINED o al estudiante:**
- **Hallazgos:** el efecto invernadero **sí** se retoma en 9.°–11.° (microhabilidades de 10.° y 11.°); potencia eléctrica
  y leyes de los gases dejan de ser tardías; mitosis y capas de la atmósfera son adelantadas; fuerzas
  intermoleculares pasan a «sin referente»; calidad del aire, satélites, nomenclatura, flotación y conservación del
  agua quedan alineadas; epidemiología, posterior.
- **Recomendaciones precisadas:** la ley de Ohm se nombra en 6.° (no en 9.°); la física nuclear se coordina en 10.°;
  la reducción entra en 7.° acoplada a la oxidación; la neutralización se observa en 7.°.
- **Contenido para estudiantes (7.° y 9.°):** el ADN como «varios hilos» (no uno), «casi todos los genes» en pares,
  el Rh como otro gen, dos claves que se delataban por su largo, un ítem que se acertaba votando por la etiqueta más
  repetida y una práctica con agua «caliente» que pasa a tibia por seguridad.

## Errores y problemas de la propia malla (para el MINED)
**Errores científicos:**
- G05-CIE-U6-6.7: bordes de placa «pasivos»; lo correcto es «transformantes».
- G10-FIS-U16-16.1: atribuye la reflexión y la refracción al comportamiento corpuscular de la luz; el modelo
  ondulatorio las explica.
- G06-CIE-U2-2.6: explica que las noches de la costa son menos frescas que las de la montaña por la capacidad
  calorífica del agua; confunde el efecto de la altitud con el del agua (comparar costa e interior a altitud
  parecida).
- G06-CIE-U5-5.12 (microhabilidad): «glucosa + oxígeno → energía + CO₂ + agua» pone la energía como un producto más.

**Progresión y profundidad:**
- G08-CIE-U8-8.1 pide argumentar con el corrimiento al rojo, pero el efecto Doppler llega en 11.°.
- G11-FIS-U9-9.2 pide «recordar V = IR», que ningún grado anterior enseña de forma explícita.
- G06 6.2 y 6.3: etapas de la mitosis y de la meiosis en 6.°.
- G05-CIE-U2-2.5 (aceleración centrípeta) y G04-CIE-U4-4.7 (precesión y nutación): formalismo alto para el grado.

## Bucle externo: lo que aprendió el método
**Ya corregido en el código** (cada corrección salió de un agente que no pudo anclar algo legítimo):
- el verificador lee **todas** las celdas de la fila de la malla (microhabilidades e indicador avanzado);
- reconoce los ids `…-f<fila>`, el tramo del docx de Australia de cada código y el `.ttl` de Japón;
- un objetivo de país se ancla con su **original**, no con la paráfrasis en español del proyecto;
- `gskg bucle fuente` ya no recorta la fila (el recorte escondió el efecto invernadero);
- una asignación rechazada queda como observación del elemento, no de toda la división;
- la sonda ciega lista lo que no puede leer (dos sondas vieron de paso resultados del panel en los README).

**Corregido en la revisión crítica (2026-10-13):**
- **Sonda ciega:** se comparaba con la resolución *original*. En 3 casos la réplica corrigió el dictamen y llegó a
  lo mismo que la sonda (asignación de Japón, capas de la atmósfera y propuesta #11), y aun así se marcaban
  «la sonda discrepó». Ahora se compara con la resolución vigente: coincidir corrobora y discrepar es inestable.
- **Snapshots por grado:** las asignaciones de objetivos de otros países (SV 9–11) se contaban en 9.°, 10.° y 11.°
  sin ser temas de la malla. Ahora van una sola vez, en «Del tramo». También se leen los rangos «9.°–11.°» y se
  muestra la clase vigente de las decisiones.
- **Totales publicados:** se había escrito «466 sólidos o respaldados». Lo correcto es 485 de 486, que son 468
  sólidos y 17 respaldados.
- **El contraste no veía las revisiones de etiquetas:** leía el etiquetado de la malla sin las revisiones de
  `data/interim/revisiones/`. Por eso las correcciones del panel (y las humanas, cuando lleguen) no llegaban a las
  clases. Ahora las lee. Efectos:
  - epidemiología pasa a 9.°: la etiqueta se agregó a G09-CIE-U9-9.1 y 9.2 («inmunidad colectiva», «boletín
    epidemiológico del MINSAL»), como señalaron el revisor y el experto de Biología;
  - el primer grado del ciclo del carbono y de los electrones de valencia se corrige, sin que cambie su clase;
  - catalizadores quedaba incierto y se resolvió con la fila: G06-CIE-U5-5.2 «Reconoce las enzimas como proteínas
    que aceleran reacciones…». Sigue «sin referente».
- **Las 4 clases «no retomado» de 9.°–11.° eran falsas o parciales.** El método v1 de ese tramo no busca en la fila
  completa: el efecto invernadero (dos conceptos), las capas de la atmósfera (presión y altitud en Física 10.°; capa
  de ozono en Química 10.°–11.°) y los usos de la energía aparecen en 10.° y 11.°. Pasaron a «retomado» con su cita
  literal. El README de 9.°–11.° se corrigió: la atmósfera se retoma en parte, y la recomendación del equilibrio en 9.°
  ahora sigue el matiz del panel (reubicar los cálculos, no las amortiguadoras como fenómeno).

**Pendiente en el método del contraste (decisión del responsable):**
- **Singapur K326–K328** se cuenta como núcleo, pero el estudiante elige dos de tres ciencias (afecta a 9.°–11.°).
- ~~**Hong Kong S1–3:** los objetivos sacados del resumen de la unidad cuentan como núcleo~~ **Corregido el
  2026-10-13:** `corregir-metadatos` marca como ampliación lo que sigue a una frase opcional («Teachers may further
  guide…»). Era un solo objetivo (HK-FIS-hk_s1_3-p062-22, gases) y ninguna clase final cambió. Las actividades
  sugeridas no se extraen como objetivos.
- **Singapur K326–K328: verificado, pendiente de decisión.** En la p. 6 dice «two of Papers 2, 3 and 4»: cada
  estudiante cursa dos de las tres ciencias. Contarlo como especialización cambiaría la regla de qué es «núcleo», y
  por coherencia habría que aplicarlo también a Japón (3 de 4 asignaturas 基礎). Afectaría buena parte del contraste
  de 9.°–11.°. **Recomendación:** introducir un nivel «núcleo parcial» (lo cursa la mayoría, pero no todos) y
  contarlo como núcleo en la lectura amplia y como especialización en la estricta. Así el método de doble lectura
  decide.
- **Ontario Grades 1–2: catálogo listo, falta extraer.** Están en `config/internacional_2_8.yaml` (pp. 92–113,
  llevados a SV 2 como HK P1–P3). La extracción requiere **24 llamadas a Vertex**, más el etiquetado de los
  objetivos nuevos, y la aprobación del gasto. Mientras tanto, el contraste no cambia.
- **Etiquetado:** objetivos asignados a un concepto vecino (calidad del aire y composición del aire; transmisión de
  patógenos y epidemiología) y conceptos casi duplicados.
- **Comparar nivel con nivel:** el primer grado mezcla el nivel cualitativo con el formal (flotación, potencia,
  vectores); el panel lo aplica, pero conviene codificarlo.
- **Fechado de etapas:** KR y TW se fechan a mitad de su etapa; en casos de umbral la clase depende de esa convención.
