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

Los estudiantes son **simulados** (un guion fija cada respuesta) y el contenido es **propuesta pendiente**: los
recorridos prueban que el ciclo funciona sobre los datos reales del grafo, no que el estudiante aprenda más. Eso solo
lo puede mostrar un piloto con estudiantes.

## Estado del contenido pedagógico (`data/pedagogia/`)
- 55 actividades, 13 dificultades y 13 microtemas para los tres objetivos de 9.°. Todo **propuesta_pendiente**:
  redactado por el subagente `redactor-actividades`, validado por `gskg lotes validar` y sin revisión del equipo de
  Ciencias. Las dificultades no citan fuente todavía.
- Los puntos que dejaron los redactores para la revisión (datos experimentales idealizados, convención de signos de
  la primera ley, seguridad de las actividades, dificultades que juntan dos ideas) están en
  [`data/pedagogia/REVISION_PENDIENTE.md`](../data/pedagogia/REVISION_PENDIENTE.md).

## Lo que no hace (todavía)
- No conversa: el agente tutor LLM que usaría `contexto.paquete()` está diseñado pero no construido.
- No evalúa respuestas abiertas (necesita un evaluador con rúbrica, separado del tutor).
- No cubre primaria con contenido: la extensión a 2.°–8.° está diseñada, pero el contenido de primaria no existe.
- No guarda datos reales de estudiantes: `data/estudiantes/` no se versiona y la política de datos es una decisión
  pendiente del MINED.
