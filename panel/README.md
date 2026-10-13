# Panel de expertos IA

Mientras no haya un equipo del MINED que revise, un panel de expertos IA resuelve con criterio técnico las decisiones
que esperaban esa revisión. El panel tiene cinco miembros: un experto en la didáctica de cada ciencia (Biología,
Física, Química y Ciencias de la Tierra y del Espacio) y un psicopedagogo. El método y sus límites están en
[`specs/14_panel_expertos.md`](../specs/14_panel_expertos.md). Este README lo escribe el equipo;
[`DICTAMEN.md`](DICTAMEN.md) lo genera `gskg panel informe`.

> **Los dictámenes no son confirmaciones del MINED.** Quedan en las capas como «dictamen del panel», con su evidencia,
> y se pueden confirmar o revertir. Usar contenido con estudiantes exige además la firma de un docente
> (`aprendizaje/PILOTO.md`, decisión 7).

## Primera revisión (2026-10-12)
Fueron 510 expedientes en 3 rondas, con 32 subagentes:
- **Ronda 1:** dictamen independiente de cada rol.
- **Ronda 2:** deliberación con los dictámenes de los demás, y la etapa del psicopedagogo sobre el contenido.
- **Ronda 3:** visto bueno científico de lo que corrigió el psicopedagogo.

Las 150 clases inciertas del contraste de 2.°–8.° fueron en una serie aparte, con verificación en las fuentes.

| Qué | Expedientes | Resultado |
|---|---|---|
| Decisiones de contenido del equipo GOES | 35 | 33 respaldadas, 2 rechazadas |
| Asignaciones de «configuración electrónica» | 85 | 78 respaldadas, 7 reasignadas |
| Asignatura y conceptos de temas (revisión de coherencia) | 44 | 40 respaldados, 3 rechazados con alternativa, 1 sin consenso |
| Capa pedagógica (actividades, dificultades, microtemas) | 138 | 69 aprobados tal cual, 69 corregidos; todos en `revisado_panel` |
| Hallazgos verificados del contraste | 25 | 6 respaldados, 18 matizados, 1 sin consenso |
| Acciones de las propuestas que la V2 no adoptó | 26 | 4 adoptar, 21 adaptar, 1 descartar |
| Clases inciertas del contraste de 2.°–8.° | 150 | 135 clasificadas con evidencia, 15 sin consenso |
| Decisiones del piloto | 7 | 7 recomendaciones (aprendizaje/PILOTO.md, sección 0) |

**Correcciones de contenido que importan.** La capa tenía errores que el tutor habría repetido en cada sesión:
- **Ósmosis:** la explicación invitaba a invertir el sentido del agua.
- **Membrana:** era «una capa» de fosfolípidos, y en un ítem la clave era falsa.
- **Equilibrio:** decía que «el agua líquida no se escribe en K».
- **Volumen de un gas a 117 °C:** se pedía medirlo en un baño de agua, que no llega a esa temperatura.
- **Tipos de rocas:** el tutor iba a marcar como error que la toba es una roca volcánica.
- **Ítems ambiguos:** en uno, la letra de una opción chocaba con el rótulo del objeto.

Además, la clave era la opción más larga en 57 de 84 ítems y la A en 34 de 84. Por eso ahora las opciones se barajan
(`sesion.barajar`) y el redactor tiene reglas nuevas (`prompts/redactar_actividades.md`).

## Bucle de fortalecimiento (2026-10-12 y 13)
Los 486 dictámenes resueltos pasaron por un revisor adversarial que buscó en las fuentes la prueba en contra, con
citas literales que el código verifica, y por una sonda ciega de 63 expedientes. Lo reabierto volvió a la réplica del
panel. El bucle convergió en 2 vueltas:
- **24 dictámenes cambiaron**, todos por unanimidad, y la vuelta 2 confirmó 21 de esos 24 cambios;
- **820 citas literales nuevas** dejan anclada la mayoría de los dictámenes;
- **solidez final:** 466 sólidos o respaldados, 1 frágil y 17 sin consenso (del panel original).

Detalle por ciencia, errores de la malla y lo que aprendió el método: [`bucle/README.md`](bucle/README.md) y los
snapshots en [`bucle/`](bucle/). La columna «Solidez» de [`DICTAMEN.md`](DICTAMEN.md) y el estado del CSV para el MINED
la muestran por dictamen.

**Decisión delegada tras el bucle:** las fuerzas intermoleculares pasan a «sin referente». Solo ENG GCSE (p. 20) las
tiene en el núcleo; HK p. 81 es Extension Part.

## Lo que decidió el responsable del proyecto después del panel
Por delegación, con evidencia verificada en la fuente:
1. **Neutralización:** la clase pasa a «tardío». El panel mostró que HK S1–3 p. 60 (8.4) es núcleo y no Extension;
   con HK, el consenso queda en 7.° y la V2 la enseña en 9.°.
2. **Agentes oxidantes y reductores:** la clase pasa a «posterior». HK p. 80 no nombra la oxidación ni la reducción,
   así que quedan 4 países. La reducción sigue llegando tarde a través de «oxidación y reducción».
3. **Etiquetas de 4 temas corregidas** (`data/interim/revisiones/2026-10-12_panel_expertos.json`):
   - G03-CIE-U6-6.8 (microorganismos);
   - G04-CIE-U2-2.12 (agricultura);
   - G07-CIE-U6-6.6 (sin inducción de Faraday);
   - G05-CIE-U3-3.6, que es electrostática de Física y no iones de Química.
4. **«Configuración electrónica por orbitales» en 9.°–11.°** pasa de «solo especialización» a «retomado». La V2 ya
   la usa en 5.° (G05-CIE-U3-3.11), así que el problema es otro: formalismo de bachillerato en primaria.
5. **Punto decimal** en todo lo que ve el estudiante, como la malla del MINED.
6. **No se rechazó el prerrequisito aminoácidos → proteínas** que observó el experto de Biología: la dependencia es
   válida. Lo que pasa es que la V2 enseña los aminoácidos dentro de Biología 10.°, antes que Química 11.°.

## Para el MINED, cuando haya equipo
- **Error en la malla:** G05-CIE-U6-6.7 dice bordes de placa «pasivos»; lo correcto es «transformantes». La propia V2
  lo escribe bien en 9.° (G09-CIE-U5-5.12).
- **Más errores y problemas de la malla** que encontró el bucle (corpuscular en G10-FIS-U16-16.1, costa y montaña en
  G06-CIE-U2-2.6, la energía como producto en G06-CIE-U5-5.12 y otros): [`bucle/README.md`](bucle/README.md).
- **La química de 5.° debe decidirse en bloque:** números cuánticos, orbitales, iones, propiedades periódicas y
  enlace iónico, junto con la nomenclatura de 7.° que depende de ellos. Si se mueve una sola pieza, la secuencia se
  rompe.
- **El pivote de Química de Bachillerato:** medir 10.°–11.° solo contra JP, TW y EE equivale a cambiar el pivote
  (ACARA Senior Secondary). Esa decisión le corresponde al responsable del proyecto. ACARA no incluye orbitales ni la
  ley de Hess.
- **Contenidos ausentes:** la pubertad no aparece en 2.°–8.°, y los recursos renovables y no renovables llegan en 7.°
  frente a 5.° en los países.
- **La conciliación de las propuestas con la V2 se quedó corta:** marcó como «no adoptadas» acciones que la V2 ya
  trae en otras columnas (fricción, eficiencia, pH). El panel lo corrigió en sus dictámenes.

## Lo que queda para una persona
- **17 expedientes sin consenso** (lista en `DICTAMEN.md`). Por ejemplo:
  - G07-CIE-U6-6.12: los dos expertos proponen la misma alternativa, pero uno con confianza baja;
  - el enlace iónico en 6.°;
  - 15 clases del contraste, con dos lecturas válidas.
- **Las referencias de literatura** que algunos miembros citaron de memoria (Biología, Tierra y Espacio) no están
  verificadas. Valen como argumento, no como prueba.
- **Mejora del método del contraste:** la búsqueda de texto confunde raíces cercanas, por ejemplo «potencia» con
  «potencial». No produce hallazgos falsos, pero amplía la lectura amplia.
