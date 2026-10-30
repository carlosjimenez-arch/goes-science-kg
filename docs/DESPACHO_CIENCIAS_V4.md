# Entrega en el Escritorio y control de calidad

La instrucción del usuario queda registrada en `AGENTS.md` y `CONTRIBUTING.md`: dejar todos los paquetes
finales en el Escritorio, conservando sus originales y comprobando la copia. Las salidas futuras deben
mantener revisión editorial, científica/pedagógica e integridad estructural en su alcance real.

## Entrega de Ciencias V4

Destino: `$HOME/Desktop/Ciencias_V4_Entrega_20261029/`.

- `LEEME.md`: índice de acceso a R1–R5, los dos guiones corregidos y el módulo de medición honesta.
- `entrega/`: copia íntegra de los 4.909 archivos de la edición final, con las unidades, clases, anexos,
  evaluaciones, hojas diferenciadas, fuentes, revisiones y antecedentes.
- `ciencias_v4_mejora_didactica_final.zip`: la misma edición en ZIP.
- `calidad/`: auditoría independiente, nueva revisión de adecuación, reglas del repositorio, informes
  de pruebas y cobertura, y documentación pedagógica.
- `recibo_despacho.json`: inventario por bytes/SHA de los archivos efectivamente copiados, con identidad
  de edición, ZIP, alcance y fecha. El recibo es portable y no necesita las rutas originales para verificarse.

Edición: `1960ed2480c21750874890d9f74f2b0e790569822b13021ab66208fcb2cc3dd9`.
ZIP SHA-256: `a85d8250fefba9436216993d754d301ffa37ae10baa6efce5fe3efee47aaa5e2`.

El contenido científico no cambió al copiarlo: el [informe de la edición](ENTREGA_DIDACTICA_V2.md)
documenta los cinco recorridos y casos identificados, las correcciones y sus dictámenes. Se conservan
los 151 objetivos sin guion y los 54 retenidos con sus estados; no se presenta al resto del corpus como
nuevamente revisado a partir de estos ocho paquetes.

## Nueva revisión de adecuación

Otro agente leyó completos los ocho paquetes, sus dos GuionClase anidados y los 15 ítems de la evaluación
corregida, incluidas opciones, claves, soluciones, rúbricas, seguridad y adecuación al grado. Comprobó
40 ítems nuevos, 52 criterios y 28 cálculos, además de la integridad actual de los archivos y de los nueve
JSON respecto de sus dictámenes. No detectó un defecto sustantivo nuevo que bloquee el despacho documental.

Evidencia original: `data/clases_v4/despacho_20261029/adecuacion_final.json` y `.md`.
Las condiciones de campo, las alternativas ficticias y la prioridad municipal no se confunden con una
competencia instrumental observada ni con una medición real de riesgo o de carga cognitiva.

## Comprobación obligatoria antes de despachar

`gskg entrega despachar` comprueba la carpeta, las cuatro hojas de los materiales nuevos, los dictámenes
exactos y sus SHA, la exclusión de retenidos y los enlaces internos. Coteja también nombres seguros, CRC,
inventario y SHA de todas las entradas del ZIP contra la edición. Exige una auditoría independiente
favorable y correspondiente a esa identidad y a ese ZIP, sin errores abiertos.

La medición de pruebas debe ser completa y actual: cero fallos, errores y omisiones, JUnit y cobertura
coincidentes, denominador de la colección vigente y huella del código y de las políticas. Cambiar el código,
`AGENTS.md` o `CONTRIBUTING.md` invalida la medición anterior. La ausencia de esa evidencia bloquea el despacho.

El comando prepara una copia en una carpeta propia, comprueba sus SHA, reserva un destino nuevo sin
sobrescribir y verifica la entrega efectiva. Los originales y los recibos de publicación se conservan.
Los controles automáticos no sustituyen el juicio científico/pedagógico; cualquier cambio de contenido
requiere un dictamen nuevo de su versión exacta.

```sh
uv run --frozen gskg entrega despachar \
  data/clases_v4/mejora_didactica_20261029/entrega_final \
  --archivo-zip data/clases_v4/mejora_didactica_20261029/ciencias_v4_mejora_didactica_final.zip \
  --auditoria data/clases_v4/mejora_didactica_20261029/auditoria_final_independiente/resultado.json \
  --evidencia data/clases_v4/despacho_20261029/adecuacion_final.json \
  --evidencia data/clases_v4/despacho_20261029/adecuacion_final.md \
  --evidencia AGENTS.md \
  --evidencia CONTRIBUTING.md \
  --destino "$HOME/Desktop/Ciencias_V4_Entrega_20261029"
```

Sin `--destino`, se propone una carpeta en el Escritorio identificada por la edición. Si el destino ya
existe se rechaza la operación para conservarlo; una nueva versión necesita una carpeta nueva.

La validación completa del código de despacho pasó **1.819 pruebas, sin fallos, errores ni omisiones**,
en 487,02 segundos de pytest. Cobertura de líneas **79,83 % (20.295/25.423)**. También pasaron Ruff
(344 archivos con formato correcto), las seis pruebas JavaScript y la auditoría del repositorio.
La huella de código y políticas de esta medición es
`804dfa67a5272639ec3742bcd4d2218f6e8ca0c495cfa20defd5e7ba652f7385`.

Una invocación real previa con la medición obsoleta fue rechazada antes de crear la carpeta del
Escritorio. Las regresiones comprueban suite parcial, filtros de entorno, evidencia alterada, ZIP
divergente, falta de dictámenes, destino existente, cambios durante la copia y recibos con rutas escapadas.

Los registros del despacho y la comprobación física independiente del Escritorio se guardan en
`data/clases_v4/despacho_20261029/`. `verificacion_escritorio.json` coteja la copia y el ZIP con los
originales, el recibo y la auditoría, y comprueba los enlaces del índice. Las pruebas y la política
vigentes quedan además copiadas en `calidad/` del destino.

No se llamó a Vertex, no se amplió ni reinició el presupuesto y no se publicó en GCS. La entrega en el
Escritorio es una copia local verificada. La revisión documental y técnica no acredita eficacia con
estudiantes, retención ni carga cognitiva medida.

## Piloto Vertex de guiones sucesores

El 29 de octubre se despachó además el piloto de [ampliación Vertex](AMPLIACION_VERTEX_CIENCIAS_V4.md)
a `$HOME/Desktop/Ciencias_V4_Piloto_Vertex_20261029/`, preservando la carpeta anterior.
Contiene ocho guiones sucesores con materiales, de los cuales seis llevan ediciones Codex
identificadas; no son aún nuevos anexos, recorridos completos ni unidades. El índice distingue
los materiales, fuentes, límites, dictámenes y antecedentes retenidos.

Esta materialización usa GuionClase y su catálogo específico, diferente de la edición didáctica V2
que acepta `gskg entrega despachar`. Se aplicaron controles equivalentes mediante el compilador y
copiador privados revisados: versión exacta por SHA, autor/revisor distintos, ciencia/pedagogía,
retirada de claves, fuentes, enlaces generados, inventario, ZIP/CRC, suite vigente, conservación,
destino nuevo exclusivo, limpieza del destino propio ante error y recibo portable de copia.
Se comprobaron los originales HTML como evidencia íntegra; sus rutas web no se convierten en enlaces
locales creados por el renderizador. Las políticas de repositorio se adjuntan como texto original
para conservar sus bytes sin presentar enlaces del árbol del repositorio como interfaces locales.

La revisión independiente materializada y la revisión técnica del copiador precedieron al despacho;
otro agente verificó después los 296 archivos físicos contra sus orígenes, los 271 miembros del ZIP,
el recibo y los 4.923 archivos de la entrega anterior. No se detectaron diferencias.
Recibo: `c94b33468c2eb9a73ac674f09856bd57d0f77fa62d9c4318564c7bdf890e9c10`.
La evidencia está en `data/clases_v4/ampliacion_vertex_20261029/revision/`, incluidos
`verificacion_escritorio_piloto_independiente.json` y `.md`.

La suite vigente pasó 1.908 pruebas sin omisiones, cobertura 79,9339579 %, seis pruebas JavaScript,
Ruff y auditoría del repositorio. Es evidencia del código, no de eficacia educativa. El navegador
bloqueó `file://`; se cotejaron HTML, Markdown y CSS localmente, sin afirmar inspección visual ni
paginación impresa. El piloto consumió sus 18 solicitudes y USD 29,661560 de reserva conservadora;
la compilación y el despacho no hicieron llamadas y no hubo publicación en GCS.
