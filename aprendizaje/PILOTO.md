# Propuesta de piloto del tutor y de política de datos de estudiantes

> **Decisiones técnicas tomadas el 2026-10-12** (sección 0) por delegación del responsable del proyecto, con la
> asesoría del panel de expertos IA (spec 14, `panel/DICTAMEN.md`). Siguen necesitando el aval institucional del
> MINED para trabajar con estudiantes. Las secciones 1–6 son la propuesta original. El sistema que se describe
> es el prototipo de la spec 13 (`specs/13_apoyo_al_aprendizaje.md`). Las recomendaciones van marcadas como tales; las
> decisiones que se piden están en la última sección. La política de datos es una propuesta técnica: la tienen que
> validar la asesoría jurídica de GOES y del MINED con la normativa vigente de protección de datos personales y de
> niñez y adolescencia.

## 0. Decisiones tomadas (2026-10-12)
| # | Decisión | Evidencia | Estado en el repositorio |
|---|---|---|---|
| 1 | **Fases A → B0 → B → C.** **B0 es nueva:** 1 centro, 1–2 secciones de 9.°, 2 semanas, sin grupo de comparación, con revisión diaria de todos los turnos. | Panel (psicopedagogo): la fase A no ve a estudiantes reales y B0 lo detecta a bajo costo. | Documentado aquí. |
| 2 | **Unidad del piloto: 9.° U8, La célula** (4 objetivos; uno ya tiene contenido revisado por el panel). La alternativa, según el calendario, es U1, Mecánica de fluidos. | El panel descarta U3, porque el contraste propone reubicar K, Ka y amortiguadoras. Descarta U2, por un problema de secuencia. Descarta U9, por temas sensibles. U8 es la unidad más chica, así que el contenido se puede revisar entero. | Falta redactar y revisar los otros 3 objetivos de U8. |
| 3 | **B es un piloto de factibilidad con estimación preliminar del efecto, no una prueba de eficacia.** Los criterios de avance y de detención se escriben antes de empezar (sección 3 y punto 5 abajo). | Con 6–8 secciones el efecto de diseño es de 4 a 8: no hay potencia para detectar d ≈ 0,35. | Documentado aquí. |
| 4 | **Uso en clase, con el docente presente.** 2 sesiones por semana de 20–25 min. El grupo de comparación dedica el mismo tiempo a la práctica habitual. El repaso espaciado se adapta a ese calendario. | El panel la considera la única modalidad que vigila la fidelidad, iguala el acceso y protege a los menores. | `config/aprendizaje.yaml`: `repaso.intervalos_dias` = 3, 7, 14 y 30. |
| 5 | **Fidelidad científica del tutor: las dos medidas.** Primero, una prueba de banco antes de B0: ≥ 200 turnos, dos revisores humanos, 0 errores. Además, un verificador de fidelidad en cada turno, con un modelo distinto del tutor. En B0 se revisan todos los turnos; en B, una muestra diaria del 10 %. | La prueba de humo mostró un error que justo refuerza la idea equivocada del objetivo. Con 0 errores en 200 turnos, la tasa real queda por debajo de 1,5 % con 95 % de confianza. | Verificador construido: `aprendizaje/fidelidad.py`, obligatorio en `llm.fidelidad`. La prueba de banco requiere aprobar el gasto en Vertex: de 400 a 800 llamadas. |
| 6 | **Salvaguardas de menores**, además de la sección 4: un filtro de datos personales antes del modelo; un protocolo ante señales de riesgo (no se llama al modelo y se avisa al docente); nunca mostrar etiquetas como «brecha» ni comparaciones; consentimiento explicado también de forma oral; asentimiento con palabras de la edad; ninguna consecuencia académica. | Panel (psicopedagogo). | Construido: `aprendizaje/salvaguardas.py`, integrado al evaluador y al tutor. Faltan el consentimiento oral, la región fija y el contrato sin entrenamiento, que son tareas institucionales. |
| 7 | **El contenido llega a estudiantes solo con verificación humana interina.** Hace falta: dictamen favorable del panel (estado `revisado_panel`); firma de un docente de aula del grado en `revisado_por` (estado `verificado`); los puntos de `REVISION_PENDIENTE.md` cerrados; y las rúbricas calificadas por dos docentes. Mientras κ < 0,7, toda respuesta abierta pasa por el docente. | El panel también es IA y puede compartir los sesgos del redactor. | Estados `propuesta_pendiente` → `revisado_panel` → `verificado` en la capa. Los 138 elementos están en `revisado_panel`. |
| 8 | **Primaria (fase C) solo después de B sin incidentes.** Condiciones: lectura en voz alta para todos; enunciados de 50 palabras como máximo; respuesta abierta oral o con dibujo; el evaluador solo sugiere; parejas por dispositivo; 2 refuerzos de 8 min como máximo. | 7 de los 18 enunciados de 5.° pasan de 50 palabras, con una mediana de unas 115 contando las opciones. | Límites por tramo en `config/aprendizaje.yaml` (`refuerzo.por_tramo`; se ven en R4). Regla de enunciados agregada al redactor. |
| 9 | **Opciones barajadas y respuestas numéricas tolerantes.** | Panel: la clave era la A en 34 de 84 ítems. Además, «50 000» se marcaba como error. | `sesion.barajar()` y `sesion.lecturas_numericas()`, con pruebas. |

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
4. **Control de fidelidad del tutor.** La prueba de humo con Vertex (2026-10-12) mostró que un turno puede decir
   algo científicamente impreciso que las guardas no detectan. Hay dos caminos: revisar turnos reales en la fase A,
   o agregar un segundo control automático (una llamada más por turno). Es una decisión de costo y calidad.
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
