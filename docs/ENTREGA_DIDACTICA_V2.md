# Edición didáctica local · cierre del 29 de octubre de 2026

Se corrigieron y cerraron **los cinco recorridos R1–R5 y los casos identificados**, alcance confirmado
por el usuario. La edición incorpora dos guiones de 4.º corregidos, un módulo de medición honesta y
una evaluación de unidad revisada. Cada recorrido dispone de diagnóstico, refuerzo y comprobación
reservada en hojas separadas, además de la guía docente con soluciones y rúbricas completas.

La revisión científica aplicada y la revisión pedagógica asistida de las versiones finales fueron
favorables en ese alcance documental. Los nueve JSON revisados (ocho paquetes y una evaluación)
coinciden con los SHA de sus dictámenes. No se trasladaron los votos anteriores a los textos nuevos.

## Paquete y trazabilidad

Carpeta de trabajo y evidencia: `data/clases_v4/mejora_didactica_20261029/`.

| Archivo | Uso |
|---|---|
| `ciencias_v4_mejora_didactica_final.zip` | Entrega local completa y autónoma |
| `entrega_final/INDICE.md` | Entrada a unidades, materiales y recorridos finales |
| `entrega_final/manifest.json` | Inventario exacto por tamaño y SHA, procedencia y alcance de mediciones |
| `entrega_final/recorridos/R1` a `R5` | Cuatro hojas, JSON, estado de mediciones y manifiesto por recorrido |
| `entrega_final/clases/` | Guiones docentes/estudiante; las dos correcciones incluyen diagnóstico y comprobación separados |
| `entrega_final/modulos/` | Módulo nuevo de medición honesta, con sus cuatro hojas |
| `entrega_final/evaluaciones/` | Hojas docente/estudiante de las 97 evaluaciones y sus JSON |
| `entrega_final/auditoria/revisiones/` | Dictámenes finales, con identidades y SHA cotejados automáticamente |
| `entrega_final/antecedentes/` | ZIP original de guiones, publicación complementaria original y cinco recibos conservados |

Identidad de esta edición: `1960ed2480c21750874890d9f74f2b0e790569822b13021ab66208fcb2cc3dd9`.
SHA-256 del ZIP: `a85d8250fefba9436216993d754d301ffa37ae10baa6efce5fe3efee47aaa5e2`.
Son 134.017.490 bytes. La identidad del manifiesto y el SHA del ZIP son magnitudes distintas.

La publicación vigente en GCS continúa fijada por los recibos anteriores. Esta edición es local y
no reemplaza los recibos ni los objetos publicados. La API que consume esos recibos conserva la
publicación anterior; para consultar estos materiales se usa el índice de esta edición.

## Correcciones de contenido científico

**Amenazas y vulnerabilidad, 4.º.** Se reemplazaron las explicaciones de química ajenas al objetivo en
las filas terminadas en `e73c460191` y `d602c19904`. Ambos GuionClase completos mantienen literalmente
el objetivo curricular, tienen las cinco fases y una sesión propuesta de 60 minutos. Distinguen amenaza,
exposición, vulnerabilidad y capacidad con casos ficticios explícitos. Su implementación contiene recursos,
seguridad, accesibilidad, lectura fácil, versión mínima y progresión como contenido anclado en JSON.
Los anexos anteriores de esos dos guiones se conservan como antecedentes y se marcan no aplicables
automáticamente a la corrección.

La prioridad y la proporción de daños no se deducen contando símbolos, vulnerabilidades o acciones de
preparación. La terminología se apoya en fuentes primarias de
[UNDRR](https://www.undrr.org/terminology/disaster-risk). Una actividad escolar no se presenta como un
estudio técnico de riesgo ni como acreditación de preparación real para emergencias.

**Evaluación de la unidad `c959dd0d12`.** Se leyeron completos sus 15 ítems y se corrigieron seis:

- I01: los requerimientos pueden incluir condiciones ambientales, además de recursos.
- I10: una tabla simulada de ocho meses no acredita un rango anual ni el clima real. Menos lluvia sólo
  permite plantear un riesgo agrícola condicionado a suelo, distribución de lluvia y necesidades del cultivo.
- I11: un tsunami puede presentarse como inundación rápida y corrientes, sin una ola grande evidente.
- I13: el relato usado se identifica como ficticio.
- I14: se separa inundación, condición del drenaje y humo; el número de puntos no determina prioridad ni daño.
- I15: se explicita la exposición compartida y una condición concreta de vulnerabilidad.

**Medición honesta, 10.º.** El paquete diferencia repetibilidad, efecto sistemático, corrección,
variación entre objetos, dispersión e incertidumbre estándar. Enseña unidades y signo de corrección
antes de pedirlos en una tarea nueva; la incertidumbre suministrada no se presenta como rango ni
cobertura del 95 %. Los ejes recortados se comparan con el cambio porcentual real de los datos.
Las tablas son simuladas y los límites del resultado se explicitan. Fuentes primarias y capturas
locales disponibles están en `correcciones/fuentes/`; el registro declara los accesos HTTP rechazados
en lugar de inventar un SHA del recurso remoto no descargado.

## Cinco recorridos cerrados

| Recorrido | Material final y criterios corregidos |
|---|---|
| R1 · Difusión y ósmosis | Cantidad y concentración con volúmenes distintos; membrana y modelo explícitos; % m/v, gráfico y cambio de masa cero enseñados antes de la tabla nueva. No se infiere una concentración isotónica exacta de dos puntos simulados. |
| R2 · Gases | Temperatura absoluta, presión absoluta, cantidad fija y control de variables; nueva conversión Celsius → kelvin en la comprobación. Modelos y actividades en papel, sin calentar ni forzar sistemas cerrados. |
| R3 · Constante de equilibrio | Equilibrio dinámico, exponentes y fases puras; expresiones nuevas, cálculo e interpretación de K. Las rúbricas responden a todas las partes efectivamente preguntadas. |
| R4 · Suelo, 5.º | Procesos químicos diferenciados de drenaje/cambios físicos; contexto, límites y apoyos propios del grado. La comprobación nueva no se sustituye por terminar el tiempo asignado. |
| R5 · Respuesta abierta | Paquete autónomo con explicación y ejemplos de exponentes, fases y K menor que uno; calificación vinculada a la respuesta y a criterios explícitos. Las instrucciones incrustadas en una respuesta no se toman como órdenes al evaluador. |

Los cinco contienen 19 ítems. Los tres paquetes CIEN contienen otros 21 ítems y 28 criterios específicos;
no se cuentan sus representaciones duplicadas como nuevos módulos. La secuencia de entrega es:

1. Entregar y recoger `diagnostico_estudiante.md`.
2. Seleccionar apoyo con el criterio docente; entregar `estudiante.md` para ejemplo y práctica guiada.
3. Retirar las ayudas de resolución y entregar `comprobacion_estudiante.md`.
4. Calificar con `docente.md`; conservar adaptaciones de acceso, respuesta y criterio. Si falta evidencia,
   registrar seguimiento, sin reutilizar una tarea ya vista como si fuera independiente.

## Carga cognitiva y mediciones honestas

El [protocolo pedagógico](PEDAGOGIA_CIENCIAS_V4.md) distingue indicadores de diseño, esfuerzo mental
autoinformado, desempeño inmediato, retención y eficacia. Longitud, minutos, número de fases, respuestas
simuladas, integridad SHA y pruebas de código no se convierten en puntuaciones de carga o aprendizaje.
Las previas y actualizaciones BKT del prototipo siguen siendo supuestos no calibrados, señalados como
salidas del simulador en sus informes.

Los nuevos controles rechazan:

- cierre por reutilizar la evaluación inicial, o por clonar su enunciado con otro ID;
- confirmación diagnóstica contando varias veces la misma tarea;
- tratar un sondeo sin calificación como error conceptual;
- comprobaciones sin solución, sin niveles de rúbrica o con cálculos incorrectos;
- hojas desactualizadas o incompletas aunque se rehaga su inventario SHA;
- cambios de versión que intenten conservar el dictamen anterior;
- denominadores inflados, alias contados como nuevos módulos y simulaciones presentadas como datos reales.

`resumen_esfuerzo()` devuelve `no_medido` si faltan datos reales. Conserva instrumento, escala ordinal,
pregunta, grado, tarea, momento, ayudas y contexto; mantiene las simulaciones aparte. No crea una media
de categorías, porcentaje de reducción, umbral de sobrecarga ni número de participantes a partir de
registros de tarea. La adaptación del instrumento a edades y contexto requiere contraste local.

Una futura evidencia de cierre observado exige registros de la misma persona seudonimizada y sesión,
orden de etapas, respuestas no vacías, comprobación sin pistas conceptuales, todos los criterios
y citas que existan en la respuesta. Eso tampoco prueba por sí solo retención ni efecto causal.
Sin aplicación con estudiantes, esta edición mantiene **carga cognitiva y eficacia no medidas**.

## Reparaciones de representación en toda la entrega

- Las 97 evaluaciones imprimen los tres niveles de sus **949 criterios de rúbrica** y tienen hoja de
  estudiante sin claves. El antecedente tenía 948: la evaluación corregida agrega un criterio.
- Las 70 unidades incompletas muestran los objetivos faltantes y sus motivos en Markdown y en el índice.
- Los 2.106 destinos de progresión son enlaces locales a su objetivo; cuando falta guion, el destino lo informa.
- Los 54 retenidos se mantienen fuera de los conjuntos aprobados. Los 151 objetivos sin guion no se rehabilitan.
- Los otros 860 guiones reciben un plan explícito de organización y observación del esfuerzo. Es apoyo de
  diseño; no se presenta como un nuevo recorrido validado por cada objetivo ni como corrección científica integral.

El alcance confirmado no incluye producir 1.013 recorridos nuevos ni resolver automáticamente las
713 observaciones del corpus. Se conservan los motivos de retención, las correcciones R23 pendientes
y la exigencia de contraste institucional; el triaje no se cuenta como errores confirmados o resueltos.

## Reproducción y validación

```sh
uv run --frozen gskg entrega compilar \
  data/clases_v4/entrega/guiones-ciencias-v4-20261025-v3.zip \
  --destino <carpeta_nueva> \
  --ciencias data/clases_v4/mejora_didactica_20261029/ciencias \
  --recorridos data/clases_v4/mejora_didactica_20261029/recorridos_finales \
  --revisiones data/clases_v4/mejora_didactica_20261029/revisiones \
  --archivo-zip <archivo_nuevo.zip>
uv run --frozen gskg entrega validar <carpeta_nueva>
make lint
make cobertura
make pruebas-js
make auditoria
git diff --check
```

El compilador usa un renderizador nuevo fuera de los módulos congelados de `clases/`. Regenera las
cuatro hojas desde el JSON canónico, conserva los bytes de la evaluación revisada, comprueba procedencia
y objetivo literal y coteja cada dictamen con los archivos efectivos. Valida inventario, denominadores,
exclusión de retenidos y enlaces internos. Un ZIP sucesor no modifica la publicación anterior.

La suite integral de la edición, antes de añadir el despacho al Escritorio, pasó **1.795 pruebas,
sin fallos, errores ni omisiones**, en 312,06 segundos
de pytest. Cobertura de líneas **79,81 % (20.109/25.197)**. También pasaron Ruff (342 archivos con formato
correcto), las seis pruebas JavaScript, la auditoría del repositorio y `git diff --check`. Los badges
se regeneraron con esa ejecución y la huella de código
`b3c691195607ae013feb08479a58f11d0f19f1694880835a77e8d22702b2e67c`.

La auditoría independiente del artefacto no usó el renderizador de producción como oráculo. Comprobó
CRC, nombres seguros y correspondencia por bytes/SHA de las **4.909 entradas del ZIP**, incluidos los
4.908 archivos inventariados y el manifiesto. Verificó las nueve identidades revisadas, ocho paquetes
con cuatro hojas, 16 ítems reservados, 52 criterios nuevos completos y **4.816 enlaces internos**.
No detectó claves finales íntegras en hojas de estudiante, ni consignas reservadas adelantadas en el
diagnóstico o refuerzo. Esta es una comprobación documental/textual, no una prueba de ausencia de
toda pista semántica ni de eficacia con estudiantes.

`gskg datos verificar` cotejó el corpus con el inventario remoto: 30.914 archivos idénticos por SHA,
42 SQLite operativos contados aparte, cero diferencias y cero faltantes. El cotejo de conservación
comprobó **23.231 archivos antecedentes** de datos, configuración y código de clases congelado sin
alteraciones; las dos bibliotecas conservan los SHA de sus recibos. Las tres tablas completas del ledger
conservan recuentos y huellas lógicas. Las modificaciones de código se limitan al prototipo de aprendizaje,
el contrato de mediciones, los materiales nuevos y el exportador sucesor.

Comandos adicionales reproducibles:

```sh
uv run --frozen python data/clases_v4/mejora_didactica_20261029/auditoria_final_independiente/auditar.py
uv run --frozen python data/clases_v4/mejora_didactica_20261029/verificar_preservacion.py
uv run --frozen gskg datos verificar
```

Un primer ensayo de integración descubrió un alias de ruta temporal de macOS, corregido con resolución
canónica; otro mostró dos representaciones contadas como módulos adicionales, corregidas sin duplicar
identidades. La suite anterior a ese último cambio se interrumpió y no se usa como medición de cierre.
Las cifras anteriores corresponden exclusivamente a la ejecución completa final y al ZIP final.

La entrega en el Escritorio y sus controles posteriores se documentan en
[Despacho y control de calidad](DESPACHO_CIENCIAS_V4.md). `AGENTS.md` conserva la instrucción del usuario
de dejar todos los paquetes finales en ese destino y mantener el mismo estándar para salidas futuras.

Los registros completos de comandos, dictámenes, auditoría independiente y conservación están en la
carpeta de trabajo. Hubo ensayos de integración conservados aparte; sólo `entrega_final/` y el ZIP
nombrado arriba constituyen la edición final. No se ejecutó Vertex, no se amplió el presupuesto y no
se escribió en GCS. La campaña conserva 4.294 llamadas y USD 3.219,5364705 de reserva.
