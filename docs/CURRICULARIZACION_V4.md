# Curricularización de Ciencias V4 · 22 de octubre de 2026

Estado vigente: **108 unidades y 1.013 filas de Ciencias con propuestas respaldadas**. Las siete filas
fuera de alcance se conservan, sobre 1.020 filas originales. P6 resolvió las diez incidencias y P7 corrigió
un falso positivo adicional encontrado por revisión técnica. No se afirma eficacia medida ni aprobación
institucional. La publicación definitiva está seleccionada; el respaldo nuevo está restaurado y verificado.

La suite final pasó **1.360 pruebas en 262,79 segundos**; Ruff, calidad/determinismo (18 pruebas) y
las 86 pruebas nuevas desde el checkout público sin corpus están en verde. Selección definitiva producto-4:
`e92bc700d78f0f559671acc62f559f9e5176b09c3341a47c575c640195022008`.
Manifiesto SHA: `af8f228bd397430585a751978e437d4988efedc81f94e46dcadaceb068b80789`.
El recibo por generación está en `config/datos_ciencias.lock.json`;
[restauración y reanudaciones verificadas](VERIFICACION_GCS.md).

## Rectificación adicional P7

La revisión técnica detectó que Biotecnología microbiana de 11.º ofrecía levadura como alternativa
para el objetivo de cultivos bacterianos. El original K41 y la propuesta P5 conservaban esa contradicción,
que los cuatro jueces no habían detectado. El expediente previo se conserva como falso positivo.
P7 añade la definición primaria de [hongos y levaduras](https://openstax.org/books/biology-2e/pages/24-1-characteristics-of-fungi)
y las páginas PDF 12, 47 y 48 de la [guía PHAC/CFIA para bioseguridad escolar](https://www.canada.ca/en/public-health/services/canadian-biosafety-standards-guidelines/guidance/elementary-intermediate-secondary-school-classroom/document.html).
Se comprobaron las páginas completas y las dos últimas visualmente; la guía informa condiciones de
diseño y no traslada obligaciones legales canadienses a El Salvador. SHA del PDF capturado por HTTPS:
`0b40b03c9561f8da44d83310538742cdd3e96c0d7e886174d0a488d00040a500`.

La rectificación conserva la intención bacteriana, distingue hongos y exige cepas identificadas de bajo
riesgo, procedencia documentada, evaluación de riesgos y condiciones docentes. El primer borrador
excedió el límite de un campo; la reparación pasó contrato y cuatro votos nuevos. Son dos rondas,
seis invocaciones y 480,280 segundos. No se volvió a votar el mismo texto aprobado ni se borró el fallo.
El publicador impide promover el caso conocido sin la rectificación. Los originales con erratas siguen
bloqueados para generación genérica, incluso cuando la copia propuesta ya tiene corrección respaldada.

Plan P7 definitivo: `d6a3b5f29a0e13950fd1ac2b96cf882841431901c0b02e5b3c1fcbaa3f23db63`.
Archivo curricular consolidado: `471d0aeb9f5717ea5e32516bf00e69c0e5dcd1175fa2e42fbfa264833a8afa4a`.
Contador final único: **668 invocaciones, 633 completadas, 35 fallidas, cero pendientes y
USD 731,1485125 de reserva**, dentro de 1.100/USD 1.200. No es importe facturado. P6 añadió 34 llamadas
y resolvió sus diez unidades en una ronda cada una, en 1.202,233 segundos. No se reinició el ledger.

## Antecedentes P1–P6 y revisión P5

Las secciones siguientes documentan el estado previo P5 y sus incidencias; sus cifras no sustituyen
las del cierre indicado arriba.

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
