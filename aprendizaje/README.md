# Apoyo al aprendizaje sobre el grafo · prototipo

Diseño completo: [`specs/13_apoyo_al_aprendizaje.md`](../specs/13_apoyo_al_aprendizaje.md). Código:
`src/goes_science_kg/aprendizaje/`. Parámetros: `config/aprendizaje.yaml`.

## Qué es
Un tutor que **complementa** la malla V2 del MINED sin modificarla. Para un objetivo de la malla:
1. revisa sus bases en el grafo («¿qué necesita comprender?»);
2. si la malla enseña una base después del objetivo, ofrece una activación breve (**previo**);
3. evalúa el objetivo; si la respuesta es incorrecta, abre **hipótesis** y las comprueba con preguntas breves;
4. refuerza lo confirmado (**durante**) con un microtema, una práctica y una comprobación distinta;
5. vuelve al objetivo y lo reevalúa con **otra** actividad (otra habilidad);
6. actualiza el estado del estudiante y programa **repasos** espaciados (**posterior**);
7. muestra «¿dónde ayudará reforzar esto?» con el recorrido inverso del grafo.

## Recorridos de ejemplo (`uv run gskg tutor recorridos`)
| Recorrido | Objetivo (malla V2) | Qué muestra | Resultado |
|---|---|---|---|
| [R1](recorridos/R1_difusion_osmosis.md) | G09-CIE-U8-8.2 · difusión y ósmosis | falta una base de grados anteriores (concentración, 3.°); la membrana queda «sin comprobar», no «en brecha» | logrado provisional |
| [R2](recorridos/R2_procesos_termodinamicos.md) | G09-CIE-U2-2.4 · procesos termodinámicos | la malla enseña la base en el mismo tema: activación previa; su comprobación falla y el diagnóstico baja a profundidad 2 (kelvin) | dominado |
| [R3](recorridos/R3_constante_equilibrio.md) | G09-CIE-U3-3.6 · constante de equilibrio | los sondeos descartan las bases y confirman la dificultad en el concepto del objetivo | logrado provisional |
| [R4](recorridos/R4_suelo_primaria.md) | G05-CIE-U6-6.14 · suelo (primaria) | el ciclo en 5.° con tutor y evaluador simulados: la guarda rechaza un turno demasiado largo y el reintento pasa; un refuerzo de 10 min supera el límite de primaria (8 min) y queda para el docente; la reevaluación es una respuesta abierta calificada con la rúbrica | logrado provisional |
| [R5](recorridos/R5_respuesta_abierta_a_revision.md) | G09-CIE-U3-3.6 · constante de equilibrio | la respuesta abierta intenta darle instrucciones al evaluador: no se llama al modelo y va a revisión docente | en progreso (espera al docente) |

Los estudiantes son **simulados** (un guion fija cada respuesta) y el contenido es **propuesta pendiente**. En R4 y R5,
el tutor y el evaluador también son simulados: son modelos de guion, sin Vertex. Los recorridos prueban que el ciclo y
sus guardas funcionan sobre los datos reales del grafo, no que el estudiante aprenda más. Eso solo lo puede mostrar un
piloto con estudiantes ([`PILOTO.md`](PILOTO.md)).

## Tutor conversacional y evaluador de respuestas abiertas
- **Tutor** (`tutor.py`). La sesión decide qué hacer y el modelo solo redacta el turno: presentar el refuerzo, dar una
  pista o cerrar. Antes de mostrar un turno se revisa que:
  - respete el largo del grado;
  - no revele la respuesta (letra, texto de la opción, valor o respuesta modelo);
  - cite solo fuentes del contexto;
  - no traiga enlaces ni pida datos personales.

  Si el turno falla dos veces, se muestra el microtema tal como está en la capa pedagógica.
- **Evaluador** (`evaluador.py`). Es separado del tutor y califica con la rúbrica. Cada criterio cumplido necesita una
  cita literal de la respuesta. «Correcta» la calcula el código. Va a revisión docente, sin cambiar el estado del
  estudiante, todo lo que tenga confianza baja, guardas que fallan o instrucciones dentro de la respuesta.
- **Modelos** (`llm.py`, `config/aprendizaje.yaml`): Gemini en Vertex.
  - No guarda caché.
  - El identificador del estudiante no llega a ningún prompt.
  - Solo se llama con `--confirmar`, y el harness pide aprobación del gasto.
  - Hoy todo está probado con modelos de guion.

```bash
uv run gskg tutor turno G09-CIE-U8-8.2 --grado 9          # sin --confirmar: respaldo, sin gasto
uv run gskg tutor evaluar ACT:G05-CIE-U6-6.14/obj-abierta "…"   # sin --confirmar: muestra la rúbrica
```

## Estado del contenido pedagógico (`data/pedagogia/`)
- **96 actividades, 21 dificultades y 21 microtemas** para 6 objetivos:
  - **3.°:** G03-CIE-U1-1.3, fuerzas de contacto;
  - **5.°:** G05-CIE-U6-6.14, suelo;
  - **7.°:** G07-CIE-U2-2.7, genes y alelos;
  - **9.°:** G09-CIE-U8-8.2, U2-2.4 y U3-3.6.

  Cada objetivo trae una **respuesta abierta con rúbrica**.
- **Estado:** `revisado_panel`. Lo redactó el subagente `redactor-actividades`. Después lo revisó el panel de
  expertos IA (spec 14): el experto de la disciplina, luego el psicopedagogo y luego otra vez el experto. El panel
  corrigió 69 de los 138 elementos.
- **Con estudiantes:** el estado no basta. Hace falta la firma de un docente del grado (`aprendizaje/PILOTO.md`,
  decisión 7). Las dificultades no citan fuente.
- Los puntos que dejaron los redactores para la revisión (datos experimentales idealizados, convención de signos de
  la primera ley, seguridad de las actividades, dificultades que juntan dos ideas) están en
  [`data/pedagogia/REVISION_PENDIENTE.md`](../data/pedagogia/REVISION_PENDIENTE.md).

## Prueba de humo con el modelo real (2026-10-12, 12 llamadas aprobadas)
Se usó Gemini en Vertex con respuestas de ejemplo escritas por el equipo, sin datos de estudiantes.

| Prueba | Resultado |
|---|---|
| 4 turnos del tutor (3.°, 5.°, 7.° y 9.°) | Los 4 salieron del modelo. En 3.° y 9.° el primer turno se pasaba del largo del grado (46 de 40 y 86 de 80 palabras); la guarda lo rechazó y el reintento pasó. |
| Calidad de los turnos | El turno de 7.° decía «el gen es el color»: confundía el gen con el rasgo, que es justo la dificultad del objetivo. Las guardas no detectan errores de sentido. Se reforzó la instrucción (definiciones con el sentido exacto del contexto) y el turno repetido salió correcto. Además, se agregó una guarda contra las etiquetas de fuente dentro del texto. |
| Pistas por sentido | En 5.° la explicación del tutor apunta a la opción correcta de la práctica sin copiarla. Es la misma idea que trae el microtema: la práctica está muy cerca de la explicación. Queda para la revisión del contenido. |
| 5 respuestas abiertas (5.° y 7.°) | Las 5 se evaluaron como se esperaba: 2 paráfrasis correctas aceptadas con citas literales; 2 errores típicos detectados con su dificultad; 1 respuesta ambigua enviada a revisión docente por confianza baja. En una de 7.° el criterio opcional c3 se dio por cumplido con generosidad. |

Es una muestra mínima: confirma que el circuito funciona con el modelo real, no su calidad. La calidad y la
concordancia con los docentes se miden en la fase A del piloto.

## Salvaguardas y decisiones del piloto (2026-10-12)
Las decisiones técnicas del piloto están en [`PILOTO.md`](PILOTO.md), sección 0:
- **Fases:** A → B0 → B → C.
- **Unidad:** 9.° U8, La célula.
- **Uso:** en clase, dos sesiones por semana.
- **Fidelidad del tutor:** prueba de banco y verificador obligatorio.

Lo que ya está construido:
- `salvaguardas.py`: se quitan los datos personales antes de enviar una respuesta al modelo; una señal de riesgo va al
  docente sin pasar por el modelo; el estudiante nunca ve etiquetas como «brecha».
- `sesion.barajar()`: las opciones se barajan sin perder el diagnóstico.
- `sesion.lecturas_numericas()`: acepta «50 000», «50,000» o «50000 Pa».
- `config/aprendizaje.yaml`: límites de refuerzo propios de primaria y repasos ajustados a dos sesiones por semana.

## Lo que no hace (todavía)
- No tiene validación con docentes. El tutor puede decir algo científicamente impreciso que las guardas no detectan:
  hace falta revisión humana de turnos reales (fase A del piloto) o un segundo control de fidelidad, con su costo.
- No tiene interfaz para estudiantes ni docentes: es de línea de comandos.
- No cubre una unidad completa. Hay 6 objetivos; un piloto necesita todos los de su unidad, revisados.
- No guarda datos reales de estudiantes: `data/estudiantes/` no se versiona. La propuesta de política de datos está
  en [`PILOTO.md`](PILOTO.md) y la decisión es de GOES y del MINED.
