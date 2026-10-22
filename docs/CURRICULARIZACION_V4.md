# Curricularización de Ciencias V4 · revisión del 22 de octubre de 2026

El producto propone una curricularización comparable con el insumo, con evidencias y decisiones por
unidad. No se presenta como validación del aprendizaje ni aprobación institucional. El estado actual
es **98 unidades respaldadas y diez incidencias abiertas**, sobre un denominador fijo de 108 unidades
y 1.020 filas. Las siete filas fuera de Ciencias se conservan, sin contarlas como mejoras científicas.

## Entrega comprobada

- 888 filas de Ciencias con objetivo propuesto, indicador observable, producto evaluable, criterio,
  orientación didáctica, recursos condicionales, seguridad, andamiaje y contexto salvadoreño propuesto.
- Las cinco fases originales, indicadores, evidencia y localizadores siguen disponibles; 138 ausencias
  de «Aproximar» no se rellenan como si fueran contenido del insumo.
- Excel/CSV original-propuesta, vista HTML sin conexión y expediente JSON íntegro con fuentes y votos.
- Copia derivada de Biología: tres enmiendas respaldadas en S3, W3 y W14; comparación de todas las
  celdas y estilos. Sólo cambia el XML de las hojas afectadas; otras partes OOXML conservan sus bytes.
- Doce expectativas NGSS verificadas físicamente, cuatro bandas por dimensión y nueve relaciones
  `SIGUE_EN_REFERENCIA`. No se proyectan como prerrequisitos locales.
- Cinco controles adversariales distintos detectados por el criterio y especialista previstos. Un
  fallo del proveedor no cuenta como detección. Son pruebas sintéticas de desarrollo, no calibración
  independiente ni evidencia educativa.

| Grado | Unidades respaldadas | Abstenciones | Vetos |
|---|---:|---:|---:|
| 2.º | 6 | 0 | 0 |
| 3.º | 6 | 0 | 0 |
| 4.º | 6 | 0 | 0 |
| 5.º | 6 | 0 | 0 |
| 6.º | 3 | 3 | 0 |
| 7.º | 4 | 1 | 1 |
| 8.º | 8 | 1 | 0 |
| 9.º | 11 | 0 | 0 |
| 10.º | 24 | 2 | 0 |
| 11.º | 24 | 0 | 2 |

## Protocolo y experimentos

P1 recibió errores 400 antes de generación. P2 simplificó la gramática de transporte conservando la
validación local completa: sus propuestas fallaron por alcance/ciencia. P3 comparó un redactor con
razonamiento HIGH; agotó límites de formato. P4 usó MEDIUM: tres pilotos respaldados, una unidad grande
sin salida admitida y un control incompleto. P5 declaró límites completos, FIDs restringidos al contexto,
120.000 bytes por borrador, respuestas inválidas recuperables y psicopedagogía MEDIUM.

La campaña P5 tomó 3.699,761 s con ocho unidades concurrentes: 81 unidades terminaron en una ronda y 27
requirieron dos. Cada ronda válida fue leída a ciegas por ciencia, currículo y adversarial (Argon HIGH)
y psicopedagogía (Flash MEDIUM). Un voto negativo o insuficiente impide el respaldo; no se compensa
por mayoría. Compartir proveedor/modelo limita la independencia de estos revisores.

El contexto conserva todos los campos originales, deduplica sólo textos idénticos y vuelve a verificar
Excel, regiones PDF, bandas físicas y párrafos DOM. Los fragmentos de cita son localizadores de hasta
veinte palabras; los revisores también reciben las lecturas primarias completas pertinentes.
PISA/ERCE y currículos de Inglaterra, Singapur y Japón aportan referencias de diseño con su edición
y población; no prueban equivalencia entre edades ni obligan a enseñar toda una banda en una unidad.

El índice científico auxiliar trabaja con párrafos completos, sin cortar evidencia. En siete consultas
de desarrollo, la expansión explícita español-inglés obtuvo seis aciertos frente a uno del léxico
estricto con el mismo presupuesto. Ese conjunto abierto no permite declarar ganador general ni
promover Agentic RAG. El baseline previamente evaluado sigue seleccionado.

## Diez incidencias y seguimiento P6

Cuatro unidades necesitan únicamente un voto ausente por 429; se preservan los otros tres votos y el
borrador exacto. Las seis restantes requieren reparación real de formato, alcance, recursos, citas o
ciencia. P6 conserva cada antecedente completo y deja de nuevo un máximo de dos rondas; no reevalúa
las 98 unidades respaldadas ni vuelve a votar un borrador idéntico vetado. Dos unidades incorporan
fuentes puntuales separadas del índice P5:

- [OpenStax, elasticidad y ley de Hooke](https://openstax.org/books/college-physics-2e/pages/5-3-elasticity-stress-and-strain).
- [OpenStax, proceso de disolución](https://openstax.org/books/chemistry-2e/pages/11-1-the-dissolution-process).

P6 reduce a dos unidades concurrentes y dos revisores concurrentes por unidad. Su cota conservadora
es USD 213,649365, dentro del saldo operativo. El primer intento de inicio fue rechazado por identidad
ADC no renovable **antes de cualquier llamada a modelos**. Tras la respuesta del usuario, se verificó nuevamente la identidad ADC GOES y la renovación de gcloud.
El seguimiento se reanudó con el mismo plan y contador. No se sustituye la cuenta institucional.

## Artefactos y contabilidad

Rutas institucionales restaurables (los resultados P5 todavía no están en el respaldo previo):

```text
data/operaciones/mejoras_v4_20261022_p5/plan.json
data/operaciones/mejoras_v4_20261022_p5/resultados/
data/operaciones/mejoras_v4_20261022_p6/plan.json
data/producto/mejoras/campana_p5_20261022.json
data/producto/mejoras/controles_p5_20261022/resultado.json
data/producto/V4_revision_p5/
data/producto/entrega_revision_p5_20261022/
data/operaciones/registro.sqlite
```

La revisión `producto-4` contiene 2.202 nodos, 6.929 aristas y diez archivos. Snapshot:
`6ca75555924ff9c2dcd362bfbef389649b2a2fd20ebc3cafb4cb844c0853feec`.
Archivo de propuestas: `5210bea7db2cf9e60a6fbb875d575df130ebcd4aa4f823557152916eaacab590`.
La selección estable `data/producto/V4/actual.json` conserva por ahora `producto-3`; la revisión completa
se consulta indicando `data/producto/V4_revision_p5`. Se verifica antes de promover una nueva selección.

El ledger único `ciencias_v4_curricularizacion_20261022` conserva **628 invocaciones**, 594 completadas,
34 fallidas y **USD 682,815936 de reserva acumulada**, sin invocaciones pendientes. Los límites son
1.100 llamadas/USD 1.200; quedan 472 llamadas y USD 517,184064 de reserva. No son importes facturados.
Las tarifas configuradas usan cotas conservadoras del [precio oficial](https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing).

El respaldo GCS previo permanece válido por generación. Al cerrar P6 se debe preparar un paquete nuevo,
subir objetos nuevos, releer las generaciones, restaurar íntegramente y sólo entonces retirar los datos
locales. No retirar los resultados nuevos usando el recibo anterior.
