# Juicios semánticos de conocimiento V4

El descubrimiento conserva 6.901 hipótesis. El nuevo flujo permite examinar una de ellas con cuatro
lecturas ciegas y un cierre determinista. Preparar un expediente acredita disponibilidad de evidencia;
un respaldo requiere que esa evidencia implique la relación propuesta. Ningún juicio real de este flujo
se ha ejecutado todavía: los enlaces aceptados de V4 siguen en cero.

## Responsabilidades y contratos

| Componente | Responsabilidad |
|---|---|
| `producto/juicios.py` | Verificar informe, identidad del candidato, extremos, política y fuentes; preparar el contexto |
| `producto/_juicios_contratos.py` | Contratos tipados de soportes, expediente, cuatro rúbricas, dictamen, relación y colección |
| `motor/conocimiento.py` | Fanout ciego LangGraph, selección de citas, cierre y revalidación de estados |
| `producto/relaciones.py` | Reconstruir terminales, consolidar lotes y comprobar ciclos sobre las relaciones indicadas |
| `motor/validacion_conocimiento.py` | Reconstruir citas, criterios y cierre sin fuentes, generación ni recursión |
| `producto/conocimiento_publicado.py` | Archivar evidencias deduplicadas y revalidar expedientes contra currículo y catálogo |
| `producto/grafo_conocimiento.py` | Publicar relaciones condicionadas a una fila, sin prerrequisitos globales |
| `producto/consulta_conocimiento.py` | Rehidratar fuentes y recuperar exclusivamente el conocimiento admitido para la fila solicitada |
| `cli/juicios.py` | Preparar antes de modelos, validar destinos y presupuesto; exportar y consolidar |
| `config/juicios_conocimiento.yaml` | Rutas, límites y correspondencia de roles con la configuración de Vertex |

Una relación conserva candidato y tarea por huella, fila, grado SV, origen/destino y tipo. Su ámbito es
`fila_curricular`; no se vuelve una afirmación global sobre el concepto. Los tipos son `trabaja_concepto`,
`practica_declarada`, `contraste_documental` y `prerrequisito_necesario`. Estos artefactos están separados
del informe de hipótesis. Consolidar exporta un archivo verificable; su incorporación a un snapshot
requiere `producto construir --conocimiento`. Ninguno de estos pasos crea `CUBRE` ni un prerrequisito global.

La preparación comprueba huellas de la referencia y catálogo de candidatos e identidad reproducible de
cada candidato. Resuelve nodos por tipo, nunca por prefijos ni grados extranjeros normalizados. Rehidrata
la fila completa y exige todas sus celdas no vacías, incluidas las fórmulas antes de excluirlas del texto
factual. Compara documento, hoja, coordenada, ancla combinada, valores original/efectivo y tipo Excel.
Revalida alertas científicas antes de habilitar lectores. No basta que permanezca la celda del alias.

Los grupos de evidencia separan fila, objetivo y evaluación local cuando existe. Para un contraste se
añade el objetivo extranjero en la edición fijada; su tramo nativo permanece y la equivalencia SV es
nula. Para concepto/práctica se necesita un soporte primario de definición/desempeño. Un prerrequisito
necesita además soporte para el concepto de origen y para la dependencia: orden observado, afinidad o
facilitación no prueban necesidad cognitiva.

Los soportes adicionales son localizadores, sin texto científico aportado por el solicitante:

```json
[
  {
    "candidato_id": "CANDIDATO_V4:<huella-del-candidato>",
    "grupo": "destino",
    "documento": "<id-de-documento-en-catalogo>",
    "pagina": 12,
    "sha256": "<sha256-hexadecimal-verificado>",
    "version_documental": "<edicion-del-catalogo>"
  }
]
```

En DOCX/HTML se usa `localizador` con el código nativo en lugar de `pagina`. Se exige exactamente uno.
La raíz y el archivo pertenecen al catálogo de confianza; el soporte no concede acceso a otra ruta.
SHA, edición, localizador, glifos y bytes se vuelven a verificar. Un soporte no elimina las diferencias
de significado ni aprueba la relación: los lectores juzgan la implicación en los pasajes originales.

## Lecturas y decisión

| Lector | Criterios adicionales a evidencia, alcance y ausencia de extrapolación |
|---|---|
| Científico de la disciplina | Significado científico; definición o desempeño primario |
| Curricular | Desempeño local; demanda cognitiva; traducción y modalidades |
| Psicopedagogo | Adecuación al grado SV; carga y apoyos; necesidad cognitiva o aplicabilidad |
| Refutador | Ambigüedades/negaciones; contraejemplos y alternativas |

Cada criterio exige `si`, `no` o `insuficiente`. No hay valores predeterminados ni campos extra. El
contexto no contiene confianza IA, decisiones ajenas ni justificaciones de las aristas históricas.
El proveedor recibe fragmentos y procedencia, con máximo completo de 24.000 caracteres JSON. Si no
cabe evidencia de cada grupo obligatorio, se abstiene antes de gastar. El empaquetado reserva primero
un fragmento por grupo, permitiendo grupos superpuestos, antes de completar por coincidencia léxica.
Cada lector debe citar al menos
un fragmento registrado de cada grupo; el código copia el literal (hasta veinte palabras), no el modelo.

Todos los criterios de los cuatro lectores deben ser `si` para `respaldado`. Un `no` veta el respaldo
(`no_respaldado`); evidencia insuficiente o fallo de contrato deja `abstencion`. No se promedian lectores
ni se repite un juicio para obtener acuerdo. Un rechazo describe este enlace y evidencia: no demuestra
ausencia del concepto en toda la malla ni ineficacia de una estrategia docente.

La reanudación vincula solicitud, entorno, código, prompts, modelos, corpus, ledger e ID de presupuesto.
Rehidrata fuentes y reconstruye terminales desde los dictámenes. Rechaza un terminal sin preparación,
otro modelo, criterios/citas incompatibles o una bandera positiva alterada. No basta confiar en el JSON
guardado. La configuración reutiliza `motor/ejecuciones.py` y `Registro`; no hay otro mecanismo de gasto.

## Uso

```bash
# Preparar un caso real sin SDK, ADC, ledger ni llamadas a modelos:
uv run gskg producto juicios evaluar CANDIDATO_V4:7e7bc57c33959776aea27726c158470d8f2d070d652c30459819863abdda0471 --salida /tmp/expediente.json

# Sólo cuando el corpus/destino/gasto de este flujo tenga autorización:
uv run gskg producto juicios evaluar <candidato-id> --soportes /tmp/soportes.json --ejecutar --ejecucion conocimiento-001 --salida /tmp/resultado.json

# Revalidación local de los resultados completos indicados:
uv run gskg producto juicios consolidar /tmp/resultado.json /tmp/otro-resultado.json --soportes /tmp/soportes.json --salida /tmp/coleccion.json

# Medición estructural del contexto, sin proveedores ni gold:
uv run gskg producto juicios medir-contexto --salida /tmp/presupuesto-contexto.json

# Incorporación opcional a una generación local; exige catálogo completo:
uv run gskg producto construir --conocimiento /tmp/coleccion.json
```

Los cuatro lectores usan los modelos definidos por rol en `motor.yaml`, proyecto institucional y región
`global`, máximo cuatro intentos y USD 2 de reserva por ejecución, sin reintentos. Es una configuración,
no una autorización ni factura. Cambiar el ID no debe usarse para ocultar gasto o escoger una ronda
favorable. Los destinos de resultados, ledger, checkpoints y log deben ser distintos entre sí y de los
inputs; se validan antes de crear un proveedor. Una interrupción exporta el consumo conservado.

El ejemplo real guardado en `data/producto/juicios/contraste_preparado.json` es un contraste propuesto
desde instrumentos de medición de Ciencias 8.º hacia un objetivo histórico ENG de distribución de especies.
La coincidencia que lo propuso no garantiza compatibilidad científica: es un expediente para juicio,
no un caso positivo ni un resultado de calidad. No ha sido enviado a modelos.
El tamaño, fragmentos y huellas actuales del expediente se registran en la auditoría local. El caso de concepto sin
definición primaria quedó en `concepto_sin_soporte.json`, con abstención y cero llamadas. Sus huellas,
alcance, pruebas y presupuesto conservado están en [la auditoría local](investigacion/resultados_juicios_locales_2026.json).

Consolidar usa un puerto que sólo identifica los modelos configurados; no instancia un cliente, ADC o
ledger. Exige el workflow completo, y el resultado visible debe coincidir con su terminal. Rechaza un
candidato repetido: no selecciona el resultado más favorable entre rondas. Conserva rechazos y abstenciones.

## Dependencias y límites

La consolidación comprueba componentes cíclicas entre **todos los estados que se le entregan**. Un ciclo
conserva las relaciones respaldadas y sus dictámenes, pero deja vacías las relaciones admisibles de toda
esa colección; no elimina aristas para fabricar un DAG. La proyección acíclica ofrece orden topológico
estructural sin inventar clausura transitiva. Sin prerrequisitos respaldados declara explícitamente ese
estado, no una progresión verificada.

Una colección parcial no prueba consistencia frente a lotes omitidos ni exhaustividad del currículo.
El archivo `conocimiento-publicado-1` conserva todos los resultados, expedientes, fuentes y evidencias
deduplicadas. El constructor revalida cada cierre, sus grupos/celdas originales, extremos, edición y
modelos configurados; rehidrata los originales y comprueba ciclos antes de publicarlo. El lector del
snapshot vuelve a verificar el archivo y su correspondencia exacta con el grafo. Sus hashes comprueban
integridad local; no son firmas digitales ni certifican la precisión de los jueces.

El snapshot `producto-2` exige ocho archivos, incluido `conocimiento.json` (`null` cuando no se aporta).
Cada vínculo admisible se representa mediante un nodo `RelacionCurricular` con aristas `EN_CONTEXTO`,
`ORIGEN_RELACION` y `DESTINO_RELACION`. Conserva fila, grado SV, candidato y dictámenes. Los extremos
históricos mantienen sus tramos nativos como metadata; no reciben un grado SV ni pasan a ser fuente
primaria. No se proyectan relaciones globales que permitan saltar entre filas o heredar prerrequisitos.

`Solicitud.fila_id` y `motor buscar/responder --fila-id` activan la recuperación por fila exacta.
`BuscadorProducto` exige versión V4, grado y disciplina admitida por el catálogo; añade únicamente
evidencia primaria de los vínculos admisibles de esa fila, rehidratada antes de usarse. Sin este campo,
la búsqueda general conserva el baseline. Las unidades siempre lo incluyen y el Motor veta un anclaje
de otra fila antes de llamar a los jueces. La unidad conserva una segunda comprobación independiente.
Reanudar actividades también rehidrata las evidencias persistidas y reconstruye el resultado.

La publicación V4 local conserva quince juicios reales: dos respaldos, seis rechazos y siete
abstenciones. `conocimiento-publicado-2` conserva tres cohortes originales completas y sus protocolos;
la vista de consulta deduplica evidencia. Componer rechaza candidatos repetidos y reconstruye los
cierres y ciclos del conjunto. No admite seleccionar sólo los casos favorables de una cohorte ni
reemplazar un voto anterior por otro ensayo. No hay prerrequisitos respaldados ni progresión verificada.
[Resultados actuales](investigacion/continuacion_ciencias_20261021.md).

Las pruebas usan libros/PDF sintéticos, lectores simulados y SQLite real: vetos por cada rol, criterios
insuficientes, citas ajenas, celdas omitidas, fuente cambiada, alertas, terminales falsificados, reanudación,
destinos protegidos y ciclos entre lotes. Verifican contratos y operación; no calibran precisión semántica
ni eficacia educativa. Los ensayos remotos registrados verifican la integración y muestran errores
observados; sigue pendiente una calibración semántica independiente, con corpus/destino/gasto
delimitados y registro de costo/latencia.

## Lectura completa y lotes acotados

El contexto conserva el texto primario completo de las celdas y páginas seleccionadas. Las citas
breves de hasta veinte palabras son localizadores, no sustituyen la lectura. El presupuesto cuenta
el JSON completo; si los grupos obligatorios no caben, el preparador se abstiene. Los jueces
seleccionan un ID válido por grupo mediante esquema escalar y el código vuelve a validar el contrato
original del rol. Una cita válida todavía puede no implicar la afirmación: el veto semántico permanece.

`producto juicios preparar-lote` fija candidatos, expedientes, soportes, modelos y cotas en un plan;
`ejecutar-lote` lo verifica sin gastar y sólo invoca modelos con `--ejecutar`. Todos los casos comparten
ID y ledger. Cuatro errores de lectores en un mismo caso detienen el resto del lote; sus resultados
pendientes y gasto se conservan. Una abstención semántica no se vuelve a votar para obtener unanimidad.

`producto juicios componer <original-1.json> <original-2.json> --salida <compuesto.json>` conserva las
cohortes completas. Los componentes agregan almacenamiento y carga: deduplicación de consulta no
equivale a compresión de los archivos originales. La reanudación de los dos casos de lectura completa
recuperó los terminales con generación prohibida en memoria y cero consumo incremental.
