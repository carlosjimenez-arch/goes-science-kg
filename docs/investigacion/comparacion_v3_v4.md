# Comparación documental V3 → V4

Se compararon 935 registros del grafo V3 y 1020 filas V4.

Hay **506 coincidencias únicas de objetivo** y **0 grupos ambiguos**. Permanecen sin coincidencia exacta 429 registros V3 y 514 filas V4.

Estas cifras no cuentan conceptos eliminados, nuevos o fusionados. No se trasladan IDs ni decisiones.

## Criterio

La clave exige grado, asignatura declarada en la malla y objetivo. El objetivo solo normaliza NFKC y espacios: conserva puntuación, mayúsculas, numeración y negaciones. No se utiliza similitud aproximada.

La V3 almacena los nombres de malla como slugs de configuración. Se traduce únicamente la representación explícita ciencias→Ciencias, biologia→Biología, fisica→Física y quimica→Química. No se usa la disciplina inferida o revisada del nodo.

Hay 0 registros V3 y 0 filas V4 con el mismo literal en otro contexto. Quedan como referencias de revisión, sin confirmar traslado de grado o asignatura.

## Campos comparables

Cada valor comparado de V3 se localiza de nuevo por cabecera y fila en un archivo con SHA verificado. Un blanco arrastrado por el lector antiguo o una columna no identificable se declara no comparable. Las diferencias son textuales; no prueban mejora o pérdida pedagógica.

| Campo del grafo V3 | Campo V4 | Estados en parejas únicas |
|---|---|---|
| contenido | contenido | igual_normalizado: 502; no_comparable: 1; valor_distinto: 3 |
| subcontenido | subcontenido | antes_vacio_ahora_presente: 17; igual_normalizado: 479; no_comparable: 2; vacios_ambos: 1; valor_distinto: 7 |
| evidencia | evidencia_aprendizaje | antes_presente_ahora_vacio: 1; igual_normalizado: 504; valor_distinto: 1 |
| habilidad_timss | habilidad_timss | antes_presente_ahora_vacio: 1; igual_normalizado: 504; valor_distinto: 1 |
| competencia_pisa | competencia_pisa | antes_presente_ahora_vacio: 1; igual_normalizado: 505 |
| indicador | Indicadores de logro o Indicador avanzado, solo si se identifica | antes_presente_ahora_vacio: 1; igual_normalizado: 466; valor_distinto: 39 |

El indicador V3 combinaba Indicadores de logro con Indicador avanzado mediante fallback. Se compara únicamente con la columna cuyo valor original coincide de forma inequívoca. Si ambas columnas contienen el mismo texto, la procedencia semántica permanece ambigua.

## Información incorporada al contrato

`eje_integrador`, `numero_tema`, `numero_clase`, `actitudinal`, `conocimiento_pisa`, `contexto_pisa`, `habilidad_siglo_xxi`, `competencia_digital`, `actividad_digital`, `habilidad_transversal`, `competencia_men`, `dominio_clave`, `notacion`, `notas`, `origen_contenido`, `celdas`, `fases`.

Son campos sin contraparte almacenada comparable en el grafo V3. Pueden estar presentes en el Excel antiguo: incorporados al contrato no significa contenidos curriculares nuevos. Los dos indicadores se desagregan; las fases V4 conservan texto/códigos locales, mientras `micro_pisa` V3 preservaba listas parciales de códigos y no permite comparar el texto completo. La unidad se muestra como contexto, sin equiparar automáticamente sus formatos de nombre.

## Trazabilidad y límites

Huella curricular V4: `9f491de56b3ccb1f76dd9b0a216b2fe32564600dd9de30f5be7003a4b1f241c5`.

El JSON adjunto conserva todas las parejas, grupos ambiguos, valores comparados, localizadores y registros sin correspondencia. La procedencia del grafo incluye sus SHA. No se consultaron conjuntos de evaluación reservados ni servicios remotos.

- Una coincidencia de objetivo no demuestra identidad de toda la secuencia, profundidad o carga horaria.
- Sin coincidencia exacta no equivale a tema eliminado, concepto nuevo, fusión o traslado confirmado.
- Los campos sin contraparte se incorporan al contrato; pueden haber existido antes en los Excel.
- V3 colapsó los dos indicadores y perdió campos; no se atribuyen cambios a esa pérdida de representación.
- No se trasladan IDs, decisiones humanas, etiquetas, clasificaciones, alineaciones o aristas.
- La comparación usa el grafo histórico validado; no afirma que este capture toda la V3 original.

## Reproducción

```python
from pathlib import Path
from goes_science_kg.curriculo import cargar_curriculo
from goes_science_kg.curriculo.comparacion import comparar_curriculos, guardar_comparacion
from goes_science_kg.producto.referencias import cargar_referencias_historicas

comparacion = comparar_curriculos(cargar_referencias_historicas(Path("data/grafo")), cargar_curriculo())
guardar_comparacion(
    comparacion,
    salida_json=Path("docs/investigacion/comparacion_v3_v4.json"),
    salida_markdown=Path("docs/investigacion/comparacion_v3_v4.md"),
)
```
