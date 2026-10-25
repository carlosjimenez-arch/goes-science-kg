# Ciencias V4: continuidad y verificación

Actualización operativa: 23 de octubre de 2026, America/Bogota.

## Ampliación de guiones de clase

El usuario autorizó un máximo **acumulado** de 4.000 invocaciones y USD 3.500 de reserva para los
1.013 guiones de Ciencias. Las 668 llamadas anteriores no se reinician. El recibo literal privado
está en `data/operaciones/clases_v4_20261022/autorizacion.json`; `config/presupuesto_clases_v4.json`
fija el prefijo de consumo y sus límites. El saldo se calcula desde el ledger real, no desde este texto.

El corte de la campaña P11 cubre los 1.013 objetivos: 968 respaldos automáticos, 27 vetos y
18 abstenciones. La revisión directa de los 32 casos está completa y conserva seguimientos
adicionales: los defectos conocidos bloquean sus versiones aunque tengan votos positivos.
La publicación íntegra de guiones y unidades continúa pendiente. Hay 34 resoluciones exactas
registradas y 2.060 trazas verificadas en 369 resultados seleccionados. El siguiente plan de 45 lotes
requiere 225–450 llamadas y hasta USD 548,04604 de reserva. Su preflight no cabe en 4.000 llamadas;
la solicitud a 4.400 está pendiente, conservando el máximo USD 3.500 y el contador.
El cierre local conserva 3.941 llamadas y USD 2.912,1834795 de reserva, con cero llamadas pendientes.
P9 permite correcciones explícitas y cuatro lecturas nuevas; P10/P11 separan historial y contexto,
conservan pasajes completos y auditan los protocolos anteriores. [Estado y controles](CLASES_V4.md).

El respaldo P11 contenía 13.762 archivos y 41 SQLite y fijaba 3.941 llamadas acumuladas; el recibo vigente del 25 de octubre (13.919 archivos) lo incluye sin cambiar el contador. Se
restauró independientemente y se comprobaron 2.295 trazas y la recuperación de 32 terminales con
cero llamadas nuevas. Un punto mínimo de continuidad impide reanudar desde un ledger antiguo que
pierda el consumo posterior a las primeras 668 llamadas. La suite completa pasó 1.581 pruebas.
[Generaciones y reproducción](VERIFICACION_GCS.md). La biblioteca de preparaciones sigue disponible;
no se presenta como entrega de clases completas.

## Cierre curricular anterior

Estado vigente: P6 resolvió las diez incidencias y P7 corrigió un falso positivo adicional con fuentes
primarias y cuatro votos sobre otro borrador. La publicación definitiva producto-4 selecciona las
108 unidades y 1.013 filas de Ciencias, conservando las siete fuera de alcance. Se exportaron la
matriz comparada, la vista y cuatro enmiendas en la copia derivada de Biología. Google pidió
reautenticación antes de gastar; tras la respuesta del usuario se verificaron ADC y gcloud GOES.
El ledger conserva 668 invocaciones y USD 731,1485125 de reserva, cero pendientes y ningún reinicio.
La suite final pasó 1.360 pruebas. [Resultados actuales](CURRICULARIZACION_V4.md).

El respaldo histórico GCS de 7.580 archivos se adoptó y restauró antes de ampliar los guiones. Los once terminales P6/P7 se
reanudaron desde la copia recuperada con cero llamadas nuevas y ledger idéntico byte a byte.
[Recibo y comprobaciones](VERIFICACION_GCS.md). Los apartados históricos conservan las etapas anteriores.
El corpus local se retiró tras una segunda restauración y comparación completa: 7.580 archivos en
61 rutas. La entrega de consulta se conserva fuera del checkout y dentro del respaldo privado.

## Alcance autorizado

La solicitud vigente corresponde exclusivamente a Ciencias. Se omiten las instrucciones de la conversación
cruzada de Matemáticas: su bucket, rondas, límites y documento `OPERATOR_REHEARSAL.md` no se aplican aquí.
El usuario autorizó investigar, descargar fuentes necesarias, usar Vertex, completar el producto, probarlo
rigurosamente y enviar commits con la identidad Git ya configurada. Solicitó la rama `feat/ciencias-v4`.
La rama de entrega con código se renombró y se envió a `origin/feat/ciencias-v4`. El checkout local con
historia privada del corpus se mantiene separado para impedir publicar ese corpus en GitHub.

## Respaldo privado

Se eligió el bucket general existente `goes-ai-kg-artefactos`, prefijo `ciencias/v4`, del proyecto
`g-edu-lxp-xai-dev-prj-976d`, con identidad `carlos.jimenez@goes.gob.sv`. No se crea un bucket ni se cambia IAM.
La lectura inicial constató acceso uniforme y prevención pública heredada con política efectiva obligatoria.
La implementación vuelve a comprobar esa política por cada escritura, exige generación nueva y relee
los bytes de cada generación. La aceptación de protección heredada sigue la [documentación de Google](https://docs.cloud.google.com/storage/docs/using-public-access-prevention).

El paquete base local contiene 828 archivos y 256.258.866 bytes comprimidos, incluidos cinco SQLite
copiados mediante la API de backup consistente. SHA-256:
`1b8f68d9716e1e1a8cd0d8fdbf24b24ea2604fc4a315b94e4de4611c35f6eb72`.
Su plan está en `data/operaciones/respaldos/ciencias-v4-base-20261022.json`.

La revisión automática rechazó subir el corpus completo: consideró que la autorización previa cubría
checkpoints y descriptores, no los 828 archivos. Se solicitó autorización explícita para ese paquete y
entregas posteriores de las mismas clases de contenido hasta 1 GiB acumulado, en el mismo prefijo privado.
Después se verificó una autorización humana posterior y explícita en el chat «Mover datos a un bucket».
Ese chat completó el traslado y la restauración de 7.397 archivos. El recibo por generaciones está en
`config/datos_ciencias.lock.json`; no se subió el paquete base de 828 archivos rechazado. La autorización
posterior cubre el corpus de Ciencias y no cambia cuenta, proyecto ni bucket. [Traslado verificado](DATOS_EXTERNOS.md).

## Antecedente: producto durante P5

Durante P5 la publicación base verificable era `producto-3`, snapshot
`0e2da287eb9248c37df078835d00fb63cd9a7585c882fb1cbc1ba5ed543f41aa`.
La revisión `producto-4` está publicada en `data/producto/V4_revision_p5`: propuesta curricular por unidad, matriz comparada,
progresiones documentales nativas, evidencias, revisiones y vista sin conexión. No se selecciona una
publicación nueva hasta consolidar el denominador completo y comprobar sus fuentes y controles.

Se prepararon 108 unidades y 1.020 filas completas sin modelos. El contexto conserva los campos originales,
las fases presentes y ausentes, clasificaciones, alertas y fuentes. Los recursos adicionales son condiciones
para impartir la propuesta; no disponibilidad comprobada en escuelas. Los referentes extranjeros mantienen
su población: no se homologan grados ni se deducen prerrequisitos individuales por orden documental.

Las fuentes nuevas incluyen NGSS (12 expectativas de tres dimensiones en cuatro bandas y nueve enlaces
`SIGUE_EN_REFERENCIA`) y seis capturas HTML primarias de NHGRI/OpenStax. Las regiones PDF comprueban banda
física, extremos y SHA. Las capturas HTML reabren el selector DOM y verifican bytes/texto; no inventan páginas.
Las enmiendas a `S3`, `W3` y `W14` de Biología 10 se proponen explícitamente, conservando los originales.

## Campaña y experimentos

Contador único: `ciencias_v4_curricularizacion_20261022`, en `data/operaciones/registro.sqlite`.
Límites operativos: 1.100 invocaciones y USD 1.200 de reserva conservadora acumulativa, sin reinicio.
Las tarifas configuradas son cotas operativas, no una factura. El adaptador conserva reservas incluso
ante errores, limita reintentos y valida contratos antes de cachear. Cada unidad tiene comprobación
`safe_to_start` y checkpoint durable; una reanudación terminal no vuelve a votar.

P1 recibió rechazos 400 antes de generar. Un diagnóstico sin nivel de razonamiento también fue rechazado.
P2 simplificó la gramática de transporte según las [restricciones documentadas de Vertex](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output),
manteniendo toda la validación local. El redactor produjo contenido, pero los jueces detectaron omisiones
científicas y curriculares; el resultado quedó rechazado. La revisión curricular agotó 16.384 tokens.
No se borraron votos ni se publicó ese borrador. Código P2 archivado con SHA
`823f08deddf8d9a8a54d22f5aeb1408acdceb8f77a94f28014c16471ae1f2438`.

P3 refuerza el redactor con Argon y preservación explícita de todos los desempeños; proyecta metadatos
no semánticos y permite 32.768 tokens de salida. P4 compara redacción MEDIUM frente a HIGH con el mismo
prompt y cuatro revisores HIGH. La comparación se declaró antes de conocer el resultado de P3; se conservan
ambas variantes. La elección exige calidad revisada y considera latencia, sin votaciones ilimitadas.
Los experimentos están en `data/operaciones/mejoras_v4_20261022_p*` y no se confunden con una aprobación.

Un diagnóstico de desarrollo del RAG auxiliar sobre siete consultas y seis secciones mostró seis aciertos
con expansión terminológica frente a uno con búsqueda léxica estricta. No es conjunto ciego, no demuestra
cobertura científica del currículo ni superioridad general de un enfoque agentic. El RAG sigue siendo auxiliar.

## Registro del cierre técnico

- P6 terminó sus diez incidencias y P7 rectificó otro falso positivo con fuentes y cuatro votos nuevos.
- La entrega definitiva selecciona las 108 unidades y conserva todos los antecedentes y controles.
- La batería integral y el envío de código se documentan en [CIERRE_TECNICO.md](CIERRE_TECNICO.md).
- El recibo final fija 7.580 archivos; la restauración y las reanudaciones conservan el contador.

El cierre corresponde al producto técnico. La aprobación institucional y la eficacia de aprendizaje
requieren sus propios procesos; no se obtienen mediante votos de agentes.

## Coordinación posterior de migración (22 de octubre UTC)

Se verificaron las instrucciones humanas del chat «Mover datos a un bucket»
(`01a161c9-c16e-7191-ac79-25659864e77b`): mover todos los datos/PDF/resultados a almacenamiento externo,
con recuperación comprobada, y coordinar el cierre de escrituras con este chat. Esta autorización es
posterior al rechazo descrito arriba; el otro chat debe presentarla en su revisión de aprobación.
No se elude ese rechazo mediante una carga indirecta de este chat.

El piloto P5 terminó con respaldo de los cuatro revisores en una ronda. Los escritores de esta sesión
quedaron cerrados: no hay archivos abiertos bajo `data/operaciones` ni llamadas reservadas en curso.
Balance de sólo lectura al cierre: 50 llamadas, reserva USD 50,6882185, 41 completadas y 9 fallidas.
Se conserva `ciencias_v4_curricularizacion_20261022` y sus límites de 1.100 llamadas / USD 1.200.

P4 obtuvo tres pilotos respaldados (Materia 2.º, Física 10.º y Biomoléculas 10.º), pero la unidad de
25 filas quedó en abstención por un límite global de 60.000 bytes. Un control falló por agotar la salida
de Psicopedagogía HIGH, por lo que no se declaró superado. P5 permite 120.000 bytes por borrador, informa
los límites completos, restringe FIDs al contexto y conserva respuestas inválidas en `salidas_llm` para
repararlas con el texto recibido. Recupera salidas recibidas sin pagar otra llamada si faltase su caché.
Psicopedagogía usa MEDIUM y se añadió un quinto control específico de adecuación al grado. No se han
bajado las rúbricas científicas ni se aceptan fallos de proveedor como detecciones correctas.

El protocolo P5 está en `data/operaciones/mejoras_v4_20261022_p5/plan.json`;
ID `06c8c90c267df8c62aa17e1c7f89bebf53a72679a55fef69b139581ad968ca3f`.
La cota de dos rondas para todas las unidades es USD 2.189,52, superior al tope operativo: no se garantiza
cubrir el peor caso completo. Cada unidad comprueba su cota antes de comenzar y el ledger impide exceder
USD 1.200. El consumo real de reservas del piloto es considerablemente menor; no se reinicia el contador.

Durante el traslado no se inician nuevas generaciones ni escrituras en datos. Se continúa con código y
pruebas sintéticas. La restauración debe conservar rutas y archivos normales: los lectores rechazan enlaces
simbólicos. La tabla `checkpoint_presupuestos` vincula el registro a ruta, dispositivo e inodo; restaurar
requiere migrar explícitamente esa identidad sólo después de verificar el inventario y la conservación
íntegra de llamadas y reservas. No se borra la tabla ni se cambia el ID para sortear el control.

Verificación anterior a los últimos ajustes P5: 1.322 tests pasados, calidad/determinismo del grafo 18 pasados.
Regresión de P5 con recuperación de salidas y contratos: 71 tests pasados. Se ejecutará nuevamente la suite
completa después de terminar e integrar la migración y la publicación final.
