# Pedagogía de Ciencias V4: carga cognitiva, medición y recorridos cerrados

Fecha de revisión: 29 de octubre de 2026. Este documento fija criterios para las versiones sucesoras
locales y separa su revisión de diseño de la evidencia que sólo puede producir una aplicación con
estudiantes. Los guiones publicados y sus recibos se conservan como antecedentes.

## Qué se puede afirmar y qué exige observaciones

| Resultado disponible | Afirmación admisible | Afirmación que no se deriva de ese resultado |
|---|---|---|
| Archivo íntegro, SHA y pruebas de código | El archivo conserva sus bytes; el comportamiento probado cumple el contrato | Contenido científicamente correcto, aprendizaje eficaz o ausencia de errores |
| Rúbricas completas, soluciones y ejemplos revisados | El material contiene esos componentes y se revisaron los criterios declarados | Que estudiantes reales los comprendieron o que la rúbrica está calibrada |
| Límite de palabras, minutos propuestos, número de pasos | Indicadores descriptivos y decisiones locales de diseño | Una medida de carga cognitiva, de atención o de dificultad universal |
| Ejecución con un guion de respuestas o un evaluador simulado | Prueba de flujo y de guardas | Mejora de aprendizaje ni concordancia con docentes reales |
| Autoinforme tras una tarea | Esfuerzo mental percibido declarado bajo esas condiciones | Carga intrínseca/extrínseca separada ni éxito de aprendizaje |
| Respuesta nueva sin ayuda, calificada con evidencia | Desempeño observado en esa tarea | Dominio estable, retención, transferencia general ni efecto causal del refuerzo |

Las previas por ubicación en la malla, el desliz, el acierto al azar y el incremento
`aprendizaje_tras_refuerzo` de `config/aprendizaje.yaml` son parámetros del modelo histórico. Sin
calibración con datos no representan probabilidades empíricas de dominio. El aumento automático tras
un refuerzo no constituye evidencia adicional de que el estudiante aprendió. Un puntaje y una etiqueta
deben mostrar su procedencia y sus límites; no se deben convertir en un porcentaje de aprendizaje.

## Fundamento consultado y límites de traslado

El estudio de Leppink y colegas construyó y contrastó un cuestionario de diez ítems en cohortes
universitarias de estadística, con estudios correlacionales y un experimento. Esa validación no se
transfiere automáticamente a niños de 2.º–11.º, al español salvadoreño o a una escala abreviada. Su
instrumento y los autoinformes de esfuerzo requieren conservar pregunta, escala, condiciones y
población; cambiar esos elementos exige comprobar la interpretación de la adaptación.
[Estudio original de Leppink et al., 2013](https://doi.org/10.3758/s13428-013-0334-1).

Renkl y colegas contrastaron una transición gradual de ejemplos resueltos a problemas en experimentos
de campo y laboratorio. Encontraron apoyo para transferencia cercana y para retirar primero pasos
finales; el alcance sobre transferencia lejana fue menos claro. Aquí se adopta esa secuencia como
hipótesis de diseño que debe adaptarse a conocimientos previos, no como garantía de eficacia para cada
guion. [Estudio original de Renkl et al., 2002, registro de la universidad de sus autores](https://asu.elsevierpure.com/en/publications/from-example-study-to-problem-solving-smooth-transitions-help-lea/).

La guía institucional IES recomienda alternar ejemplos resueltos y resolución, combinar explicaciones
verbales con representaciones pertinentes, conectar representaciones concretas y abstractas y espaciar
la revisión. Sus recomendaciones declaran distintos niveles de evidencia; no justifican un umbral
universal de palabras, minutos o pasos para cada edad. En estos paquetes esos límites se presentan
como decisiones operativas revisables.
[Guía IES/WWC, Organizing Instruction and Study to Improve Student Learning](https://ies.ed.gov/ncee/wwc/PracticeGuide/1).

En el experimento de Karpicke y Roediger, producir una respuesta correcta durante el estudio no hizo
innecesaria la recuperación posterior: la práctica de recuperación favoreció el recuerdo demorado de
vocabulario. Es evidencia experimental en ese contexto, no una validación directa de estos paquetes
de Ciencias. Motiva separar la comprobación inmediata de una prueba posterior de retención, que aquí
no se declara realizada. [Estudio original de Karpicke y Roediger, 2008](https://doi.org/10.1126/science.1152408).

## Revisión del diseño de cada paquete

Los siguientes son criterios editoriales y de revisión local. Su cumplimiento no mide por sí mismo
la carga del estudiante ni la eficacia en el aula.

1. **Alineación y conocimientos previos.** Precisar qué idea científica se aprenderá, qué se necesita
   saber para la tarea y qué evidencia la demostraría. No deducir que una base está aprendida porque
   aparece en un grado anterior. Distinguir una dificultad observada de una base aún no comprobada.
2. **Elementos que deben coordinarse.** Revisar conjuntamente conceptos, datos, unidades, operaciones,
   representaciones y decisiones. Una tarea breve puede exigir muchas relaciones simultáneas; una
   explicación más larga puede reducirlas si presenta los pasos y sus conexiones con claridad.
3. **Información pertinente.** Eliminar analogías o datos que no explican el objetivo. La explicación
   redox del guion de vulnerabilidad es un defecto de pertinencia científica y pedagógica, aunque sus
   frases fueran cortas. Suprimirla no prueba una reducción medida de carga cognitiva.
4. **Presentación integrada.** Situar definición, diagrama o tabla y la consigna que los utiliza cerca
   uno de otro. Rotular magnitudes y unidades; mostrar correspondencias entre dibujo y símbolo.
   La versión sin conexión debe incluir el recurso o una instrucción reproducible para construirlo.
5. **Ejemplo explicado.** Presentar datos, objetivo, decisión de método, pasos y conclusión con sus
   límites. Explicar por qué se hace un paso; no ofrecer únicamente una respuesta final para imitar.
6. **Retirada de ayuda.** Pasar de ejemplo completo a tarea con parte de la solución ausente, después
   a práctica sin esos pasos visibles. Si aparece un error, devolver una ayuda concreta y comprobar
   luego con una tarea reservada. Un estudiante con conocimientos previos suficientes puede avanzar
   sin repetir apoyos que ya no necesita.
7. **Acceso e inclusión.** Ofrecer lectura oral literal, ampliación, descripción del gráfico, espacio
   para dibujo o respuesta oral cuando corresponda. Separar estos ajustes de una pista conceptual:
   una adaptación de acceso no significa por sí misma que la respuesta haya sido guiada.
8. **Datos y seguridad.** Distinguir dato real, medición del aula, simulación y estimación. No atribuir
   cifras ficticias a una institución. Conservar incertidumbre, supuestos y unidades. Una adaptación
   de recursos o de lectura debe conservar las condiciones de seguridad del procedimiento.

## Diagnóstico → refuerzo → comprobación independiente

El cierre documental requiere materiales que se puedan usar de principio a fin. Cada recorrido debe
contener, como mínimo:

- **Diagnóstico:** consigna completa, datos/imagen necesarios, respuestas esperables y criterio
  docente de derivación. Si el diagnóstico permite varias explicaciones del error, sondeo específico
  antes de declarar una base deficitaria. Evitar la etiqueta personal «tiene baja capacidad».
- **Refuerzo:** explicación pertinente, ejemplo trabajado con razonamiento, práctica con ayuda que
  disminuye y retroalimentación específica para los errores previstos. Explicitar cómo se vuelve al
  objetivo y qué hacer si el material o el tiempo no bastan.
- **Comprobación reservada:** tarea alineada con el mismo criterio, datos o situación nuevos,
  solución no visible, condiciones de ayuda declaradas y rúbrica docente completa. Cambiar sólo el
  identificador no crea una tarea nueva. Comprobar también si la práctica ya muestra la respuesta o
  una solución que puede copiarse sin comprender.
- **Retorno:** decisión basada en la nueva respuesta: avance provisional, refuerzo concreto pendiente,
  o revisión docente. Un registro de práctica no sustituye silenciosamente una comprobación ausente.
  No encadenar reintentos hasta producir una apariencia de éxito: si se agotan los ítems reservados,
  registrar que falta evidencia y preparar otra oportunidad.
- **Materiales finales separados:** hoja del estudiante sin claves; guía docente con soluciones,
  razonamiento, criterios de rúbrica, derivación, ayudas permitidas y seguimiento. Los enlaces deben
  llevar a materiales existentes. El estado de completitud debe distinguir material disponible de
  aprendizaje comprobado.

«Independiente» describe aquí la separación de la respuesta respecto de la ayuda y de la solución
mostrada. Un segundo agente puede revisar el paquete, pero compartir modelo, proveedor o criterios no
da independencia estadística. Una nueva comprobación inmediata tampoco demuestra retención; queda
planificado un control posterior sin afirmar que ya se realizó. No se deben ensayar ni revelar sus
respuestas durante el refuerzo.

## Registro honesto de esfuerzo percibido

`aprendizaje/carga_cognitiva.py` ofrece `resumen_esfuerzo()`. Sin respuestas de estudiantes devuelve
`no_medido`; con sólo guiones simulados, `solo_simulado`. Nunca convierte la ausencia de datos en
«carga cero» ni crea un porcentaje de eficacia. Es un registro descriptivo opcional para un protocolo
de aplicación, no una prueba ya administrada a estudiantes.

Cada autoinforme declara `instrumento_id`, `version`, `referencia`, `idioma`, `pregunta`, todas las
categorías de la `escala`, `grado`, `tarea`, `momento`, `contexto_aplicacion`, `ayuda_conceptual`, `adaptaciones_acceso`,
`origen`, un `registro_id` único y `respuesta`. El momento debe precisar la ubicación respecto de
la tarea y la retroalimentación. El contexto identifica aplicación, condiciones y versión del material,
sin datos personales. El origen es declarado por quien registra: el contrato no puede
demostrar por sí solo que una respuesta fue producida por una persona real. Su procedencia se audita
con el protocolo y la evidencia de aplicación; no se introducen datos ficticios como observaciones.

No se incluyen nombres ni identificadores personales en este contrato. `n_reales` cuenta registros de
tarea, no estudiantes únicos. Una misma persona puede aportar varios registros y no debe contarse
como varios participantes. La aplicación con menores, sus consentimientos y el tratamiento de sus
datos requieren el proceso institucional correspondiente; esta revisión no recoge esos datos.

Para una primera aplicación, el equipo docente debe ensayar que el alumnado comprenda la pregunta,
las categorías y la diferencia entre esfuerzo, interés, dificultad y acierto. Registrar la versión
exacta y la aplicación; cualquier adaptación lingüística o por edad sigue pendiente de validación
local. No atribuir a una pregunta local la validación de Paas o de Leppink.

La salida conserva distribuciones de categorías y, cuando hay respuestas, las dos posiciones
centrales ordinales. No promedia categorías ni transforma su diferencia en «porcentaje de reducción».
Las faltantes se cuentan aparte; las simulaciones no entran en la distribución real. No se agregan
tareas, grados, escalas, versiones, idiomas, preguntas o condiciones diferentes. La interpretación
debe considerar también el desempeño y los apoyos: esfuerzo bajo puede coexistir con incomprensión,
y esfuerzo alto con una tarea relevante y productiva. El módulo no aplica un umbral de sobrecarga.

## Criterio de entrega y límites

Se puede cerrar una versión **documentalmente completa** cuando tiene todos los materiales, fuentes
pertinentes, soluciones comprobadas, rúbricas completas, condiciones de aplicación y pruebas de sus
guardas, y una revisión que no haya encontrado defectos materiales pendientes en ese alcance. El
registro de revisión debe indicar autor, versión exacta, criterios, resultados y observaciones.

La aplicación y la eficacia siguen teniendo sus propios estados: sin respuestas reales, el aprendizaje
permanece **sin comprobar** y el esfuerzo **no medido**. Con respuestas inmediatas sólo se describe
ese desempeño; hacen falta controles posteriores y un diseño de evaluación adecuado para estudiar
retención, transferencia o efectos causales. La expresión «a prueba de errores» se operacionaliza como
pruebas adversariales y límites explícitos, nunca como garantía de ausencia de errores científicos.

Verificaciones del contrato: `uv run --frozen pytest -q tests/test_carga_cognitiva.py`. Incluyen ausencia
de datos, respuestas faltantes, rechazo de categorías inválidas, duplicados, separación entre simulación
y observación, no agregación de condiciones incompatibles y conservación de las categorías ordinales.
