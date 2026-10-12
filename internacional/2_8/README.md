# Contraste internacional de 2.°–8.° con la malla V2

> Spec 12 (`specs/12_grafos_internacionales_2_8.md`). Verificación experta del 2026-10-11. Este README lo escribe el
> equipo; `<asignatura>.md`, `Contraste_<asignatura>.xlsx`, `contraste.json`, `revision_humana.csv` y `visor.html` se
> generan con `uv run gskg internacional --tramo 2_8 construir`.

## Qué hay aquí
- **9 países** (SG, JP, KR, ENG, AU, HK, TW, EE y ON), solo el **núcleo** (en 2.°–8.° todo es obligatorio).
  **3.615 objetivos** etiquetados: SG, KR, HK, TW, EE y ON se extrajeron con Vertex AI (Gemini 3.1 Pro extrae y
  Gemini 2.5 Pro valida); AU, ENG (KS1–KS3) y JP se importaron del grafo principal.
- Consenso por concepto (448 conceptos) en `data/grafo/internacional_2_8/` y contraste con la V2 de 2.°–8.°.
- Revisión humana: `revision_humana.csv` (568 objetivos parciales o con etiquetas de confianza baja).
- Correcciones expertas: `data/interim/internacional_2_8/revisiones.json` (11 clases, con evidencia; ganan sobre la
  regla y van a confirmación del MINED con `gskg revision exportar-decisiones`).

## Advertencia principal: las clases automáticas de 2.°–8.° son candidatas, no hallazgos
Se verificaron **24 hallazgos** (todas las clases y asignaturas) contra la fila de la V2 y la página del documento de
cada país: **7 confirmados, 6 parciales y 11 falsos (46 %)**. En ningún caso el país dice algo distinto de lo que
afirma su objetivo: los errores vienen del **etiquetado de la V2**, más irregular en primaria que en 9.°–11.°. Hasta
mejorar el método (abajo), al MINED solo se presentan los **hallazgos verificados** de esta página; las tablas de
`<asignatura>.md` son candidatos.

## Hallazgos verificados (se presentan al MINED)
Formato de la evidencia: tema de la V2 con hoja y fila; país con documento y página (posición en el PDF).

| Hallazgo | Evidencia | Lectura |
|---|---|---|
| **Agentes oxidantes y reductores llegan tarde** (V2 desde 10.°) | V2: nada de reducción ni serie de actividad antes de G10-QUI-U13-13.3 (fila 108); redox formal en G11-QUI-U6. Países: TW Jc-Ⅳ-1 a 7 (p. 31, SV 6–8), ENG KS3 (p. 8–9: oxidación, desplazamiento, serie de reactividad), EE (p. 27), HK S1–3 (p. 80), JP 中3 | Introducir en 7.°–8.° la serie de reactividad y la oxidación-reducción cualitativas. |
| **Suelo llega tarde** (V2 en 5.°) | V2: G05-CIE-U6-6.14 a 6.19; antes solo «la planta necesita suelo» (G02-CIE-U4-4.3). Países a la altura de 3.°: ENG Year 3 (p. 17), HK P4 (4EA3, p. 40), AU Year 3, ON Grade 3 (p. 123–124), JP 小4 (p. 61), TW etapa II | Adelantar formación, componentes y tipos de suelo a 3.° (6 países). |
| **Formación de imágenes en espejos planos llega tarde** (V2 en 10.°) | V2: reflexión en espejos en G04-CIE-U1-1.14, imágenes en G10-FIS-U16-16.10. Países (SV 5–8): HK P6 (p. 38), KR [9과10-02] (p. 55), SG Lower Sec (p. 37), TW Ka-Ⅳ-8/9, ENG KS3 (p. 12) | Introducir la imagen en espejo plano en la óptica de 6.°–8.°. |
| **Fuerzas intermoleculares, adelantadas** (V2 en 6.°) | V2: G06-CIE-U4-4.7/4.8 (filas 9–10), Van der Waals explícito. Solo ENG las nombra, en GCSE (SV 8–9) | Revisar la profundidad en 6.° (cualitativo: «las partículas se atraen»). |
| **Límites de placas, adelantados** (V2 en 5.°) | V2: G05-CIE-U6-6.7 (fila 9). AU Year 8, TW Ia-Ⅳ-2/3, KR [9과09-05] (p. 54), EE (p. 22): hacia 7.° | Es una mediana de 4 países, no un consenso; el indicador de 5.° es cualitativo y local. Coherente si se mantiene así. |
| **Ciclo de vida de las estrellas, sin referente** (V2 en 5.° y 8.°) | V2: G05-CIE-U5-5.5/5.6, G08-CIE-U8-8.3. Ningún país lo tiene en 2.°–8.°; KR lo da en 통합과학 (SV 9) | 5.° es temprano incluso frente al bachillerato de esos países: revisar profundidad. |
| **Celdas galvánicas, corrientes oceánicas y termorregulación: posteriores** | V2: celdas en 11.°, corrientes en 9.° (G09-CIE-U4-4.5–4.7), termorregulación en 9.° (G09-CIE-U9-9.3). Solo 2–3 países las tienen antes (TW, JP 中3; TW, KR, EE; EE, TW) | Sin exigencia internacional antes de 9.°: no es una brecha. |
| **Casos límite (1 grado): motor eléctrico y sistema endocrino** | V2 en 9.° (G09-CIE-U7-7.5–7.7; G09-CIE-U9-9.3). JP, KR, TW y ENG KS3 enseñan el motor hacia 7.°; KR, TW y AU el sistema endocrino hacia 8.° | Dentro de la tolerancia de la regla (± 1,5): alineados. Se informan como nota. |
| **Secuencia: argumentar el Big Bang en 8.° sin el corrimiento al rojo** | G08-CIE-U8-8.1 pide la expansión como evidencia; el efecto Doppler llega en G11-FIS-U4-4.5. KR enseña la expansión con modelos y excluye el corrimiento al rojo (p. 59) | Introducir un corrimiento al rojo cualitativo o acotar las evidencias que se piden en 8.°. |

## Candidatos automáticos corregidos o descartados (11 falsos y 2 parciales)
| Candidato automático | Realidad | Causa |
|---|---|---|
| Ley de Coulomb tardía | ningún núcleo pide la ley cuantitativa; la electrostática cualitativa está en 5.° | etiqueta específica apilada sobre objetivos cualitativos |
| Conducción, convección y radiación adelantadas | por contenido empieza en 4.° (como la mediana) | etiqueta secundaria suelta en G02 2.6 |
| Leyes de Kepler sin referente | G04 4.1 es geo/heliocentrismo; Kepler en 11.° | etiqueta secundaria suelta |
| Espejos planos «posterior» | era tardío (formación de imágenes) | la IA no captó «espejos» en G04 1.14 |
| Sustancias puras tardías | elementos y compuestos desde 5.° | secundaria de confianza baja descartada por la regla de presencia |
| Química de lípidos sin referente | biomoléculas en general en 6.°; lípidos en 10.°–11.° | etiqueta secundaria suelta |
| Factores bióticos tardíos | necesidades y hábitat en 2.° | etiquetado asimétrico V2/países |
| Campo magnético terrestre tardío | imanes en 3.°, campo terrestre en 5.° | equivalencia aplicada en un solo lado |
| Conservación de la energía tardía | en 5.° y 8.° como «energía mecánica» | concepto vecino sin relación «parte de» |
| Nicho ecológico adelantado | un solo país, etiqueta secundaria | mediana sin mínimo de países |
| Eutrofización sin referente | la V2 la nombra en 10.° | etiqueta que va más allá del texto |
| Dos secuencias (fósiles/erosión; fuentes de energía/renovables) | la V2 sí trae la base antes, o la etiqueta es demasiado amplia | etiquetas laxas; profundidad del tema |

## Cambios de método en esta etapa
1. **«Tardío» después del tramo exige ≥ 2 grados** (`contraste.clase_de`), como dicen la spec y el docstring; el
   código marcaba tardío con 1 grado (Coulomb, motor, sistema endocrino). No cambia 9.°–11.° (verificado: salidas
   idénticas).
2. **11 correcciones expertas** en `revisiones.json` del tramo, con evidencia y pendientes del MINED.

## Mejoras de método pendientes (antes de usar las tablas automáticas)
1. **Presencia sólida también en la V2:** principal en un tema, o secundario en dos (como ya se exige a los países en
   9.°–11.°). Corrige las etiquetas secundarias sueltas.
2. **Mínimo de 3 países** para calcular la mediana de «adelantado»; con menos, «sin referente».
3. **Relación «parte de»** entre conceptos vecinos (p. ej. conservación de la energía mecánica ⊂ conservación de la
   energía), o etiquetar ambos: es una decisión de vocabulario.
4. **Aplicar las equivalencias en los dos lados** con la misma regla.
5. **Búsqueda de texto en la V2** antes de publicar un «tardío» o una secuencia, y alerta cuando un tardío comparte
   sus objetivos de país con un concepto vecino «alineado» o «adelantado».
6. Re-etiquetar la V2 de 2.°–8.° con un vocabulario de primaria más fino (tiene costo en Vertex: requiere aprobación).

## Límites declarados
- 52 ids de concepto inventados por el modelo quedaron como «propuestos» y no entran al grafo (31 en AU); 1 objetivo
  de JP sin etiquetar.
- EE, KR, TW y ENG KS1–2 dan rangos de grados: el grado de cada objetivo es el punto medio.
- SG separa Standard y Foundation (puede duplicar objetivos); el consenso cuenta presencia por país, no conteos.
- Las clases dependen de etiquetas de IA y de la equivalencia de grados por edad de ingreso.

## Validación (2026-10-11)
24 hallazgos, en dos lotes verificados por el subagente `verificador-hallazgos` contra las fuentes: confirmados 7
(agentes oxidantes, fuerzas intermoleculares, celdas galvánicas, suelo, límites de placas, ciclo estelar, corrientes
oceánicas); parciales 6 (motor, sistema endocrino, nicho, eutrofización, termorregulación, Big Bang/Doppler); falsos 11
(los de la tabla anterior).
