# 02 · Modelo del grafo

Versión ejecutable: `src/goes_science_kg/modelos.py`. Si cambia uno, cambia el otro.

## Nodos
| Tipo | Id | Qué es | Evidencia obligatoria |
|---|---|---|---|
| `Asignatura` | `ASIG:biologia` | Una de las 4 disciplinas | — |
| `Grado` | `GRADO:07` | Grado de El Salvador (2–11) | — |
| `Documento` | `DOC:timss27`, `DOC:MALLA:<archivo>` | Fuente (manifiesto o malla) | url/archivo + sha256 |
| `Marco` | `MARCO:T8_27` | Evaluación internacional | — |
| `ObjetivoMarco` | `OBJ:T8_27-B1.2`, `OBJ:PISA-V3`, `OBJ:TA-M1.1`, `OBJ:ACSCH127` | Objetivo del pivote | documento + página (o `localizador` = código oficial si el documento es HTML) |
| `Pais` | `PAIS:UY` | País de referencia | — |
| `ObjetivoPais` | `OP:UY-BIO-G3-01` | Objetivo de aprendizaje de un país | documento + página |
| `Tema` | `TEMA:G07-CIE-U2-2.3` | Tema procedimental de la malla de El Salvador | archivo + hoja + fila |
| `Concepto` *(fase 3)* | `CON:biologia/fotosintesis` | Idea científica enseñable | ≥1 arista TRABAJA con evidencia |
| `Practica` *(fase 3)* | `PRAC:controlar-variables` | Práctica científica (TIMSS Investigations, PISA, NGSS) | documento + página |
| `PropuestaTema` *(fase 5)* | `PROP:biologia-G05-001` | Tema propuesto para la nueva malla | aristas PROPONE con evidencia |

**Id de tema:** `G{grado}-{CIE|FIS|QUI|BIO}-U{unidad}-{código del procedimental}`. Si el código
se repite, se agrega `-f{fila}`. No depende del orden de lectura. La llave de unión con las
clasificaciones previas es `(archivo canónico, hoja, fila)`.

## Aristas
| Tipo | De → A | Atributos | Método |
|---|---|---|---|
| `EN_GRADO` | Tema → Grado | — | malla |
| `DE_ASIGNATURA` | Tema / ObjetivoMarco / ObjetivoPais → Asignatura | `via` (malla, timss, pisa, alineación) | malla / regla |
| `EN_MARCO` | ObjetivoMarco → Marco | — | catálogo |
| `DE_PAIS` | ObjetivoPais → Pais | — | catálogo |
| `FUENTE` | * → Documento | `pagina` o `hoja`/`fila` | catálogo / malla |
| `CUBRE` | Tema → ObjetivoMarco | `rol` (principal, secundario, elemento), confianza, justificación, versión | ia |
| `ALINEA_CON` | ObjetivoPais → ObjetivoMarco | `rol`, confianza, justificación, versión | ia |
| `EQUIVALE_A` | Objetivo TIMSS 2023 → TIMSS 2027 | `tipo` (igual, dividido, fusionado) | catálogo |
| `TRABAJA` *(f3)* | Tema / ObjetivoPais / ObjetivoMarco → Concepto / Practica | confianza, justificación, versión | ia |
| `PRERREQUISITO_DE` *(f3)* | Concepto → Concepto | confianza, `evidencias` (lista de documentos y páginas o de órdenes observados) | ia / regla |
| `PROPONE` *(f5)* | PropuestaTema → ObjetivoMarco / Concepto | justificación, evidencias | ia + revisión |
| `REEMPLAZA` *(f5)* | PropuestaTema → Tema | `accion` (mantener, mover, fusionar, dividir, nuevo, quitar) | ia + revisión |

## Reglas
1. Un tema tiene **un** objetivo principal y como máximo uno secundario por marco. Si no tiene
   contenido del marco, no lleva arista CUBRE y el nodo guarda `estado_timss = FUERA`.
2. Los elementos procedimentales y epistémicos de PISA se registran con `rol = elemento`.
3. `PRERREQUISITO_DE` debe formar un **DAG** dentro de cada asignatura (sin ciclos). La validación lo exige.
4. Un concepto se crea solo si al menos dos fuentes lo trabajan, o si lo trabaja una fuente y un marco.
   Así se evita la granularidad arbitraria.
5. Los nodos nunca se borran entre versiones. Se marcan con `props.obsoleto = <versión>`.

## Almacenamiento
`data/grafo/{nodos,aristas}.jsonl` + `manifest.json` (versión, conteos y sha256).
Exportar: `gskg grafo exportar` (GraphML). Para Neo4j, agregar `exportar --formato neo4j`
(CSV de nodos y relaciones) en la fase 2 si hace falta.

## Estado v0 (lo que ya existe)
2.326 nodos y 9.350 aristas: 1.260 temas, 493 objetivos de marco (incluidos los 263 de ACARA Senior
Secondary), 506 objetivos de países y 2.027 aristas CUBRE. Hay 49 temas sin asignatura y 338 aristas de
confianza baja.
Ver `data/grafo/manifest.json`.
