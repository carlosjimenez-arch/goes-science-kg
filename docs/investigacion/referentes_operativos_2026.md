# Referentes operativos internacionales para analizar tareas

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Consulta y verificación: **21 de octubre de 2026**. Este trabajo incorpora una fuente técnica real de ERCE y
un catálogo de **29 paráfrasis locales**, con identidad documental, páginas, anclas y conteos explícitos.
La presencia del ancla demuestra localización documental; **no demuestra alineación de una tarea**.

## Fuentes verificadas e ingesta

| ID del registro | Obra y edición | Identidad local |
| --- | --- | --- |
| `pisa_2025_marco_final` | [PISA 2025 Assessment and Analytical Framework](https://www.oecd.org/en/publications/pisa-2025-assessment-and-analytical-framework_86c36975-en.html), OECD, edición final publicada en 2026 | 214 páginas; SHA `5b50212929d3fe97c7226e9180a7349a3b619d416e3a5424c327a59e2d33898f` |
| `erce_2019_reporte_tecnico_2025` | [Reporte técnico: Estudio Regional Comparativo y Explicativo (ERCE 2019)](https://unesdoc.unesco.org/ark:/48223/pf0000394282), UNESCO, 2025 | 297 páginas; 2.246.111 bytes; SHA `def86f829083cdfa94437eb0fb65334a3526b3467ef66778ff0e0c329d117892` |

La edición de ERCE se confirmó visualmente en PDF 2: copyright y publicación UNESCO **2025**, con licencia
CC BY-SA 3.0 IGO. La [ficha de publicación UNESCO](https://www.unesco.org/es/articles/estudio-regional-comparativo-y-explicativo-erce-2019-reporte-tecnico)
fecha su anuncio el 30 de junio de 2025. Esa fecha de página no se presenta como día editorial del PDF.

Los bytes se descargaron de la [copia pública de MINEDUC Guatemala](https://edu.mineduc.gob.gt/digeduca/documents/erce/2023/Reporte-tecnico-ERCE19.pdf).
La ruta contiene `2023`, pero el año de la obra es 2025. Se conservan por separado la ficha bibliográfica
UNESCO, el alojamiento ministerial y la URL final de los bytes. No se ha comprobado igualdad binaria con
una descarga de UNESDOC: el acceso directo a su ficha devolvió HTTP 403 durante esta comprobación.

Se añadió sólo esta identidad nueva a `config/referentes_2026.yaml` y el dominio ministerial explícito
`edu.mineduc.gob.gt` a los destinos permitidos. Se ejecutó `RepositorioReferencias.incorporar(...,
descargar=True)` del módulo existente `ingesta/referencias.py`. El manifiesto fija también la extracción
`pypdf/6.19.0;fonttools/4.67.0;paginas-jsonl/1`, SHA de páginas
`51e3b2c60477ea9786f35be438405fbe99d2ac32130129d178d3cc33f0f4494d`, y 297 páginas con texto.
No se enviaron mallas V4, datos del proyecto ni credenciales a ningún modelo o servicio remoto.

El resumen ejecutivo de 77 páginas conserva su ID e identidad previos. **No se reclasificó como marco
técnico granular**, ni se lo usó como catálogo exhaustivo.

## Qué aporta realmente el reporte técnico ERCE

La sección de aprendizajes de ciencias en **PDF 11, folio impreso 15**, define cinco dominios y tres
familias de procesos. La definición se encuentra en una página de dos columnas y contiene una nota
conceptual importante sobre la diversidad de denominaciones de energía en los currículos regionales.
Se verificó la página completa visualmente, incluida esa nota.

En **PDF 18, folio 22**, la sección de la prueba de ciencias identifica sexto de primaria y remite al cruce de
dominios y procesos. La **tabla 2.9, PDF 19, folio 23**, presenta la distribución de preguntas de la prueba
con los cinco dominios y las tres familias. Es una tabla del diseño que se reporta, distinta de las propuestas
provisionales del análisis curricular de 2020.

Transcripción numérica comprobada visualmente de la tabla 2.9, en porcentaje de preguntas:

| Dominio descrito por la fuente | Reconocer | Analizar y aplicar | Producir, transferir y evaluar | Total |
| --- | ---: | ---: | ---: | ---: |
| Cuerpo humano y salud | 8 | 10 | 9 | 27 |
| Ciencia, tecnología y sociedad | 3 | 6 | 5 | 14 |
| La Tierra y el sistema solar | 4 | 9 | 2 | 15 |
| Energía y materia | 4 | 11 | 3 | 18 |
| Seres vivos, ecología y medioambiente | 6 | 14 | 6 | 26 |
| Total | 25 | 50 | 25 | 100 |

Son distribuciones de una **prueba de ciencias de sexto de 2019**: no se convierten en ponderaciones para
puntuar alineación, tiempo de clase, dificultad de tareas ni parámetros del ciclo ERCE 2025.

El reporte explica que del cruce de dominios y procesos se desprenden indicadores para construir preguntas,
pero estas páginas **no enumeran una matriz completa de indicadores de ciencias**. Los ocho referentes
operativos representan cinco dominios y tres procesos; no se presentan como los indicadores faltantes.
Los identificadores de ítems que aparecen en anexos psicométricos tampoco sustituyen una descripción
curricular de cada indicador. La afirmación de cobertura de todos los indicadores quedaría injustificada.

Se localizó además el [análisis curricular regional de 2020 en UNESDOC](https://unesdoc.unesco.org/ark:/48223/pf0000373982).
Su anexo 4 avisa que sus tablas son propuestas y pueden cambiar tras el pilotaje y ensamblaje. No se ingirió
como marco final alternativo ni se copiaron sus ponderaciones al catálogo operativo.

## PISA final: unidad de cobertura y conteos

Se usaron los bytes finales ya ingeridos, no el borrador anterior ni etiquetas presentes en la V4.
Se verificaron visualmente PDF 24, 34 y 36 completos y se contrastaron sus anclas con el texto extraído
de esos mismos bytes. En estas páginas el folio impreso coincide con la numeración PDF.

| Unidad explícita | Localizador | Esperados contados | Referentes incluidos | Alcance de la cobertura |
| --- | --- | ---: | ---: | --- |
| Competencias centrales de ciencias | Recuadros 2.3, 2.4 y 2.5, PDF 34 y 36 | 3 | 3 | Las tres competencias de esos recuadros |
| Desempeños de explicar fenómenos | Recuadro 2.3, PDF 34 | 6 | 6 | Una viñeta por referente hijo |
| Desempeños de diseño e interpretación | Recuadro 2.4, PDF 34 | 4 | 4 | Una viñeta por referente hijo |
| Desempeños de información y decisiones | Recuadro 2.5, PDF 36 | 5 | 5 | Una viñeta por referente hijo |
| Tipos de conocimiento científico | Recuadro 2.2, PDF 24 | 3 | 3 | Definiciones de contenido, procedimental y epistémico |
| Dominios de ciencias ERCE | PDF 11 y comprobación de tabla en PDF 19 | 5 | 5 | Dominios descritos; no todos sus indicadores |
| Procesos de ciencias ERCE | PDF 11 y comprobación de tabla en PDF 19 | 3 | 3 | Familias de procesos; no escala de dificultad |

Total PISA: **21**. Total ERCE: **8**. Total del catálogo: **29**. La cobertura completa se limita a cada
unidad contada: **no se declara exhaustividad de los marcos**.
Los conteos esperados proceden de la inspección de esas unidades; el validador comprueba su coherencia
con el catálogo, no deduce por sí mismo todas las unidades posibles leyendo el PDF.

La palabra `subcompetencia` es una categoría del proyecto para cada viñeta de desempeño de los recuadros.
No implica que OECD le asigne ese nombre o un código. Todos los IDs comienzan por `LOCAL:` y las descripciones
son paráfrasis españolas del proyecto, con anclas breves en la lengua del PDF para poder auditarlas.

Quedan fuera, entre otros, los ejemplos temáticos del recuadro 2.6, los descriptores detallados de saber
procedimental y epistémico de los recuadros 2.7 y 2.8, las dimensiones de identidad científica y las
competencias ambientales específicas. Tampoco se ingirió en esta tanda un catálogo operativo TIMSS.
El conocimiento de contenido no se reduce a un listado de temas; el procedimental y el epistémico no se
tratan como categorías mutuamente excluyentes de una tarea. Una misma actuación puede necesitar varios.

PISA se referencia a población nominal de **15 años**; no se deriva de ello un grado salvadoreño. ERCE
ciencias se referencia a **sexto de primaria**, sin una edad fija deducida. Una adaptación a estudiantes
menores exige establecer prerrequisitos y apoyos; no basta cambiar el campo de grado del referente.

## Contrato implementado y uso

`config/referentes_operativos_2026.yaml` contiene las paráfrasis, sus siete declaraciones de cobertura y
los límites. `ingesta/referentes_operativos.py` incorpora un esquema independiente del catálogo de 22
dimensiones y de los conjuntos congelados de evaluación. No cambia el grafo ni acredita una alineación.

Cada `ReferenteOperativo` guarda ID local, marco, ciclo, versión documental, fuente, SHA del PDF, páginas
desde 1, ancla, descripción, eje, tipo, padre, alcance y población de referencia por edad o grado cuando
corresponde. El esquema rechaza jerarquías entre marcos, ciclos, fuentes o poblaciones diferentes,
padres inexistentes, ciclos, IDs duplicados, doble conteo, falsos conteos completos y páginas ambiguas.

```python
from pathlib import Path

from goes_science_kg.ingesta.referencias import RepositorioReferencias
from goes_science_kg.ingesta.referentes_operativos import (
    cargar_referentes,
    evidencias_referentes,
)

repositorio = RepositorioReferencias(Path("data/referencias_2026"))
catalogo = cargar_referentes(Path("config/referentes_operativos_2026.yaml"), repositorio)
referente = catalogo.por_id["LOCAL:pisa2025_inv_valorar_diseno"]
evidencias = evidencias_referentes(catalogo, repositorio)[referente.id]
```

La carga verifica SHA, versión y existencia de las páginas. La búsqueda del ancla sólo normaliza Unicode
NFKC y espacios: conserva letras, cifras y signos. Las evidencias se hidratan nuevamente desde los bytes
PDF comprobados y se cachean por página durante esa validación. Las páginas auxiliares de ERCE 19
conservan su evidencia incluso cuando el ancla definitoria está en PDF 11. El manifiesto debe permanecer
estable durante la operación. No hay llamadas de red ni modelos en estas funciones.

El informe reproducible queda en `data/referencias_2026/referentes_operativos_validacion.json`. La huella del
catálogo validado en esta entrega es
`63478acbb32f738e477820a6edcdcee3b40bbca0cfcbaee4dd0b5747e743ada5`.
Su estado es `procedencia_y_anclas_verificadas`; la etiqueta deliberadamente no dice «alineado».

Para juzgar alineación hacen falta la consigna completa, la actuación que se espera del estudiante, los datos
o materiales y los criterios con los que se evalúa su respuesta. Cubrir un tema, citar una página o reconocer
un nombre de competencia no basta. Cuando falta esa información corresponde abstenerse de acreditar el
desempeño. El catálogo provee criterio y evidencia documental, no ese juicio por adelantado.

## Calidad de extracción y verificación

El nuevo PDF ERCE se renderiza correctamente. Su extracción con el extractor fijado presenta, sin embargo,
algunos nombres de glifos en vez de caracteres normales: por ejemplo, `/f_i` y `/two.oldstyle` dentro de
palabras o números. El texto raw se conserva tal cual para no introducir una transcripción silenciosa.
Las anclas elegidas no contienen esas secuencias y se verificaron también visualmente. **Ancla válida no
significa extracción íntegramente limpia**. En particular, para los números de tabla y la edición de ERCE se
usó la inspección visual, no una conversión automática de esos nombres de glifo.

Se comparó localmente con **PDFplumber 0.11.10**, sin modificar objetos ni manifiesto:

| Página PDF | Pypdf: secuencias de nombres de glifo detectadas | PDFplumber: secuencias detectadas | Resultado observado |
| --- | ---: | ---: | --- |
| 11 | 46 | 0 | PDFplumber recupera palabras como «científico» y cifras como 2020, pero intercala las dos columnas con la configuración predeterminada |
| 19 | 17 | 0 | PDFplumber recupera «Tabla 2.9», los nombres y porcentajes en la tabla; las secciones inferiores siguen requiriendo control de orden |

Los conteos usan un detector explícito de nombres de glifo y no representan una tasa de error de OCR ni
una medición completa de fidelidad. Ambos extractores produjeron cero controles no espaciales en estas
dos páginas. La comparación completa con hashes del texto está en `/tmp/erce_comparacion_extractores.json`;
los textos de control están en `/tmp/erce_tecnico_pdf11_pypdf.txt`, `/tmp/erce_tecnico_pdf11_pdfplumber.txt`
y los equivalentes para PDF 19. No se presenta la ausencia de marcadores como garantía de lectura correcta.

Se concretó una extracción adicional versionada en
`config/extraccion_referencias_2026.yaml`. Sus dos perfiles están vinculados a la fuente, SHA del PDF,
página y versión `1`. `ingesta/extraccion.py` registra la versión real de PDFplumber, el perfil y la
huella del ejecutor; verifica los bytes originales incluso al reutilizar una página en caché.
No cambia los 29 referentes ni la extracción original de Pypdf. Usa `pdfplumber`, recorte por región y
`extract_text(layout=True)`.

### Regiones auditadas de la extracción adicional

Dimensiones medidas en ambas páginas: **595,276 × 841,89 puntos PDF**. Las cajas usan
`[x0, top, x1, bottom]` con origen superior izquierdo, en puntos, no en píxeles. Son cajas específicas de
este SHA y estas páginas, no una heurística aplicable a cualquier documento.

| Perfil y orden | Región | Caja en puntos | Comprobación visual |
| --- | --- | --- | --- |
| `LOCAL:erce2019_pdf11_columnas_v1`, 1 | Cuerpo, columna izquierda | `[54, 75, 305, 655]` | Incluye título, introducción y cuatro primeros dominios hasta la continuación de energía |
| Mismo perfil, 2 | Cuerpo, columna derecha | `[313, 75, 565, 655]` | Continúa energía, incluye seres vivos y los tres procesos completos |
| Mismo perfil, 3 | Nota, columna izquierda | `[54, 669, 305, 795]` | Incluye la llamada de nota y su primera parte, sin capturar el cuerpo |
| Mismo perfil, 4 | Nota, columna derecha | `[313, 669, 565, 795]` | Continúa y termina la nota, sin cortar la última línea |
| `LOCAL:erce2019_pdf19_tabla_2_9_v1`, 1 | Tabla 2.9 y fuente | `[54, 75, 565, 308]` | Incluye título, encabezados, cinco filas, totales y fuente; excluye las tablas de escritura inferiores |

Se renderizaron e inspeccionaron **los cinco recortes**, no sólo el texto. No hay palabras ni filas
cortadas por sus límites. La secuencia de cuerpo izquierda/derecha conserva el párrafo de energía
que cruza de columna; ambas regiones de nota se conservan después como contexto separado mediante
sus IDs propios. Se excluyen deliberadamente cabecera de capítulo y número de folio, disponibles en la
página original y los metadatos. La viñeta de color puede extraerse como `z` y la llamada de nota como un
`1` pegado a la palabra anterior: son artefactos tipográficos residuales, no contenido científico nuevo.
Una comprobación geométrica adicional encontró **cero caracteres intersectados y cortados por los bordes**
de las cinco cajas. Las ocho anclas ERCE aparecen en el texto de las regiones con `layout=True`.

Con la lectura secuencial por regiones se resuelve la mezcla de columnas observada en la extracción
predeterminada de página completa. Los encabezados multilínea de la tabla todavía se linealizan en texto;
este perfil **no certifica una tabla semántica estructurada**, y no se utilizarán sus porcentajes para
inferir cobertura o puntuar alineaciones. Los referentes actuales dependen de definiciones de dominios
y procesos, con la tabla como contexto documental.

Estado de este entregable: **regiones auditadas visualmente, texto comprobado y ejecutor implementado**.
Los contratos rechazan regiones solapadas, cajas fuera de página y ediciones distintas. El workflow de
alineación utiliza el puerto `PaginasConPerfil`; las páginas sin perfil conservan su extractor raw.
No se declara que todas las páginas del documento estén limpias. Los dos perfiles son una extracción
adicional identificada, sin migrar ni sobrescribir el raw.
Huella del archivo de perfiles auditado:
`3347b0a5dfdd2716d909cef93e1079450e19f784dc45b6995a04cfaaa139728e`.

Los cinco PNG y textos están en `/tmp/erce_regiones_auditadas/`: `pdf11_cuerpo_izquierda.png`,
`pdf11_cuerpo_derecha.png`, `pdf11_nota_izquierda.png`, `pdf11_nota_derecha.png` y `pdf19_tabla_2_9.png`.
`auditoria.json` conserva dimensiones, cajas y huellas de las variantes de texto con y sin `layout=True`.

La implementación conserva raw, versión, configuración y hashes previos y nuevos, sin sobrescribir
el manifiesto actual. No corresponde sustituir texto corrupto por una transcripción
generada por IA. Hasta contar con extracción suficiente, los consumidores deben conservar la advertencia
y abstenerse si el pasaje necesario no es legible o su orden impide juzgar. No se atribuyen al texto defectos
que sólo pertenecen a la extracción.

Comprobaciones ejecutadas: **57 tests** de referentes, ingesta y casos adversariales, sin red; Ruff de los
archivos nuevos; validación completa de los 29 referentes contra los dos documentos reales. Los tests
verifican rechazos por edición, SHA, citas, páginas, población y jerarquía incorrectos. No evalúan psicometría,
eficacia de aprendizaje ni la fidelidad semántica de todas las paráfrasis mediante un estudio externo.

Renderizados de inspección conservados en `/tmp`: `erce_tecnico_pdf02.png`, `erce_tecnico_pdf11.png`,
`erce_tecnico_pdf19.png`, `pisa_final_pdf24.png`, `pisa_final_pdf34.png` y `pisa_final_pdf36.png`.
