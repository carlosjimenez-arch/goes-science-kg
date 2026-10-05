# 09 · Grafos por grado

El pedido del MINED es un grafo **por grado**: lo que vive un estudiante de El Salvador en un año escolar,
conectado con lo que trae de años anteriores y con lo que se espera en los marcos y en otros países.

## Qué contiene el grafo del grado g (`gskg grados construir`)
| Capa | Nodos | Cómo entra |
|---|---|---|
| Núcleo | Temas de g (las 4 asignaturas) | `Tema.grado == g` |
| Conceptos y prácticas | Conceptos y prácticas que esos temas trabajan | aristas `TRABAJA` |
| Marcos | Objetivos de TIMSS, PISA, TIMSS Advanced o ACARA que esos temas cubren | aristas `CUBRE` |
| Anclajes | Prerrequisitos **directos** de los conceptos de g | aristas `PRERREQUISITO_DE` (pueden ser de otros grados u otras asignaturas) |
| Referentes | Objetivos de países cuyo grado equivalente (o banda) incluye g y que comparten un objetivo de marco con los temas de g | `ALINEA_CON` |

Salida por grado: `data/grafo/grados/G<gg>/{nodos,aristas}.jsonl` + `manifest.json` + `diagnostico.json`,
y la ficha legible en `grados/G<gg>/ficha.md`. El índice está en `grados/README.md`.

## Diagnóstico didáctico de cada grado
1. **Conceptos nuevos y retomados.** Un concepto es *nuevo* en g si es el primer grado en que la malla lo trabaja.
   Muchos retomados sin profundización indican una espiral plana. Muchos nuevos indican un grado sobrecargado.
2. **Prerrequisitos que no llegan a tiempo.** Para cada concepto de g y cada uno de sus prerrequisitos directos:
   - `previo`: la malla lo trabaja antes de g (✓);
   - `mismo_grado`: hay que cuidar el orden de las unidades dentro del año;
   - `posterior`: la malla lo trabaja **después** de g (error de secuencia);
   - `ausente`: la malla **nunca** lo trabaja (vacío).
   Los dos últimos son los hallazgos accionables para la propuesta curricular (spec 06).
3. **Faltantes por edad.** Conceptos que la mediana de al menos dos países de referencia trabaja en g o antes,
   y que El Salvador todavía no trabaja. El primer grado de cada país se calcula con el **etiquetado directo** de sus
   objetivos (objetivo de país → `TRABAJA` → concepto). La vía del pivote (→ `ALINEA_CON` → objetivo de marco →
   `TRABAJA` → concepto) queda solo como respaldo si un país no tiene etiquetado directo.

## Limitaciones conocidas
- Países en el grafo: Uruguay, Colombia, Singapur (primaria), Inglaterra, Australia y Japón. Los de alto desempeño
  (top 10 de TIMSS 2023 Ciencias) son Singapur, Inglaterra, Australia y Japón.
- Los objetivos por **banda** (KS3 de Inglaterra = 5.°–7.°, KS4 = 8.°–9.°; Estándares de Colombia por grupos de grados) cuentan
  en el punto medio de la banda.
- La equivalencia de grados entre países se hace por **edad de ingreso** (`config/referentes.yaml`).
- Uruguay y Singapur empiezan en 3.° y Colombia en 1.°. Los grados 1 se cuentan como 2 (ver
  `reportes/cobertura_curricular/outputs/informe_paises_timss2027.md` §5).
- Los prerrequisitos son propuestas de IA con evidencia y confianza. Las aristas de confianza baja deben pasar
  por revisión humana antes de usarse para mover temas.
