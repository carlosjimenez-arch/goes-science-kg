# Base educativa para la reconstrucción de GOES Science KG

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Fecha de consulta y corte: **21 de octubre de 2026**, America/Bogota. Responsable: investigación educativa del proyecto. Estado: memorando de decisiones fundamentadas; no certifica la eficacia de un currículo ni constituye aprobación del MINED.

Auditoría posterior del mismo corte: [fuentes primarias y correcciones](auditoria_fuentes_primarias.md). Corrige la inversión de columnas TIMSS 2019/2023 de la primera redacción y precisa la naturaleza del resumen ejecutivo ERCE. Las dimensiones operativas usan identificadores locales en `config/dimensiones_evaluativas_2026.yaml`.

## 1. Decisión principal

El producto debe construir una progresión salvadoreña de **conocimientos, prácticas y evidencias de aprendizaje**, sustentada en la nueva malla V4 y contrastada con marcos internacionales. Una coincidencia de palabras entre un tema y un estándar no demuestra que se enseñe ni evalúe la competencia correspondiente. La unidad de análisis propuesta es un resultado de aprendizaje verificable: qué debe hacer el estudiante, con qué contenido, bajo qué condiciones, y qué respuesta mostraría dominio.

La arquitectura educativa recomendada tiene cinco capas: currículo nacional y malla propuesta; progresiones y prerrequisitos; marcos externos independientes; experiencias de enseñanza; y evaluación de aprendizaje. Las recomendaciones de diseño en este documento son **inferencias del proyecto**, diferenciadas de los hallazgos atribuidos a fuentes.

No conviene convertir el porcentaje de cobertura internacional en el objetivo único. El criterio de aceptación debe combinar exactitud científica, fidelidad curricular, demanda cognitiva, viabilidad de aula, inclusión y aprendizaje observado. Un contenido amplio pero superficial puede obtener una cobertura aparente alta y producir poca comprensión.

## 2. Qué está realmente disponible al corte

| Referencia | Población y alcance | Estado verificado | Uso en GOES |
| --- | --- | --- | --- |
| PISA 2025 | Estudiantes de 15 años; ciencias como dominio principal | Marco final publicado el 29 de mayo de 2026; resultados, volumen I, publicados el 8 de septiembre de 2026 | Competencias para usar ciencia, referencia de desempeño y contextos de aplicación; no es una secuencia anual de enseñanza |
| ERCE 2019 | Lectura/escritura y matemática en 3.º y 6.º; ciencias únicamente en 6.º | Resultados publicados; El Salvador participó | Referencia regional de final de primaria y diagnóstico histórico |
| ERCE 2025 | Lectura y matemática en 3.º y 6.º; ciencias únicamente en 6.º | UNESCO anuncia primeros resultados para diciembre de 2026; El Salvador figura entre los 18 participantes | Registrar el ciclo, pero no inventar puntajes, brechas o nuevos porcentajes de cobertura |
| TIMSS 2023 | Cuarto y octavo grado; comparaciones por años de escolaridad | Resultados publicados | Desempeño internacional y relación con currículo enseñado |
| TIMSS 2027 | Cuarto y octavo grado | Marco publicado en 2025; recolección principal en 2027, resultados previstos para diciembre de 2028 | Referencia prospectiva versionada; nunca presentarlo como resultados observados |
| PISA 2029, alfabetización climática | Marco de un dominio específico | Documento consultado identificado como borrador preliminar | Horizonte de diseño; no reemplaza al marco final de ciencias 2025 |

Fuentes de estado: [OCDE, marco PISA 2025](https://www.oecd.org/en/publications/pisa-2025-assessment-and-analytical-framework_86c36975-en.html), [OCDE, resultados PISA 2025](https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en.html), [UNESCO, ERCE 2019](https://www.unesco.org/es/articles/estudio-regional-comparativo-y-explicativo-erce-2019), [UNESCO, calendario ERCE 2025](https://www.unesco.org/en/articles/unesco-and-countries-latin-america-and-caribbean-prepare-present-results-erce-2025-regions-leading), [IEA, TIMSS 2023](https://www.iea.nl/studies/iea/timss/timss2023), [Boston College, calendario TIMSS 2027](https://timss.bc.edu/timss2027/), [OCDE, borrador climático 2029](https://www.oecd.org/content/dam/oecd/en/about/projects/edu/pisa-rdi-programme/PISA%202029%20Climate%20Literacy%20Framework%20Digital%20version.pdf).

**Regla de comparación propuesta:** cada estándar debe guardar edad, grado o etapa, ciclo de evaluación, país/jurisdicción, fecha, obligatoriedad, fuente y versión. PISA no equivale automáticamente a noveno grado. TIMSS permite poblaciones evaluadas en grados diferentes; por ejemplo, la tabla de cuarto muestra Türkiye en quinto. Los puntajes de PISA, TIMSS y ERCE no comparten escala y no se deben restar entre sí. La edad normativa y los años de escolarización deben verificarse antes de sugerir adelantos o retrasos.

La documentación general de [IEA sobre poblaciones TIMSS](https://www.iea.nl/studies/iea/timss) explica los grados y las opciones de participación; las notas de cada tabla son parte de la evidencia, no metadatos prescindibles.

## 3. PISA: incorporar prácticas y juicio sobre evidencia

El marco final de ciencias PISA 2025 articula tres competencias: explicar fenómenos; diseñar y evaluar investigaciones e interpretar críticamente datos; e investigar, evaluar y usar información científica para decidir y actuar. Cruza conocimiento de contenido, procedimental y epistémico, en sistemas físicos, vivos y de la Tierra y el espacio. También contempla identidad científica y agencia ambiental. El diseño aproxima las competencias a una distribución de puntos de 40/30/30 y distingue demanda cognitiva. **Son especificaciones de evaluación, no porcentajes obligatorios del tiempo de clase salvadoreño.** Fuente: [marco final, capítulo 2, tablas 2.1–2.4 y sección ambiental](https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/05/pisa-2025-assessment-and-analytical-framework_3abce6d6/86c36975-en.pdf).

Implicaciones de diseño:

- Separar `contenido`, `practica`, `tipo_conocimiento`, `demanda` y `contexto`; compartir tema no basta para declarar una alineación.
- Exigir evidencia específica de interpretación de gráficos, control de variables, incertidumbre y evaluación de fuentes. Una unidad que solo explica una definición no cubre la competencia de investigar información.
- Hacer visibles las limitaciones de modelos escolares y la diferencia entre observación, inferencia y afirmación. Los jueces deben poder rechazar una explicación elegante que no esté sustentada.
- Tratar interés, autoeficacia y agencia como dimensiones que se observan con instrumentos adecuados; no inferir identidad científica desde una respuesta correcta.
- Diferenciar familiaridad con el formato PISA de mejora de comprensión y transferencia.

La nota oficial PISA 2025 de El Salvador informa que el 35% alcanzó al menos nivel 2 en ciencias, frente al 74% OCDE, y que la proporción por debajo de ese nivel disminuyó seis puntos porcentuales respecto de 2022. En lectura alcanzó nivel 2 el 29% y en matemática el 12%. Estos resultados describen a la población escolar cubierta por PISA; no permiten atribuir el cambio a una malla particular. Fuente: [nota de El Salvador, desempeño y calidad de datos](https://www.oecd.org/en/publications/pisa-2025-results-volume-i-country-notes_2d4ff9ea-en/el-salvador_f00ad4b8-en.html).

**Inferencia para el producto:** el tutor y los paquetes deben incluir apoyos de lectura científica y matemática contextual —unidades, proporciones, lectura de ejes— y evaluarlos por separado. De lo contrario, un error de comprensión lectora puede diagnosticarse equivocadamente como desconocimiento de física.

El borrador climático PISA 2029 se conserva como señal de evolución, etiquetado `draft`, sin trasladar sus formulaciones a un catálogo definitivo de estándares. [Portada y estado del documento](https://www.oecd.org/content/dam/oecd/en/about/projects/edu/pisa-rdi-programme/PISA%202029%20Climate%20Literacy%20Framework%20Digital%20version.pdf).

## 4. ERCE: primaria y contexto latinoamericano

ERCE parte de convergencias entre currículos regionales. El **resumen ejecutivo publicado en 2021** presenta cinco dominios de ciencias: organismo humano y bienestar; relaciones entre ciencia, tecnología y sociedad; planeta y entorno solar; fenómenos materiales y energéticos; y organismos, relaciones ecológicas y ambiente. Resume tres familias de procesos: reconocer información, analizar/aplicar y producir/transferir/evaluar conocimiento. Su página PDF 19 documenta estas categorías y la evaluación de sexto; no constituye el marco técnico granular completo. En ciencias de sexto los promedios publicados incluyen Cuba 779, Costa Rica 758, Uruguay 731, Perú 723, El Salvador 705 y región 702. El resumen excluye a El Salvador de comparaciones con TERCE 2013 porque no participó. La cercanía de promedios debe interpretarse con sus errores e intervalos, sin construir un orden absoluto por diferencias pequeñas. Fuente: [UNESCO, resumen ejecutivo, páginas PDF 19–20 y gráfico 15](https://unesdoc.unesco.org/in/rest/annotationSVC/DownloadWatermarkedAttachment/attach_import_467d448e-d64b-4f4d-b86f-f65db90b6b9b?_=380257spa.pdf).

El análisis curricular histórico de El Salvador identificó en sexto un peso cercano al 40% de cuerpo humano y salud. Describe los documentos analizados para ERCE 2019: **no describe automáticamente la V4 ni el programa público 2026**. Fuente: [análisis nacional alojado por MINED](https://enlaces.mined.gob.sv/evaluacion/publicaciones/2021/2021%20-%20ERCE%202019%20An%C3%A1lisis%20El%20Salvador.pdf).

Implicaciones de diseño:

- Crear un catálogo ERCE propio; no usar TIMSS como sustituto de ERCE ni renombrar un catálogo 2019 como 2025.
- Alinear ciencias de 2.º a 5.º como progresiones hacia la expectativa de sexto; esos grados no recibieron una prueba ERCE de ciencias.
- Usar Costa Rica como comparación regional prioritaria y Uruguay y Perú como contrastes adicionales. Cuba sirve para contraste de logro; su promedio tampoco acredita una política pedagógica concreta.
- Distinguir países presentes en el análisis curricular de países que realmente rindieron la evaluación. Una lista de miembros del LLECE no prueba participación en cada ciclo.
- Actualizar resultados 2025 cuando UNESCO los publique, con nueva versión y análisis de comparabilidad. Este memorando no encontró un marco detallado público 2025 suficiente para certificar todas sus categorías y ponderaciones; las de 2019 deben conservar su etiqueta histórica.

UNESCO confirma publicación de resultados académicos en diciembre de 2026, socioemocionales en abril de 2027 y escritura durante el segundo semestre de 2027. [Anuncio oficial de agosto/septiembre de 2026](https://www.unesco.org/en/articles/unesco-and-countries-latin-america-and-caribbean-prepare-present-results-erce-2025-regions-leading).

## 5. TIMSS: progresión curricular y razonamiento

El marco 2027 mantiene, en cuarto, biología 45%, ciencias físicas 35% y Tierra 20%; en octavo, biología 35%, química 20%, física 25% y Tierra 20%. Para conocer/aplicar/razonar asigna 35/40/25 en cuarto y 35/35/30 en octavo. Aumenta el énfasis de razonamiento en cuarto e identifica conocimiento ambiental como subescala transversal. Estos son porcentajes de puntos de la prueba. Fuente: [IEA/Boston College, marco 2027, páginas impresas 23–25; copia ERIC del documento original](https://files.eric.ed.gov/fulltext/ED676227.pdf), [registro oficial IEA](https://www.iea.nl/publications/assessment-framework/timss-2027-assessment-frameworks).

Los resultados 2023 de ciencias sitúan a Singapur en 607 puntos en cuarto; Corea en 583 y Chinese Taipei en 573. En octavo Singapur obtuvo **606**, Chinese Taipei **572**, Japón **557** y Corea **545**; Inglaterra y Finlandia 531, Australia 520 y Chile 455. La lectura visual de las tablas originales de 2023 confirma estos valores: encabezados de ciencias de cuarto y octavo, tablas 2.1.1 y 2.2.1, columna de promedio. Son poblaciones y escalas de grado distintas; no corresponde calcular una ganancia longitudinal entre ellas. La primera redacción había confundido las columnas 2019/2023 de una tabla comparativa; los valores TIMSS 2023 del catálogo previo del repositorio eran correctos. Fuentes: [IEA, portal de resultados y tablas originales](https://timss2023.org/results/), [ERC, informe nacional oficial, tabla 6.1, página PDF 79/impresa 72](https://www.erc.ie/wp-content/uploads/2024/12/B23701-TIMSS-2023-National-Report-Inside-Pages-rev6-electronic.pdf).

Recomendación: usar 2027 para requisitos de diseño prospectivos y 2023 para desempeño observado. Separar contenido cubierto, oportunidad de realizar una práctica y evidencia de dominio. Las inferencias de prerrequisito entre conceptos deben justificarse con una relación de dependencia concreta; el orden de una lista de estándares no basta para afirmar causalidad cognitiva.

## 6. Sistemas comparadores y qué transferir

La selección no debe apoyarse en reputaciones históricas. PISA 2025 sitúa entre los diez primeros de sus tres dominios a Estonia, Japón, Corea, Singapur, Chinese Taipei, Macao y Reino Unido, junto con jurisdicciones chinas. La comparación de Reino Unido no es idéntica a una comparación del currículo de Inglaterra. Tampoco se debe presentar B-S-J-Z como todo el sistema de China. Fuente: [OCDE, resultados PISA 2025, introducción y prefacio](https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en.html).

| Sistema | Documento o mecanismo educativo observado | Adaptación que se propone experimentar |
| --- | --- | --- |
| Singapur | Programa primario 2023 organizado en ideas centrales, prácticas y valores; estudiantes que indagan y evaluación con retroalimentación | Progresión conceptual explícita, menos objetivos por sesión y tareas que produzcan explicaciones y evidencia; registrar diferencias Standard/Foundation |
| Estonia | Marco nacional concretado por escuelas, competencias y evaluación formativa; reformas curriculares aprobadas en 2023 | Núcleo común verificable y variantes por recursos de escuela, sin imponer una única actividad a todo contexto |
| Inglaterra | Conocimientos secuenciados y prácticas científicas integradas en las disciplinas; distinción entre contenido obligatorio y orientaciones | Mapear conjuntamente contenido y práctica, reforzar transiciones y conservar el estatus normativo de cada fragmento |
| Finlandia | Currículo por asignaturas, competencias transversales, adaptación local y al menos un módulo interdisciplinario anual | Un proyecto contextual con evidencias de varias disciplinas; evitar confundir interdisciplinariedad con eliminar asignaturas |
| Costa Rica | Programas de ciencias para I y II ciclos y materiales oficiales para metodología indagatoria | Estudiar la claridad del acompañamiento docente en español y adaptar tareas, sin atribuirle por ello el resultado ERCE |
| Japón, Corea, Chinese Taipei y Macao | Alto desempeño observado en los estudios citados | Segunda ronda de extracción de fuentes curriculares vigentes y condiciones de implementación antes de importar una secuencia concreta |

Fuentes curriculares: [MOE Singapur, programa primario 2023](https://www.moe.gov.sg/-/media/files/primary/syllabus/2023-primary-science.ashx), [Ministerio de Estonia, organización educativa](https://www.hm.ee/en/education-research-and-youth-affairs/general-education/general-education-estonia), [Estonia, reformas aprobadas en 2023](https://www.hm.ee/sites/default/files/documents/2024-06/MoER%20annual%20report%202023.pdf), [Department for Education, ciencias](https://www.gov.uk/government/publications/national-curriculum-in-england-science-programmes-of-study/national-curriculum-in-england-science-programmes-of-study), [Agencia Finlandesa de Educación, currículo básico](https://www.oph.fi/en/education-and-qualifications/national-core-curriculum-primary-and-lower-secondary-basic-education), [MEP Costa Rica, programa I/II ciclos](https://www.mep.go.cr/sites/default/files/media/ciencias1y2ciclo2018.pdf), [MEP, formación en indagación](https://mep.go.cr/educatico/modulo-3-indagacion).

Límites de acceso: el sitio central MOE devolvió una verificación JavaScript; se revisaron sus extractos indexados y materiales de escuelas públicas, no se declara una extracción íntegra del PDF. La traducción inglesa de Estonia encontrada en Riigi Teataja era histórica; no se usó como currículo vigente. La página inglesa de MEXT mezcla revisiones: algunos PDF de ciencias corresponden a 2008/2009. El producto debe rechazar esa mezcla automática por fecha, aunque provenga de un ministerio. No se completó una extracción granular vigente de Japón, Corea, Chinese Taipei o Macao en este memorando.

**Límite causal:** las evaluaciones internacionales observacionales no identifican por sí mismas qué método produjo el resultado. Ingreso, selección, cobertura poblacional, lengua de evaluación, preparación docente y recursos pueden modificar una comparación. El proyecto debe transferir mecanismos plausibles y probarlos localmente; no copiar una lista de temas de los países con mayor promedio.

## 7. Evidencia de enseñanza de ciencias

### Indagación con apoyo suficiente

El metaanálisis de Lazonder y Harmsen sintetiza 72 estudios y encuentra beneficios de la guía para el aprendizaje por indagación, con efecto sobre resultados de aprendizaje de d = 0,50 e intervalo 95% de 0,37–0,62. La heterogeneidad y la evidencia por edades impiden convertirlo en una receta universal. Fuente: [artículo original, Review of Educational Research, 2016](https://pure.rug.nl/ws/portalfiles/portal/81069469/Meta_analysis_of_inquiry_based_learning_Effects_of_guidance.pdf).

Inferencia: el generador debe decidir el grado de apoyo usando presaberes observados, complejidad y objetivo. Para estudiantes principiantes: modelado breve, ejemplo resuelto, variables delimitadas, registro preparado y preguntas de interpretación. La apertura aumenta cuando se demuestra comprensión. Una actividad de manipulación sin explicación o análisis de datos no demuestra indagación.

### Concepciones previas y lenguaje disciplinar

La guía EEF de secundaria recomienda identificar ideas previas, atender las concepciones que chocan con la explicación científica y comprobar el cambio mediante evaluación formativa posterior. La guía de primaria recomienda enseñar explícitamente vocabulario científico y retomarlo con uso repetido. Son orientaciones basadas en síntesis de evidencia y contexto británico, no ensayos de este producto en El Salvador. Fuentes: [EEF, secundaria, 2018](https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/science-ks3-ks4), [EEF, primaria, 2023](https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/primary-science-ks1-ks2).

Inferencia: cada paquete necesita una pregunta diagnóstica con distractores interpretables, vocabulario contextualizado, una respuesta esperada y una comprobación diferida. Evitar etiquetas clínicas o supuestos estilos de aprendizaje. El juez psicopedagógico revisará carga, claridad, apoyos y accesibilidad; no emitirá diagnósticos individuales.

### Recuperación, espaciamiento y representaciones

IES/What Works Clearinghouse recomienda espaciar contenido, alternar ejemplos resueltos con resolución, combinar gráficos y explicación verbal, relacionar representaciones concretas y abstractas, practicar recuperación y hacer preguntas explicativas. La guía declara niveles de evidencia distintos: no todas sus recomendaciones tienen la misma fuerza. Fuente: [IES, Organizing Instruction and Study to Improve Student Learning, 2007](https://ies.ed.gov/ncee/wwc/PracticeGuide/1).

Inferencia: el tutor debe programar recuperaciones con retroalimentación y problemas nuevos que conserven la estructura conceptual. Repetir exactamente el mismo ítem puede medir recuerdo de la respuesta. Los intervalos iniciales del software son hipótesis ajustables, no una pauta universal clínicamente validada.

### Aprendizaje activo: no extrapolar el tamaño de efecto

Freeman y colaboradores analizaron 225 estudios universitarios STEM; encontraron una mejora media de 0,47 desviaciones estándar con aprendizaje activo y menor fracaso respecto de exposición tradicional. La población es universitaria, por lo que ese tamaño no predice el efecto en segundo grado salvadoreño ni en un tutor de IA. Fuente: [PNAS, artículo original, 2014](https://doi.org/10.1073/pnas.1319030111).

Inferencia: incorporar predicción individual, explicación, discusión estructurada y revisión de la respuesta. Medir el aprendizaje obtenido por esas tareas, sin etiquetar cualquier clic como aprendizaje activo.

## 8. Adaptación curricular y operacional a El Salvador

MINED publica programas de Ciencia y Tecnología para 2.º–6.º, tercer ciclo y bachillerato, además de textos, cuadernos y guías. La asignatura sustituyó Ciencia, Salud y Medio Ambiente en 2.º–6.º desde 2022. El programa primario público articula Indagación, Creatividad y Comunicación con Integralidad —ICC+I— y evaluación diagnóstica, formativa y sumativa. Fuentes: [portal curricular](https://www.mined.gob.sv/ciencia-educativa/), [programa de 2.º–6.º, secciones III–V](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/1.%20Programas%20de%20estudio/Programas%20de%20estudio_Ciencia%20y%20Tecnolog%C3%ADa_2.%C2%B0%20a%206.%C2%B0%20grados.pdf).

La ruta web contiene `2026`, pero eso no basta para inferir año de aprobación o nueva versión normativa. Deben conservarse portada, créditos, fecha interna, fecha de descarga, hash y alcance. La V4 entregada por el usuario debe ser su propia versión de fuente; no se puede declarar oficial por su nombre. En la inspección limitada de rutas de esta investigación solo se identificaron mallas hasta v3; la validación e ingestión V4 queda a cargo del inventario técnico del proyecto.

MINED contempla pruebas impresas cuando no es viable la evaluación en línea y advierte cambios de cobertura por transiciones curriculares. Es evidencia de que no debe suponerse conectividad homogénea ni equivalencia de todas las cohortes. Fuente: [Conociendo Mis Logros 2025, documento informativo](https://mined.gob.sv/evaluacion/docs/2025/DOC%20informativo%20CML%202025.pdf).

Diseño propuesto:

1. **Español claro con precisión científica.** Conservar el término original de estándares extranjeros y su traducción revisada; generar lenguaje del estudiante y nota docente separados. No bajar la demanda conceptual por simplificar vocabulario.
2. **Perfiles de aula explícitos.** Grado, presaberes, tiempo real, tamaño del grupo, materiales, conectividad, condiciones de acceso y necesidad de apoyos. Los valores no conocidos se marcan pendientes; no se rellenan con estereotipos sobre escuelas rurales.
3. **Tres modalidades equivalentes en objetivo.** Actividad sin internet y con materiales cotidianos; actividad con dispositivo compartido; y extensión con laboratorio o simulador. No afirmar que son equivalentes en resultados sin probarlo.
4. **Contextos locales con datos auténticos.** Lluvia, agua, suelo, energía, biodiversidad y riesgo geológico, con fuente, fecha, unidad e incertidumbre. MARN publica monitoreo y mapas sobre lluvia, estaciones, sismos e inundaciones. No inventar una serie local para hacer un gráfico más atractivo. Fuentes: [catálogo de mapas MARN](https://mapas.snet.gob.sv/), [Observatorio de Amenazas, explicación de su trabajo](https://www.ambiente.gob.sv/el-observatorio-de-amenazas-la-ciencia-detras-de-la-prevencion-en-el-salvador/).
5. **Pertinencia climática.** Una tarea importada sobre cuatro estaciones requiere adaptación: la fuente MARN distingue épocas seca y lluviosa. No basta con cambiar nombres de ciudades.
6. **Seguridad por actividad.** Materiales, supervisión, residuos y sustitución segura deben quedar explícitos. No proponer visitas a zonas amenazadas ni prácticas peligrosas para ganar autenticidad; los datos oficiales permiten investigar sin esa exposición.
7. **Progresión con límites de modelo.** Observación macroscópica, representación y explicación pueden aparecer en diferentes etapas. Cada prerrequisito debe indicar si es conceptual, matemático, lingüístico o procedimental y si es necesario o solo facilitador.

## 9. Qué pueden garantizar los agentes y qué deben demostrar los datos

El estudio IEA de generación automática de ítems TIMSS de cuarto combinó evaluación por expertos y prueba de campo con análisis psicométrico. Encontró muchos ítems útiles, pero menor calidad agregada que los originales: dificultades fuera del objetivo, baja o negativa discriminación, dependencia entre ítems, repetición y problemas de distractores. El trabajo usó modelos disponibles en 2024; no prueba el comportamiento de todos los modelos posteriores. Sí demuestra la necesidad de evaluar funcionamiento con estudiantes, más allá del texto aparente. Fuente: [Muszyński et al., IEA, 2025, resumen y conclusiones](https://www.iea.nl/sites/default/files/2025-10/Muszy%C5%84ski%20AIG%20LLM%20Report.pdf).

Por tanto, la automatización recomendada evita que cada salida necesite aprobación humana rutinaria, pero no convierte consenso de modelos en evidencia de eficacia. Un paquete puede pasar validaciones automáticas y mantener estado `eficacia_no_evaluada`. Un ítem puede tener una dificultad objetivo y conservar `calibracion_no_observada`. Los modelos no sustituyen la medición empírica de aprendizaje ni la autoridad curricular.

Jueces propuestos y criterios independientes:

| Juez | Debe comprobar | Debe abstenerse cuando |
| --- | --- | --- |
| Científico de la disciplina | Exactitud, condiciones de validez, unidades, cálculos y modelos | Falta fuente o no puede resolver de forma independiente |
| Curricular salvadoreño | Fidelidad V4, alcance, grado, vigencia y prerrequisitos | Mezcla versiones o confunde propuesta con norma |
| Evaluación internacional | Competencia efectivamente exigida y evidencia observable | Solo hay coincidencia temática |
| Psicopedagógico | Carga, claridad, apoyos, accesibilidad y retroalimentación | Faltan condiciones del grupo o requiere diagnóstico clínico |
| Psicométrico | Clave única, distractores plausibles, independencia y especificación | Se solicita certificar dificultad empírica sin respuestas de estudiantes |
| Contexto y factibilidad | Tiempo, recursos, idioma, entorno y seguridad | Los supuestos necesarios no están verificados |

El umbral de aceptación no debe promediar un fallo científico crítico con buenas notas de estilo. Una contradicción, una respuesta incorrecta o ausencia de evidencia bloquea la salida; se permiten corrección acotada y nueva verificación. El autor no debe ser su único juez. La independencia de instrucciones y recuperación de evidencia ayuda a probar el mecanismo, pero no garantiza independencia estadística entre modelos.

## 10. Roadmap educativo con puertas de aceptación

| Fase | Entregable verificable | Criterio para avanzar |
| --- | --- | --- |
| E0: fijar fuentes | Inventario V4 y programas oficiales, hashes, versiones, derechos y celdas/páginas | Ningún archivo supuesto; conflictos y campos faltantes explícitos |
| E1: definir el modelo educativo | Resultados atómicos, contenido/prácticas/conocimiento/contexto y tipos de prerrequisito | Ejemplos positivos y negativos de alineación y granularidad |
| E2: construir catálogos | PISA 2025 final, ERCE 2019 histórico y estado 2025, TIMSS 2027 prospectivo; comparadores | Toda afirmación apunta a un fragmento y conserva edad, estatus y versión |
| E3: validar una progresión completa | Una unidad V4 con diagnóstico, apoyos, indagación, explicación, evaluación y repaso | Cero fallos científicos críticos; trazabilidad y factibilidad; resultados de jueces registrados |
| E4: calibrar evaluación | Banco de ítems con modelos de respuesta y prueba independiente | Duplicados controlados; dificultad objetivo separada de dificultad observada; sin entrenamiento sobre el conjunto final de evaluación |
| E5: demostrar utilidad | Piloto de comprensión, transferencia, retención, tiempo docente y equidad | Diseño de comparación y métricas definidos antes de observar resultados; estimación de incertidumbre |
| E6: ampliar con control | Cobertura por grados y disciplinas; incorporación de resultados ERCE 2025 cuando existan | No degradar calidad, tiempo, costo o accesibilidad frente a la unidad validada |

Las fases son dependencias de evidencia, no un calendario prometido. E0–E3 pueden automatizarse y producir artefactos reproducibles. E5 requiere aprendizaje real para sostener una afirmación de eficacia. Se puede entregar una plataforma funcional antes de esa validación, siempre que no presente como demostrado lo que todavía es hipótesis.

## 11. Limitaciones y pendientes concretos

- No se certificó aquí la integridad o aprobación oficial de V4. El documento no contiene una comparación granular V3→V4.
- No se hicieron experimentos escolares ni se obtuvo evidencia causal propia. Las propuestas de enseñanza deben verificarse en implementación local.
- El alcance de la investigación cubre marcos y decisiones; todavía debe construirse el catálogo completo por fragmentos y extraerse con revisión las fuentes de sistemas comparadores.
- No se publican rankings nuevos ni diferencias derivadas de microdatos. Para ello se requieren ponderaciones muestrales, valores plausibles, réplicas y errores estándar conforme al manual de cada estudio.
- Las páginas oficiales cambian y pueden bloquear automatización. La ingestión debe preservar una copia permitida y su procedencia; los extractos de búsqueda no bastan para una cita granular de producción.
- El estado de publicación se verificó al corte indicado. Las referencias anunciadas para después del 21 de octubre de 2026 no se tratan como resultados disponibles.

## 12. Referencias primarias y de autoridad consultadas

Todas consultadas el **21 de octubre de 2026**. Los enlaces anteriores llevan al documento que soporta cada afirmación. Esta relación facilita congelar el registro de fuentes durante E0.

| ID | Institución/documento | Versión y propósito |
| --- | --- | --- |
| EDU-01 | [OCDE, marco PISA 2025](https://www.oecd.org/en/publications/pisa-2025-assessment-and-analytical-framework_86c36975-en.html) | Final, 2026; competencias y evaluación |
| EDU-02 | [OCDE, resultados PISA 2025 I](https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en.html) | 8-09-2026; desempeño observado |
| EDU-03 | [OCDE, El Salvador PISA 2025](https://www.oecd.org/en/publications/pisa-2025-results-volume-i-country-notes_2d4ff9ea-en/el-salvador_f00ad4b8-en.html) | Nota nacional; población y resultados |
| EDU-04 | [UNESCO, ERCE 2019](https://www.unesco.org/es/articles/estudio-regional-comparativo-y-explicativo-erce-2019) | Alcance y participación efectiva |
| EDU-05 | [UNESCO, resumen ejecutivo ERCE 2019, publicado en 2021](https://unesdoc.unesco.org/in/rest/annotationSVC/DownloadWatermarkedAttachment/attach_import_467d448e-d64b-4f4d-b86f-f65db90b6b9b?_=380257spa.pdf) | Resumen de dominios, procesos y resultados; no marco técnico completo |
| EDU-06 | [UNESCO, calendario ERCE 2025](https://www.unesco.org/en/articles/unesco-and-countries-latin-america-and-caribbean-prepare-present-results-erce-2025-regions-leading) | 2026; anuncio de publicación |
| EDU-07 | [IEA, TIMSS 2023](https://www.iea.nl/studies/iea/timss/timss2023) | Alcance y resultados |
| EDU-08 | [IEA, marco TIMSS 2027](https://www.iea.nl/publications/assessment-framework/timss-2027-assessment-frameworks) | 2025; marco prospectivo |
| EDU-09 | [IEA/Boston College, marco completo vía ERIC](https://files.eric.ed.gov/fulltext/ED676227.pdf) | Documento original, tablas de ciencias |
| EDU-10 | [Boston College, calendario TIMSS 2027](https://timss.bc.edu/timss2027/) | Fechas de recolección y resultados |
| EDU-11 | [MINED, Ciencia Educativa](https://www.mined.gob.sv/ciencia-educativa/) | Portal oficial; programas y materiales |
| EDU-12 | [MINED, 2.º–6.º](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/1.%20Programas%20de%20estudio/Programas%20de%20estudio_Ciencia%20y%20Tecnolog%C3%ADa_2.%C2%B0%20a%206.%C2%B0%20grados.pdf) | Programa público; ICC+I |
| EDU-13 | [MINED, tercer ciclo](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/1.%20Programas%20de%20estudio/Programas%20de%20estudio_Ciencia%20y%20Tecnolog%C3%ADa_III%20ciclo.pdf) | Programa público; pendiente de extracción granular |
| EDU-14 | [MINED, bachillerato](https://www.mined.gob.sv/materiales/2026/CIENCIA_Y_TECNOLOGIA/1.%20Programas%20de%20estudio/Programas%20de%20estudio_Ciencia%20y%20Tecnolog%C3%ADa_Bachillerato.pdf) | Programa público; pendiente de extracción granular |
| EDU-15 | [MINED/UNESCO, análisis ERCE nacional](https://enlaces.mined.gob.sv/evaluacion/publicaciones/2021/2021%20-%20ERCE%202019%20An%C3%A1lisis%20El%20Salvador.pdf) | Histórico; no sustituye V4 |
| EDU-16 | [MOE, primaria Singapur](https://www.moe.gov.sg/-/media/files/primary/syllabus/2023-primary-science.ashx) | 2023; acceso completo pendiente por barrera JavaScript |
| EDU-17 | [Estonia, estructura educativa](https://www.hm.ee/en/education-research-and-youth-affairs/general-education/general-education-estonia) | Marco y adaptación escolar |
| EDU-18 | [Estonia, informe ministerial 2023](https://www.hm.ee/sites/default/files/documents/2024-06/MoER%20annual%20report%202023.pdf) | Reformas aprobadas; no extracción de todos los anexos |
| EDU-19 | [DfE, ciencias Inglaterra](https://www.gov.uk/government/publications/national-curriculum-in-england-science-programmes-of-study/national-curriculum-in-england-science-programmes-of-study) | Secuenciación, prácticas y estatus normativo |
| EDU-20 | [Agencia Finlandesa, currículo básico](https://www.oph.fi/en/education-and-qualifications/national-core-curriculum-primary-and-lower-secondary-basic-education) | Asignaturas, transversalidad y evaluación |
| EDU-21 | [MEP, ciencias I/II ciclos Costa Rica](https://www.mep.go.cr/sites/default/files/media/ciencias1y2ciclo2018.pdf) | Mayo 2016; referencia regional a versionar |
| EDU-22 | [Lazonder y Harmsen](https://pure.rug.nl/ws/portalfiles/portal/81069469/Meta_analysis_of_inquiry_based_learning_Effects_of_guidance.pdf) | 2016; metaanálisis original |
| EDU-23 | [EEF, primaria](https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/primary-science-ks1-ks2) | 2023; guía basada en evidencia |
| EDU-24 | [EEF, secundaria](https://educationendowmentfoundation.org.uk/education-evidence/guidance-reports/science-ks3-ks4) | 2018; guía basada en evidencia |
| EDU-25 | [IES/WWC, organización del aprendizaje](https://ies.ed.gov/ncee/wwc/PracticeGuide/1) | 2007; fuerza de evidencia diferenciada |
| EDU-26 | [Freeman et al., PNAS](https://doi.org/10.1073/pnas.1319030111) | 2014; metaanálisis universitario STEM |
| EDU-27 | [Muszyński et al., IEA](https://www.iea.nl/sites/default/files/2025-10/Muszy%C5%84ski%20AIG%20LLM%20Report.pdf) | 2025; validación de ítems LLM y límites |
| EDU-28 | [MARN, mapas de monitoreo](https://mapas.snet.gob.sv/) | Datos locales a congelar por fecha |
| EDU-29 | [MARN, Observatorio de Amenazas](https://www.ambiente.gob.sv/el-observatorio-de-amenazas-la-ciencia-detras-de-la-prevencion-en-el-salvador/) | 10-02-2025; contexto climático y geológico |
| EDU-30 | [OCDE, clima PISA 2029](https://www.oecd.org/content/dam/oecd/en/about/projects/edu/pisa-rdi-programme/PISA%202029%20Climate%20Literacy%20Framework%20Digital%20version.pdf) | Borrador preliminar; prospectiva |
