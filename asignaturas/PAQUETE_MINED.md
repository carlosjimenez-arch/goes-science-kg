# Paquete para el equipo de Ciencias del MINED (actualizado el 2026-10-12)

Esto es lo que el equipo GOES necesita que el MINED revise, en orden de prioridad. Todo es **borrador con evidencia**:
nada cambia la malla sin una decisión del MINED. Cada archivo indica qué columnas llenar (`decision`, `comentario` y
`revisado_por`).

## 1. Confirmar decisiones de contenido: 35 decisiones y 85 asignaciones
El equipo GOES tomó estas decisiones fuera de la IA. El grafo ya las aplica, pero falta su confirmación.

**[`decisiones/2026-10-12_decisiones.csv`](decisiones/2026-10-12_decisiones.csv)** (reemplaza al del 2026-10-11):
- 2 equivalencias retiradas.
- 1 prerrequisito rechazado.
- 1 división de concepto: «configuración electrónica» por orbitales en Bachillerato y por capas en secundaria.
- **7 relaciones «parte de» (nuevas).** Enseñar la parte cuenta como enseñar el todo; por ejemplo, la conservación de
  la energía mecánica cuenta como conservación de la energía. Solo se usan en el contraste internacional.
- 5 clases corregidas en el contraste de 9.°–11.°.
- 19 clases corregidas en el contraste de 2.°–8.° (**8 nuevas**). Todas están verificadas contra las fuentes.

**[`decisiones/2026-10-12_asignaciones_division.csv`](decisiones/2026-10-12_asignaciones_division.csv):** a qué
versión de «configuración electrónica» se asignó cada tema u objetivo.

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
  - ley de Ohm como relación explícita: 11.°, aunque 6.° ya usa la relación sin nombrarla.
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
- **Límite del método:** las clases automáticas de 2.°–8.° tenían 46 % de falsos. El método se corrigió el 2026-10-12
  y se probó con una muestra nueva: bajó a 25 %. Por eso solo se presentan los hallazgos verificados. 150 conceptos
  quedan «inciertos» hasta revisarlos.

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
objetivos (3.°, 5.°, 7.° y tres de 9.°) y todo está en borrador.

**Lo que pedimos al MINED:**
1. **Revisar el contenido.** Los puntos para su revisión están en
   [`data/pedagogia/REVISION_PENDIENTE.md`](../data/pedagogia/REVISION_PENDIENTE.md).
2. **Decidir sobre el piloto.** [`aprendizaje/PILOTO.md`](../aprendizaje/PILOTO.md) trae la propuesta de piloto y de
   política de datos de menores. Pide decidir grado, unidad, centros, consentimiento, retención, modelo y región, y
   quién aprueba el contenido.

## Cómo devolverlo
1. Llenen los CSV y envíenlos al equipo GOES.
2. Se importan así:
   - decisiones: `uv run gskg revision importar-decisiones <csv>`;
   - revisión de etiquetas: `uv run gskg revision importar <csv>`.
3. El grafo se reconstruye con `make todo`.
