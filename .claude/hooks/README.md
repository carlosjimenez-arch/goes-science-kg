# Harness del proyecto (Claude Code)

Las reglas de `CLAUDE.md` que dependían de recordarlas ahora las aplica Claude Code solo, en cualquier sesión.
Configuración en `.claude/settings.json`; identidad esperada en `.claude/harness.json`; subagentes en
`.claude/agents/`. Los scripts usan solo la
biblioteca estándar de Python y se prueban en `tests/test_harness.py`.

| Hook | Cuándo | Qué hace |
|---|---|---|
| `contexto_sesion.py` | al iniciar, retomar, limpiar o compactar | rama, cambios sin commit, cuenta de git frente a la de GOES, decisiones sin confirmar con el MINED y estado de las etapas internacionales |
| `guardia_bash.py` | antes de cada comando de terminal | **bloquea** leer o copiar `.env`, escribir en `data/fuentes/` o `reportes/`, commit con otra cuenta o con `ruff`/`pytest` en rojo, push forzado a main o a otro remoto; **pide aprobación** para todo gasto en Vertex (`--confirmar` de `internacional` o de `tutor`, `congelar-catalogo`, `make internacional-ia CONFIRMAR=…`) |
| `guardia_archivos.py` | antes de editar o escribir un archivo | **bloquea** `.env`, PDF, `data/fuentes/`, `reportes/` y salidas generadas (`data/grafo/`, caché de Vertex) |
| `validar_lotes.py` | al terminar un subagente de lotes (`SubagentStop`) | corre `gskg lotes validar --agente <nombre>` (las mismas reglas que cada «unir»); si la salida no pasa, **devuelve al subagente a corregirla** (hasta 3 veces; después lo deja terminar y avisa al usuario) |

Además, `permissions.deny` impide leer `.env` y editar las fuentes aunque un hook fallara. Un hook que excede su
tiempo no bloquea; por eso las guardas son rápidas y deciden de forma explícita.

## Subagentes (`.claude/agents/`)
Cada tarea de IA por lotes tiene su subagente, con su prompt, sus reglas duras y su autovalidación. Escriben solo su
`salida_*.json`; la unión (`gskg … unir-*`) la corre la sesión principal. Al terminar, `validar_lotes.py` los revisa.

| Subagente | Tarea | Lotes | Se une con |
|---|---|---|---|
| `alineador-marcos` | temas u objetivos → TIMSS 2027, TIMSS Advanced, PISA 2025 o AUSS | `data/interim/alineaciones/lotes/` | `gskg alinear unir-bachillerato` · `unir-temas` |
| `etiquetador-conceptos` | temas y objetivos de países → conceptos y prácticas | `data/interim/conceptos/lotes/`, `lotes_paises/` | `gskg conceptos unir-etiquetado` · `unir-paises` |
| `ordenador-prerrequisitos` | aristas de prerrequisito por asignatura | `data/interim/prerrequisitos/lotes/` | `gskg conceptos unir-prerrequisitos` |
| `redactor-bloques` | título y resumen de bloques temáticos | `data/interim/comunidades/` | `gskg grados resumenes` |
| `conciliador-propuestas` | propuestas frente a una malla nueva del MINED | `data/interim/propuestas/` | `gskg propuesta unir-adopcion` |
| `redactor-actividades` | actividades, dificultades y microtemas de un objetivo (nacen «propuesta_pendiente») | `data/pedagogia/lotes/` | `gskg tutor unir-actividades` |
| `experto-biologia`, `experto-fisica`, `experto-quimica`, `experto-tierra-espacio`, `psicopedagogo` | panel de expertos IA: dictámenes, réplicas del bucle y sonda ciega (spec 14) | `data/interim/panel/lotes/` | `gskg panel consolidar` · `gskg bucle cerrar-*` |
| `refutador` | revisor adversarial del bucle de fortalecimiento: impugna cada dictamen con citas literales que el código verifica en la fuente (spec 14, sección 7) | `data/interim/panel/bucle/lotes/` | `gskg bucle cerrar-impugnacion` |
| `verificador-hallazgos` | verifica hallazgos contra las fuentes (solo lectura) | — | — |

Las reglas de validación viven en el código: `src/goes_science_kg/lotes.py` reúne, por tipo de lote, la misma función
que usa su «unir». Para revisar a mano: `uv run gskg lotes validar [--tipo …|--agente …]`.

Skills: `internacional-contraste`, `calidad-grafos` y `decisiones-mined`, más las de cada fase en `.claude/skills/`.

Para cambiar la cuenta o el remoto esperados se edita `.claude/harness.json`; para desactivar una guarda, su entrada
en `.claude/settings.json` (con el acuerdo del responsable del proyecto).
