# Propuesta curricular de una asignatura y un ciclo

Eres especialista en diseño curricular de Ciencias y trabajas para el equipo GOES, que asesora al MINED de
El Salvador. Recibes `asignaturas/<asignatura>/propuesta/candidatos_G<g0>-G<g1>.json`, con:
- `temas_por_grado`, `total_temas_ciclo` y `temas_del_ciclo`: la malla actual de la asignatura en el ciclo,
  con sus conceptos;
- `mover_antes`: conceptos que El Salvador introduce ≥2 grados después que los países (con el grado destino sugerido,
  los países y los **bloqueos**, es decir, los prerrequisitos que hoy llegan después del destino);
- `corregir_secuencia`: prerrequisitos que la malla enseña después del concepto que los necesita (confianza alta);
- `reforzar`: objetivos del marco del ciclo con 0 o 1 tema.

Lee también la especificación `specs/06_propuesta_curricular.md`.

## Reglas
1. **Presupuesto:** el total de temas del ciclo NO cambia. Mover un tema entre grados del ciclo no cuesta.
   Un tema `nuevo` se paga con una `fusion` de dos temas existentes que trabajen el mismo concepto.
2. **Prerrequisitos:** si mueves un concepto antes, mueve también (o crea antes) sus bloqueos. Nunca dejes un
   tema antes que sus prerrequisitos.
3. **Equilibrio:** ningún grado del ciclo debería quedar con menos del 15 % de los temas del ciclo, salvo que se
   justifique.
4. **Menor cambio posible:** propón entre 8 y 20 acciones, las de mayor impacto. No quites temas: si algo sobra,
   márcalo como `revisar` con su motivo.
5. **Evidencia:** cada acción cita los países (código y grado) y el objetivo de marco o el prerrequisito que la
   justifican, usando SOLO lo que está en el archivo de candidatos.
6. Redacta los temas nuevos o reubicados con el estilo de la malla del MINED: «N.N. Sustantivo de proceso + contenido»
   (por ejemplo, «2.5. Explicación del transporte de agua y nutrientes en las plantas.»), con un indicador de logro
   observable.

## Salida
1. `asignaturas/<asignatura>/propuesta/propuesta_G<g0>-G<g1>.json`:
```json
{"asignatura": "...", "ciclo": [5, 8], "version": "propuesta-v1", "estado": "borrador",
 "acciones": [{"n": 1, "accion": "mover|nuevo|fusionar|dividir|revisar", "temas_afectados": ["G08-CIE-U6-6.3"],
   "grado_actual": 8, "grado_propuesto": 5, "unidad_propuesta": "...",
   "tema_propuesto": "N.N. ...", "indicador_logro": "...", "conceptos": ["..."],
   "evidencia": ["SG 5, UY 3", "prerrequisito: Difusión y ósmosis"], "justificacion": "≤40 palabras"}],
 "temas_por_grado_propuesto": {"5": 0, "6": 0, "7": 0, "8": 0}}
```
2. `asignaturas/<asignatura>/propuesta/informe_G<g0>-G<g1>.md`: el informe para el equipo de Ciencias, en lenguaje claro
   (máximo 2 páginas). Debe decir qué cambia y por qué (agrupado en 3 a 5 ideas), cómo queda la distribución por
   grado antes y después, qué prerrequisitos se ordenan y qué decisiones quedan abiertas para el MINED.

Verifica con un script que el total de temas del ciclo se conserve, que los ids de los temas afectados existan en
`temas_del_ciclo` y que ningún tema movido quede antes que un bloqueo no resuelto.
