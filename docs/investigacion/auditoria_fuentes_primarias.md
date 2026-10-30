# Auditoría de fuentes y dimensiones evaluativas

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Corte y consulta: **21 de octubre de 2026**. Alcance: revisión de las afirmaciones educativas introducidas en `educacion.md` y `config/referentes_2026.yaml`, con comprobación granular de tres documentos primarios. Se distingue lectura de fuente, metadatos bibliográficos, decisiones locales e ingesta. Esta auditoría no certifica eficacia pedagógica, alineación de la V4 ni aprobación ministerial.

## Corrección de puntajes TIMSS

**La investigación inicial invirtió las columnas 2019/2023 de una tabla comparativa. Los valores TIMSS 2023 que ya tenía el catálogo previo del repositorio eran correctos. Se retira expresamente la observación que proponía corregirlos.** Se corrigieron los valores introducidos por esta investigación en `educacion.md` y en `hallazgos_verificados` y `EDU_PENDING_06` de `config/referentes_2026.yaml`.

La comprobación visual se efectuó renderizando, sin modificar, las tablas oficiales locales:

- `data/fuentes/externos/timss/TIMSS2023_2-2-1_ach-g8s-dist.pdf`, página PDF 1: encabezado de ciencias, grado 8, edición 2023, tabla 2.2.1; columna **Average Scale Score**. La tabla tiene una sola columna de medias del ciclo, seguida de intervalo y desviación; los valores entre paréntesis son errores estándar, según su nota.
- `data/fuentes/externos/timss/TIMSS2023_2-1-1_ach-g4s-dist.pdf`, página PDF 1: encabezado de ciencias, grado 4, edición 2023, tabla 2.1.1; misma columna de promedio. Confirma Singapur 607, Corea 583 y Chinese Taipei 573, que estaban bien transcritos.

| Jurisdicción | Octavo, media 2023 | Error estándar |
| --- | ---: | ---: |
| Singapur | 606 | 5,7 |
| Chinese Taipei | 572 | 2,4 |
| Japón | 557 | 3,1 |
| Corea | 545 | 2,2 |
| Inglaterra | 531 | 4,3 |
| Finlandia | 531 | 3,2 |
| Australia | 520 | 3,2 |
| Chile | 455 | 2,7 |

La lectura visual coincide con la tabla 6.1 del [informe del centro nacional de TIMSS en Irlanda, ERC](https://www.erc.ie/wp-content/uploads/2024/12/B23701-TIMSS-2023-National-Report-Inside-Pages-rev6-electronic.pdf), página PDF **79**, folio impreso **72**. La [figura 14 de NSF/NCSES](https://ncses.nsf.gov/pubs/nsbsep20261/stem-talent-education-training-and-workforce-2) ofrece otra corroboración oficial de las siete primeras jurisdicciones de esta selección. Las tablas originales proceden del [portal IEA de resultados 2023](https://timss2023.org/results/).

Las marcas de población, muestreo y participación forman parte de las tablas y deben conservarse al ingerirlas. No se interpretaron diferencias pequeñas como significativas sin contraste estadístico; tampoco se compararon escalas de cuarto y octavo como crecimiento de una cohorte. La leyenda de una fuente no se puede trasladar a otra: por ejemplo, las marcas de comparaciones con Estados Unidos en NSF no son las notas de cumplimiento muestral de IEA.

## Identidad bibliográfica y estado

| Fuente | Dato confirmado y precisión necesaria |
| --- | --- |
| [OCDE, marco final PISA 2025](https://www.oecd.org/en/publications/pisa-2025-assessment-and-analytical-framework_86c36975-en.html) | Título: *PISA 2025 Assessment and Analytical Framework*; 214 páginas, DOI `10.1787/86c36975-en`. La ficha muestra **29 de mayo de 2026** y el PDF © OCDE 2026. Ciclo 2025 y publicación 2026 son datos diferentes y compatibles. |
| [OCDE, resultados PISA 2025, volumen I](https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en.html) | La ficha muestra subtítulo *Future-Ready Students*, 377 páginas, DOI `10.1787/73451bc5-en`, **8 de septiembre de 2026**. Al corte sí figura publicado. No se debe deducir su indisponibilidad a partir del calendario de ciclos anteriores. |
| [UNESCO, documento ARK 380257](https://unesdoc.unesco.org/ark:/48223/pf0000380257) | El archivo de 77 páginas es el **resumen ejecutivo de 2021** de *Los aprendizajes fundamentales en América Latina y el Caribe*, evaluación de logros ERCE 2019. La portada y página legal lo identifican. La denominación anterior «informe regional» no precisaba su naturaleza. El identificador local legado se conserva por compatibilidad; no acredita un marco técnico completo. |
| [UNESCO, página del ciclo ERCE 2019](https://www.unesco.org/es/articles/estudio-regional-comparativo-y-explicativo-erce-2019) | La fecha 9 de marzo de 2023 corresponde a la página web; no es la fecha del resumen ejecutivo ni el año de evaluación. Mantener estos campos separados. |
| [IEA, marco TIMSS 2027](https://www.iea.nl/publications/assessment-framework/timss-2027-assessment-frameworks) | *TIMSS 2027 Assessment Frameworks*, DOI `10.6017/lse.tpisc.timss.vp1245`, 101 páginas, © IEA **2025**. [El anuncio](https://www.iea.nl/news-events/news/timss-2027-assessment-frameworks-released) está fechado **9 de septiembre de 2025**. Se corrigió el catálogo: año bibliográfico 2025; fecha exacta del libro sin confirmar; fecha del anuncio en campo propio. |
| [UNESCO, anuncio ERCE 2025](https://www.unesco.org/en/articles/unesco-and-countries-latin-america-and-caribbean-prepare-present-results-erce-2025-regions-leading) | Los primeros resultados se anuncian para diciembre de 2026. No autoriza puntajes publicados ni trasladar automáticamente la taxonomía 2019 al nuevo ciclo. |
| [Centro internacional, calendario TIMSS 2027](https://timss.bc.edu/timss2027/) | Marco disponible, estudio principal en 2027 y resultados previstos para diciembre de 2028. Su uso en diseño es prospectivo. |

Los documentos fuente del catálogo operativo son el [PDF OCDE final](https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/05/pisa-2025-assessment-and-analytical-framework_3abce6d6/86c36975-en.pdf), el [PDF UNESCO del resumen ejecutivo](https://unesdoc.unesco.org/in/rest/annotationSVC/DownloadWatermarkedAttachment/attach_import_467d448e-d64b-4f4d-b86f-f65db90b6b9b?_=380257spa.pdf) y la [copia del original IEA en ERIC](https://files.eric.ed.gov/fulltext/ED676227.pdf). IEA enlaza asimismo el [PDF en su centro internacional](https://timss2027.org/frameworks/downloads/T27_Assessment-Frameworks.pdf); el artefacto ingerido y validado en esta ejecución es la copia ERIC, sin suponer igualdad de bytes entre alojamientos.

## Páginas comprobadas para el contrato

**Página PDF** cuenta desde 1 e incluye portada. En PISA y el resumen ERCE coincide aquí con el folio impreso; en TIMSS 2027 el folio impreso es dos menos.

| Fuente | Página PDF | Folio impreso | Evidencia localizada |
| --- | ---: | ---: | --- |
| PISA 2025 final | 24 | 24 | Recuadro 2.2, tipos de conocimiento |
| PISA 2025 final | 32–33 | 32–33 | Componentes y contextos; tablas 2.1 y 2.2 |
| PISA 2025 final | **34** | 34 | Recuadros 2.3 y 2.4: primeras dos competencias; comprobación visual |
| PISA 2025 final | **36** | 36 | Recuadro 2.5: tercera competencia |
| PISA 2025 final | 38 | 38 | Recuadro 2.6, sistemas de contenido |
| PISA 2025 final | 49–50 | 49–50 | Figura 2.2 y descriptores de demanda |
| PISA 2025 final | 53 | 53 | Tablas 2.3 y 2.4, rangos de puntos por conocimiento y competencia |
| ERCE 2019, resumen ejecutivo 2021 | **19** | 19 | Cinco dominios, tres familias de procesos y ciencias de sexto; comprobación visual |
| ERCE 2019, resumen ejecutivo 2021 | 20 | 20 | Promedios de ciencias y exclusión de comparaciones TERCE para países no participantes |
| TIMSS 2027 | 25 | 23 | Tabla 2.1, contenidos por grado y subescala ambiental |
| TIMSS 2027 | 26 | 24 | Tabla 2.2, distribución cognitiva por grado |
| TIMSS 2027 | **27** | 25 | Cinco prácticas integradas; comprobación visual |
| TIMSS 2027 | **49–50** | 47–48 | Descriptores de las tres familias cognitivas de ciencias |

La segunda competencia PISA comienza en PDF 34 y continúa su discusión en PDF 35. Se usa 34 como página de su definición. En TIMSS las prácticas se integran con contenido y procesos; la lista de PDF 27 no prescribe una secuencia lineal de enseñanza.

## Catálogo operativo y límites de la evidencia

`config/dimensiones_evaluativas_2026.yaml` contiene **22 dimensiones de muestra**, con identificadores `LOCAL:`, etiquetas españolas parafraseadas, fuente, eje, página, ancla literal breve y alcance. Distribución: 12 PISA, 4 ERCE y 6 TIMSS. Incluye los cinco ejes locales requeridos; no pretende completar todas las categorías de cada marco.

Se verificó para cada entrada que el ancla existe en la página indicada de la extracción local, normalizando únicamente espacios y saltos de línea, sin aproximar palabras. Todas tienen entre 12 y 280 caracteres y como máximo 20 palabras. Se usan fragmentos descriptivos breves, no definiciones completas. También se comprobaron los SHA-256 de los tres PDF y de sus tres archivos de páginas contra `data/referencias_2026/manifest.json`. Las fuentes tienen 214, 77 y 101 páginas respectivamente. El manifiesto conserva el extractor y permite repetir la verificación sobre el artefacto concreto.

Estas garantías tienen alcance documental: una coincidencia del ancla prueba ubicación, **no que una propuesta cubra esa dimensión**. Las etiquetas, la selección de muestra y el nombre de los ejes son decisiones del proyecto. En ERCE y TIMSS el eje local `demanda` conserva familias de procesos de la fuente; no las equipara con niveles de demanda PISA. No se inventó para esos documentos una clasificación de conocimiento idéntica a PISA ni un catálogo de contextos que no se comprobó.

El resumen ERCE permite esas categorías generales y resultados, pero no una alineación granular exhaustiva. PISA se orienta a una cohorte nominal de 15 años, mientras ERCE ciencias se refiere a sexto y TIMSS a cuarto y octavo; ninguna página demuestra equivalencia automática con un grado salvadoreño. Los porcentajes de puntos de prueba tampoco establecen horas de clase.

La revisión granular de esta auditoría se limita a los tres documentos indicados y a las tablas TIMSS corregidas. Los demás recursos de países, pedagogía y contexto nacional del memorando conservan el alcance y las reservas de su consulta inicial; no se les extiende una certificación de páginas o vigencia curricular desde esta revisión. Siguen pendientes la verificación normativa completa de cada programa extranjero, sus modalidades, traducciones y correspondencia con la V4. Los resultados nacionales justifican estudiar sistemas comparadores, pero no prueban que una práctica específica haya causado sus puntajes.
