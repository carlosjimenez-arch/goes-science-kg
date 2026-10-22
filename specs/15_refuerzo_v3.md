# 15 · Entrega V3 del MINED y refuerzo de cada tema

> Contrato del pipeline histórico V1–V3. Conserva decisiones y capacidades todavía usadas.
> Para la publicación V4 y la API actual, consultar [spec 16](16_producto_v4.md),
> [spec 17](17_aplicacion_curricular.md) y [documentación vigente](../docs/README.md).

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

**Correspondencia final** (`data/interim/mallas/v2_a_v3.json`, 2026-10-13). Además de idénticos y parecidos, la V3:
- **amplía o fusiona** temas: 75 temas de la V3 contienen casi entero (≥ 80 % de sus raíces) un tema de la V2 sin
  par, y heredan su id;
- **absorbe** temas: 136 temas de la V2 están dentro de otro tema de la V3 que ya tiene par;
- **mueve de grado** temas: 5, sobre todo genética y evolución, que pasa de 7.° a 9.°.

| Tema de la V3 | Cantidad |
|---|---|
| Idéntico a la V2 | 819 |
| Parecido | 21 |
| Ampliado | 75 |
| Nuevo | 20 |

Quedan 251 temas de la V2 sin rastro en el texto de la V3. Se juzgan por concepto en 15.4.

**Lo que ya se sabe para el refuerzo:**
- 10 de los 11 errores y problemas de progresión registrados siguen literales en la V3. Solo se corrigió la fibra
  óptica de 10.°. El «recordar V = IR» se movió a un tema nuevo de 11.°.
- Al pasar la resistencia bacteriana de 7.° a 9.°, el ciclo 5.°–8.° deja sin cubrir el objetivo de TIMSS 8.° B6.1
  (causas, transmisión, prevención y resistencia a enfermedades).
- Posible error nuevo de la V3: en 9.° 8.4, el procedimental habla de producir oxígeno y el indicador mide CO₂ (y
  repite el número 8.3).

## Fases
### 15.0 · Ingesta de la V3 ✅ (2026-10-13)
- El responsable copia los archivos a `data/fuentes/mined/Mallas sugeridas v3/`. La guarda impide que lo haga Claude.
- `config/mallas.yaml` apunta a la V3, con el nombre explícito de cada archivo. `config/mallas_v2.yaml` conserva la
  V2.
- **Correspondencia V2 → V3** (`data/interim/mallas/v2_a_v3.json`): cada tema de la V3 es `identico`, `parecido`
  (con su par y su similitud) o `nuevo`. Cada tema de la V2 sin par queda `sin_par`. Es determinista y tiene prueba.
- Pruebas: la V3 se lee completa por hoja, los ids son únicos y la correspondencia cubre los dos lados.

### 15.1 · Migración de las capas por la correspondencia ✅ (2026-10-13)
Todo lo que está atado a un id de tema de la V2 pasa al id de la V3 de su par idéntico:
- etiquetado de conceptos del grafo principal;
- revisiones de etiquetas y de coherencia;
- etiquetado `malla_v2` del contraste;
- capa pedagógica;
- decisiones y dictámenes del panel.

Lo de un par «parecido» se copia marcado para verificar. Lo de un tema «sin par» se conserva como histórico y no se
borra. El script valida que ninguna referencia quede apuntando a un id que no existe.

**Cómo quedó** (sin reescribir capas: los ids estables hacen casi todo el trabajo):
- `mallas.vigente_de(id)` traduce un id de la V2 al tema de la V3 que lo contiene. Lo usan la capa pedagógica (las
  actividades sin objetivo vigente pasan a `historico`) y su validación;
- el etiquetado de conceptos suma, como secundarios, los conceptos de lo absorbido al tema que lo absorbe;
- las clasificaciones TIMSS, PISA y ACARA llegan por `TemaMalla.llave`, la llave de la V2 de su par;
- el orden de la malla sale de la posición real del tema y no del id;
- el verificador del bucle busca una cita en el texto de la V1, la V2 y la V3;
- la conciliación de propuestas sigue siendo con la V2.

### 15.2 · Etiquetado de los temas nuevos y parecidos ✅ (2026-10-13)
- **Grafo principal:** subagentes `etiquetador-conceptos` sobre los 116 temas, sin costo de Vertex.
- **Contraste:** el etiquetado `malla_v2` se hace con Vertex. Primero se estima sin `--confirmar` y se pide la
  aprobación por número de llamadas, con margen.

**Hecho el 2026-10-13:**
- `alineador-marcos` clasificó 30 temas: TIMSS 4.° y 8.°, PISA, TIMSS Advanced y ACARA. Los lotes llevan el sufijo
  `_V3` para no pisar los ya unidos;
- cuatro `etiquetador-conceptos` re-etiquetaron los 116 temas nuevos, parecidos y ampliados (`preparar-etiquetado
  --v3`). Su etiqueta gana sobre la heredada;
- Vertex etiquetó la malla para el contraste: 67 llamadas, aprobadas hasta 84.

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

### 15.6 · Entregable histórico

El exportador V3 desconectado `refuerzo_excel.py` se retiró en `feat/api` tras comprobar la ausencia
de consumidores. Las entregas V4 usan los exportadores activos de producto y enmiendas. El diseño
siguiente conserva el requisito histórico; no afirma que exista un comando de exportación V3.
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
