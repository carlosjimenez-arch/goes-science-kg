# 12 · Grafos internacionales de 2.° a 8.° y contraste con la malla Versión 2

> Siguiente etapa lógica después de la spec 11 (9.°–11.°). Queda **lista para ejecutar**: el código ya trabaja por
> tramo de grados, el catálogo de fuentes está en `config/internacional_2_8.yaml` y el costo está estimado. Correrla
> cuesta llamadas a Vertex, así que espera la aprobación del responsable del proyecto.

## Qué cambia frente a la spec 11
El método es el mismo: extraer y validar con dos modelos distintos, etiquetar con el catálogo congelado, construir el
grafo y el consenso, contrastar con la V2 y revisar a mano una muestra. Cambia lo siguiente:

| | 9.°–11.° (spec 11) | 2.°–8.° (esta spec) |
|---|---|---|
| Niveles | núcleo y especialización (electivas) | **solo núcleo**: todo es obligatorio |
| Antes del tramo | secundaria baja como antecedente | no hay: el tramo empieza en 2.° |
| Clases posibles | faltante, no retomado, tardío, especialización, adelantado, sin referente, alineado, retomado, previo | faltante, **tardío** (también si la V2 lo enseña después de 8.°), **posterior**, adelantado, sin referente, alineado |
| Malla V2 | 9.° Ciencias y 10.°–11.° por asignatura | 2.°–8.° Ciencias (integrada); su etiquetado ya existe (`malla_v2_g02_08`) |
| Salidas | `data/grafo/internacional/`, `internacional/` | `data/grafo/internacional_2_8/`, `internacional/2_8/` |

Aquí el momento sí se puede juzgar: los datos de los países cubren todo el tramo, así que «adelantado» y «tardío» son
los hallazgos centrales. «posterior» marca lo que la V2 deja para 9.°–11.° y que el núcleo internacional tampoco exige
antes de 9.°; no es un problema, solo ubica el concepto.

## Equivalencia de grados (por edad de ingreso; SV 1.° ≈ 7 años)
| País | SV 2.° | SV 5.° | SV 8.° | Fuente en el catálogo |
|---|---|---|---|---|
| Singapur | (sin ciencias hasta P3) | P5 | Sec 2 | Primary Science P3–P6 (2023), Lower Secondary G2/G3 (2024) |
| Japón | 小3 | 小6 | 中3 | importado del grafo principal (jp-cos, 2017) |
| Corea | 초3 | 초6 | 중3 | 2022 개정: 초 3~4 (pp. 19–31), 초 5~6 (pp. 32–45), 중 1~3 (pp. 46–67) |
| Inglaterra | Year 4 | KS3 Year 7 | Year 10 | importado: KS1–2 y KS3; Year 10 desde GCSE Combined |
| Australia | Year 3 | Year 6 | Year 9 | importado: v9 F–10 |
| Taiwán | 三年級 (Ⅱ) | 六年級 (Ⅲ) | 國三 (Ⅳ) | 第二~第三學習階段 (pp. 15–25), 第四 (pp. 25–35) |
| Estonia | grado 2 | grado 5 | grado 8 | etapas I–II (pp. 8–11), III (pp. 12–28) |
| Ontario | Grade 3 | Grade 6 | Grade 9 | SNC1W (SV 8). **Pendiente:** Science and Technology 1–8 (2022) |
| Hong Kong | P3 | P6 | S3 | **Pendiente:** Primary Science (2025) y Science S1–3 |

Hasta descargar las fuentes pendientes, Hong Kong no tiene núcleo en 2.°–8.° y Ontario solo aporta 8.°: el denominador
del consenso es de 7 países en casi todos los grados. Se declara en el informe.

## Costo y reutilización
- **Sin costo:** AU, ENG (KS1–KS3) y JP se importan del grafo principal. KR 중학교, TW Ⅳ, EE etapa III, ON SNC1W y
  GCSE Combined son copias exactas de documentos ya extraídos en 9.°–11.° y salen de la caché.
- **Extracción nueva:** 116 llamadas como mínimo (estimación del 2026-10-09): SG 72, KR 28, TW 12 y EE 4. Se calcula
  con `gskg internacional --tramo 2_8 extraer`, que no gasta sin `--confirmar`.
- **Etiquetado:** se estima después de extraer (unas 75–90 llamadas, con lotes de 20 enunciados). También se detiene
  sin `--confirmar`.

## Cómo ejecutarla
```bash
uv run gskg internacional --tramo 2_8 extraer                 # muestra el costo; no gasta
uv run gskg internacional --tramo 2_8 extraer --confirmar     # tras la aprobación
uv run gskg internacional --tramo 2_8 etiquetar               # muestra el costo
uv run gskg internacional --tramo 2_8 etiquetar --confirmar
uv run gskg internacional --tramo 2_8 construir               # sin Vertex: grafo, consenso, informes, visor
uv run pytest -q                                              # incluye las divisiones de conceptos en los dos tramos
```
Después: muestrear unos 20 hallazgos contra las fuentes (subagente `verificador-hallazgos`), escribir
`internacional/2_8/README.md` con los hallazgos verificados y exportar las decisiones nuevas para el MINED.

## Riesgos y límites conocidos
- **Granularidad desigual:** SG separa Standard y Foundation (puede duplicar objetivos), AU v9 es grueso y ENG KS1–2
  agrupa años. El consenso cuenta presencia por país, no conteos.
- **Etapas de varios años:** EE, KR, TW y ENG KS1–2 dan rangos de grados; el grado de un objetivo es el punto medio.
- **Concepto dividido:** cualquier objetivo nuevo etiquetado con «Configuración electrónica» necesita asignación en
  `conceptos/divisiones.json`; la prueba de calidad lo exige.
- **Fuentes pendientes:** HK y ON 1–8 (skill `fuentes-descargar`); conviene descargarlas antes de correr, para no
  extraer dos veces.
