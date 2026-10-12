# Paquete para el equipo de Ciencias del MINED (2026-10-11)

Lo que el equipo GOES necesita que el MINED revise, en orden de prioridad. Todo es **borrador con evidencia**: nada
cambia la malla sin su decisión. Cada archivo indica qué columna llenar (`decision`, `comentario`, `revisado_por`).

## 1. Confirmar decisiones de contenido · 20 decisiones y 85 asignaciones
Decisiones que el equipo GOES tomó fuera de la IA y que el grafo ya aplica, pendientes de su confirmación.
- [`decisiones/2026-10-11_decisiones.csv`](decisiones/2026-10-11_decisiones.csv): 2 equivalencias retiradas, 1
  prerrequisito rechazado, 1 división de concepto («configuración electrónica»: por orbitales en Bachillerato, modelo de
  capas en secundaria), 5 clases corregidas en el contraste de 9.°–11.° y **11 nuevas** del contraste de 2.°–8.°.
- [`decisiones/2026-10-11_asignaciones_division.csv`](decisiones/2026-10-11_asignaciones_division.csv): a qué versión
  de «configuración electrónica» se asignó cada tema u objetivo.
- `decision`: aceptar | cambiar (solo en asignaciones) | rechazar. Un rechazo no revierte nada: pide una nueva decisión.

Además, 4 temas nuevos de la V2 cambiaron de asignatura para quedar con el resto de su unidad (revisión experta,
`data/interim/revisiones/2026-10-11_coherencia_asignatura_v2.json`):

| Tema | Antes | Ahora | Por qué |
|---|---|---|---|
| G04-CIE-U1-1.15 conductores y aislantes eléctricos | Química | Física | se prueba con un circuito, en la unidad de energía |
| G08-CIE-U10-10.1 ciclo del carbono | Biología | Tierra y Espacio | unidad de cambio climático |
| G08-CIE-U9-9.2 línea del tiempo geológico | Biología | Tierra y Espacio | escala geológica con hitos de la vida |
| G09-CIE-U4-4.17 acidificación del océano | Química | Tierra y Espacio | unidad de Oceanografía; el pH es su base química |

## 2. Hallazgos verificados del contraste internacional
Solo hallazgos comprobados contra la fila de la malla V2 y la página del documento de cada país.
- **9.°–11.°** ([`internacional/README.md`](../internacional/README.md)): el Bachillerato obliga más contenido que
  casi todos los referentes (solo Japón, Taiwán y Estonia tienen las tres ciencias obligatorias después de los 16
  años); Química de 9.°–11.° incluye contenidos que en los países son de electiva (K, Ka, amortiguadoras en 9.°; Gibbs,
  orbitales moleculares en 10.°–11.°); Física pide poco razonamiento (10 % frente a 31 %); el efecto invernadero no se
  retoma en 9.°–11.°; secuencias por ordenar (gases antes de procesos termodinámicos, superposición antes de
  interferencia, mitocondria antes del metabolismo).
- **2.°–8.°** ([`internacional/2_8/README.md`](../internacional/2_8/README.md)): agentes oxidantes y reductores llegan
  tarde (10.° frente a 7.°–8.°); suelo llega tarde (5.° frente a 3.°); la formación de imágenes en espejos planos llega
  tarde (10.° frente a 5.°–8.°); fuerzas intermoleculares en 6.° y ciclo de vida de las estrellas en 5.° van antes que
  en cualquier país; el Big Bang de 8.° pide evidencias sin el corrimiento al rojo.
- **Límite que deben conocer:** en 2.°–8.° el 46 % de los candidatos automáticos verificados resultó falso por el
  etiquetado de la V2. Por eso solo se presentan los verificados.

## 3. Propuestas curriculares y lo que la V2 ya incorporó
[`PROPUESTAS.md`](PROPUESTAS.md): 11 borradores por ciclo, simulados sobre la V2 (errores de secuencia de confianza
alta: 55 → 5). Ninguno quita temas.
- **Conciliación con la V2:** de 47 acciones «nuevo», la V2 ya trae 5 en el mismo grado (imanes, termómetro,
  instrumentos del tiempo atmosférico, reflexión, circuito y conductores, en 3.° y 4.°), 8 en otro grado y 8 en parte.
  Les pedimos **confirmar qué tomaron de las propuestas** (tabla al final de `PROPUESTAS.md`) y opinar sobre las 26
  pendientes.
- Las decisiones abiertas de cada propuesta están en su informe (`<asignatura>/propuesta/informe_*.md`).

## 4. Opcional: prototipo de apoyo al aprendizaje
[`aprendizaje/README.md`](../aprendizaje/README.md): un tutor que complementa la malla sin cambiarla (revisa bases,
comprueba hipótesis con preguntas breves, refuerza y vuelve al objetivo). El contenido de 3 objetivos de 9.° está en
borrador; los puntos para su revisión están en
[`data/pedagogia/REVISION_PENDIENTE.md`](../data/pedagogia/REVISION_PENDIENTE.md). Antes de un piloto con
estudiantes hace falta su decisión sobre la política de datos de menores y qué grados y asignaturas entrarían.

## Cómo devolverlo
Llenen los CSV y envíenlos al equipo GOES. Se importan con `uv run gskg revision importar-decisiones <csv>` (decisiones)
y `uv run gskg revision importar <csv>` (revisión de etiquetas); el grafo se reconstruye con `make todo`.
