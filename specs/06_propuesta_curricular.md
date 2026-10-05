# 06 · Propuesta curricular

Objetivo: para cada asignatura, una **malla propuesta** que El Salvador pueda adoptar, con
el menor cambio posible respecto de la malla actual y con cada cambio justificado.

## Entradas
1. Brechas de la asignatura (`asignaturas/<x>/brechas/`): objetivos no cubiertos o débiles,
   balance contra metas, nivel cognitivo, medio ambiente, investigación.
2. **Oportunidad**: grado de El Salvador menos la mediana de los países de referencia, por
   objetivo. Un valor positivo significa que El Salvador llega tarde. Se calcula con dos grupos:
   todos los países y solo los de alto desempeño.
3. **Prerrequisitos** (DAG de conceptos): ningún tema puede quedar antes que sus prerrequisitos.
4. **Presupuesto**: mismo total de temas por ciclo. Las fusiones liberan lo que usan las
   inserciones (reglas en `reportes/cobertura_curricular/CLAUDE.md`). Sesiones de 55 minutos.

## Acciones posibles (arista REEMPLAZA)
| Acción | Cuándo | Evidencia mínima |
|---|---|---|
| `mantener` | El tema cubre un objetivo y está en un grado razonable | — |
| `mover` | Oportunidad ≥ +1 con alto desempeño y prerrequisitos disponibles antes | primer grado en ≥2 países + DAG |
| `nuevo` | Objetivo del pivote sin cobertura en el ciclo | objetivo + ≥1 país que lo enseña (con página) |
| `fusionar` | Dos o más temas cubren el mismo objetivo con profundidad «sólida» (4+) y hace falta presupuesto | lista de temas fusionados |
| `dividir` | Un tema cubre dos objetivos de dominios distintos | — |
| `quitar` | Tema FUERA de todo marco **y** sin presencia en los países de referencia | se requiere revisión humana obligatoria |

## Salidas por asignatura (`asignaturas/<x>/propuesta/`)
- `propuesta.json`: nodos PropuestaTema con acción, grado propuesto, objetivos, conceptos y evidencias.
- `Propuesta_<Asignatura>.xlsx`: malla propuesta con columnas compatibles con la malla del MINED
  (Unidad, Contenido, Procedimental, Indicador…) más «Acción», «Motivo» y «Evidencia».
  Estilo de los libros 2027: encabezado verde bosque (1E4D3A), sin azul y compatible con Numbers
  (ver `reportes/cobertura_curricular/CLAUDE.md`, «Convenciones»).
- `informe.md`: qué cambia, por qué, impacto en las métricas antes y después, y decisiones pendientes.

## Simulación (`gskg propuesta simular <asig> <g0> <g1>` → `simulacion_G..-G...json`)
Aplica la propuesta al grafo en memoria y compara antes y después: errores de secuencia en el ciclo (todos y de
confianza alta), conceptos que llegan 2 o más grados tarde frente a la mediana de los países y desfase medio.
- `mover`, `fusionar`, `dividir`, `nuevo` y `revisar` cambian grados, temas y etiquetas.
- `quitar_conceptos` (opcional en cualquier acción) retira etiquetas que el tema reformulado deja de trabajar.
- Las `quitar_conceptos` de las **otras asignaturas del mismo ciclo** también se aplican (campo
  `quitas_de_otras_asignaturas`): por ejemplo, Biología 10.° deja de tratar «Química de los carbohidratos», lo que
  resuelve una secuencia de Química. El resto de las acciones de otras asignaturas no se aplica.
- `secuencia_alta_pendiente` lista lo que queda por resolver; el informe lo trata como decisiones abiertas.

## Restricciones
- No se proponen contenidos que no estén en algún marco **ni** en algún país de referencia.
- Cada propuesta lleva `estado: borrador` hasta que el MINED la revise (`revisado_por`).
- La propuesta se recalcula sola si cambian el grafo o las decisiones humanas.
