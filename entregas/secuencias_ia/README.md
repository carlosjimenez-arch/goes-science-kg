# Secuencias de Ciencias V3 · revisión multiagente IA

Esta capa continúa la autoría de los temas de Ciencias de 2.º–11.º mediante especialistas de Biología,
Física, Química y Tierra/Espacio, psicopedagogía y refutación independiente. El responsable autorizó este
proceso al no contar con revisión humana. Los textos originales de los once libros se conservan y las
propuestas se registran por separado. El alcance es de 920 temas; los otros 15 del catálogo permanecen
fuera de Ciencias.

## Resultado de este corte

Se completaron 3.806 dictámenes y 1.138 cambios explícitos: cuatro lecturas por cada tema y una quinta para
los 126 cierres con correcciones. Las 920 propuestas están en la entrega de contenido **0.2.0**, contrato **1.1.0**.
Hay **444 secuencias disponibles para autoría asistida IA** y **476 retenidas para consulta y mejora**.
Una retención puede conservar un reparo histórico aunque el cierre discrepe o lo haya corregido: estas cifras
no equivalen a 476 errores científicos vigentes ni a 476 temas ausentes del currículo.

La mayor cantidad de retenciones de este corte está en 10.º y 11.º: 97 de 151 y 121 de 166, respectivamente.
Conviene priorizar allí la conciliación de columnas y el desarrollo de tareas, protocolos y datos que faltan.
Se debe comprobar el motivo de cada caso: ni sumar sesiones propuestas ni retirar un reparo de la interfaz
resuelve por sí solo el problema didáctico o científico. La siguiente versión debe documentar las reparaciones
y su nueva revisión, conservando la historia de este corte.

- [Excel de revisión](Revision_multiagente_Ciencias_V3_2a11.xlsx): resumen en prosa y por grado, secuencias,
  momentos, dictámenes y cambios; filtros y comparación con originales. También se dejó copia en Desktop.
- [Visor sin conexión](visor.html): filtros por grado, disciplina, estado y búsqueda; original y propuesta.
- [Pendientes por tema](pendientes_por_tema.csv): tabla para organizar la siguiente iteración.
- [Entrega para el motor](../motor/0.2.0/LEEME.md), con manifiesto, esquemas y registros completos.
- [Cinco ciclos](VALIDACION_5_CICLOS.json), [validación portátil](VALIDACION_MOTOR.json) y
  [331 pruebas aprobadas](PRUEBAS.txt). La publicación coincide por bytes con la candidata que pasó las pruebas.
- [Verificación del Excel](VERIFICACION_EXCEL.json) y [del visor](VERIFICACION_VISOR.json).

El Excel contiene 4.600 momentos y los 3.806 dictámenes. Se revisaron visualmente sus cinco hojas y se reabrió
para comprobar 107.363 celdas, sin errores de Excel y con las fórmulas calculadas conservadas. El visor se probó
en navegador con filtros combinados y comparación visible del original y la propuesta.

## Qué contiene

Cada secuencia incluye los cinco momentos originales y sus propuestas revisadas, producto evaluable,
tres criterios observables, consigna de salida, apoyos, alternativa sin internet y número sugerido de
sesiones. Incluye los dictámenes, sus citas literales, cambios completos y huellas de las candidatas
realmente leídas. Los grados y unidades actuales proceden de los atributos y la fuente, no de los
números que aparezcan en los identificadores heredados.

La revisión de todos los temas no equivale a disponer de todos los experimentos terminados. Se
retienen los casos con objeciones materiales o confianza baja. Un acuerdo posterior no borra una
retención anterior por mayoría. Las competencias digitales, PISA, TIMSS, MEN y del siglo XXI
siguen identificadas como declaraciones de la malla: su etiqueta no certifica ejercitación o dominio.

## Proceso y límites de la evidencia

1. Identidad y fuente: comprobación de libros, hojas, filas y columnas completas contra la entrega base.
2. Primera revisión científica: lectura por disciplina con cita comprobable y cambios explícitos.
3. Psicopedagogía: lectura de la candidata científica y las columnas originales, incluidos recursos digitales.
4. Refutación: lectura independiente de la candidata y los dos dictámenes, sin aprobación por votación.
5. Cierre científico: revisión de las objeciones y de la adaptación; las correcciones finales pasan por otra refutación.

La primera proyección científica no incluía el indicador avanzado. El cierre complementa esa lectura
con las columnas completas y cita ese indicador cuando está presente; se interpreta como meta de unidad,
sin exigir su desarrollo íntegro en cada tema. Se conserva la huella de la entrada realmente vista en
cada pase. Los agentes son ejecuciones separadas; no se presume diversidad de modelos ni independencia
estadística. Una cita curricular prueba la presencia de una frase, no su corrección científica.

Los cinco ciclos del informe incluyen la comprobación inicial de identidad y fuentes. La nueva refutación
se aplica a los 126 cierres con cambios; no se afirman cinco lecturas científicas de todos los temas.

La distribución de 55 minutos es orientativa para adaptar cada sesión. Las sesiones sugeridas no se
presentan como presupuesto curricular aprobado ni como duración observada. `tiempo_observado_min`,
`revisado_por` y las aprobaciones institucionales no se inventan. El perfil de aula permanece deshabilitado.

Los 230 paquetes anteriores tienen permisos propios: esta revisión no promueve sus componentes por
asociación. La entrega anterior conserva sus archivos y esquemas para permitir compatibilidad y reversión.

## Preparar y comprobar

```bash
uv run gskg secuencias preparar --etapa ciencia
uv run gskg secuencias validar-dictamenes --etapa ciencia --completo
# Las etapas siguientes son psicopedagogia, refutacion, final y refutacion_final.
# Refutacion_final se aplica a los cierres con cambios.
uv run gskg secuencias construir
uv run gskg motor exportar --version 0.2.0 --secuencias-ia
uv run gskg motor validar entregas/motor/0.2.0
uv run python scripts/preparar_revision_secuencias.py entregas/motor/0.2.0 entregas/secuencias_ia
```

Los lotes se regeneran desde la entrega base y los dictámenes; no se versionan porque contienen
proyecciones repetidas de las fuentes. Los dictámenes y la configuración sí se versionan y sus huellas
forman parte de los insumos de la entrega. Las instrucciones de revisión están en
[`prompts/revisar_secuencias_ia.md`](../../prompts/revisar_secuencias_ia.md) y el contrato en la
[`spec 17`](../../specs/17_panel_secuencias_ia.md).

El Excel se genera con [`scripts/crear_revision_secuencias.mjs`](../../scripts/crear_revision_secuencias.mjs),
usando `@oai/artifact-tool` del entorno de documentos de Codex. Recibe la carpeta de entrega, el archivo de
salida y, opcionalmente, una carpeta de previsualizaciones. Comprueba los conteos por grado y el recálculo
de fórmulas antes de exportar; guarda `VERIFICACION_EXCEL.json` junto al libro. Las cifras de resumen y
los minutos totales son fórmulas compatibles con Numbers; las sesiones de cada tema son datos propuestos.

Antes de publicar una versión inmutable se comprueba una candidata temporal. La variable
`GSKG_ENTREGA_SECUENCIAS=/ruta/candidata` permite ejecutar la aceptación completa del motor contra esa
carpeta; sin la variable, las pruebas usan `entregas/motor/0.2.0`. La candidata aprobada y la entrega publicada
deben coincidir por bytes. El manifiesto registra el commit de partida y las huellas del código exportador.
Al reproducir un corte, conservar sus insumos exactos, incluido el código, pasar `--commit-base` con el valor
exacto de su manifiesto y usar otro destino. Ese argumento identifica el punto de partida; no restaura código
histórico. Cambiar código, contenido o revisiones produce otra identidad y requiere una versión nueva:
la exportación rechaza sustituir una entrega existente por otra identidad.

## Cómo continuar con los retenidos

Se trabaja sobre una nueva candidata y se conserva este corte. La siguiente iteración debe resolver
el motivo concreto, no cambiar la decisión para aumentar la cifra de autoría:

- Corregir contradicciones de dominio, notación, recursos y habilidades mediante una capa explícita de
  propuestas de corrección, conservando la columna oficial. El contrato actual no permite reescribir esos campos.
- Completar protocolos y datos necesarios para la práctica, con fuente, condiciones, controles y límites;
  una alternativa documental no acredita por sí sola un indicador experimental.
- Incorporar tareas para los subobjetivos evaluados: añadirlos únicamente a una rúbrica no completa la secuencia.
- Precisar prerrequisitos y progresión cuando la abstracción o el alcance no corresponden al desarrollo mostrado.
- Distribuir las actividades entre sesiones cuando se sugiera más de una, antes de probar el presupuesto temporal.

Cada cambio material necesita una nueva lectura de la candidata exacta. Las decisiones institucionales y
el ensayo en aula se mantienen como evidencia por obtener, sin impedir seguir redactando, investigando y
revisando propuestas mediante el panel IA autorizado.
