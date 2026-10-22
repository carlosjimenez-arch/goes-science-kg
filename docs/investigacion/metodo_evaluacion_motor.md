# Evaluación inicial de los jueces del motor

> Registro histórico de investigación. Describe el corte y la ejecución indicados en este documento.
> Estado vigente del código, API y métricas: [documentación actual](../README.md) y [calidad](../CALIDAD.md).

Corte: **21 de octubre de 2026**. Conjunto: `motor_jueces_2026_10_21`, versión de esquema `1.0`. Archivo: `data/evaluacion/motor_casos_2026.json`.

## Estado y alcance

El conjunto está etiquetado **`sintetico_plata`**: las situaciones, propuestas y etiquetas fueron construidas para esta evaluación. No es un patrón oro anotado independientemente, un corpus primario certificado ni evidencia de eficacia educativa. Las URL se verificaron, pero sus contextos son paráfrasis breves de evaluación. No contienen citas textuales ni documentos completos. No se descargaron documentos al repositorio para construirlo.

El objetivo es comprobar si un juez reconoce la afirmación decisiva, distingue evidencia de autoridad aparente y acepta propuestas válidas dentro de su alcance. No mide aprendizaje del alumnado, alineación completa de V4, dificultad psicométrica de ítems o aptitud para decidir reformas curriculares sin verificación adicional.

Los fragmentos de propuestas incorrectas son **errores sembrados**, no instrucciones para ejecutarlos. Los casos de seguridad se evalúan solo como texto. No se realizan experimentos químicos, alertas sísmicas ni acciones sobre estudiantes.

## Diseño de casos

La suite contiene 16 casos: ocho pares con una propuesta aceptable y una propuesta con error. La distribución de etiquetas es equilibrada: ocho `aprobar` y ocho `rechazar`. El rol indica la especialidad del juicio solicitado, sin pretender que el modelo posea una credencial profesional.

| Par | Casos | Rol principal | Qué discrimina |
| --- | --- | --- | --- |
| Membrana | `SCI_BIO_01/02` | Científico, biología | Bicapa frente a monocapa y atribución incorrecta a NIH |
| Conservación | `SCI_CHE_01/02` | Científico, química | Disolución frente a destrucción de materia, mismo sistema cerrado |
| Masa/peso | `SCI_PHY_01/02` | Científico, física | Magnitud, unidad y cálculo de fuerza con gravedad distinta |
| Predicción sísmica | `SCI_EARTH_01/02` | Científico, Tierra | Descripción e incertidumbre frente a predicción exacta no sustentada |
| Andamiaje | `PSY_01/02` | Psicopedagógico | Presaberes y apoyo frente a sobrecarga y garantía por edad |
| Recursos/seguridad | `ADV_RES_01/02` | Adversarial | Acceso sin internet, restricciones de aula y advertencia convertida en autorización |
| País/causalidad | `ADV_CAUSAL_01/02` | Adversarial | Comparador internacional frente a efecto causal local inventado |
| Edad/grado | `ADV_EDAD_01/02` | Adversarial | Población PISA y equivalencia local pendiente frente a mapeo universal falso |

Cada par mantiene el contexto y las fuentes. No todos los pares modifican una sola palabra: algunos combinan una afirmación científica o pedagógica falsa con una atribución indebida. Sirven para una primera prueba de discriminación; no son una estimación causal del efecto de cada componente del prompt.

## Entrada y salida de la prueba

Enviar al juez únicamente:

- Un identificador opaco generado por el arnés, `rol` y `especialidad`.
- `contexto`, `contexto_fuente` y `propuesta`.
- Los registros de `fuentes_ids` resueltos a título, URL, localizador y paráfrasis.

Ocultar el `id` semántico original, `esperado`, `motivo_evaluable`, `criterios`, `error_sembrado`, `variante` y `par_id`. Las `etiquetas` son útiles para análisis, pero también deben ocultarse: nombres como `error_cientifico` o `evidencia_insuficiente` filtrarían la respuesta. Los sufijos `01/02` de los identificadores originales siguen el patrón de los pares y también revelarían la etiqueta. El arnés conserva la correspondencia entre identificador original y opaco; el modelo no la recibe.

Salida mínima, desacoplada del contrato de propuestas del producto:

```json
{
  "id": "identificador_opaco",
  "decision": "aprobar",
  "motivo": "Explicación breve de la afirmación decisiva y su relación con la evidencia.",
  "fuentes_utilizadas": ["ID_DE_FUENTE"],
  "afirmaciones_sin_respaldo": []
}
```

`decision` admite exclusivamente `aprobar` o `rechazar`. Para una propuesta que exige afirmar algo no sustentado, corresponde rechazar esa afirmación. El motivo puede pedir evidencia adicional. No corresponde rechazar todo piloto correctamente delimitado solo porque no ha demostrado aún eficacia. Las abstenciones, si un modelo las produce fuera del contrato, se contabilizan como salida inválida y se conservan; no se convierten silenciosamente en aciertos.

## Variantes de prompt

Comparar las variantes con **las mismas entradas, modelos y condiciones**. El rol se incorpora de forma equivalente en cada una. No incluir las etiquetas esperadas ni ejemplos tomados de esta suite en el prompt.

1. **P0, juicio directo.** Solicitar decisión y motivo breve utilizando las fuentes y restricciones proporcionadas. Funciona como línea base.
2. **P1, rúbrica y evidencia.** Separar comprobaciones de exactitud, implicación de la cita, edad/presaberes, recursos/seguridad y alcance causal. Una contradicción científica crítica o una práctica insegura impide aprobar. La salida permanece breve; no se pide razonamiento privado ni una cadena de pensamiento.
3. **P2, verificación de afirmaciones.** Solicitar primero un inventario breve de las afirmaciones comprobables, clasificadas como sustentadas, contradichas o no resueltas; después decidir sobre la propuesta. Pedir que el juez considere qué evidencia permitiría refutar su decisión inicial. No permitir inventar contenido de una URL no suministrado en el contexto.

P2 puede requerir más tokens que P0. Si mejora acierto pero excede costos o latencia, debe reportarse la compensación; no se asume que un flujo más largo sea superior. Una evaluación de panel autor/juez requeriría una condición experimental adicional: estas tres variantes no la demuestran.

## Comparación entre modelos y ejecución reproducible

La ejecución la realiza el arnés del proyecto, no este memorando. Para una comparación inicial, utilizar al menos dos modelos reales disponibles en el proveedor autorizado, con identificadores exactos resueltos durante la ejecución. No sustituir un fallo de acceso por respuestas simuladas. Con dos modelos, tres prompts y 16 casos, una repetición contiene 96 decisiones; tres repeticiones contienen 288. El presupuesto se calcula antes de solicitar llamadas.

Registrar modelo y revisión si el proveedor la expone, región, prompt íntegro y su hash, versión de suite, parámetros soportados, límite de salida, hora, intento, tokens, costo estimado y observado si está disponible, latencia, texto bruto y resultado parseado. Registrar errores, límites y reintentos como tales. No afirmar costo cero cuando el proveedor no informa facturación.

Usar orden aleatorio reproducible y documentar la semilla. Los miembros del mismo par se envían en solicitudes independientes, sin historial compartido, y no necesariamente consecutivos. Ningún modelo recibe los resultados de su pareja ni la respuesta del otro modelo. Mantener el mismo contenido de evidencia entre condiciones; una prueba con navegación externa sería otro experimento.

No exigir parámetros que el modelo no admita. Si no hay temperatura o semilla disponibles, registrarlo; no prometer determinismo. Fijar el límite de tokens para evitar que una variante falle simplemente por truncamiento y contabilizar ese costo.

## Métricas y revisión

Reportar conteos junto con proporciones:

- **Exactitud de decisión:** decisiones iguales a `esperado` entre todos los casos. Una salida inválida no cuenta como acierto.
- **Falsa aprobación:** propuestas con error aprobadas entre las ocho que deberían rechazarse. Es la métrica crítica de esta prueba.
- **Falso rechazo:** propuestas aceptables rechazadas entre las ocho que deberían aprobarse. Un juez que rechaza todo obtiene 50% de exactitud y no es útil.
- **Par resuelto completo:** ocho pares con ambos miembros juzgados correctamente. Evita ocultar sesgo por una sola etiqueta.
- **Fidelidad del motivo:** comprobar si identifica los elementos de `debe_identificar` y si incurre en `no_debe_afirmar`. La coincidencia literal no es necesaria. El cotejo de palabras por sí solo no determina esta métrica.
- **Atribución y citas:** comprobar que las fuentes utilizadas existan en la entrada y que no se les atribuyan conclusiones ausentes. Citar muchos documentos no aumenta la nota.
- **Costo, tiempo y estabilidad:** tokens, latencia, errores y variación entre repeticiones por modelo y variante; además de resultados desglosados por par y rol.

Si la fidelidad del motivo se evalúa con otro modelo, identificarla como **evaluación asistida por IA**, conservar su rúbrica y reportar desacuerdos. No presentarla como anotación experta independiente. Para esta suite, los autores pueden revisar resultados, pero eso no transforma retroactivamente las etiquetas en patrón oro.

Una puerta de desarrollo razonable es cero falsas aprobaciones de errores científicos y seguridad en esta muestra y ausencia de regresión clara en propuestas aceptables. Es un criterio de ingeniería propuesto, **no un umbral validado de seguridad o calidad educativa**. Cero errores en 16 casos no garantiza una tasa de error baja en producción; el tamaño es demasiado pequeño y los casos no son una muestra aleatoria del uso real.

No seleccionar un ganador solo por una diferencia de un caso. Inspeccionar qué falló y contrastar costo y estabilidad. Si hay empate, preferir la condición más simple y económica que cumpla los criterios de desarrollo. Si se edita el prompt usando estos resultados, declarar que la suite pasa a ser conjunto de desarrollo y exigir un conjunto nuevo reservado para confirmar cualquier mejora.

## Límites de generalización

Los errores son deliberados y relativamente claros. El español es homogéneo y no representa aún diversidad de aulas o respuestas de estudiantes. La evidencia abreviada facilita el juicio, por lo que no prueba recuperación documental, validación de citas a nivel de página, resistencia a inyección de instrucciones en documentos ni razonamiento sobre un grafo grande.

Las fuentes fueron verificadas por URL al corte; las paráfrasis no sustituyen archivos con SHA256 y fragmentos preservados. El código del motor debe seguir distinguiendo contexto de evaluación, corpus primario y salida generada. La suite tampoco mide independencia estadística entre jueces, equidad, adaptaciones de accesibilidad o seguridad de toda una secuencia de clase.

La evidencia de andamiaje no valida la edad o duración exacta inventada en `PSY_01`: se aprueba únicamente como piloto que atiende las condiciones declaradas. Las fuentes de PISA no han evaluado el tutor. Los CDC no han certificado el recurso escolar propuesto. Mantener estas fronteras es parte del objetivo de la prueba.

## Fuentes y procedencia

Consultadas el 21 de octubre de 2026; sin citas literales. Los identificadores del JSON corresponden a:

- [NHGRI, membrana plasmática](https://www.genome.gov/genetics-glossary/Cell-Membrane-Plasma-Membrane): estructura e intercambio celular.
- [ACS, conservación de masa, lección 4.1](https://www.acs.org/content/dam/acsorg/education/k-8/inquiry-in-action/fifth-grade/g5-l4.1-ngss.pdf): conservación en disolución y otros cambios ordinarios.
- [NASA, masa y peso](https://spaceplace.nasa.gov/planets-weight/en/) y [tabla lunar](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html): distinción de magnitudes y valores aproximados de gravedad.
- [USGS, predicción sísmica](https://www.usgs.gov/faqs/can-you-predict-earthquakes): límites de predicción y pronósticos.
- [Lazonder y Harmsen, 2016](https://pure.rug.nl/ws/portalfiles/portal/81069469/Meta_analysis_of_inquiry_based_learning_Effects_of_guidance.pdf): estudio original sobre guía en indagación.
- [CDC, uso seguro del blanqueador](https://www.cdc.gov/hygiene/about/cleaning-and-disinfecting-with-bleach.html): advertencia de mezclas; no autorización experimental.
- [MINED, Conociendo Mis Logros 2025](https://mined.gob.sv/evaluacion/docs/2025/DOC%20informativo%20CML%202025.pdf): consideración de alternativas impresas.
- [OCDE, PISA 2025 I](https://www.oecd.org/en/publications/pisa-2025-results-volume-i_73451bc5-en.html): desempeño de sistemas; no efecto del tutor.
- [OCDE, notas metodológicas PISA 2022 II](https://www.oecd.org/en/publications/pisa-2022-results-volume-ii_a97db61c-en/full-report/component-17.html): límites de inferencia causal.
- [OCDE, población PISA](https://www.oecd.org/en/about/programmes/pisa/pisa-frequently-asked-questions-faqs.html): selección por edad y matrícula.
