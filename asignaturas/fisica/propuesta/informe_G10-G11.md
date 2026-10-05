# Propuesta de Física, 10.° y 11.° (borrador)

Versión `propuesta-v2`, estado **borrador** hasta la revisión del equipo de Ciencias del MINED.
Detalle de cada acción, con su evidencia, en `propuesta_G10-G11.json`.

## En resumen
Proponemos **10 acciones**: 2 movimientos y 8 reformulaciones (`revisar`). No hay temas nuevos ni fusiones
ejecutadas. El total del ciclo se mantiene en **267 temas** y no se quita ninguno.

La malla de Bachillerato ya cubre los 23 objetivos de TIMSS Advanced 2015 (TA15). Por eso la propuesta es pequeña:
- **ordena** dos secuencias de óptica que hoy van al revés y una de física cuántica (cuantización antes del fotón);
- **señala** dónde se repite lo de 8.° y 9.° o se profundiza más de lo que pide TA15.

Ahí está el tiempo que el MINED puede recuperar si decide fusionar.

## Qué cambia y por qué

**1. La óptica ondulatoria va después de las ondas (acción 1).**
- Hoy la interferencia, la difracción y la polarización de la luz (G10 16.2 y 16.3) se estudian en 10.°.
- La superposición de ondas que las explica llega en 11.° (unidad 5).
- Los dos temas pasan a la unidad 18 de 11.° (*Naturaleza ondulatoria de la luz*): uno la abre de forma
  experimental y otro la cierra con las aplicaciones.

**2. Las aplicaciones de las imágenes van después de las lentes (acción 2).**
- El tema G10 16.12 (ojo e instrumentos) pasa a la unidad 17 de 11.°.
- Se ubica entre la ecuación de las lentes (17.5) y el ojo (17.6).

**3. Etiquetas que no corresponden y una idea que se adelanta (acciones 3, 4, 9 y 10).**
- **G10 16.7** está etiquetado como dualidad onda-partícula, pero su indicador trata del modelo de rayos. Se
  redacta como *modelo de rayos* y la dualidad queda en 11.° (15.2), después del fotón.
- **Conductores y aislantes** (G11 6.3) aparece como candidato a bajar a 10.° (CO 4, SG 5). **No se mueve.**
  - En 10.° no hay electricidad.
  - El retraso real está en primaria; las propuestas de 2.°–4.° y 5.°–8.° ya lo resuelven.
  - En 11.° el tema pasa a explicar la diferencia con el modelo de electrones libres.
- **Cuantización de la energía (acción 9).** Química de 10.° (G10 3.5, espectros de emisión) ya usa el fotón,
  pero la hipótesis de Planck llega en 11.° (G11 15.3). El cuerpo negro ya se estudia en 10.° (G10 13.3):
  ese tema se cierra con una introducción cualitativa a la hipótesis de Planck. G11 15.3 la formaliza.
- **G10 5.6 (acción 10)** clasifica las fuerzas en interacciones fundamentales, pero está etiquetado como
  *modelo estándar de partículas*. Se acota a las cuatro interacciones, sin partículas mediadoras, y la acción retira
  esa etiqueta (el MINED la valida). El modelo estándar queda en 11.° (20.5), después del núcleo (20.1 y 20.2).

**4. Dónde se puede liberar tiempo (acciones 5 a 8, todas `revisar`).** El análisis previo encontró exceso de
ondas y de física moderna. El objetivo *Reflexión, refracción, interferencia y difracción* (TA-O1.4) tiene
39 temas principales, el más cargado del marco.
- **Óptica de 10.° (acción 5).**
  - La dispersión ocupa tres temas (reconocer, experimentar, aplicar) que caben en uno.
  - Las imágenes se calculan en 10.° y otra vez en 11.°. Proponemos que 10.° quede en lo cualitativo.
- **Fluidos y termodinámica de 10.° (acción 6).** Repiten lo de 9.°:
  - empuje (G09 1.1, 1.2), viscosidad y ley de Stokes (G09 1.10 a 1.12);
  - procesos en diagramas p-V (G09 2.4, 2.5) y primera ley (G09 2.8).
  - Los temas de 10.° deben partir de ese trabajo. Dos (11.11 y 15.4) pueden integrarse en temas vecinos.
- **Oscilaciones y ondas de 11.° (acción 7).** 8.° ya mide el período del péndulo, grafica la energía del
  oscilador y clasifica las ondas (G08 3.3 a 3.10). La clasificación de ondas (G11 3.1) puede reducirse a un repaso.
- **Física moderna de 11.° (acción 8).**
  - La unidad 23 repite la relatividad de la unidad 19 y la radiación ionizante de la unidad 21.
  - La simultaneidad y la contracción de longitudes pasan a la unidad 19.
  - Los dos temas de radiación ionizante se integran en uno.
  - Las métricas (23.1) y el cálculo con Heisenberg (15.7) quedan en nivel cualitativo, porque superan TA15.

Si el MINED acepta todas las integraciones sugeridas, se liberan unos **8 a 10 temas** del ciclo sin perder
cobertura de TA15.

## Distribución por grado

| Grado | Antes | Después | % del ciclo (después) |
|---|---|---|---|
| 10.° | 121 | 118 | 44,2 % |
| 11.° | 146 | 149 | 55,8 % |
| **Total** | **267** | **267** | |

Las reformulaciones no cambian estos números. Si se aprueban las integraciones, bajarían sobre todo en 11.°.

## Prerrequisitos que se ordenan
Un script de validación confirma:
- el total de 267 temas;
- que todos los ids existen;
- que ningún tema movido queda antes de un bloqueo.

El archivo de candidatos regenerado tiene tres secuencias de confianza alta:
- superposición de ondas → interferencia de la luz: **corregida** (acción 1);
- cuantización de la energía → fotón y efecto fotoeléctrico: **corregida** (acción 9);
- núcleo atómico → modelo estándar de partículas: **corregida** (acción 10, que retira la etiqueta secundaria
  de G10 5.6; el MINED valida ese retiro).

La secuencia *lentes delgadas → ojo e instrumentos ópticos* ya no aparece en el grafo; la acción 2 se mantiene
porque el orden sigue siendo el correcto. Con la acción 3 también se mantiene *fotón → dualidad*.

**Orden dentro de 11.°:** la unidad 18 (interferencia de la luz) debe enseñarse **antes** de la unidad 15
(*La luz*), porque la dualidad onda-partícula necesita la interferencia. La secuencia queda así:
unidad 5 (superposición) → unidad 18 → unidad 15.

## Qué cambió con el triaje de conceptos
- El triaje añadió 14 conceptos; en Física de 10.° y 11.° solo entra uno: *Movimiento circular uniformemente
  acelerado* (G10 9.2, 9.3, 9.5 y 9.7). Sus dos prerrequisitos sugeridos (movimiento circular y aceleración
  constante) se enseñan antes y no generan errores de secuencia.
- Los dos errores nuevos no vienen de aristas del triaje (ambas aristas son de confianza alta y correctas).
  Vienen de etiquetas secundarias del reetiquetado: el fotón en Química G10 3.5 y el modelo estándar en Física G10 5.6.
- Con esta versión, la simulación pasa de 3 a **0** errores de secuencia de confianza alta en el ciclo.
- Los candidatos a adelantar ahora incluyen también *Ley de Ohm* y *Ondas de radio y telecomunicaciones* (de 11.° a
  10.°). No se mueven, por la misma razón que conductores y aislantes: 10.° no tiene unidad de electricidad.

## Decisiones abiertas para el MINED
1. **Integraciones:** ¿se aprueban las integraciones de las acciones 5 a 8? Cada una libera tiempo, pero cambia
   la redacción de unidades vigentes.
2. **Uso del tiempo liberado:** según nuestro conteo, *Estructura atómica y espectros de emisión y absorción*
   (TA-O2.1) tiene un solo tema principal en el ciclo. Es un buen destino para lo que se libere.
   El archivo de candidatos no lo marca como débil, así que conviene confirmarlo.
3. **Dato que conviene verificar:** el grafo indica (confianza media) que *Ondas electromagnéticas* y
   *Refracción de la luz* (G10 16.1 y 16.8) necesitan *Rapidez de la luz*, que el ciclo ubica en 11.° (G11 15.1,
   experimentos de Rømer y Fizeau). La óptica de 10.° solo necesita saber que la luz cambia de rapidez al cambiar
   de medio, no esas mediciones históricas. No se propone mover nada por ese dato.
4. **Óptica geométrica en dos grados:** proponemos que 10.° quede en lo cualitativo y 11.° haga los cálculos.
   La otra opción es pasar toda la óptica a 11.°, pero 11.° quedaría con más de 155 temas.
5. **Ciencias del espacio (unidad 22, 9 temas)** y **modelo estándar (G11 20.5)** van más allá del núcleo de TA15.
   No se tocan en esta versión, pero son candidatos a revisar si hace falta más tiempo.
6. **Etiquetas:** validar que se retire *Modelo estándar de partículas* de G10 5.6, como propone la
   acción 10. Para el equipo de Química: G10 3.5 usa el fotón; conviene que su redacción remita a la
   cuantización o que se coordine con G10 13.3 de Física (acción 9).
