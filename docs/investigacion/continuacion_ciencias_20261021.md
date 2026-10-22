# Continuación de Ciencias: juicios, contexto y producto

Fecha: 21 de octubre de 2026. Las instrucciones de Matemáticas se omitieron por confirmación del
usuario. Esta continuación no cambia su presupuesto, bucket, cuenta ni rama Git.

## Publicación y evidencia real

Actualización posterior: la generación actual es
`0e2da287eb9248c37df078835d00fb63cd9a7585c882fb1cbc1ba5ed543f41aa`, formato `producto-3`, nueve
archivos, 1.191 nodos y 4.136 aristas. Añade los cuatro casos originales de alineación documental con
sus votos y perfiles; un respaldo por fila, un rechazo y dos abstenciones. No hubo llamadas nuevas.
La [integración reproducible](integracion_alineaciones_v4.md) y la
[investigación NGSS](progresiones_ngss_20261021.md) documentan el nuevo corte. Las cifras y experimentos
siguientes conservan la historia anterior a esa integración.

La publicación local V4 anterior era
`c8098a090648ea4cc966cce7f95ce28d1f214f758b8d0c2e305d68db27d14045`, formato `producto-2`.
Conserva 1.020 filas, 108 unidades y el catálogo completo con 68 abstenciones. Incluye quince juicios
originales: **dos respaldos, seis rechazos y siete abstenciones**, limitados a quince filas. No hay
prerrequisitos reales respaldados ni progresión educativa acreditada.

Los respaldos relacionan dos filas de quinto grado con el Sistema Internacional de Unidades, mediante
cálculo de magnitudes derivadas, nomenclatura y representación de cantidades. Los cuatro lectores los aceptaron con límites de
alcance explícitos; no atribuyen a quinto las definiciones cuánticas del BIPM ni una enseñanza realizada.
El archivo conserva los otros trece estados. Las relaciones admitidas se recuperan únicamente en su
fila; las inferencias históricas siguen sin trasladarse globalmente a V4.

Los archivos `conocimiento-publicado-1` mantienen sus hashes anteriores. La composición
`conocimiento-publicado-2` conserva íntegros los componentes y sus protocolos, además de una vista
conjunta de evidencia deduplicada. Revalida cada componente, rechaza candidatos repetidos y comprueba
ciclos en la unión. Un ciclo bloquea toda la admisión, conservando los juicios. Los componentes
completos agregan almacenamiento y validación inicial; la consulta usa la vista conjunta.

## Experimentos y límites

| Ejecución | Intentos | Reserva USD | Resultado |
|---|---:|---:|---|
| Nueve contrastes con cuatro lectores | 36 | 4,743792 | Tres rechazos y seis abstenciones |
| Esquema con listas por grupo | 8 | 1,087252 | Primer caso procesado; cuatro errores 400 en el segundo; siete casos sin ejecutar |
| Diagnóstico del error 400 | 1 | 0,0741555 | Mensaje genérico de argumento inválido |
| Selección escalar, seis casos | 24 | 3,280060 | Cero errores estructurales; cuatro rechazos y dos abstenciones |
| Cuatro conceptos SI con fuente primaria | 16 | 2,170181 | Un respaldo, dos rechazos y una abstención |
| Cuatro pares PISA/ERCE | 12 | 1,563349 | Un respaldo documental, un rechazo y dos abstenciones |
| Dos pares nuevos con lectura primaria completa | 8 | 1,082511 | Un respaldo y un rechazo; cero fallos estructurales |

Las 105 reservas de juicios y alineación suman **USD 14,0013005**. La comparación estructural, incluidos sus fallos
y diagnóstico, consumió 33 intentos y USD 4,4414675: permanece dentro del límite anunciado 36/USD 6.
El piloto comparte el contador de los seis casos. No se reinició ningún contador ni se reintentaron
dictámenes para forzar unanimidad. Los casos repetidos sólo se usan para ingeniería; sus votos no se
publican como relaciones nuevas.

El baseline tenía ocho lecturas que omitían grupos obligatorios. En los primeros seis casos comparables
eran cinco de 24; la selección escalar obligatoria las redujo a cero. Las rúbricas, vetos, validación
de citas y unanimidad siguen vigentes. Es una regresión sobre casos conocidos, no una medición de
precisión educativa ni prueba de independencia entre modelos.

Vertex no explicó la causa concreta del error 400. La complejidad del esquema es una hipótesis
compatible con sus [limitaciones documentadas](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output),
no una causa demostrada. El corte automático detuvo el lote al fallar los cuatro lectores de un caso.

En la primera suite global, una prueba antigua dependía de que no existiera una publicación V4 en
el repo real. Dejó dos reservas fallidas por `TransportError`, USD 0,125946, sin respuesta ni tokens
reportados. Se conservan y se informan separadamente: **107 intentos registrados y USD 14,1272465**
incluyéndolas. No se afirma facturación cero. Se corrigió el aislamiento y se añadió una guarda global
que impide abrir el cliente real de Vertex/ADC; los tests deben inyectar un proveedor sin red. También
se restauran los handlers de logging al terminar cada test. El subtotal excluye clasificación,
embeddings, unidad y experimentos anteriores, cuyos contadores permanecen separados.

## Lectura y citas

Los tres resultados no respaldados del lote SI señalaron definiciones ausentes de los fragmentos
presentados. El texto completo sí estaba en las evidencias archivadas, pero no llegaba al lector.
Se separaron lectura y cita: los jueces reciben completos los objetivos, evaluación y páginas externas
seleccionadas; las citas siguen siendo literales de hasta veinte palabras, resueltos por código.
Cada fuente externa incluida conserva un fragmento seleccionable. Si el JSON completo no cabe, se
abstiene sin recortar el texto primario para aparentar cobertura.

La [medición local](medicion_lectura_primaria_20261021.json) conserva 1.166 preparados de 1.203 con
24.000 y 40.000 caracteres; los otros 37 mantienen el veto científico. Se retienen **24.000** por
eficiencia. Los cuatro expedientes SI incluyen sus cuatro páginas completas y la definición del SI
en ambos presupuestos. Dos pares que nunca se habían juzgado recorrieron el nuevo formato: uno quedó
respaldado y otro rechazado, con ocho lectores completados y cero fallos estructurales. Reanudar con
generación prohibida recuperó los dos terminales y consumió cero. Esto comprueba integración real;
no es una comparación semántica independiente ni sustituye retrospectivamente los dictámenes.

La fuente científica está separada de evaluación y países: BIPM, *The International System of Units*,
9.ª edición, V4.01 de junio de 2026, inglés, 102 páginas y SHA fijado. Licencia CC BY 4.0, con atribución
en `NOTICE` y [catálogo oficial](https://www.bipm.org/en/publications/si-brochure). Se verificaron las
páginas físicas de soporte; ingerir el PDF no valida todas sus extracciones ni una adecuación escolar.

## Acceso y escenarios

La API `/api/v4` consulta una generación fijada, sin cargar V3 como alternativa. Ofrece salud,
diagnóstico, filas con filtros/paginación, evidencia de la fila exacta, auditoría de juicios y preparación
de unidades sin modelos. Un cambio de snapshot invalida la instancia hasta verificar y reiniciar.
La auditoría relee las fuentes primarias, también para los resultados rechazados. No hay endpoints
de generación remota ni publicación desde peticiones HTTP.
La [verificación sobre la publicación real](api_v4_publicada_20261021.json) comprobó las 1.020 filas,
los dos nuevos juicios, el veto de grado y una preparación de ocho sesiones, con el constructor de
Vertex prohibido. En treinta listados locales secuenciales de cincuenta filas, p50 fue 1,95 ms y p95
2,36 ms; arranque 1.171 ms y auditorías con relectura de fuentes 317–361 ms. No es una prueba de carga.

`producto escenario` comprueba recursos y capacidad declarados conservando cada objetivo exactamente
una vez. Los ejemplos mantienen ocho objetivos y proponen doce bloques de cuarenta minutos: con
320 minutos y papel/lápiz hay déficit de 160 y faltan instrumentos; con 480 y los materiales propuestos
se satisfacen esas restricciones. Ningún ejemplo certifica duración suficiente, recursos reales,
respaldo pedagógico o aprendizaje, ni modifica los cuatro respaldos y cuatro abstenciones de la unidad.

La carga horaria del insumo no es uniforme. Biología, `Notas!B6`, dice que no asigna horas y contrapone
36 h/año sugeridas a planeadores pensados para unas 160. Física, `Mapa de unidades!G3:G10`, declara
una hora por cada tema de su primera unidad. No se generaliza una nota a todas las asignaturas ni
se convierte automáticamente «hora» a minutos de clase. [Localizadores](localizadores_tiempo_v4.json).

Datos verificables: [publicación, resultados y consumo](resultados_continuacion_ciencias_20261021.json),
[comparación estructural](resultados_seleccion_grupos_20261021.json),
[lectura primaria SI](lectura_primaria_si_20261021.json),
[escenarios](resultados_escenarios_20261021.json) y
[unidad ejecutada](resultados_unidad_fisica10_v4.md).

## Unidad experimental íntegra

El [escenario de sesenta minutos](resultados_unidad60_20261021.md) obtuvo siete respaldos y una
abstención por carga cognitiva y tiempo insuficiente para comprobar el objetivo de seno/coseno.
Conserva 64 intentos y USD 10,517924, incluidos dieciséis fallos de transporte. La recuperación usó
el mismo contador; reanudar sus ocho terminales consumió cero y tardó 79,65 ms del orquestador.

Una variante fijada antes de generar dividió ese objetivo en dos encuentros de sesenta minutos,
reservando quince minutos para la comprobación. Obtuvo los tres respaldos, con ocho intentos y
USD 1,533031 de reserva dentro del nuevo protocolo 8/USD 2. No repite el mismo contexto ni cambia
el contador anterior. La [entrega experimental](entrega_unidad_fisica10_20261021.md) conserva los ocho
objetivos, siete propuestas de la cohorte completa y la nueva variante: nueve encuentros y 540
minutos propuestos. Releyó fuentes y reconstruyó gates sin modelos; conserva íntegros los originales,
incluida su abstención. No es un paquete uniforme de sesenta minutos ni carga oficial.

Estas dos fases de unidad añaden 72 intentos y USD 12,050955. Sumadas a juicios, alineación e incidente
de pruebas, la continuación registrada acumula **179 intentos y USD 26,1782015**. Se mantienen separados
clasificación, embeddings y el ensayo anterior de cuarenta minutos; no se reinician sus contadores.

La reconstrucción curricular completa sigue pendiente: los juicios reales cubren quince filas,
todavía no hay progresiones verificadas y la alineación PISA/ERCE conserva cuatro pares de prueba.
La unidad experimental supera su gate bajo las condiciones propuestas; no acredita cobertura de la
V4 nacional ni convierte los estados previos en aprobaciones. La suite mide controles de software.
