# 00 · Visión y alcance

## Problema
El MINED está rediseñando las mallas de Ciencias (2.° a 11.°). La V3 vigente (2026-10-13) contiene
935 temas, de los cuales 920 están en el alcance de Ciencias. Existe un análisis histórico de cobertura
(`reportes/cobertura_curricular/`, basado en la V1 de 1.260 temas) que dice **qué cubre
y qué no** frente a TIMSS 2027, TIMSS Advanced y PISA 2025, y **cuándo** enseña El Salvador
cada objetivo comparado con Uruguay, Colombia y Singapur.

Ese análisis responde «¿cómo estamos?». No responde «¿cómo debería ser?». Para proponer una
curricularización mejor hace falta saber, además, **qué se necesita saber antes de qué**
(prerrequisitos), **cómo lo secuencian los países con mejor desempeño** y **qué cambio mínimo**
lleva la malla a esa referencia sin romper el presupuesto de horas.

## Objetivo
Construir un **grafo de conocimiento de Ciencias** que:

1. Represente la malla de El Salvador (temas → grado → asignatura).
2. Use como **pivote** los marcos internacionales: TIMSS 2027 (4.° y 8.°), TIMSS Advanced
   (Física) y PISA 2025. Todo currículo se alinea contra el pivote, nunca país contra país.
3. Integre los currículos de **otros países**, priorizando a los de mejor desempeño en Ciencias
   y a los referentes regionales (`config/referentes.yaml`).
4. Agregue una capa de **conceptos y prerrequisitos** con evidencia.
5. Permita **proponer, por asignatura**, una malla mejorada y justificada: qué agregar, mover,
   fusionar o quitar, en qué grado y por qué. Cada propuesta debe traer su evidencia.
6. Sostenga una **capa de contenido para autoría y un motor independiente**: identidades estables,
   componentes trazables, revisión por componente y entregas versionadas (specs 13–16). El catálogo
   curricular y las propuestas institucionales mantienen su autoridad propia; una revisión IA no aprueba clases.

## Alcance
- **Asignaturas:** Biología, Física, Química y Ciencias de la Tierra y del Espacio
  (`asignaturas/`). Los temas técnicos de «Ciencia y Tecnología» quedan fuera y se enlazan
  con `goes-techonoly-kg`.
- **Grados:** 2.° a 11.° (Ciencias de la Tierra, 2.° a 9.°).
- **Usuarios:** equipo GOES (diseño curricular), autores y revisores de contenido y equipo de Ciencias del MINED
  (validación curricular). El uso con docentes y estudiantes exige los hitos de revisión y piloto de la spec 16.

## Fuera de alcance (por ahora)
- Publicar planes, materiales o evaluaciones como aprobados para aula sin verificación humana y prueba temporal.
  La elaboración y revisión de propuestas pedagógicas sí forma parte del alcance ampliado (specs 13–16).
- Datos personales de estudiantes en el grafo o las entregas compartidas. El prototipo de la spec 13 mantiene
  cualquier estado individual en una capa separada; el contrato inicial del motor no lo transporta.
- Decidir la malla final. El grafo **propone con evidencia** y el MINED decide.

## Criterios de éxito
- Cada asignatura tiene en `asignaturas/<asignatura>/` su ficha, su análisis de brechas y una
  propuesta con evidencia trazable a documento y página.
- `gskg grafo validar` termina sin errores. Toda inferencia de IA trae confianza,
  justificación y versión.
- Al menos 4 países de alto desempeño, además de los 3 regionales, alineados al pivote.
- La entrega para el motor se valida sin los Excel del productor, se importa sin duplicar registros y permite
  activar o revertir una versión. Distingue consulta, autoría asistida y habilitación de aula.
