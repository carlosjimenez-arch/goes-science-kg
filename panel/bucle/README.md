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

## Serie inc9: las clases inciertas de 9.°–11.° (2026-10-13)
Al pasar 9.°–11.° a la doble lectura quedaron 57 clases inciertas. El panel decidió 55 y 2 se resolvieron por
delegación. Las 55 pasaron por el bucle en una serie aparte (lotes `b1-inc9`, `r11-inc9`, `b2-inc9`):
| Etapa | Resultado |
|---|---|
| Vuelta 1: impugnación | 46 se sostienen, 2 debilitados y 7 refutados; 9 reabiertos |
| Vuelta 1: réplica | 8 cambiados y 1 mantenido (diagramas de fases: EE se suma al núcleo, pero son 2 países) |
| Vuelta 2 | los 8 cambios se sostienen: el bucle se detiene |
| Solidez | de las 55: 54 sólidas y 1 respaldada; además, 2 delegadas |

**Lo que cambió:**
- a «solo especialización» (la V2 hace obligatorio lo que fuera es electivo): ciclo del nitrógeno (9.°), química verde
  (Química 11.°), técnicas de estructura orgánica (cristalografía en Física 11.°), potencial eléctrico en un punto del
  campo (Física 11.°) y astronomía multionda (Física 11.°);
- a «sin referente»: oleaje y dinámica costera (la palabra «oleaje» de 4.° está en la lista de efectos de un ciclón;
  9.° lo presenta como fenómeno nuevo) y cuantización de Planck (solo EE y TW en el núcleo);
- a «alineado»: reflexión interna total (núcleo de HK S1–3, JP 中1 y ON SNC2D; no es especialización).

**Por qué se equivocó el panel:** casi siempre por una de dos razones, que ahora están como reglas en
`prompts/panel_dictaminar.md` («Clases inciertas del contraste»):
- contó como núcleo objetivos de un concepto vecino (desarrollo sostenible, ciclado de la materia, diferencia de
  potencial de un circuito);
- usó la regla del umbral para no afirmar «sin referente» o «solo especialización» cuando la evidencia era clara.

**Antecedente de 2.°–8.° (bucle externo).** El refutador de Física vio que la reflexión interna total, núcleo de HK
S1–3, no contaba porque la secundaria baja de HK no estaba cargada en 9.°–11.°. Desde ahora el antecedente suma el
núcleo de 2.°–8.° de HK, SG, EE, KR, TW y ON (`consenso.ANTECEDENTE_2_8`), ya extraído y etiquetado, sin Vertex:
- 8 clases automáticas cambiaron. Por ejemplo, indicadores ácido-base y genómica dejan de ser «solo especialización»
  (HK S1–3, KR, SG y TW los tienen en el núcleo);
- 4 quedaron inciertas y el panel las decidió (serie inc9b):
  - rapidez de la luz → alineado: el valor de HK está en la Extension Part y el de SG es opcional, así que quedan 3
    países;
  - estructura y propiedades de polímeros → solo especialización;
  - capacidad de carga → solo especialización;
  - nutrición mineral de las plantas → alineado.
- El antecedente trae también el ruido de las etiquetas de esos países: hay etiquetas principales de conceptos
  vecinos, como la propagación de la luz por su rapidez en HK. La doble lectura lo convierte en clases inciertas, no
  en hallazgos falsos.

**Recomendaciones del panel en esta serie (no son clases ni quitan temas):**
- ciclo del nitrógeno: en 9.°, de forma cualitativa; la fijación, la nitrificación y la desnitrificación, en Biología
  10.°;
- rapidez de la luz: ENG, TW y ON dan el dato entre 6.° y 9.°, y la V2 lo hace explícito en 11.°. Se puede adelantar:
  el cambio de rapidez como causa de la refracción en 7.°, el relámpago y el trueno en 8.° y n = c/v en el indicador
  de 10.°;
- polímeros: la relación estructura-propiedad, de forma cualitativa (cadenas lineales y entrecruzadas); la
  tacticidad, como ampliación;
- capacidad de carga: apoyarla en la curva de levaduras de 7.° (G07-CIE-U4-4.4) y limitar el ajuste del modelo a la
  lectura de la meseta;
- nutrición mineral: nombrar en 8.° (G08-CIE-U6-6.4) que la raíz absorbe sales minerales, como tres referentes antes
  de 9.°; en 11.°, separar «nutriente mineral» de «alimento de la planta»;
- diagrama de fases: está dos veces en 10.° (Física 12.9 y Química 7.5); coordinar las dos asignaturas.

**Etiquetas de objetivos de países que el bucle encontró mal** (no cambian ninguna clase, porque esos conceptos
tienen revisión del panel; corregirlas en el próximo etiquetado):
- KR-TYE-kr_primaria_34-p023-02: lleva oleaje como concepto principal, pero la p. 23 excluye la erosión, el transporte
  y la sedimentación por el agua de mar;
- EE-FIS-ee_gym-p012-25: trata el diagrama de fases y no lleva ese concepto;
- EE-FIS-ee_gym-p012-23: la ecuación de Einstein y E = hf quedaron solo en «fotón y efecto fotoeléctrico»;
- HK-FIS-hk_s1_3-p074-07: lleva como principal la rapidez de la luz, pero solo dice que la luz se propaga en el vacío;
- SG Lower Secondary p. 50 («xylem transports water and mineral salts»): sin la etiqueta de nutrición mineral;
- EE-BIO-ee_gym-p008-17: lleva como principal la capacidad de carga, pero trata la autorregulación del ecosistema;
- Japón: los 内容の取扱い del Course of Study de secundaria baja (p. ej., 全反射も扱い) no están en
  `data/interim/paises/japon.json`.

## Errores y problemas de la propia malla (para el MINED)
**Errores científicos:**
- G05-CIE-U6-6.7: bordes de placa «pasivos»; lo correcto es «transformantes».
- G10-FIS-U16-16.1: atribuye la reflexión y la refracción al comportamiento corpuscular de la luz; el modelo
  ondulatorio las explica.
- G06-CIE-U2-2.6: explica que las noches de la costa son menos frescas que las de la montaña por la capacidad
  calorífica del agua; confunde el efecto de la altitud con el del agua (comparar costa e interior a altitud
  parecida).
- G06-CIE-U5-5.12 (microhabilidad): «glucosa + oxígeno → energía + CO₂ + agua» pone la energía como un producto más.
- G10-FIS-U16-16.6 (evidencia E1): pide explicar la fibra óptica «a partir de la dispersión y la descomposición de la
  luz». La fibra óptica funciona por reflexión interna total; el espectroscopio sí se explica por la dispersión.
  (Serie inc9, refutador de Física.)
- G03-CIE-U5-5.3: llama taxismo a la respuesta de las cochinillas a la humedad, que es una cinesis. En lo seco se mueven
  más y giran más, y en lo húmedo se detienen; no se orientan hacia el estímulo. Una variante que sí muestra un taxismo
  es la respuesta a una luz lateral (fototaxismo negativo). En 3.° basta con hablar de «respuesta a la humedad».

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
- ~~**Singapur K326–K328: pendiente de decisión**~~ **Resuelto el 2026-10-13 (decisión del responsable: núcleo
  parcial).** SG Combined, JP 基礎 y SG H1 cuentan como núcleo en la presencia laxa de los países y como
  especialización en la sólida. 9.°–11.° pasó a la doble lectura; el panel revisó los 57 inciertos que resultaron.
  Al hacerlo se encontró y corrigió un bug: el núcleo sólido no contaba la secundaria baja de ENG, AU y JP.
- ~~**Frases que dan falsos positivos en la búsqueda de texto**~~ **Corregido el 2026-10-13**
  (`contraste.AJUSTES_BUSQUEDA`, solo para la búsqueda del contraste; el vocabulario no cambia). Efectos:
  - en 9.°–11.°, la clase automática de 7 conceptos pasó a coincidir con la que decidió el panel a mano;
  - en 2.°–8.°, 5 conceptos que solo entraban por coincidencias falsas salen del contraste;
  - virus quedó incierto y se resolvió como «posterior» por decisión delegada.

  Las frases eran:
  - «reacción en cadena» encuentra la PCR;
  - «ángulo crítico» encuentra el pensamiento crítico;
  - «interacciones fundamentales» encuentra el material genético;
  - «energía potencial» encuentra la energía mecánica (para el potencial eléctrico);
  - «constante de tiempo» encuentra el movimiento circular;
  - «cuantificación de energía» encuentra los impactos ambientales;
  - «sedimentación» encuentra el ciclo de las rocas (para los ciclos sedimentarios);
  - «fases» encuentra las fases de la Luna (para los diagramas de fases);
  - falta el sinónimo «virus» para el concepto virus.
- **Criterio para todo el panel** (propuesto por Tierra y Espacio): una etiqueta secundaria de la IA sin texto en la
  fila no cuenta como «mención lateral» en la regla del umbral; una palabra del contenido oficial sí cuenta.
- **Singapur K326–K328 (nota original):** En la p. 6 dice «two of Papers 2, 3 and 4»: cada
  estudiante cursa dos de las tres ciencias. Contarlo como especialización cambiaría la regla de qué es «núcleo», y
  por coherencia habría que aplicarlo también a Japón (3 de 4 asignaturas 基礎). Afectaría buena parte del contraste
  de 9.°–11.°. **Recomendación:** introducir un nivel «núcleo parcial» (lo cursa la mayoría, pero no todos) y
  contarlo como núcleo en la lectura amplia y como especialización en la estricta. Así el método de doble lectura
  decide.
- ~~**Ontario Grades 1–2** no se extrajeron~~ **Resuelto el 2026-10-13.** Se extrajeron con Vertex (gasto aprobado:
  29 llamadas de extracción y 19 de etiquetado) 85 objetivos (pp. 92–113, llevados a SV 2 como HK P1–P3).
  Cambiaron 4 clases:
  - el ciclo del agua pasa de «adelantado» a «alineado», porque Ontario lo enseña en Grade 2;
  - grupos de vertebrados, energía cinética y tono y volumen del sonido quedaron inciertos y se resolvieron como
    «alineado» por decisión delegada (la V2 coincide con la mediana).

  **Bug encontrado:** la extracción reescribía los objetivos desde la caché y borraba las correcciones de
  metadatos (Extension Part de HK). Ahora `extraer` vuelve a correr `corregir-metadatos` al terminar.
- **Etiquetado:** objetivos asignados a un concepto vecino (calidad del aire y composición del aire; transmisión de
  patógenos y epidemiología) y conceptos casi duplicados.
- **Comparar nivel con nivel:** el primer grado mezcla el nivel cualitativo con el formal (flotación, potencia,
  vectores); el panel lo aplica, pero conviene codificarlo.
- **Fechado de etapas:** KR y TW se fechan a mitad de su etapa; en casos de umbral la clase depende de esa convención.
