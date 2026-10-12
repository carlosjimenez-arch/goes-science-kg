# 14 · Panel de expertos IA: revisión técnica interina

> Creada el 2026-10-12, a pedido del responsable del proyecto: hoy no hay un equipo del MINED que revise. El panel
> resuelve con criterio técnico las decisiones que esperaban esa revisión, para que el proyecto avance. Sus
> dictámenes **no son confirmaciones del MINED**.

## 1. Propósito y límites
- **Qué hace.** Dictamina las decisiones pendientes de revisión: las decisiones de contenido, la división de un
  concepto, los cambios de asignatura, la capa pedagógica, los hallazgos y las propuestas curriculares. También
  asesora el piloto del tutor.
- **Qué no hace:**
  - no confirma en nombre del MINED;
  - no cambia la malla;
  - no quita temas;
  - no aprueba el uso con estudiantes. Usar el sistema con menores exige además el aval de una persona responsable
    (aprendizaje/PILOTO.md).
- **Trazabilidad.** Cada dictamen queda con:
  - quién lo dio (rol);
  - en qué ronda;
  - la decisión;
  - la justificación (70 palabras como máximo);
  - la evidencia (fuente y cita);
  - la confianza.

  En las capas queda como `dictamenes_panel` o `revision_panel`, y el estado lo dice: «dictamen del panel: … (pendiente
  de confirmar)» o «revisado_panel». Un rechazo del panel va a `observaciones`, como un rechazo del MINED: pide una
  nueva decisión y no revierte nada por sí solo.
- **Precedencia:** una decisión humana (`revisado_por`, `confirmaciones`) gana sobre el panel. El MINED puede
  confirmar o revertir cualquier dictamen con `gskg revision importar-decisiones`.

## 2. Roles (`.claude/agents/`, `config/panel.yaml`)
| Rol | Mira sobre todo |
|---|---|
| `experto-biologia`, `experto-fisica`, `experto-quimica`, `experto-tierra-espacio` | exactitud científica, progresión y prerrequisitos, ideas previas reales, alineación con el indicador de la malla, calidad de la evidencia internacional |
| `psicopedagogo` | adecuación al desarrollo, carga cognitiva, lenguaje por grado, validez y justicia de la evaluación, inclusión (DUA), bienestar, ética y datos de menores |

Las instrucciones comunes están en `prompts/panel_dictaminar.md`:
- independencia en la primera ronda;
- confianza baja cuando no se puede decidir;
- sin referencias inventadas;
- sin quitar temas;
- cada rol escribe solo su salida.

## 3. Expedientes y quién los dictamina
| Tipo | Origen | Roles | Opciones |
|---|---|---|---|
| `decision` | capas de decisión (`revision_decisiones.ARCHIVOS`) | expertos de los conceptos; además el psicopedagogo en las divisiones por nivel | aceptar · rechazar |
| `asignacion` | asignaciones de cada división de concepto | experto del concepto | aceptar · cambiar · rechazar |
| `cambio_asignatura` | `data/interim/revisiones/20*_coherencia_asignatura*.json` | expertos de la asignatura anterior y de la nueva | aceptar · rechazar |
| `contenido` | capa pedagógica en estado `propuesta_pendiente` | en secuencia: experto → psicopedagogo → experto | aprobar · corregir |
| `hallazgo` | `data/interim/panel/hallazgos.json` (hallazgos verificados de los README del contraste) | experto + psicopedagogo | respaldar · matizar · no_respaldar |
| `propuesta` | acciones «no adoptadas» de la conciliación con la V2 | experto + psicopedagogo | adoptar · adaptar · descartar |
| `piloto` | `config/panel.yaml` | psicopedagogo (asesora; decide el responsable) | recomendar |

## 4. Circuito y consolidación (`src/goes_science_kg/panel.py`)
```bash
uv run gskg panel preparar --ronda 1      # crea el estado y los lotes por rol (partidos por peso)
# subagentes del panel → salida_r1_<rol>[_k].json (el hook SubagentStop valida con gskg lotes validar)
uv run gskg panel consolidar --ronda 1    # todas las salidas válidas o nada; avanza cada expediente
uv run gskg panel preparar --ronda 2      # deliberación y segunda etapa del contenido
uv run gskg panel consolidar --ronda 2
uv run gskg panel preparar --ronda 3      # visto bueno final del experto en el contenido que corrigió el psicopedagogo
uv run gskg panel consolidar --ronda 3
uv run gskg panel aplicar                 # escribe lo resuelto en las capas, con procedencia (idempotente)
uv run gskg panel informe                 # panel/DICTAMEN.md
```
- **Paralelo** (todo menos el contenido):
  - se resuelve con unanimidad de los roles requeridos y confianza media o alta;
  - si no la hay, una ronda de deliberación con los dictámenes de los demás;
  - si sigue sin unanimidad, queda «sin consenso» para una persona.
- **Contenido**, en tres etapas:
  1. el experto revisa la exactitud y puede corregir campos editables;
  2. el psicopedagogo revisa la forma (lenguaje, carga, ítems, accesibilidad) sobre esa versión;
  3. si el psicopedagogo cambió algo, el experto da el visto bueno científico.

  Toda corrección se valida con las reglas de la capa: la clave entre las opciones, los distractores mapeados y el
  largo por grado.
- **Confianza baja** en cualquier etapa: sin consenso.

## 5. Qué queda en manos humanas
- **Lo que el panel deja sin consenso** (panel/DICTAMEN.md): lo decide una persona.
- **El aval para usar el contenido con estudiantes:** el estado `revisado_panel` es necesario, pero no suficiente.
- **La confirmación del MINED,** cuando haya un equipo: el paquete (`asignaturas/PAQUETE_MINED.md`) lleva los
  dictámenes del panel como insumo.

## 6. Riesgos
- **Sesgo compartido.** Los roles son el mismo tipo de modelo y pueden compartir sesgos. La unanimidad no equivale a
  una validación independiente; por eso todo queda con evidencia y es reversible.
- **Referencias inventadas.** Están prohibidas y se pide verificar en la fuente. Aun así, lo que el panel cite fuera
  del repositorio debe tomarse como argumento, no como prueba.
- **Costo.** Es una ronda por tipo de expediente con subagentes de Claude, sin Vertex.
