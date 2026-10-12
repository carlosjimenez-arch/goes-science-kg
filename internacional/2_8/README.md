# Contraste internacional de 2.°–8.° con la malla V2

> Spec 12 (`specs/12_grafos_internacionales_2_8.md`). Verificación experta del 2026-10-11 y del 2026-10-12. Este README
> lo escribe el equipo. Los demás archivos de la carpeta se generan con
> `uv run gskg internacional --tramo 2_8 construir`: `<asignatura>.md`, `Contraste_<asignatura>.xlsx`, `contraste.json`,
> `revision_humana.csv`, `revision_clases.csv` y `visor.html`.

## Qué hay aquí
- **9 países** (SG, JP, KR, ENG, AU, HK, TW, EE y ON). En 2.°–8.° se compara solo el **núcleo**: es lo que cursan
  todos los estudiantes.
- **3.615 objetivos etiquetados.**
  - SG, KR, HK, TW, EE y ON se extrajeron con Vertex AI: Gemini 3.1 Pro extrae y Gemini 2.5 Pro valida.
  - AU, ENG (KS1–KS3) y JP se importaron del grafo principal.
- **Consenso por concepto** (448 conceptos) en `data/grafo/internacional_2_8/`, y contraste con la V2 de 2.°–8.°.
- **Revisión humana:**
  - `revision_humana.csv`: objetivos de los países con extracción parcial o etiquetas de confianza baja.
  - `revision_clases.csv`: conceptos «inciertos» y hallazgos con alertas.
- **Correcciones expertas:** 19 clases en `data/interim/internacional_2_8/revisiones.json`. Cada una trae su evidencia
  y gana sobre la regla automática. Van a confirmación del MINED con `gskg revision exportar-decisiones`.

## Método v2: solo se afirma lo que resiste dos lecturas (2026-10-12)
La primera verificación (24 hallazgos) dio **46 % de falsos**. Casi todos venían de etiquetas sueltas, de la V2 o de
los países. Por eso la regla se aplica ahora dos veces y una clase solo se afirma si sale igual en las dos lecturas
(`contraste.py`, «doble lectura»):

| | Lectura amplia (favorable a la V2) | Lectura estricta (desfavorable) |
|---|---|---|
| V2 | cualquier etiqueta de los **dos** etiquetados (Vertex y el del grafo principal), con cualquier confianza, **o el texto de cualquier columna** de la fila | presencia sólida: principal en un tema, dos etiquetados que coinciden o secundaria en dos temas |
| Países | presencia sólida: principal en un objetivo o secundaria en dos | regla de presencia (principal, o secundaria de confianza alta o media) |

Si las lecturas no coinciden, el concepto queda **incierto**: no se afirma nada y va a revisión con las dos clases.

Reglas que se agregan a la doble lectura:
1. **Mínimo de 3 países** para fechar con la mediana; con menos, «sin referente».
2. **Relaciones «parte de»:** 7 relaciones (`data/interim/conceptos/partes.json`), aplicadas en los dos lados. Por
   ejemplo, la conservación de la energía mecánica cuenta como conservación de la energía. Es una decisión de
   vocabulario y va al MINED.
3. **Búsqueda de texto como frase en toda la fila de la V2:** evidencia, habilidad TIMSS, microhabilidades e indicador
   avanzado. El etiquetado solo lee contenido, subcontenido, procedimental e indicador, y ahí no estaban la fricción
   de 3.° ni la conservación de la masa de 7.°.
4. **Secuencias prudentes:** el concepto tiene que ser principal en un tema, y el prerrequisito no puede aparecer antes
   ni en el texto.
5. **Alerta de vecinos en los «tardíos»:** se avisa cuando los objetivos de los países que fechan el consenso también
   enseñan un concepto que la V2 da antes.
6. **Metadatos de los países corregidos sin Vertex** (`gskg internacional --tramo 2_8 corregir-metadatos`):
   - 76 objetivos de Estonia tenían el rango 2.°–6.° en lugar de su etapa;
   - 37 de Singapur («P5 Foundation», «P4-P6») tampoco tenían su grado;
   - 98 objetivos de HK S1–3 son de la «Extension Part», que el documento imprime en cursiva (p. 27), y pasan a
     especialización.

Las salidas de 9.°–11.° no cambian: el tramo usa el método v1 (`lectura_doble` está solo en 2_8).

## Verificación
| Ronda | Qué se verificó | Confirmados | Parciales | Falsos |
|---|---|---|---|---|
| 1 (2026-10-11), método v1 | 24 hallazgos de todas las clases | 7 | 6 | **11 (46 %)** |
| 2 (2026-10-12), método v2 sin la búsqueda de texto, **muestra nueva al azar** | 8 tardíos, 7 adelantados, 4 sin referente, 2 posteriores y 3 secuencias | 13 | 5 | **6 (25 %)** |

- **Puntuación del método v2 completo sobre los 42 conceptos verificados en las dos rondas:**
  - afirma 28 clases y acierta 24 (86 %), contando como acierto los parciales;
  - deja 14 conceptos como inciertos.
- **Ese 86 % no es fuera de muestra.** La búsqueda de texto se ajustó después de ver la ronda 2. La medición limpia es
  la de la ronda 2.
- **Errores que quedan en lo verificado:**
  - conservación de la energía y mecanismos de transferencia de calor: los dos etiquetados se equivocan igual;
  - indicadores ácido-base: «papel indicador» no nombra el concepto;
  - neutralización: la amplitud del concepto difiere entre países.

  Los cuatro están corregidos en `revisiones.json`.
- **Secuencias:** de las 5 verificadas, 3 siguen como candidatas y solo 1 es cierta. Las 51 secuencias automáticas son
  candidatos: al MINED solo se presenta la verificada.

## Hallazgos verificados (se presentan al MINED)
Formato de la evidencia: tema de la V2 con hoja y fila; país con documento y página (posición en el PDF).

### Llegan tarde
| Hallazgo | Evidencia | Lectura |
|---|---|---|
| **Agentes oxidantes y reductores, reducción y par redox** (V2 desde 10.°) | **V2:** la oxidación con oxígeno está en 7.° (G07-CIE-U1-1.1/1.2); la reducción y la serie de actividad, en G10-QUI-U13-13.3 (fila 108); el redox formal, en G11-QUI-U6. **Países:** TW Jc-Ⅳ-1 a 7 (p. 31, SV 6–8), ENG KS3 (p. 8–9: desplazamiento, serie de reactividad, obtener metales con carbono), EE (p. 27), JP 中2–3. | Introducir en 7.°–8.° la serie de reactividad y la reducción cualitativa. |
| **Suelo** (V2 en 5.°) | **V2:** G05-CIE-U6-6.14 a 6.19; antes solo «la planta necesita suelo» (G02-CIE-U4-4.3). **Países a la altura de 3.°:** ENG Year 3 (p. 17), HK P4 (4EA3, p. 40), AU Year 3, ON Grade 3 (p. 123–124), JP 小4 (p. 61), TW etapa II. | Adelantar a 3.° la formación, los componentes y los tipos de suelo (6 países). |
| **Formación de imágenes en espejos planos** (V2 en 10.°) | **V2:** reflexión en espejos en G04-CIE-U1-1.14; imágenes en G10-FIS-U16-16.10. **Países (SV 5–8):** HK P6 (p. 38), KR [9과10-02] (p. 55), SG Lower Sec (p. 37), TW Ka-Ⅳ-8/9, ENG KS3 (p. 12). | Introducir la imagen en espejo plano en la óptica de 6.°–8.°. |
| **Lentes e imágenes** (V2 en 10.°–11.°) | **V2:** antes de 10.° la lupa es solo un instrumento; en 7.° hay refracción sin lentes (G07-CIE-U6-6.21); las lentes explícitas están en G11-FIS-U17-17.2 a 17.10. **Países:** KR [9과10-02] (p. 55, cualitativo), TW INe-Ⅲ-8 (p. 23) y p. 32, EE (p. 19), JP 中1, ENG KS3 (p. 12, lente convexa). | Introducir lentes convergentes cualitativas (imagen, lupa, ojo) en 7.°–8.°. |
| **Reacciones exotérmicas y endotérmicas** (V2 en 10.°) | **V2:** G10-QUI-U9-9.3 (fila 79); en 6.° solo el cambio de temperatura como evidencia de reacción (G06-CIE-U4-4.9). **Países:** ENG KS3 (p. 8), JP 中2, KR [9과16-06] (p. 60), TW (p. 27), EE (p. 12). | Nombrar en 7.°–8.° la energía que se libera o se absorbe en las reacciones. |
| **Ley de Ohm como relación explícita** (parcial; V2 la nombra en 11.°) | **V2:** en 6.° se miden voltaje y corriente y se predice la corriente (G06-CIE-U3-3.1 a 3.5) sin nombrar la ley; la ley está en G11-FIS-U9-9.2 (fila 47). **Países (SV 7–8):** KR [9과14-02] (p. 58), TW (p. 32), JP 中2, ENG KS3 (p. 12, R = V/I). SG la deja opcional (p. 48). | Nombrar la relación V = I·R en 8.°–9.°, sobre lo que 6.° ya trabaja. |

### Van antes que los países
| Hallazgo | Evidencia | Lectura |
|---|---|---|
| **Números cuánticos en 5.°**, sin referente | **V2:** G05-CIE-U3-3.10 y 3.11 (filas 12–13), con su conjunto de números; se repiten con todo el formalismo en G10-QUI-U3-3.8. **Países:** ningún objetivo de 2.°–8.° trata números cuánticos, orbitales ni subniveles; EE (p. 26) pide diagramas por capas. | Formalismo de bachillerato en primaria: revisar la profundidad o moverlo a 10.°. |
| **Enlace iónico en 5.°–6.°**, sin referente | **V2:** G05-CIE-U4-4.6 (fila 8) y G06-CIE-U4-4.2 (fila 4). **Países:** solo EE (p. 26, SV 7–9) y ENG GCSE (p. 20, SV 8–9). No lo tienen AU 7–10, ON, SG Lower Sec, HK S1–3, KR 중 ni TW 國中. | 2 o 3 grados antes que los únicos dos países que lo enseñan. |
| **Iones en 5.°**, adelantados | **V2:** G05-CIE-U3-3.7 (fila 9), iones monoatómicos; G05-CIE-U4-4.4 (fila 6), energía de ionización y radio iónico. **Países (SV 6–8):** KR [9과11-04] (p. 56), TW Jb-Ⅳ-4 (p. 31), EE (p. 26). | Junto con los números cuánticos y el enlace iónico, la química de 5.° está 2 o 3 grados adelantada. |
| **Fuerzas intermoleculares en 6.°**, adelantadas | **V2:** G06-CIE-U4-4.7/4.8 (filas 9–10), con Van der Waals explícito. **Países:** solo ENG las nombra, en GCSE (SV 8–9). | Revisar la profundidad en 6.° (cualitativo: «las partículas se atraen»). |
| **Ciclo de vida de las estrellas**, sin referente (V2 en 5.° y 8.°) | **V2:** G05-CIE-U5-5.5/5.6 y G08-CIE-U8-8.3. **Países:** ninguno lo tiene en 2.°–8.°; KR lo da en 통합과학 (SV 9). | 5.° es temprano incluso frente al bachillerato de esos países: revisar la profundidad. |
| **Formación de la Tierra**, sin referente (V2 en 5.°) | **V2:** G05-CIE-U5-5.8 (fila 10). **Países:** ENG GCSE solo la atmósfera primitiva (p. 26, SV 8–9); TW, en bachillerato (p. 42 y 56). | Decisión propia: mantener el nivel descriptivo. |
| **Precursores y monitoreo de sismos y erupciones**, sin referente (V2 en 5.°) | **V2:** G05-CIE-U6-6.10 y 6.12 (filas 12 y 14). **Países:** en 2.°–8.° solo preparación y respuesta (KR p. 27, TW p. 24); AU, en elaboraciones opcionales de Year 8. | Contenido pertinente para El Salvador por el riesgo sísmico y volcánico. Es una decisión propia, no un desajuste. |
| **Eclipses en 4.°**, adelantados | **V2:** G04-CIE-U4-4.8 (fila 10) y 8.° (fila 6). **Países (SV 5–7):** HK P6 (6EC4, p. 43), AU Year 7, KR [9과07-04] (p. 52), TW (p. 29). | Ningún país lo enseña antes de 5.°. |
| **Enfermedades infecciosas y no infecciosas en 3.°**, adelantadas | **V2:** G03-CIE-U6-6.1 (fila 3); higiene y vacunas ya en 2.°. **Países:** HK P4 (p. 28) y KR (p. 24) en el mismo grado; ON (p. 139–140), SG y ENG, más tarde. | Adelantadas frente a la mediana, pero con dos países al mismo nivel: es coherente. |
| **Límites de placas en 5.°**, adelantados | **V2:** G05-CIE-U6-6.7 (fila 9). **Países (hacia 7.°):** AU Year 8, TW Ia-Ⅳ-2/3, KR [9과09-05] (p. 54), EE (p. 22). | Es la mediana de 4 países. Si el indicador se mantiene cualitativo y local, es coherente. |
| **Fósiles en 3.°** y **adaptaciones estructurales en 2.°**: en el umbral | **Fósiles:** V2 G03-CIE-U2-2.16 (fila 18); ENG y ON los dan en 2.°–3.°. **Adaptaciones:** V2 G02-CIE-U4-4.8 (fila 14); ON, KR y TW en SV 2–3. | La V2 está en el extremo temprano, no por delante. **El hueco real:** las adaptaciones no se retoman entre 3.° y 10.° (solo G08-CIE-U6-6.3, celular), mientras 6 de 8 países las tratan en SV 3–6. |

### Secuencia
| Hallazgo | Evidencia | Lectura |
|---|---|---|
| **Tipos de rocas (3.°) antes que minerales (8.°)** | **V2:** G03-CIE-U2-2.7 (fila 9) clasifica rocas ígneas, sedimentarias y metamórficas; los minerales aparecen por primera vez en G08-CIE-U5-5.1/5.2. **Países:** ON Grade 4 enseña rocas y minerales juntos (p. 134–135, SV 3); TW, «las rocas están compuestas de minerales» (p. 21). | Introducir los minerales como componentes de las rocas en 3.°–4.°. |
| **Argumentar el Big Bang en 8.° sin el corrimiento al rojo** | G08-CIE-U8-8.1 pide la expansión como evidencia; el efecto Doppler llega en G11-FIS-U4-4.5. KR enseña la expansión con modelos y excluye el corrimiento al rojo (p. 59). | Introducir un corrimiento al rojo cualitativo o acotar las evidencias que se piden en 8.°. |

### Sin desajuste (se informan como nota)
- **Solo después de 8.°, igual que en los países:**
  - celdas galvánicas (V2 en 11.°);
  - corrientes oceánicas (9.°);
  - termorregulación (9.°);
  - ingeniería genética (9.°, como EE y ENG);
  - radiación ionizante (11.°).
- **Dentro de la tolerancia de ± 1,5 grados:**
  - motor eléctrico y sistema endocrino (V2 en 9.°);
  - neutralización ácido-base (9.° frente a 8.° en sentido estricto);
  - fricción (3.°);
  - conservación de la masa (7.°);
  - indicadores ácido-base (7.°).

## Candidatos automáticos que resultaron falsos
| Candidato automático | Realidad | Causa | ¿El método v2 lo evita? |
|---|---|---|---|
| Ley de Coulomb tardía | ningún núcleo pide la ley cuantitativa; la electrostática cualitativa está en 5.° | etiqueta específica sobre objetivos cualitativos | sí (incierto) |
| Conducción, convección y radiación adelantadas | por contenido empiezan en 4.° | los dos etiquetados ven los tres mecanismos en G02 2.6 | no (corregido a mano) |
| Leyes de Kepler sin referente | G04 4.1 es geo/heliocentrismo; Kepler en 11.° | etiqueta secundaria suelta | sí (incierto) |
| Espejos planos «posterior» | era tardío (formación de imágenes) | solo 4 países en los datos | no (corregido a mano) |
| Sustancias puras tardías | elementos y compuestos desde 5.° | secundaria de confianza baja | sí (incierto) |
| Química de lípidos sin referente | biomoléculas en general en 6.° | etiqueta secundaria suelta | sí (incierto) |
| Factores bióticos tardíos | necesidades y hábitat en 2.° | etiquetado asimétrico | sí (incierto) |
| Campo magnético terrestre tardío | imanes en 3.°, campo terrestre en 5.° | el concepto amplio en los países, el fino en la V2 | sí (incierto) |
| Conservación de la energía tardía | en 5.° y 8.° como «energía mecánica» | concepto vecino | pasa a «adelantado» (corregido a mano a alineado) |
| Nicho ecológico adelantado | un solo país | mediana sin mínimo de países | sí (sin referente) |
| Eutrofización sin referente | la V2 la nombra en 10.° | etiqueta que va más allá del texto | sí (incierto) |
| Fricción tardía (ronda 2) | fricción en 3.° | estaba en la habilidad TIMSS, que no se etiqueta | sí (búsqueda de texto) |
| Conservación de la masa tardía (ronda 2) | la ley en 7.° con Lavoisier | estaba en la evidencia de aprendizaje | sí (búsqueda de texto) |
| Indicadores ácido-base tardíos (ronda 2) | papel indicador en 7.° | «papel indicador» no nombra el concepto | no (corregido a mano) |
| Neutralización tardía (ronda 2) | 1 grado en sentido estricto | amplitud distinta y notas de los países que la excluyen | no (corregido a mano) |
| Masa y peso antes que gravedad; tejidos antes que diferenciación (secuencias, ronda 2) | medir masa no exige la gravedad; los tejidos histológicos van con la diferenciación en 6.° | etiquetas de un solo lado | no: siguen como candidatos sin presentar |

## Límites y pendientes
- **150 conceptos inciertos (31 %)** esperan revisión en `revision_clases.csv`. Son el costo de afirmar solo lo que
  resiste las dos lecturas.
- **Notas de los países que excluyen contenido** (KR p. 39: «no se trata la neutralización»; SG p. 48: opcional) y
  notas de alcance de JP (触れること) que no se importaron.
- **Metadatos de 9.°–11.°:** 66 objetivos de electivas de AU Senior Secondary («Unit 1 & 2») caen en el rango del
  documento. No se corrigió para no mover salidas ya verificadas; afecta solo a la especialización.
- **Ids inventados:** 52 ids de concepto inventados por el modelo quedaron como «propuestos» y no entran al grafo
  (31 son de AU). Un objetivo de JP quedó sin etiquetar.
- **Rangos de grados:** KR, TW y ENG KS1–2 dan rangos; el grado de cada objetivo es el punto medio.
- **Duplicados de SG:** SG separa Standard y Foundation, lo que puede duplicar objetivos. El consenso cuenta presencia
  por país, no conteos.
- **Etiquetas de IA:** las clases dependen de ellas y de la equivalencia de grados por edad de ingreso.
- **No hace falta re-etiquetar la V2 con Vertex por ahora.** El segundo etiquetado (el del grafo principal) y la
  búsqueda de texto cubren lo que la verificación encontró.
