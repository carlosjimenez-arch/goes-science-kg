# Grafo de conocimiento para reforzamiento · 2.º–11.º

El objetivo central del proyecto es conectar qué se enseña, qué bases requiere, cómo se puede reforzar y qué
conviene mejorar en la progresión curricular. Esta entrega integra el grafo curricular y el contenido revisado
en una proyección compartida para autoría. Las relaciones existentes conservan sus fuentes y confianza.

**8.530 nodos, 26.410 relaciones y 920 rutas**, una por tema de Ciencias. Incluye los 3.303 nodos y las
18.177 relaciones originales, las 920 secuencias propuestas, sus 2.760 criterios y los 1.547 componentes
exportados al motor. Las fuentes y las entregas anteriores permanecen intactas.

## Recorrer el grafo

[Abrir el visor](revision/visor.html). Permite filtrar grado, disciplina y disponibilidad, enfocar un concepto y
ver sus bases. Las flechas representan relaciones reales de la proyección. Se muestran las actividades y
microtemas disponibles, sus permisos, los reparos de la secuencia, apoyos y alternativas sin internet.

| Grado | Acceso al grafo | Temas de Ciencias |
|---|---|---:|
| 2.º | [Grafo de segundo](revision/visor.html?grado=2) | 66 |
| 3.º | [Grafo de tercero](revision/visor.html?grado=3) | 66 |
| 4.º | [Grafo de cuarto](revision/visor.html?grado=4) | 64 |
| 5.º | [Grafo de quinto](revision/visor.html?grado=5) | 71 |
| 6.º | [Grafo de sexto](revision/visor.html?grado=6) | 56 |
| 7.º | [Grafo de séptimo](revision/visor.html?grado=7) | 87 |
| 8.º | [Grafo de octavo](revision/visor.html?grado=8) | 100 |
| 9.º | [Grafo de noveno](revision/visor.html?grado=9) | 93 |
| 10.º | [Grafo de décimo](revision/visor.html?grado=10) | 151 |
| 11.º | [Grafo de undécimo](revision/visor.html?grado=11) | 166 |

El grafo compuesto en [`0.1.0/`](0.1.0/manifiesto.json) contiene nodos, aristas, rutas y cola en JSONL,
además de metadatos y manifiesto. Se puede cargar sin los Excel ni el repositorio productor. Los diez accesos
filtran la misma entrega: comparten identidades y permiten conservar conexiones entre grados.

## Qué permite decidir y qué sigue pendiente

La proyección enlaza por campos explícitos: Secuencia→Tema, Secuencia→Criterio, Tema→Concepto/Práctica,
Concepto base→Concepto, Actividad→Objetivo/Concepto y Microtema→Concepto. El mapeo semántico de los
criterios permanece pendiente; definirlos no demuestra que evalúen todos los conceptos del tema.

Hay 228 temas con dos actividades cerradas diferentes, del grado y permitidas para autoría, para evaluar
el objetivo y reevaluarlo. Ese dato no acredita que estén completos todos sus refuerzos. Las 444 secuencias
permitidas y 476 retenidas conservan sus estados; los recursos anteriores tienen permisos independientes.
Los seis objetivos metodológicos sin concepto principal conservan sus prácticas legítimas.

La [cola para autoría](revision/cola_autoria.csv) contiene 3.266 necesidades agrupadas por tipo y clave.
Una misma ruta puede tener varias necesidades. La prioridad cuenta temas distintos afectados y sirve para
organizar revisión; no demuestra impacto educativo ni ahorro de horas. El estado es candidato a revisar,
sin recomendaciones curriculares firmes automáticas.

La disponibilidad se refiere a la entrega del motor 0.2.0. El banco del repositorio contiene más recursos:
827 actividades y 33 microtemas, frente a 785 y 24 exportados. Antes de crear contenido conviene comprobar
si falta redactarlo, revisarlo, adaptarlo al grado o incorporarlo a una entrega nueva.

## Ruta para llenar vacíos y proponer una progresión mejor

1. Conciliar el banco con lo exportado: recuperar candidatos ya existentes, como los de quinto y séptimo,
   mediante revisión y una nueva versión, sin sustituir este corte.
2. Revisar los caminos conceptuales discutibles antes de anticipar contenidos. El caso de propagación asexual
   de sexto y la etiqueta de biotecnología conserva una observación semántica explícita.
3. Elaborar sondeos, microtemas, prácticas y comprobaciones por grado, empezando por las bases de mayor
   alcance y los grados sin banco: segundo, cuarto, sexto y octavo. Usar especialistas, psicopedagogía y
   refutación sobre cada candidata exacta.
4. Mapear los criterios a conceptos o prácticas con evidencia de las tareas y comprobar diagnóstico y
   reevaluación con actividades distintas. La respuesta del alumno se incorpora después, en una capa individual.
5. Evaluar propuestas de progresión contra los marcos y referentes, con sus consecuencias temporales explícitas.
   El ensayo docente y la decisión curricular institucional conservan su autoridad propia.

Las inferencias de prerrequisito orientan hipótesis. La ausencia de una base en el grafo no prueba una
dificultad de un estudiante. La autoría compartida no incluye datos personales y el uso en aula permanece
deshabilitado. Los fallos del tutor original señalados en la auditoría requieren corrección y pruebas propias;
esta entrega construye el soporte compartido del refuerzo.

## Reproducir y consultar

```bash
uv run gskg grafo-refuerzo construir --destino /tmp/grafo-refuerzo
uv run gskg grafo-refuerzo validar /tmp/grafo-refuerzo
uv run gskg grafo-refuerzo consultar NM26-G10-FIS-U4-4.1 --carpeta /tmp/grafo-refuerzo
uv run python scripts/preparar_visor_grafo_refuerzo.py /tmp/grafo-refuerzo /tmp/visor-refuerzo
```

Se verifican las huellas y el orden de los registros contra el manifiesto fuente, la integridad de los extremos,
los permisos y la reconstrucción completa de la proyección. La publicación es inmutable; cambiar código,
política o fuente requiere otra versión o destino. Los archivos HTML y CSV quedan fuera de la versión inmutable.

Auditorías: [estructura](../../data/interim/grafo_refuerzo/auditoria_estructura.json),
[rutas y tutor](../../data/interim/grafo_refuerzo/auditoria_rutas.json),
[revisión psicopedagógica de la proyección](../../data/interim/grafo_refuerzo/auditoria_proyeccion_psico.json).
Diseño: [spec 18](../../specs/18_grafo_para_reforzamiento.md).

La aceptación completa pasó **365 pruebas**, incluidas 34 nuevas de la proyección. Los cinco ciclos y los
cambios que detectaron están en [VALIDACION_5_CICLOS.json](VALIDACION_5_CICLOS.json), y el resultado completo
en [PRUEBAS.txt](PRUEBAS.txt). El [visor se comprobó en navegador](revision/VERIFICACION_NAVEGADOR.json):
filtros combinados, objetivos metodológicos, alerta semántica, gráfico, consignas, apoyos y alternativa sin internet.
La versión publicada coincide por bytes con la candidata aprobada.
