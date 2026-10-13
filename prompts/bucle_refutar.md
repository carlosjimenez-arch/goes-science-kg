# Impugnar los dictámenes del panel (bucle de fortalecimiento, spec 14, sección 7)

El panel de expertos IA resolvió estos expedientes por unanimidad. Pero sus miembros son el mismo tipo de modelo y
pueden equivocarse juntos, citar de memoria o apoyarse en los informes del propio proyecto en lugar de la fuente.
Tu trabajo es **intentar derribar cada dictamen con evidencia de las fuentes**. Si no puedes, aportas la cita
literal que lo sostiene. Un dictamen que sobrevive a tu búsqueda queda más fuerte; uno que cae se corrige antes de
llegar al MINED o a un estudiante.

## Entrada
`data/interim/panel/bucle/lotes/lote_b<k>_refutador_<disciplina>[_n].json`:
- `disciplina`: la ciencia del lote. Usa los criterios de `.claude/agents/experto-<disciplina>.md` (sección «Tus
  criterios»), pero tu postura es la de un revisor externo escéptico, no la de un miembro del panel.
- `expedientes`: cada uno con `id`, `tipo`, `opciones`, `datos` (la evidencia reunida para el panel), `resolucion`
  (lo que decidió el panel), `fundamentos` (los dictámenes que la sostienen, con su evidencia) y `anclaje` (lo que el
  código ya verificó: cuántas citas están literales en una fuente primaria, cuántas son paráfrasis, internas o solo
  argumentos). En contenido, `elemento_vigente` y `campos_editables`.

## Cómo impugnar
1. **Pregúntate qué tendría que ser cierto para que el dictamen estuviera equivocado**, y búscalo en la fuente. Los
   errores que ya aparecieron en este proyecto son la mejor guía:
   - un objetivo electivo o de ampliación contado como núcleo (la «Extension Part» de HK va en cursiva);
   - la V2 lo enseña en otra asignatura, en otro grado o con otro nombre;
   - una etiqueta secundaria suelta que no representa el objetivo;
   - el grado del país mal llevado a SV;
   - la página no dice lo que se afirma;
   - el panel se apoyó en el README del contraste y no en la fuente (evidencia circular);
   - el número de países no alcanza para la clase;
   - en contenido: errores científicos, una clave discutible, un distractor que en realidad es correcto, una pista en
     la forma o un lenguaje que no corresponde a la edad.
2. **Ve a la fuente primaria**: la fila de la malla (`uv run gskg bucle fuente "TEMA:<id>"`), el objetivo del país
   (`uv run gskg bucle fuente "<id del objetivo>"`) o la página del PDF (`uv run gskg bucle fuente "<archivo.pdf> p. N"`;
   la página es la posición en el PDF; el código también mira hasta 8 páginas vecinas). Para buscar en toda la malla:
   `uv run python -c "from goes_science_kg.ingesta.mallas import extraer; ..."`. Los PDF se leen con `pypdf`.
3. **Cita literal, en el idioma de la fuente.** Cada cita va como `{fuente, cita_literal, dice}`:
   - `fuente`: `TEMA:<id>`, el id del objetivo del país o `<archivo.pdf> p. N`;
   - `cita_literal`: copiada tal cual de la fuente, de 4 a 30 palabras (en chino, japonés o coreano, 8 caracteres o
     más). Puedes saltar texto con «…»;
   - `dice`: qué significa, en español, en una línea.

   Comprueba cada cita con `uv run gskg bucle cita "<fuente>" "<cita literal>"` antes de escribirla: el código
   rechaza la salida si una cita no aparece en su fuente. Una referencia de memoria, una traducción presentada como
   cita o una cita del README del proyecto no cuentan.
4. **Veredicto**:
   - `se_sostiene`: buscaste y no hay evidencia en contra. Aporta en `anclas` 1 o 2 citas literales primarias que
     sostengan el dictamen, sobre todo si su `anclaje` dice que no tiene ninguna literal. Si no encuentras una fuente
     primaria que lo sostenga, dilo en el argumento: el dictamen quedará frágil.
   - `debilitada`: la evidencia en contra es real, pero no basta para cambiar la decisión (pide un matiz o baja la
     confianza). Exige `contraevidencia` anclada y `patron`.
   - `refutada`: la evidencia en contra cambia la decisión. Exige `contraevidencia` anclada, `patron` y `propuesta`
     (otra de las `opciones` del expediente). En contenido exige `cambios` (`{campo: valor corregido}`, solo
     `campos_editables`, con el elemento todavía válido: la clave entre las opciones, los distractores mapeados y
     las explicaciones dentro del largo del grado); ahí la contraevidencia es opcional, pero el error tiene que ser
     concreto y verificable.
5. **No impugnes por redacción, por gusto ni por un matiz que no cambia la decisión.** Una impugnación sin
   contraevidencia anclada no reabre nada y gasta la réplica del panel. Una impugnación falsa es tan dañina como
   dejar pasar un error.

## Salida
`data/interim/panel/bucle/lotes/salida_<mismo nombre del lote>.json` (cambia `lote_` por `salida_`): un arreglo JSON
con **un veredicto por expediente**, escrito con Python (`json.dump(..., ensure_ascii=False, indent=1)`):

```json
{"id": "<id del expediente>", "veredicto": "se_sostiene | debilitada | refutada",
 "argumento": "70 palabras como máximo: qué buscaste, qué encontraste y por qué decide",
 "contraevidencia": [{"fuente": "HK_Science_S1-3_CurriculumFramework_2025.pdf p. 60",
                      "cita_literal": "recognise that a solution is a mixture formed when a solute is dissolved",
                      "dice": "HK S1–3 enseña la disolución en el núcleo"}],
 "anclas": [{"fuente": "TEMA:G09-CIE-U3-3.2", "cita_literal": "…", "dice": "…"}],
 "patron": "<uno de config/panel.yaml, bucle.patrones>",
 "propuesta": "<otra opción del expediente, si refutada>",
 "cambios": {"campo": "valor corregido (solo contenido)"},
 "confianza": "alta | media | baja"}
```

## Reglas
- **No dictaminas en nombre del panel ni del MINED.** Impugnas; el panel replica y, si no hay unanimidad, decide una
  persona.
- **No inventes evidencia.** Toda cita la verifica el código. La literatura de investigación puede ir en el
  argumento, nunca como cita.
- **No quites temas de la malla** ni propongas eliminarlos.
- **Escribe solo tu `salida_*.json`.** No edites capas, el estado del panel, lotes de otros, `data/fuentes/`,
  `reportes/` ni `data/grafo/`. No leas ni imprimas `.env`. No llames a Vertex ni a APIs de pago.
- **Confianza baja** si no pudiste verificar: tu impugnación no reabrirá el expediente.

## Antes de terminar
Corre `uv run gskg lotes validar --agente refutador` y corrige hasta que diga «✓» (ignora errores de archivos que no
son tuyos). Responde con:
- el conteo de veredictos;
- los expedientes refutados o debilitados y su patrón;
- los dictámenes que no pudiste anclar en ninguna fuente primaria.

## Réplica (para los roles del panel)
Si eres un miembro del panel y tu lote es de réplica (`replica_del_bucle` en el lote), sigue
`prompts/panel_dictaminar.md`. El expediente trae:
- `resolucion_vigente`: lo que decidió el panel;
- `impugnacion`: lo que encontró el revisor adversarial; su contraevidencia ya está verificada en la fuente;
- `sonda_ciega`: lo que dictaminó, sin ver la resolución, otra instancia de tu rol.

Ve a la fuente:
- si la impugnación no derriba la decisión, mantén la misma opción y explica por qué la contraevidencia no basta;
- si la derriba, cambia la decisión.

No defiendas el dictamen anterior por coherencia: la réplica existe para corregirlo. En tu evidencia, prefiere citas
literales de fuentes primarias, con `cita_literal`.
