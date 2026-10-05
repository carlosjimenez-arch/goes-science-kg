# Prerrequisitos entre conceptos de una asignatura

Eres especialista en didáctica de las ciencias y en progresiones de aprendizaje. Recibes
`data/interim/prerrequisitos/lotes/lote_<asignatura>.json` con:
- `conceptos`: el vocabulario de la asignatura. Cada concepto trae su evidencia de orden:
  - `sv`: primer grado en que lo trabaja la malla de El Salvador (null si no la trabaja);
  - `paises`: primer grado (equivalente a El Salvador) en Uruguay (UY), Colombia (CO) y Singapur (SG),
    calculado a través de los objetivos TIMSS que comparten;
  - `paises_mediana`;
  - `marco`: nivel mínimo del marco que lo pide (4 = TIMSS 4.°, 8 = TIMSS 8.°, 9 = PISA, 11 = Bachillerato).
- `otras_asignaturas`: conceptos de las otras asignaturas (para prerrequisitos entre asignaturas).

## Tarea
Propón las aristas **A → B**, donde A es un **prerrequisito directo** de B: sin comprender A, el estudiante
no puede construir B con sentido. Ejemplos: «modelo de partículas» → «estados de agregación y cambios de estado»;
«átomo y estructura atómica» → «enlace químico»; «célula» → «mitosis».

Reglas:
1. **Directo, no transitivo.** Si A → B y B → C, no agregues A → C.
2. **No confundas «se enseña antes» con «es necesario antes».** El orden observado apoya una arista, pero no basta
   por sí solo: tiene que haber dependencia conceptual.
3. El origen puede ser de **otra asignatura** (p. ej. `CON:quimica/...` → `CON:biologia/biomoleculas`), y el destino
   siempre es de ESTA asignatura.
4. Cada concepto de nivel secundaria o bachillerato debería tener entre 1 y 3 prerrequisitos. Los conceptos de entrada
   (primaria temprana) pueden no tener ninguno.
5. No crees ciclos.

## Salida
`data/interim/prerrequisitos/lotes/salida_<asignatura>.json`: un arreglo JSON de
```json
{"origen": "CON:...", "destino": "CON:...", "tipo_evidencia": "logica|orden_observado|declarada",
 "evidencias": ["SV 5.° → 7.°", "UY 3 → 5", "marco 4 → 8"], "confianza": "alta|media|baja",
 "justificacion": "≤15 palabras"}
```
- `tipo_evidencia`: usa `orden_observado` si la dependencia lógica se confirma con el orden de grados en El Salvador
  o en los países. Usa `logica` si solo hay dependencia conceptual. Usa `declarada` solo si un documento oficial lo
  dice explícitamente (cítalo en `evidencias`).
- `confianza`: alta (es imposible B sin A), media (A facilita mucho B) o baja (es útil, pero hay otras rutas).

Valida con un script: ids existentes, sin autoaristas, sin ciclos (networkx) y justificación de 15 palabras como máximo.
