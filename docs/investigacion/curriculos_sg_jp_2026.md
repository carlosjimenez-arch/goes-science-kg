# Ciencias en Singapur y Japón: verificación documental al 21 de octubre de 2026

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Consulta y corrección documental: **2026-10-21**. Esta auditoría identifica documentos oficiales y su población; no acredita equivalencias con El Salvador ni explica causalmente resultados internacionales. El paquete adjunto, `curriculos_sg_jp_2026_fuentes.json`, contiene diez PDF con bytes verificados, SHA-256, tamaño y número de páginas, y candidatos pendientes claramente separados. Incluye la edición singapurense de **enero de 2026** localizada después de la primera entrega. La ingesta y su estado se administran en el registro compartido por la tarea principal; esta auditoría no lo modifica ni activa alineaciones.

Las descargas y los renderizados se conservan exclusivamente en `/tmp/curriculos_sg_jp_2026/`. Las páginas indicadas son **PDF, empezando en 1**; el folio impreso puede diferir. Se verificaron portadas mediante renderizado, contenido mediante extracción local y versiones mediante índices oficiales. La vigencia se expresa como versión que el organismo publica para la población identificada, no como una conclusión obtenida de la fecha del nombre del archivo.

## Singapur: documentos recuperados y población

| Documento oficial | Identidad de portada | Alcance comprobado | Evidencia de aplicación y límites |
|---|---|---|---|
| [Science Teaching & Learning Syllabus: Primary Three to Six, Standard / Foundation — enero de 2026](https://www.moe.gov.sg/media/files/primary/syllabus/ba3562d3-5b31-4459-8693-45cde7b97273.pdf) | ©2022 CPDD; actualización enero de 2026; 87 páginas | P3–P6; mantiene aplicación desde cohorte P3 de 2023 | **Versión más reciente comprobada en este paquete.** Portada PDF1 revisada visualmente. Cotejo con original local y descarga oficial fresca de la tarea principal: SHA `0556023ceb55fe80de75ae044011b8c77ea7ea494a1873d2b224a9b2b8083ab0`, 1.006.566 bytes. Enero de 2026 es revisión, no nueva cohorte inicial. |
| [Mismo título — octubre de 2022](https://www.moe.gov.sg/media/files/primary/syllabus/2023-primary-science.ashx) | ©2022 CPDD; actualización octubre de 2022; 87 páginas | Misma familia y cohorte inicial | Copia anterior identificada con SHA `a1b6175dbafa7277c4ecc9ef703f60c6294bf76d278d20929381ff4f93211a03`. La [página Northland de 2026](https://www.northlandpri.moe.edu.sg/departments/science/) ayuda a identificar la cohorte, pero su enlace anterior no garantiza recuperar la revisión más reciente. Se conserva para contraste histórico. |
| [Science Teaching and Learning Syllabus: Lower Secondary, General 1 Course](https://www.moe.gov.sg/media/files/secondary/syllabuses/science/G1%20Lower%20Secondary%20Science%20Teaching%20and%20Learning%20Syllabus.pdf) | ©2024 CPDD; desde cohorte Secondary One 2021; 55 páginas | Secundaria inferior G1 | Enlazado por [Peicai Secondary, página actualizada el 25-08-2026](https://www.peicaisec.moe.edu.sg/academic/science/). Parte del interior conserva nomenclatura Normal (Technical); no es otro grado ni una población salvadoreña. |
| [Science Syllabus: Lower Secondary, General 2 Course / General 3 Course](https://www.moe.gov.sg/media/files/secondary/syllabuses/science/G2-3%20Lower%20Secondary%20Science%20Teaching%20and%20Learning%20Syllabus.pdf) | ©2024 CPDD; desde cohorte Secondary One 2021; 57 páginas | Secundaria inferior G2/G3, en un mismo documento | Mismo índice escolar oficial. Documento compartido no significa que G2 y G3 sean edades o que toda actividad tenga idéntica exigencia. |

En la edición de enero de 2026, **PDF21, folio20**, distribuye temas por P3–P6 y utiliza **subrayado** para excluir ciertos temas de Foundation; en octubre de 2022, era PDF22, folio21. Se inspeccionaron visualmente ambas tablas. Esa marca no se conserva en texto plano: el hecho de extraer palabras no certifica la restricción de modalidad ni su cobertura. PDF44 y47 distinguen resultados de reproducción en P5 Standard y Foundation. El preámbulo, PDF2, permite juicio profesional docente.

### Cambios semánticos de octubre de 2022 a enero de 2026

La comparación completa de texto por página detectó 37 páginas con diferencias después de normalizar secuencias de espacios; muchas son desplazamientos de paginación o palabras partidas. No se interpretan como 37 cambios curriculares. Las siguientes diferencias materiales se cotejaron con renderizados de enero de 2026:

| Cambio comprobado | Enero de 2026: PDF / folio | Consecuencia para el producto |
|---|---|---|
| Actualiza el marco transversal con competencias digitales y tecnológicas; explicita alfabetización en IA y relaciona prácticas de ciencias con competencias de datos y comunicación digital. | PDF9–10 / folios8–9; frente al apartado anterior de octubre PDF9–11 | Registrar como orientación transversal de esta revisión; no inferir que toda tarea exige dispositivos o uso de IA por escolares. |
| Revisa e-Pedagogy: tecnología complementaria a experiencias prácticas, andamiaje EdTech y uso de tecnologías emergentes manteniendo propósito, motivación y autorregulación del alumno. | PDF31–32 / folios30–31; frente a octubre PDF32 | Conservar el criterio pedagógico y verificar recursos antes de adaptar. Una mención de IA no demuestra eficacia ni disponibilidad salvadoreña. |
| Añade sección4.2: evaluación escolar alineada con resultados y ponderación **recomendada** de 70–85% pruebas escritas y 15–30% desempeño, tanto Standard como Foundation. | PDF36 / folio35, tabla3; octubre PDF36 carece de esta sección y tabla | Es recomendación de evaluación escolar de esta población; no es formato PSLE ni una ponderación que deba imponerse a El Salvador. |

En PDF38–82, el texto de los resultados coincide entre versiones **al eliminar todos los espacios**. Esto no acredita igualdad tipográfica, subrayados, diagramas o equivalencia de modalidades. La tabla de temas se desplazó una página; no deben reutilizarse localizadores de octubre bajo el SHA de enero. No se produjo un inventario exhaustivo de cada cambio gráfico.

G1 organiza contextos cotidianos, medición y seguridad (PDF12–14,23); G2/G3 articula temas, modelos y resultados en tres columnas (PDF14–17). Ambos incorporan indagación, pedagogía y evaluación; su presencia documental no prueba la eficacia de una implementación. G2/G3 ofrece criterios de evidencia y retroalimentación en PDF27–28; G1, PDF50–51. El producto puede separar ideas científicas, prácticas y valores como campos, conservando la modalidad de origen.

El [Education Statistics Digest 2025 de MOE](https://www.moe.gov.sg/-/media/files/about-us/esd-2025.pdf), folio vii, confirma Full Subject-Based Banding desde la cohorte Secondary 1 de 2024: G1/G2/G3 son niveles por asignatura y permiten ajustes durante la escolaridad. [SEAB](https://www.seab.gov.sg/secondary-education-certificate-sec/) confirma que el SEC comienza en **2027**, sustituyendo N(T), N(A) y O-Level. Por tanto, en el corte 2026 coexisten cohortes y nombres; no corresponde sustituir retrospectivamente todas las modalidades por G3.

La [ley oficial de educación obligatoria](https://sso.agc.gov.sg/Act/CEA2000?WholeDoc=1), artículos 2–3, distingue la obligación de primaria para ciudadanos residentes y sus excepciones. Su franja legal de edad no equivale a la edad típica de cada grado ni hace obligatoria cada ciencia de secundaria superior. No se verificó una tabla oficial actual de edades por P3–P6/Sec1–4 en este relevamiento; el JSON deja esas edades en `null` para impedir conversiones automáticas.

## Singapur: secundaria superior, exámenes y brechas reales

El [índice oficial SEAB de candidatos escolares 2026](https://www.seab.gov.sg/gce-o-level/o-level-syllabuses-examined-for-school-candidates-2026/) enlaza estos **programas de examen**, con portada O-Level (2026) y ©MOE/Cambridge 2024:

| Programa | PDF oficial y páginas verificadas por el lector web | Uso delimitado |
|---|---|---|
| Physics 6091 | [38 páginas](https://isomer-user-content.by.gov.sg/334/42ee79d0-bb13-43f5-94ab-629729f88aa0/6091_y26_sy.pdf) | Evaluación de una disciplina; PDF4–7 separa prácticas, objetivos y formato. |
| Chemistry 6092 | [34 páginas](https://isomer-user-content.by.gov.sg/334/19dfb9f9-b3ce-4609-a3cf-5d30052317f5/6092_y26_sy.pdf) | Evaluación de química; no acredita obligatoriedad para todo alumno. |
| Biology 6093 | [29 páginas](https://isomer-user-content.by.gov.sg/334/3d8f2c30-36a3-4aa3-babe-4a41b314a381/6093_y26_sy.pdf) | Evaluación de biología; separada del currículo de enseñanza MOE. |
| Science 5086/5087/5088 | [64 páginas](https://isomer-user-content.by.gov.sg/334/a67fa90c-d3a3-4cb4-8c92-4f88346b5051/5086_y26_sy.pdf) | Son **pares** física/química, física/biología o química/biología, según el código. Tres secciones en un PDF no significan tres ciencias cursadas por cada estudiante. |

Las cuatro descargas directas devolvieron HTTP403; no se calcularon hashes ni bytes. No están listas para ingesta reproducible. La lectura web confirmó identidad y paginación, pero no sustituye poseer y verificar los bytes.

Los documentos MOE de enseñanza de [Física](https://www.moe.gov.sg/-/media/files/secondary/syllabuses/science/updated-2024/2023-olevel-physics-syllabus-updated-2024.pdf) y [Biología](https://www.moe.gov.sg/-/media/files/secondary/syllabuses/science/updated-2024/2023-olevel-biology-syllabus-updated-2024.pdf) aparecen en el índice del buscador oficial: Express, cohorte Sec3 de 2023, actualización abril de 2024. No se recuperaron sus bytes; su aplicación exacta a las cohortes Full SBB requiere comprobación adicional. La [página MOE de Express](https://www.moe.gov.sg/secondary/courses/express/electives/?subterm=Foreign+Language+Programme%3A+French%2C+German+or+Spanish&term=Language), indexada con fecha 18-06-2025, distingue Science obligatorio de asignaturas/itinerarios disponibles, pero la apertura actual exige JavaScript. No se ha certificado un inventario completo actual de enseñanza para G1/G2/G3 superior, Integrated Programme o preuniversitario H1/H2/H3.

Una URL de primaria terminada en `primary-science-syllabus-2023_may24.pdf` devolvió404, también bajo `/media/`. Esa revisión intermedia no se ha reconstruido. La incorporación de enero de 2026 corrige la insuficiencia de actualidad de la primera entrega, conservando por separado los bytes comprobados de octubre de 2022; no fusiona versiones.

## Japón: originales, traducciones y aplicación

El [índice MEXT vigente consultado](https://www.mext.go.jp/a_menu/shotou/new-cs/1384661.htm) publica los siguientes originales; la [comunicación oficial de implementación](https://www.mext.go.jp/magazine/backnumber/1421624.htm), apartado 学習指導要領, fija primaria desde abril de 2020, secundaria inferior desde abril de 2021 y superior desde abril de 2022 por progresión de cohortes. Las [sesiones del grupo de ciencias en 2026](https://www.mext.go.jp/b_menu/shingi/chukyo/chukyo3/111/giji_list/index.htm) documentan deliberaciones; no constituyen por sí mismas un currículo nuevo promulgado.

| Documento y naturaleza | Versión comprobada | Localizador de ciencias |
|---|---|---|
| [小学校学習指導要領 — original japonés de primaria](https://www.mext.go.jp/content/20230120-mxt_kyoiku02-100002604_01.pdf) | Portada: marzo de 2017; 337 páginas totales | PDF96–113, folios94–111. PDF114 abre Living Environment Studies para años1–2. |
| [中学校学習指導要領 — original japonés de secundaria inferior](https://www.mext.go.jp/content/20230120-mxt_kyoiku02-100002604_02.pdf) | Portada: marzo de 2017; 331 páginas | PDF80–100, folios78–98. No confundir con ciencias de primaria repetida en anexos. |
| [高等学校学習指導要領 — original japonés de secundaria superior](https://www.mext.go.jp/content/20230120-mxt_kyoiku02-100002604_03.pdf) | Portada: marzo de 2018; 604 páginas | PDF105–132, folios103–130; selección obligatoria en PDF25, folio23. Los anexos reproducen niveles previos. |
| [Section 4 Science — traducción inglesa de primaria](https://www.mext.go.jp/content/20220405-mxt_kyoiku02-000005241_003.pdf) | 23 páginas; traducción **provisional**, vinculada a revisión2017 por el [índice japonés](https://www.mext.go.jp/a_menu/shotou/new-cs/1417513_00001.htm) | Grade3 PDF1; Grade4 PDF6; Grade5 PDF11; Grade6 PDF16. Son comienzos de secciones, algunos a mitad de página. |
| [Section 4 Science — traducción inglesa de secundaria inferior](https://www.mext.go.jp/content/20220405-mxt_kyoiku02-000005242_003.pdf) | 27 páginas; traducción **provisional**, revisión2017 según [MEXT](https://www.mext.go.jp/a_menu/shotou/new-cs/1417513_00002.htm) | Campo físico PDF1; vida/Tierra comienza **PDF13**; secuenciación por años PDF10 y21–22; planificación y seguridad PDF25–27. |
| [解説 理科編 理数編 — comentario de ciencias y ciencias/matemáticas de superior](https://www.mext.go.jp/content/20250311-mxt_kyoiku02-100002620_05.pdf) | Portada: julio2018, revisión parcial agosto2021; 382 páginas; comentario, no otro estándar promulgado | Portada PDF1 verificada. No se ha catalogado exhaustivamente su interior. El `20250311` de la URL no lo convierte en currículo2025. |

La [estructura escolar MEXT](https://www.mext.go.jp/en/policy/education/overview/), apartados3–6, describe primaria6–12 y secundaria inferior12–15, ambas obligatorias. Ciencias como asignatura específica de primaria se organiza en años3–6; no debe deducirse ausencia de experiencias naturales en años1–2. Los años1/2/3 de secundaria inferior son años dentro de esa etapa, no primaria. Superior continúa tras nueve años obligatorios: tiempo completo de tres años, tiempo parcial/correspondencia de tres o más; también distingue cursos generales, especializados e integrados. Una edad nominal15–18 sólo describe la trayectoria ordinaria de tiempo completo.

En superior, **PDF25 del original, folio23, comprobado visualmente**, exige una de estas rutas: Ciencia y vida humana más **una** básica, o **tres** básicas entre física, química, biología y ciencias de la Tierra. Las cuatro disciplinas no son universales. PDF132 establece la precedencia de la ciencia básica correspondiente para las asignaturas avanzadas, como regla general. El producto debe distinguir oferta, prerrequisito y obligación.

La traducción de primaria permite observar progresión: preguntas desde diferencias/semejanzas en3º; predicciones justificadas en4º; diseño de procedimientos y control de condiciones en5º; mejora de explicaciones en6º (PDF1,6,11–12,16–17). Son énfasis curriculares, no etapas psicológicas rígidas. El uso inglés de “weight” requiere contraste terminológico con el original; no autoriza a confundir masa con fuerza en una tarea local.

El [portal MEXT en inglés](https://www.mext.go.jp/en/policy/education/elsec/title02/detail02/1373859.htm) mezcla apartados2017–2018 con traducciones2008–2009. Su enlace de Science de primaria pertenece al apartado antiguo. Para ciencias superior, el [índice de traducción2018](https://www.mext.go.jp/a_menu/shotou/new-cs/1417513.htm) ofrece nombres de materias y lenguas, no una traducción inglesa completa de ciencias. No se suple esa ausencia con2008 ni con traducción de terceros.

## Decisión concreta para el producto y pendientes de ingesta

1. Mantener diez identidades PDF separadas, con **original/traducción/comentario**, modalidad y páginas, y preferir la revisión primaria singapurense de enero de 2026 para el corte. La tarea principal gestiona su ingesta; esta auditoría no determina el estado compartido. La traducción inglesa japonesa de secundaria inferior queda **excluida de extracción automática por sus permisos PDF**, aunque sus bytes estén identificados. Los originales japoneses presentan encabezados/glifos defectuosos: revisar cada fragmento antes de usarlo como evidencia.
2. Ingerir el cuadro de primaria singapurense con estructura visual o anotación auditada de subrayados, no sólo texto. Separar Standard/Foundation y G1/G2/G3 como procedencia; no equipararlos a “nivel bajo/alto” de alumnos salvadoreños.
3. Mantener los cuatro programas de examen bloqueados para uso reproducible hasta obtener bytes oficiales y SHA. Recuperar y verificar currículos MOE superiores por modalidad/cohorte antes de afirmar cobertura de ese tramo.
4. Para cada propuesta salvadoreña, comprobar después prerrequisitos, edad real, tiempo, idioma, materiales, seguridad y evidencia solicitada. No se revisaron textos V4 ni se ejecutó alineación en esta tarea; toda equivalencia curricular SV permanece pendiente.

No se usan rankings como prueba pedagógica ni se promete eficacia por incorporar estas fuentes. Este paquete cierra identidad documental y varios errores de población posibles; no es un catálogo granular exhaustivo de resultados de aprendizaje.

## Evidencia técnica y revisión visual

Se usó `curl` con validación TLS y `pypdf` para identidad; Poppler para portadas y páginas de decisión. `urllib` falló por confianza SSL con MEXT; `curl` recuperó los PDF sin desactivar TLS. MOE devolvió404 en varias rutas antiguas `/-/media/`; las rutas `/media/` recuperaron primaria y los dos documentos inferiores. Enero de 2026 se cotejó desde una copia local leída sin modificarla y con la descarga fresca de la tarea principal, validada con TLS/certifi; coinciden SHA, bytes y páginas. SEAB/Isomer sigue con cuatro descargas403. No hubo rechazo de autorización ni ejecución cloud.

Los seis PDF MEXT están cifrados pero son legibles sin introducir clave. Cifrado no implica por sí mismo impedimento de extracción: cinco declaran permiso `EXTRACT=true` (`/P` interpretado como entero sin signo4294965972). La traducción inferior inglesa declara `EXTRACT=false` (4294965956): se identifica y excluye de ingesta automática. Nueve de las diez copias del paquete permiten extracción según sus metadatos; este conteo no acredita calidad textual ni activación para alineación. La extracción preliminar no comprobó ese permiso; sus resultados no habilitan la ingesta automática. En el cotejo correctivo sólo se inspeccionaron sus metadatos, sin realizar nueva extracción de esa traducción.

Renderizados inspeccionados: `sg_g1_cover.png`, `sg_lower_g2g3_peicai_1.png`, `sg_primary_actual_1.png`, `sg_primary_actual_22.png`, `jp_elementary_original_1.png`, `jp_lower_original_1.png`, `jp_upper_original_1.png`, `jp_upper_original_25.png`, `jp_upper_science_commentary_1.png`, `jp_elementary_science_en_6.png`, `jp_elementary_science_en_12.png`, `jp_lower_science_en_13.png`, todos en `/tmp/curriculos_sg_jp_2026/`. No se declara revisión visual completa de cada página ni de portadas SEAB.

Cotejo correctivo inspeccionado: `sg_primary_jan2026_1.png`, `sg_primary_jan2026_9.png`, `sg_primary_jan2026_10.png`, `sg_primary_jan2026_21.png`, `sg_primary_jan2026_31.png`, `sg_primary_jan2026_32.png`, `sg_primary_jan2026_36.png` y `sg_primary_oct2022_36.png`, en el mismo directorio. El diff local reproducible es `comparacion_primaria_2022_2026.diff`; contiene comparación mecánica, no dictámenes curriculares automáticos.


## Estado de integración posterior a esta auditoría

El repositorio incorporó los documentos admitidos en la colección `data/referencias_paises_2026/`,
con selección y huellas en `config/curriculos_paises_2026.yaml`. El paquete de investigación conserva
la etapa en que se verificaron las fuentes; el manifiesto de la colección es la autoridad de disponibilidad.
Hay doce PDF y 2.028 páginas entre los tres países, sin objetivos o vínculos aceptados por esta ingesta.
La traducción japonesa inglesa de secundaria inferior sin permiso EXTRACT permanece fuera del proceso.
