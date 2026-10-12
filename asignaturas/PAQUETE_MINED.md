# Paquete para el equipo de Ciencias del MINED (actualizado el 2026-10-12)

Esto es lo que el equipo GOES necesita que el MINED revise, en orden de prioridad. Todo es **borrador con evidencia**:
nada cambia la malla sin una decisión del MINED. Cada archivo indica qué columnas llenar (`decision`, `comentario` y
`revisado_por`).

> **Revisión técnica interina.** El 2026-10-12 todavía no había un equipo del MINED que revisara. Por eso un **panel
> de expertos IA** dictaminó estas decisiones y la capa pedagógica (spec 14). El panel tiene un experto por ciencia y
> un psicopedagogo, y trabajó con evidencia en la fuente, deliberación y unanimidad. El resumen y lo que dejó sin
> consenso están en [`panel/README.md`](../panel/README.md) y [`panel/DICTAMEN.md`](../panel/DICTAMEN.md). Sus
> dictámenes **no son confirmaciones del MINED**: en los CSV aparecen como «dictamen del panel: … (pendiente de
> confirmar)», para que el MINED los confirme o los revierta.

## 1. Confirmar decisiones de contenido: 170 decisiones y 85 asignaciones
El grafo ya aplica estas decisiones, pero falta la confirmación del MINED.

**[`decisiones/2026-10-12_decisiones-2.csv`](decisiones/2026-10-12_decisiones-2.csv)** (reemplaza a los anteriores). Trae
168 con dictamen del panel y 2 decisiones nuevas tomadas tras sus observaciones: la neutralización pasa a «tardío» y
los agentes oxidantes, a «posterior». Las 35 originales:
- 2 equivalencias retiradas.
- 1 prerrequisito rechazado.
- 1 división de concepto: «configuración electrónica» por orbitales en Bachillerato y por capas en secundaria.
- **7 relaciones «parte de» (nuevas).** Enseñar la parte cuenta como enseñar el todo; por ejemplo, la conservación de
  la energía mecánica cuenta como conservación de la energía. Solo se usan en el contraste internacional.
- 5 clases corregidas en el contraste de 9.°–11.°.
- 19 clases corregidas en el contraste de 2.°–8.° (**8 nuevas**). Todas están verificadas contra las fuentes.

Además, **135 clases del contraste de 2.°–8.°** que la doble lectura había dejado inciertas, ahora clasificadas por el
panel con evidencia en la fila de la V2 y en la página de cada país.

**[`decisiones/2026-10-12_asignaciones_division-2.csv`](decisiones/2026-10-12_asignaciones_division-2.csv):** a qué
versión de «configuración electrónica» se asignó cada tema u objetivo. El panel respaldó 78 y reasignó 7; por
ejemplo, G05-CIE-U3-3.11 queda con las dos versiones, porque 5.° ya usa la notación por subniveles.

En `decision` se escribe: aceptar, cambiar (solo en asignaciones) o rechazar. Un rechazo no revierte nada: pide una
nueva decisión.

Además, 4 temas nuevos de la V2 cambiaron de asignatura para quedar con el resto de su unidad (revisión experta,
`data/interim/revisiones/2026-10-11_coherencia_asignatura_v2.json`):

| Tema | Antes | Ahora | Por qué |
|---|---|---|---|
| G04-CIE-U1-1.15 conductores y aislantes eléctricos | Química | Física | se prueba con un circuito, en la unidad de energía |
| G08-CIE-U10-10.1 ciclo del carbono | Biología | Tierra y Espacio | unidad de cambio climático |
| G08-CIE-U9-9.2 línea del tiempo geológico | Biología | Tierra y Espacio | escala geológica con hitos de la vida |
| G09-CIE-U4-4.17 acidificación del océano | Química | Tierra y Espacio | unidad de Oceanografía; el pH es su base química |

## 2. Hallazgos verificados del contraste internacional
Solo se incluyen hallazgos comprobados contra la fila de la malla V2 y la página del documento de cada país.

### 9.°–11.° ([`internacional/README.md`](../internacional/README.md))
- **El Bachillerato obliga más contenido** que casi todos los referentes. Solo Japón, Taiwán y Estonia tienen las tres
  ciencias obligatorias después de los 16 años.
- **Química de 9.°–11.° incluye contenido de electiva** en los países: K, Ka y amortiguadoras en 9.°; Gibbs y
  orbitales moleculares en 10.°–11.°.
- **Física pide poco razonamiento:** 10 % frente a 31 %.
- **El efecto invernadero no se retoma** en 9.°–11.°.
- **Secuencias por ordenar:** gases antes de procesos termodinámicos, superposición antes de interferencia,
  mitocondria antes del metabolismo.

### 2.°–8.° ([`internacional/2_8/README.md`](../internacional/2_8/README.md), con evidencia por hallazgo)
- **Llegan tarde frente a los países:**
  - reducción, agentes oxidantes y serie de reactividad: 10.°–11.° frente a 7.°–8.°;
  - suelo: 5.° frente a 3.°;
  - formación de imágenes en espejos planos: 10.° frente a 5.°–8.°;
  - lentes e imágenes: 10.°–11.° frente a 7.°–8.°;
  - reacciones exotérmicas y endotérmicas: 10.° frente a 7.°;
  - ley de Ohm como relación explícita: 11.°, aunque 6.° ya usa la relación sin nombrarla;
  - neutralización: 9.° frente a 7.° (corregido por el panel).
- **Llegan tarde según el panel** (clasificados con evidencia, sin una segunda verificación):
  - masa y peso: 10.° frente a 6.°–7.°;
  - potencia eléctrica: 9.° frente a 7.°;
  - refracción: 7.° frente a 5.°;
  - el ojo y los instrumentos ópticos: 11.° frente a 6.°–8.°;
  - relaciones de los gases: 9.° frente a 7.°;
  - recursos renovables: 7.° frente a 5.°.
- **Van antes que todos los países:**
  - **números cuánticos en 5.°**, con su formalismo; ningún país los enseña antes de bachillerato;
  - enlace iónico en 5.°–6.°;
  - iones en 5.°;
  - fuerzas intermoleculares en 6.°;
  - ciclo de vida de las estrellas en 5.°;
  - eclipses en 4.°.

  La química de 5.° está 2 o 3 grados adelantada.
- **Secuencias:**
  - los tipos de rocas en 3.° llegan antes que los minerales, que aparecen en 8.°;
  - el Big Bang de 8.° pide evidencias sin el corrimiento al rojo.
- **Decisiones propias que conviene sostener:**
  - precursores y monitoreo de sismos y erupciones en 5.°, por el riesgo local;
  - formación de la Tierra en 5.°.
- **Hueco de profundización:** las adaptaciones de los seres vivos no se retoman entre 3.° y 10.°.
- **Error en la malla:** G05-CIE-U6-6.7 dice bordes de placa «pasivos»; lo correcto es «transformantes».
- **Límite del método:** las clases automáticas de 2.°–8.° tenían 46 % de falsos. El método se corrigió el 2026-10-12
  y se probó con una muestra nueva: bajó a 25 %. Por eso solo se presentan los hallazgos verificados. El panel
  clasificó 135 de los 150 conceptos inciertos; quedan 15 para una persona.

## 3. Propuestas curriculares y lo que la V2 ya incorporó
[`PROPUESTAS.md`](PROPUESTAS.md) tiene 11 borradores por ciclo, simulados sobre la V2. Los errores de secuencia de
confianza alta bajan de 55 a 5. Ninguno quita temas.
- **Conciliación con la V2.** De 47 acciones «nuevo»:
  - la V2 ya trae 5 en el mismo grado (imanes, termómetro, instrumentos del tiempo atmosférico, reflexión, circuito y
    conductores, en 3.° y 4.°);
  - 8 las trae en otro grado;
  - 8 las trae en parte.

  Les pedimos **confirmar qué tomaron de las propuestas** (tabla al final de `PROPUESTAS.md`) y opinar sobre las 26
  pendientes.
- Las decisiones abiertas de cada propuesta están en su informe (`<asignatura>/propuesta/informe_*.md`).

## 4. Prototipo de apoyo al aprendizaje y propuesta de piloto
[`aprendizaje/README.md`](../aprendizaje/README.md) describe un tutor que complementa la malla sin cambiarla:
- revisa las bases;
- comprueba hipótesis con preguntas breves;
- refuerza y vuelve al objetivo.

Tiene un tutor conversacional y un evaluador de respuestas abiertas, los dos con guardas. Su contenido abarca 6
objetivos (3.°, 5.°, 7.° y tres de 9.°). El panel revisó los 138 elementos y corrigió 69; están en estado
`revisado_panel`, que no basta para usarlos con estudiantes: falta la firma de un docente.

**Lo que pedimos al MINED:**
1. **Revisar el contenido.** Los puntos para su revisión están en
   [`data/pedagogia/REVISION_PENDIENTE.md`](../data/pedagogia/REVISION_PENDIENTE.md).
2. **Avalar el piloto.** [`aprendizaje/PILOTO.md`](../aprendizaje/PILOTO.md) trae las decisiones técnicas que ya se
   tomaron:
   - fases A → B0 → B → C;
   - unidad 9.° U8, La célula;
   - uso en clase;
   - control de fidelidad del tutor en dos niveles;
   - salvaguardas para menores.

   Trabajar con estudiantes exige el aval institucional del MINED, que además debe designar a los revisores.

## Cómo devolverlo
1. Llenen los CSV y envíenlos al equipo GOES.
2. Se importan así:
   - decisiones: `uv run gskg revision importar-decisiones <csv>`;
   - revisión de etiquetas: `uv run gskg revision importar <csv>`.
3. El grafo se reconstruye con `make todo`.
