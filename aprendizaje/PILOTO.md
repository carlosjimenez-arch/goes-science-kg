# Propuesta de piloto del tutor y de política de datos de estudiantes

> **Borrador para decisión de GOES y del MINED (2026-10-12).** Nada de esto está aprobado. El sistema que se describe
> es el prototipo de la spec 13 (`specs/13_apoyo_al_aprendizaje.md`). Las recomendaciones van marcadas como tales; las
> decisiones que se piden están en la última sección. La política de datos es una propuesta técnica: la tienen que
> validar la asesoría jurídica de GOES y del MINED con la normativa vigente de protección de datos personales y de
> niñez y adolescencia.

## 1. Qué tiene que responder el piloto
1. **¿Mejora el logro de los objetivos?** Comparar con la práctica habitual en una prueba posterior sobre los mismos
   objetivos, con ítems que el tutor no usó.
2. **¿Es correcto el diagnóstico?** Comparar las hipótesis que el tutor confirma con el juicio del docente sobre el
   mismo estudiante.
3. **¿Califica bien el evaluador de respuestas abiertas?** Medir su concordancia con la calificación de docentes en
   respuestas reales.
4. **¿Respeta el tiempo de clase?** Medir el desvío por sesión (límite de diseño: 25 minutos) y cuántas veces se toca
   un límite.
5. **¿Lo usan y lo valoran?** Recoger la opinión de docentes y estudiantes, y cuánto trabajo da la revisión docente.

Mientras no haya respuesta a estas preguntas, la mejora educativa sigue siendo una hipótesis (spec 13, sección 9).

## 2. Alcance recomendado
| Fase | Qué | Con quién | Duración | Requisito para pasar a la siguiente |
|---|---|---|---|---|
| A. Revisión y calibración | El equipo de Ciencias revisa la capa pedagógica de los objetivos del piloto. Docentes califican respuestas abiertas reales, sin datos de identificación, con la misma rúbrica. | Equipo de Ciencias y 4–6 docentes; **sin estudiantes usando el tutor** | 3–4 semanas | Contenido en estado «verificado». Concordancia entre el evaluador y los docentes de κ ≥ 0,7 (si no se alcanza, las abiertas siempre pasan por el docente). Prerrequisitos de esos objetivos revisados. |
| B. Piloto en aula | Una unidad de **9.°** con el tutor como complemento de la clase, frente a secciones con la práctica habitual. | 2–3 centros escolares, 6–8 secciones | 6–8 semanas, con una prueba diferida a las 3–4 semanas | Criterios de éxito definidos antes de empezar (sección 3). |
| C. Exploración en primaria (opcional) | Uso guiado por el docente en **5.°** (el objetivo de suelo ya tiene contenido) para probar lenguaje, lectura y formatos. Se mide factibilidad, no efecto. | 1–2 secciones | 2–3 semanas | Decisión sobre formatos no textuales: lectura en voz alta, imágenes, manipulación. |

**Por qué 9.°:** es donde hay más evidencia. Están el contraste internacional verificado y la malla V2 completa, y
la capa pedagógica ya tiene 3 objetivos de 9.°. La unidad concreta depende del calendario escolar: hay que redactar y
revisar el contenido de **todos** los objetivos de esa unidad (hoy hay 3; una unidad tiene entre 10 y 20).

## 3. Diseño de la medición (recomendación)
- **Comparación.** Secciones con tutor frente a secciones con la práctica habitual, idealmente del mismo docente
  para controlar su efecto. La asignación se hace por sección, no por estudiante dentro de un aula.
- **Medidas:**
  - prueba previa y posterior sobre los objetivos de la unidad;
  - prueba diferida a las 3–4 semanas (retención);
  - tiempo en tarea;
  - objetivos «logrados provisionales» que el docente confirma;
  - concordancia del evaluador;
  - encuesta a docentes y estudiantes.
- **Tamaño orientativo.** Para detectar un efecto moderado (d ≈ 0,35, potencia 0,8, α = 0,05) hacen falta unos 130
  estudiantes por grupo **sin contar** el agrupamiento por sección. Con secciones como unidad hacen falta más. Conviene
  que un estadístico fije el tamaño con la correlación intraclase esperada.
- **Criterios de éxito y de detención, escritos antes de empezar:**
  - ganancia frente al grupo de comparación;
  - ningún daño (que no empeore la retención ni quite tiempo de clase por encima del límite);
  - concordancia del evaluador;
  - satisfacción docente.

  Si un docente reporta un contenido erróneo, ese contenido se retira hasta revisarlo.

## 4. Política de datos (propuesta)
| Tema | Propuesta |
|---|---|
| Identificación | Ningún nombre en el sistema. Cada estudiante tiene un **seudónimo** que genera el centro escolar. La tabla de correspondencia queda en el centro y nunca entra al sistema. |
| Qué se guarda | Por estudiante: evidencias (actividad, respuesta, si fue correcta), estado de dominio, hipótesis, refuerzos y repasos. Nada de eso va a las capas compartidas: hoy vive en `data/estudiantes/`, fuera de git. En el piloto iría en un almacenamiento cifrado del proyecto GOES. |
| Qué se envía al modelo de lenguaje | El grado, el contexto curricular y, en las respuestas abiertas, el texto que escribió el estudiante. **Nunca el seudónimo.** El tutor no guarda los prompts en caché (`vertex.generar_json(cache=False)`; una prueba lo comprueba). Antes del piloto hay que confirmar en el contrato del proveedor que no usa esos datos para entrenar y en qué región se procesan. Hoy la región es «global» (`GSKG_VERTEX_REGION`); para datos de menores se recomienda fijar una región. |
| Datos que el estudiante escribe sin querer | Una respuesta abierta puede traer un nombre o un dato personal. El tutor nunca los pide (es una guarda). Se recomienda indicarlo a los estudiantes y revisar una muestra durante la fase A. |
| Consentimiento | Consentimiento informado de madres, padres o responsables y asentimiento del estudiante. Quien no participe sigue con la clase habitual, sin consecuencia académica. |
| Uso de la evidencia | El tutor **no califica**: su evidencia no entra en la libreta de notas. El docente ve el estado de su sección y las notas del tutor (refuerzos que no se cumplieron, respuestas en revisión). |
| Acceso | Cada docente ve su sección. El equipo GOES ve datos seudonimizados para el análisis. El MINED recibe resultados agregados. |
| Retención | Los datos individuales se borran al cerrar el análisis (se propone a los 6 meses del fin del piloto). Se conservan solo agregados. |
| Revisión docente | Toda respuesta abierta que el evaluador no decide con certeza va al docente. También las que parecen instrucciones al evaluador. El estado del estudiante no cambia hasta que el docente decide. |

## 5. Lo que falta construir antes de la fase B
1. **Interfaz para estudiantes y docentes.** El prototipo es de línea de comandos (`gskg tutor …`). Hacen falta una
   interfaz web sencilla, una vista docente con la cola de revisión y el almacenamiento cifrado.
2. **Contenido.** Hay que redactar y revisar todos los objetivos de la unidad del piloto con el subagente
   `redactor-actividades`, y después revisarlos en el equipo de Ciencias.
3. **Prerrequisitos.** Hay que revisar los prerrequisitos de esos objetivos; hoy los 822 son propuestas de IA.
4. **Prueba de humo con el modelo real.** Correr con Vertex los turnos y las evaluaciones de los recorridos. Necesita
   la aprobación del gasto: hoy todo corre con modelos de guion.
5. **Estimación de llamadas.** Por sesión se calculan de 6 a 10:
   - unas 3 del tutor por refuerzo, con un máximo de 3 refuerzos;
   - 1 del evaluador si hay respuesta abierta.

   Para 130 estudiantes con 10 sesiones serían de 8.000 a 13.000 llamadas. Hay que pedir la cotización y la
   aprobación antes de empezar.

## 6. Decisiones que se piden
| # | Decisión | Opciones o recomendación |
|---|---|---|
| 1 | Grado, unidad y centros del piloto | Se recomienda 9.°, una unidad según el calendario, 2–3 centros |
| 2 | Uso en clase o fuera de clase | Se recomienda en clase, con el docente presente (más control y menos brecha de acceso) |
| 3 | Modelo de lenguaje, proveedor y región | Gemini en Vertex (proyecto GOES), con región fija; o el que GOES defina |
| 4 | Consentimiento y retención | Lo de la sección 4, validado por la asesoría jurídica |
| 5 | Quién revisa y aprueba la capa pedagógica | El equipo de Ciencias del MINED, con un docente de aula por objetivo |
| 6 | Qué se hace con los huecos de secuencia que detecte el tutor | Que vayan a la revisión de la malla (spec 06), no al tutor |
| 7 | Presupuesto de llamadas al modelo | Según la estimación de la sección 5 |
