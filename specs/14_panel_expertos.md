# 14 · Panel de expertos IA: revisión técnica interina

> Creada el 2026-10-12, a pedido del responsable del proyecto: hoy no hay un equipo del MINED que revise. El panel
> resuelve con criterio técnico las decisiones que esperaban esa revisión, para que el proyecto avance. Sus
> dictámenes **no son confirmaciones del MINED**.
>
> **Primera revisión (2026-10-12):**
> - 510 expedientes en 3 rondas, con 32 subagentes;
> - 493 resueltos y 17 sin consenso, que quedan para una persona;
> - lo resuelto ya está aplicado en las capas.
>
> Resultados en `panel/README.md` y `panel/DICTAMEN.md`.

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
| `clase_incierta` | conceptos «inciertos» del contraste de 2.°–8.° | experto de la disciplina, con verificación en la fuente | faltante · tardío · posterior · adelantado · sin_referente · alineado (lo resuelto entra a `revisiones.json` del tramo) |

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
# Un grupo de tipos que corre aparte lleva su serie de lotes, para no mezclarse con las rondas principales:
uv run gskg panel preparar --ronda 1 --tipos clase_incierta --serie inc
uv run gskg panel consolidar --ronda 1 --serie inc
# y las rondas principales se preparan con --tipos sin ese grupo (si no, lo pendiente de la serie entra en ellas)
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
  una validación independiente; por eso todo queda con evidencia y es reversible, y pasa por el bucle de la
  sección 7.
- **Referencias inventadas.** Están prohibidas y se pide verificar en la fuente. Aun así, lo que el panel cite fuera
  del repositorio debe tomarse como argumento, no como prueba.
- **Costo.** Es una ronda por tipo de expediente con subagentes de Claude, sin Vertex.

## 7. Bucle de fortalecimiento (`src/goes_science_kg/bucle.py`, `gskg bucle …`)
> Agregado el 2026-10-12, a pedido del responsable del proyecto: fortalecer los hallazgos del panel con un diseño de
> bucles agénticos antes de llevarlos al MINED o a un estudiante.

### 7.1 Por qué
La unanimidad del panel no basta: los cinco roles son el mismo tipo de modelo. Antes del bucle, el código midió la
evidencia de los 360 dictámenes resueltos que afirman algo sobre las fuentes (todo menos el contenido y el piloto):
- solo 91 (25 %) traían una cita que está literal en una fuente primaria;
- 263 citaban una fuente que existe, pero con una paráfrasis o una traducción que no se puede comprobar;
- 6 decisiones no tenían ninguna fuente primaria (solo criterio o informes del proyecto);
- 2 citaban algo que no existe: una página fuera del documento y un tema que no está en la malla;
- 165 evidencias eran circulares: el README del contraste, el propio contraste u otro dictamen.

### 7.2 Diseño: tres bucles anidados
**Bucle interno: agente ↔ validador, segundos.** El revisor adversarial (`refutador`) escribe su salida, y el hook
SubagentStop la devuelve a corregir si una cita literal no aparece en la fuente que nombra (hasta 3 veces). El
agente se corrige solo antes de terminar, con `gskg bucle cita "<fuente>" "<cita>"`.

**Bucle medio: impugnación ↔ réplica, una vuelta por corrida.**
```
         resuelto por el panel
                  │
   anclaje (código) ──► nivel: anclado · ubicado · sin fuente primaria · fuente inexistente
                  │
   ┌──────────────┴───────────────┐
   impugnación (refutador)        sonda ciega (muestra, mismos roles, sin ver la resolución)
   └──────────────┬───────────────┘
   el código verifica las citas: solo la contraevidencia anclada reabre; una discrepancia de la sonda también
                  │
     sostenida ◄──┴──► impugnada ──► réplica del panel (unanimidad → mantiene o cambia;
                                       sin unanimidad tras deliberar o confianza baja → una persona)
                                             │
                               cambiada ─────┴──► vuelta siguiente: solo lo que cambió se vuelve a impugnar
```
**Bucle externo: de los errores a las reglas, entre corridas.** Cada impugnación lleva un `patron` del error
(`config/panel.yaml`, `bucle.patrones`). Un patrón que se repite se convierte en una regla del código o del prompt,
como pasó antes con la «Extension Part» en cursiva de HK (spec 12) o con la clave más larga de los ítems (spec 13).

### 7.3 Reglas de diseño
1. **El modelo propone y el código decide.** Toda cita del bucle es literal, en el idioma de la fuente, y el código
   la busca en la fila de la malla, el objetivo del país o la página del PDF. Es la misma idea del evaluador y del
   verificador de fidelidad (spec 13). El texto se normaliza (sin acentos, espacios ni mayúsculas), se aceptan
   tramos separados por «…» y se miran hasta 8 páginas vecinas, porque la numeración impresa no es la posición en el
   PDF.
2. **Asimetría de la prueba.** Para reabrir un expediente hace falta contraevidencia anclada, con confianza media o
   alta. En el contenido basta un error concreto con su corrección válida. Para sostenerlo hay que haber buscado: el
   refutador aporta anclas literales a favor, y lo que no tiene ninguna queda frágil.
   Una revisión adversarial con confianza baja no reabre por sí sola, pero tampoco certifica: queda frágil hasta
   conseguir evidencia suficiente, también en contenido pedagógico y refuerzos.
3. **Independencia por postura.** El refutador no es miembro del panel y se le mide por los errores reales que
   encuentra. La sonda es ciega: no ve la resolución, ni los dictámenes, ni el informe.
4. **Convergencia acotada.** Una vuelta impugna, replica y aplica. La siguiente solo vuelve a impugnar lo que cambió.
   El bucle se detiene si una vuelta no cambia nada o al llegar a `vueltas_max` (2). Lo que cambió en la última
   vuelta queda frágil: no se volvió a probar.
5. **Escalamiento a una persona**, como en el panel: una réplica sin unanimidad tras deliberar, o con confianza baja,
   queda «sin consenso».
6. **Trazable y reversible.** Todo queda en `data/interim/panel/estado.json`:
   - por expediente: `bucle.anclaje`, `bucle.vueltas[]` (impugnación, sonda y réplica), `bucle.anclas`, `bucle.solidez`;
   - por resolución reemplazada: `historial_resoluciones`.

   `gskg panel aplicar` vuelve a aplicar lo que cambió:
   - retira la observación del panel si ya no rechaza;
   - devuelve una asignación a su versión original;
   - actualiza la clase del contraste.

   Lo humano no se toca. Las capas guardan la solidez en el registro del panel, y el CSV para el MINED la muestra en
   el estado («dictamen del panel: aceptar, sólido»).

### 7.4 Solidez
| Etiqueta | Significa |
|---|---|
| **sólido** | sobrevivió a la impugnación sin contraevidencia anclada y tiene al menos una cita literal verificada en una fuente primaria (en contenido: el revisor adversarial no encontró errores) |
| **respaldado** | sobrevivió, pero su fuente solo está ubicada (paráfrasis o traducción), o la réplica lo mantuvo frente a contraevidencia anclada, o la sonda ciega dictaminó otra opción que la resolución **vigente** (inestable). Si la réplica corrigió el dictamen y llegó a lo mismo que la sonda, eso corrobora |
| **frágil** | sin fuente primaria verificable, con una fuente inexistente, o cambiado en la última vuelta sin volver a impugnarse |
| **sin consenso** | lo decide una persona |

Antes de llevar un hallazgo al MINED como recomendación, lo frágil necesita una fuente primaria.

### 7.5 Circuito
```bash
uv run gskg bucle anclar                       # sin IA: nivel de anclaje de cada dictamen
uv run gskg bucle impugnar --vuelta 1          # lotes del refutador → data/interim/panel/bucle/lotes/
uv run gskg bucle sonda --vuelta 1             # muestra ciega (63 de 360 con la semilla 2026) → lotes c1 del panel
# subagentes: refutador (lote_b1_*) y roles del panel (lote_c1_*)
uv run gskg bucle cerrar-impugnacion --vuelta 1
uv run gskg bucle replicar --vuelta 1 --paso 1 # réplica (ronda 11); paso 2: deliberación o psicopedagogo; paso 3: experto
uv run gskg bucle cerrar-replica --vuelta 1 --paso 1
uv run gskg bucle impugnar --vuelta 2          # solo lo que cambió
uv run gskg panel aplicar && uv run gskg panel informe   # reaplica lo cambiado; DICTAMEN.md con la solidez
uv run gskg bucle cita "<fuente>" "<cita>"     # ¿está literal? (lo usan los agentes)
uv run gskg bucle fuente "<fuente>"            # el texto en que se busca
# Expedientes nuevos (p. ej. clases inciertas que aparecen después): una serie aparte, con sus propias vueltas.
uv run gskg bucle impugnar --vuelta 1 --serie inc9      # lotes b1-inc9_*; la vuelta 2 solo toma los cambios de la serie
uv run gskg bucle replicar --vuelta 1 --paso 1 --serie inc9   # lotes r11-inc9_*
```

### 7.6 Límites
- **El refutador también es un modelo del mismo tipo.** La independencia es de postura y de información (ciega), no de
  modelo. Un segundo proveedor de modelo como refutador sería más fuerte, pero gasta fuera de Claude y hay que
  aprobarlo.
- **Una cita literal prueba que la fuente dice eso**, no que la lectura del panel sea la correcta. Por eso la réplica
  la pondera y lo contestado queda «respaldado», no «sólido».
- **Las traducciones no se anclan.** Hay que citar en el idioma de la fuente. Las afirmaciones de ausencia («no
  aparece en todo el marco») tampoco se anclan: quedan como paráfrasis ubicada.
- **La sonda es una muestra.** Su acuerdo estima la estabilidad por tipo; no garantiza cada expediente.

### 7.7 Primera corrida (2026-10-12 y 13)
- **Vuelta 1:**
  - el refutador revisó 486 dictámenes y aportó 820 anclas literales;
  - se reabrieron 35;
  - la sonda coincidió en 56 de 63;
  - la réplica cambió 24 y mantuvo 11, todos por unanimidad.
- **Vuelta 2:** de los 24 cambios, 21 se sostuvieron; 3 se reabrieron y la réplica los mantuvo. Con eso convergió.
- **Solidez:** de los 486 resueltos, 468 quedan sólidos, 17 respaldados y 1 frágil (cita a una página inexistente);
  17 siguen sin consenso desde el panel original.
- **Bucle externo:** ocho correcciones al verificador y al circuito salieron de agentes que no pudieron anclar
  evidencia legítima (`panel/bucle/README.md`). Quedan seis problemas de método del contraste para el responsable.
- **Costo y robustez:** 40 subagentes de Claude completados, más unos 30 intentos cortados, sin Vertex. Hubo tres
  cortes por límites de uso o de sesión. El bucle se retomó sin perder trabajo, porque cada salida se valida y se
  consolida por lote. Desde entonces corre en olas de 6 y con commits por etapa.
- **Revisión crítica (2026-10-13):** la sonda se comparaba con la resolución original y no con la vigente, así que
  marcaba como inestables 3 casos en que la réplica había llegado a lo mismo que la sonda. Además, los snapshots por
  grado contaban tres veces los objetivos de otros países. Las dos cosas están corregidas y probadas, y los totales
  publicados («466») se corrigieron.

### 7.8 Series inc9 e inc9b (2026-10-13)
- **Qué se revisó:** las 59 clases inciertas de 9.°–11.° que decidió el panel: 55 de la doble lectura y 4 que
  aparecieron al sumar el antecedente de 2.°–8.°.
- **Vuelta 1:** el refutador reabrió 9 y la réplica cambió 8.
- **Vuelta 2:** sostuvo los 8 cambios. Quedan 58 sólidos y 1 respaldado.
- **Bucle externo:**
  - el refutador de Física vio que la secundaria baja de HK no contaba. Desde ahora el antecedente suma el núcleo de
    2.°–8.° de los demás países (`consenso.ANTECEDENTE_2_8`);
  - los dos errores de criterio del panel (conceptos vecinos contados como núcleo y la regla del umbral usada como
    comodín) pasaron a ser reglas de `prompts/panel_dictaminar.md`;
  - se corrigió un bug de `panel aplicar`: la solidez de las clases de 9.°–11.° se buscaba en las revisiones de
    2.°–8.°.
