# 15 · Entrega V3 del MINED y refuerzo de cada tema

Objetivo: tomar la entrega nueva del MINED (V3, 2026-10-13) y **reforzar cada tema con lo que el repo ya sabe**:
errores corregidos, recomendaciones del panel, hallazgos del contraste internacional y lo que la V3 dejó de cubrir.
El refuerzo se entrega en copias de las matrices del MINED con filas marcadas «Propuesta GOES», como el propio MINED
marca sus propuestas. Es una propuesta con evidencia, no una decisión: el MINED la adopta o no.

## Decisiones del responsable (2026-10-13)
1. **La V3 es la malla vigente.** `config/mallas.yaml` lee la V3; la V2 queda en `config/mallas_v2.yaml` como
   referencia, igual que la V1.
2. **Formato del refuerzo:** copias de las matrices del MINED (nunca los originales), con filas nuevas marcadas en la
   columna «Origen del contenido» como `Propuesta · GOES · <origen>`, en otro color, y una columna de refuerzo por
   tema con la evidencia, la solidez y la fuente. Más un resumen por grado.
3. **Qué se inyecta** (solo lo que tiene evidencia; nada se quita):
   - correcciones de los errores científicos de la malla que sigan en la V3;
   - recomendaciones del panel con solidez «sólido» o «respaldado» (lo frágil no se inyecta);
   - hallazgos del contraste internacional (tardío, adelantado, faltante, solo especialización → acotar);
   - lo que la V3 quitó y los países o los marcos enseñan en el núcleo (propuesta de recuperar).

## Qué trae la V3 (medido el 2026-10-13, `nuevas_mallas/`)
| | V2 | V3 |
|---|---|---|
| Temas | 1.307 | 935 |
| Idénticos a la V2 (mismo procedimental) | — | 819 |
| Parecidos (≥ 0,75 de similitud) | — | 21 |
| Nuevos | — | 95 |
| Temas de la V2 sin par en la V3 | — | 467 (384 en 10.°–11.°) |

- **2.°–9.°:** casi todo se conserva. Hay pocos temas nuevos (31) y algunos quitados (83). 9.° fusiona unidades
  (Genética y evolución; Salud humana; Biosfera y sostenibilidad).
- **10.°–11.°:** la V3 consolida en clases. Física pasa de 281 filas a 80; Química trae la columna «N° Clase» (72
  clases por grado). Un tema de la V2 «sin par» puede seguir dentro de los subcontenidos de una clase consolidada:
  **lo quitado se juzga por concepto, no por fila.**
- **Hoja nueva «Herramientas IA»** en Bachillerato (actividades con herramientas de IA). Queda fuera del alcance de
  ciencias y se enlaza con `goes-techonoly-kg`.

## Fases
### 15.0 · Ingesta de la V3
- El responsable copia los archivos a `data/fuentes/mined/Mallas sugeridas v3/`. La guarda impide que lo haga Claude.
- `config/mallas.yaml` apunta a la V3, con el nombre explícito de cada archivo. `config/mallas_v2.yaml` conserva la
  V2.
- **Correspondencia V2 → V3** (`data/interim/mallas/v2_a_v3.json`): cada tema de la V3 es `identico`, `parecido`
  (con su par y su similitud) o `nuevo`. Cada tema de la V2 sin par queda `sin_par`. Es determinista y tiene prueba.
- Pruebas: la V3 se lee completa por hoja, los ids son únicos y la correspondencia cubre los dos lados.

### 15.1 · Migración de las capas por la correspondencia
Todo lo que está atado a un id de tema de la V2 pasa al id de la V3 de su par idéntico:
- etiquetado de conceptos del grafo principal;
- revisiones de etiquetas y de coherencia;
- etiquetado `malla_v2` del contraste;
- capa pedagógica;
- decisiones y dictámenes del panel.

Lo de un par «parecido» se copia marcado para verificar. Lo de un tema «sin par» se conserva como histórico y no se
borra. El script valida que ninguna referencia quede apuntando a un id que no existe.

### 15.2 · Etiquetado de los temas nuevos y parecidos
- **Grafo principal:** subagentes `etiquetador-conceptos` sobre los 116 temas, sin costo de Vertex.
- **Contraste:** el etiquetado `malla_v2` se hace con Vertex. Primero se estima sin `--confirmar` y se pide la
  aprobación por número de llamadas, con margen.

### 15.3 · Recalcular sobre la V3
- Se reconstruyen el grafo, los grados, las fichas y el contraste de los dos tramos.
- Las clases que cambien se comparan con las de la V2. Las nuevas inciertas van al panel y al bucle, en una serie
  propia.

### 15.4 · Catálogo de refuerzos por tema (código, sin IA)
`data/interim/refuerzo_v3/candidatos.json`: por tema de la V3, cada candidato a refuerzo trae:
- `tipo`: corregir, precisar, adelantar, acotar, agregar microhabilidad o indicador, tema nuevo o recuperar;
- `origen`: error de la malla, panel, contraste o quitado en la V3;
- la evidencia (fuente primaria y cita literal cuando la hay) y la solidez del dictamen que lo respalda.

Reglas por fuente:
- **Errores:** se buscan en el texto de la V3. Si el MINED ya los corrigió, no se inyectan y se registra.
- **Panel:** solo las recomendaciones de dictámenes sólidos o respaldados.
- **Contraste:** tardío, adelantado y faltante (verificados), y solo especialización (acotar o tratar de forma
  cualitativa). «Sin referente» y «alineado» no generan refuerzo.
- **Quitado en la V3:** un concepto que la V2 enseñaba y la V3 ya no cubre en ningún tema, y que tiene núcleo en ≥ 3
  países o un objetivo de TIMSS o PISA del grado. Se propone recuperarlo, con su evidencia.

**Presupuesto:** siguen vigentes las reglas de `reportes/cobertura_curricular/CLAUDE.md`. Se prefiere reforzar
dentro del tema (microhabilidad, indicador, precisión) antes que agregar filas. Una fila nueva solo entra para un
faltante o una recuperación con evidencia fuerte. El resumen por ciclo cuenta las filas que se agregan.

### 15.5 · Redacción y revisión de las propuestas
- **Redacción:** un subagente nuevo, `redactor-refuerzos`, escribe cada refuerzo en el formato de la malla
  (procedimental, indicador, microhabilidades por fase, evidencia de aprendizaje), parafraseado y en español. El hook
  `validar_lotes.py` valida su salida. Todo nace `propuesta_pendiente`.
- **Revisión:** el panel revisa las propuestas (experto de la disciplina y psicopedagogo), y el bucle de
  fortalecimiento las impugna con citas. Solo se entregan las propuestas sólidas o respaldadas.

### 15.6 · Entregable
`entregas/mallas_v3_reforzadas/` (se genera):
- **Una copia anotada de cada matriz de la V3:**
  - las filas «Propuesta GOES» van junto al tema que refuerzan, con relleno verde claro;
  - las celdas combinadas y los estilos del MINED se respetan;
  - columnas nuevas al final: «Refuerzo GOES», «Evidencia GOES» y «Solidez GOES».

  El texto oficial no se modifica: una corrección va en «Refuerzo GOES», nunca sobre la celda del MINED.
- **`RESUMEN.md` y un `G<gg>.md` por grado:** qué se refuerza, por qué y con qué evidencia, más el conteo frente al
  presupuesto.
- **Compatibilidad con Numbers:** sin «·» en los nombres de pestaña, sin CHAR(10) y sin XLOOKUP ni FILTER.

## Reglas
- No se quita ningún tema ni se modifica el texto oficial. Lo que la V3 quitó se propone recuperar, no se impone.
- Cada refuerzo trae su fuente. Las inferencias de IA traen confianza, justificación y versión.
- Las propuestas son del equipo GOES con revisión del panel de expertos IA: **no son confirmaciones del MINED**.
- Parafrasear; no copiar párrafos de los PDF.
